import json
import shutil
import urllib.request
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import scripts.publish_release as p

def main():
    token = p.get_github_token()
    repo = p.REPO
    tag = "v5.3.0.18"

    patch_zip = Path("dist/installer/MatrixExamAI_Patch.zip")
    delta_zip = Path("dist/installer/MatrixExamAI_Delta.zip")

    # Replace delta_zip with full patch so clients without v5.3.0.17 baseline never fail SHA check
    shutil.copy2(patch_zip, delta_zip)
    print(f"[OK] Replaced delta_zip with full patch ({delta_zip.stat().st_size} bytes)")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MatrixExamAI-Publisher"
    }

    # Fetch release
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases/tags/{tag}", headers=headers)
    with urllib.request.urlopen(req) as resp:
        rel = json.loads(resp.read().decode("utf-8"))

    # Delete existing MatrixExamAI_Delta.zip
    for a in rel.get("assets", []):
        if a["name"] == "MatrixExamAI_Delta.zip":
            asset_id = a["id"]
            print(f"Deleting old MatrixExamAI_Delta.zip (ID: {asset_id})...")
            del_req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases/assets/{asset_id}", headers=headers, method="DELETE")
            urllib.request.urlopen(del_req)
            print("[OK] Deleted old asset.")

    # Upload new MatrixExamAI_Delta.zip
    upload_url_template = rel["upload_url"].split("{")[0]
    upload_url = f"{upload_url_template}?name=MatrixExamAI_Delta.zip"
    data = delta_zip.read_bytes()
    up_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream",
        "User-Agent": "MatrixExamAI-Publisher"
    }
    print(f"Uploading safe MatrixExamAI_Delta.zip ({len(data)} bytes)...")
    up_req = urllib.request.Request(upload_url, data=data, headers=up_headers, method="POST")
    with urllib.request.urlopen(up_req) as up_resp:
        res = json.loads(up_resp.read().decode("utf-8"))
        print(f"[SUCCESS] Uploaded {res['name']} ({res['size']} bytes) to release {tag}!")

if __name__ == "__main__":
    main()
