import json
import os
import sys
from pathlib import Path
import urllib.request
import urllib.parse
import zipfile
import subprocess

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def get_github_token():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    try:
        proc = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n", capture_output=True, text=True)
        for line in proc.stdout.splitlines():
            if line.startswith("password="):
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return ""

REPO = "Do-Miinh-1210/MEA_v5"
TAG = "v5.2.0.4"
TITLE = "MatrixExamAI Pro v5.2.0.4 (Centered Word A4 Paper Preview)"
BODY = "Bản phát hành MatrixExamAI Pro v5.2.0.4: Căn giữa hoàn hảo trang in Word A4 (khung giấy trắng) trong chế độ xem trước; tự động cân đối hai bên lề đối xứng đẹp mắt trên mọi kích thước màn hình."

def build_patch_zip(publish_dir: Path, output_zip: Path):
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    files_to_pack = [
        "MatrixExamAI.Desktop.dll",
        "MatrixExamAI.Desktop.exe",
        "MatrixExamAI.Shared.dll",
        "MatrixExamAI.Desktop.deps.json",
        "MatrixExamAI.Desktop.runtimeconfig.json"
    ]
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in files_to_pack:
            fpath = publish_dir / fname
            if fpath.exists():
                zf.write(fpath, arcname=fname)
                print(f"  + Added to patch: {fname} ({fpath.stat().st_size} bytes)")
    print(f"[OK] Created patch zip: {output_zip.name} ({output_zip.stat().st_size} bytes)")

def create_release_and_upload():
    token = get_github_token()
    if not token:
        print("[ERROR] GitHub token not found.")
        return

    base_dir = Path(__file__).resolve().parent.parent
    publish_dir = base_dir / "desktop_csharp" / "publish"
    dist_dir = base_dir / "dist" / "installer"
    patch_zip_path = dist_dir / "MatrixExamAI_Patch.zip"
    installer_path = dist_dir / "MatrixExamAI_Pro_Setup.exe"

    # 1. Build patch zip
    if publish_dir.exists():
        build_patch_zip(publish_dir, patch_zip_path)

    # 2. Create or fetch release
    url = f"https://api.github.com/repos/{REPO}/releases"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MatrixExamAI-Publisher"
    }
    payload = {
        "tag_name": TAG,
        "target_commitish": "main",
        "name": TITLE,
        "body": BODY,
        "draft": False,
        "prerelease": False
    }

    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f"HTTPError: {e.code} - {err_body}")
        req_get = urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases/tags/{TAG}", headers=headers)
        with urllib.request.urlopen(req_get) as resp_get:
            data = json.loads(resp_get.read().decode("utf-8"))

    release_id = data['id']
    upload_url_template = data["upload_url"].split("{")[0]
    print(f"Release ID: {release_id}, Tag: {data['tag_name']}")

    # 3. List of files to upload
    files_to_upload = []
    if patch_zip_path.exists():
        files_to_upload.append(patch_zip_path)
    if installer_path.exists():
        files_to_upload.append(installer_path)

    # Delete existing assets if they have matching names
    existing_assets = {a["name"]: a["id"] for a in data.get("assets", [])}
    for file_path in files_to_upload:
        asset_name = file_path.name
        if asset_name in existing_assets:
            asset_id = existing_assets[asset_name]
            print(f"Deleting existing asset '{asset_name}' (ID: {asset_id})...")
            del_req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases/assets/{asset_id}", headers=headers, method="DELETE")
            try:
                urllib.request.urlopen(del_req)
                print(f"[OK] Deleted old asset: {asset_name}")
            except Exception as ex:
                print(f"[WARN] Failed to delete old asset {asset_name}: {ex}")

    # 4. Upload Assets
    for file_path in files_to_upload:
        asset_name = file_path.name
        upload_url = f"{upload_url_template}?name={urllib.parse.quote(asset_name)}"
        file_bytes = file_path.read_bytes()
        upload_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
            "User-Agent": "MatrixExamAI-Publisher"
        }

        print(f"Uploading {asset_name} ({len(file_bytes)} bytes)...")
        up_req = urllib.request.Request(upload_url, data=file_bytes, headers=upload_headers, method="POST")
        with urllib.request.urlopen(up_req) as up_resp:
            up_data = json.loads(up_resp.read().decode("utf-8"))
            print(f"[OK] Upload complete: {up_data['name']} (Size: {up_data['size']} bytes)")
            print(f"     Download URL: {up_data['browser_download_url']}")

if __name__ == "__main__":
    create_release_and_upload()
