"""Tests for the V5-owned multi-image contract."""
from __future__ import annotations

from pathlib import Path

from v5 import image_fields


def test_normalize_image_field_accepts_legacy_and_list_values():
    assert image_fields.normalize_image_field(None) == []
    assert image_fields.normalize_image_field(" a.png | b.jpg ") == [
        "a.png",
        "b.jpg",
    ]
    assert image_fields.normalize_image_field(["a.png", "", Path("b.jpg")]) == [
        "a.png",
        "b.jpg",
    ]


def test_serialize_image_field_preserves_storage_contract():
    assert image_fields.serialize_image_field([]) == ""
    assert image_fields.serialize_image_field("existing.png") == "existing.png"
    assert image_fields.serialize_image_field(["a.png", "", "b.jpg"]) == (
        "a.png|b.jpg"
    )


def test_copy_to_images_dir_uses_v5_storage_path(monkeypatch, tmp_path):
    source = tmp_path / "input.jpg"
    source.write_bytes(b"question-image")
    image_dir = tmp_path / "stored"
    monkeypatch.setattr(image_fields, "IMAGES_DIR", image_dir)

    copied = image_fields.copy_to_images_dir(source)

    assert copied is not None
    output = Path(copied)
    assert output.parent == image_dir
    assert output.suffix == ".jpg"
    assert output.read_bytes() == b"question-image"

