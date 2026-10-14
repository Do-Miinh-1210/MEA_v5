import re
import xml.etree.ElementTree as ET
from pathlib import Path
import fitz
from PIL import Image, ImageDraw, ImageOps

def build_logos():
    root = Path(__file__).resolve().parent.parent
    svg_path = root / "Logonew.svg"
    assets_dir = root / "assets"
    csharp_assets = root / "desktop_csharp" / "src" / "MatrixExamAI.Desktop" / "Assets"
    csharp_assets.mkdir(parents=True, exist_ok=True)

    # 1. Render pure full SVG at high res (1024x1024)
    doc = fitz.open(str(svg_path))
    page = doc[0]
    # Native page is 2000x2000
    pix = page.get_pixmap(dpi=108) # 3000x3000
    temp_full = assets_dir / "temp_full.png"
    pix.save(str(temp_full))

    raw_img = Image.open(temp_full).convert("RGBA")
    
    # The character is primarily black (#000000) with white inner details (#ffffff).
    # Outside background is white (#ffffff).
    # Let's find the bounding box of all non-white pixels (the black character).
    w, h = raw_img.size
    pixels = raw_img.load()
    
    # Find bounding box of dark pixels
    min_x, min_y, max_x, max_y = w, h, 0, 0
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            r, g, b, a = pixels[x, y]
            # If pixel is significantly dark (part of the black mascot)
            if r < 100 and g < 100 and b < 100:
                if x < min_x: min_x = x
                if x > max_x: max_x = x
                if y < min_y: min_y = y
                if y > max_y: max_y = y

    print(f"Mascot bounds: ({min_x}, {min_y}) to ({max_x}, {max_y}), size: {max_x - min_x} x {max_y - min_y}")

    # Add 4% padding around character
    char_w = max_x - min_x
    char_h = max_y - min_y
    pad_x = int(char_w * 0.05)
    pad_y = int(char_h * 0.05)
    crop_box = (max(0, min_x - pad_x), max(0, min_y - pad_y), min(w, max_x + pad_x), min(h, max_y + pad_y))
    cropped = raw_img.crop(crop_box)

    # Create 2 versions:
    # Version 1: Modern Squircle Badge (Windows 11 / Apple style) - clean white background with rounded corners and subtle border
    target_size = 512
    badge = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    
    # Fit cropped mascot inside badge (with 15% inner margin)
    inner_size = int(target_size * 0.82)
    cropped_aspect = cropped.width / cropped.height
    if cropped_aspect > 1:
        new_w = inner_size
        new_h = int(inner_size / cropped_aspect)
    else:
        new_h = inner_size
        new_w = int(inner_size * cropped_aspect)
    
    scaled_mascot = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Draw rounded squircle background (smooth white card with subtle elegant dark border)
    corner_radius = 96
    bg_card = Image.new("RGBA", (target_size, target_size), (255, 255, 255, 255))
    mask = Image.new("L", (target_size, target_size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle([0, 0, target_size - 1, target_size - 1], radius=corner_radius, fill=255)
    
    # Create squircle badge with outline
    badge.paste(bg_card, (0, 0), mask)
    
    # Paste mascot centered inside squircle
    pos_x = (target_size - new_w) // 2
    pos_y = (target_size - new_h) // 2
    badge.paste(scaled_mascot, (pos_x, pos_y))

    # Add a subtle 2px rounded border for contrast on light backgrounds
    draw_badge = ImageDraw.Draw(badge)
    draw_badge.rounded_rectangle([1, 1, target_size - 2, target_size - 2], radius=corner_radius, outline=(220, 225, 230, 255), width=3)

    # Save squircle app icon
    badge.save(str(assets_dir / "app.png"), "PNG")
    badge.save(str(assets_dir / "logo.png"), "PNG")
    badge.save(str(assets_dir / "logo_main.png"), "PNG")
    badge.save(str(csharp_assets / "logo.png"), "PNG")

    # Multi-size ICO for Windows
    ico_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    badge.save(str(assets_dir / "app.ico"), format="ICO", sizes=ico_sizes)
    badge.save(str(assets_dir / "icon_app.ico"), format="ICO", sizes=ico_sizes)
    badge.save(str(csharp_assets / "app.ico"), format="ICO", sizes=ico_sizes)

    if temp_full.exists():
        temp_full.unlink()

    print("[SUCCESS] Modern squircle app.png and app.ico generated!")

if __name__ == "__main__":
    build_logos()
