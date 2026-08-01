-- BIBI-tabs schema. Postgres (Neon).
--
-- Two rules run through every table here:
--   owner_id  is on every user-owned row from day one, populated with a single
--             constant until real accounts exist. Every query filters by it, so
--             multi-account stays additive rather than a migration.
--   deleted_at is a tombstone. Rows are never hard-deleted -- a hard delete is
--             invisible to the other device, which resurrects the row on its
--             next sync.

CREATE TABLE IF NOT EXISTS song (
    id          UUID        PRIMARY KEY,
    owner_id    UUID        NOT NULL,
    title       TEXT        NOT NULL,
    artist      TEXT,
    chordpro    TEXT        NOT NULL,  -- the single source of truth, original key
    source_url  TEXT,                  -- provenance: where it came from
    source      TEXT,                  -- 'ug' | 'boiteachansons' | 'paste'
    prefs       JSONB,                 -- {transpose, capo} -- never font size or layout
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at  TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS setlist (
    id          UUID        PRIMARY KEY,
    owner_id    UUID        NOT NULL,
    name        TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at  TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS setlist_song (
    setlist_id  UUID    NOT NULL REFERENCES setlist(id) ON DELETE CASCADE,
    song_id     UUID    NOT NULL REFERENCES song(id)    ON DELETE CASCADE,
    position    INTEGER NOT NULL,
    PRIMARY KEY (setlist_id, song_id)
);

-- Sync pulls "everything of mine changed since T", so this is the hot path.
CREATE INDEX IF NOT EXISTS song_owner_updated_idx    ON song    (owner_id, updated_at);
CREATE INDEX IF NOT EXISTS setlist_owner_updated_idx ON setlist (owner_id, updated_at);
