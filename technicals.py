# =============================================================================
# technicals.py — Technical Indicator Engine v2.0
# Phase 3B — Added 52-week breakout + VCP + ATR% signals
# =============================================================================

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core Indicator Functions
# ---------------------------------------------------------------------------

def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta    = close.diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    rs       = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(close: pd.Series, fast=12, slow=26, signal=9) -> pd.DataFrame:
    ema_fast   = ema(close, fast)
    ema_slow   = ema(close, slow)
    macd_line  = ema_fast - ema_slow
    signal_line= ema(macd_line, signal)
    histogram  = macd_line - signal_line
    return pd.DataFrame({
        "macd":      macd_line,
        "signal":    signal_line,
        "histogram": histogram,
    })


def adx(high: pd.Series, low: pd.Series, close: pd.Series,
        period: int = 14) -> pd.Series:
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)

    dm_pos = high.diff().clip(lower=0)
    dm_neg = (-low.diff()).clip(lower=0)
    dm_pos = dm_pos.where(dm_pos > (-low.diff()).clip(lower=0), 0.0)
    dm_neg = dm_neg.where(dm_neg > high.diff().clip(lower=0),  0.0)

    atr    = tr.ewm(com=period - 1, adjust=False).mean()
    di_pos = 100 * dm_pos.ewm(com=period - 1, adjust=False).mean() / atr
    di_neg = 100 * dm_neg.ewm(com=period - 1, adjust=False).mean() / atr
    dx     = 100 * (di_pos - di_neg).abs() / (di_pos + di_neg).replace(0, np.nan)
    return dx.ewm(com=period - 1, adjust=False).mean()


def atr(high: pd.Series, low: pd.Series, close: pd.Series,
        period: int = 14) -> pd.Series:
    """Average True Range."""
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(com=period - 1, adjust=False).mean()


def supertrend(high: pd.Series, low: pd.Series, close: pd.Series,
               period: int = 10, multiplier: float = 3.0) -> pd.Series:
    hl_avg   = (high + low) / 2
    atr_vals = atr(high, low, close, period)

    upper_band = hl_avg + multiplier * atr_vals
    lower_band = hl_avg - multiplier * atr_vals
    st_val     = pd.Series(index=close.index, dtype=float)
    direction  = pd.Series(index=close.index, dtype=int)

    for i in range(1, len(close)):
        ub = upper_band.iloc[i] if (
            upper_band.iloc[i] < upper_band.iloc[i-1] or
            close.iloc[i-1] > upper_band.iloc[i-1]
        ) else upper_band.iloc[i-1]

        lb = lower_band.iloc[i] if (
            lower_band.iloc[i] > lower_band.iloc[i-1] or
            close.iloc[i-1] < lower_band.iloc[i-1]
        ) else lower_band.iloc[i-1]

        upper_band.iloc[i] = ub
        lower_band.iloc[i] = lb

        prev_st = st_val.iloc[i-1]
        if i == 1:
            direction.iloc[i] = 1
        elif prev_st == upper_band.iloc[i-1]:
            direction.iloc[i] = 1 if close.iloc[i] > ub else -1
        else:
            direction.iloc[i] = -1 if close.iloc[i] < lb else 1

        st_val.iloc[i] = lb if direction.iloc[i] == 1 else ub

    return direction


# ---------------------------------------------------------------------------
# NEW Phase 3B — Breakout Signals
# ---------------------------------------------------------------------------

def breakout_signal(close: pd.Series, high: pd.Series,
                    days: int = 20) -> dict:
    """
    Detects 3 types of breakouts:
    1. 20-day high breakout  — price closes above 20-day high
    2. 52-week high breakout — price within 5% of 52-week high
    3. VCP pattern           — volatility contraction (tight base)
    """
    # 20-day high breakout
    high_20d       = high.rolling(days).max()
    is_20d_breakout= (close.iloc[-1] >= high_20d.iloc[-2])  # today > yesterday's high

    # 52-week metrics
    high_52w       = high.rolling(252).max()
    pct_from_52w   = (close.iloc[-1] / high_52w.iloc[-1]) * 100

    # Breakout strength — how far above the 20d high
    breakout_pct   = ((close.iloc[-1] - high_20d.iloc[-2]) /
                      high_20d.iloc[-2] * 100) if high_20d.iloc[-2] > 0 else 0

    # VCP — Volatility Contraction Pattern (Mark Minervini)
    # Price range contracts over last 10 days vs prior 20 days
    range_recent   = (high.iloc[-10:] - close.iloc[-10:]).mean()
    range_prior    = (high.iloc[-30:-10] - close.iloc[-30:-10]).mean()
    is_vcp         = (range_recent < range_prior * 0.6) if range_prior > 0 else False

    # Tight base — low ATR% (volatility drying up before breakout)
    atr_val        = atr(high, close, close).iloc[-1]
    atr_pct        = (atr_val / close.iloc[-1]) * 100

    return {
        "is_20d_breakout":  bool(is_20d_breakout),
        "breakout_pct":     round(float(breakout_pct), 2),
        "high_20d":         round(float(high_20d.iloc[-1]), 2),
        "high_52w":         round(float(high_52w.iloc[-1]), 2),
        "pct_from_52w_high":round(float(pct_from_52w), 2),
        "is_near_52w_high": bool(pct_from_52w >= 90),
        "is_at_52w_high":   bool(pct_from_52w >= 98),
        "is_vcp":           bool(is_vcp),
        "atr_pct":          round(float(atr_pct), 2),
        "is_tight_base":    bool(atr_pct < 3.0),
    }


