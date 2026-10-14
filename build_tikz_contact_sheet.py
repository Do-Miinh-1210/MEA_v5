"""
build_tikz_contact_sheet.py — Render TẤT CẢ 88 TikZ templates rồi ghép
thành 1 PNG contact sheet để user inspect visually.

Output: dist/tikz_kb_contact_sheet.png + dist/tikz_kb_pages/page_N.png

Cách dùng:
    python build_tikz_contact_sheet.py
    explorer dist\tikz_kb_contact_sheet.png

Nếu thấy hình nào sai → user chỉ ra tên template → fix.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, ".")

from services import tikz_kb
from services.tikz_pipeline import render_single

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass


COLS = 4               # 4 thumbnails per row
THUMB_W = 380          # px per thumbnail
THUMB_H = 280
PAD     = 16
NAME_H  = 32
PAGE_W  = COLS * (THUMB_W + PAD) + PAD
ROWS_PER_PAGE = 6      # 24 thumbnails/page
PAGE_H  = ROWS_PER_PAGE * (THUMB_H + NAME_H + PAD) + PAD + 60


def render_thumb(template, idx: int) -> "Image.Image":
    """Render template → PIL thumbnail (DPI 100 fit THUMB_W×THUMB_H)."""
    from PIL import Image, ImageDraw, ImageFont
    canvas = Image.new("RGB", (THUMB_W, THUMB_H + NAME_H), "white")
    draw = ImageDraw.Draw(canvas)
    try: font = ImageFont.truetype("seguiemj.ttf", 13)
    except Exception:
        try: font = ImageFont.truetype("arial.ttf", 13)
        except Exception: font = ImageFont.load_default()

    # Vẽ tên template trên đầu (max 2 dòng)
    name = template.name
    title = f"[{idx+1}] {name[:50]}"
    draw.text((6, 4), title, fill="#1F2937", font=font)

    # Render TikZ
    try:
        png_path, err = render_single(template.code, dpi=100)
        if png_path and not err:
            img = Image.open(png_path)
            # Fit vào THUMB_W × THUMB_H
            iw, ih = img.size
            scale = min((THUMB_W - 8) / iw, (THUMB_H - 8) / ih, 1.0)
            new_w, new_h = int(iw * scale), int(ih * scale)
            img_resized = img.resize((new_w, new_h), Image.LANCZOS)
            # Paste vào giữa
            ox = (THUMB_W - new_w) // 2
            oy = NAME_H + (THUMB_H - new_h) // 2
            canvas.paste(img_resized, (ox, oy))
        else:
            err_text = (err or "render fail")[:60]
            draw.rectangle((4, NAME_H + 4, THUMB_W - 4, THUMB_H + NAME_H - 4),
                             outline="#DC2626", width=2)
            draw.text((20, NAME_H + 40), f"✘ ERROR\n{err_text}",
                        fill="#DC2626", font=font)
    except Exception as e:
        draw.text((20, NAME_H + 40), f"✘ EXCEPTION\n{str(e)[:60]}",
                    fill="#DC2626", font=font)

    # Viền
    draw.rectangle((0, 0, THUMB_W - 1, THUMB_H + NAME_H - 1),
                     outline="#94A3B8", width=1)
    return canvas


def build_page(thumbs: list, page_num: int, total_pages: int) -> "Image.Image":
    from PIL import Image, ImageDraw, ImageFont
    page = Image.new("RGB", (PAGE_W, PAGE_H), "#F8FAFC")
    draw = ImageDraw.Draw(page)
    try: font_big = ImageFont.truetype("arial.ttf", 22)
    except Exception: font_big = ImageFont.load_default()
    # Header
    title = f"MEA v5 — Kho TikZ ({len(thumbs)} templates)   "\
             f"Trang {page_num}/{total_pages}"
    draw.text((PAD, 18), title, fill="#1F497D", font=font_big)
    # Paste thumbs
    for i, th in enumerate(thumbs):
        row, col = i // COLS, i % COLS
        x = PAD + col * (THUMB_W + PAD)
        y = 60 + row * (THUMB_H + NAME_H + PAD)
        page.paste(th, (x, y))
    return page


def main():
    print("=" * 60)
    print("  TIKZ KB CONTACT SHEET BUILDER")
    print("=" * 60)
    tikz_kb._LOADED = False
    tikz_kb.load()
    templates = tikz_kb.all_templates()
    print(f"  Tổng: {len(templates)} templates")
    print(f"  Layout: {COLS} cols × {ROWS_PER_PAGE} rows = "
          f"{COLS * ROWS_PER_PAGE} per page")

    out_dir = Path("dist/tikz_kb_pages")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Render tất cả thumbs
    thumbs = []
    for i, t in enumerate(templates):
        print(f"  [{i+1:>3}/{len(templates)}] {t.name[:60]}", end="\r",
                flush=True)
        thumbs.append(render_thumb(t, i))
    print()

    # Chia thành pages
    per_page = COLS * ROWS_PER_PAGE
    total_pages = (len(thumbs) + per_page - 1) // per_page
    pages = []
    for p in range(total_pages):
        page_thumbs = thumbs[p * per_page : (p + 1) * per_page]
        page = build_page(page_thumbs, p + 1, total_pages)
        out_path = out_dir / f"page_{p+1:02d}.png"
        page.save(out_path)
        print(f"  ✓ Saved {out_path}")
        pages.append(page)

    # Cũng tạo 1 ảnh COMBINED tổng (cao toàn bộ)
    from PIL import Image
    combined_h = sum(p.height for p in pages) + (len(pages) - 1) * PAD
    combined = Image.new("RGB", (PAGE_W, combined_h), "#F8FAFC")
    cy = 0
    for p in pages:
        combined.paste(p, (0, cy))
        cy += p.height + PAD
    combined_path = Path("dist/tikz_kb_contact_sheet.png")
    combined.save(combined_path)
    print(f"\n  ✓ Combined: {combined_path}  ({PAGE_W}×{combined_h})")

    # In list templates để user copy tên cái sai
    print()
    print("─" * 60)
    print("  DANH SÁCH 88 TEMPLATES (để user chỉ tên cái sai):")
    print("─" * 60)
    from collections import defaultdict
    by_src = defaultdict(list)
    for t in templates:
        src = Path(t.source).stem
        by_src[src].append(t.name)
    for src, names in by_src.items():
        print(f"\n  [{src}]")
        for n in names:
            print(f"    • {n}")


if __name__ == "__main__":
    main()
