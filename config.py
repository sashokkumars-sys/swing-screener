# =============================================================================
# config.py — Swing Screener Configuration
# Edit this file to customize your universe, thresholds, and scoring weights
# =============================================================================

# ---------------------------------------------------------------------------
# STOCK UNIVERSE — Nifty 500 curated liquid stocks (add/remove as needed)
# All symbols use NSE format. yfinance appends ".NS" automatically.
# ---------------------------------------------------------------------------
STOCK_UNIVERSE = [
    # Large Cap — Nifty 50
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR",
    "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK", "LT", "BAJFINANCE",
    "HCLTECH", "ASIANPAINT", "AXISBANK", "MARUTI", "SUNPHARMA", "TITAN",
    "ULTRACEMCO", "NESTLEIND", "WIPRO", "POWERGRID", "NTPC", "TECHM",
    "BAJAJFINSV", "ONGC", "JSWSTEEL", "COALINDIA", "TATAMOTORS", "TATASTEEL",
    "ADANIENT", "ADANIPORTS", "CIPLA", "DRREDDY", "DIVISLAB", "APOLLOHOSP",
    "EICHERMOT", "BAJAJ_AUTO", "HEROMOTOCO", "BRITANNIA",

    # Mid Cap — Quality + Momentum
    "PERSISTENT", "LTIM", "MPHASIS", "COFORGE", "TATAELXSI",
    "PIDILITIND", "BERGEPAINT", "GODREJCP", "MARICO", "DABUR",
    "VOLTAS", "HAVELLS", "POLYCAB", "DIXON", "AMBER",
    "IDFCFIRSTB", "FEDERALBNK", "BANDHANBNK", "RBLBANK",
    "CHOLAFIN", "BAJAJHFL", "MUTHOOTFIN", "MANAPPURAM",
    "ABBOTINDIA", "AUROPHARMA", "TORNTPHARM", "ALKEM", "IPCA",
    "ASTRAL", "SUPREMEIND", "FINPIPE", "CENTURYPLY",
    "TRENT", "DMART", "NYKAA", "ZOMATO", "PAYTM",
    "IRCTC", "INDHOTEL", "LEMONTREE", "CHALET",
    "CANBK", "BANKBARODA", "PNB", "UNIONBANK",
    "HFCL", "RAILTEL", "RVNL", "IRFC", "RECLTD", "PFC",
    "NHPC", "SJVN", "CESC", "TATAPOWER",
    "AMBUJACEM", "SHREECEM", "RAMCOCEM", "JKCEMENT",
    "MRF", "APOLLOTYRE", "CEAT", "BALKRISIND",
    "PAGEIND", "MANYAVAR", "KPRMILL", "ARVIND",

    # Small Cap — High Growth
    "KAYNES", "IDEAFORGE", "SYRMA", "AVALON",
    "HAPPYFORGE", "JYOTICNC", "WAAREEENER", "GREENPANEL",
    "BIKAJI", "DEVYANI", "SAPPHIRE", "WESTLIFE",
]

# ---------------------------------------------------------------------------
# DATA PARAMETERS
# ---------------------------------------------------------------------------
LOOKBACK_DAYS = 365          # Historical data period (1 year)
MIN_AVG_VOLUME = 200000      # Minimum avg daily volume (2 lakh shares)
MIN_PRICE = 50               # Minimum stock price (₹)
MIN_MARKET_CAP_CR = 500      # Minimum market cap in Crores

# ---------------------------------------------------------------------------
# TECHNICAL THRESHOLDS
# ---------------------------------------------------------------------------
TECH = {
    "ema_short":        20,
    "ema_medium":       50,
    "ema_long":         200,
    "rsi_period":       14,
    "rsi_low":          50,      # RSI must be above this
    "rsi_high":         72,      # RSI must be below this (not overbought)
    "macd_fast":        12,
    "macd_slow":        26,
    "macd_signal":      9,
    "adx_period":       14,
    "adx_min":          20,      # Trend strength minimum
    "volume_multiplier": 1.5,    # Volume vs 20-day average
    "volume_avg_period": 20,
    "week52_pct":       0.70,    # Price > 70% of 52-week high
}

# ---------------------------------------------------------------------------
# FUNDAMENTAL THRESHOLDS
# ---------------------------------------------------------------------------
FUND = {
    "roe_min":          12,      # Return on Equity %
    "debt_equity_max":  1.0,     # Debt to Equity ratio
    "revenue_growth_min": 10,    # Revenue growth % YoY
    "pe_max":           60,      # Maximum P/E ratio (avoid overvalued)
    "pe_min":           0,       # Minimum P/E (positive earnings)
}

# ---------------------------------------------------------------------------
# SCORING WEIGHTS  (must add up to 100)
# ---------------------------------------------------------------------------
SCORE_WEIGHTS = {
    # Technical (60 points)
    "ema_alignment":    15,   # 20 EMA > 50 EMA > 200 EMA
    "price_above_ema20": 5,   # Price above EMA 20
    "rsi_zone":         10,   # RSI in sweet zone
    "macd_signal":      10,   # MACD bullish
    "adx_strength":     10,   # ADX > threshold
    "volume_confirm":   10,   # Volume above average

    # Fundamental (40 points)
    "roe":              12,   # ROE quality
    "debt_equity":      10,   # Balance sheet strength
    "revenue_growth":   10,   # Topline growth
    "valuation":        8,    # P/E reasonable
}

# ---------------------------------------------------------------------------
# GRADE THRESHOLDS
# ---------------------------------------------------------------------------
GRADES = {
    "A+": 85,   # Strong Swing Candidate
    "A":  75,   # Good Swing Candidate
    "B":  60,   # Watch List
    "C":  45,   # Weak — monitor only
    "D":  0,    # Avoid
}

# ---------------------------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------------------------
OUTPUT_DIR = "output"
EXCEL_FILENAME = "swing_screener_report.xlsx"
CSV_FILENAME = "swing_screener_report.csv"
