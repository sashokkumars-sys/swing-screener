# 📈 NSE Swing Trade Screener

A fully automated swing trading screener for NSE stocks.
Runs daily via GitHub Actions, outputs a scored Excel report and a Power BI-ready CSV.

---

## 🏗️ Project Structure

```
swing-screener/
├── main.py              ← Run this to start the screener
├── config.py            ← Edit your stock universe, thresholds, weights
├── fetch_data.py        ← NSE data via yfinance
├── technicals.py        ← EMA, RSI, MACD, ADX, Supertrend engine
├── scorer.py            ← 0–100 scoring + grade assignment
├── report.py            ← Excel + CSV report generator
├── requirements.txt     ← Python dependencies
├── .github/
│   └── workflows/
│       └── daily_screener.yml  ← GitHub Actions schedule
├── output/              ← Auto-created: daily Excel + CSV
├── historical/          ← Auto-created: cumulative CSV for Power BI
└── logs/                ← Auto-created: daily log files
```

---

## ⚡ Quick Start (Local)

### Step 1 — Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/swing-screener.git
cd swing-screener
pip install -r requirements.txt
```

### Step 2 — Test with 20 stocks first

```bash
python main.py --quick
```

### Step 3 — Full run (all stocks in universe)

```bash
python main.py
```

### Step 4 — Single stock analysis

```bash
python main.py --symbol RELIANCE
python main.py --symbol TATAMOTORS
```

---

## 📊 Scoring System (0–100)

### Technical Score (60 points)

| Signal | Points | Logic |
|---|---|---|
| EMA Stack (20>50>200) | 15 | Full bull alignment |
| Price > EMA 20 | 5 | Short-term support |
| RSI 55–65 zone | 10 | Momentum sweet spot |
| MACD Bullish / Fresh Cross | 10 | 10 for fresh cross, 6 for positive histogram |
| ADX > 20 | 10 | Trend strength |
| Volume > 1.5× avg | 10 | Institutional participation |

### Fundamental Score (40 points)

| Factor | Points | Logic |
|---|---|---|
| ROE ≥ 15% | 12 | Quality business |
| Debt/Equity ≤ 1.0 | 10 | Balance sheet strength |
| Revenue Growth ≥ 10% | 10 | Topline momentum |
| P/E ≤ 35 | 8 | Reasonable valuation |

### Grades

| Grade | Score | Action |
|---|---|---|
| A+ | 85–100 | 🟢 Strong Swing Candidate |
| A  | 75–84  | 🟢 Good Swing Candidate |
| B  | 60–74  | 🟡 Watch List |
| C  | 45–59  | 🟠 Monitor Only |
| D  | 0–44   | 🔴 Avoid |

---

## ⚙️ Configuration (config.py)

### Customize your stock universe

```python
STOCK_UNIVERSE = ["RELIANCE", "TCS", "INFY", ...]
```

### Change thresholds

```python
TECH = {
    "rsi_low":  50,    # Increase to 55 for stricter momentum filter
    "adx_min":  25,    # Increase for stronger trend requirement
    ...
}
FUND = {
    "roe_min":  15,    # Increase for higher quality filter
    ...
}
```

### Adjust scoring weights

```python
SCORE_WEIGHTS = {
    "ema_alignment":  15,   # Increase if you want trend-heavy scoring
    "rsi_zone":       10,
    "roe":            12,   # Increase for quality-first approach
    ...
}
```

---

## 🤖 GitHub Actions — Daily Automation

### Setup (one time)

1. Push this repo to your GitHub account
2. Go to `Settings → Actions → General`
3. Enable **"Read and write permissions"** under Workflow permissions
4. Done! The workflow runs automatically Mon–Fri at 4:00 PM IST

### Manual trigger

Go to `Actions → Daily Swing Screener → Run workflow`

### What it does

```
4:00 PM IST (weekdays)
      ↓
Pull NSE stock data (yfinance)
      ↓
Calculate all technical indicators
      ↓
Fetch fundamental ratios
      ↓
Score and rank all stocks (0–100)
      ↓
Generate Excel report + CSV
      ↓
Commit reports back to repo ← Download from here
      ↓
Append to historical/all_runs.csv ← Connect Power BI here
```

### Download your report

After each run:
1. Go to `Actions` tab in your GitHub repo
2. Click the latest run
3. Download the **artifact** (Excel + CSV)

Or: the reports are also committed directly to `output/` folder in the repo.

---

## 📊 Power BI Integration

Connect Power BI to the CSV that GitHub auto-updates:

1. Open Power BI Desktop
2. **Get Data → Web**
3. Enter your raw CSV URL:
   ```
   https://raw.githubusercontent.com/YOUR_USERNAME/swing-screener/main/output/swing_screener_report.csv
   ```
4. For **historical trend analysis**, use:
   ```
   https://raw.githubusercontent.com/YOUR_USERNAME/swing-screener/main/historical/all_runs.csv
   ```
5. Set refresh schedule to **Daily** in Power BI Service

---

## 📋 Output Columns

| Column | Description |
|---|---|
| Total Score | 0–100 composite score |
| Grade | A+/A/B/C/D |
| Flags | 🔥 Fresh MACD Cross / ✅ Supertrend Buy etc. |
| RSI (14) | Relative Strength Index |
| ADX | Average Directional Index (trend strength) |
| Volume Ratio | Today's volume ÷ 20-day average |
| EMA 20/50/200 | Exponential moving averages |
| ROE % | Return on Equity |
| Debt/Equity | Leverage ratio |
| Revenue Growth % | Year-on-year revenue growth |
| Screener Link | Direct link to screener.in |
| TradingView Link | Direct link to chart |

---

## ⚠️ Risk Disclaimer

> This tool is for **research and educational purposes only**.
> It does not constitute financial advice.
> Always apply your own judgment, position sizing, and stop-losses.
> Never risk more than 2% of capital per trade.

---

## 🗺️ Roadmap

- [x] Technical indicators (EMA, RSI, MACD, ADX, Supertrend, Volume)
- [x] Fundamental scoring (ROE, D/E, Revenue growth, P/E)
- [x] Excel report with color coding
- [x] CSV for Power BI
- [x] GitHub Actions daily automation
- [x] Historical data accumulation
- [ ] Screener.in fundamental scraper (deeper data)
- [ ] Telegram alert bot (top A+ picks daily)
- [ ] Power BI template file (.pbit)
- [ ] Sector rotation heatmap
- [ ] Backtesting module

---

*Built with Python · yfinance · openpyxl · GitHub Actions*
