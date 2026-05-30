# =============================================================================
# scorer.py — Swing Trading Score Engine v2.0
# Phase 3B — Added breakout signal + promoter scoring
# =============================================================================

import logging
from config import SCORE_WEIGHTS, GRADES, FUND, TECH

logger = logging.getLogger(__name__)


def score_technicals(tech: dict, weights: dict) -> tuple:
    breakdown = {}
    total     = 0.0

    # 1. EMA Alignment (20 > 50 > 200)
    w = weights["ema_alignment"]
    if tech.get("signal_ema_stack"):
        pts = w
    elif tech.get("signal_price_ema50") and tech.get("ema50",0) > tech.get("ema200",0):
        pts = w * 0.6
    elif tech.get("signal_price_ema200"):
        pts = w * 0.3
    else:
        pts = 0
    breakdown["EMA Alignment"] = round(pts, 1)
    total += pts

    # 2. Price > EMA 20
    w   = weights["price_above_ema20"]
    pts = w if tech.get("signal_price_ema20") else 0
    breakdown["Price > EMA20"] = pts
    total += pts

    # 3. RSI Zone (50–72)
    w       = weights["rsi_zone"]
    rsi_val = tech.get("rsi", 0)
    if tech.get("signal_rsi_zone"):
        pts = w if 55 <= rsi_val <= 65 else w * 0.7
    elif 45 <= rsi_val < 50:
        pts = w * 0.3
    else:
        pts = 0
    breakdown["RSI Zone"] = round(pts, 1)
    total += pts

    # 4. MACD
    w = weights["macd_signal"]
    if tech.get("signal_macd_cross"):
        pts = w                    # Fresh crossover — best signal
    elif tech.get("signal_macd_bullish"):
        pts = w * 0.6
    else:
        pts = 0
    breakdown["MACD"] = round(pts, 1)
    total += pts

    # 5. ADX Trend Strength
    w       = weights["adx_strength"]
    adx_val = tech.get("adx", 0)
    if adx_val >= 30:
        pts = w
    elif adx_val >= TECH["adx_min"]:
        pts = w * 0.6
    else:
        pts = 0
    breakdown["ADX"] = round(pts, 1)
    total += pts

    # 6. Volume Confirmation
    w         = weights["volume_confirm"]
    vol_ratio = tech.get("vol_ratio", 0)
    if vol_ratio >= 2.0:
        pts = w
    elif vol_ratio >= TECH["volume_multiplier"]:
        pts = w * 0.6
    elif vol_ratio >= 1.0:
        pts = w * 0.3
    else:
        pts = 0
    breakdown["Volume"] = round(pts, 1)
    total += pts

    # 7. ── NEW Phase 3B — Breakout Signal ────────────────────────────────
    w = weights.get("breakout_signal", 6)

    if tech.get("signal_vcp_breakout"):
        # VCP + 20d breakout = highest quality (Mark Minervini method)
        pts = w
        breakdown["Breakout"] = round(pts, 1)
    elif tech.get("signal_breakout_confirmed"):
        # 20d breakout + volume + above EMA50 = confirmed breakout
        pts = w * 0.85
        breakdown["Breakout"] = round(pts, 1)
    elif tech.get("is_20d_breakout"):
        # Plain 20d breakout — partial credit
        pts = w * 0.5
        breakdown["Breakout"] = round(pts, 1)
    elif tech.get("signal_52w_momentum"):
        # Near 52W high + EMA stack = momentum leadership
        pts = w * 0.4
        breakdown["Breakout"] = round(pts, 1)
    elif tech.get("is_near_52w_high"):
        # Just near 52W high
        pts = w * 0.25
        breakdown["Breakout"] = round(pts, 1)
    else:
        pts = 0
        breakdown["Breakout"] = 0
    total += pts

    return round(total, 1), breakdown


