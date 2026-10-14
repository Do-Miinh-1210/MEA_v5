"""
export/math_converter.py — LaTeX → OMML (Office Math Markup Language) converter.

Cho phép chèn công thức toán dạng MathType-compatible vào file Word.
Chain: LaTeX → MathML (via latex2mathml) → OMML (custom converter)
"""

from __future__ import annotations
import re
from typing import Optional

try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree as etree  # type: ignore


MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
MATHML_NS = "http://www.w3.org/1998/Math/MathML"
_MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
_V_NS = "urn:schemas-microsoft-com:vml"
_O_NS = "urn:schemas-microsoft-com:office:office"

_NSMAP = {"m": MATH_NS, "w": WORD_NS, "mc": _MC_NS, "v": _V_NS, "o": _O_NS}


def _mel(tag: str, text: str = "") -> etree.Element:
    """Create an element in the math namespace."""
    el = etree.Element(f"{{{MATH_NS}}}{tag}")
    if text:
        el.text = text
    return el


def _make_run(text: str, italic: bool = False) -> etree.Element:
    """Create an OMML math run <m:r><m:t>text</m:t></m:r>."""
    r = _mel("r")
    if italic:
        rPr = _mel("rPr")
        sty = _mel("sty")
        sty.set(f"{{{MATH_NS}}}val", "i")
        rPr.append(sty)
        r.append(rPr)
    t = _mel("t", text)
    # Preserve spaces
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    r.append(t)
    return r


def latex_to_omml(latex: str) -> Optional[etree.Element]:
    """Convert a LaTeX formula to an OMML <m:oMath> element.

    Returns None if conversion fails.
    """
    try:
        import latex2mathml.converter
        mathml_str = latex2mathml.converter.convert(latex)
        # Parse MathML
        mathml_root = etree.fromstring(mathml_str.encode("utf-8"))
        # Convert to OMML
        omath = _mel("oMath")
        _convert_mathml_to_omml(mathml_root, omath)
        return omath
    except Exception:
        return None


