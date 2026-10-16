import sys, os, marshal, json

sys.stdout.reconfigure(encoding='utf-8')

src_dir = r"M:\IT\TikZStudio\extracted_src"
out_dir = r"m:\IT\Phần mềm biên soạn tài liệu\MEA_v5.0\desktop_csharp\src\MatrixExamAI.Desktop\Resources\TikzModels"
os.makedirs(out_dir, exist_ok=True)

modules = [
    "tab_hinh_khong_gian.pyc",
    "tab_mat_tron_xoay.pyc",
    "tab_hinh_phang.pyc",
    "tab_duong_conic.pyc",
    "tab_duong_tron.pyc",
    "tab_do_thi.pyc",
    "tab_do_thi_khac.pyc",
    "tab_to_mien_do_thi.pyc",
    "tab_bang_bien_thien.pyc"
]

all_extracted = {}

for m in modules:
    mpath = os.path.join(src_dir, m)
    if not os.path.exists(mpath):
        continue
    with open(mpath, "rb") as f:
        f.seek(16)
        co = marshal.load(f)
    
    module_data = {
        "filename": m,
        "consts": [],
        "strings": [],
        "tuples": []
    }
    
    for i, c in enumerate(co.co_consts):
        if isinstance(c, str):
            module_data["strings"].append({"idx": i, "val": c})
        elif isinstance(c, tuple):
            # serialize tuple
            def ser_t(t):
                res = []
                for x in t:
                    if isinstance(x, tuple):
                        res.append(ser_t(x))
                    elif isinstance(x, (str, int, float, bool, type(None))):
                        res.append(x)
                    else:
                        res.append(str(type(x)))
                return res
            module_data["tuples"].append({"idx": i, "val": ser_t(c)})
            
    all_extracted[m] = module_data

out_json = os.path.join(out_dir, "raw_tikzstudio_extracted.json")
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(all_extracted, f, ensure_ascii=False, indent=2)

print(f"Extracted {len(all_extracted)} modules to {out_json}")
