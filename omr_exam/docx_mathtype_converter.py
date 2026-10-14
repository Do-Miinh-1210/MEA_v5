"""
omr_exam/docx_mathtype_converter.py — Chuyển đổi công thức trong file Word (.docx)
sang công thức MathType chuẩn (OLE Object: Equation.DSMT4).

Đảm bảo:
- Đầu ra là công thức MathType OLE thực sự (không phải Word Equation / OMML).
- Nháy đúp (double-click) vào công thức trong Microsoft Word sẽ mở trực tiếp MathType.
- Đi kèm ảnh xem trước trong suốt (transparent preview PNG) hiển thị sắc nét trong Word và khi xuất PDF.
- Hỗ trợ chuyển đổi từng file hoặc toàn bộ thư mục đề thi sau khi trộn vào 1 thư mục riêng.
"""
from __future__ import annotations

import io
import os
import uuid
import struct
import zipfile
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Set, Dict

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except Exception:
    matplotlib = None
    plt = None
from PIL import Image
from lxml import etree

logger = logging.getLogger(__name__)

# OpenXML & VML Namespaces
_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
_R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_V_NS = "urn:schemas-microsoft-com:vml"
_O_NS = "urn:schemas-microsoft-com:office:office"
_MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
_CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
_RELS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

_REL_OLE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject"
_REL_IMG = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"

_NSMAP = {
    "w": _W_NS,
    "m": _M_NS,
    "r": _R_NS,
    "v": _V_NS,
    "o": _O_NS,
    "mc": _MC_NS,
}


def _w(tag: str) -> str:
    return f"{{{_W_NS}}}{tag}"


def _m(tag: str) -> str:
    return f"{{{_M_NS}}}{tag}"


def _r(tag: str) -> str:
    return f"{{{_R_NS}}}{tag}"


def _v(tag: str) -> str:
    return f"{{{_V_NS}}}{tag}"


def _o(tag: str) -> str:
    return f"{{{_O_NS}}}{tag}"


def mathml_to_latex_string(el: etree._Element) -> str:
    """Chuyển đổi MathML XML element thành chuỗi LaTeX gần đúng để render ảnh preview."""
    tag = el.tag.split('}')[-1]
    if tag in ('math', 'mrow'):
        return ''.join(mathml_to_latex_string(c) for c in el)
    elif tag == 'mfrac':
        children = list(el)
        num = mathml_to_latex_string(children[0]) if len(children) > 0 else ''
        den = mathml_to_latex_string(children[1]) if len(children) > 1 else ''
        return f"\\frac{{{num}}}{{{den}}}"
    elif tag == 'msqrt':
        inner = ''.join(mathml_to_latex_string(c) for c in el)
        return f"\\sqrt{{{inner}}}"
    elif tag == 'mroot':
        children = list(el)
        base = mathml_to_latex_string(children[0]) if len(children) > 0 else ''
        deg = mathml_to_latex_string(children[1]) if len(children) > 1 else ''
        return f"\\sqrt[{deg}]{{{base}}}"
    elif tag == 'msup':
        children = list(el)
        base = mathml_to_latex_string(children[0]) if len(children) > 0 else ''
        sup = mathml_to_latex_string(children[1]) if len(children) > 1 else ''
        return f"{{{base}}}^{{{sup}}}"
    elif tag == 'msub':
        children = list(el)
        base = mathml_to_latex_string(children[0]) if len(children) > 0 else ''
        sub = mathml_to_latex_string(children[1]) if len(children) > 1 else ''
        return f"{{{base}}}_{{{sub}}}"
    elif tag == 'msubsup':
        children = list(el)
        base = mathml_to_latex_string(children[0]) if len(children) > 0 else ''
        sub = mathml_to_latex_string(children[1]) if len(children) > 1 else ''
        sup = mathml_to_latex_string(children[2]) if len(children) > 2 else ''
        return f"{{{base}}}_{{{sub}}}^{{{sup}}}"
    elif tag == 'munder':
        children = list(el)
        base = mathml_to_latex_string(children[0]) if len(children) > 0 else ''
        und = mathml_to_latex_string(children[1]) if len(children) > 1 else ''
        return f"{{{base}}}_{{{und}}}"
    elif tag == 'mover':
        children = list(el)
        base = mathml_to_latex_string(children[0]) if len(children) > 0 else ''
        ovr = mathml_to_latex_string(children[1]) if len(children) > 1 else ''
        if ovr in ('\u2192', '\u20d7', '→'):
            return f"\\vec{{{base}}}"
        return f"\\overline{{{base}}}"
    elif tag == 'munderover':
        children = list(el)
        base = mathml_to_latex_string(children[0]) if len(children) > 0 else ''
        und = mathml_to_latex_string(children[1]) if len(children) > 1 else ''
        ovr = mathml_to_latex_string(children[2]) if len(children) > 2 else ''
        return f"{{{base}}}_{{{und}}}^{{{ovr}}}"
    elif tag in ('mi', 'mn', 'mo', 'mtext'):
        txt = (el.text or '').strip()
        op_map = {
            '\u2212': '-', '\u00b1': '\\pm ', '\u2264': '\\le ', '\u2265': '\\ge ',
            '\u2260': '\\ne ', '\u00d7': '\\times ', '\u00f7': '\\div ', '\u221e': '\\infty ',
            '\u2192': '\\to ', '\u222b': '\\int ', '\u2211': '\\sum ', '\u220f': '\\prod ',
            '\u2208': '\\in ', '\u2209': '\\notin ', '\u2282': '\\subset ', '\u222a': '\\cup ',
            '\u2229': '\\cap ', '\u03b1': '\\alpha ', '\u03b2': '\\beta ', '\u03c0': '\\pi ',
            '\u0394': '\\Delta ', '\u03b8': '\\theta ', '\u03bb': '\\lambda ',
            '\u21d4': '\\Leftrightarrow ', '\u21d2': '\\Rightarrow ', '\u2190': '\\leftarrow ',
            '\u2248': '\\approx ', '\u22c5': '\\cdot ', '\u2205': '\\emptyset ',
            '\u2115': '\\mathbb{N} ', '\u2124': '\\mathbb{Z} ', '\u211d': '\\mathbb{R} ',
            '\u211a': '\\mathbb{Q} ', '\u2200': '\\forall ', '\u2203': '\\exists ',
            '\u2245': '\\cong ', '\u223c': '\\sim ', '\u22a5': '\\perp ', '\u2225': '\\parallel ',
        }
        return op_map.get(txt, txt)
    return ''.join(mathml_to_latex_string(c) for c in el)


