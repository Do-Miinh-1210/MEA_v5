import os
import json
from datetime import datetime
from pathlib import Path
import sys
from flask import Flask, request, jsonify, render_template_string
from supabase import create_client

app = Flask(__name__)

def _load_config_fallback():
    """Use the desktop config credentials when admin_web runs from this repo."""
    try:
        repo_root = Path(__file__).resolve().parents[2]
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from config import SUPABASE_URL as cfg_url, SUPABASE_KEY as cfg_key
        return (cfg_url or "").strip(), (cfg_key or "").strip()
    except Exception:
        return "", ""

def get_supabase_config():
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.environ.get("SUPABASE_KEY", "").strip()
    )
    source = "env" if url and key else "missing"

    if not url or not key:
        cfg_url, cfg_key = _load_config_fallback()
        if not url and cfg_url:
            url = cfg_url
        if not key and cfg_key:
            key = cfg_key
        if url and key:
            source = "config.py"

    return url, key, source

def get_db():
    url, key, _source = get_supabase_config()
    if not url or not key:
        raise ValueError("Lỗi: Chưa cấu hình SUPABASE_URL hoặc SUPABASE_KEY/SUPABASE_SERVICE_ROLE_KEY.")
    return create_client(url, key)

def api_error(error, status=500):
    return jsonify({'ok': False, 'error': str(error)}), status

# ── Feature catalog (đồng bộ với config.py v4.1.0) ──────────────────────
FEATURE_CATALOG = {
    "tab_matrix":  "Bảng câu hỏi",
    "tab_result":  "Xem đề & Xuất file",
    "tab_bank":    "Ngân hàng câu hỏi",
    "tab_qc":      "Kiểm tra chất lượng",
    "tab_tikz":    "TikZ vẽ hình",
    "tab_convert": "Convert (Ảnh/PDF)",
    "quick_gen":   "Tạo đề nhanh",
    "export_word": "Xuất Word",
    "nhch_cloud":  "NHCH Cloud",
    "ai_review":   "AI Review & Fix",
    "multi_code":  "Nhiều mã đề",
    "tab_history": "Lịch sử đề",
    "smart_prompt":"Smart Prompt",
}

