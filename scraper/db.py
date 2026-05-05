"""SQLite layer for the business pipeline. Tracks scraping → build → outreach → sale."""

import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "businesses.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS businesses (
    place_id            TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    address             TEXT,
    phone               TEXT,
    email               TEXT,
    lat                 REAL,
    lng                 REAL,
    rating              REAL,
    ratings_count       INTEGER,
    types               TEXT,   -- JSON array
    photo_refs          TEXT,   -- JSON array of photo_reference strings
    hours               TEXT,   -- JSON array of weekday_text strings
    business_status     TEXT,
    scraped_at          TEXT DEFAULT (datetime('now')),

    -- Pipeline state
    site_built          INTEGER DEFAULT 0,
    site_url            TEXT,
    generating          INTEGER DEFAULT 0,
    generate_error      TEXT,
    outreach_sent       INTEGER DEFAULT 0,
    outreach_sent_at    TEXT,
    responded           INTEGER DEFAULT 0,
    response_positive   INTEGER DEFAULT 0,
    sold                INTEGER DEFAULT 0,
    sale_amount         REAL,
    skipped             INTEGER DEFAULT 0,
    notes               TEXT
);
"""

# Columns added after initial schema — applied safely on every startup
_MIGRATIONS = [
    "ALTER TABLE businesses ADD COLUMN email TEXT",
    "ALTER TABLE businesses ADD COLUMN generating INTEGER DEFAULT 0",
    "ALTER TABLE businesses ADD COLUMN generate_error TEXT",
    "ALTER TABLE businesses ADD COLUMN skipped INTEGER DEFAULT 0",
    "ALTER TABLE businesses ADD COLUMN notes TEXT",
]


def _conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as c:
        c.executescript(_SCHEMA)
        for migration in _MIGRATIONS:
            try:
                c.execute(migration)
            except sqlite3.OperationalError:
                pass  # column already exists


def is_scraped(place_id: str) -> bool:
    with _conn() as c:
        return c.execute("SELECT 1 FROM businesses WHERE place_id = ?", (place_id,)).fetchone() is not None


def save_business(result: dict) -> None:
    geo = result.get("geometry", {}).get("location", {})
    photos = [p["photo_reference"] for p in result.get("photos", [])[:10]]
    hours = result.get("opening_hours", {}).get("weekday_text", [])

    with _conn() as c:
        c.execute(
            """
            INSERT OR IGNORE INTO businesses
              (place_id, name, address, phone, lat, lng, rating, ratings_count,
               types, photo_refs, hours, business_status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                result.get("place_id"),
                result.get("name"),
                result.get("formatted_address"),
                result.get("formatted_phone_number"),
                geo.get("lat"),
                geo.get("lng"),
                result.get("rating"),
                result.get("user_ratings_total"),
                json.dumps(result.get("types", [])),
                json.dumps(photos),
                json.dumps(hours),
                result.get("business_status"),
            ),
        )


def count_businesses() -> int:
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM businesses").fetchone()[0]


def get_business(place_id: str) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM businesses WHERE place_id = ?", (place_id,)).fetchone()
        return dict(row) if row else None


def get_businesses_without_site() -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM businesses WHERE site_built = 0 ORDER BY rating DESC NULLS LAST"
        ).fetchall()
        return [dict(r) for r in rows]


def get_businesses_ready_for_outreach() -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM businesses WHERE site_built = 1 AND outreach_sent = 0 ORDER BY rating DESC NULLS LAST"
        ).fetchall()
        return [dict(r) for r in rows]


def mark_site_built(place_id: str, url: str) -> None:
    with _conn() as c:
        c.execute(
            "UPDATE businesses SET site_built = 1, site_url = ? WHERE place_id = ?",
            (url, place_id),
        )


def mark_outreach_sent(place_id: str) -> None:
    with _conn() as c:
        c.execute(
            "UPDATE businesses SET outreach_sent = 1, outreach_sent_at = datetime('now') WHERE place_id = ?",
            (place_id,),
        )
