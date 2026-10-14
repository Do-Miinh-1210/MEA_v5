"""ui package — shared utilities."""
from pathlib import Path

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def set_dialog_icon(toplevel) -> None:
    """Set taskbar/title-bar icon for any Toplevel dialog.
    Tries app.ico → icon_app.ico, silently ignores errors.
    """
    try:
        import sys
        if getattr(sys, "frozen", False):
            base = Path(sys.executable).parent / "assets"
        else:
            base = _ASSETS_DIR
        for name in ("app.ico", "icon_app.ico"):
            ico = base / name
            if ico.exists():
                toplevel.iconbitmap(default=str(ico))
                break
    except Exception:
        pass
