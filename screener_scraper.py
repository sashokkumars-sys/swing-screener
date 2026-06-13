# =============================================================================
# screener_scraper.py — Fetch promoter + fundamental data from Screener.in
# Strategy: Only scrapes top 100 stocks by technical score
# Rate limited — 2.5 sec between requests to avoid IP ban
# Caches results — avoids re-scraping same stock same day
# =============================================================================

import requests, json, os, time, logging
from datetime import datetime
from bs4 import BeautifulSoup

logger       = logging.getLogger(__name__)
SCREENER_BASE = "https://www.screener.in/company"
DELAY         = 2.5
TIMEOUT       = 15
MAX_STOCKS    = 100
CACHE_FILE    = "output/screener_cache.json"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer":         "https://www.screener.in/",
}

DEFAULTS = {
    "promoter_holding":  None,
    "promoter_pledged":  None,
    "roce":              None,
    "roe_screener":      None,
    "sales_growth_3yr":  None,
    "profit_growth_3yr": None,
    "screener_pe":       None,
}


def load_cache() -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(CACHE_FILE):
        try:
            cache = json.load(open(CACHE_FILE))
            if cache.get("date") == today:
                logger.info(f"Cache: {len(cache.get('data',{}))} stocks loaded")
                return cache.get("data", {})
        except Exception:
            pass
    return {}


def save_cache(data: dict):
    os.makedirs("output", exist_ok=True)
    json.dump({"date": datetime.now().strftime("%Y-%m-%d"), "data": data},
              open(CACHE_FILE, "w"), indent=2)


def scrape_screener(symbol: str, session: requests.Session) -> dict:
    result = dict(DEFAULTS)
    for url in [f"{SCREENER_BASE}/{symbol}/consolidated/",
                f"{SCREENER_BASE}/{symbol}/"]:
        try:
            resp = session.get(url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")

            # Promoter holding
            holding_sec = soup.find("section", {"id": "shareholding"})
            if holding_sec:
                for row in holding_sec.find_all("tr"):
                    cells = row.find_all("td")
                    if cells and "promoter" in cells[0].get_text(strip=True).lower():
                        vals = [c.get_text(strip=True).replace("%","").replace(",","")
                                for c in cells[1:] if c.get_text(strip=True)]
                        if vals:
                            try: result["promoter_holding"] = float(vals[-1])
                            except ValueError: pass
                    if cells and "pledged" in cells[0].get_text(strip=True).lower():
                        vals = [c.get_text(strip=True).replace("%","").replace(",","")
                                for c in cells[1:] if c.get_text(strip=True)]
                        if vals:
                            try: result["promoter_pledged"] = float(vals[-1])
                            except ValueError: pass

            # Key ratios
            ratios = soup.find("section", {"id": "top-ratios"})
            if ratios:
                for li in ratios.find_all("li"):
                    lbl_el = li.find("span", {"class": "name"})
                    val_el = (li.find("span", {"class": "nowrap"}) or
                              li.find("span", {"class": "number"}))
                    if lbl_el and val_el:
                        lbl = lbl_el.get_text(strip=True).lower()
                        val_str = (val_el.get_text(strip=True)
                                   .replace("%","").replace(",","")
                                   .replace("₹","").strip())
                        try:
                            val = float(val_str)
                            if "roce"     in lbl: result["roce"]         = val
                            elif "roe"    in lbl: result["roe_screener"] = val
                            elif "p/e"    in lbl: result["screener_pe"]  = val
                        except ValueError:
                            pass

            logger.info(f"  {symbol}: Promoter={result['promoter_holding']}% "
                        f"ROCE={result['roce']}% PE={result['screener_pe']}")
            return result

        except requests.Timeout:
            logger.warning(f"{symbol}: timeout")
        except Exception as e:
            logger.error(f"{symbol}: {e}")

    return result


def enrich_with_screener(results: list, max_stocks: int = MAX_STOCKS) -> list:
    results_sorted = sorted(results,
        key=lambda x: x.get("score", {}).get("tech_score", 0), reverse=True)

    to_scrape = results_sorted[:max_stocks]
    skip_rest = results_sorted[max_stocks:]

    logger.info(f"Screener.in: scraping top {len(to_scrape)} stocks")

    cache   = load_cache()
    session = requests.Session()
    enriched = []

    for i, result in enumerate(to_scrape, 1):
        symbol = result["symbol"]
        if symbol in cache:
            logger.info(f"  [{i}/{len(to_scrape)}] {symbol}: cached ✓")
            screener_data = cache[symbol]
        else:
            logger.info(f"  [{i}/{len(to_scrape)}] {symbol}: scraping...")
            screener_data = scrape_screener(symbol, session)
            cache[symbol] = screener_data
            save_cache(cache)
            time.sleep(DELAY)

        # Merge into fundamentals — only override if screener has the value
        for k, v in screener_data.items():
            if v is not None:
                result["fundamentals"][k] = v

        enriched.append(result)

    enriched.extend(skip_rest)
    logger.info(f"Enrichment complete — {len(enriched)} stocks")
    return enriched
