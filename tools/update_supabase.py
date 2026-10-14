"""
tools/update_supabase.py — Cập nhật Supabase credentials trong config.py
Cách dùng:
    python tools/update_supabase.py
Hoặc truyền thẳng:
    python tools/update_supabase.py "URL_MỚI" "KEY_MỚI"
"""
import base64, sys

def encode(s: str) -> str:
    return base64.b64encode(s.encode()).decode()

def clean_url(u: str) -> str:
    u = u.strip().rstrip("/")
    if u.endswith("/rest/v1"):
        u = u[:-len("/rest/v1")].rstrip("/")
    return u

def update_config(url: str, key: str) -> None:
    url = clean_url(url)
    key = key.strip()
    cfg = open("config.py", encoding="utf-8").read()
    url_enc = encode(url)
    key_enc = encode(key)
    for old, new in [
        ('_SUPABASE_URL_ENC = "', f'_SUPABASE_URL_ENC = "{url_enc}'),
        ('_SUPABASE_KEY_ENC = "', f'_SUPABASE_KEY_ENC = "{key_enc}'),
    ]:
        if old in cfg:
            cfg = cfg.replace(cfg[cfg.find(old):].split('"')[0] + '"', new, 1)
        else:
            print(f"  [!] Khong tim thay '{old}' trong config.py")
            return
    open("config.py", "w", encoding="utf-8").write(cfg)
    print(f"  [OK] Da cap nhat config.py")
    print(f"       URL : {url}")
    print(f"       KEY : {key[:12]}...")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        update_config(sys.argv[1], sys.argv[2])
    else:
        print("Nhap SUPABASE_URL moi:")
        url = input().strip()
        print("Nhap SUPABASE_KEY moi:")
        key = input().strip()
        if url and key:
            update_config(url, key)
        else:
            print("Can nhap day du ca 2 gia tri.")
