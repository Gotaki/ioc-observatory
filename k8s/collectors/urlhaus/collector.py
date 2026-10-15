"""URLhaus collector (local version).

In one line: download the list of recently reported malware URLs from
abuse.ch's URLhaus, turn it into Python data, and print a short summary.
"""
import csv
import os
import sys
from collections import Counter

import requests
from dotenv import load_dotenv

# Base address of the URLhaus export files. The API key is inserted into it below.
BASE = "https://urlhaus-api.abuse.ch/v2/files/exports"

def fetch_recent(auth_key: str) -> str:

"""Download recent.csv and return its contents as one big string."""
    # abuse.ch expects the key as part of the address itself.

    url = f"{BASE}/{auth_key}/recent.csv"
    try:

    # Ask the server for the file. Give up after 30 seconds.
        resp = requests.get(url, timeout=30)
    except requests.RequestException as exc:
        # Network problem (no internet, DNS failure, timeout).
        # Print only the error TYPE: the full message would include the URL,
        # and the URL contains your secret key.       
        sys.exit(f"Request failed ({type(exc).__name__})")
    if resp.status_code != 200:

        # 200 means OK. Anything else (401/403 = bad key, 5xx = server trouble) stops the script.
        sys.exit(f"URLhaus returned HTTP {resp.status_code}")
    return resp.text


def parse(text: str):
    """Turn the CSV text into (column_names, list_of_records)."""
    header, rows = None, []
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.startswith("#"):
            candidate = line.lstrip("# ").strip()
            if "," in candidate and "url" in candidate.lower():
                header = next(csv.reader([candidate]))
            continue
        # A normal line is one record. csv.reader splits it correctly even when
        # a value contains a comma inside quotes. It expects a list of lines,
        # so we pass [line] and take the first (only) result with next().
        rows.append(next(csv.reader([line])))
    if header is None and rows:
        header = rows.pop(0)
    header = header or []
    # Pair the column names with each row so a record becomes a dictionary,
    # e.g. {"id": "123", "url": "http://...", "url_status": "online", ...}
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
            # Count how often each value appears in that column and show the top 5,
            # e.g. {'offline': 17783, 'online': 16109}
            print(f"{col}: {dict(Counter(r[col] for r in records).most_common(5))}")


if __name__ == "__main__":
    main()
