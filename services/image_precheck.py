"""
services/image_precheck.py -- lightweight image quality checks before OCR/Vision.

The checks are intentionally local and cheap: resolution, contrast, brightness,
and edge detail. They do not block conversion; the UI uses the report to warn
users before spending AI calls on poor scans.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class ImageQualityReport:
    name: str = ""
    width: int = 0
    height: int = 0
    megapixels: float = 0.0
    brightness: float = 0.0
    contrast: float = 0.0
    edge_detail: float = 0.0
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.warnings

    @property
    def confidence(self) -> float:
        penalty = min(0.75, 0.16 * len(self.warnings))
        if self.megapixels < 0.25:
            penalty += 0.12
        return max(0.05, round(1.0 - penalty, 2))

    @property
    def size_label(self) -> str:
        return f"{self.width}x{self.height}px"


def _open_image(source):
    from PIL import Image

    if hasattr(source, "mode") and hasattr(source, "size"):
        return source.copy()
    if isinstance(source, (bytes, bytearray)):
        return Image.open(io.BytesIO(source))
    return Image.open(source)


def analyze_image_quality(source, *, name: str = "") -> ImageQualityReport:
    from PIL import ImageFilter, ImageStat

    img = _open_image(source)
    width, height = img.size
    report = ImageQualityReport(
        name=name or getattr(source, "name", "") or str(source),
        width=width,
        height=height,
        megapixels=round((width * height) / 1_000_000, 3),
    )

    gray = img.convert("L")
    if max(gray.size) > 900:
        gray.thumbnail((900, 900))

    stat = ImageStat.Stat(gray)
    report.brightness = round(float(stat.mean[0]), 2)
    report.contrast = round(float(stat.stddev[0]), 2)

    edge = gray.filter(ImageFilter.FIND_EDGES)
    edge_stat = ImageStat.Stat(edge)
    report.edge_detail = round(float(edge_stat.stddev[0]), 2)

    min_dim = min(width, height)
    if min_dim < 700 or report.megapixels < 0.6:
        report.warnings.append("ảnh nhỏ, OCR có thể mất công thức/chỉ số")
    if report.brightness < 45:
        report.warnings.append("ảnh quá tối")
    elif report.brightness > 235:
        report.warnings.append("ảnh quá sáng hoặc bị cháy nền")
    if report.contrast < 18:
        report.warnings.append("tương phản thấp, nên scan lại rõ hơn")
    if report.edge_detail < 8 and report.megapixels >= 0.6:
        report.warnings.append("nét/đường biên yếu, có thể bị mờ")
    if width / max(height, 1) > 4 or height / max(width, 1) > 4:
        report.warnings.append("tỉ lệ ảnh bất thường, nên crop lại vùng đề")

    return report


def analyze_many_images(paths: Iterable[str | Path]) -> list[ImageQualityReport]:
    reports: list[ImageQualityReport] = []
    for path in paths:
        p = Path(path)
        try:
            reports.append(analyze_image_quality(p, name=p.name))
        except Exception as exc:
            reports.append(ImageQualityReport(name=p.name, warnings=[f"không đọc được ảnh: {exc}"]))
    return reports


def format_image_quality_warnings(
    reports: Iterable[ImageQualityReport],
    *,
    max_items: int = 5,
) -> str:
    problem_reports = [r for r in reports if not r.ok]
    if not problem_reports:
        return ""

    lines = ["Cảnh báo chất lượng ảnh trước OCR:"]
    for report in problem_reports[:max_items]:
        warnings = "; ".join(report.warnings)
        name = report.name or "image"
        lines.append(
            f"- {name}: {report.size_label}, confidence {int(report.confidence * 100)}% - {warnings}"
        )
    if len(problem_reports) > max_items:
        lines.append(f"... và {len(problem_reports) - max_items} ảnh khác")
    return "\n".join(lines)
