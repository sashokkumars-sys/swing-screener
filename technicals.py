# =============================================================================
# technicals.py — Technical Indicator Engine
# Calculates EMA, RSI, MACD, ADX, Volume signals, Supertrend
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
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(close: pd.Series, fast: int = 12, slow: int = 26,
         signal: int = 9) -> pd.DataFrame:
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return pd.DataFrame({
        "macd":      macd_line,
        "signal":    signal_line,
        "histogram": histogram,
    })


def adx(high: pd.Series, low: pd.Series, close: pd.Series,
        period: int = 14) -> pd.Series:
    """Average Directional Index — measures trend strength."""
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)

    dm_pos = high.diff()
    dm_neg = -low.diff()

    dm_pos = dm_pos.where((dm_pos > dm_neg) & (dm_pos > 0), 0.0)
    dm_neg = dm_neg.where((dm_neg > dm_pos) & (dm_neg > 0), 0.0)

    atr   = tr.ewm(com=period - 1, adjust=False).mean()
    di_pos = 100 * dm_pos.ewm(com=period - 1, adjust=False).mean() / atr
    di_neg = 100 * dm_neg.ewm(com=period - 1, adjust=False).mean() / atr

    dx = 100 * (di_pos - di_neg).abs() / (di_pos + di_neg).replace(0, np.nan)
    return dx.ewm(com=period - 1, adjust=False).mean()


def supertrend(high: pd.Series, low: pd.Series, close: pd.Series,
               period: int = 10, multiplier: float = 3.0) -> pd.Series:
    """
    Supertrend indicator.
    Returns: +1 (bullish) or -1 (bearish)
    """
    hl_avg = (high + low) / 2

    # ATR via Wilder's smoothing
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)
    atr_val = tr.ewm(com=period - 1, adjust=False).mean()

    upper_band = hl_avg + multiplier * atr_val
    lower_band = hl_avg - multiplier * atr_val

    supertrend_val = pd.Series(index=close.index, dtype=float)
    direction      = pd.Series(index=close.index, dtype=int)

    for i in range(1, len(close)):
        # Upper band
        if upper_band.iloc[i] < upper_band.iloc[i - 1] or close.iloc[i - 1] > upper_band.iloc[i - 1]:
            upper_band.iloc[i] = upper_band.iloc[i]
        else:
            upper_band.iloc[i] = upper_band.iloc[i - 1]

        # Lower band
        if lower_band.iloc[i] > lower_band.iloc[i - 1] or close.iloc[i - 1] < lower_band.iloc[i - 1]:
            lower_band.iloc[i] = lower_band.iloc[i]
        else:
            lower_band.iloc[i] = lower_band.iloc[i - 1]

        # Direction
        if i == 1:
            direction.iloc[i] = 1
        elif supertrend_val.iloc[i - 1] == upper_band.iloc[i - 1] and close.iloc[i] <= upper_band.iloc[i]:
            direction.iloc[i] = -1
        elif supertrend_val.iloc[i - 1] == upper_band.iloc[i - 1] and close.iloc[i] > upper_band.iloc[i]:
            direction.iloc[i] = 1
        elif supertrend_val.iloc[i - 1] == lower_band.iloc[i - 1] and close.iloc[i] >= lower_band.iloc[i]:
            direction.iloc[i] = 1
        elif supertrend_val.iloc[i - 1] == lower_band.iloc[i - 1] and close.iloc[i] < lower_band.iloc[i]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i - 1]

        supertrend_val.iloc[i] = lower_band.iloc[i] if direction.iloc[i] == 1 else upper_band.iloc[i]

    return direction


# ---------------------------------------------------------------------------
# Main: Compute all indicators for a stock
# ---------------------------------------------------------------------------

def compute_indicators(df: pd.DataFrame, cfg: dict) -> dict | None:
    """
    Takes OHLCV DataFrame, returns dict of indicator values + signals.
    Returns None if data is too short.
    """
    try:
        if len(df) < 220:
            return None

        close  = df["close"]
        high   = df["high"]
        low    = df["low"]
        volume = df["volume"]

        # EMAs
        ema20  = ema(close, cfg["ema_short"])
        ema50  = ema(close, cfg["ema_medium"])
        ema200 = ema(close, cfg["ema_long"])

        # RSI
        rsi_vals = rsi(close, cfg["rsi_period"])

        # MACD
        macd_df = macd(close, cfg["macd_fast"], cfg["macd_slow"], cfg["macd_signal"])

        # ADX
        adx_vals = adx(high, low, close, cfg["adx_period"])

        # Volume
        vol_avg = volume.rolling(cfg["volume_avg_period"]).mean()

        # 52-week high
        week52_high = high.rolling(252).max()

        # Supertrend
        st_direction = supertrend(high, low, close)

        # --- Latest values (last row) ---
        latest = {
            # Price
            "close":            round(close.iloc[-1], 2),
            "prev_close":       round(close.iloc[-2], 2),

            # EMAs
            "ema20":            round(ema20.iloc[-1], 2),
            "ema50":            round(ema50.iloc[-1], 2),
            "ema200":           round(ema200.iloc[-1], 2),

            # RSI
            "rsi":              round(rsi_vals.iloc[-1], 2),

            # MACD
            "macd":             round(macd_df["macd"].iloc[-1], 4),
            "macd_signal":      round(macd_df["signal"].iloc[-1], 4),
            "macd_histogram":   round(macd_df["histogram"].iloc[-1], 4),
            "macd_prev_hist":   round(macd_df["histogram"].iloc[-2], 4),

            # ADX
            "adx":              round(adx_vals.iloc[-1], 2),

            # Volume
            "volume":           int(volume.iloc[-1]),
            "vol_20d_avg":      int(vol_avg.iloc[-1]),
            "vol_ratio":        round(volume.iloc[-1] / vol_avg.iloc[-1], 2)
                                if vol_avg.iloc[-1] > 0 else 0,

            # 52-week high
            "week52_high":      round(week52_high.iloc[-1], 2),
            "pct_from_52w_high": round(
                (close.iloc[-1] / week52_high.iloc[-1]) * 100, 2),

            # Supertrend
            "supertrend_signal": int(st_direction.iloc[-1])
                                  if not pd.isna(st_direction.iloc[-1]) else 0,

            # Daily change
            "day_change_pct":   round(
                ((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]) * 100, 2),
        }

        # --- Boolean Signals ---
        latest["signal_ema_stack"]     = (latest["ema20"] > latest["ema50"] > latest["ema200"])
        latest["signal_price_ema20"]   = (latest["close"] > latest["ema20"])
        latest["signal_price_ema50"]   = (latest["close"] > latest["ema50"])
        latest["signal_price_ema200"]  = (latest["close"] > latest["ema200"])
        latest["signal_rsi_zone"]      = (cfg["rsi_low"] < latest["rsi"] < cfg["rsi_high"])
        latest["signal_macd_bullish"]  = (latest["macd_histogram"] > 0)
        latest["signal_macd_cross"]    = (latest["macd_histogram"] > 0 and
                                          latest["macd_prev_hist"] <= 0)   # fresh crossover
        latest["signal_adx_strong"]    = (latest["adx"] > cfg["adx_min"])
        latest["signal_volume_confirm"]= (latest["vol_ratio"] > cfg["volume_multiplier"])
        latest["signal_supertrend"]    = (latest["supertrend_signal"] == 1)
        latest["signal_near_52w_high"] = (latest["pct_from_52w_high"] >
                                          cfg["week52_pct"] * 100)

        return latest

    except Exception as e:
        logger.error(f"Indicator computation error: {e}")
        return None
