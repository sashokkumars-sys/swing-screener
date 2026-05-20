# =============================================================================
# update_sheets.py — Auto-updates Google Sheets with daily screener results
# Called by GitHub Actions after screener runs
# =============================================================================

import os
import csv
import json
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SHEET_ID        = os.environ.get("GOOGLE_SHEET_ID")
CREDENTIALS_JSON = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
CSV_PATH        = "output/swing_screener_report.csv"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ---------------------------------------------------------------------------
# Connect to Google Sheets
# ---------------------------------------------------------------------------

def get_client():
    creds_dict = json.loads(CREDENTIALS_JSON)
    creds      = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


# ---------------------------------------------------------------------------
# Load CSV
# ---------------------------------------------------------------------------

def load_csv(path: str):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows   = list(reader)
    return rows   # rows[0] = headers, rows[1:] = data


# ---------------------------------------------------------------------------
# Update Sheets
# ---------------------------------------------------------------------------

def update_main_sheet(spreadsheet, rows: list):
    """Replaces 'Daily Report' sheet with today's screener data."""
    try:
        ws = spreadsheet.worksheet("Daily Report")
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet("Daily Report", rows=500, cols=40)

    # Write all data at once (batch for speed)
    ws.update(rows, value_input_option="RAW")

    # Freeze header row
    ws.freeze(rows=1)

    print(f"  ✅ Daily Report sheet updated — {len(rows)-1} stocks")
    return ws


def update_historical_sheet(spreadsheet, rows: list):
    """
    Appends today's data to 'Historical' sheet.
    Keeps all past runs — used for trend charts in Looker Studio.
    """
    try:
        ws = spreadsheet.worksheet("Historical")
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet("Historical", rows=10000, cols=40)
        # Write header only once
        ws.append_row(rows[0], value_input_option="RAW")
        print("  ✅ Historical sheet created with headers")

    # Append data rows (skip header)
    if len(rows) > 1:
        ws.append_rows(rows[1:], value_input_option="RAW")
        print(f"  ✅ Historical sheet — appended {len(rows)-1} rows")


def update_summary_sheet(spreadsheet, rows: list):
    """
    Updates a clean 'Summary' sheet with key stats and top picks.
    This is what Looker Studio scorecards read from.
    """
    try:
        ws = spreadsheet.worksheet("Summary")
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet("Summary", rows=50, cols=5)

    today = datetime.now().strftime("%d-%b-%Y")

    # Calculate stats from data rows
    data_rows = rows[1:]  # skip header
    headers   = rows[0]

    def col(name):
        try:
            idx = headers.index(name)
            return [r[idx] for r in data_rows if len(r) > idx]
        except ValueError:
            return []

    def safe_float(v):
        try: return float(v)
        except: return 0.0

    scores  = [safe_float(v) for v in col("Total Score")]
    grades  = col("Grade")
    sectors = col("Sector")

    from collections import Counter
    grade_count = Counter(grades)
    top_sector  = Counter(sectors).most_common(1)[0][0] if sectors else "N/A"

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    top_score = round(max(scores), 1) if scores else 0
    min_score = round(min(scores), 1) if scores else 0

    summary = [
        ["Metric",              "Value"],
        ["Run Date",            today],
        ["Total Stocks",        len(data_rows)],
        ["Avg Score",           avg_score],
        ["Top Score",           top_score],
        ["Min Score",           min_score],
        ["Grade A+ Count",      grade_count.get("A+", 0)],
        ["Grade A Count",       grade_count.get("A",  0)],
        ["Grade B Count",       grade_count.get("B",  0)],
        ["Grade C Count",       grade_count.get("C",  0)],
        ["Grade D Count",       grade_count.get("D",  0)],
        ["Top Sector",          top_sector],
        ["Last Updated",        datetime.now().strftime("%d-%b-%Y %H:%M IST")],
    ]

    ws.update(summary, value_input_option="RAW")
    ws.freeze(rows=1)
    print(f"  ✅ Summary sheet updated — {today}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 50)
    print("  Google Sheets Updater")
    print("=" * 50)

    # Validate env vars
    if not SHEET_ID:
        print("❌ GOOGLE_SHEET_ID not set"); return
    if not CREDENTIALS_JSON:
        print("❌ GOOGLE_SHEETS_CREDENTIALS not set"); return
    if not os.path.exists(CSV_PATH):
        print(f"❌ CSV not found: {CSV_PATH}"); return

    # Connect
    print("Connecting to Google Sheets...")
    client      = get_client()
    spreadsheet = client.open_by_key(SHEET_ID)
    print(f"  ✅ Connected to: {spreadsheet.title}")

    # Load CSV
    print("Loading screener CSV...")
    rows = load_csv(CSV_PATH)
    print(f"  ✅ Loaded {len(rows)-1} stocks")

    # Update all 3 sheets
    print("Updating sheets...")
    update_main_sheet(spreadsheet, rows)
    update_historical_sheet(spreadsheet, rows)
    update_summary_sheet(spreadsheet, rows)

    print("=" * 50)
    print("  ✅ Google Sheets fully updated!")
    print(f"  🔗 https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    print("=" * 50)


if __name__ == "__main__":
    main()
