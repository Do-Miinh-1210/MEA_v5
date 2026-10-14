import sys
from pathlib import Path
import pytest

from services.desktop_shortcut import (
    get_desktop_paths,
    get_primary_desktop,
    resolve_app_executable,
    resolve_app_icon,
    has_desktop_shortcut,
    create_desktop_shortcut,
    open_install_directory,
)


def test_get_desktop_paths():
    paths = get_desktop_paths()
    assert isinstance(paths, list)
    if sys.platform == "win32":
        assert len(paths) > 0


def test_get_primary_desktop():
    p = get_primary_desktop()
    assert isinstance(p, Path)
    assert p.name.lower() == "desktop"


def test_resolve_app_executable():
    exe, work_dir = resolve_app_executable()
    assert isinstance(exe, Path)
    assert isinstance(work_dir, Path)
    assert work_dir.exists()


def test_resolve_app_icon():
    _, work_dir = resolve_app_executable()
    icon = resolve_app_icon(work_dir)
    if icon is not None:
        assert isinstance(icon, Path)
        assert icon.suffix.lower() == ".ico"


def test_create_and_clean_desktop_shortcut():
    if sys.platform != "win32":
        pytest.skip("Windows only")

    test_name = "MEA_v5_Pytest_Check"
    desk = get_primary_desktop()
    test_lnk = desk / f"{test_name}.lnk"

    # Ensure clean state
    if test_lnk.exists():
        test_lnk.unlink()

    ok, msg = create_desktop_shortcut(shortcut_name=test_name)
    try:
        assert ok is True
        assert test_lnk.exists()
        assert has_desktop_shortcut(test_name) is True
    finally:
        if test_lnk.exists():
            test_lnk.unlink()
