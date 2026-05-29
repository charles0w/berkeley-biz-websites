"""Business store with two interchangeable backends.

- **Supabase** (when SUPABASE_URL + SUPABASE_SERVICE_KEY are set) — durable
  state that survives GitHub Actions runs. This is what makes the scrape
  cron safe to enable. Matches the pattern used by shopify-arbitrage.
- **SQLite** (fallback) — local dev / no-creds. Same `data/businesses.db`
  file as before.

The public `Database()` interface is identical for both backends so the
scraper/generator/outreach callers don't change. Re-scraping a known
place_id only updates the freshly-scraped columns — demo_url and the
outreach_* fields are preserved across both backends.
"""
import os
import re
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'businesses.db')

# Columns the scraper writes; everything else (status, demo_url, outreach_*)
# is owned by the generator/outreach stages and must survive a re-scrape.
_SCRAPE_COLS = {
    'name', 'address', 'phone', 'website', 'rating', 'review_count',
    'category', 'hours_json', 'photo_refs', 'lat', 'lng', 'slug',
}


def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    s = s.strip('-')
    return s


class Database:
    def __init__(self):
        url = os.environ.get('SUPABASE_URL', '')
        key = os.environ.get('SUPABASE_SERVICE_KEY', '')
        if url and key:
            from supabase import create_client
            self.backend = 'supabase'
            self.sb = create_client(url, key)
        else:
            self.backend = 'sqlite'
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            self.conn = sqlite3.connect(DB_PATH)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute('PRAGMA journal_mode=WAL')
            self._init_schema()

    # ── SQLite schema (no-op for Supabase; run supabase/schema.sql there) ──
    def _init_schema(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS businesses (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                place_id            TEXT    UNIQUE NOT NULL,
                name                TEXT    NOT NULL,
                address             TEXT,
                phone               TEXT,
                website             TEXT,
                rating              REAL,
                review_count        INTEGER,
                category            TEXT,
                hours_json          TEXT,
                photo_refs          TEXT,
                lat                 REAL,
                lng                 REAL,
                slug                TEXT,
                owner_name          TEXT,
                owner_email         TEXT,
                status              TEXT    DEFAULT 'scraped',
                demo_url            TEXT,
                outreach_status     TEXT    DEFAULT 'new',
                outreach_sent_at    TEXT,
                outreach_channel    TEXT,
                outreach_subject    TEXT,
                outreach_body_id    TEXT,
                outreach_opened_at  TEXT,
                outreach_replied_at TEXT,
                closed_amount       REAL,
                notes               TEXT,
                created_at          TEXT    DEFAULT (datetime('now')),
                updated_at          TEXT    DEFAULT (datetime('now'))
            );
        ''')
        self.conn.commit()

    def upsert_business(self, data: dict):
        if not data.get('slug'):
            data['slug'] = slugify(data['name'])

        if self.backend == 'supabase':
            existing = self.get_business(data['place_id'])
            if existing:
                # Only touch scraped columns — preserve demo_url/outreach_*.
                self.update_business(data['place_id'], **{
                    k: v for k, v in data.items()
                    if k != 'place_id' and k in _SCRAPE_COLS
                })
            else:
                self.sb.table('businesses').insert(data).execute()
            return

        cols = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        updates = ', '.join(
            f"{k} = excluded.{k}" for k in data if k != 'place_id'
        )
        self.conn.execute(
            f'''INSERT INTO businesses ({cols}) VALUES ({placeholders})
                ON CONFLICT(place_id) DO UPDATE SET {updates},
                updated_at = datetime('now')''',
            list(data.values())
        )
        self.conn.commit()

    def get_business(self, place_id: str) -> dict | None:
        if self.backend == 'supabase':
            res = (self.sb.table('businesses').select('*')
                   .eq('place_id', place_id).limit(1).execute())
            return res.data[0] if res.data else None

        row = self.conn.execute(
            'SELECT * FROM businesses WHERE place_id = ?', (place_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_all(self, status: str | None = None) -> list[dict]:
        if self.backend == 'supabase':
            q = self.sb.table('businesses').select('*')
            if status:
                q = q.eq('status', status)
            res = q.order('rating', desc=True).order('review_count', desc=True).execute()
            return res.data or []

        if status:
            rows = self.conn.execute(
                'SELECT * FROM businesses WHERE status = ? ORDER BY rating DESC, review_count DESC',
                (status,)
            ).fetchall()
        else:
            rows = self.conn.execute(
                'SELECT * FROM businesses ORDER BY rating DESC, review_count DESC'
            ).fetchall()
        return [dict(r) for r in rows]

    def update_business(self, place_id: str, **kwargs):
        if self.backend == 'supabase':
            payload = dict(kwargs)
            payload['updated_at'] = datetime.now(timezone.utc).isoformat()
            self.sb.table('businesses').update(payload).eq('place_id', place_id).execute()
            return

        sets = ', '.join(f"{k} = ?" for k in kwargs)
        self.conn.execute(
            f"UPDATE businesses SET {sets}, updated_at = datetime('now') WHERE place_id = ?",
            list(kwargs.values()) + [place_id]
        )
        self.conn.commit()

    def count(self) -> int:
        if self.backend == 'supabase':
            res = self.sb.table('businesses').select('place_id', count='exact').execute()
            return res.count or 0

        return self.conn.execute('SELECT COUNT(*) FROM businesses').fetchone()[0]
