"""Automated upgrade pipeline for MEA v4 and v5 desktop.

One command can now:
  1. Run release tests.
  2. Build EXE artifacts in a temp staging directory on a drive with space.
  3. Run EXE selftest before replacing dist artifacts.
  4. Deploy V4/V5 desktop artifacts and lightweight resources.
  5. Write updater-compatible release manifest JSON files.

Examples:
    python tools/upgrade_app.py --test-mode fast
    python tools/upgrade_app.py --target v5 --test-mode fast
    python tools/upgrade_app.py --skip-build --test-mode fast --manifest-only
    python tools/upgrade_app.py --download-url https://example.test/MEA_v4_Setup.exe
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DIST = ROOT / "dist"
APP_EXE = "MEA_v4.exe"
ADMIN_EXE = "MEA_v4_Admin.exe"
V5_EXE = "MEA_v5_alpha.exe"
V4_MANIFEST_NAME = "update_manifest_v4.json"
V5_MANIFEST_NAME = "update_manifest_v5.json"

FAST_TESTS = [
    "tests/test_updater.py",
    "tests/test_update_safety.py",
    "tests/test_v5_updater.py",
    "tests/test_v4_v5_tikz_vector_parity.py",
    "tests/test_v5_question_cards.py",
    "tests/test_exe_smoke.py",
    "tests/test_v5_release_readiness.py",
    "tests/test_upgrade_automation.py",
]


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _safe_rmtree(path: Path, *, within: Path) -> None:
    resolved = path.resolve()
    if not _is_relative_to(resolved, within.resolve()):
        raise RuntimeError(f"Refusing to delete outside {within}: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved, ignore_errors=True)


def _run(
    label: str,
    args: list[str],
    *,
    timeout: int | None = None,
    env: dict[str, str] | None = None,
) -> None:
    print(f"\n[{label}] {' '.join(args[:6])}")
    result = subprocess.run(args, cwd=str(ROOT), timeout=timeout, env=env)
    if result.returncode != 0:
        raise SystemExit(f"{label} failed with exit code {result.returncode}")


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _stage_root(value: str | None) -> Path:
    if value:
        root = Path(value).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        return root
    env_value = os.environ.get("MEA_BUILD_STAGE_DIR", "").strip()
    if env_value:
        root = Path(env_value).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        return root
    return Path(tempfile.mkdtemp(prefix="MEA_v4_upgrade_")).resolve()


def _run_tests(mode: str) -> None:
    if mode == "none":
        print("\n[tests] skipped")
        return
    cmd = [sys.executable, "-m", "pytest", "-q"]
    if mode == "fast":
        cmd += FAST_TESTS
    _run(f"tests:{mode}", cmd, timeout=600)


def _build_to_stage(stage: Path, *, build_admin: bool) -> Path:
    import build_helper

    stage_dist = stage / "dist"
    stage_work = stage / "work"
    _safe_rmtree(stage_dist, within=stage)
    _safe_rmtree(stage_work, within=stage)
    stage_dist.mkdir(parents=True, exist_ok=True)
    stage_work.mkdir(parents=True, exist_ok=True)

    old_dist = build_helper.DIST
    old_tmp = build_helper.BUILD_TMP
    build_helper.DIST = stage_dist
    build_helper.BUILD_TMP = stage_work

    print(f"\n[build] staging dist: {stage_dist}")
    print(f"[build] staging work: {stage_work}")

    build_helper.check_deps()
    disabled_hooks = build_helper._disable_kivy_hooks()
    try:
        ok_main = build_helper.build_app("main.py", APP_EXE[:-4], build_helper.ICON_MAIN)
        ok_admin = True
        if build_admin:
            ok_admin = build_helper.build_app("admin_tool.py", ADMIN_EXE[:-4], build_helper.ICON_ADMIN)
    finally:
        build_helper._restore_kivy_hooks(disabled_hooks)
        build_helper.DIST = old_dist
        build_helper.BUILD_TMP = old_tmp

    if not (ok_main and ok_admin):
        raise SystemExit("PyInstaller build failed")

    _copy_stage_resources(stage_dist)
    return stage_dist


def _build_v5_to_stage(stage: Path) -> Path:
    stage_dist = stage / "v5_dist"
    stage_work = stage / "MEA_v5_build_work"
    _safe_rmtree(stage_dist, within=stage)
    _safe_rmtree(stage_work, within=stage)
    stage_dist.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["MEA_V5_DIST"] = str(stage_dist)
    env["MEA_V5_BUILD_TMP"] = str(stage_work)

    print(f"\n[build:v5] staging dist: {stage_dist}")
    print(f"[build:v5] staging work: {stage_work}")
    _run(
        "build:v5",
        [sys.executable, str(ROOT / "build_v5_alpha.py")],
        timeout=1200,
        env=env,
    )
    if not (stage_dist / V5_EXE).exists():
        raise SystemExit(f"Missing V5 build artifact: {stage_dist / V5_EXE}")
    return stage_dist


def _copy_stage_resources(stage_dist: Path) -> None:
    """Copy release resources into the staging dist without writing installer.iss."""
    import build_helper

    old_dist = build_helper.DIST
    build_helper.DIST = stage_dist
    try:
        build_helper.copy_resources()
    finally:
        build_helper.DIST = old_dist


def _selftest(exe_path: Path) -> None:
    if not exe_path.exists():
        raise SystemExit(f"Missing EXE for selftest: {exe_path}")
    print(f"\n[selftest] {exe_path} --selftest")
    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    proc = subprocess.Popen(
        [str(exe_path), "--selftest"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startupinfo,
        creationflags=creationflags,
    )
    try:
        code = proc.wait(timeout=420)
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
        raise SystemExit(f"selftest timed out and was killed: {exe_path}")
    if code != 0:
        raise SystemExit(f"selftest failed with exit code {code}: {exe_path}")


def _deploy_from_stage(stage_dist: Path, *, build_admin: bool) -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    names = [APP_EXE]
    if build_admin:
        names.append(ADMIN_EXE)

    for name in names:
        src = stage_dist / name
        dst = DIST / name
        if not src.exists():
            raise SystemExit(f"Missing built artifact: {src}")
        if not _is_relative_to(dst, ROOT):
            raise RuntimeError(f"Unsafe deploy target: {dst}")
        if dst.exists():
            dst.unlink()
        shutil.copy2(src, dst)
        print(f"[deploy] {dst} ({dst.stat().st_size} bytes)")

    for name in ("config.py", ".env.template", "README.txt", "Chay MEA_v4.bat", "Chay Admin Tool.bat"):
        src = stage_dist / name
        if src.exists():
            shutil.copy2(src, DIST / name)

    for dirname in ("assets", "data"):
        src = stage_dist / dirname
        dst = DIST / dirname
        if src.exists():
            shutil.copytree(src, dst, dirs_exist_ok=True)


def _deploy_v5_from_stage(stage_dist: Path) -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    src = stage_dist / V5_EXE
    dst = DIST / V5_EXE
    if not src.exists():
        raise SystemExit(f"Missing built V5 artifact: {src}")
    if not _is_relative_to(dst, ROOT):
        raise RuntimeError(f"Unsafe deploy target: {dst}")
    if dst.exists():
        dst.unlink()
    shutil.copy2(src, dst)
    print(f"[deploy:v5] {dst} ({dst.stat().st_size} bytes)")


def _read_release_notes(version: str) -> str:
    path = ROOT / f"RELEASE_NOTES_v{version}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"MEA v{version}"


def _write_v4_manifest(*, download_url: str, min_version: str, mandatory: bool) -> Path:
    from config import APP_VERSION

    app_path = DIST / APP_EXE
    admin_path = DIST / ADMIN_EXE
    if not app_path.exists():
        raise SystemExit(f"Cannot create manifest; missing {app_path}")

    manifest = {
        "version": APP_VERSION,
        "tag_name": f"v{APP_VERSION}",
        "channel": "v4",
        "notes": _read_release_notes(APP_VERSION),
        "changelog": _read_release_notes(APP_VERSION),
        "download_url": download_url,
        "asset_name": Path(download_url).name if download_url else APP_EXE,
        "file_size": app_path.stat().st_size,
        "file_hash": f"sha256:{_sha256(app_path)}",
        "min_version": min_version,
        "is_mandatory": mandatory,
        "source": "release-manifest",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": {
            APP_EXE: {
                "size": app_path.stat().st_size,
                "sha256": _sha256(app_path),
            },
        },
    }
    if admin_path.exists():
        manifest["artifacts"][ADMIN_EXE] = {
            "size": admin_path.stat().st_size,
            "sha256": _sha256(admin_path),
        }

    output = DIST / V4_MANIFEST_NAME
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[manifest] {output}")
    if not download_url:
        print("[manifest] warning: download_url is empty; add it before publishing to an update endpoint.")
    return output


def _read_v5_release_notes(version: str) -> str:
    try:
        from v5.whats_new import CHANGELOG
    except Exception:
        return f"MEA v5 {version}"

    changes = CHANGELOG.get(version) or []
    if not changes:
        return f"MEA v5 {version}"

    lines = [f"# MEA v5 {version}", ""]
    for _icon, title, description in changes:
        lines.append(f"- {title}: {description}")
    return "\n".join(lines)


def _write_v5_manifest(*, download_url: str, min_version: str, mandatory: bool) -> Path:
    from v5 import __version__

    app_path = DIST / V5_EXE
    if not app_path.exists():
        raise SystemExit(f"Cannot create V5 manifest; missing {app_path}")

    notes = _read_v5_release_notes(__version__)
    manifest = {
        "version": __version__,
        "tag_name": f"v{__version__}",
        "channel": "v5",
        "notes": notes,
        "changelog": notes,
        "download_url": download_url,
        "asset_name": Path(download_url).name if download_url else V5_EXE,
        "file_size": app_path.stat().st_size,
        "file_hash": f"sha256:{_sha256(app_path)}",
        "min_version": min_version,
        "is_mandatory": mandatory,
        "source": "release-manifest-v5",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": {
            V5_EXE: {
                "size": app_path.stat().st_size,
                "sha256": _sha256(app_path),
            },
        },
    }

    output = DIST / V5_MANIFEST_NAME
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[manifest:v5] {output}")
    if not download_url:
        print("[manifest:v5] warning: download_url is empty; add it before publishing to an update endpoint.")
    return output


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the MEA V4/V5 automated upgrade pipeline.")
    parser.add_argument("--target", choices=("all", "v4", "v5"), default="all")
    parser.add_argument("--test-mode", choices=("full", "fast", "none"), default="full")
    parser.add_argument("--test-only", action="store_true", help="Only run tests without building or selftesting.")
    parser.add_argument("--skip-build", action="store_true", help="Reuse current dist EXE artifacts.")
    parser.add_argument("--manifest-only", action="store_true", help="Only write manifest after tests.")
    parser.add_argument("--stage-root", help="Staging folder. Defaults to a temp folder on the system drive.")
    parser.add_argument("--keep-stage", action="store_true", help="Keep staging files for inspection.")
    parser.add_argument("--skip-admin", action="store_true", help="Only build/deploy MEA_v4.exe.")
    parser.add_argument("--download-url", default="", help="Backward-compatible V4 public URL.")
    parser.add_argument("--download-url-v4", default="", help="Public URL for the V4 installer or EXE.")
    parser.add_argument("--download-url-v5", default="", help="Public URL for the V5 installer or EXE.")
    parser.add_argument("--min-version", default="", help="Backward-compatible V4 forced-update floor.")
    parser.add_argument("--min-version-v4", default="", help="Force V4 update when local version is below this.")
    parser.add_argument("--min-version-v5", default="", help="Force V5 update when local version is below this.")
    parser.add_argument("--mandatory", action="store_true", help="Mark selected manifests as mandatory.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    stage: Path | None = None
    want_v4 = args.target in {"all", "v4"}
    want_v5 = args.target in {"all", "v5"}
    try:
        _run_tests(args.test_mode)
        if args.test_only:
            print("\n[done] test run completed successfully")
            return 0

        if not args.skip_build and not args.manifest_only:
            stage = _stage_root(args.stage_root)
            if want_v4:
                stage_dist = _build_to_stage(stage, build_admin=not args.skip_admin)
                _selftest(stage_dist / APP_EXE)
                _deploy_from_stage(stage_dist, build_admin=not args.skip_admin)
                _selftest(DIST / APP_EXE)
            if want_v5:
                v5_stage_dist = _build_v5_to_stage(stage)
                _selftest(v5_stage_dist / V5_EXE)
                _deploy_v5_from_stage(v5_stage_dist)
                _selftest(DIST / V5_EXE)
        else:
            if want_v4:
                _selftest(DIST / APP_EXE)
            if want_v5:
                _selftest(DIST / V5_EXE)

        if want_v4:
            _write_v4_manifest(
                download_url=args.download_url_v4 or args.download_url,
                min_version=args.min_version_v4 or args.min_version,
                mandatory=args.mandatory,
            )
        if want_v5:
            _write_v5_manifest(
                download_url=args.download_url_v5,
                min_version=args.min_version_v5,
                mandatory=args.mandatory,
            )
        print("\n[done] upgrade automation finished successfully")
        return 0
    finally:
        if stage and not args.keep_stage:
            temp_parent = Path(tempfile.gettempdir()).resolve()
            if _is_relative_to(stage, temp_parent):
                _safe_rmtree(stage, within=temp_parent)


if __name__ == "__main__":
    raise SystemExit(main())
