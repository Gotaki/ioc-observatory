"""URLhaus collector with OpenTelemetry metrics.

Downloads the recent-URLs list from abuse.ch, prints a summary, and reports
numbers (records, online/offline counts, run time, success) to an OTel Collector.
If OTEL_EXPORTER_OTLP_ENDPOINT is not set, it skips telemetry and just prints.
"""
import csv
import os
import sys
import time
from collections import Counter

import requests
from dotenv import load_dotenv
from opentelemetry import metrics

from common.ioc import from_urlhaus
from common.db import save_iocs
from common.telemetry import setup_metrics

BASE = "https://urlhaus-api.abuse.ch/v2/files/exports"


class FetchError(Exception):
    """A failure whose message is safe to print (it never contains the API key)."""


def fetch_recent(auth_key: str) -> str:
    url = f"{BASE}/{auth_key}/recent.csv"
    try:
        resp = requests.get(url, timeout=30)
    except requests.RequestException as exc:
        # "from None" hides the original error: its text contains the URL, and the URL contains the key.
        raise FetchError(f"Request failed ({type(exc).__name__})") from None
    if resp.status_code != 200:
        raise FetchError(f"URLhaus returned HTTP {resp.status_code}")
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
    provider = setup_metrics("urlhaus-collector")
    meter = metrics.get_meter("urlhaus-collector")  # a harmless no-op meter if telemetry is off

    # Gauges: "the value at the end of the latest run".
    g_records = meter.create_gauge("urlhaus.records.fetched", description="Rows in the feed this run")
    g_status = meter.create_gauge("urlhaus.records.by_status", description="Rows per url_status value")
    g_duration = meter.create_gauge("urlhaus.run.duration", unit="s", description="Run time in seconds")
    g_success = meter.create_gauge("urlhaus.last_run.success", description="1 if the last run worked, else 0")
    g_last_ok = meter.create_gauge("urlhaus.last_success.timestamp", unit="s", description="Unix time of last good run")
    g_new = meter.create_gauge("urlhaus.records.new", description="IOCs first seen in this run")
    g_total = meter.create_gauge("urlhaus.db.total", description="Total IOCs stored in Postgres")
    start = time.monotonic()
    ok = False
    try:
        key = os.environ.get("ABUSE_CH_AUTH_KEY")
        if not key:
            raise FetchError("ABUSE_CH_AUTH_KEY is not set (put it in .env)")
        header, records = parse(fetch_recent(key))
        print(f"columns: {header}")
        print(f"records fetched: {len(records)}")
        g_records.set(len(records))
        for col in ("url_status", "threat"):
            if col in header:
                counts = Counter(r[col] for r in records)
                print(f"{col}: {dict(counts.most_common(5))}")
                if col == "url_status":
                    for status, n in counts.items():
                        g_status.set(n, {"status": status})
         
        # --- NEW: store the IOCs in Postgres and count how many were new ---
        iocs = [from_urlhaus(r) for r in records]
        new_count, total = save_iocs(iocs)
        print(f"new IOCs: {new_count}, total stored: {total}")
        g_new.set(new_count)
        g_total.set(total)

        ok = True
    except FetchError as exc:
        print(f"run failed: {exc}")
    except Exception as exc:
        # Print only the exception type: the message could contain the key.
        print(f"run failed: {type(exc).__name__}")
    finally:
        g_duration.set(time.monotonic() - start)
        g_success.set(1 if ok else 0)
        if ok:
            g_last_ok.set(time.time())
        if provider is not None:
            provider.force_flush()  # send now: the process is about to exit
            provider.shutdown()
    sys.exit(0 if ok else 1)  # non-zero marks the Kubernetes Job as failed


if __name__ == "__main__":
    main()
