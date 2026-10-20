"""Database helper: store IOCs and report how many were new."""
import psycopg
from common.ioc import IOC

# ON CONFLICT DO NOTHING: an IOC we already stored is silently skipped.
# That is how "new vs already seen" works (UNIQUE on source + source_id).
INSERT_SQL = """
INSERT INTO iocs (source, source_id, ioc_type, value, first_seen, last_seen,
                  status, threat, tags, reference_url)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (source, source_id) DO NOTHING
"""


def save_iocs(iocs: list[IOC]) -> tuple[int, int]:
    """Insert IOCs, skipping known ones. Returns (new_count, total_for_this_source)."""
    if not iocs:
        return 0, 0
    source = iocs[0].source        # every IOC in one call comes from the same source
    rows = [(i.source, i.source_id, i.ioc_type, i.value, i.first_seen, i.last_seen,
             i.status, i.threat, list(i.tags), i.reference_url) for i in iocs]

    with psycopg.connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM iocs WHERE source = %s", (source,))
        before = cur.fetchone()[0]
        cur.executemany(INSERT_SQL, rows)
        cur.execute("SELECT count(*) FROM iocs WHERE source = %s", (source,))
        after = cur.fetchone()[0]
    return after - before, after