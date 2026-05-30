# =============================================================================
# config.py — Swing Screener Configuration v2.0
# Phase 3B — Expanded universe + improved scoring
# =============================================================================

# ---------------------------------------------------------------------------
# STOCK UNIVERSE — 250 NSE stocks across all sectors
# ---------------------------------------------------------------------------
STOCK_UNIVERSE = [
    # ── LARGE CAP — Nifty 50 ──────────────────────────────────────────────
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR",
    "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK", "LT", "BAJFINANCE",
    "HCLTECH", "ASIANPAINT", "AXISBANK", "MARUTI", "SUNPHARMA", "TITAN",
    "ULTRACEMCO", "NESTLEIND", "WIPRO", "POWERGRID", "NTPC", "TECHM",
    "BAJAJFINSV", "ONGC", "JSWSTEEL", "COALINDIA", "TATAMOTORS", "TATASTEEL",
    "ADANIENT", "ADANIPORTS", "CIPLA", "DRREDDY", "DIVISLAB", "APOLLOHOSP",
    "EICHERMOT", "BAJAJ_AUTO", "HEROMOTOCO", "BRITANNIA", "GRASIM",
    "INDUSINDBK", "M&M", "SBILIFE", "HDFCLIFE", "BPCL", "SHREECEM",
    "TATACONSUM", "VEDL", "UPL",

    # ── IT & TECHNOLOGY ───────────────────────────────────────────────────
    "PERSISTENT", "LTIM", "MPHASIS", "COFORGE", "TATAELXSI",
    "OFSS", "KPITTECH", "ZENSARTECH", "HEXAWARE", "NIITLTD",
    "MASTEK", "SONATSOFTW", "INTELLECT", "TANLA", "ROUTE",
    "RATEGAIN", "NETWEB", "DATAMATICS", "NEWGEN", "SAKSOFT",

    # ── BANKING & FINANCE ─────────────────────────────────────────────────
    "IDFCFIRSTB", "FEDERALBNK", "BANDHANBNK", "RBLBANK", "AUBANK",
    "CANBK", "BANKBARODA", "PNB", "UNIONBANK", "INDIANB",
    "CHOLAFIN", "BAJAJHFL", "MUTHOOTFIN", "MANAPPURAM", "SUNDARMFIN",
    "AAVAS", "HOMEFIRST", "APTUS", "UGROCAP", "CREDITACC",
    "ANGELONE", "CDSL", "BSE", "MCX", "CAMS",

    # ── CONSUMER & FMCG ──────────────────────────────────────────────────
    "PIDILITIND", "BERGEPAINT", "GODREJCP", "MARICO", "DABUR",
    "EMAMILTD", "COLPAL", "PGHH", "GILLETTE", "VBL",
    "RADICO", "UNITDSPR", "MCDOWELL-N", "BAJAJCON", "JYOTHYLAB",
    "TRENT", "DMART", "NYKAA", "ZOMATO", "DEVYANI",
    "SAPPHIRE", "WESTLIFE", "JUBLFOOD", "BIKAJI", "CAMPUS",

    # ── PHARMA & HEALTHCARE ───────────────────────────────────────────────
    "ABBOTINDIA", "AUROPHARMA", "TORNTPHARM", "ALKEM", "IPCA",
    "LUPIN", "GLENMARK", "BIOCON", "NATCOPHARM", "LAURUSLABS",
    "GRANULES", "DIVIS", "SYNGENE", "METROPOLIS", "THYROCARE",
    "MAXHEALTH", "FORTIS", "NARAYANHC", "KIMS", "RAINBOW",

    # ── INDUSTRIALS & CAPITAL GOODS ───────────────────────────────────────
    "HAVELLS", "POLYCAB", "DIXON", "AMBER", "VOLTAS",
    "BLUESTARCO", "WHIRLPOOL", "CROMPTON", "ORIENTELEC", "BAJAJELEC",
    "SIEMENS", "ABB", "HONAUT", "THERMAX", "CUMMINSIND",
    "BHEL", "BEL", "HAL", "BEML", "GRSE",
    "KAYNES", "SYRMA", "AVALON", "IDEAFORGE", "WAAREEENER",

    # ── INFRASTRUCTURE & PSU ──────────────────────────────────────────────
    "HFCL", "RAILTEL", "RVNL", "IRFC", "RECLTD", "PFC",
    "NHPC", "SJVN", "CESC", "TATAPOWER", "TORNTPOWER",
    "ADANIGREEN", "ADANITRANS", "ADANIENSOL", "INDIGRID", "POWERMECH",
    "KEC", "KALPATPOWR", "VOLTAMP", "TRIL", "PATELENG",

    # ── METALS & MINING ───────────────────────────────────────────────────
    "HINDALCO", "NATIONALUM", "HINDCOPPER", "NMDC", "MOIL",
    "SAIL", "JSPL", "WELSPUNLIV", "RATNAMANI", "APARINDS",
    "ASTRAL", "SUPREMEIND", "FINPIPE", "CENTURYPLY", "GREENPLY",

    # ── AUTO & AUTO ANCILLARIES ───────────────────────────────────────────
    "MRF", "APOLLOTYRE", "CEAT", "BALKRISIND", "TVSSRICHAK",
    "MOTHERSON", "BOSCHLTD", "MINDA", "SUNDRMFAST", "SCHAEFFLER",
    "ENDURANCE", "TIINDIA", "SUPRAJIT", "GABRIEL", "MAHINDCIE",

    # ── CEMENT & BUILDING MATERIALS ───────────────────────────────────────
    "AMBUJACEM", "RAMCOCEM", "JKCEMENT", "HEIDELBERG", "BIRLACORPN",
    "ORIENTCEM", "INDIACEM", "DALMIA", "NUVOCO", "SAURASHCEM",

    # ── REAL ESTATE & HOSPITALITY ─────────────────────────────────────────
    "DLF", "GODREJPROP", "OBEROIRLTY", "PHOENIXLTD", "BRIGADE",
    "PRESTIGE", "SOBHA", "MAHLIFE", "KOLTEPATIL", "SUNTECK",
    "INDHOTEL", "LEMONTREE", "CHALET", "EIHOTEL", "MAHINDRA",

    # ── TEXTILES & APPAREL ────────────────────────────────────────────────
    "PAGEIND", "MANYAVAR", "KPRMILL", "ARVIND", "WELSPUN",
    "RAYMOND", "VIPIND", "GOKEX", "FILATEX", "NITIN",

    # ── OIL & GAS ─────────────────────────────────────────────────────────
    "IOC", "HINDPETRO", "MRPL", "GAIL", "IGL",
    "MGL", "GUJGASLTD", "ATGL", "PETRONET", "AEGISLOG",

    # ── SPECIALTY CHEMICALS ───────────────────────────────────────────────
    "SRF", "ATUL", "DEEPAKNTR", "FINEORG", "GALAXYSURF",
    "NAVINFLUOR", "FLUOROCHEM", "ALKYLAMINE", "CLEAN", "TATACHEM",
]

