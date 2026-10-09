"""DSE Market Capitalisation collector.

Fetches day-end MARKET CAPITALISATION from DSE's public JSON API and
appends one row per trading session to dse_market_cap.csv.
Safe to run multiple times a day: same session_date is recorded once
(existing row for that date is updated, not duplicated).

API: https://www.dse.com.bd/api/live/market-statistics
Schedule suggestion (Windows Task Scheduler): Sun-Thu 15:00 Dhaka time
(DSE closes 14:00, Thu = last trading day of week).
"""
import csv
import json
import urllib.request
from datetime import datetime
from pathlib import Path

API_URL = "https://www.dse.com.bd/api/live/market-statistics"
CSV_FILE = Path(__file__).with_name("dse_market_cap.csv")
COLUMNS = ["fetched_at", "session_date", "equity", "mutual_fund", "debt", "total"]


def fetch() -> dict:
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    cap = data.get("marketCap", {})
    return {
        "session_date": str(cap.get("date", "")),
        "equity": int(cap.get("equity") or 0),
        "mutual_fund": int(cap.get("mutualFund") or 0),
        "debt": int(cap.get("debt") or 0),
        "total": int(cap.get("total") or 0),
    }


def save(row: dict) -> str:
    rows: list[dict] = []
    if CSV_FILE.exists():
        with CSV_FILE.open("r", newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    now = datetime.now().astimezone().isoformat()
    new_row = {"fetched_at": now, **row}
    for r in rows:
        if r.get("session_date") == row["session_date"]:
            r.update(new_row)
            action = "updated"
            break
    else:
        rows.append(new_row)
        action = "added"
    with CSV_FILE.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows([{c: r.get(c, "") for c in COLUMNS} for r in rows])
    return action


if __name__ == "__main__":
    row = fetch()
    assert row["session_date"] and row["total"] > 0, f"Bad API data: {row}"
    action = save(row)
    print(f"{action}: {row} -> {CSV_FILE.resolve()}")