def volume_analysis(volume: pd.Series, close: pd.Series) -> dict:
    """Extended volume signals."""
    vol_avg_20  = volume.rolling(20).mean().iloc[-1]
    vol_avg_50  = volume.rolling(50).mean().iloc[-1]
    vol_today   = volume.iloc[-1]

    # Volume trend — is volume expanding?
    vol_expanding = (vol_avg_20 > vol_avg_50 * 1.1)

    # Dry-up — volume contracting (good before breakout)
    vol_dryup     = (vol_avg_20 < vol_avg_50 * 0.8)

    return {
        "volume":           int(vol_today),
        "vol_20d_avg":      int(vol_avg_20),
        "vol_50d_avg":      int(vol_avg_50),
        "vol_ratio":        round(vol_today / vol_avg_20, 2) if vol_avg_20 > 0 else 0,
        "vol_expanding":    bool(vol_expanding),
        "vol_dryup":        bool(vol_dryup),
    }


# ---------------------------------------------------------------------------
# Main: Compute all indicators
# ---------------------------------------------------------------------------

def compute_indicators(df: pd.DataFrame, cfg: dict) -> dict | None:
    """
    Takes OHLCV DataFrame → returns full indicator dict.
    Returns None if data insufficient.
    """
    try:
        if len(df) < 220:
            return None

        close  = df["close"]
        high   = df["high"]
        low    = df["low"]
        volume = df["volume"]

        # Core indicators
        ema20    = ema(close, cfg["ema_short"])
        ema50    = ema(close, cfg["ema_medium"])
        ema200   = ema(close, cfg["ema_long"])
        rsi_vals = rsi(close, cfg["rsi_period"])
        macd_df  = macd(close, cfg["macd_fast"], cfg["macd_slow"], cfg["macd_signal"])
        adx_vals = adx(high, low, close, cfg["adx_period"])
        st_dir   = supertrend(high, low, close)

        # Phase 3B additions
        breakout = breakout_signal(close, high, cfg.get("breakout_days", 20))
        vol_data = volume_analysis(volume, close)

        latest = {
            # Price
            "close":            round(float(close.iloc[-1]), 2),
            "prev_close":       round(float(close.iloc[-2]), 2),
            "day_change_pct":   round(float(
                (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100), 2),

            # EMAs
            "ema20":            round(float(ema20.iloc[-1]), 2),
            "ema50":            round(float(ema50.iloc[-1]), 2),
            "ema200":           round(float(ema200.iloc[-1]), 2),

            # RSI
            "rsi":              round(float(rsi_vals.iloc[-1]), 2),

            # MACD
            "macd":             round(float(macd_df["macd"].iloc[-1]), 4),
            "macd_signal":      round(float(macd_df["signal"].iloc[-1]), 4),
            "macd_histogram":   round(float(macd_df["histogram"].iloc[-1]), 4),
            "macd_prev_hist":   round(float(macd_df["histogram"].iloc[-2]), 4),

            # ADX
            "adx":              round(float(adx_vals.iloc[-1]), 2),

            # Volume
            **vol_data,

            # Breakout (Phase 3B)
            **breakout,

            # Supertrend
            "supertrend_signal": int(st_dir.iloc[-1])
                                  if not pd.isna(st_dir.iloc[-1]) else 0,
        }

        # ── Boolean Signals ──────────────────────────────────────────────
        latest["signal_ema_stack"]      = (latest["ema20"] > latest["ema50"] > latest["ema200"])
        latest["signal_price_ema20"]    = (latest["close"] > latest["ema20"])
        latest["signal_price_ema50"]    = (latest["close"] > latest["ema50"])
        latest["signal_price_ema200"]   = (latest["close"] > latest["ema200"])
        latest["signal_rsi_zone"]       = (cfg["rsi_low"] < latest["rsi"] < cfg["rsi_high"])
        latest["signal_macd_bullish"]   = (latest["macd_histogram"] > 0)
        latest["signal_macd_cross"]     = (latest["macd_histogram"] > 0 and
                                           latest["macd_prev_hist"] <= 0)
        latest["signal_adx_strong"]     = (latest["adx"] > cfg["adx_min"])
        latest["signal_volume_confirm"] = (latest["vol_ratio"] > cfg["volume_multiplier"])
        latest["signal_supertrend"]     = (latest["supertrend_signal"] == 1)

        # Phase 3B signal combos
        latest["signal_breakout_confirmed"] = (
            latest["is_20d_breakout"] and
            latest["signal_volume_confirm"] and
            latest["signal_price_ema50"]
        )
        latest["signal_vcp_breakout"] = (
            latest["is_vcp"] and
            latest["is_20d_breakout"]
        )
        latest["signal_52w_momentum"] = (
            latest["pct_from_52w_high"] >= 85 and
            latest["signal_ema_stack"]
        )

        return latest

    except Exception as e:
        logger.error(f"Indicator computation error: {e}")
        return None