# ---------------------------------------------------------------------------
# DATA PARAMETERS
# ---------------------------------------------------------------------------
LOOKBACK_DAYS       = 365
MIN_AVG_VOLUME      = 200000
MIN_PRICE           = 50
MIN_MARKET_CAP_CR   = 300       # Lowered to catch quality small caps

# ---------------------------------------------------------------------------
# TECHNICAL THRESHOLDS
# ---------------------------------------------------------------------------
TECH = {
    "ema_short":            20,
    "ema_medium":           50,
    "ema_long":             200,
    "rsi_period":           14,
    "rsi_low":              50,
    "rsi_high":             72,
    "macd_fast":            12,
    "macd_slow":            26,
    "macd_signal":          9,
    "adx_period":           14,
    "adx_min":              20,
    "volume_multiplier":    1.5,
    "volume_avg_period":    20,
    "week52_pct":           0.70,

    # Phase 3B — new signals
    "breakout_days":        20,     # 20-day high breakout
    "atr_period":           14,     # For volatility filter
    "consolidation_atr":    3.0,    # Max ATR% for tight base
}

# ---------------------------------------------------------------------------
# FUNDAMENTAL THRESHOLDS
# ---------------------------------------------------------------------------
FUND = {
    "roe_min":              12,
    "debt_equity_max":      1.0,
    "revenue_growth_min":   10,
    "pe_max":               80,
    "pe_min":               0,

    # Phase 3B — new thresholds
    "promoter_holding_min": 40,     # Minimum promoter holding %
    "promoter_pledge_max":  20,     # Maximum pledged shares %
}

# ---------------------------------------------------------------------------
# SCORING WEIGHTS (must add to 100)
# Phase 3B — rebalanced with promoter + breakout signals
# ---------------------------------------------------------------------------
SCORE_WEIGHTS = {
    # Technical (55 points)
    "ema_alignment":        12,
    "price_above_ema20":    5,
    "rsi_zone":             8,
    "macd_signal":          8,
    "adx_strength":         8,
    "volume_confirm":       8,
    "breakout_signal":      6,      # NEW — 20-day breakout bonus

    # Fundamental (45 points)
    "roe":                  12,
    "debt_equity":          10,
    "revenue_growth":       10,
    "valuation":            7,
    "promoter_holding":     6,      # NEW — promoter confidence
}

# ---------------------------------------------------------------------------
# GRADE THRESHOLDS
# ---------------------------------------------------------------------------
GRADES = {
    "A+": 85,
    "A":  75,
    "B":  60,
    "C":  45,
    "D":  0,
}

# ---------------------------------------------------------------------------
# SCREENER.IN — Fundamental data scraping
# ---------------------------------------------------------------------------
SCREENER_BASE_URL   = "https://www.screener.in/company"
SCREENER_DELAY      = 2.0       # seconds between requests (be polite)
SCREENER_TIMEOUT    = 15        # request timeout in seconds
SCREENER_ENABLED    = True      # set False to skip if rate-limited

# ---------------------------------------------------------------------------
# NSE FII/DII — Daily institutional flow
# ---------------------------------------------------------------------------
NSE_FII_URL         = "https://www.nseindia.com/api/fiidiiTradeReact"
NSE_ENABLED         = True

# ---------------------------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------------------------
OUTPUT_DIR          = "output"
EXCEL_FILENAME      = "swing_screener_report.xlsx"
CSV_FILENAME        = "swing_screener_report.csv"
