from __future__ import annotations

from PIL import Image, ImageDraw

from services.image_precheck import analyze_image_quality, format_image_quality_warnings


def test_image_precheck_warns_for_small_low_contrast_image():
    img = Image.new("RGB", (320, 240), (128, 128, 128))

    report = analyze_image_quality(img, name="scan.png")

    assert report.ok is False
    assert report.confidence < 1.0
    assert any("ảnh nhỏ" in w for w in report.warnings)
    assert "scan.png" in format_image_quality_warnings([report])


def test_image_precheck_accepts_reasonable_text_like_scan():
    img = Image.new("RGB", (1400, 1000), "white")
    draw = ImageDraw.Draw(img)
    for y in range(80, 900, 80):
        draw.text((80, y), "Cau hoi 1. Tinh 1 + 1 = ?", fill="black")
        draw.line((80, y + 28, 900, y + 28), fill="black", width=2)

    report = analyze_image_quality(img, name="good.png")

    assert report.megapixels > 1.0
    assert report.confidence >= 0.5
    assert not any("ảnh nhỏ" in w for w in report.warnings)
