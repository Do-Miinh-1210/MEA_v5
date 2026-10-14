import json
import os
import pathlib
import sys

# Ensure repo root is on sys.path to import services.key_manager
repo_dir = pathlib.Path(__file__).resolve().parent.parent
if str(repo_dir) not in sys.path:
    sys.path.insert(0, str(repo_dir))

try:
    from services.key_manager import get_key_manager
    km = get_key_manager()
    gk = km.load('Google Gemini') or ''
    rk = km.load('9Router') or ''
    
    app_data = pathlib.Path(os.environ.get('LOCALAPPDATA', '')) / 'MatrixExamAI'
    app_data.mkdir(parents=True, exist_ok=True)
    cfg_file = app_data / 'config.json'
    
    cfg = {}
    if cfg_file.exists():
        try:
            cfg = json.loads(cfg_file.read_text(encoding='utf-8'))
        except Exception:
            pass
            
    if gk.strip():
        cfg['apiKey'] = gk.strip().splitlines()[0]
    cfg['model'] = 'gemini-3.8-flash'
    if rk.strip():
        cfg['nineRouterApiKey'] = rk.strip().splitlines()[0]
        
    cfg_file.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding='utf-8')
    print('  [OK] Da dong bo API key thanh cong vao:', cfg_file)
except Exception as ex:
    print('  [WARN] Khong the tu dong dong bo key:', ex)
