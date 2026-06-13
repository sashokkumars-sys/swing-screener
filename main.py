# =============================================================================
# main.py — Swing Screener Orchestrator
# Run this script daily to generate your stock report
#
# Usage:
#   python main.py                    # Full run (all stocks)
#   python main.py --quick            # Quick test (first 20 stocks)
#   python main.py --symbol RELIANCE  # Single stock analysis
# =============================================================================

import logging
import argparse
import sys
import os
from datetime import datetime

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            f"logs/screener_{datetime.now().strftime('%Y%m%d')}.log",
            mode="a"
        ) if os.path.exists("logs") or not os.makedirs("logs", exist_ok=True)
        else logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from config import (STOCK_UNIVERSE, TECH, FUND, OUTPUT_DIR,
                    EXCEL_FILENAME, CSV_FILENAME, MIN_PRICE,
                    MIN_AVG_VOLUME, MIN_MARKET_CAP_CR, LOOKBACK_DAYS)
from fetch_data import fetch_all_stocks
from technicals import compute_indicators
from scorer import score_stock
from report import generate_excel_report, generate_csv


# ---------------------------------------------------------------------------
# Pre-screening filter
# ---------------------------------------------------------------------------

def passes_basic_filters(symbol: str, tech: dict, fund: dict) -> tuple[bool, str]:
    """Quick sanity checks before full scoring."""

    # Price floor
    close = tech.get("close", 0)
    if close < MIN_PRICE:
        return False, f"Price ₹{close} below minimum ₹{MIN_PRICE}"

    # Volume floor
    avg_vol = tech.get("vol_20d_avg", 0)
    if avg_vol < MIN_AVG_VOLUME:
        return False, f"Avg volume {avg_vol:,} below minimum {MIN_AVG_VOLUME:,}"

    # Market cap (if available)
    mcap = fund.get("market_cap_cr")
    if mcap and mcap < MIN_MARKET_CAP_CR:
        return False, f"Market cap ₹{mcap}Cr below minimum ₹{MIN_MARKET_CAP_CR}Cr"

    # Must be above 200 EMA (basic trend filter)
    if not tech.get("signal_price_ema200"):
        return False, "Price below 200 EMA — not in uptrend"

    return True, "OK"


# ---------------------------------------------------------------------------
# Core Pipeline
# ---------------------------------------------------------------------------

def run_screener(symbols: list[str]) -> list[dict]:
    """
    Full pipeline v2:
    1. Fetch OHLCV + yfinance fundamentals
    2. Compute technical indicators
    3. Pre-filter (price, volume, 200 EMA)
    4. Score with available data
    5. ENRICH top 100 with Screener.in (promoter, ROCE, 3yr growth)
    6. RE-SCORE with complete data
    7. Final sort and return
    """
    from screener_scraper import enrich_with_screener
 
    logger.info("=" * 60)
    logger.info("  NSE SWING SCREENER v2 — Phase 3B")
    logger.info(f"  Universe: {len(symbols)} stocks")
    logger.info(f"  Run: {datetime.now().strftime('%d-%b-%Y %H:%M IST')}")
    logger.info("=" * 60)
 
    # ── Step 1 & 2: Fetch + Indicators ─────────────────────────────
    raw_data = fetch_all_stocks(symbols, price_days=LOOKBACK_DAYS)
    logger.info(f"✓ Data fetched: {len(raw_data)} stocks")
 
    # ── Step 3 & 4: Filter + Initial Score ─────────────────────────
    results      = []
    filtered_out = 0
 
    for symbol, data in raw_data.items():
        tech = compute_indicators(data["prices"], TECH)
        if tech is None:
            continue
 
        ok, reason = passes_basic_filters(symbol, tech, data["fundamentals"])
        if not ok:
            logger.info(f"  ✗ {symbol}: {reason}")
            filtered_out += 1
            continue
 
        score = score_stock(symbol, tech, data["fundamentals"])
        results.append({
            "symbol":          symbol,
            "tech_indicators": tech,
            "fundamentals":    data["fundamentals"],
            "score":           score,
        })
 
    logger.info(f"✓ After filters: {len(results)} stocks | Filtered: {filtered_out}")
 
    # ── Step 5: Enrich top 100 with Screener.in ────────────────────
    logger.info("Enriching with Screener.in data...")
    results = enrich_with_screener(results, max_stocks=100)
 
    # ── Step 6: Re-score with complete data ────────────────────────
    logger.info("Re-scoring with complete fundamental data...")
    for r in results:
        r["score"] = score_stock(r["symbol"], r["tech_indicators"], r["fundamentals"])
 
    # ── Step 7: Final sort ─────────────────────────────────────────
    results.sort(key=lambda x: x["score"]["total_score"], reverse=True)
 
    logger.info(f"✓ Final ranked list: {len(results)} stocks")
    logger.info(f"  Top pick: {results[0]['symbol']} "
                f"Score: {results[0]['score']['total_score']}")
    return results



