"""
omr_exam/excel_exporter.py — Xuất Bảng đáp án & Ma trận hoán vị câu hỏi (Phiếu soi câu) ra Excel (.xlsx).
Sử dụng openpyxl, định dạng chuyên nghiệp, đẹp mắt chuẩn giáo dục.
"""
from __future__ import annotations
from typing import Dict, List, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def export_exam_keys_and_matrix_to_excel(
    filepath: str,
    keys_by_code: Dict[str, Dict[int, str]],
    question_map_by_code: Optional[Dict[str, Dict[int, int]]] = None,
    orig_keys: Optional[Dict[int, str]] = None,
    option_map_by_code: Optional[Dict[str, Dict[int, Dict[str, str]]]] = None,
) -> str:
    """
    Tạo file Excel (.xlsx) với 3 trang tính (sheets):
    1. 'Bảng Đáp Án': Ma trận đáp án chuẩn của tất cả các mã đề.
    2. 'Phiếu Soi Câu': Đối chiếu câu mới <-> câu gốc của từng mã đề.
    3. 'Ma Trận Hoán Vị Đ/A': Chi tiết hoán vị từng phương án A, B, C, D.
    """
    wb = openpyxl.Workbook()
    
    # Border & Font chuẩn
    font_header = Font(name="Times New Roman", size=11, bold=True, color="FFFFFF")
    font_bold = Font(name="Times New Roman", size=11, bold=True)
    font_regular = Font(name="Times New Roman", size=11)
    
    fill_header_navy = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    fill_header_blue = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
    fill_zebra = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    fill_highlight = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1")
    )
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    
    codes = sorted(keys_by_code.keys())
    if not codes:
        wb.save(filepath)
        return filepath
        
    all_q_nums = sorted(list({q for c in codes for q in keys_by_code[c].keys()}))
    
    # ── SHEET 1: BẢNG ĐÁP ÁN TỔNG HỢP ───────────────────────────────────────
    ws1 = wb.active
    ws1.title = "Bảng Đáp Án"
    ws1.views.sheetView[0].showGridLines = True
    
    # Tiêu đề lớn
    ws1.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(codes) + 1)
    title_cell = ws1.cell(row=1, column=1, value="BẢNG ĐÁP ÁN CÁC MÃ ĐỀ THI TRẮC NGHIỆM")
    title_cell.font = Font(name="Times New Roman", size=14, bold=True, color="1E3A8A")
    title_cell.alignment = align_center
    ws1.row_dimensions[1].height = 28
    
    # Header dòng 3
    ws1.row_dimensions[3].height = 24
    c_cau = ws1.cell(row=3, column=1, value="Câu")
    c_cau.font = font_header
    c_cau.fill = fill_header_navy
    c_cau.alignment = align_center
    c_cau.border = thin_border
    
    for c_idx, code in enumerate(codes, start=2):
        cell = ws1.cell(row=3, column=c_idx, value=f"Mã {code}")
        cell.font = font_header
        cell.fill = fill_header_navy
        cell.alignment = align_center
        cell.border = thin_border
        
    # Data rows
    for r_idx, q_num in enumerate(all_q_nums, start=4):
        ws1.row_dimensions[r_idx].height = 20
        c_q = ws1.cell(row=r_idx, column=1, value=q_num)
        c_q.font = font_bold
        c_q.alignment = align_center
        c_q.border = thin_border
        if (r_idx % 2) == 1:
            c_q.fill = fill_zebra
            
        for c_idx, code in enumerate(codes, start=2):
            ans = keys_by_code[code].get(q_num, "-")
            c_ans = ws1.cell(row=r_idx, column=c_idx, value=ans)
            c_ans.font = font_bold if ans != "-" else font_regular
            c_ans.alignment = align_center
            c_ans.border = thin_border
            if ans != "-":
                c_ans.fill = fill_highlight if (r_idx % 2 == 0) else fill_zebra
            elif (r_idx % 2) == 1:
                c_ans.fill = fill_zebra
                
    # ── SHEET 2: PHIẾU SOI CÂU (HOÁN VỊ CÂU HỎI) ───────────────────────────
    ws2 = wb.create_sheet(title="Phiếu Soi Câu (Hoán Vị)")
    ws2.views.sheetView[0].showGridLines = True
    
    ws2.merge_cells(start_row=1, start_column=1, end_row=1, end_column=5)
    t2 = ws2.cell(row=1, column=1, value="MA TRẬN HOÁN VỊ CÂU HỎI (PHIẾU SOI CÂU)")
    t2.font = Font(name="Times New Roman", size=14, bold=True, color="1E3A8A")
    t2.alignment = align_center
    ws2.row_dimensions[1].height = 28
    
    headers_s2 = ["Mã Đề", "Câu Mới", "Câu Gốc (Đề Gốc)", "Đáp Án Mã Này", "Đáp Án Đề Gốc"]
    ws2.row_dimensions[3].height = 24
    for col_idx, h_name in enumerate(headers_s2, start=1):
        cell = ws2.cell(row=3, column=col_idx, value=h_name)
        cell.font = font_header
        cell.fill = fill_header_blue
        cell.alignment = align_center
        cell.border = thin_border
        
    s2_row = 4
    if question_map_by_code:
        for code in codes:
            q_map = question_map_by_code.get(code, {})
            sorted_qs = sorted(q_map.keys())
            for q_new in sorted_qs:
                q_orig = q_map[q_new]
                ans_new = keys_by_code.get(code, {}).get(q_new, "-")
                ans_orig = (orig_keys or {}).get(q_orig, "-")
                
                ws2.row_dimensions[s2_row].height = 19
                cells = [
                    ws2.cell(row=s2_row, column=1, value=f"Mã {code}"),
                    ws2.cell(row=s2_row, column=2, value=f"Câu {q_new}"),
                    ws2.cell(row=s2_row, column=3, value=f"Câu {q_orig}"),
                    ws2.cell(row=s2_row, column=4, value=ans_new),
                    ws2.cell(row=s2_row, column=5, value=ans_orig),
                ]
                for c in cells:
                    c.font = font_regular
                    c.alignment = align_center
                    c.border = thin_border
                    if (s2_row % 2) == 1:
                        c.fill = fill_zebra
                cells[3].font = font_bold
                s2_row += 1
                
    # ── SHEET 3: CHI TIẾT HOÁN VỊ PHƯƠNG ÁN (NẾU CÓ) ──────────────────────
    if option_map_by_code:
        ws3 = wb.create_sheet(title="Hoán Vị Phương Án")
        ws3.views.sheetView[0].showGridLines = True
        
        ws3.merge_cells(start_row=1, start_column=1, end_row=1, end_column=7)
        t3 = ws3.cell(row=1, column=1, value="CHI TIẾT HOÁN VỊ CÁC PHƯƠNG ÁN A, B, C, D")
        t3.font = Font(name="Times New Roman", size=14, bold=True, color="1E3A8A")
        t3.alignment = align_center
        ws3.row_dimensions[1].height = 28
        
        headers_s3 = ["Mã Đề", "Câu Mới", "Câu Gốc", "Ý A là ý gốc", "Ý B là ý gốc", "Ý C là ý gốc", "Ý D là ý gốc"]
        ws3.row_dimensions[3].height = 24
        for col_idx, h_name in enumerate(headers_s3, start=1):
            cell = ws3.cell(row=3, column=col_idx, value=h_name)
            cell.font = font_header
            cell.fill = fill_header_navy
            cell.alignment = align_center
            cell.border = thin_border
            
        s3_row = 4
        for code in codes:
            opt_map_code = option_map_by_code.get(code, {})
            q_map = (question_map_by_code or {}).get(code, {})
            for q_new in sorted(opt_map_code.keys()):
                q_orig = q_map.get(q_new, q_new)
                perm = opt_map_code[q_new] # e.g. {'A': 'B', 'B': 'A', 'C': 'D', 'D': 'C'}
                ws3.row_dimensions[s3_row].height = 19
                cells = [
                    ws3.cell(row=s3_row, column=1, value=f"Mã {code}"),
                    ws3.cell(row=s3_row, column=2, value=f"Câu {q_new}"),
                    ws3.cell(row=s3_row, column=3, value=f"Câu {q_orig}"),
                    ws3.cell(row=s3_row, column=4, value=perm.get("A", "-")),
                    ws3.cell(row=s3_row, column=5, value=perm.get("B", "-")),
                    ws3.cell(row=s3_row, column=6, value=perm.get("C", "-")),
                    ws3.cell(row=s3_row, column=7, value=perm.get("D", "-")),
                ]
                for c in cells:
                    c.font = font_regular
                    c.alignment = align_center
                    c.border = thin_border
                    if (s3_row % 2) == 1:
                        c.fill = fill_zebra
                s3_row += 1

    # Tự động điều chỉnh độ rộng cột
    for ws in wb.worksheets:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                # Bỏ qua dòng tiêu đề merge ở row 1
                if cell.row == 1:
                    continue
                v_str = str(cell.value or "")
                if len(v_str) > max_len:
                    max_len = len(v_str)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)
            
    wb.save(filepath)
    return filepath


