import json
import os
import sys
import shutil
import hashlib
from pathlib import Path
import urllib.request
import urllib.parse
import zipfile
import subprocess

try:
    import bsdiff4
except ImportError:
    bsdiff4 = None

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
TAG = "v5.3.0.22"
TITLE = "MatrixExamAI Pro v5.3.0.22 (Nâng cấp Kỹ năng Vẽ hình TikZ 3D & Mô hình Khối Tròn Xoay Chuyên sâu)"
BODY = "Bản phát hành MatrixExamAI Pro v5.3.0.22: Nâng cấp toàn diện phân hệ TikZ 3D và các mô hình khối tròn xoay (hình nón, hình trụ, mặt cầu, nón cụt, chỏm cầu, thiết diện qua trục/song song trục, mặt phẳng cắt mặt cầu, khối tròn xoay lồng nhau và khối tròn xoay tích phân). Chuẩn hóa góc nhìn elip đáy (nửa sau nét đứt, nửa trước nét liền), bổ sung đổ bóng 3D chân thực trên cả Desktop App và Word Add-in."

def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().lower()

def build_patch_zip(publish_dir: Path, output_zip: Path):
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    files_to_pack = [
        "MatrixExamAI.Desktop.dll",
        "MatrixExamAI.Desktop.exe",
        "MatrixExamAI.Shared.dll",
        "ICSharpCode.SharpZipLib.dll",
        "MatrixExamAI.Desktop.deps.json",
        "MatrixExamAI.Desktop.runtimeconfig.json"
    ]
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in files_to_pack:
            fpath = publish_dir / fname
            if fpath.exists():
                zf.write(fpath, arcname=fname)
                print(f"  + Added to full patch: {fname} ({fpath.stat().st_size} bytes)")
        
        word_addon_dir = publish_dir.parent.parent / "word_addon" / "src" / "MatrixExamAI.WordAddIn" / "bin" / "Debug" / "net48"
        if word_addon_dir.exists():
            for root, dirs, files in os.walk(word_addon_dir):
                for file in files:
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(word_addon_dir)
                    arcname = f"word_addon/{rel_path.as_posix()}"
                    zf.write(full_path, arcname=arcname)
            print(f"  + Added word_addon folder to full patch")

    print(f"[OK] Created full patch zip: {output_zip.name} ({output_zip.stat().st_size} bytes)")

