"""
build_helper.py — MEA v4.2.2
Build script: PyInstaller + Inno Setup installer.
Chay: python build_helper.py

Output:
  dist/MEA_v4.exe           — App chinh tao de kiem tra
  dist/MEA_v4_Admin.exe     — Admin tool quan ly license
  installer.iss             — Inno Setup script

Doi voi v4.2.2, build script tu dong:
  - Bundle services/latex_engine.py (auto-detect pdflatex/xelatex/tectonic)
  - Bundle data/tikz_kb/ (kho mau hinh TikZ, da fix loi calc trong "right angle pic")
  - PyInstaller modulegraph tu dong include moi module trong services/, ui/, core/
"""
import subprocess
import sys
import os
import shutil
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SRC       = Path(__file__).parent.resolve()
DIST      = SRC / "dist"
BUILD_TMP = SRC / "build_temp"
ASSETS    = SRC / "assets"

# Icon: app.ico cho app AI, icon3.ico cho Admin
ICON_MAIN  = ASSETS / "app.ico" if (ASSETS / "app.ico").exists() else ASSETS / "icon3.ico"
ICON_ADMIN = ASSETS / "icon3.ico"

from config import APP_VERSION


def run(cmd: list, label: str) -> bool:
    print(f"\n  [{label}] {' '.join(str(c) for c in cmd[:5])} ...")
    result = subprocess.run(cmd, cwd=str(SRC))
    if result.returncode != 0:
        print(f"  [ERROR] {label} failed (code {result.returncode})")
        return False
    print(f"  [OK] {label} done.")
    return True


def _disable_kivy_hooks():
    """Tạm ẩn kivy hook directories để PyInstaller không scan chúng."""
    import importlib.util
    disabled = []
    for pkg in ("kivymd", "kivy"):
        spec = importlib.util.find_spec(pkg)
        if spec and spec.submodule_search_locations:
            for loc in spec.submodule_search_locations:
                hook_dir = Path(loc) / "tools" / "packaging" / "pyinstaller"
                if hook_dir.exists():
                    renamed = hook_dir.with_name("_pyinstaller_disabled")
                    if not renamed.exists():
                        hook_dir.rename(renamed)
                        disabled.append((renamed, hook_dir))
                        print(f"  [HOOK] Disabled: {hook_dir.name} in {pkg}")
    return disabled


def _restore_kivy_hooks(disabled: list):
    """Khôi phục kivy hook directories sau build."""
    for renamed, original in disabled:
        if renamed.exists() and not original.exists():
            renamed.rename(original)
            print(f"  [HOOK] Restored: {original.name}")


def _generate_spec(script: str, name: str, icon_path: Path) -> Path:
    """Generate a .spec file with full control over Analysis excludes."""
    sep = ";" if sys.platform == "win32" else ":"

    # Tìm certifi CA bundle để đóng gói (cần cho SSL/HTTPS)
    certifi_data = ""
    try:
        import certifi
        cacert = Path(certifi.where())
        certifi_data = f"(r'{cacert.parent}', 'certifi')"
    except ImportError:
        pass

    datas = [f"(r'{ASSETS}', 'assets')"]
    if certifi_data:
        datas.append(certifi_data)
    if (SRC / 'storage').exists():
        datas.append(f"(r'{SRC / 'storage'}', 'storage')")
    if (SRC / 'data').exists():
        datas.append(f"(r'{SRC / 'data'}', 'data')")
    if (SRC / 'Prompt Chatbot').exists():
        datas.append(f"(r'{SRC / 'Prompt Chatbot'}', 'Prompt Chatbot')")
    if (SRC / 'native').exists():
        datas.append(f"(r'{SRC / 'native'}', 'native')")

    icon_line = ""
    if sys.platform == "win32" and icon_path.exists() and icon_path.suffix == ".ico":
        icon_line = f"icon=r'{icon_path}',"

    manifest_line = ""
    manifest = SRC / "app.manifest"
    if manifest.exists():
        manifest_line = f"manifest=r'{manifest}',"

    upx_dir = shutil.which("upx")
    upx_line = f"upx_dir=r'{Path(upx_dir).parent}'," if upx_dir else ""
    noupx = "False" if upx_dir else "True"

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
import sys
sys.setrecursionlimit(200000)

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
certifi_datas = collect_data_files('certifi')