def export_consolidated_master_excel(
    filepath: str,
    exam_datasets: List[Dict[str, any]],
) -> str:
    """
    Xuất file Excel tổng hợp cho NHIỀU bộ đề thi đã trộn cùng lúc.
    Mỗi phần tử trong exam_datasets là 1 dict:
      {
          "name": str,
          "keys_by_code": Dict[str, Dict[int, str]],
          "question_map_by_code": Optional[Dict[str, Dict[int, int]]],
          "option_map_by_code": Optional[Dict[str, Dict[int, Dict[str, str]]]],
      }
    """
    wb = openpyxl.Workbook()

    font_header = Font(name="Times New Roman", size=11, bold=True, color="FFFFFF")
    font_bold = Font(name="Times New Roman", size=11, bold=True)
    font_regular = Font(name="Times New Roman", size=11)

    fill_header_navy = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    fill_header_blue = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
    fill_zebra = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    fill_highlight = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")

    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1")
    )
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")

    # ── SHEET 1: TỔNG QUAN TẤT CẢ CÁC BỘ ĐỀ ────────────────────────────────
    ws_main = wb.active
    ws_main.title = "Tổng Quan Các Bộ Đề"
    ws_main.views.sheetView[0].showGridLines = True

    ws_main.merge_cells(start_row=1, start_column=1, end_row=1, end_column=5)
    title_cell = ws_main.cell(row=1, column=1, value="BẢNG TỔNG HỢP CÁC BỘ ĐỀ THI ĐÃ TRỘN")
    title_cell.font = Font(name="Times New Roman", size=14, bold=True, color="1E3A8A")
    title_cell.alignment = align_center
    ws_main.row_dimensions[1].height = 28

    headers_main = ["STT", "Tên Bộ Đề Thi", "Số Câu Hỏi", "Số Mã Đề Đã Trộn", "Danh Sách Mã Đề"]
    ws_main.row_dimensions[3].height = 24
    for c_idx, h_name in enumerate(headers_main, start=1):
        c = ws_main.cell(row=3, column=c_idx, value=h_name)
        c.font = font_header
        c.fill = fill_header_navy
        c.alignment = align_center
        c.border = thin_border

    for idx, ds in enumerate(exam_datasets, start=1):
        row_num = 3 + idx
        ws_main.row_dimensions[row_num].height = 22
        k_by_code = ds.get("keys_by_code", {})
        codes = sorted(k_by_code.keys())
        all_qs = {q for c in codes for q in k_by_code[c].keys()}

        cells = [
            ws_main.cell(row=row_num, column=1, value=idx),
            ws_main.cell(row=row_num, column=2, value=ds.get("name", f"Bộ đề {idx}")),
            ws_main.cell(row=row_num, column=3, value=len(all_qs)),
            ws_main.cell(row=row_num, column=4, value=len(codes)),
            ws_main.cell(row=row_num, column=5, value=", ".join(codes)),
        ]
        for c in cells:
            c.font = font_regular
            c.border = thin_border
            if (row_num % 2) == 1:
                c.fill = fill_zebra
        cells[0].alignment = align_center
        cells[1].alignment = align_left
        cells[1].font = font_bold
        cells[2].alignment = align_center
        cells[3].alignment = align_center
        cells[4].alignment = align_center

    # ── SHEET CHO TỪNG BỘ ĐỀ ──────────────────────────────────────────────
    for idx, ds in enumerate(exam_datasets, start=1):
        name = ds.get("name", f"Bo_{idx}")
        keys_by_code = ds.get("keys_by_code", {})
        question_map_by_code = ds.get("question_map_by_code", {})
        codes = sorted(keys_by_code.keys())
        if not codes:
            continue

        all_q_nums = sorted(list({q for c in codes for q in keys_by_code[c].keys()}))

        # Sheet Đáp Án
        sheet_key_name = f"Bo_{idx:02d}_DapAn"[:31]
        ws_k = wb.create_sheet(title=sheet_key_name)
        ws_k.views.sheetView[0].showGridLines = True

        ws_k.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(codes) + 1)
        t_k = ws_k.cell(row=1, column=1, value=f"BẢNG ĐÁP ÁN: {name.upper()}")
        t_k.font = Font(name="Times New Roman", size=13, bold=True, color="1E3A8A")
        t_k.alignment = align_center
        ws_k.row_dimensions[1].height = 26

        ws_k.row_dimensions[3].height = 22
        c_q = ws_k.cell(row=3, column=1, value="Câu")
        c_q.font = font_header
        c_q.fill = fill_header_navy
        c_q.alignment = align_center
        c_q.border = thin_border

        for c_idx, code in enumerate(codes, start=2):
            cell = ws_k.cell(row=3, column=c_idx, value=f"Mã {code}")
            cell.font = font_header
            cell.fill = fill_header_navy
            cell.alignment = align_center
            cell.border = thin_border

        for r_idx, q_num in enumerate(all_q_nums, start=4):
            ws_k.row_dimensions[r_idx].height = 20
            cq = ws_k.cell(row=r_idx, column=1, value=q_num)
            cq.font = font_bold
            cq.alignment = align_center
            cq.border = thin_border
            if (r_idx % 2) == 1:
                cq.fill = fill_zebra

            for c_idx, code in enumerate(codes, start=2):
                ans = keys_by_code[code].get(q_num, "-")
                c_ans = ws_k.cell(row=r_idx, column=c_idx, value=ans)
                c_ans.font = font_bold if ans != "-" else font_regular
                c_ans.alignment = align_center
                c_ans.border = thin_border
                if ans != "-":
                    c_ans.fill = fill_highlight if (r_idx % 2 == 0) else fill_zebra
                elif (r_idx % 2) == 1:
                    c_ans.fill = fill_zebra

        # Sheet Phiếu Soi Câu
        sheet_map_name = f"Bo_{idx:02d}_SoiCau"[:31]
        ws_m = wb.create_sheet(title=sheet_map_name)
        ws_m.views.sheetView[0].showGridLines = True

        ws_m.merge_cells(start_row=1, start_column=1, end_row=1, end_column=4)
        t_m = ws_m.cell(row=1, column=1, value=f"PHIẾU SOI CÂU (HOÁN VỊ): {name.upper()}")
        t_m.font = Font(name="Times New Roman", size=13, bold=True, color="1E3A8A")
        t_m.alignment = align_center
        ws_m.row_dimensions[1].height = 26

        h_map = ["Mã Đề", "Câu Mới", "Câu Gốc", "Đáp Án Mã Này"]
        ws_m.row_dimensions[3].height = 22
        for c_idx, h_val in enumerate(h_map, start=1):
            cell = ws_m.cell(row=3, column=c_idx, value=h_val)
            cell.font = font_header
            cell.fill = fill_header_blue
            cell.alignment = align_center
            cell.border = thin_border

        s_row = 4
        if question_map_by_code:
            for code in codes:
                q_map = question_map_by_code.get(code, {})
                for q_new in sorted(q_map.keys()):
                    q_orig = q_map[q_new]
                    ans_new = keys_by_code.get(code, {}).get(q_new, "-")

                    ws_m.row_dimensions[s_row].height = 19
                    cells = [
                        ws_m.cell(row=s_row, column=1, value=f"Mã {code}"),
                        ws_m.cell(row=s_row, column=2, value=f"Câu {q_new}"),
                        ws_m.cell(row=s_row, column=3, value=f"Câu {q_orig}"),
                        ws_m.cell(row=s_row, column=4, value=ans_new),
                    ]
                    for c in cells:
                        c.font = font_regular
                        c.alignment = align_center
                        c.border = thin_border
                        if (s_row % 2) == 1:
                            c.fill = fill_zebra
                    cells[3].font = font_bold
                    s_row += 1

    # Tự động căn chỉnh độ rộng cột tất cả các sheets
    for ws in wb.worksheets:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.row == 1:
                    continue
                v_str = str(cell.value or "")
                if len(v_str) > max_len:
                    max_len = len(v_str)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    wb.save(filepath)
    return filepath

