"""Common IOC schema. Every collector converts its raw rows into this shape."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class IOC:
    source: str                      # "urlhaus", "cisa_kev", "otx"
    source_id: str                   # the source's own ID
    ioc_type: str                    # "url", "domain", "ip", "cve"
    value: str                       # the indicator itself
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    status: Optional[str] = None     # e.g. "online" / "offline"
    threat: Optional[str] = None     # e.g. "malware_download"
    tags: tuple[str, ...] = ()
    reference_url: Optional[str] = None

    @property
    def key(self) -> tuple[str, str]:
        """Unique identity used for new-vs-seen detection."""
        return (self.source, self.source_id)


def _ts(text: Optional[str]) -> Optional[datetime]:
    """Parse URLhaus timestamps like '2026-10-18 01:23:45' (UTC). Empty or 'None' -> None."""
    text = (text or "").strip()
    if not text or text.lower() == "none":
        return None
    return datetime.strptime(text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def _clean(text: Optional[str]) -> Optional[str]:
    text = (text or "").strip()
    return None if not text or text.lower() == "none" else text


def from_urlhaus(row: dict) -> IOC:
    """Map one URLhaus CSV row (as a dict) to an IOC."""
    tags = tuple(t.strip() for t in (row.get("tags") or "").split(",")
                 if t.strip() and t.strip().lower() != "none")
    return IOC(
        source="urlhaus",
        source_id=str(row["id"]).strip(),
        ioc_type="url",
        value=row["url"].strip(),
        first_seen=_ts(row.get("dateadded")),
        last_seen=_ts(row.get("last_online")),
        status=_clean(row.get("url_status")),
        threat=_clean(row.get("threat")),
        tags=tags,
        reference_url=_clean(row.get("urlhaus_link")),
    )