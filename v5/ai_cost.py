"""
v5/ai_cost.py — Tính cost USD cho AI calls dựa trên model + tokens.

Bảng giá tham khảo (USD per 1M tokens, tháng 4/2025):
    • Gemini 2.5 Flash:  $0.30 in  / $2.50 out
    • Gemini 2.5 Pro:    $1.25 in  / $10   out
    • Claude Haiku 4:    $0.25 in  / $1.25 out
    • Claude Sonnet 4:   $3       / $15
    • Claude Opus 4:     $15      / $75
    • GPT-4o:            $2.50    / $10
    • GPT-4o-mini:       $0.15    / $0.60
    • GPT-5:             $1.25    / $10
    • DeepSeek Chat:     $0.27    / $1.10

Khi có model mới chưa biết → fallback _DEFAULT_PRICE.
Khi log entry không có tokens_in/out → cost = 0.
"""
from __future__ import annotations

# Pricing: (in_per_1M_USD, out_per_1M_USD)
_PRICES: dict[str, tuple[float, float]] = {
    # Google
    "gemini-2.5-flash":         (0.30,  2.50),
    "gemini-2.5-flash-lite":    (0.10,  0.40),
    "gemini-2.5-pro":           (1.25, 10.00),
    "gemini-2.0-flash":         (0.075, 0.30),
    "gemini-1.5-flash":         (0.075, 0.30),
    "gemini-1.5-pro":           (1.25,  5.00),

    # Anthropic
    "claude-haiku-4":           (0.25,  1.25),
    "claude-haiku-4-5":         (0.25,  1.25),
    "claude-sonnet-4":          (3.00, 15.00),
    "claude-sonnet-4-5":        (3.00, 15.00),
    "claude-sonnet-4-7":        (3.00, 15.00),
    "claude-opus-4":            (15.00, 75.00),
    "claude-opus-4-1":          (15.00, 75.00),
    "claude-3-5-sonnet":        (3.00, 15.00),
    "claude-3-5-haiku":         (0.80,  4.00),

    # OpenAI
    "gpt-5":                    (1.25, 10.00),
    "gpt-5-mini":               (0.25,  2.00),
    "gpt-4o":                   (2.50, 10.00),
    "gpt-4o-mini":              (0.15,  0.60),
    "gpt-4.1":                  (2.00,  8.00),
    "o3":                       (15.00, 60.00),
    "o4-mini":                  (1.10,  4.40),

    # DeepSeek
    "deepseek-chat":            (0.27,  1.10),
    "deepseek-reasoner":        (0.55,  2.19),
}

_DEFAULT_PRICE = (1.00, 3.00)    # fallback nếu model lạ


def _norm(model: str) -> str:
    """Chuẩn hoá tên model về key trong _PRICES.

    VD: 'gemini-2.5-flash-preview-0915' → 'gemini-2.5-flash'
        'models/gemini-1.5-pro-latest'  → 'gemini-1.5-pro'
    """
    if not model: return ""
    m = model.lower().strip()
    # Bỏ prefix 'models/'
    if m.startswith("models/"):
        m = m[7:]
    # Bỏ suffix '-latest', '-preview-XXXX', '-YYYYMMDD'
    for sfx in ("-latest",):
        if m.endswith(sfx):
            m = m[:-len(sfx)]
    # Match longest prefix trong _PRICES
    candidates = sorted([k for k in _PRICES if m.startswith(k)],
                          key=lambda x: -len(x))
    return candidates[0] if candidates else m


def estimate_cost(model: str, tokens_in: int = 0, tokens_out: int = 0
                    ) -> float:
    """Trả về USD cost (float, làm tròn 6 decimal)."""
    key = _norm(model)
    price_in, price_out = _PRICES.get(key, _DEFAULT_PRICE)
    cost = (tokens_in / 1_000_000) * price_in \
           + (tokens_out / 1_000_000) * price_out
    return round(cost, 6)


def estimate_cost_from_log(entries: list[dict]) -> float:
    """Tính tổng cost từ list log entries."""
    total = 0.0
    for e in entries or []:
        try:
            total += estimate_cost(
                e.get("model", ""),
                int(e.get("tokens_in", 0) or 0),
                int(e.get("tokens_out", 0) or 0))
        except Exception: continue
    return round(total, 4)


def format_cost(cost_usd: float) -> str:
    """Format USD → human string. <0.01 → milli (vd '5m₵')."""
    if cost_usd >= 100:
        return f"${cost_usd:,.0f}"
    if cost_usd >= 1:
        return f"${cost_usd:,.2f}"
    if cost_usd >= 0.01:
        return f"${cost_usd:.3f}"
    if cost_usd >= 0.0001:
        return f"${cost_usd * 1000:.2f}m"   # mili-dollar
    return "<$0.0001"