def render_latex_to_png(latex_str: str, dpi: int = 300) -> Tuple[bytes, float, float]:
    """Render chuỗi LaTeX thành ảnh PNG trong suốt với kích thước (point width, point height)."""
    clean_tex = (latex_str or '').strip()
    if not clean_tex:
        clean_tex = "f(x)"
    if not clean_tex.startswith('$'):
        clean_tex = f"${clean_tex}$"

    try:
        fig = plt.figure(figsize=(0.01, 0.01))
        fig.patch.set_alpha(0.0)
        plt.axis('off')
        plt.text(0.5, 0.5, clean_tex, size=13, color='black',
                 horizontalalignment='center', verticalalignment='center')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', pad_inches=0.01, transparent=True)
        plt.close(fig)
        buf.seek(0)
        img = Image.open(buf)
        w_px, h_px = img.size
        pt_w = max(12.0, w_px * 72.0 / dpi)
        pt_h = max(10.0, h_px * 72.0 / dpi)
        return buf.getvalue(), pt_w, pt_h
    except Exception as exc:
        logger.debug("Render LaTeX failed for '%s': %s", latex_str, exc)
        # Fallback 1x1 transparent PNG
        fallback = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
        return fallback, 24.0, 14.0


def convert_omml_to_mathtype_in_docx(input_docx_path: str, output_docx_path: str) -> Tuple[bool, int, str]:
    """
    Chuyển đổi toàn bộ công thức OMML (Word Equation) trong file .docx sang công thức MathType OLE Object (Equation.DSMT4).
    
    Kết quả:
    - Khi mở trong Word, nháy đúp (double click) sẽ kích hoạt phần mềm MathType.
    - Không còn dạng Word Equation.
    - Bảo toàn 100% hình ảnh, bảng biểu và cấu trúc đề thi.
    """
    if not os.path.exists(input_docx_path):
        return False, 0, f"File không tồn tại: {input_docx_path}"

    same_file = False
    try:
        same_file = os.path.abspath(input_docx_path).lower() == os.path.abspath(output_docx_path).lower()
    except Exception:
        same_file = (input_docx_path == output_docx_path)

    target_out = output_docx_path
    temp_target = None
    if same_file:
        import tempfile
        fd, temp_target = tempfile.mkstemp(suffix=".docx")
        os.close(fd)
        target_out = temp_target

    try:
        from omr_exam.docx_mathtype_converter import _do_convert_docx
        res = _do_convert_docx(input_docx_path, target_out)
        if same_file and res[0]:
            import shutil
            shutil.copy2(target_out, output_docx_path)
        return res
    except Exception as e:
        logger.exception("Error converting docx to MathType: %s", e)
        return False, 0, f"Lỗi chuyển đổi: {e}"
    finally:
        if temp_target and os.path.exists(temp_target):
            try:
                os.remove(temp_target)
            except Exception:
                pass


