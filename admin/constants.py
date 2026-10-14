"""
admin/constants.py — Hằng số dùng chung cho admin package.
"""

TIER_LABELS = {
    "basic":   "🥉 Basic — 2 đề/ngày (tự nhập key)",
    "pro":     "🥈 Pro — Admin cấp API key",
    "premium": "🏆 Pre — Toàn quyền + API key ưu tiên",
}

STATUS_BG = {
    "active":   "#E8F5E9",
    "revoked":  "#FFEBEE",
    "expired":  "#FFF3E0",
    "suspended":"#FFF3E0",
}

TIER_STYLES = {
    "basic":   {"bg": "#64748B", "text": "🥉  BASIC — 2 đề/ngày, tự nhập key"},
    "pro":     {"bg": "#2563EB", "text": "🥈  PRO — Admin cấp API key"},
    "premium": {"bg": "#7C3AED", "text": "🏆  PREMIUM — Toàn quyền + ưu tiên"},
}

TIER_OFF_BG = "#F1F5F9"
TIER_OFF_FG = "#64748B"

DEFAULT_PRICING_V2 = {
    "basic": {
        "name": "BASIC", "color": "#64748B",
        "desc": "2 đề/ngày, tự nhập API Key",
        "durations": [
            {"duration": "1 tháng",  "price": "99.000 ₫",   "hot": False, "enabled": True},
            {"duration": "3 tháng",  "price": "259.000 ₫",  "hot": False, "enabled": True},
            {"duration": "6 tháng",  "price": "479.000 ₫",  "hot": True,  "enabled": True},
            {"duration": "12 tháng", "price": "899.000 ₫",  "hot": False, "enabled": True},
        ],
    },
    "pro": {
        "name": "PRO", "color": "#2563EB",
        "desc": "Admin cấp API Key, tạo đề nhanh",
        "durations": [
            {"duration": "1 tháng",  "price": "199.000 ₫",   "hot": False, "enabled": True},
            {"duration": "3 tháng",  "price": "569.000 ₫",   "hot": False, "enabled": True},
            {"duration": "6 tháng",  "price": "1.099.000 ₫", "hot": True,  "enabled": True},
            {"duration": "12 tháng", "price": "1.999.000 ₫", "hot": False, "enabled": True},
        ],
    },
    "premium": {
        "name": "PREMIUM", "color": "#7C3AED",
        "desc": "Toàn quyền + API key ưu tiên",
        "durations": [
            {"duration": "1 tháng",  "price": "299.000 ₫",   "hot": False, "enabled": True},
            {"duration": "3 tháng",  "price": "849.000 ₫",   "hot": False, "enabled": True},
            {"duration": "6 tháng",  "price": "1.599.000 ₫", "hot": True,  "enabled": True},
            {"duration": "12 tháng", "price": "2.999.000 ₫", "hot": False, "enabled": True},
        ],
    },
}