# Gom submodules cho các SDK hay bị bỏ sót (lazy imports, __getattr__ modules)
_sdk_hidden: list[str] = []
for _sdk in (
    'anthropic', 'openai',
    'google.genai', 'google.auth',
    'supabase', 'postgrest', 'storage3', 'gotrue', 'realtime',
    'httpx', 'httpcore', 'pydantic', 'pydantic_core',
    'omr_exam', 'openpyxl',
):
    try:
        _sdk_hidden += collect_submodules(_sdk)
    except Exception:
        pass

# Gom datas (cacert, schemas, templates) cho các SDK cần file tài nguyên
_sdk_datas: list = []
for _sdk_d in ('certifi', 'anthropic', 'openai', 'supabase', 'google.genai'):
    try:
        _sdk_datas += collect_data_files(_sdk_d)
    except Exception:
        pass

a = Analysis(
    [r'{SRC / script}'],
    pathex=[r'{SRC}'],
    binaries=[],
    datas=[{', '.join(datas)}] + certifi_datas + _sdk_datas,
    hiddenimports=[
        # Tkinter
        'tkinter', 'tkinter.ttk', 'tkinter.scrolledtext',
        'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.font',
        # Database & Crypto
        'sqlite3', 'cryptography', 'cryptography.fernet',
        'cryptography.hazmat.primitives',
        # Image
        'PIL', 'PIL.Image', 'PIL.ImageTk', 'PIL.PngImagePlugin',
        'PIL.ImageGrab',
        # AI Providers — base modules (collect_submodules handles full tree)
        'google.genai', 'google.genai.types', 'google.genai.client',
        'google.genai.models', 'google.genai._common',
        'google.auth', 'google.auth.transport.requests',
        'anthropic', 'anthropic._client', 'anthropic.types', 'anthropic.resources',
        'openai', 'openai._client',
        # Document processing (Word + PDF reading)
        'docx', 'docx.shared',
        'docx.enum.text', 'docx.enum.table',
        'docx.oxml', 'docx.oxml.ns',
        'docx.table', 'docx.text.paragraph',
        'lxml', 'lxml.etree', 'xml.etree.ElementTree',
        'mammoth',                        # .docx -> HTML (parser.py, doc_question_parser.py)
        'pdfplumber',                     # PDF reading (exam_parser/loader, doc_question_parser)
        # Network
        'requests', 'certifi', 'charset_normalizer',
        # Stdlib
        'json', 'pathlib', 'threading', 'logging', 'typing_extensions',
        # LaTeX & PDF rendering
        'latex2mathml', 'latex2mathml.converter',
        'fitz', 'pymupdf',                # PyMuPDF (tab_tikz, tab_result, pdf_image_extractor)
        # Supabase + transitive deps (license_manager + admin_tool)
        'supabase', 'postgrest', 'storage3',
        'gotrue', 'realtime',
        'httpx', 'httpx._transports', 'httpx._transports.default',
        'httpcore', 'httpcore._async', 'httpcore._sync',
        'h11', 'h2', 'hpack',
        'anyio', 'anyio._backends', 'anyio._backends._asyncio',
        'sniffio',
        'websockets', 'websockets.client',
        # Pydantic (used by supabase/openai/anthropic)
        'pydantic', 'pydantic.fields', 'pydantic_core',
        'annotated_types',
        # OMR & Excel shuffling
        'openpyxl', 'openpyxl.styles', 'openpyxl.utils',
        'omr_exam', 'omr_exam.models', 'omr_exam.docx_parser',
        'omr_exam.exam_shuffler', 'omr_exam.docx_exporter',
        'omr_exam.excel_exporter', 'omr_exam.docx_shuffler_xml',
        # Transitive deps of storage3/supabase
        'pyparsing', 'pyiceberg',
    ] + _sdk_hidden,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'scipy', 'pandas',
        'notebook', 'jupyter', 'IPython',
        'pytest', 'setuptools', 'pip', 'wheel',
        'test', 'tkinter.test', 'email.test', 'lib2to3',
        'kivy', 'kivymd', 'kivy_deps',
        'kivy_deps.angle', 'kivy_deps.glew', 'kivy_deps.sdl2',
        'google.generativeai', 'google.cloud',
        'grpc', 'grpcio',
        # Heavy transitive deps
        'boto3', 'botocore', 'tensorflow', 'torch', 'transformers',
        'cv2', 'sklearn', 'skimage',
        # sympy has deeply circular imports that crash modulegraph
        # (used optionally in quality_pipeline.py with try/except)
        'sympy',
        # Modules deprecated/removed trong v4.2 (audit 5/2026, 0 imports)
        'core.controller', 'core.tagging',
        # v5 desktop deps — KHÔNG bundle vào v4 EXE (v4 chỉ Tkinter,
        # không cần CTk + matplotlib + tkinterdnd2)
        'customtkinter', 'tkinterdnd2', 'v5',
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='{name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx={not noupx == "True"},
    {upx_line}
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    {icon_line}
    {manifest_line}
)
'''

    spec_path = BUILD_TMP / f"{name}.spec"
    BUILD_TMP.mkdir(exist_ok=True)
    spec_path.write_text(spec_content, encoding="utf-8")
    print(f"  [SPEC] Generated: {spec_path}")
    return spec_path


def build_app(script: str, name: str, icon_path: Path) -> bool:
    spec_path = _generate_spec(script, name, icon_path)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        f"--distpath={DIST}",
        f"--workpath={BUILD_TMP / name}",
        str(spec_path),
    ]

    return run(cmd, f"Build {name}")


def _safe_copy_tree(src: Path, dst: Path):
    dst.mkdir(parents=True, exist_ok=True)
    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        target_dir = dst / rel
        target_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            src_file = Path(root) / f
            dst_file = target_dir / f
            try:
                shutil.copy2(src_file, dst_file)
            except Exception as e:
                print(f"  [WARN] Khong the ghi de {dst_file.name}: {e}")


def copy_resources():
    print("\n  [COPY] Sao chep tai nguyen vao dist/ ...")
    DIST.mkdir(exist_ok=True)

    # assets/
    _safe_copy_tree(ASSETS, DIST / "assets")

    # data/
    src_data = SRC / "data"
    if src_data.exists():
        _safe_copy_tree(src_data, DIST / "data")

    # config.py
    shutil.copy2(str(SRC / "config.py"), str(DIST / "config.py"))

    # .env.template — luon dong goi (an toan, khong chua secret)
    env_template = SRC / ".env.template"
    if env_template.exists():
        shutil.copy2(str(env_template), str(DIST / ".env.template"))
        print("  [OK] .env.template da sao chep vao dist/.")
    else:
        print("  [!] Khong tim thay .env.template — bo qua.")

    # .env — chi dong goi khi BUILD_INCLUDE_ENV=1.
    # Mac dinh KHONG dong goi de tranh lo secret khi phat hanh portable zip.
    env_file = SRC / ".env"
    include_env = os.environ.get("BUILD_INCLUDE_ENV", "").strip().lower() in {"1", "true", "yes"}
    if include_env and env_file.exists():
        shutil.copy2(str(env_file), str(DIST / ".env"))
        print("  [OK] .env da sao chep vao dist/ (BUILD_INCLUDE_ENV=1).")
    elif env_file.exists():
        print("  [SKIP] .env ton tai nhung KHONG sao chep vao dist/ "
              "(set BUILD_INCLUDE_ENV=1 truoc khi build de bao gom .env).")
    else:
        print("  [!] Khong tim thay .env — EXE se dung API Keys mac dinh trong config.py.")

    # Thu muc can thiet khi chay
    for d in ("storage", "sessions", "logs"):
        (DIST / d).mkdir(exist_ok=True)

    # README
    (DIST / "README.txt").write_text(
        f"MEA v{APP_VERSION} — Tao de kiem tra bang AI (da mon)\n"
        f"{'=' * 50}\n\n"
        "1. Chay MEA_v4.exe           -> App chinh tao de kiem tra\n"
        "2. Chay MEA_v4_Admin.exe     -> Quan ly license (admin)\n\n"
        "Tinh nang chinh:\n"
        "  - Tao de kiem tra da mon (Toan, Ly, Hoa, Sinh, Van, Anh, Su, Dia...)\n"
        "  - Ho tro TN, Dung-Sai, Tra loi ngan, Tu luan\n"
        "  - TikZ ve hinh toan hoc + AI ve hinh tu dong (Gemini Vision)\n"
        "  - Kiem tra chat luong, ngan hang cau hoi\n"
        "  - Xuat Word / nhieu ma de\n\n"
        f"Moi trong v{APP_VERSION}:\n"
        "  - TikZ -> EMF trong tab Xem de, giu PNG preview va EMF vector cho Word\n"
        "  - V4/V5 dung chung workflow vector de khong lech tinh nang\n"
        "  - Multi-engine LaTeX: tu dong dung pdflatex / xelatex / tectonic\n"
        "    (config LATEX_ENGINE_PREFERENCE de doi engine)\n"
        "  - Zoom/pan ke ben anh trong dialog 'Chon mau hinh tu kho'\n"
        "    (Ctrl+Wheel = zoom, Keo chuot = di chuyen)\n"
        "  - Hien thi thoi gian phan tich anh AI real-time\n"
        "  - Sua loi crash khi bam 'Xac nhan ve' tren Python 3.12\n\n"
        "Yeu cau he thong:\n"
        "  - Windows 10/11\n"
        "  - LaTeX engine (chon 1 trong cac tuy chon):\n"
        "    + TeX Live 2025+ / MiKTeX (kha pho bien, day du)\n"
        "    + Tectonic (chi 1 file, khong can TeX distribution -- nhe nhang)\n\n"
        "Cau hinh truoc khi chay (chi can lam neu app yeu cau):\n"
        "  - Mac dinh portable zip KHONG kem .env de tranh lo secret.\n"
        "  - Neu app bao loi license/Supabase, sao chep .env.template thanh .env\n"
        "    va dien SUPABASE_URL, SUPABASE_KEY (xin tu admin).\n\n"
        "Lan dau chay:\n"
        "  - App se hien man hinh kich hoat\n"
        "  - Sao chep Ma may (Machine ID)\n"
        "  - Chuyen khoan theo huong dan -> Gui ma may cho admin\n"
        "  - Sau khi admin kich hoat -> nhan Thu lai\n\n"
        "Sau khi kich hoat:\n"
        "  - Vao Tab Cai dat -> nhap API Key (Gemini / Claude / DeepSeek)\n"
        "  - Chon mon, lop, nhap ma tran de -> Tao de bang AI\n"
        "  - Xuat Word / nhieu ma de\n\n"
        "Lien he ho tro: Zalo 033.999.8261\n",
        encoding="utf-8"
    )

    # Prompt Chatbot/
    src_prompt = SRC / "Prompt Chatbot"
    if src_prompt.exists():
        _safe_copy_tree(src_prompt, DIST / "Prompt Chatbot")

    # Bat file chay nhanh
    (DIST / "Chay MEA_v5.bat").write_text(
        '@echo off\ncd /d "%~dp0"\nstart "" "MEA_v5.exe"\n', encoding="ascii")
    (DIST / "Chay Admin Tool.bat").write_text(
        '@echo off\ncd /d "%~dp0"\nstart "" "MEA_v5_Admin.exe"\n', encoding="ascii")
    print("  [OK] Tai nguyen da sao chep.")


def generate_inno_setup():
    """Tao file installer.iss cho Inno Setup 6."""
    icon_path = ICON_MAIN
    logo_path = ASSETS / "logo_1.png"

    # Kiểm tra license file (tùy chọn)
    license_line = ""
    license_file = SRC / "LICENSE.txt"
    if license_file.exists():
        license_line = f'LicenseFile={license_file}'

    # .env va .env.template chi them vao [Files] khi file thuc te ton tai
    # trong dist/. .env chi co khi build voi BUILD_INCLUDE_ENV=1.
    env_dist = DIST / ".env"
    env_template_dist = DIST / ".env.template"
    env_lines: list[str] = []
    if env_template_dist.exists():
        env_lines.append(
            f'Source: "{env_template_dist}"; DestDir: "{{app}}"; '
            "Flags: ignoreversion"
        )
    if env_dist.exists():
        env_lines.append(
            f'Source: "{env_dist}"; DestDir: "{{app}}"; '
            "Flags: ignoreversion onlyifdoesntexist"
        )
    env_files_block = "\n".join(env_lines)

    autorun_value = '"""{app}\\{#MyAppExeName}"""'
    ps_setup_arg = r'"-ExecutionPolicy Bypass -NoProfile -File ""{app}\word_addon\setup_addin.ps1"""'
    ps_register_arg = r'"-ExecutionPolicy Bypass -NoProfile -File ""{app}\word_addon\register_addin.ps1"""'
    ps_uninstall_arg = r'"-ExecutionPolicy Bypass -NoProfile -File ""{app}\word_addon\uninstall_addin.ps1"""'

    iss_content = f"""; Inno Setup Script — MEA_v5 Installer
; Auto-generated by build_helper.py

#define MyAppName "MEA_v5"
#define MyAppVersion "{APP_VERSION}"
#define MyAppPublisher "Do Minh Math"
#define MyAppURL "https://dominh.math"
#define MyAppExeName "MEA_v5.exe"

[Setup]
AppId={{{{B8E5F3A2-7C4D-4E9F-A1B3-2D8F6E4C9A71}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}
DisableProgramGroupPage=yes
OutputDir={DIST / "installer"}
OutputBaseFilename=MEA_v5_Setup
SetupIconFile={icon_path}
UninstallDisplayIcon={{app}}\\assets\\{ICON_MAIN.name}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
WizardImageFile={ASSETS / "logo_1.png"}
WizardSmallImageFile={ASSETS / "app.png"}
CloseApplications=yes
RestartApplications=no
PrivilegesRequired=admin
{license_line}

[Languages]
Name: "vietnamese"; MessagesFile: "compiler:Default.isl"

[Messages]
; --- Nut dieu huong ---
vietnamese.ButtonNext=Tiếp tục >
vietnamese.ButtonBack=< Quay lại
vietnamese.ButtonInstall=Cài đặt
vietnamese.ButtonCancel=Hủy bỏ
vietnamese.ButtonFinish=Hoàn tất
vietnamese.ButtonBrowse=Duyệt...
vietnamese.ButtonWizardBrowse=Duyệt...
vietnamese.ButtonYes=&Có
vietnamese.ButtonYesToAll=Có cho &tất cả
vietnamese.ButtonNo=&Không
vietnamese.ButtonNoToAll=Không cho tất c&ả
vietnamese.ButtonOK=Đồng ý

; --- Man hinh chao mung ---
vietnamese.WelcomeLabel1=Chào mừng bạn đến với MEA v5 v{APP_VERSION}!
vietnamese.WelcomeLabel2=Trình cài đặt sẽ cài đặt MEA v5 v{{#MyAppVersion}} — Trợ lý tạo đề kiểm tra & Chuyển đổi tài liệu AI lên máy tính của bạn.%n%nKhuyên nghị: Đóng các ứng dụng Microsoft Word hoặc phiên bản MEA trước khi tiếp tục.%n%nNhấn "Tiếp tục" để bắt đầu cài đặt.

; --- Man hinh chon thu muc ---
vietnamese.WizardSelectDir=Chọn thư mục cài đặt
vietnamese.SelectDirDesc=Nơi ứng dụng MEA v5 sẽ được cài đặt?
vietnamese.SelectDirLabel3=Trình cài đặt sẽ cài MEA v5 vào thư mục sau đây.
vietnamese.SelectDirBrowseLabel=Để tiếp tục, hãy nhấn Tiếp tục. Nếu bạn muốn chọn thư mục khác, hãy nhấn Duyệt:

; --- Man hinh chon tac vu (Tasks) ---
vietnamese.WizardSelectTasks=Chọn tác vụ bổ sung
vietnamese.SelectTasksDesc=Những tác vụ nào cần được thực hiện trong khi cài đặt?
vietnamese.SelectTasksLabel2=Chọn các tác vụ bạn muốn trình cài đặt thực hiện, sau đó nhấn Tiếp tục:

; --- Man hinh san sang cai dat ---
vietnamese.WizardReady=Sẵn sàng cài đặt
vietnamese.ReadyLabel1=Trình cài đặt đã sẵn sàng bắt đầu cài đặt MEA v5 trên máy tính của bạn.
vietnamese.ReadyLabel2a=Nhấn Cài đặt để bắt đầu, hoặc nhấn Quay lại nếu bạn muốn xem lại hoặc thay đổi các thiết lập.

; --- Man hinh chuan bi & tien trinh ---
vietnamese.WizardPreparing=Đang chuẩn bị cài đặt
vietnamese.PreparingDesc=Đang kiểm tra tiến trình và dọn dẹp hệ thống trước khi cài đặt MEA v5...
vietnamese.WizardInstalling=Đang cài đặt MEA v5
vietnamese.InstallingLabel=Vui lòng chờ trong khi trình cài đặt sao chép tập tin và thiết lập MEA v5 trên máy tính...
vietnamese.StatusExtractFiles=Đang giải nén tập tin...
vietnamese.StatusUninstalling=Đang tự động gỡ bỏ phiên bản cũ...

; --- Man hinh hoan tat ---
vietnamese.FinishedHeadingLabel=Hoàn tất cài đặt MEA v5!
vietnamese.FinishedLabel=Cài đặt MEA v5 v{APP_VERSION} thành công!%n%nBiểu tượng MEA v5 đã được tạo trên Màn hình chính (Desktop) để bạn sử dụng dễ dàng mọi lúc.%n%nKhi chạy lần đầu:%n  1. Kích hoạt giấy phép (chuyển khoản + gửi Mã máy cho admin)%n  2. Nhập API Key tại tab Cài đặt (Gemini / Claude / DeepSeek / 9Router)%n  3. Sử dụng trợ lý Tạo đề và Chuyển đổi tài liệu bằng AI.

; --- Khac ---
vietnamese.ClickNext=Nhấn Tiếp tục để tiếp tục, hoặc Hủy bỏ để thoát.
vietnamese.ClickFinish=Nhấn Hoàn tất để thoát trình cài đặt.
vietnamese.ExitSetupTitle=Hủy cài đặt MEA v5
vietnamese.ExitSetupMessage=Cài đặt MEA v5 chưa hoàn tất. Nếu thoát bây giờ, ứng dụng sẽ chưa thể sử dụng.%n%nBạn có chắc chắn muốn thoát khỏi trình cài đặt không?

[Tasks]
Name: "cleanold"; Description: "Tự động gỡ bỏ sạch sẽ các phiên bản cũ trước khi cài đặt mới (Khuyên dùng)"; GroupDescription: "Nâng cấp & Dọn dẹp hệ thống:"; Flags: checkedonce
Name: "desktopicon"; Description: "Tạo biểu tượng MEA v5 trên Màn hình chính (Desktop)"; GroupDescription: "Biểu tượng lối tắt:"
Name: "admindesktop"; Description: "Tạo biểu tượng Admin Tool trên Desktop"; GroupDescription: "Biểu tượng lối tắt:"; Flags: unchecked
Name: "wordaddin"; Description: "Tích hợp Add-in vào Microsoft Word (Ribbon MatrixExamAI & Vẽ hình TikZ)"; GroupDescription: "Tiện ích mở rộng Microsoft Word:"; Flags: checkedonce
Name: "autostart"; Description: "Khởi động MEA v5 cùng Windows"; GroupDescription: "Tùy chọn khởi động:"; Flags: unchecked

[Files]
Source: "{DIST / 'MEA_v5.exe'}"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{DIST / 'MEA_v5_Admin.exe'}"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{DIST / 'assets'}\\*"; DestDir: "{{app}}\\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{DIST / 'data'}\\*"; DestDir: "{{app}}\\data"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{DIST / 'config.py'}"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{DIST / 'Prompt Chatbot'}\\*"; DestDir: "{{app}}\\Prompt Chatbot"; Flags: ignoreversion recursesubdirs createallsubdirs
{env_files_block}
Source: "{DIST / 'README.txt'}"; DestDir: "{{app}}"; Flags: ignoreversion
; --- Word Add-in native bundle ---
Source: "{SRC / 'word_addon'}\\src\\MatrixExamAI.WordAddIn\\bin\\Debug\\net48\\*"; DestDir: "{{app}}\\word_addon"; Flags: ignoreversion recursesubdirs createallsubdirs; Tasks: wordaddin
Source: "{SRC / 'word_addon'}\\register_addin.ps1"; DestDir: "{{app}}\\word_addon"; Flags: ignoreversion; Tasks: wordaddin
Source: "{SRC / 'word_addon'}\\setup_addin.ps1"; DestDir: "{{app}}\\word_addon"; Flags: ignoreversion; Tasks: wordaddin
Source: "{SRC / 'word_addon'}\\uninstall_addin.ps1"; DestDir: "{{app}}\\word_addon"; Flags: ignoreversion; Tasks: wordaddin
Source: "{SRC / 'word_addon'}\\addon_hkcu.reg"; DestDir: "{{app}}\\word_addon"; Flags: ignoreversion; Tasks: wordaddin
Source: "{SRC / 'word_addon'}\\sync_keys.py"; DestDir: "{{app}}\\word_addon"; Flags: ignoreversion; Tasks: wordaddin

[Dirs]
Name: "{{app}}\\storage"; Permissions: users-full
Name: "{{app}}\\sessions"; Permissions: users-full
Name: "{{app}}\\logs"; Permissions: users-full
Name: "{{app}}\\nhch"; Permissions: users-full
Name: "{{app}}\\data"; Permissions: users-full
Name: "{{app}}\\word_addon"; Permissions: users-full; Tasks: wordaddin

[Icons]
; Menu Bat dau (Start Menu)
Name: "{{autoprograms}}\\{{#MyAppName}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; WorkingDir: "{{app}}"; IconFilename: "{{app}}\\assets\\{ICON_MAIN.name}"
Name: "{{autoprograms}}\\{{#MyAppName}}\\Admin Tool"; Filename: "{{app}}\\MEA_v5_Admin.exe"; WorkingDir: "{{app}}"; IconFilename: "{{app}}\\assets\\{ICON_ADMIN.name}"
Name: "{{autoprograms}}\\{{#MyAppName}}\\Cài đặt Word Add-in"; Filename: "powershell.exe"; Parameters: {ps_setup_arg}; WorkingDir: "{{app}}\\word_addon"; Tasks: wordaddin
Name: "{{autoprograms}}\\{{#MyAppName}}\\Go cai dat {{#MyAppName}}"; Filename: "{{uninstallexe}}"
; Man hinh chinh (Desktop)
Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; WorkingDir: "{{app}}"; IconFilename: "{{app}}\\assets\\{ICON_MAIN.name}"; Tasks: desktopicon
Name: "{{autodesktop}}\\{{#MyAppName}} Admin"; Filename: "{{app}}\\MEA_v5_Admin.exe"; WorkingDir: "{{app}}"; IconFilename: "{{app}}\\assets\\{ICON_ADMIN.name}"; Tasks: admindesktop

[Registry]
Root: HKCU; Subkey: "Software\\Microsoft\\Windows\\CurrentVersion\\Run"; ValueType: string; ValueName: "MEA_v5"; ValueData: {autorun_value}; Flags: uninsdeletevalue; Tasks: autostart
Root: HKCU; Subkey: "Software\\MEA_v5"; ValueType: string; ValueName: "InstallPath"; ValueData: "{{app}}"; Flags: uninsdeletevalue

[Run]
Filename: "powershell.exe"; Parameters: {ps_register_arg}; StatusMsg: "Đang kích hoạt MatrixExamAI Word Add-in..."; Flags: runhidden; Tasks: wordaddin
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "Chay MEA_v5 ngay sau khi cai dat"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "powershell.exe"; Parameters: {ps_uninstall_arg}; Flags: runhidden

[UninstallDelete]
Type: dirifempty; Name: "{{app}}\\sessions"
Type: dirifempty; Name: "{{app}}\\logs"

[Code]
// Tu dong tim va go cai dat phien ban cu truoc khi cai dat phien ban moi
function GetUninstallString(AppIdStr: String): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstallString := '';
  sUnInstPath := 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\' + AppIdStr + '_is1';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    if not RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString) then
      if not RegQueryStringValue(HKLM64, sUnInstPath, 'UninstallString', sUnInstallString) then
        RegQueryStringValue(HKCU64, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

procedure UnInstallOldVersion(AppIdStr: String);
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  sUnInstallString := GetUninstallString(AppIdStr);
  if sUnInstallString <> '' then begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    Exec(sUnInstallString, '/VERYSILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_HIDE, ewWaitUntilTerminated, iResultCode);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssInstall) then begin
    if WizardIsTaskSelected('cleanold') then begin
      try
        WizardForm.StatusLabel.Caption := 'Đang tự động gỡ bỏ sạch sẽ các phiên bản cũ...';
      except
      end;
      // Tu dong go bo moi phien ban cu da biet
      UnInstallOldVersion('{{B8E5F3A2-7C4D-4E9F-A1B3-2D8F6E4C9A71}}');
      UnInstallOldVersion('{{C9F2E7B1-8D5C-4F3A-B2E8-1C9A7E5F4D60}}');
      UnInstallOldVersion('MEA_v5');
      UnInstallOldVersion('MEA_v4');
    end;
  end;
end;
"""

    iss_path = SRC / "installer.iss"
    iss_path.write_text(iss_content, encoding="utf-8-sig")
    (DIST / "installer").mkdir(exist_ok=True)
    print(f"  [OK] Da tao installer.iss")
    return iss_path


def check_deps():
    """Kiem tra va cai thu vien thieu."""
    missing = []
    checks = {
        "google.genai":        "google-genai",
        "anthropic":           "anthropic",
        "openai":              "openai",
        "docx":                "python-docx",
        "mammoth":             "mammoth",
        "PIL":                 "pillow",
        "cryptography":        "cryptography",
        "latex2mathml":        "latex2mathml",
        "fitz":                "PyMuPDF",
        "pdfplumber":          "pdfplumber",
        "PyInstaller":         "pyinstaller",
        "supabase":            "supabase",
        "certifi":             "certifi",
    }
    for mod, pkg in checks.items():
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"\n  [SETUP] Cai {len(missing)} thu vien con thieu: {', '.join(missing)}")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing + ["-q"])
    else:
        print("  [OK] Tat ca thu vien da co san.")


def main():
    # Tăng recursion limit để tránh crash khi PyInstaller scan deep dependency trees
    sys.setrecursionlimit(200000)

    print("=" * 54)
    print(f"  MEA_v5 v{APP_VERSION} — PyInstaller Build Helper")
    print(f"  Python  : {sys.version.split()[0]}")
    print(f"  Source  : {SRC}")
    print(f"  Output  : {DIST}")
    print(f"  Icon    : {ICON_MAIN.name}")
    print("=" * 54)

    check_deps()

    # Disable kivy hooks to avoid RecursionError
    disabled_hooks = _disable_kivy_hooks()

    # Build 2 app
    try:
        ok1 = build_app("main.py",       "MEA_v5",              ICON_MAIN)
        ok2 = build_app("admin_tool.py", "MEA_v5_Admin",        ICON_ADMIN)
    finally:
        _restore_kivy_hooks(disabled_hooks)

    if not (ok1 and ok2):
        print("\n  [LOI] Build that bai!")
        sys.exit(1)

    # Đảm bảo Word Add-in C# .NET được biên dịch sẵn sàng
    addon_dll = SRC / "word_addon" / "src" / "MatrixExamAI.WordAddIn" / "bin" / "Debug" / "net48" / "MatrixExamAI.WordAddIn.dll"
    if not addon_dll.exists():
        print("\n  [DOTNET] Biên dịch Word Add-in solution...")
        try:
            subprocess.run(["dotnet", "build", str(SRC / "word_addon" / "MatrixExamAI.sln"), "-c", "Debug"], cwd=str(SRC))
        except Exception as dotnet_err:
            print(f"  [WARN] dotnet build: {dotnet_err}")

    # Dọn dẹp triệt để các phiên bản cũ và file dư thừa trong dist/
    redundant_dist = [
        DIST / "dist.rar",
        DIST / "MEA_v5_alpha.exe",
        DIST / "MatrixExamAI.exe",
        DIST / "MEA_v4.exe",
        DIST / "MEA_v4_Admin.exe",
        DIST / "Chay MEA_v4.bat",
        DIST / "update_manifest_v4.json",
    ]
    for rf in redundant_dist:
        if rf.exists():
            try:
                rf.unlink()
                print(f"  [CLEAN] Đã loại bỏ file dư thừa: {rf.name}")
            except Exception as e:
                print(f"  [WARN] Không thể xóa {rf.name}: {e}")

    copy_resources()

    # Tao Inno Setup script
    generate_inno_setup()

    # Bien dich Inno Setup neu co ISCC
    iscc_candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    iscc_exe = None
    for cand in iscc_candidates:
        if cand and os.path.exists(cand):
            iscc_exe = cand
            break

    if iscc_exe:
        print(f"\n  [INNO SETUP] Bien dich bo cai bang: {iscc_exe}")
        try:
            res = subprocess.run([iscc_exe, "/Q", str(SRC / "installer.iss")], cwd=str(SRC))
            if res.returncode == 0:
                print("  [OK] Inno Setup bien dich installer thanh cong!")
            else:
                print(f"  [WARN] Inno Setup tra ve exit code: {res.returncode}")
        except Exception as inno_err:
            print(f"  [WARN] Loi khi chay Inno Setup: {inno_err}")

    # Don dep thu muc tam
    if BUILD_TMP.exists():
        shutil.rmtree(str(BUILD_TMP), ignore_errors=True)

    print("\n" + "=" * 54)
    print("  BUILD THANH CONG!")
    print(f"  >> MEA_v5.exe (Bản chính duy nhất) -> {DIST / 'MEA_v5.exe'}")
    print(f"  >> MEA_v5_Admin.exe                 -> {DIST / 'MEA_v5_Admin.exe'}")
    print(f"  >> Word Add-in (Tích hợp cài đặt)  -> {SRC / 'word_addon'}")
    if iscc_exe and (DIST / "installer" / "MEA_v5_Setup.exe").exists():
        print(f"  >> MEA_v5_Setup.exe (Bộ cài đặt)    -> {DIST / 'installer' / 'MEA_v5_Setup.exe'}")
    print("=" * 54)


if __name__ == "__main__":
    main()