def build_delta_zip(publish_dir: Path, output_delta_zip: Path, cache_dir: Path):
    if bsdiff4 is None:
        print("[WARN] bsdiff4 is not available, skipping delta zip.")
        return False

    output_delta_zip.parent.mkdir(parents=True, exist_ok=True)
    last_pub = cache_dir / "last_published"
    last_pub.mkdir(parents=True, exist_ok=True)

    # Always fetch latest published baseline from GitHub to ensure accurate delta against deployed version
    try:
        print("[INFO] Fetching latest baseline patch from GitHub for delta reference...")
        prev_patch_url = f"https://github.com/{REPO}/releases/latest/download/MatrixExamAI_Patch.zip"
        tmp_zip = cache_dir / "prev_patch.zip"
        urllib.request.urlretrieve(prev_patch_url, tmp_zip)
        for f in last_pub.iterdir():
            if f.is_file():
                f.unlink()
        with zipfile.ZipFile(tmp_zip, "r") as zf:
            zf.extractall(last_pub)
        tmp_zip.unlink(missing_ok=True)
        print("[OK] Loaded fresh reference baseline files from GitHub into cache.")
    except Exception as ex:
        print(f"[WARN] Could not fetch fresh baseline from GitHub: {ex}")

    if not (last_pub / "MatrixExamAI.Desktop.dll").exists():
        print("[WARN] Baseline dll not found, skipping delta.")
        return False

    files_to_pack = [
        "MatrixExamAI.Desktop.dll",
        "MatrixExamAI.Desktop.exe",
        "MatrixExamAI.Shared.dll",
        "ICSharpCode.SharpZipLib.dll",
        "MatrixExamAI.Desktop.deps.json",
        "MatrixExamAI.Desktop.runtimeconfig.json"
    ]

    manifest = {"files": []}
    staging_dir = output_delta_zip.parent / "staging_delta"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    for fname in files_to_pack:
        new_path = publish_dir / fname
        old_path = last_pub / fname
        if not new_path.exists():
            continue

        new_bytes = new_path.read_bytes()
        new_sha = compute_sha256(new_bytes)

        if old_path.exists() and fname.endswith(".dll"):
            old_bytes = old_path.read_bytes()
            old_sha = compute_sha256(old_bytes)
            if old_sha != new_sha:
                diff_bytes = bsdiff4.diff(old_bytes, new_bytes)
                diff_name = fname + ".bsdiff"
                (staging_dir / diff_name).write_bytes(diff_bytes)
                reduction = (1 - len(diff_bytes) / len(new_bytes)) * 100
                print(f"  + Delta diff for {fname}: {len(diff_bytes)} bytes (was {len(new_bytes)} bytes, -{reduction:.1f}%)")
                manifest["files"].append({
                    "name": fname,
                    "is_delta": True,
                    "delta_file": diff_name,
                    "base_sha256": old_sha,
                    "target_sha256": new_sha
                })
            else:
                print(f"  = Unchanged: {fname}")
        else:
            (staging_dir / fname).write_bytes(new_bytes)
            print(f"  + Added file to delta: {fname} ({len(new_bytes)} bytes)")
            manifest["files"].append({
                "name": fname,
                "is_delta": False,
                "target_sha256": new_sha
            })

    # SAFEGUARD: MatrixExamAI.Desktop.dll MUST ALWAYS be included in manifest!
    # If not added as a delta bsdiff, include full DLL so the app never fails to update!
    has_desktop_dll = any(f["name"] == "MatrixExamAI.Desktop.dll" for f in manifest["files"])
    if not has_desktop_dll:
        dll_path = publish_dir / "MatrixExamAI.Desktop.dll"
        if dll_path.exists():
            dll_bytes = dll_path.read_bytes()
            (staging_dir / "MatrixExamAI.Desktop.dll").write_bytes(dll_bytes)
            manifest["files"].append({
                "name": "MatrixExamAI.Desktop.dll",
                "is_delta": False,
                "target_sha256": compute_sha256(dll_bytes)
            })
            print(f"[SAFEGUARD] MatrixExamAI.Desktop.dll included as full file in delta package ({len(dll_bytes)} bytes)")

    manifest_path = staging_dir / "delta_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    word_addon_dir = publish_dir.parent.parent / "word_addon" / "src" / "MatrixExamAI.WordAddIn" / "bin" / "Debug" / "net48"
    if word_addon_dir.exists():
        word_addon_staging = staging_dir / "word_addon"
        shutil.copytree(word_addon_dir, word_addon_staging, dirs_exist_ok=True)
        print(f"  + Added word_addon folder to delta staging")

    with zipfile.ZipFile(output_delta_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(staging_dir):
            for file in files:
                full_path = Path(root) / file
                arcname = full_path.relative_to(staging_dir).as_posix()
                zf.write(full_path, arcname=arcname)

    shutil.rmtree(staging_dir, ignore_errors=True)
    print(f"[OK] Created delta patch zip: {output_delta_zip.name} ({output_delta_zip.stat().st_size} bytes)")

    # Update cache for next version
    for fname in files_to_pack:
        src = publish_dir / fname
        if src.exists():
            shutil.copy2(src, last_pub / fname)

    return True

def create_release_and_upload():
    token = get_github_token()
    if not token:
        print("[ERROR] GitHub token not found.")
        return

    base_dir = Path(__file__).resolve().parent.parent
    publish_dir = base_dir / "desktop_csharp" / "publish"
    cache_dir = base_dir / "desktop_csharp" / "build_cache"
    dist_dir = base_dir / "dist" / "installer"
    patch_zip_path = dist_dir / "MatrixExamAI_Patch.zip"
    delta_zip_path = dist_dir / "MatrixExamAI_Delta.zip"
    installer_path = dist_dir / "MatrixExamAI_Pro_Setup.exe"

    # 1. Build patch zips
    if publish_dir.exists():
        build_delta_zip(publish_dir, delta_zip_path, cache_dir)
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
    # 3. List of files to upload
    files_to_upload = []
    if delta_zip_path.exists():
        files_to_upload.append(delta_zip_path)
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