# =====================================================================
# GIAO DIỆN FRONTEND — MEA v4.1.0 Admin Web
# =====================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MEA v4 Admin</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #f4f7f6; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .card { border-radius: 12px; border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
        .card-header { background-color: #fff; border-bottom: 1px solid #eee; border-radius: 12px 12px 0 0 !important; font-weight: bold; color: #1F497D; padding: 15px 20px; }
        .table-responsive { overflow-x: auto; }
        #userTable { min-width: 1100px; table-layout: fixed; }
        #userTable th:nth-child(1), #userTable td:nth-child(1) { width: 155px; word-break: break-all; white-space: normal; }
        #userTable th:nth-child(2), #userTable td:nth-child(2) { width: 140px; white-space: normal; }
        #userTable th:nth-child(3), #userTable td:nth-child(3) { width: 95px; }
        #userTable th:nth-child(4), #userTable td:nth-child(4) { width: 85px; }
        #userTable th:nth-child(5), #userTable td:nth-child(5) { width: 65px; text-align: center; }
        #userTable th:nth-child(6), #userTable td:nth-child(6) { width: 100px; }
        #userTable th:nth-child(7), #userTable td:nth-child(7) { width: 130px; font-size: 0.8rem; }
        #userTable th:nth-child(8), #userTable td:nth-child(8) { width: 230px; }
        .badge-active { background-color: #10B981; color: white; padding: 6px 10px; border-radius: 6px; font-weight: normal; }
        .badge-revoked { background-color: #EF4444; color: white; padding: 6px 10px; border-radius: 6px; font-weight: normal; }
        .badge-suspended { background-color: #F59E0B; color: white; padding: 6px 10px; border-radius: 6px; font-weight: normal; }
        .navbar-brand { font-weight: bold; color: #10B981 !important; }
        .btn-sm-action { padding: 3px 6px; font-size: 0.78rem; margin: 1px; }
        .tier-btn { min-width: 100px; }
        .tier-btn.active-tier { box-shadow: 0 0 0 3px rgba(13,110,253,.5); }
        .preset-btn { margin: 3px; }
        .preset-btn.active { box-shadow: 0 0 0 3px rgba(13,110,253,.5); }
        .action-group { display: flex; flex-wrap: nowrap; gap: 2px; }
        .feat-toggle { cursor: pointer; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; display: inline-block; min-width: 40px; text-align: center; }
        .feat-on { background: #10B981; color: white; }
        .feat-off { background: #E2E8F0; color: #64748B; }

        /* ── Sidebar collapse ── */
        .users-layout { display: flex; gap: 16px; }
        .sidebar-panel {
            width: 380px; min-width: 380px; max-width: 380px;
            transition: width 0.35s ease, min-width 0.35s ease, opacity 0.25s ease, margin 0.35s ease;
            overflow: hidden; opacity: 1;
        }
        .sidebar-panel.collapsed {
            width: 0 !important; min-width: 0 !important; max-width: 0 !important;
            opacity: 0; margin: 0 !important; padding: 0 !important;
        }
        .sidebar-panel.collapsed > * { display: none; }
        .main-panel { flex: 1; min-width: 0; }
        .toggle-sidebar-btn {
            position: fixed; left: 8px; top: 72px; z-index: 1050;
            width: 36px; height: 36px; border-radius: 50%;
            border: 2px solid #0F2D52; background: #fff; color: #0F2D52;
            font-size: 16px; cursor: pointer; display: flex; align-items: center;
            justify-content: center; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            transition: transform 0.3s ease, left 0.3s ease;
        }
        .toggle-sidebar-btn:hover { background: #0F2D52; color: #fff; }
        .toggle-sidebar-btn.shifted { left: 394px; }

        /* Card collapsible headers */
        .card-header-toggle { cursor: pointer; user-select: none; }
        .card-header-toggle:hover { background-color: #f0f4ff !important; }
        .card-header-toggle .collapse-icon { transition: transform 0.3s ease; display: inline-block; }
        .card-header-toggle.collapsed-header .collapse-icon { transform: rotate(-90deg); }
        .card-body-collapsible {
            max-height: 800px; overflow: hidden;
            transition: max-height 0.4s ease, padding 0.3s ease, opacity 0.3s ease;
            opacity: 1;
        }
        .card-body-collapsible.collapsed-body {
            max-height: 0 !important; padding-top: 0 !important; padding-bottom: 0 !important;
            opacity: 0;
        }
    </style>
</head>
<body>

<nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
    <div class="container-fluid">
        <a class="navbar-brand" href="#"><i class="fa-solid fa-shield-halved"></i> MEA v4 Admin</a>
        <ul class="navbar-nav me-auto">
            <li class="nav-item"><a class="nav-link active" href="#" onclick="showTab('users')">👥 Người dùng</a></li>
            <li class="nav-item"><a class="nav-link" href="#" onclick="showTab('stats')">📊 Thống kê</a></li>
            <li class="nav-item"><a class="nav-link" href="#" onclick="showTab('logs')">📝 Log</a></li>
        </ul>
        <span class="text-light small" id="statusIndicator">v4.1.0</span>
    </div>
</nav>

<div class="container-fluid px-3 pb-5">

    <div id="maintAlert" class="alert alert-danger d-none fw-bold" role="alert">
        <i class="fa-solid fa-wrench"></i> BẢO TRÌ ĐANG BẬT - TẤT CẢ NGƯỜI DÙNG BỊ CHẶN!
    </div>

    <!-- ═══ TAB: STATS ═══ -->
    <div id="tabStats" class="d-none">
        <div class="row mb-4">
            <div class="col-md-3"><div class="card text-center p-3"><h2 class="text-primary" id="statTotal">-</h2><small class="text-muted">Tổng người dùng</small></div></div>
            <div class="col-md-3"><div class="card text-center p-3"><h2 class="text-success" id="statActive">-</h2><small class="text-muted">Đang hoạt động</small></div></div>
            <div class="col-md-3"><div class="card text-center p-3"><h2 class="text-danger" id="statRevoked">-</h2><small class="text-muted">Đã thu hồi</small></div></div>
            <div class="col-md-3"><div class="card text-center p-3"><h2 class="text-warning" id="statActive7d">-</h2><small class="text-muted">Active 7 ngày</small></div></div>
        </div>
        <div class="row">
            <div class="col-md-6">
                <div class="card"><div class="card-header">📦 Phân bố theo gói</div>
                    <div class="card-body" id="tierChart"></div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card"><div class="card-header">⏰ Sắp hết hạn (30 ngày): <span id="statExpiring">0</span></div>
                    <div class="card-body"><p class="text-muted">Xem chi tiết ở tab Người dùng, lọc theo hạn.</p></div>
                </div>
            </div>
        </div>
    </div>

    <!-- ═══ TAB: LOGS ═══ -->
    <div id="tabLogs" class="d-none">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <span><i class="fa-solid fa-clock-rotate-left"></i> Log hoạt động Admin</span>
                <button class="btn btn-sm btn-outline-primary" onclick="loadLogs()"><i class="fa-solid fa-rotate-right"></i> Làm mới</button>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="table-light">
                            <tr><th>Thời gian</th><th>Hành động</th><th>Đối tượng</th><th>Admin</th><th>Chi tiết</th></tr>
                        </thead>
                        <tbody id="logsTableBody">
                            <tr><td colspan="5" class="text-center py-4 text-muted">Nhấn Làm mới để tải log</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- ═══ TAB: USERS (default) ═══ -->
    <div id="tabUsers">

    <!-- Toggle sidebar button -->
    <button class="toggle-sidebar-btn shifted" id="btnToggleSidebar" onclick="toggleSidebar()" title="Thu/Mở bảng điều khiển">
        <i class="fa-solid fa-angles-left" id="sidebarIcon"></i>
    </button>

    <div class="users-layout">
        <!-- ── SIDEBAR (collapsible) ── -->
        <div class="sidebar-panel" id="sidebarPanel">

            <div class="card">
                <div class="card-header card-header-toggle" onclick="toggleCard(this)">
                    <span class="collapse-icon"><i class="fa-solid fa-chevron-down"></i></span>
                    <i class="fa-solid fa-sliders ms-1"></i> Điều Khiển
                </div>
                <div class="card-body card-body-collapsible">
                    <button class="btn btn-warning w-100 mb-2 fw-bold text-dark" onclick="toggleMaint()" id="btnMaint">
                        <i class="fa-solid fa-wrench"></i> Bật Bảo Trì
                    </button>
                    <button class="btn btn-danger w-100 mb-2 fw-bold" onclick="bulkAction('lock')">
                        <i class="fa-solid fa-lock"></i> Khóa Tất Cả
                    </button>
                    <button class="btn btn-success w-100 mb-2 fw-bold" onclick="bulkAction('unlock')">
                        <i class="fa-solid fa-unlock"></i> Mở Khóa Tất Cả
                    </button>
                    <button class="btn btn-primary w-100 fw-bold" onclick="openFeaturesModal()">
                        <i class="fa-solid fa-gear"></i> Quản Lý Tính Năng Theo Gói
                    </button>
                </div>
            </div>

            <div class="card">
                <div class="card-header card-header-toggle" onclick="toggleCard(this)">
                    <span class="collapse-icon"><i class="fa-solid fa-chevron-down"></i></span>
                    <i class="fa-solid fa-user-plus ms-1"></i> Cấp Quyền
                </div>
                <div class="card-body card-body-collapsible">
                    <form id="addUserForm" onsubmit="addUser(event)">
                        <div class="mb-3">
                            <label class="form-label fw-bold text-danger">Machine ID *</label>
                            <input type="text" class="form-control" id="mid" required placeholder="VD: A1B2-C3D4-E5F6">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Tên</label>
                            <input type="text" class="form-control" id="mname" placeholder="Tên khách hàng...">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Gói</label>
                            <select class="form-select" id="mtier">
                                <option value="basic">Basic</option>
                                <option value="pro" selected>Pro</option>
                                <option value="premium">Premium</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Admin API Key (tuỳ chọn)</label>
                            <input type="text" class="form-control" id="madminkey" placeholder="Key cấp cho user...">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Ghi chú</label>
                            <input type="text" class="form-control" id="mnote" placeholder="...">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Hạn dùng</label>
                            <div class="d-flex flex-wrap gap-1 mb-2">
                                <button type="button" class="btn btn-sm btn-outline-secondary" onclick="setAddExpiry('forever')">Vĩnh viễn</button>
                                <button type="button" class="btn btn-sm btn-outline-primary" onclick="setAddExpiry(1)">1T</button>
                                <button type="button" class="btn btn-sm btn-outline-primary" onclick="setAddExpiry(3)">3T</button>
                                <button type="button" class="btn btn-sm btn-outline-primary" onclick="setAddExpiry(6)">6T</button>
                                <button type="button" class="btn btn-sm btn-outline-primary" onclick="setAddExpiry(12)">1N</button>
                            </div>
                            <input type="text" class="form-control" id="mexpiry" placeholder="DD-MM-YYYY" oninput="autoDash(this)">
                        </div>
                        <button type="submit" class="btn btn-primary w-100 fw-bold"><i class="fa-solid fa-plus"></i> Thêm</button>
                    </form>
                </div>
            </div>
        </div>

        <!-- ── MAIN PANEL ── -->
        <div class="main-panel">
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <span><i class="fa-solid fa-users"></i> Danh Sách (<span id="userCount">0</span>)</span>
                    <div>
                        <select class="form-select form-select-sm d-inline-block" style="width:auto" id="filterStatus" onchange="filterTable()">
                            <option value="">Tất cả</option>
                            <option value="active">Active</option>
                            <option value="revoked">Revoked</option>
                        </select>
                        <button class="btn btn-sm btn-outline-primary ms-2" onclick="loadData()"><i class="fa-solid fa-rotate-right"></i></button>
                    </div>
                </div>
                <div class="card-body p-0">
                    <div class="p-3 border-bottom bg-light">
                        <input type="text" class="form-control" id="searchInput" placeholder="Tìm Machine ID, Tên, Ghi chú..." onkeyup="filterTable()">
                    </div>
                    <div class="table-responsive">
                        <table class="table table-hover align-middle mb-0" id="userTable">
                            <thead class="table-light">
                                <tr>
                                    <th>Machine ID</th>
                                    <th>Tên</th>
                                    <th>Gói</th>
                                    <th>Trạng thái</th>
                                    <th>API Key</th>
                                    <th>Hạn dùng</th>
                                    <th>Lần cuối</th>
                                    <th>Hành động</th>
                                </tr>
                            </thead>
                            <tbody id="userTableBody">
                                <tr><td colspan="8" class="text-center py-4">Đang tải...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    </div><!-- end tabUsers -->
</div>

<!-- Modal: Đổi gói cước -->
<div class="modal fade" id="tierModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header bg-primary text-white">
                <h5 class="modal-title"><i class="fa-solid fa-box"></i> Đổi gói cước</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body text-center">
                <p class="mb-1">Machine ID: <strong id="tierMid" class="font-monospace"></strong></p>
                <p class="mb-3">Gói hiện tại: <span id="tierCurrent" class="badge bg-secondary"></span></p>
                <div class="d-flex justify-content-center gap-3">
                    <button class="btn btn-outline-secondary tier-btn" onclick="doChangeTier('basic')"><i class="fa-solid fa-seedling"></i><br>Basic</button>
                    <button class="btn btn-outline-primary tier-btn" onclick="doChangeTier('pro')"><i class="fa-solid fa-star"></i><br>Pro</button>
                    <button class="btn btn-outline-warning tier-btn" onclick="doChangeTier('premium')"><i class="fa-solid fa-crown"></i><br>Premium</button>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Modal: Đổi hạn sử dụng -->
<div class="modal fade" id="expiryModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header bg-info text-white">
                <h5 class="modal-title"><i class="fa-solid fa-calendar-days"></i> Đổi hạn sử dụng</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p class="mb-1">Machine ID: <strong id="expiryMid" class="font-monospace"></strong></p>
                <p class="mb-3">Hạn hiện tại: <span id="expiryCurrent" class="fw-bold text-primary"></span></p>
                <div class="mb-3">
                    <label class="form-label fw-bold">Chọn nhanh:</label>
                    <div class="d-flex flex-wrap">
                        <button class="btn btn-sm btn-outline-danger preset-btn" onclick="setExpiryPreset('forever')">Vĩnh viễn</button>
                        <button class="btn btn-sm btn-outline-primary preset-btn" onclick="setExpiryPreset(1)">1T</button>
                        <button class="btn btn-sm btn-outline-primary preset-btn" onclick="setExpiryPreset(3)">3T</button>
                        <button class="btn btn-sm btn-outline-primary preset-btn" onclick="setExpiryPreset(6)">6T</button>
                        <button class="btn btn-sm btn-outline-primary preset-btn" onclick="setExpiryPreset(12)">12T</button>
                        <button class="btn btn-sm btn-outline-primary preset-btn" onclick="setExpiryPreset(24)">24T</button>
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label fw-bold">Nhập tay:</label>
                    <input type="text" class="form-control" id="expiryInput" placeholder="DD-MM-YYYY" oninput="autoDash(this); updateExpiryPreview()">
                </div>
                <div id="expiryPreview" class="text-muted small mb-3"></div>
                <button class="btn btn-info w-100 fw-bold text-white" onclick="doChangeExpiry()"><i class="fa-solid fa-save"></i> Lưu</button>
            </div>
        </div>
    </div>
</div>

<!-- Modal: Cấp API Key -->
<div class="modal fade" id="apiKeyModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header bg-success text-white">
                <h5 class="modal-title"><i class="fa-solid fa-key"></i> Cấp / Cập nhật API Key</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p class="mb-1">Machine ID: <strong id="apiKeyMid" class="font-monospace"></strong></p>
                <div class="mb-3">
                    <label class="form-label fw-bold">API Key (nhiều key cách nhau bằng dấu phẩy):</label>
                    <textarea class="form-control" id="apiKeyInput" rows="3" placeholder="AIzaSy...,AIzaSy..."></textarea>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-success flex-fill fw-bold" onclick="doSaveApiKey()"><i class="fa-solid fa-save"></i> Lưu</button>
                    <button class="btn btn-danger" onclick="doClearApiKey()"><i class="fa-solid fa-trash"></i> Xóa Key</button>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Modal: Ghi đè tính năng cá nhân -->
<div class="modal fade" id="userFeatModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content">
            <div class="modal-header bg-dark text-white">
                <h5 class="modal-title"><i class="fa-solid fa-sliders"></i> Ghi đè tính năng cá nhân</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p class="mb-2">Machine ID: <strong id="userFeatMid" class="font-monospace"></strong> | Gói: <span id="userFeatTier" class="badge bg-secondary"></span></p>
                <p class="text-muted small mb-3">Chọn: <span class="feat-toggle feat-on">BẬT</span> / <span class="feat-toggle feat-off">TẮT</span> / <span class="badge bg-secondary">Theo gói</span></p>
                <div id="userFeatList" class="row g-2"></div>
                <button class="btn btn-primary w-100 fw-bold mt-3" onclick="doSaveUserFeatures()"><i class="fa-solid fa-save"></i> Lưu ghi đè</button>
            </div>
        </div>
    </div>
</div>

<!-- Modal: Quản lý tính năng theo gói -->
<div class="modal fade" id="featuresModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered modal-xl">
        <div class="modal-content">
            <div class="modal-header bg-primary text-white">
                <h5 class="modal-title"><i class="fa-solid fa-gear"></i> Quản Lý Tính Năng Mặc Định Theo Gói</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="table-responsive">
                    <table class="table table-bordered align-middle text-center">
                        <thead class="table-light">
                            <tr>
                                <th class="text-start">Tính năng</th>
                                <th style="width:100px">Basic</th>
                                <th style="width:100px">Pro</th>
                                <th style="width:100px">Premium</th>
                            </tr>
                        </thead>
                        <tbody id="featTableBody"></tbody>
                    </table>
                </div>
                <button class="btn btn-primary w-100 fw-bold" onclick="doSaveGlobalFeatures()"><i class="fa-solid fa-save"></i> Lưu thiết lập</button>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
    const FEAT_CATALOG = """ + json.dumps(FEATURE_CATALOG, ensure_ascii=False) + """;
    let allUsers = [];
    let isMaintenance = false;
    let _tierMid = '', _expiryMid = '', _apiKeyMid = '', _userFeatMid = '';
    let globalFeatures = {basic: {}, pro: {}, premium: {}};

    async function apiCall(ep, method='GET', body=null) {
        let opts = { method, headers: {'Content-Type': 'application/json'} };
        if (body) opts.body = JSON.stringify(body);
        try {
            let res = await fetch(ep, opts);
            let data = null;
            try { data = await res.json(); } catch(_) { data = {}; }
            if (!res.ok) {
                return { ok: false, error: (data && data.error) || ('HTTP ' + res.status), _status: res.status };
            }
            // Với GET /api/data & /api/stats... server không trả {ok:true}, giữ nguyên payload.
            return data;
        } catch (e) {
            return { ok: false, error: 'Network error: ' + (e && e.message ? e.message : e) };
        }
    }

    function autoDash(el) {
        let d = el.value.replace(/[^0-9]/g, '');
        if (d.length > 8) d = d.substring(0, 8);
        let f = '';
        for (let i = 0; i < d.length; i++) { f += d[i]; if ((i===1||i===3) && i < d.length-1) f += '-'; }
        if (f !== el.value) el.value = f;
    }

    function ddmmToYmd(v) { if(!v) return ''; let p=v.split('-'); return p.length===3&&p[0].length===2 ? `${p[2]}-${p[1]}-${p[0]}` : v; }
    function ymdToDdmm(v) { if(!v) return 'Vĩnh viễn'; let p=v.split('-'); return p.length===3&&p[0].length===4 ? `${p[2]}-${p[1]}-${p[0]}` : v; }

    function calcExpiry(months) {
        let d = new Date(); d.setMonth(d.getMonth() + months);
        return String(d.getDate()).padStart(2,'0') + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + d.getFullYear();
    }

    function setAddExpiry(v) { document.getElementById('mexpiry').value = v === 'forever' ? '' : calcExpiry(v); }

async function loadData() {
        document.getElementById('userTableBody').innerHTML = '<tr><td colspan="8" class="text-center py-4">Đang tải...</td></tr>';
        let data = await apiCall('/api/data');
        if (!data.ok) {
            document.getElementById('userTableBody').innerHTML = `<tr><td colspan="8" class="text-center text-danger py-4">${data.error || 'Không tải được dữ liệu'}</td></tr>`;
            return;
        }
        allUsers = data.users || [];
        let sets = data.settings || {};

        isMaintenance = sets.maintenance_mode === "true";
        let mA = document.getElementById('maintAlert'), mB = document.getElementById('btnMaint');
        if (isMaintenance) { mA.classList.remove('d-none'); mB.innerHTML = '<i class="fa-solid fa-check"></i> Tắt Bảo Trì'; mB.className = 'btn btn-success w-100 mb-2 fw-bold'; }
        else { mA.classList.add('d-none'); mB.innerHTML = '<i class="fa-solid fa-wrench"></i> Bật Bảo Trì'; mB.className = 'btn btn-warning w-100 mb-2 fw-bold text-dark'; }

        // Load global features
        for (let t of ['basic','pro','premium']) {
            try { globalFeatures[t] = sets['features_'+t] ? JSON.parse(sets['features_'+t]) : {}; } catch(e) { globalFeatures[t] = {}; }
        }

        renderTable(allUsers);
    }

    function renderTable(users) {
        let tbody = document.getElementById('userTableBody');
        document.getElementById('userCount').innerText = users.length;
        if (!users.length) { tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-muted">Trống</td></tr>'; return; }

        let html = '';
        users.forEach(u => {
            let badge = u.status==='active' ? 'badge-active' : (u.status==='revoked' ? 'badge-revoked' : 'badge-suspended');
            let lc = u.last_check ? u.last_check.substring(0,16).replace('T',' ') : '-';
            let exp = u.expiry ? ymdToDdmm(u.expiry) : 'Vĩnh viễn';
            let tier = (u.tier||'pro').toUpperCase();
            let tc = tier==='PREMIUM' ? 'bg-warning text-dark' : (tier==='PRO' ? 'bg-primary' : 'bg-secondary');
            let hasKey = u.admin_api_key ? '<span class="badge bg-success">Có</span>' : '<span class="text-muted">-</span>';

            html += `<tr>
                <td class="fw-bold font-monospace" style="font-size:0.78rem;cursor:pointer" title="Click để copy" onclick="navigator.clipboard.writeText('${u.machine_id}')">${u.machine_id}</td>
                <td>${u.name||''}<br><small class="text-muted">${u.note||''}</small></td>
                <td><span class="badge ${tc}">${tier}</span></td>
                <td><span class="${badge}">${(u.status||'').toUpperCase()}</span></td>
                <td>${hasKey}</td>
                <td>${exp}</td>
                <td>${lc}</td>
                <td>
                    <div class="action-group">
                        ${u.status!=='active'
                            ? `<button class="btn btn-success btn-sm-action" onclick="changeStatus('${u.machine_id}','active')" title="Kích hoạt"><i class="fa-solid fa-check"></i></button>`
                            : `<button class="btn btn-danger btn-sm-action" onclick="changeStatus('${u.machine_id}','revoked')" title="Khóa"><i class="fa-solid fa-lock"></i></button>`
                        }<button class="btn btn-primary btn-sm-action" onclick="openTierModal('${u.machine_id}','${u.tier||'pro'}')" title="Đổi gói"><i class="fa-solid fa-box"></i></button><button class="btn btn-info btn-sm-action text-white" onclick="openExpiryModal('${u.machine_id}','${u.expiry||''}')" title="Đổi hạn"><i class="fa-solid fa-calendar-days"></i></button><button class="btn btn-success btn-sm-action" onclick="openApiKeyModal('${u.machine_id}','${(u.admin_api_key||'').replace(/'/g,"\\'")}')" title="API Key"><i class="fa-solid fa-key"></i></button><button class="btn btn-dark btn-sm-action" onclick="openUserFeatModal('${u.machine_id}','${u.tier||'pro'}')" title="Tính năng"><i class="fa-solid fa-sliders"></i></button><button class="btn btn-outline-danger btn-sm-action" onclick="deleteUser('${u.machine_id}')" title="Xóa"><i class="fa-solid fa-trash"></i></button>
                    </div>
                </td>
            </tr>`;
        });
        tbody.innerHTML = html;
    }

    function filterTable() {
        let kw = document.getElementById('searchInput').value.toLowerCase();
        let sf = document.getElementById('filterStatus').value;
        let filtered = allUsers.filter(u => {
            let match = (!kw || (u.machine_id||'').toLowerCase().includes(kw) || (u.name||'').toLowerCase().includes(kw) || (u.note||'').toLowerCase().includes(kw));
            let statusMatch = (!sf || u.status === sf);
            return match && statusMatch;
        });
        renderTable(filtered);
    }

    async function addUser(e) {
        e.preventDefault();
        let raw = document.getElementById('mexpiry').value.trim();
        let mid = document.getElementById('mid').value.toUpperCase().trim();
        if (!mid) { alert('⚠️ Vui lòng nhập Machine ID'); return; }
        let body = {
            machine_id: mid,
            name: document.getElementById('mname').value.trim() || 'Không rõ',
            tier: document.getElementById('mtier').value,
            note: document.getElementById('mnote').value.trim(),
            expiry: ddmmToYmd(raw),
            admin_api_key: document.getElementById('madminkey').value.trim()
        };
        let res = await apiCall('/api/add', 'POST', body);
        if (res && res.ok) {
            alert('✅ Đã cấp quyền máy: ' + mid);
            document.getElementById('addUserForm').reset();
            loadData();
        } else {
            alert('❌ Lỗi kích hoạt: ' + (res && res.error ? res.error : 'không xác định')
                  + '\\n\\nKiểm tra: (1) SUPABASE_URL + SUPABASE_KEY/SUPABASE_SERVICE_ROLE_KEY trên Vercel; '
                  + '(2) đã chạy schema v4/v5 và bảng licenses chưa bật RLS; '
                  + '(3) Machine ID chưa bị duplicate.');
        }
    }

    async function changeStatus(mid, st) {
        if(!confirm(`Chuyển [${mid}] → ${st.toUpperCase()}?`)) return;
        let res = await apiCall('/api/status','POST',{machine_id:mid,status:st});
        if (res && res.ok) {
            alert(`✅ Máy ${mid} → ${st.toUpperCase()}`);
            loadData();
        } else {
            alert('❌ Không cập nhật được: ' + (res && res.error ? res.error : 'không rõ'));
        }
    }
    async function deleteUser(mid) {
        if(!confirm(`XÓA VĨNH VIỄN [${mid}]?`)) return;
        let res = await apiCall('/api/delete','POST',{machine_id:mid});
        if (res && res.ok) { loadData(); } else { alert('❌ Lỗi xóa: ' + (res?.error || '')); }
    }
    async function bulkAction(a) {
        if(!confirm(a==='lock'?'KHÓA TẤT CẢ?':'MỞ KHÓA TẤT CẢ?')) return;
        let res = await apiCall('/api/bulk_status','POST',{action:a});
        if (res && res.ok) { loadData(); } else { alert('❌ Lỗi: ' + (res?.error || '')); }
    }
    async function toggleMaint() {
        if(!confirm(isMaintenance?'TẮT bảo trì?':'BẬT bảo trì?')) return;
        let res = await apiCall('/api/settings','POST',{maintenance_mode:isMaintenance?"false":"true"});
        if (res && res.ok) { loadData(); } else { alert('❌ Lỗi: ' + (res?.error || '')); }
    }

    // ── Tier Modal ──
    function openTierModal(mid, t) { _tierMid=mid; document.getElementById('tierMid').innerText=mid; document.getElementById('tierCurrent').innerText=t.toUpperCase(); new bootstrap.Modal(document.getElementById('tierModal')).show(); }
    async function doChangeTier(t) { if(!confirm(`Đổi [${_tierMid}] → ${t.toUpperCase()}?`)) return; await apiCall('/api/tier','POST',{machine_id:_tierMid,tier:t}); bootstrap.Modal.getInstance(document.getElementById('tierModal')).hide(); loadData(); }

    // ── Expiry Modal ──
    function openExpiryModal(mid, exp) { _expiryMid=mid; document.getElementById('expiryMid').innerText=mid; document.getElementById('expiryCurrent').innerText=exp?ymdToDdmm(exp):'Vĩnh viễn'; document.getElementById('expiryInput').value=''; document.getElementById('expiryPreview').innerHTML=''; new bootstrap.Modal(document.getElementById('expiryModal')).show(); }
    function setExpiryPreset(m) { document.getElementById('expiryInput').value = m==='forever' ? '' : calcExpiry(m); updateExpiryPreview(); }
    function updateExpiryPreview() { let v=document.getElementById('expiryInput').value, el=document.getElementById('expiryPreview'); if(!v){el.innerHTML='Vĩnh viễn';return;} let p=v.split('-'); if(p.length===3&&p[2].length===4){let t=new Date(+p[2],+p[1]-1,+p[0]),d=Math.ceil((t-new Date())/(864e5)); el.innerHTML=d>0?`<span class="text-primary">Còn ${d} ngày</span>`:`<span class="text-danger">Đã qua ${Math.abs(d)} ngày</span>`;}else{el.innerHTML='...';} }
    async function doChangeExpiry() { let r=document.getElementById('expiryInput').value.trim(); await apiCall('/api/expiry','POST',{machine_id:_expiryMid,expiry:ddmmToYmd(r)}); bootstrap.Modal.getInstance(document.getElementById('expiryModal')).hide(); loadData(); }

    // ── API Key Modal ──
    function openApiKeyModal(mid, key) { _apiKeyMid=mid; document.getElementById('apiKeyMid').innerText=mid; document.getElementById('apiKeyInput').value=key||''; new bootstrap.Modal(document.getElementById('apiKeyModal')).show(); }
    async function doSaveApiKey() { let k=document.getElementById('apiKeyInput').value.trim(); await apiCall('/api/apikey','POST',{machine_id:_apiKeyMid,admin_api_key:k}); bootstrap.Modal.getInstance(document.getElementById('apiKeyModal')).hide(); loadData(); }
    async function doClearApiKey() { if(!confirm('Xóa API Key?')) return; await apiCall('/api/apikey','POST',{machine_id:_apiKeyMid,admin_api_key:''}); bootstrap.Modal.getInstance(document.getElementById('apiKeyModal')).hide(); loadData(); }

    // ── User Feature Override Modal ──
    let _userFeatData = {};
    function openUserFeatModal(mid, tier) {
        _userFeatMid = mid; _userFeatData = {};
        document.getElementById('userFeatMid').innerText = mid;
        document.getElementById('userFeatTier').innerText = tier.toUpperCase();
        let user = allUsers.find(u => u.machine_id === mid);
        let custom = {};
        try { custom = user && user.features ? (typeof user.features === 'string' ? JSON.parse(user.features) : user.features) : {}; } catch(e) { custom = {}; }

        let html = '';
        for (let [k, label] of Object.entries(FEAT_CATALOG)) {
            let val = custom[k]; // true, false, or undefined (= theo gói)
            let cls0 = val===undefined ? 'bg-secondary text-white' : 'bg-light text-muted';
            let cls1 = val===true ? 'feat-on' : 'feat-off';
            let cls2 = val===false ? 'bg-danger text-white' : 'bg-light text-muted';
            _userFeatData[k] = val;
            html += `<div class="col-md-6 d-flex align-items-center justify-content-between border rounded p-2">
                <span>${label}</span>
                <div class="d-flex gap-1">
                    <span class="feat-toggle ${cls0}" onclick="setUserFeat('${k}',undefined,this)" style="font-size:0.75rem">Gói</span>
                    <span class="feat-toggle ${cls1}" onclick="setUserFeat('${k}',true,this)">BẬT</span>
                    <span class="feat-toggle ${cls2}" onclick="setUserFeat('${k}',false,this)" style="font-size:0.75rem">TẮT</span>
                </div>
            </div>`;
        }
        document.getElementById('userFeatList').innerHTML = html;
        new bootstrap.Modal(document.getElementById('userFeatModal')).show();
    }
    function setUserFeat(k, v, el) {
        _userFeatData[k] = v;
        let parent = el.parentElement;
        let spans = parent.querySelectorAll('.feat-toggle');
        spans[0].className = 'feat-toggle ' + (v===undefined ? 'bg-secondary text-white' : 'bg-light text-muted');
        spans[1].className = 'feat-toggle ' + (v===true ? 'feat-on' : 'feat-off');
        spans[2].className = 'feat-toggle ' + (v===false ? 'bg-danger text-white' : 'bg-light text-muted');
    }
    async function doSaveUserFeatures() {
        let feats = {};
        for (let [k,v] of Object.entries(_userFeatData)) { if (v !== undefined) feats[k] = v; }
        await apiCall('/api/user_features', 'POST', {machine_id: _userFeatMid, features: feats});
        bootstrap.Modal.getInstance(document.getElementById('userFeatModal')).hide();
        alert('Đã lưu!'); loadData();
    }

    // ── Global Features Modal ──
    function openFeaturesModal() {
        let tbody = document.getElementById('featTableBody');
        let html = '';
        for (let [k, label] of Object.entries(FEAT_CATALOG)) {
            html += `<tr><td class="text-start">${label}</td>`;
            for (let t of ['basic','pro','premium']) {
                let on = globalFeatures[t][k] === true || globalFeatures[t][k] === undefined && false;
                let id = `gf_${t}_${k}`;
                html += `<td><span id="${id}" class="feat-toggle ${on?'feat-on':'feat-off'}" onclick="toggleGlobalFeat('${t}','${k}','${id}')">${on?'BẬT':'TẮT'}</span></td>`;
            }
            html += '</tr>';
        }
        tbody.innerHTML = html;
        new bootstrap.Modal(document.getElementById('featuresModal')).show();
    }
    function toggleGlobalFeat(tier, key, id) {
        let el = document.getElementById(id);
        let on = el.classList.contains('feat-on');
        globalFeatures[tier][key] = !on;
        el.className = 'feat-toggle ' + (!on ? 'feat-on' : 'feat-off');
        el.innerText = !on ? 'BẬT' : 'TẮT';
    }
    async function doSaveGlobalFeatures() {
        let payload = {};
        for (let t of ['basic','pro','premium']) payload['features_'+t] = JSON.stringify(globalFeatures[t]);
        await apiCall('/api/settings', 'POST', payload);
        bootstrap.Modal.getInstance(document.getElementById('featuresModal')).hide();
        alert('Đã lưu tính năng theo gói!'); loadData();
    }

    // ══ v4: Tab switching ══
    function showTab(name) {
        document.getElementById('tabUsers').classList.add('d-none');
        document.getElementById('tabStats').classList.add('d-none');
        document.getElementById('tabLogs').classList.add('d-none');
        document.querySelectorAll('.navbar-nav .nav-link').forEach(a => a.classList.remove('active'));

        if (name === 'users') {
            document.getElementById('tabUsers').classList.remove('d-none');
            document.querySelector('.navbar-nav .nav-link:nth-child(1)')?.classList.add('active');
        } else if (name === 'stats') {
            document.getElementById('tabStats').classList.remove('d-none');
            document.querySelectorAll('.navbar-nav .nav-link')[1]?.classList.add('active');
            loadStats();
        } else if (name === 'logs') {
            document.getElementById('tabLogs').classList.remove('d-none');
            document.querySelectorAll('.navbar-nav .nav-link')[2]?.classList.add('active');
            loadLogs();
        }
    }
    // Fix nav-link click handlers
    document.querySelectorAll('.navbar-nav .nav-link').forEach((a, i) => {
        a.addEventListener('click', (e) => {
            e.preventDefault();
            showTab(['users','stats','logs'][i]);
        });
    });

    // ══ v4: Stats ══
    async function loadStats() {
        try {
            let data = await apiCall('/api/stats');
            document.getElementById('statTotal').innerText = data.total || 0;
            document.getElementById('statActive').innerText = (data.by_status||{}).active || 0;
            document.getElementById('statRevoked').innerText = (data.by_status||{}).revoked || 0;
            document.getElementById('statActive7d').innerText = data.active_7d || 0;
            document.getElementById('statExpiring').innerText = data.expiring_30d || 0;

            // Tier chart (simple bars)
            let total = data.total || 1;
            let tierColors = {basic:'#64748B', pro:'#2563EB', premium:'#7C3AED'};
            let html = '';
            for (let t of ['basic','pro','premium']) {
                let count = (data.by_tier||{})[t] || 0;
                let pct = Math.max(Math.round(count/total*100), 1);
                html += `<div class="mb-2"><strong>${t.toUpperCase()}: ${count}</strong>
                    <div class="progress" style="height:24px"><div class="progress-bar" role="progressbar" style="width:${pct}%;background:${tierColors[t]}">${pct}%</div></div></div>`;
            }
            document.getElementById('tierChart').innerHTML = html;
        } catch(e) { console.error('Stats error', e); }
    }

    // ══ v4: Logs ══
    async function loadLogs() {
        let tbody = document.getElementById('logsTableBody');
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4">Đang tải...</td></tr>';
        try {
            let data = await apiCall('/api/logs');
            let logs = data.logs || [];
            if (!logs.length) { tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">Không có log (bảng activity_logs chưa tồn tại?)</td></tr>'; return; }
            let html = '';
            logs.forEach(l => {
                html += `<tr>
                    <td style="font-size:0.85rem">${(l.created_at||'').substring(0,19)}</td>
                    <td><span class="badge bg-secondary">${l.action||''}</span></td>
                    <td class="font-monospace" style="font-size:0.85rem">${l.target_mid||''}</td>
                    <td style="font-size:0.85rem">${l.admin_mid||''}</td>
                    <td style="font-size:0.85rem">${l.details||''}</td>
                </tr>`;
            });
            tbody.innerHTML = html;
        } catch(e) { tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-danger">Lỗi tải log</td></tr>'; }
    }

    // ══ v4: Sidebar toggle ══
    let sidebarOpen = true;
    function toggleSidebar() {
        let panel = document.getElementById('sidebarPanel');
        let btn = document.getElementById('btnToggleSidebar');
        let icon = document.getElementById('sidebarIcon');
        sidebarOpen = !sidebarOpen;
        if (sidebarOpen) {
            panel.classList.remove('collapsed');
            btn.classList.add('shifted');
            icon.className = 'fa-solid fa-angles-left';
            btn.title = 'Thu bảng điều khiển';
        } else {
            panel.classList.add('collapsed');
            btn.classList.remove('shifted');
            icon.className = 'fa-solid fa-angles-right';
            btn.title = 'Mở bảng điều khiển';
        }
    }

    // ══ v4: Card collapse ══
    function toggleCard(headerEl) {
        let body = headerEl.nextElementSibling;
        headerEl.classList.toggle('collapsed-header');
        body.classList.toggle('collapsed-body');
    }

    // Keyboard shortcut: Ctrl+B to toggle sidebar
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'b') { e.preventDefault(); toggleSidebar(); }
    });

    // Show users tab by default
    document.getElementById('tabUsers').classList.remove('d-none');
    loadData();
</script>
</body>
</html>
"""

# =====================================================================
# BACKEND API
# =====================================================================

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Kiểm tra nhanh env var + kết nối Supabase. Dùng để debug khi 'không kích hoạt được'."""
    url, key, source = get_supabase_config()
    result = {
        'ok': False,
        'has_supabase_url': bool(url),
        'has_supabase_key': bool(key),
        'config_source': source,
        'url_prefix': (url or '')[:40],
    }
    try:
        db = get_db()
        r = db.table('licenses').select('machine_id', count='exact').limit(1).execute()
        result['ok'] = True
        result['licenses_count'] = getattr(r, 'count', None)
    except Exception as e:
        result['error'] = str(e)
    return jsonify(result)

@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        db = get_db()
        users = db.table('licenses').select('*').order('issued_at', desc=True).execute().data
        sets = db.table('settings').select('*').execute().data
        settings = {s['key']: s['value'] for s in sets}
        return jsonify({'ok': True, 'users': users, 'settings': settings})
    except Exception as e:
        return api_error(e)

@app.route('/api/add', methods=['POST'])
def add_user():
    try:
        db = get_db()
        d = dict(request.json or {})

        # Chuẩn hoá & validate
        mid = (d.get('machine_id') or '').strip().upper()
        if not mid:
            return jsonify({'ok': False, 'error': 'Machine ID rỗng'}), 400
        d['machine_id'] = mid

        # Nếu expiry là chuỗi rỗng → gửi None (Postgres date column không chấp nhận '')
        if not d.get('expiry'):
            d['expiry'] = None

        # Loại bỏ key rỗng không cần thiết (tránh ghi đè nhầm)
        for k in ('admin_api_key', 'note', 'name'):
            if k in d and d[k] is None:
                d[k] = ''

        d['issued_at'] = datetime.now().isoformat()
        d['status'] = 'active'

        db.table('licenses').upsert(d).execute()
        return jsonify({'ok': True, 'machine_id': mid})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/status', methods=['POST'])
def change_status():
    try:
        db = get_db()
        d = request.json or {}
        mid = (d.get('machine_id') or '').strip().upper()
        status = d.get('status', 'active')
        if not mid:
            return jsonify({'ok': False, 'error': 'Machine ID rỗng'}), 400
        resp = db.table('licenses').update({'status': status}).eq('machine_id', mid).execute()
        if not resp.data:
            return jsonify({'ok': False, 'error': f'Không tìm thấy máy {mid}. Thêm máy trước khi kích hoạt.'}), 404
        return jsonify({'ok': True, 'updated': len(resp.data)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/tier', methods=['POST'])
def change_tier():
    try:
        db = get_db()
        d = request.json or {}
        mid = (d.get('machine_id') or '').strip().upper()
        if not mid:
            return jsonify({'ok': False, 'error': 'Machine ID rỗng'}), 400
        db.table('licenses').update({'tier': d['tier']}).eq('machine_id', mid).execute()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/expiry', methods=['POST'])
def change_expiry():
    try:
        db = get_db()
        d = request.json or {}
        mid = (d.get('machine_id') or '').strip().upper()
        if not mid:
            return jsonify({'ok': False, 'error': 'Machine ID rỗng'}), 400
        expiry = d.get('expiry', '')
        db.table('licenses').update({'expiry': expiry if expiry else None}).eq('machine_id', mid).execute()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/apikey', methods=['POST'])
def set_api_key():
    try:
        db = get_db()
        d = request.json or {}
        mid = (d.get('machine_id') or '').strip().upper()
        if not mid:
            return jsonify({'ok': False, 'error': 'Machine ID rỗng'}), 400
        db.table('licenses').update({'admin_api_key': d.get('admin_api_key', '')}).eq('machine_id', mid).execute()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# ── Activate endpoint (upsert + set active trong 1 call) ─────────────────
@app.route('/api/activate', methods=['POST'])
def activate_machine():
    """Kích hoạt máy: nếu chưa có → thêm mới; nếu đã có → set active + gia hạn.

    Body: {machine_id, tier?, expiry?, name?, note?, admin_api_key?}
    """
    try:
        db = get_db()
        d = dict(request.json or {})
        mid = (d.get('machine_id') or '').strip().upper()
        if not mid:
            return jsonify({'ok': False, 'error': 'Machine ID rỗng'}), 400

        # Chuẩn hoá
        if not d.get('expiry'):
            d['expiry'] = None
        d['machine_id'] = mid
        d['status'] = 'active'
        d.setdefault('tier', 'pro')
        d['issued_at'] = datetime.now().isoformat()

        # upsert — Supabase sẽ insert nếu chưa có, update nếu có
        resp = db.table('licenses').upsert(d).execute()
        return jsonify({'ok': True, 'record': resp.data[0] if resp.data else None})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/user_features', methods=['POST'])
def set_user_features():
    try:
        db = get_db()
        d = request.json or {}
        mid = (d.get('machine_id') or '').strip().upper()
        if not mid:
            return jsonify({'ok': False, 'error': 'Machine ID rỗng'}), 400
        features = d.get('features', {})
        db.table('licenses').update({'features': json.dumps(features, ensure_ascii=False)}).eq('machine_id', mid).execute()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/bulk_status', methods=['POST'])
def bulk_status():
    try:
        db = get_db()
        d = request.json or {}
        if d.get('action') == 'lock':
            db.table('licenses').update({'status': 'revoked'}).eq('status', 'active').execute()
        else:
            db.table('licenses').update({'status': 'active'}).eq('status', 'revoked').execute()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/settings', methods=['POST'])
def save_settings():
    try:
        db = get_db()
        d = request.json or {}
        for k, v in d.items():
            val = str(v).lower() if isinstance(v, bool) else str(v)
            db.table('settings').upsert({'key': k, 'value': val}).execute()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/delete', methods=['POST'])
def delete_user():
    try:
        db = get_db()
        d = request.json or {}
        mid = (d.get('machine_id') or '').strip().upper()
        if not mid:
            return jsonify({'ok': False, 'error': 'Machine ID rỗng'}), 400
        db.table('licenses').delete().eq('machine_id', mid).execute()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# ── NEW v4: Stats API ────────────────────────────────────────────────────
@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        db = get_db()
        users = db.table('licenses').select('status, tier, last_check, expiry').execute().data or []
        total = len(users)
        by_status = {}
        by_tier = {}
        for u in users:
            s = u.get('status', 'unknown')
            t = u.get('tier', 'basic')
            by_status[s] = by_status.get(s, 0) + 1
            by_tier[t] = by_tier.get(t, 0) + 1

        from datetime import timedelta
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        active_7d = sum(1 for u in users if u.get('last_check') and u['last_check'] >= week_ago)

        # Expiring in 30 days
        cutoff = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        expiring = [u for u in users if u.get('expiry') and today < u['expiry'] <= cutoff and u.get('status') == 'active']

        return jsonify({
            'ok': True,
            'total': total,
            'by_status': by_status,
            'by_tier': by_tier,
            'active_7d': active_7d,
            'expiring_30d': len(expiring),
        })
    except Exception as e:
        return api_error(e)


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Lấy log hoạt động admin từ bảng activity_logs."""
    try:
        db = get_db()
        limit = int(request.args.get('limit', 200))
        resp = db.table('activity_logs').select('*').order('created_at', desc=True).limit(limit).execute()
        return jsonify({'logs': resp.data or []})
    except Exception as e:
        return jsonify({'logs': [], 'note': f'activity_logs table may not exist: {e}'})


@app.route('/api/log_action', methods=['POST'])
def log_action():
    """Ghi hành động admin vào activity_logs."""
    try:
        db = get_db()
        d = request.json
        db.table('activity_logs').insert({
            'admin_mid': d.get('admin_mid', ''),
            'action': d.get('action', ''),
            'target_mid': d.get('target_mid', ''),
            'details': d.get('details', ''),
        }).execute()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})


@app.route('/api/export', methods=['GET'])
def export_data():
    """Xuất dữ liệu JSON (full backup)."""
    try:
        db = get_db()
        users = db.table('licenses').select('*').order('issued_at', desc=True).execute().data or []
        return jsonify({
            'ok': True,
            'exported_at': datetime.now().isoformat(),
            'total': len(users),
            'records': users,
        })
    except Exception as e:
        return api_error(e)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
