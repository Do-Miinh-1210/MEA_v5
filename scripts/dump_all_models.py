import sys, os, marshal, json

sys.stdout.reconfigure(encoding='utf-8')

src_dir = r"M:\IT\TikZStudio\extracted_src"
out_dir = r"m:\IT\Phần mềm biên soạn tài liệu\MEA_v5.0\desktop_csharp\src\MatrixExamAI.Desktop\Resources\TikzModels"
os.makedirs(out_dir, exist_ok=True)

def dump_hinh_khong_gian():
    fpath = os.path.join(src_dir, "tab_hinh_khong_gian.pyc")
    with open(fpath, "rb") as f:
        f.seek(16)
        co = marshal.load(f)
    consts = list(co.co_consts)
    shapes = []
    for i, c in enumerate(consts):
        if isinstance(c, str) and ("Chóp" in c or "Lăng trụ" in c or "Hình" in c or "Tứ diện" in c) and len(c) < 50:
            shape_name = c
            tikz_code = ""
            decl = ""
            params = []
            points = []
            for j in range(i + 1, min(i + 16, len(consts))):
                cj = consts[j]
                if isinstance(cj, str) and "\\begin{tikzpicture}" in cj:
                    tikz_code = cj
                elif isinstance(cj, str) and ("goc" in cj or "a=" in cj or "h=" in cj) and ";" in cj:
                    decl = cj
                elif isinstance(cj, tuple) and len(cj) > 0:
                    if isinstance(cj[0], tuple):
                        params = cj
                    elif all(isinstance(x, str) and len(x) <= 5 for x in cj):
                        points = cj
            if tikz_code:
                # convert tuples to json friendly
                p_list = []
                for p in params:
                    if isinstance(p, tuple) and len(p) >= 2:
                        p_list.append({"name": str(p[0]), "default": str(p[1])})
                shapes.append({
                    "category": "Hình không gian 3D",
                    "name": shape_name,
                    "tikz": tikz_code,
                    "declaration": decl,
                    "params": p_list,
                    "points": list(points)
                })
    return shapes

def dump_mat_tron_xoay():
    fpath = os.path.join(src_dir, "tab_mat_tron_xoay.pyc")
    with open(fpath, "rb") as f:
        f.seek(16)
        co = marshal.load(f)
    consts = list(co.co_consts)
    solids = []
    for i, c in enumerate(consts):
        if isinstance(c, str) and ("Hình" in c or "Mặt" in c or "Trụ" in c or "Nón" in c or "Cầu" in c) and len(c) < 50:
            name = c
            tikz_code = ""
            for j in range(i + 1, min(i + 15, len(consts))):
                cj = consts[j]
                if isinstance(cj, str) and "\\begin{tikzpicture}" in cj:
                    tikz_code = cj
                    break
            if tikz_code:
                solids.append({
                    "category": "Mặt tròn xoay",
                    "name": name,
                    "tikz": tikz_code
                })
    return solids

def dump_module_templates(fname, cat_name):
    fpath = os.path.join(src_dir, fname)
    if not os.path.exists(fpath):
        return []
    with open(fpath, "rb") as f:
        f.seek(16)
        co = marshal.load(f)
    
    def get_all(co_obj):
        res = []
        for c in co_obj.co_consts:
            if isinstance(c, type(co_obj)):
                res.extend(get_all(c))
            elif isinstance(c, str):
                res.append(c)
        return res

    all_strs = get_all(co)
    items = []
    current_title = ""
    for s in all_strs:
        if len(s) < 60 and not s.startswith("\\") and any(kw in s for kw in ["Tam giác", "Tứ giác", "Hình", "Đường", "Elip", "Parabol", "Hypebol", "Hàm", "Phân thức", "Bảng", "Lượng giác", "Logarit"]):
            current_title = s
        elif ("\\begin{tikzpicture}" in s or "\\addplot" in s or "\\tkz" in s or "\\draw" in s) and len(s) > 40:
            items.append({
                "category": cat_name,
                "name": current_title if current_title else f"{cat_name} mẫu",
                "tikz": s
            })
    return items

models = {
    "hinh_khong_gian": dump_hinh_khong_gian(),
    "mat_tron_xoay": dump_mat_tron_xoay(),
    "hinh_phang": dump_module_templates("tab_hinh_phang.pyc", "Hình phẳng 2D"),
    "duong_tron": dump_module_templates("tab_duong_tron.pyc", "Đường tròn"),
    "duong_conic": dump_module_templates("tab_duong_conic.pyc", "Đường conic"),
    "bang_bien_thien": dump_module_templates("tab_bang_bien_thien.pyc", "Bảng biến thiên"),
    "do_thi": dump_module_templates("tab_do_thi.pyc", "Đồ thị hàm số"),
    "do_thi_khac": dump_module_templates("tab_do_thi_khac.pyc", "Đồ thị khác"),
    "to_mien": dump_module_templates("tab_to_mien_do_thi.pyc", "Tô miền diện tích")
}

out_path = os.path.join(out_dir, "tikz_studio_library.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(models, f, ensure_ascii=False, indent=2)

print("Dumped complete library!")
for k, v in models.items():
    print(f"  {k}: {len(v)} models")
