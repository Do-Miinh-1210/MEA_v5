"""Build the optional C++ acceleration DLL used by MEA V5.

The runtime keeps a Python fallback, but release builds call this script before
PyInstaller so packaged EXEs always include the native backend.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "native" / "mea_native.cpp"
OUTPUT = ROOT / "native" / "bin" / "mea_native.dll"


def _find_zig() -> str | None:
    found = shutil.which("zig")
    if found:
        return found
    local_appdata = Path(os.environ.get("LOCALAPPDATA", ""))
    packages = local_appdata / "Microsoft" / "WinGet" / "Packages"
    matches = sorted(packages.glob("zig.zig_*/*/zig.exe"))
    return str(matches[-1]) if matches else None


def main() -> int:
    zig = _find_zig()
    if not zig:
        raise RuntimeError(
            "Không tìm thấy Zig compiler. Cài bằng: "
            "winget install --id zig.zig --exact --scope user"
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        zig, "c++", "-std=c++17", "-O3", "-shared",
        str(SOURCE), "-o", str(OUTPUT),
    ]
    print("Building native accelerator:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)
    print(f"Built: {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

