"""URLhaus collector (local version): fetch the recent-URLs dump and summarise it."""
import csv
import os
import sys
from collections import Counter

import requests
from dotenv import load_dotenv

BASE = "https://urlhaus-api.abuse.ch/v2/files/exports"


def fetch_recent(auth_key: str) -> str:
    url = f"{BASE}/{auth_key}/recent.csv"
    try:
        resp = requests.get(url, timeout=30)
    except requests.RequestException as exc:
        # Never print the exception text: it can contain the URL, and the URL contains the key.
        sys.exit(f"Request failed ({type(exc).__name__})")
    if resp.status_code != 200:
        sys.exit(f"URLhaus returned HTTP {resp.status_code}")
    return resp.text


def parse(text: str):
    header, rows = None, []
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.startswith("#"):
            candidate = line.lstrip("# ").strip()
            if "," in candidate and "url" in candidate.lower():
                header = next(csv.reader([candidate]))
            continue
        rows.append(next(csv.reader([line])))
    if header is None and rows:
        header = rows.pop(0)
    header = header or []
    return header, [dict(zip(header, r)) for r in rows]


def main() -> None:
    load_dotenv()
    key = os.environ.get("ABUSE_CH_AUTH_KEY")
    if not key:
        sys.exit("ABUSE_CH_AUTH_KEY is not set (put it in .env)")
    header, records = parse(fetch_recent(key))
    print(f"columns: {header}")
    print(f"records fetched: {len(records)}")
    for col in ("url_status", "threat"):
        if col in header:
            print(f"{col}: {dict(Counter(r[col] for r in records).most_common(5))}")


if __name__ == "__main__":
    main()