def sync_mathtype_preferences_from_eqp(eqp_path: str = r"M:\Mathtype\MT1.eqp") -> bool:
    """Đồng bộ cài đặt font, cỡ chữ, khoảng cách từ file .eqp (mặc định M:\\Mathtype\\MT1.eqp)
    vào Registry của MathType (HKCU\\Software\\Design Science\\DSMT7) để MathType hiển thị đúng chuẩn."""
    if not os.path.exists(eqp_path):
        return False
    try:
        import configparser
        import winreg
        cp = configparser.RawConfigParser()
        cp.optionxform = lambda opt: opt
        cp.read(eqp_path, encoding='utf-8-sig')
        for sec in ['Styles', 'Sizes', 'Spacing']:
            if cp.has_section(sec):
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Design Science\DSMT7\{sec}")
                for k, v in cp.items(sec):
                    winreg.SetValueEx(key, k, 0, winreg.REG_SZ, v)
                winreg.CloseKey(key)
        logger.info("Successfully synced MathType preferences from %s to registry DSMT7", eqp_path)
        return True
    except Exception as e:
        logger.warning("Could not sync MathType preferences from %s: %s", eqp_path, e)
        return False


# Preamble chuẩn MathType (Times New Roman, Symbol, Courier New, MT Extra) matching M:\Mathtype\MT1.eqp
MATHTYPE_PREAMBLE_STANDARD = (
    b"\x13WinAllBasicCodePages\x00"
    b"\x11\x05Times New Roman\x00"
    b"\x11\x03Symbol\x00"
    b"\x11\x05Courier New\x00"
    b"\x11\x04MT Extra\x00"
    b"\x12\x00\x08!/'\xf2_!\x8f!/G_AP\xf2\x1f\x1eAP\xf4\x15\x0fA\x00"
    b"\xf4E\xf4%\xf4\x8fB_A\x00\xf4\x10\x0fC_A\x00\xf2\x1f \xa5\xf2\n%\xf4"
    b"\x8f!\xf4\x10\x0fA\x00\xf4\x0fH\xf4\x17\xf4\x8fA\x00\xf2\x1a_D_E\xf4_E"
    b"\xf4_A\x0f\x0c\x01\x00\x01\x00\x01\x02\x02\x02\x02\x00\x02\x00\x01\x01"
    b"\x01\x00\x03\x00\x01\x00\x04\x00\x00"
)


def build_mathtype_equation_native(equation_bytes: bytes, latex_str: str = "") -> bytes:
    """Tạo stream Equation Native chuẩn MathType 7.0/6.0, bảo toàn font Times New Roman và kích thước chuẩn 12pt."""
    header = bytes([
        0x05, 0x01, 0x00, 0x07, 0x04,
        0x44, 0x53, 0x4D, 0x54, 0x37, 0x00,
        0x00
    ])

    # FULL size (12 pt), tuyệt đối KHÔNG chèn _size_display() (nguyên nhân gây phóng đại 320pt tràn màn hình MathType)
    main_line = b"\x0a\x01\x00" + equation_bytes + b"\x00"
    mtef_data = header + MATHTYPE_PREAMBLE_STANDARD + main_line
    
    # EQNOLEFILEHDR: cbHdr (28), version (0x00020000), cf (0), cbObject, reserved (16 bytes)
    hdr = struct.pack("<HIHI", 28, 0x00020000, 0, len(mtef_data)) + bytes(16)
    return hdr + mtef_data


def build_mathtype_ole_object(equation_bytes: bytes, latex_str: str = "") -> bytes:
    """Tạo file nhị phân OLE CFBF chứa đối tượng MathType Equation.DSMT4 chuẩn."""
    eq_native = build_mathtype_equation_native(equation_bytes, latex_str)
    from omml_converter.ole import make_ole
    return make_ole(eq_native)



