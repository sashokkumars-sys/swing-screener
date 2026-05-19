# =============================================================================
# fetch_data.py — NSE Data Fetcher using yfinance
# =============================================================================

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)


def get_nse_symbol(symbol: str) -> str:
    """Convert plain symbol to NSE yfinance format."""
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
        return f"{symbol}.NS"
    return symbol


def fetch_price_history(symbol: str, days: int = 365) -> pd.DataFrame | None:
    """
    Fetch OHLCV price history for a single NSE stock.
    Returns None if data is unavailable or insufficient.
    """
    ns_symbol = get_nse_symbol(symbol)
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days + 50)  # extra buffer

    try:
        ticker = yf.Ticker(ns_symbol)
        df = ticker.history(start=start_date.strftime("%Y-%m-%d"),
                            end=end_date.strftime("%Y-%m-%d"),
                            auto_adjust=True)

        if df is None or len(df) < 100:
            logger.warning(f"{symbol}: Insufficient price data ({len(df) if df is not None else 0} rows)")
            return None

        df.index = pd.to_datetime(df.index).tz_localize(None)
        df.columns = [c.lower() for c in df.columns]
        df = df[["open", "high", "low", "close", "volume"]].dropna()
        return df

    except Exception as e:
        logger.error(f"{symbol}: Price fetch failed — {e}")
        return None


def fetch_fundamentals(symbol: str) -> dict:
    """
    Fetch fundamental data from yfinance .info
    Returns a dict with key financial ratios.
    """
    ns_symbol = get_nse_symbol(symbol)
    defaults = {
        "market_cap_cr":    None,
        "pe_ratio":         None,
        "roe":              None,
        "debt_to_equity":   None,
        "revenue_growth":   None,
        "earnings_growth":  None,
        "price_to_book":    None,
        "dividend_yield":   None,
        "sector":           "Unknown",
        "industry":         "Unknown",
        "company_name":     symbol,
    }

    try:
        ticker = yf.Ticker(ns_symbol)
        info = ticker.info

        if not info or "regularMarketPrice" not in info:
            return defaults

        # Market cap in Crores (1 Cr = 10M)
        raw_cap = info.get("marketCap")
        market_cap_cr = round(raw_cap / 1e7, 0) if raw_cap else None

        # ROE — yfinance gives as decimal (0.18 = 18%)
        roe_raw = info.get("returnOnEquity")
        roe = round(roe_raw * 100, 2) if roe_raw else None

        # Revenue growth — decimal
        rev_growth_raw = info.get("revenueGrowth")
        rev_growth = round(rev_growth_raw * 100, 2) if rev_growth_raw else None

        # Earnings growth — decimal
        earn_growth_raw = info.get("earningsGrowth")
        earn_growth = round(earn_growth_raw * 100, 2) if earn_growth_raw else None

        # Dividend yield — decimal
        div_raw = info.get("dividendYield")
        div_yield = round(div_raw * 100, 2) if div_raw else 0.0

        return {
            "company_name":     info.get("longName", symbol),
            "sector":           info.get("sector", "Unknown"),
            "industry":         info.get("industry", "Unknown"),
            "market_cap_cr":    market_cap_cr,
            "pe_ratio":         info.get("trailingPE"),
            "forward_pe":       info.get("forwardPE"),
            "roe":              roe,
            "debt_to_equity":   info.get("debtToEquity"),
            "revenue_growth":   rev_growth,
            "earnings_growth":  earn_growth,
            "price_to_book":    info.get("priceToBook"),
            "dividend_yield":   div_yield,
            "current_ratio":    info.get("currentRatio"),
            "promoter_holding": None,  # Not in yfinance — add screener.in later
        }

    except Exception as e:
        logger.error(f"{symbol}: Fundamentals fetch failed — {e}")
        return defaults


def fetch_all_stocks(symbols: list, price_days: int = 365,
                     delay: float = 0.3) -> dict:
    """
    Fetch price + fundamentals for all symbols.
    Returns dict: { symbol: { "prices": df, "fundamentals": dict } }

    delay: seconds between API calls to avoid rate limiting
    """
    results = {}
    total = len(symbols)

    logger.info(f"Starting data fetch for {total} stocks...")

    for i, symbol in enumerate(symbols, 1):
        logger.info(f"[{i}/{total}] Fetching {symbol}...")

        prices = fetch_price_history(symbol, days=price_days)
        time.sleep(delay)

        if prices is not None:
            fundamentals = fetch_fundamentals(symbol)
            time.sleep(delay)

            results[symbol] = {
                "prices":       prices,
                "fundamentals": fundamentals,
            }
        else:
            logger.warning(f"{symbol}: Skipped — no price data")

    logger.info(f"Data fetch complete. {len(results)}/{total} stocks loaded.")
    return results
