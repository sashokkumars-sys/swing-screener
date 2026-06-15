# =============================================================================
# zscore_expectancy.py — Z-Score + Expectancy + Half-Kelly
# Add to technicals.py (z_score) and use in scorer.py + report.py
# =============================================================================

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Z-SCORE
# Measures how far current price is from its 20-day mean
# in standard deviation units
# ---------------------------------------------------------------------------

def compute_zscore(close: pd.Series, period: int = 20) -> float:
    """
    Z = (Price - Mean) / StdDev
    Interpretation:
      z < -2.0  → Strong mean reversion buy signal
      z < -1.0  → Mild pullback — potential entry zone
      -1 to +1  → Neutral — trend continuation zone
      z > +2.0  → Overbought — avoid entry
      z > +3.0  → Extreme — fade the move (contrarian only)
    """
    if len(close) < period:
        return 0.0

    window  = close.iloc[-period:]
    mean    = window.mean()
    std     = window.std()

    if std == 0:
        return 0.0

    z = (close.iloc[-1] - mean) / std
    return round(float(z), 3)


def zscore_signal(z: float) -> dict:
    """
    Translate z-score into actionable signal for scorer.
    Returns signal dict with label, score adjustment, and action.
    """
    if z < -2.0:
        return {
            "label":       "🔵 Mean Reversion Zone",
            "action":      "Strong pullback — high probability bounce",
            "score_adj":   +5,     # bonus points — rare high-value setup
            "zone":        "reversion",
        }
    elif z < -1.0:
        return {
            "label":       "🟦 Mild Pullback",
            "action":      "Healthy pullback in uptrend — watch for bounce",
            "score_adj":   +2,
            "zone":        "pullback",
        }
    elif z <= 1.0:
        return {
            "label":       "⬜ Neutral Zone",
            "action":      "Trend continuation plays work here",
            "score_adj":   0,
            "zone":        "neutral",
        }
    elif z <= 2.0:
        return {
            "label":       "🟧 Extended",
            "action":      "Price stretched above mean — wait for pullback",
            "score_adj":   -3,     # penalty — risk of immediate reversion
            "zone":        "extended",
        }
    else:
        return {
            "label":       "🔴 Overbought",
            "action":      "Avoid entry — high reversion risk",
            "score_adj":   -6,
            "zone":        "overbought",
        }


# ---------------------------------------------------------------------------
# EXPECTANCY
# Expected rupee gain per ₹10,000 risked, before placing the trade
# E = (W × Avg_Win_R) - ((1-W) × Avg_Loss_R)
# Where R = reward in multiples of risk (R-multiple)
# ---------------------------------------------------------------------------

def compute_expectancy(
    win_rate: float,
    reward_risk: float,
    risk_per_trade: float = 10000,
) -> dict:
    """
    Args:
        win_rate:      Historical win rate as decimal (e.g. 0.55 = 55%)
                       Use 0.50 as placeholder until real data exists
        reward_risk:   Target / Stop Loss distance ratio (e.g. 2.0 = 1:2 R:R)
        risk_per_trade: Rupees risked per trade (default ₹10,000)

    Returns:
        dict with expectancy, edge, and Kelly fraction
    """
    # Validate
    win_rate    = max(0.01, min(0.99, win_rate))
    reward_risk = max(0.1, reward_risk)

    loss_rate = 1 - win_rate

    # Expectancy in R-multiples
    expectancy_r = (win_rate * reward_risk) - (loss_rate * 1.0)

    # Expectancy in rupees per ₹10,000 risked
    expectancy_rs = expectancy_r * risk_per_trade

    # Edge percentage
    edge_pct = expectancy_r * 100

    # ---------------------------------------------------------------------------
    # KELLY CRITERION
    # K = W - (1-W)/R
    # Half-Kelly used because full Kelly causes 30-50% drawdowns
    # even when math is correct (parameter estimation error)
    # ---------------------------------------------------------------------------
    kelly_full = win_rate - (loss_rate / reward_risk)
    kelly_half = kelly_full / 2    # Half-Kelly — standard practice

    # Cap Kelly at 25% — never risk more than 25% on any single trade
    kelly_half = max(0.0, min(0.25, kelly_half))

    # Position size in rupees given capital
    # (caller passes total_capital separately)

    return {
        "win_rate":       round(win_rate * 100, 1),
        "reward_risk":    round(reward_risk, 2),
        "expectancy_r":   round(expectancy_r, 3),
        "expectancy_rs":  round(expectancy_rs, 0),
        "edge_pct":       round(edge_pct, 1),
        "kelly_full":     round(kelly_full * 100, 1),
        "kelly_half":     round(kelly_half * 100, 1),
        "is_positive_edge": expectancy_r > 0,
        "label":          _expectancy_label(expectancy_r),
    }


def _expectancy_label(e: float) -> str:
    if e >= 0.5:   return "🟢 Strong Edge"
    elif e >= 0.2: return "🟡 Moderate Edge"
    elif e >= 0.0: return "🟠 Marginal Edge"
    else:          return "🔴 Negative Edge — Do Not Trade"


