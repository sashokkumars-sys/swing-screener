# =============================================================================
# telegram_alert.py — Sends daily swing screener results to Telegram
# =============================================================================

import os
import csv
import requests
from datetime import datetime
from collections import Counter

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID")
CSV_PATH  = "output/swing_screener_report.csv"

GRADE_EMOJI = {"A+": "🟢", "A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴"}


def load_results(csv_path):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def escape(text):
    """Escape special chars for Telegram MarkdownV2."""
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in str(text))


def build_message(rows):
    today = datetime.now().strftime("%d %b %Y")
    rows_sorted = sorted(rows, key=lambda x: float(x.get("Total Score", 0) or 0), reverse=True)

    total     = len(rows_sorted)
    scores    = [float(r.get("Total Score", 0) or 0) for r in rows_sorted]
    avg_score = round(sum(scores) / total, 1) if total else 0
    top_score = round(max(scores), 1) if scores else 0
    min_score = round(min(scores), 1) if scores else 0

    grades      = [r.get("Grade", "D") for r in rows_sorted]
    grade_count = Counter(grades)

    top10_sectors = [r.get("Sector", "Unknown") for r in rows_sorted[:10]]
    top_sector    = Counter(top10_sectors).most_common(1)[0][0] if top10_sectors else "Unknown"

    top_picks = [r for r in rows_sorted if r.get("Grade") in ("A+", "A")][:5]
    if len(top_picks) < 5:
        top_picks += [r for r in rows_sorted if r.get("Grade") == "B"][:5 - len(top_picks)]
    top_picks = top_picks[:5]

    lines = []
    lines.append(f"📈 *NSE Swing Screener — {escape(today)}*")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("🏆 *TOP PICKS TODAY*")

    if top_picks:
        for i, r in enumerate(top_picks, 1):
            symbol = escape(r.get("Symbol", ""))
            score  = float(r.get("Total Score", 0) or 0)
            grade  = r.get("Grade", "D")
            rsi    = escape(r.get("RSI (14)", "0"))
            sector = escape(r.get("Sector", "")[:15])
            emoji  = GRADE_EMOJI.get(grade, "⚪")
            flags  = r.get("Flags", "")

            short_flags = []
            if "MACD Cross" in flags:  short_flags.append("🔥 MACD")
            if "Supertrend" in flags:  short_flags.append("✅ ST")
            if "EMA Bull"   in flags:  short_flags.append("📈 EMA")
            if "High Volume" in flags: short_flags.append("📊 Vol↑")
            if "52W High"   in flags:  short_flags.append("🏆 52W")
            if "High ROE"   in flags:  short_flags.append("💎 ROE")
            flag_str = escape(" | ".join(short_flags[:3]) if short_flags else "—")

            lines.append(
                f"{i}\\. *{symbol}* — Score: `{escape(f'{score:.1f}')}` {emoji} *{escape(grade)}*\n"
                f"   RSI: `{rsi}` \\| {sector}\n"
                f"   {flag_str}"
            )
    else:
        lines.append("_No strong picks today — market weak_")

    lines.append("")
    lines.append("📊 *MARKET STATS*")
    lines.append(f"• Stocks Screened: `{escape(str(total))}`")
    lines.append(f"• Avg Score: `{escape(str(avg_score))}`")
    lines.append(f"• Top Score: `{escape(str(top_score))}` \\| Min: `{escape(str(min_score))}`")
    lines.append(f"• Top Sector: `{escape(top_sector)}`")
    lines.append("")

    lines.append("🎯 *GRADE DISTRIBUTION*")
    for grade in ["A+", "A", "B", "C", "D"]:
        count = grade_count.get(grade, 0)
        if count > 0:
            bar = "█" * min(count, 10)
            lines.append(f"  {GRADE_EMOJI.get(grade, '⚪')} {escape(grade)}: `{count}` {escape(bar)}")
    lines.append("")

    a_plus = grade_count.get("A+", 0)
    a_cnt  = grade_count.get("A", 0)
    b_cnt  = grade_count.get("B", 0)

    if a_plus >= 3:
        signal = "🚀 *Strong Bull — High conviction day*"
    elif a_plus + a_cnt >= 3:
        signal = "✅ *Good Market — Selective buying zone*"
    elif b_cnt >= 5:
        signal = "🟡 *Cautious — Only top B grades*"
    elif avg_score < 45:
        signal = "⛔ *Weak Market — Stay on sidelines*"
    else:
        signal = "⚠️ *Mixed Market — Wait for confirmation*"

    lines.append(signal)
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("_⚠️ Research only\\. Not financial advice\\._")

    return "\n".join(lines)


def send_message(token, chat_id, text):
    url  = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id":    chat_id,
        "text":       text,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True,
    }
    r = requests.post(url, data=data, timeout=30)
    if r.status_code == 200:
        print("✅ Telegram alert sent!")
        return True
    else:
        print(f"❌ Telegram error {r.status_code}: {r.text}")
        return False


def main():
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set"); return
    if not CHAT_ID:
        print("❌ TELEGRAM_CHAT_ID not set"); return

    print("Loading results...")
    rows = load_results(CSV_PATH)
    print(f"Loaded {len(rows)} stocks")

    message = build_message(rows)
    send_message(BOT_TOKEN, CHAT_ID, message)


if __name__ == "__main__":
    main()
