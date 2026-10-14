import json
import os
from pathlib import Path
import urllib.request
import urllib.parse

import subprocess

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
TAG = "v5.1.2"
TITLE = "MatrixExamAI Pro v5.1.2"
BODY = "Bản phát hành MatrixExamAI Pro v5.1.2: Chuẩn hóa phân hệ Ngân hàng câu hỏi (NHCH) theo app cũ - Bỏ toàn bộ ví dụ mẫu mặc định, xóa cột Đáp án và bổ sung nút Xóa câu hỏi / Xóa sạch."

def create_release_and_upload():
    token = get_github_token()
    if not token:
        print("[ERROR] GitHub token not found.")
        return

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
        # If release already exists, fetch it
        req_get = urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases/tags/{TAG}", headers=headers)
        with urllib.request.urlopen(req_get) as resp_get:
            data = json.loads(resp_get.read().decode("utf-8"))

    upload_url_template = data["upload_url"] # e.g. https://uploads.github.com/repos/.../assets{?name,label}
    upload_url = upload_url_template.split("{")[0] + f"?name=MatrixExamAI_Pro_Setup.exe"

    print(f"Release ID: {data['id']}, Tag: {data['tag_name']}")
    print(f"Upload URL: {upload_url}")

    # 2. Upload Asset
    installer_path = Path(r"M:\IT\Phần mềm biên soạn tài liệu\MEA_v5.0\dist\installer\MatrixExamAI_Pro_Setup.exe")
    if not installer_path.exists():
        print(f"[ERROR] Installer not found at: {installer_path}")
        return

    file_bytes = installer_path.read_bytes()
    upload_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream",
        "User-Agent": "MatrixExamAI-Publisher"
    }

    print(f"Uploading installer ({len(file_bytes)} bytes)...")
    up_req = urllib.request.Request(upload_url, data=file_bytes, headers=upload_headers, method="POST")
    with urllib.request.urlopen(up_req) as up_resp:
        up_data = json.loads(up_resp.read().decode("utf-8"))
        print(f"[OK] Upload complete: {up_data['name']} (Size: {up_data['size']} bytes)")
        print(f"Download URL: {up_data['browser_download_url']}")

if __name__ == "__main__":
    create_release_and_upload()
