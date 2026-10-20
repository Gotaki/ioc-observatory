"""CISA KEV collector: downloads the Known Exploited Vulnerabilities catalogue,
stores each CVE in Postgres, and reports metrics to the OTel Collector."""
import sys
import time

import requests
from opentelemetry import metrics

from common.db import save_iocs
from common.ioc import from_kev
from common.telemetry import setup_metrics

URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


def fetch() -> list[dict]:
    """Download the catalogue and return its list of vulnerability entries."""
    resp = requests.get(URL, timeout=30)
    resp.raise_for_status()                 # raises on HTTP errors such as 404 or 500
    return resp.json()["vulnerabilities"]


def main() -> None:
    provider = setup_metrics("cisa-kev-collector")
    meter = metrics.get_meter("cisa-kev-collector")

    g_records = meter.create_gauge("cisa_kev.records.fetched", description="Entries in the catalogue this run")
    g_new = meter.create_gauge("cisa_kev.records.new", description="CVEs first seen in this run")
    g_total = meter.create_gauge("cisa_kev.db.total", description="Total KEV CVEs stored in Postgres")
    g_duration = meter.create_gauge("cisa_kev.run.duration", unit="s", description="Run time in seconds")
    g_success = meter.create_gauge("cisa_kev.last_run.success", description="1 if the last run worked, else 0")
    g_last_ok = meter.create_gauge("cisa_kev.last_success.timestamp", unit="s", description="Unix time of last good run")

    start = time.monotonic()
    ok = False
    try:
        items = fetch()
        print(f"entries fetched: {len(items)}")
        g_records.set(len(items))

        iocs = [from_kev(i) for i in items]
        new_count, total = save_iocs(iocs)
        print(f"new IOCs: {new_count}, total stored: {total}")
        g_new.set(new_count)
        g_total.set(total)
        ok = True
    except Exception as exc:
        print(f"run failed: {type(exc).__name__}")   # type only, same safe habit as URLhaus
    finally:
        g_duration.set(time.monotonic() - start)
        g_success.set(1 if ok else 0)
        if ok:
            g_last_ok.set(time.time())
        if provider is not None:
            provider.force_flush()
            provider.shutdown()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()