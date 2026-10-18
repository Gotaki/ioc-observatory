-- One row per indicator, from any source.
-- Columns match the IOC dataclass in common/ioc.py.
CREATE TABLE IF NOT EXISTS iocs (
    id            BIGSERIAL PRIMARY KEY,        -- internal auto-numbered row ID
    source        TEXT NOT NULL,                -- 'urlhaus', 'cisa_kev', 'otx'
    source_id     TEXT NOT NULL,                -- the source's own ID for this indicator
    ioc_type      TEXT NOT NULL,                -- 'url', 'domain', 'ip', 'cve'
    value         TEXT NOT NULL,                -- the indicator itself
    first_seen    TIMESTAMPTZ,                  -- when the source first reported it (UTC)
    last_seen     TIMESTAMPTZ,                  -- when the source last saw it online
    status        TEXT,                         -- e.g. 'online' / 'offline'
    threat        TEXT,                         -- e.g. 'malware_download'
    tags          TEXT[] NOT NULL DEFAULT '{}', -- list of tags
    reference_url TEXT,                         -- link back to the source's page
    ingested_at   TIMESTAMPTZ NOT NULL DEFAULT now(),  -- when WE first stored it;
                                                       -- used to count "new this run"

    -- Same indicator from the same source can only exist once.
    -- Inserting a duplicate conflicts, which is how we tell new from already-seen.
    UNIQUE (source, source_id)
);

-- Speeds up "how many rows were added in the last N minutes" queries.
CREATE INDEX IF NOT EXISTS iocs_ingested_at_idx ON iocs (ingested_at);