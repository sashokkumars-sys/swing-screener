# =============================================================================
# scorer.py — Swing Trading Score Engine
# Combines technical + fundamental signals into a 0–100 score with grade
# =============================================================================

import logging
from config import SCORE_WEIGHTS, GRADES, FUND, TECH

logger = logging.getLogger(__name__)


def score_technicals(tech: dict, weights: dict) -> tuple[float, dict]:
    """
    Score technical indicators. Returns (score, breakdown_dict).
    """
    breakdown = {}
    total = 0.0

    # 1. EMA Alignment — 20 > 50 > 200 (full bull stack)
    w = weights["ema_alignment"]
    if tech.get("signal_ema_stack"):
        pts = w
    elif tech.get("signal_price_ema50") and tech.get("ema50", 0) > tech.get("ema200", 0):
        pts = w * 0.6          # partial: medium-term aligned
    elif tech.get("signal_price_ema200"):
        pts = w * 0.3          # weak: only above 200 EMA
    else:
        pts = 0
    breakdown["EMA Alignment"] = round(pts, 1)
    total += pts

    # 2. Price above EMA 20
    w = weights["price_above_ema20"]
    pts = w if tech.get("signal_price_ema20") else 0
    breakdown["Price > EMA20"] = pts
    total += pts

    # 3. RSI in sweet zone (50–72)
    w = weights["rsi_zone"]
    rsi_val = tech.get("rsi", 0)
    if tech.get("signal_rsi_zone"):
        # Extra reward if RSI is between 55–65 (ideal momentum zone)
        pts = w if 55 <= rsi_val <= 65 else w * 0.7
    elif 45 <= rsi_val < 50:
        pts = w * 0.3          # just below zone — borderline
    else:
        pts = 0
    breakdown["RSI Zone"] = round(pts, 1)
    total += pts

    # 4. MACD signal
    w = weights["macd_signal"]
    if tech.get("signal_macd_cross"):
        pts = w                # Fresh crossover — maximum points
    elif tech.get("signal_macd_bullish"):
        pts = w * 0.6          # Positive histogram — partial
    else:
        pts = 0
    breakdown["MACD"] = round(pts, 1)
    total += pts

    # 5. ADX trend strength
    w = weights["adx_strength"]
    adx_val = tech.get("adx", 0)
    if adx_val >= 30:
        pts = w                # Strong trend
    elif adx_val >= TECH["adx_min"]:
        pts = w * 0.6          # Moderate trend
    else:
        pts = 0
    breakdown["ADX Strength"] = round(pts, 1)
    total += pts

    # 6. Volume confirmation
    w = weights["volume_confirm"]
    vol_ratio = tech.get("vol_ratio", 0)
    if vol_ratio >= 2.0:
        pts = w                # Strong volume
    elif vol_ratio >= TECH["volume_multiplier"]:
        pts = w * 0.6          # Above average
    elif vol_ratio >= 1.0:
        pts = w * 0.3          # Average — no penalty
    else:
        pts = 0
    breakdown["Volume"] = round(pts, 1)
    total += pts

    return round(total, 1), breakdown


def score_fundamentals(fund: dict, weights: dict) -> tuple[float, dict]:
    """
    Score fundamental ratios. Returns (score, breakdown_dict).
    Handles None values gracefully — unknown data gets partial neutral score.
    """
    breakdown = {}
    total = 0.0

    def safe(val, default=None):
        return val if val is not None else default

    # 1. ROE — Return on Equity
    w = weights["roe"]
    roe = safe(fund.get("roe"))
    if roe is None:
        pts = w * 0.4          # Unknown — neutral
    elif roe >= 20:
        pts = w                # Excellent
    elif roe >= FUND["roe_min"]:
        pts = w * 0.7          # Good
    elif roe >= 8:
        pts = w * 0.3          # Weak but positive
    else:
        pts = 0
    breakdown["ROE"] = round(pts, 1)
    total += pts

    # 2. Debt to Equity
    w = weights["debt_equity"]
    de = safe(fund.get("debt_to_equity"))
    if de is None:
        pts = w * 0.5          # Unknown
    elif de <= 0.2:
        pts = w                # Debt-free or near
    elif de <= FUND["debt_equity_max"]:
        pts = w * 0.7          # Low debt
    elif de <= 1.5:
        pts = w * 0.3          # Moderate debt
    else:
        pts = 0                # High debt — red flag
    breakdown["Debt/Equity"] = round(pts, 1)
    total += pts

    # 3. Revenue Growth
    w = weights["revenue_growth"]
    rev_g = safe(fund.get("revenue_growth"))
    if rev_g is None:
        pts = w * 0.4          # Unknown
    elif rev_g >= 25:
        pts = w                # High growth
    elif rev_g >= FUND["revenue_growth_min"]:
        pts = w * 0.7          # Decent growth
    elif rev_g >= 0:
        pts = w * 0.3          # Flat but positive
    else:
        pts = 0                # Revenue decline
    breakdown["Revenue Growth"] = round(pts, 1)
    total += pts

    # 4. Valuation (P/E)
    w = weights["valuation"]
    pe = safe(fund.get("pe_ratio"))
    if pe is None or pe <= 0:
        pts = w * 0.3          # Unknown or negative earnings
    elif pe <= 20:
        pts = w                # Undervalued / value zone
    elif pe <= 35:
        pts = w * 0.8          # Reasonable
    elif pe <= FUND["pe_max"]:
        pts = w * 0.4          # High but acceptable
    else:
        pts = 0                # Extremely overvalued
    breakdown["P/E Ratio"] = round(pts, 1)
    total += pts

    return round(total, 1), breakdown


def assign_grade(score: float) -> str:
    for grade, threshold in GRADES.items():
        if score >= threshold:
            return grade
    return "D"


def score_stock(symbol: str, tech: dict, fund: dict,
                weights: dict = None) -> dict:
    """
    Master scoring function. Combines technical + fundamental scores.
    Returns complete score card for the stock.
    """
    if weights is None:
        weights = SCORE_WEIGHTS

    tech_score, tech_breakdown = score_technicals(tech, weights)
    fund_score, fund_breakdown = score_fundamentals(fund, weights)

    total_score = tech_score + fund_score
    grade = assign_grade(total_score)

    # Bonus flags for human review
    flags = []
    if tech.get("signal_macd_cross"):
        flags.append("🔥 Fresh MACD Cross")
    if tech.get("signal_supertrend"):
        flags.append("✅ Supertrend Buy")
    if tech.get("signal_ema_stack"):
        flags.append("📈 EMA Bull Stack")
    if tech.get("vol_ratio", 0) >= 2.0:
        flags.append("📊 High Volume")
    if tech.get("pct_from_52w_high", 0) >= 95:
        flags.append("🏆 Near 52W High")
    if fund.get("roe", 0) and fund.get("roe", 0) >= 20:
        flags.append("💎 High ROE")
    if fund.get("debt_to_equity") == 0:
        flags.append("🏦 Zero Debt")

    return {
        "symbol":           symbol,
        "total_score":      total_score,
        "tech_score":       tech_score,
        "fund_score":       fund_score,
        "grade":            grade,
        "flags":            " | ".join(flags),
        "tech_breakdown":   tech_breakdown,
        "fund_breakdown":   fund_breakdown,
    }