def position_size(
    total_capital: float,
    kelly_half_pct: float,
    entry_price: float,
    stop_loss_price: float,
    max_risk_pct: float = 0.02,   # hard cap: never risk more than 2%
) -> dict:
    """
    Calculate position size using Half-Kelly AND hard 2% risk cap.
    Takes the MORE CONSERVATIVE of the two.

    Args:
        total_capital:   Total paper/real capital in ₹
        kelly_half_pct:  Half-Kelly fraction as % (e.g. 8.5 for 8.5%)
        entry_price:     Entry price per share
        stop_loss_price: Stop loss price per share
        max_risk_pct:    Hard cap on capital risked (default 2%)
    """
    if entry_price <= stop_loss_price:
        return {"error": "Entry must be above stop loss"}

    risk_per_share = entry_price - stop_loss_price

    # Kelly-based allocation
    kelly_capital  = total_capital * (kelly_half_pct / 100)
    kelly_shares   = int(kelly_capital / entry_price)

    # Hard 2% risk cap allocation
    max_risk_rs    = total_capital * max_risk_pct
    cap_shares     = int(max_risk_rs / risk_per_share)

    # Take the conservative number
    final_shares   = min(kelly_shares, cap_shares)
    final_shares   = max(1, final_shares)   # at least 1 share

    total_invested = round(final_shares * entry_price, 0)
    total_risk     = round(final_shares * risk_per_share, 0)
    risk_pct       = round((total_risk / total_capital) * 100, 2)

    return {
        "shares":         final_shares,
        "total_invested": total_invested,
        "total_risk_rs":  total_risk,
        "risk_pct":       risk_pct,
        "kelly_shares":   kelly_shares,
        "cap_shares":     cap_shares,
        "limiting_factor": "Kelly" if kelly_shares < cap_shares else "2% Cap",
    }


# ---------------------------------------------------------------------------
# CONVENIENCE: Full pre-trade analysis for a single stock
# Call this from main.py or a Telegram command
# ---------------------------------------------------------------------------

def pre_trade_analysis(
    symbol:         str,
    close_prices:   pd.Series,
    entry_price:    float,
    stop_loss:      float,
    target:         float,
    total_capital:  float,
    win_rate:       float = 0.50,   # placeholder until real data
    zscore_period:  int   = 20,
) -> dict:
    """
    Complete pre-trade decision package.
    Returns everything needed to decide: enter or skip.
    """
    # Z-Score
    z     = compute_zscore(close_prices, zscore_period)
    z_sig = zscore_signal(z)

    # R:R
    risk   = entry_price - stop_loss
    reward = target - entry_price
    rr     = round(reward / risk, 2) if risk > 0 else 0

    # Expectancy
    exp = compute_expectancy(win_rate, rr)

    # Position size
    pos = position_size(total_capital, exp["kelly_half"], entry_price, stop_loss)

    # Final verdict
    proceed = (
        exp["is_positive_edge"] and
        rr >= 1.5 and
        z_sig["zone"] not in ("overbought",) and
        risk > 0
    )

    return {
        "symbol":        symbol,
        "entry":         entry_price,
        "stop_loss":     stop_loss,
        "target":        target,
        "risk_per_share": round(risk, 2),
        "reward_per_share": round(reward, 2),
        "reward_risk":   rr,
        "z_score":       z,
        "z_signal":      z_sig,
        "expectancy":    exp,
        "position":      pos,
        "proceed":       proceed,
        "verdict":       "✅ ENTER" if proceed else "⛔ SKIP",
        "note": (
            f"Win rate used: {win_rate*100:.0f}% (placeholder — "
            "update after 30 real trades)"
            if win_rate == 0.50 else
            f"Win rate: {win_rate*100:.1f}% from your trade history"
        ),
    }


# ---------------------------------------------------------------------------
# Pretty print for Telegram / console
# ---------------------------------------------------------------------------

def format_pre_trade(analysis: dict) -> str:
    e   = analysis["expectancy"]
    pos = analysis["position"]
    z   = analysis["z_signal"]

    lines = [
        f"📊 PRE-TRADE ANALYSIS — {analysis['symbol']}",
        f"{'─'*35}",
        f"Entry:      ₹{analysis['entry']:,.0f}",
        f"Stop Loss:  ₹{analysis['stop_loss']:,.0f}  "
        f"(Risk: ₹{analysis['risk_per_share']}/share)",
        f"Target:     ₹{analysis['target']:,.0f}  "
        f"(Reward: ₹{analysis['reward_per_share']}/share)",
        f"R:R Ratio:  1:{analysis['reward_risk']}",
        f"",
        f"📐 Z-Score:  {analysis['z_score']}  {z['label']}",
        f"   → {z['action']}",
        f"",
        f"🎯 Expectancy:",
        f"   Per ₹10,000 risked: ₹{e['expectancy_rs']:,.0f}",
        f"   Edge: {e['edge_pct']}%  {e['label']}",
        f"",
        f"🃏 Kelly Criterion:",
        f"   Full Kelly: {e['kelly_full']}%  →  "
        f"Half-Kelly: {e['kelly_half']}%",
        f"",
        f"📦 Position Size:",
        f"   Shares:    {pos['shares']}",
        f"   Invested:  ₹{pos['total_invested']:,.0f}",
        f"   At Risk:   ₹{pos['total_risk_rs']:,.0f} ({pos['risk_pct']}%)",
        f"   Limited by: {pos['limiting_factor']}",
        f"",
        f"{'─'*35}",
        f"VERDICT:  {analysis['verdict']}",
        f"",
        f"⚠️  {analysis['note']}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import pandas as pd
    import numpy as np

    np.random.seed(42)
    close = pd.Series(9000 + np.cumsum(np.random.randn(60) * 50))

    result = pre_trade_analysis(
        symbol        = "OFSS",
        close_prices  = close,
        entry_price   = 9240,
        stop_loss     = 8950,
        target        = 9820,
        total_capital = 500000,
        win_rate      = 0.50,
    )

    print(format_pre_trade(result))