def _strip_ns(tag: str) -> str:
    """Remove namespace from XML tag."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _convert_mathml_to_omml(mathml_el, omml_parent):
    """Recursively convert MathML elements to OMML."""
    tag = _strip_ns(mathml_el.tag)

    if tag == "math":
        for child in mathml_el:
            _convert_mathml_to_omml(child, omml_parent)

    elif tag == "mrow":
        for child in mathml_el:
            _convert_mathml_to_omml(child, omml_parent)

    elif tag == "mi":
        # Identifier (variable) — italic
        text = (mathml_el.text or "").strip()
        if text:
            omml_parent.append(_make_run(text, italic=True))

    elif tag == "mn":
        # Number — regular
        text = (mathml_el.text or "").strip()
        if text:
            omml_parent.append(_make_run(text))

    elif tag == "mo":
        # Operator
        text = (mathml_el.text or "").strip()
        if text:
            omml_parent.append(_make_run(text))

    elif tag == "mtext":
        text = (mathml_el.text or "").strip()
        if text:
            omml_parent.append(_make_run(text))

    elif tag == "msup":
        # Superscript: <msup><base/><exp/></msup>
        children = list(mathml_el)
        if len(children) >= 2:
            ssup = _mel("sSup")
            # base
            e = _mel("e")
            _convert_mathml_to_omml(children[0], e)
            ssup.append(e)
            # superscript
            sup = _mel("sup")
            _convert_mathml_to_omml(children[1], sup)
            ssup.append(sup)
            omml_parent.append(ssup)

    elif tag == "msub":
        # Subscript: <msub><base/><sub/></msub>
        children = list(mathml_el)
        if len(children) >= 2:
            ssub = _mel("sSub")
            e = _mel("e")
            _convert_mathml_to_omml(children[0], e)
            ssub.append(e)
            sub = _mel("sub")
            _convert_mathml_to_omml(children[1], sub)
            ssub.append(sub)
            omml_parent.append(ssub)

    elif tag == "msubsup":
        # Combined sub+sup: <msubsup><base/><sub/><sup/></msubsup>
        children = list(mathml_el)
        if len(children) >= 3:
            sSubSup = _mel("sSubSup")
            e = _mel("e")
            _convert_mathml_to_omml(children[0], e)
            sSubSup.append(e)
            sub = _mel("sub")
            _convert_mathml_to_omml(children[1], sub)
            sSubSup.append(sub)
            sup = _mel("sup")
            _convert_mathml_to_omml(children[2], sup)
            sSubSup.append(sup)
            omml_parent.append(sSubSup)

    elif tag == "mfrac":
        # Fraction: <mfrac><num/><den/></mfrac>
        children = list(mathml_el)
        if len(children) >= 2:
            f = _mel("f")
            num = _mel("num")
            _convert_mathml_to_omml(children[0], num)
            f.append(num)
            den = _mel("den")
            _convert_mathml_to_omml(children[1], den)
            f.append(den)
            omml_parent.append(f)

    elif tag == "msqrt":
        # Square root
        rad = _mel("rad")
        radPr = _mel("radPr")
        degHide = _mel("degHide")
        degHide.set(f"{{{MATH_NS}}}val", "1")
        radPr.append(degHide)
        rad.append(radPr)
        deg = _mel("deg")
        rad.append(deg)
        e = _mel("e")
        for child in mathml_el:
            _convert_mathml_to_omml(child, e)
        rad.append(e)
        omml_parent.append(rad)

    elif tag == "mroot":
        # Nth root: <mroot><radicand/><index/></mroot>
        children = list(mathml_el)
        rad = _mel("rad")
        radPr = _mel("radPr")
        degHide = _mel("degHide")
        degHide.set(f"{{{MATH_NS}}}val", "0")
        radPr.append(degHide)
        rad.append(radPr)
        deg = _mel("deg")
        if len(children) >= 2:
            _convert_mathml_to_omml(children[1], deg)
        rad.append(deg)
        e = _mel("e")
        if children:
            _convert_mathml_to_omml(children[0], e)
        rad.append(e)
        omml_parent.append(rad)

    elif tag in ("mfenced", "mpadded", "mstyle", "merror", "mphantom"):
        # Container: recurse
        for child in mathml_el:
            _convert_mathml_to_omml(child, omml_parent)

    elif tag == "mtable":
        # Table/matrix — simplified: output as flat text
        for child in mathml_el:
            _convert_mathml_to_omml(child, omml_parent)

    elif tag in ("mtr", "mtd"):
        for child in mathml_el:
            _convert_mathml_to_omml(child, omml_parent)

    elif tag == "mover":
        # Overscript (e.g., vector arrow)
        children = list(mathml_el)
        if children:
            _convert_mathml_to_omml(children[0], omml_parent)

    elif tag == "munder":
        children = list(mathml_el)
        if children:
            _convert_mathml_to_omml(children[0], omml_parent)

    else:
        # Fallback: try to get text from all children
        text = mathml_el.text or ""
        if text.strip():
            omml_parent.append(_make_run(text.strip()))
        for child in mathml_el:
            _convert_mathml_to_omml(child, omml_parent)


def insert_math_in_paragraph(paragraph, latex: str) -> bool:
    """Insert an OMML equation into a docx paragraph.

    Returns True if OMML was inserted, False if fallback text was used.
    """
    omath = latex_to_omml(latex)
    if omath is not None:
        paragraph._p.append(omath)
        return True
    return False


def split_text_and_math(text: str):
    """Split text into alternating (plain_text, formula) segments.

    Returns list of (is_math: bool, content: str) tuples.
    """
    parts = []
    i = 0
    while i < len(text):
        if text[i] == '$':
            j = text.find('$', i + 1)
            if j == -1:
                parts.append((False, text[i:]))
                break
            parts.append((True, text[i + 1:j]))
            i = j + 1
        else:
            # Find next $
            j = text.find('$', i)
            if j == -1:
                parts.append((False, text[i:]))
                break
            parts.append((False, text[i:j]))
            i = j
    return parts


def omml_to_latex(elem) -> str:
    """Convert an OMML <m:oMath> element or sub-element to clean LaTeX representation."""
    if elem is None:
        return ""
    tag = _strip_ns(elem.tag)

    if tag in ("oMath", "oMathPara"):
        return "".join(omml_to_latex(c) for c in elem)

    elif tag == "r":
        # Math run
        texts = [t.text or "" for t in elem.findall(f".//{{{MATH_NS}}}t")]
        raw = "".join(texts)
        # Convert known unicode math symbols to LaTeX
        replacements = {
            "≤": r"\le ", "≥": r"\ge ", "≠": r"\ne ",
            "∈": r"\in ", "∉": r"\notin ", "⊂": r"\subset ",
            "∪": r"\cup ", "∩": r"\cap ", "∅": r"\emptyset ",
            "→": r"\to ", "⇒": r"\Rightarrow ", "⇔": r"\Leftrightarrow ",
            "∞": r"\infty ", "π": r"\pi ", "α": r"\alpha ", "β": r"\beta ",
            "Δ": r"\Delta ", "±": r"\pm ", "·": r"\cdot ", "×": r"\times ",
        }
        for u, ltx in replacements.items():
            raw = raw.replace(u, ltx)
        return raw

    elif tag == "f":
        # Fraction <m:f><m:num>...</m:num><m:den>...</m:den></m:f>
        num_el = elem.find(f"{{{MATH_NS}}}num")
        den_el = elem.find(f"{{{MATH_NS}}}den")
        num = "".join(omml_to_latex(c) for c in num_el) if num_el is not None else ""
        den = "".join(omml_to_latex(c) for c in den_el) if den_el is not None else ""
        return f"\\frac{{{num}}}{{{den}}}"

    elif tag == "sSup":
        # Superscript <m:sSup><m:e>...</m:e><m:sup>...</m:sup></m:sSup>
        e_el = elem.find(f"{{{MATH_NS}}}e")
        sup_el = elem.find(f"{{{MATH_NS}}}sup")
        e = "".join(omml_to_latex(c) for c in e_el) if e_el is not None else ""
        sup = "".join(omml_to_latex(c) for c in sup_el) if sup_el is not None else ""
        return f"{{{e}}}^{{{sup}}}"

    elif tag == "sSub":
        # Subscript <m:sSub><m:e>...</m:e><m:sub>...</m:sub></m:sSub>
        e_el = elem.find(f"{{{MATH_NS}}}e")
        sub_el = elem.find(f"{{{MATH_NS}}}sub")
        e = "".join(omml_to_latex(c) for c in e_el) if e_el is not None else ""
        sub = "".join(omml_to_latex(c) for c in sub_el) if sub_el is not None else ""
        return f"{{{e}}}_{{{sub}}}"

    elif tag == "sSubSup":
        e_el = elem.find(f"{{{MATH_NS}}}e")
        sub_el = elem.find(f"{{{MATH_NS}}}sub")
        sup_el = elem.find(f"{{{MATH_NS}}}sup")
        e = "".join(omml_to_latex(c) for c in e_el) if e_el is not None else ""
        sub = "".join(omml_to_latex(c) for c in sub_el) if sub_el is not None else ""
        sup = "".join(omml_to_latex(c) for c in sup_el) if sup_el is not None else ""
        return f"{{{e}}}_{{{sub}}}^{{{sup}}}"

    elif tag == "rad":
        # Radical <m:rad><m:radPr>...</m:radPr><m:deg>...</m:deg><m:e>...</m:e></m:rad>
        radPr = elem.find(f"{{{MATH_NS}}}radPr")
        deg_el = elem.find(f"{{{MATH_NS}}}deg")
        e_el = elem.find(f"{{{MATH_NS}}}e")
        e = "".join(omml_to_latex(c) for c in e_el) if e_el is not None else ""
        is_sqrt = False
        if radPr is not None:
            degHide = radPr.find(f"{{{MATH_NS}}}degHide")
            if degHide is not None and degHide.get(f"{{{MATH_NS}}}val") == "1":
                is_sqrt = True
        deg_text = "".join(omml_to_latex(c) for c in deg_el) if deg_el is not None else ""
        if is_sqrt or not deg_text.strip():
            return f"\\sqrt{{{e}}}"
        return f"\\sqrt[{deg_text}]{{{e}}}"

    elif tag == "d":
        # Delimiters <m:d><m:dPr>...</m:dPr><m:e>...</m:e></m:d>
        dPr = elem.find(f"{{{MATH_NS}}}dPr")
        beg = "("
        end = ")"
        if dPr is not None:
            beg_el = dPr.find(f"{{{MATH_NS}}}begChr")
            if beg_el is not None:
                beg = beg_el.get(f"{{{MATH_NS}}}val", "(")
            end_el = dPr.find(f"{{{MATH_NS}}}endChr")
            if end_el is not None:
                end = end_el.get(f"{{{MATH_NS}}}val", ")")
        e_list = elem.findall(f"{{{MATH_NS}}}e")
        parts = ["".join(omml_to_latex(c) for c in e_child) for e_child in e_list]
        inner = ", ".join(parts)
        beg_tex = r"\{" if beg == "{" else beg
        end_tex = r"\}" if end == "}" else end
        if beg_tex and end_tex:
            return f"\\left{beg_tex}{inner}\\right{end_tex}"
        elif beg_tex:
            return f"\\left{beg_tex}{inner}\\right."
        elif end_tex:
            return f"\\left.{inner}\\right{end_tex}"
        return inner

    elif tag == "bar":
        e_el = elem.find(f"{{{MATH_NS}}}e")
        e = "".join(omml_to_latex(c) for c in e_el) if e_el is not None else ""
        return f"\\overline{{{e}}}"

    elif tag == "limLow":
        e_el = elem.find(f"{{{MATH_NS}}}e")
        lim_el = elem.find(f"{{{MATH_NS}}}lim")
        e = "".join(omml_to_latex(c) for c in e_el) if e_el is not None else ""
        lim = "".join(omml_to_latex(c) for c in lim_el) if lim_el is not None else ""
        return f"{e}_{{{lim}}}"

    elif tag == "eqArr":
        e_list = elem.findall(f"{{{MATH_NS}}}e")
        rows = ["".join(omml_to_latex(c) for c in e_child) for e_child in e_list]
        return "\\begin{cases} " + " \\\\ ".join(rows) + " \\end{cases}"

    elif tag in ("m", "matrix"):
        rows_list = elem.findall(f".//{{{MATH_NS}}}mr")
        rows = []
        for r_elem in rows_list:
            cells = ["".join(omml_to_latex(c) for c in cell) for cell in r_elem.findall(f"{{{MATH_NS}}}e")]
            rows.append(" & ".join(cells))
        return "\\begin{matrix} " + " \\\\ ".join(rows) + " \\end{matrix}"

    elif tag in ("acc", "accent"):
        e_el = elem.find(f"{{{MATH_NS}}}e")
        e = "".join(omml_to_latex(c) for c in e_el) if e_el is not None else ""
        accPr = elem.find(f"{{{MATH_NS}}}accPr")
        chr_val = ""
        if accPr is not None:
            chr_el = accPr.find(f"{{{MATH_NS}}}chr")
            if chr_el is not None:
                chr_val = chr_el.get(f"{{{MATH_NS}}}val", "")
        if chr_val in ("\u20D7", "→"):
            return f"\\vec{{{e}}}"
        elif chr_val == "^":
            return f"\\hat{{{e}}}"
        return f"\\vec{{{e}}}"

    elif tag in ("e", "num", "den", "sup", "sub", "deg", "lim"):
        return "".join(omml_to_latex(c) for c in elem)

    elif tag in ("rPr", "pPr", "ctrlPr", "dPr", "radPr", "fPr"):
        return ""

    else:
        return "".join(omml_to_latex(c) for c in elem)


def extract_para_text_with_math(para) -> str:
    """Extract full text from a python-docx paragraph, converting OMML/MathType equations to LaTeX ${...}$
    and preserving tab stops (w:tab) and line breaks (w:br)."""
    parts = []

    def _process_element(elem):
        tag = _strip_ns(elem.tag)

        if tag == "r":
            for sub in elem:
                sub_tag = _strip_ns(sub.tag)
                if sub_tag == "t" and sub.text:
                    parts.append(sub.text)
                elif sub_tag == "tab":
                    parts.append("\t")
                elif sub_tag in ("br", "cr"):
                    parts.append("\n")
                elif sub_tag in ("oMathPara", "oMath"):
                    latex = omml_to_latex(sub)
                    if latex:
                        parts.append(f"${{{latex}}}$")
                elif sub_tag == "AlternateContent":
                    _process_alternate_content(sub)
                elif sub_tag == "object":
                    _process_object(sub)
        elif tag in ("oMathPara", "oMath"):
            latex = omml_to_latex(elem)
            if latex:
                parts.append(f"${{{latex}}}$")
        elif tag == "AlternateContent":
            _process_alternate_content(elem)
        elif tag == "hyperlink":
            for r_child in elem:
                _process_element(r_child)

    def _process_alternate_content(ac_elem):
        # MathType trong Word thường nằm trong AlternateContent (Choice chứa OLE, Fallback chứa OMML)
        omaths = ac_elem.xpath('.//m:oMath', namespaces=_NSMAP)
        if omaths:
            for om in omaths:
                latex = omml_to_latex(om)
                if latex:
                    parts.append(f"${{{latex}}}$")
        else:
            texts = ac_elem.xpath('.//w:t/text()', namespaces=_NSMAP)
            if texts:
                parts.append("".join(texts))

    def _process_object(obj_elem):
        # Kiểm tra title/alt của OLE MathType nếu có
        titles = obj_elem.xpath('.//@o:title | .//@alt', namespaces=_NSMAP)
        for t_val in titles:
            t_str = str(t_val).strip()
            if t_str and t_str != "Equation":
                parts.append(f"${{{t_str}}}$" if not t_str.startswith("$") else t_str)
                break

    for child in para._element:
        _process_element(child)

    return "".join(parts).strip()