def score_fundamentals(fund: dict, weights: dict) -> tuple:
    breakdown = {}
    total     = 0.0

    def safe(val, default=None):
        return val if val is not None else default

    # 1. ROE
    w   = weights["roe"]
    roe = safe(fund.get("roe"))
    if roe is None:        pts = w * 0.4
    elif roe >= 25:        pts = w               # Excellent
    elif roe >= 18:        pts = w * 0.85        # Good
    elif roe >= FUND["roe_min"]: pts = w * 0.65  # Acceptable
    elif roe >= 8:         pts = w * 0.3
    else:                  pts = 0
    breakdown["ROE"] = round(pts, 1)
    total += pts

    # 2. Debt / Equity
    w  = weights["debt_equity"]
    de = safe(fund.get("debt_to_equity"))
    if de is None:         pts = w * 0.5
    elif de <= 0.1:        pts = w               # Near zero debt
    elif de <= 0.5:        pts = w * 0.85
    elif de <= FUND["debt_equity_max"]: pts = w * 0.65
    elif de <= 1.5:        pts = w * 0.3
    else:                  pts = 0
    breakdown["Debt/Equity"] = round(pts, 1)
    total += pts

    # 3. Revenue Growth
    w     = weights["revenue_growth"]
    rev_g = safe(fund.get("revenue_growth"))
    if rev_g is None:      pts = w * 0.4
    elif rev_g >= 30:      pts = w
    elif rev_g >= 20:      pts = w * 0.85
    elif rev_g >= FUND["revenue_growth_min"]: pts = w * 0.65
    elif rev_g >= 0:       pts = w * 0.3
    else:                  pts = 0
    breakdown["Revenue Growth"] = round(pts, 1)
    total += pts

    # 4. Valuation (P/E)
    w  = weights["valuation"]
    pe = safe(fund.get("pe_ratio"))
    if pe is None or pe <= 0: pts = w * 0.3
    elif pe <= 15:         pts = w               # Value zone
    elif pe <= 25:         pts = w * 0.9
    elif pe <= 40:         pts = w * 0.65
    elif pe <= FUND["pe_max"]: pts = w * 0.3
    else:                  pts = 0
    breakdown["P/E Ratio"] = round(pts, 1)
    total += pts

    # 5. ── NEW Phase 3B — Promoter Holding ───────────────────────────────
    w        = weights.get("promoter_holding", 6)
    promoter = safe(fund.get("promoter_holding"))

    if promoter is None:
        pts = w * 0.4          # Unknown — neutral
    elif promoter >= 70:
        pts = w                # Strong promoter confidence
    elif promoter >= 55:
        pts = w * 0.8
    elif promoter >= FUND["promoter_holding_min"]:
        pts = w * 0.55
    elif promoter >= 25:
        pts = w * 0.2          # Low — concern
    else:
        pts = 0                # Very low — red flag
    breakdown["Promoter %"] = round(pts, 1)
    total += pts

    return round(total, 1), breakdown


def assign_grade(score: float) -> str:
    for grade, threshold in GRADES.items():
        if score >= threshold:
            return grade
    return "D"


def build_flags(tech: dict, fund: dict) -> str:
    """Generate human-readable signal flags."""
    flags = []

    # Technical flags
    if tech.get("signal_vcp_breakout"):
        flags.append("🔥 VCP Breakout")
    elif tech.get("signal_breakout_confirmed"):
        flags.append("🔥 Breakout Confirmed")
    elif tech.get("is_20d_breakout"):
        flags.append("📤 20D Breakout")

    if tech.get("signal_macd_cross"):
        flags.append("⚡ Fresh MACD Cross")
    if tech.get("signal_supertrend"):
        flags.append("✅ Supertrend Buy")
    if tech.get("signal_ema_stack"):
        flags.append("📈 EMA Bull Stack")
    if tech.get("vol_ratio", 0) >= 2.0:
        flags.append("📊 High Volume")
    if tech.get("is_at_52w_high"):
        flags.append("🏆 At 52W High")
    elif tech.get("is_near_52w_high"):
        flags.append("🏆 Near 52W High")
    if tech.get("is_vcp"):
        flags.append("🎯 VCP Pattern")
    if tech.get("is_tight_base"):
        flags.append("📉 Tight Base")

    # Fundamental flags
    roe = fund.get("roe")
    if roe and roe >= 20:
        flags.append("💎 High ROE")
    if fund.get("debt_to_equity") is not None and fund.get("debt_to_equity", 1) <= 0.1:
        flags.append("🏦 Zero Debt")
    promoter = fund.get("promoter_holding")
    if promoter and promoter >= 70:
        flags.append("👤 High Promoter")

    return " | ".join(flags)


def score_stock(symbol: str, tech: dict, fund: dict,
                weights: dict = None) -> dict:
    if weights is None:
        weights = SCORE_WEIGHTS

    tech_score, tech_breakdown = score_technicals(tech, weights)
    fund_score, fund_breakdown = score_fundamentals(fund, weights)

    total_score = tech_score + fund_score
    grade       = assign_grade(total_score)
    flags       = build_flags(tech, fund)

    return {
        "symbol":         symbol,
        "total_score":    total_score,
        "tech_score":     tech_score,
        "fund_score":     fund_score,
        "grade":          grade,
        "flags":          flags,
        "tech_breakdown": tech_breakdown,
        "fund_breakdown": fund_breakdown,
    }