# ---------------------------------------------------------------------------
# Output + Summary
# ---------------------------------------------------------------------------

def print_top_picks(results: list[dict], top_n: int = 15):
    """Print top picks to console."""
    grade_emoji = {"A+": "🟢", "A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴"}

    print("\n" + "=" * 75)
    print("  🎯  TOP SWING TRADING PICKS — TODAY")
    print("=" * 75)
    print(f"  {'#':<3} {'Symbol':<14} {'Score':>6} {'Grade':>5}  "
          f"{'RSI':>5}  {'ADX':>5}  {'Vol Ratio':>9}  {'Sector'}")
    print("-" * 75)

    for i, r in enumerate(results[:top_n], 1):
        t = r["tech_indicators"]
        s = r["score"]
        f = r["fundamentals"]
        emoji = grade_emoji.get(s["grade"], "⚪")

        print(f"  {i:<3} {r['symbol']:<14} {s['total_score']:>6.1f} "
              f"{emoji} {s['grade']:>3}  "
              f"{t.get('rsi', 0):>5.1f}  "
              f"{t.get('adx', 0):>5.1f}  "
              f"{t.get('vol_ratio', 0):>9.2f}  "
              f"{f.get('sector', 'Unknown')[:20]}")

    print("=" * 75)

    # Show flags for top 5
    print("\n  🔍 KEY SIGNALS — TOP 5")
    print("-" * 75)
    for r in results[:5]:
        flags = r["score"].get("flags", "No special signals")
        print(f"  {r['symbol']:14s} → {flags}")

    print("=" * 75 + "\n")


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="NSE Swing Trade Screener")
    parser.add_argument("--quick", action="store_true",
                        help="Quick test with first 20 stocks")
    parser.add_argument("--symbol", type=str,
                        help="Analyse a single stock (e.g. --symbol RELIANCE)")
    parser.add_argument("--top", type=int, default=15,
                        help="Number of top picks to display (default: 15)")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.symbol:
        symbols = [args.symbol.upper()]
        logger.info(f"Single stock mode: {symbols[0]}")
    elif args.quick:
        symbols = STOCK_UNIVERSE[:20]
        logger.info("Quick mode: testing with first 20 stocks")
    else:
        symbols = STOCK_UNIVERSE

    # Run the screener
    results = run_screener(symbols)

    if not results:
        logger.warning("No stocks passed the filters today. Market may be weak.")
        return

    # Print top picks
    print_top_picks(results, top_n=args.top)

    # Generate reports
    logger.info("Generating Excel report...")
    excel_path = generate_excel_report(results, OUTPUT_DIR, EXCEL_FILENAME)

    logger.info("Generating CSV for Power BI...")
    csv_path = generate_csv(results, OUTPUT_DIR, CSV_FILENAME)

    print(f"\n  📁 Reports saved:")
    print(f"     Excel : {excel_path}")
    print(f"     CSV   : {csv_path}")
    print(f"\n  ✅ Done! Open the Excel file to review your picks.\n")


if __name__ == "__main__":
    main()