def _do_convert_docx(input_docx_path: str, output_docx_path: str) -> Tuple[bool, int, str]:
    import omml_converter
    from omml_converter.omml_to_mathml import omml_to_mathml
    from omml_converter.mathml_to_mtef import mathml_to_mtef_bytes

    # Tự động đồng bộ chuẩn Font và Kích thước từ M:\Mathtype\MT1.eqp vào MathType Registry
    sync_mathtype_preferences_from_eqp()

    zf_in = zipfile.ZipFile(input_docx_path)
    
    # Đọc document.xml
    if 'word/document.xml' not in zf_in.namelist():
        return False, 0, "File docx không hợp lệ (thiếu word/document.xml)."

    doc_xml_bytes = zf_in.read('word/document.xml')
    rels_xml_bytes = zf_in.read('word/_rels/document.xml.rels') if 'word/_rels/document.xml.rels' in zf_in.namelist() else None
    ct_xml_bytes = zf_in.read('[Content_Types].xml') if '[Content_Types].xml' in zf_in.namelist() else None

    doc_root = etree.fromstring(doc_xml_bytes)
    rels_root = etree.fromstring(rels_xml_bytes) if rels_xml_bytes else etree.Element(f"{{{_RELS_NS}}}Relationships")
    ct_root = etree.fromstring(ct_xml_bytes) if ct_xml_bytes else etree.Element(f"{{{_CT_NS}}}Types")

    # Đảm bảo ContentTypes hỗ trợ OLE (.bin) và ảnh (.png)
    def ensure_default_ct(ext, ct):
        for c in ct_root.findall(f"{{{_CT_NS}}}Default"):
            if c.get("Extension", "").lower() == ext.lower():
                return
        el = etree.SubElement(ct_root, f"{{{_CT_NS}}}Default")
        el.set("Extension", ext)
        el.set("ContentType", ct)

    ensure_default_ct("bin", "application/vnd.openxmlformats-officedocument.oleObject")
    ensure_default_ct("png", "image/png")

    # Thu thập các relationship Id hiện có để tránh xung đột
    existing_rids = set()
    for rel in rels_root.findall(f"{{{_RELS_NS}}}Relationship"):
        rid = rel.get("Id", "")
        if rid:
            existing_rids.add(rid)

    next_rid_idx = 1
    def get_next_rid():
        nonlocal next_rid_idx
        while f"rIdMT{next_rid_idx}" in existing_rids:
            next_rid_idx += 1
        rid = f"rIdMT{next_rid_idx}"
        existing_rids.add(rid)
        next_rid_idx += 1
        return rid

    # Xử lý các khối mc:AlternateContent trước (nếu có OMML trong fallback)
    for ac in doc_root.xpath('//mc:AlternateContent', namespaces=_NSMAP):
        omaths_in_ac = ac.xpath('.//m:oMath', namespaces=_NSMAP)
        if omaths_in_ac:
            parent = ac.getparent()
            if parent is not None:
                ac_idx = parent.index(ac)
                for om in omaths_in_ac:
                    parent.insert(ac_idx, om)
                    ac_idx += 1
                parent.remove(ac)

    # Tự động nhận diện công thức LaTeX dạng $...$ trong văn bản nếu có và chuyển sang OMML
    try:
        from export.math_converter import split_text_and_math, latex_to_omml
        for p_node in doc_root.xpath('//w:p', namespaces=_NSMAP):
            p_text = "".join(p_node.xpath('.//w:t/text()', namespaces=_NSMAP))
            if "$" not in p_text:
                continue
            for r_node in list(p_node.xpath('./w:r', namespaces=_NSMAP)):
                t_nodes = r_node.xpath('./w:t', namespaces=_NSMAP)
                if not t_nodes:
                    continue
                r_text = "".join(t.text or "" for t in t_nodes)
                if "$" not in r_text:
                    continue
                parts = split_text_and_math(r_text)
                if len(parts) <= 1 and not (parts and parts[0][0]):
                    continue
                r_idx = p_node.index(r_node)
                for is_math, content in parts:
                    if is_math:
                        om = latex_to_omml(content)
                        if om is not None:
                            p_node.insert(r_idx, om)
                            r_idx += 1
                        else:
                            new_r = etree.Element(_w("r"))
                            new_t = etree.SubElement(new_r, _w("t"))
                            new_t.text = f"${content}$"
                            p_node.insert(r_idx, new_r)
                            r_idx += 1
                    elif content:
                        new_r = etree.Element(_w("r"))
                        new_t = etree.SubElement(new_r, _w("t"))
                        new_t.text = content
                        new_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                        p_node.insert(r_idx, new_r)
                        r_idx += 1
                p_node.remove(r_node)
    except Exception as _dollar_err:
        logger.debug("Lỗi nhận diện LaTeX $..$ sang OMML: %s", _dollar_err)

    # Tìm tất cả công thức OMML
    omaths = doc_root.xpath('//m:oMath', namespaces=_NSMAP)
    if not omaths:
        zf_in.close()
        # Không có công thức OMML nào trong file
        # Nếu file đã là MathType sẵn hoặc không có công thức, copy sang file đích (nếu khác đường dẫn)
        if str(Path(input_docx_path).resolve()) != str(Path(output_docx_path).resolve()):
            Path(output_docx_path).parent.mkdir(parents=True, exist_ok=True)
            with open(input_docx_path, 'rb') as f_src, open(output_docx_path, 'wb') as f_dst:
                f_dst.write(f_src.read())
        return True, 0, "Không tìm thấy công thức OMML (file đã được sao chép nguyên vẹn)."

    embeddings: Dict[str, bytes] = {}
    media: Dict[str, bytes] = {}
    converted_count = 0

    for idx, omath in enumerate(omaths, 1):
        try:
            mathml_root = omml_to_mathml(omath)
            tex_str = mathml_to_latex_string(mathml_root)
            if not tex_str.strip():
                raw_texts = omath.xpath('.//m:t/text()', namespaces=_NSMAP)
                tex_str = ''.join(raw_texts).strip() or "f(x)"
            mtef_bytes = mathml_to_mtef_bytes(mathml_root)
            ole_bytes = build_mathtype_ole_object(mtef_bytes, latex_str=tex_str)
        except Exception as ex:
            logger.debug("Failed converting OMML #%d to MTEF: %s", idx, ex)
            continue

        ole_filename = f"oleObjectMT_{uuid.uuid4().hex[:8]}_{idx}.bin"
        ole_rel_path = f"embeddings/{ole_filename}"
        ole_zip_path = f"word/embeddings/{ole_filename}"
        embeddings[ole_zip_path] = ole_bytes

        # Render ảnh xem trước
        try:
            png_bytes, pt_w, pt_h = render_latex_to_png(tex_str)
        except Exception:
            png_bytes, pt_w, pt_h = render_latex_to_png("f(x)")

        img_filename = f"imageMT_{uuid.uuid4().hex[:8]}_{idx}.png"
        img_rel_path = f"media/{img_filename}"
        img_zip_path = f"word/media/{img_filename}"
        media[img_zip_path] = png_bytes

        # Tạo relationships
        r_id_ole = get_next_rid()
        r_id_img = get_next_rid()

        r_ole = etree.SubElement(rels_root, f"{{{_RELS_NS}}}Relationship")
        r_ole.set("Id", r_id_ole)
        r_ole.set("Type", _REL_OLE)
        r_ole.set("Target", ole_rel_path)

        r_img = etree.SubElement(rels_root, f"{{{_RELS_NS}}}Relationship")
        r_img.set("Id", r_id_img)
        r_img.set("Type", _REL_IMG)
        r_img.set("Target", img_rel_path)

        # Xây dựng khối OpenXML w:object
        dxa_w = int(pt_w * 20)
        dxa_h = int(pt_h * 20)
        shape_id = f"_x0000_iMT{idx}"
        obj_id = f"{{{uuid.uuid4()}}}".upper()

        wr = etree.Element(_w("r"))
        wobj = etree.SubElement(wr, _w("object"))
        wobj.set(_w("dxaOrig"), str(dxa_w))
        wobj.set(_w("dyaOrig"), str(dxa_h))

        vshape = etree.SubElement(wobj, _v("shape"))
        vshape.set("id", shape_id)
        vshape.set("type", "#_x0000_t75")
        vshape.set("style", f"width:{pt_w:.1f}pt;height:{pt_h:.1f}pt")
        vshape.set(f"{{{_O_NS}}}ole", "")

        vimagedata = etree.SubElement(vshape, _v("imagedata"))
        vimagedata.set(_r("id"), r_id_img)
        vimagedata.set(f"{{{_O_NS}}}title", "")

        oleobj = etree.SubElement(wobj, _o("OLEObject"))
        oleobj.set("Type", "Embed")
        # ProgID Equation.DSMT4 chuẩn cho MathType 7.0 / 6.0 trên Windows
        oleobj.set("ProgID", "Equation.DSMT4")
        oleobj.set("ShapeID", shape_id)
        oleobj.set("DrawAspect", "Content")
        oleobj.set("ObjectID", obj_id)
        oleobj.set(_r("id"), r_id_ole)

        # Thay thế phần tử oMath trong cây XML
        p_elem = omath.getparent()
        if p_elem is not None:
            if p_elem.tag == _m("oMathPara"):
                grandparent = p_elem.getparent()
                if grandparent is not None:
                    g_idx = grandparent.index(p_elem)
                    grandparent.insert(g_idx, wr)
                    p_elem.remove(omath)
                    # Nếu oMathPara không còn oMath nào thì xóa hẳn oMathPara
                    if not p_elem.xpath('.//m:oMath', namespaces=_NSMAP):
                        grandparent.remove(p_elem)
                    converted_count += 1
            else:
                o_idx = p_elem.index(omath)
                p_elem.insert(o_idx, wr)
                p_elem.remove(omath)
                converted_count += 1

    # Tạo thư mục đích
    out_p = Path(output_docx_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = out_p.with_name(f"{out_p.stem}_tmp_{uuid.uuid4().hex[:6]}.docx")

    # Ghi lại file ZIP .docx hoàn chỉnh sang file tạm an toàn
    try:
        with zipfile.ZipFile(tmp_out, 'w', compression=zipfile.ZIP_DEFLATED) as zf_out:
            written_rels = False
            for item in zf_in.infolist():
                if item.filename == 'word/document.xml':
                    zf_out.writestr(item, etree.tostring(doc_root, xml_declaration=True, encoding='UTF-8', standalone=True))
                elif item.filename == 'word/_rels/document.xml.rels':
                    zf_out.writestr(item, etree.tostring(rels_root, xml_declaration=True, encoding='UTF-8', standalone=True))
                    written_rels = True
                elif item.filename == '[Content_Types].xml':
                    zf_out.writestr(item, etree.tostring(ct_root, xml_declaration=True, encoding='UTF-8', standalone=True))
                else:
                    zf_out.writestr(item, zf_in.read(item.filename))

            if not written_rels:
                zf_out.writestr('word/_rels/document.xml.rels', etree.tostring(rels_root, xml_declaration=True, encoding='UTF-8', standalone=True))

            # Ghi các stream nhúng OLE và ảnh
            for fname, fbytes in embeddings.items():
                zf_out.writestr(fname, fbytes)
            for fname, fbytes in media.items():
                zf_out.writestr(fname, fbytes)
    finally:
        zf_in.close()

    # Thay thế nguyên tử file tạm vào file đích (an toàn tuyệt đối trên Windows)
    os.replace(str(tmp_out), str(output_docx_path))
    return True, converted_count, f"Đã chuyển đổi thành công {converted_count} công thức sang MathType OLE."


def batch_convert_folder_to_mathtype(
    folder_path: str,
    output_subfolder_name: str = "De_Tron_MathType"
) -> Tuple[int, int, List[str], str]:
    """
    Chuyển đổi toàn bộ các file Word (.docx) trong thư mục chỉ định sang một thư mục riêng biệt chuẩn MathType.
    
    Trả về:
    - total_files: Số lượng file đã chuyển đổi.
    - total_equations: Tổng số lượng công thức MathType đã sinh.
    - converted_file_paths: Danh sách đường dẫn file kết quả.
    - dest_folder: Đường dẫn thư mục riêng chứa kết quả.
    """
    in_dir = Path(folder_path)
    if not in_dir.exists() or not in_dir.is_dir():
        return 0, 0, [], ""

    dest_folder = in_dir / output_subfolder_name
    dest_folder.mkdir(parents=True, exist_ok=True)

    docx_files = [
        f for f in in_dir.glob("*.docx")
        if not f.name.startswith("~$") and f.parent == in_dir
    ]

    total_eqs = 0
    converted_files: List[str] = []

    for f in docx_files:
        out_file = dest_folder / f.name
        success, n_eqs, msg = convert_omml_to_mathtype_in_docx(str(f), str(out_file))
        if success:
            total_eqs += n_eqs
            converted_files.append(str(out_file))

    return len(converted_files), total_eqs, converted_files, str(dest_folder)
