import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'businesses.db')


def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    s = s.strip('-')
    return s


class Database:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA journal_mode=WAL')
        self._init_schema()

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
        row = self.conn.execute(
            'SELECT * FROM businesses WHERE place_id = ?', (place_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_all(self, status: str | None = None) -> list[dict]:
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
        sets = ', '.join(f"{k} = ?" for k in kwargs)
        self.conn.execute(
            f"UPDATE businesses SET {sets}, updated_at = datetime('now') WHERE place_id = ?",
            list(kwargs.values()) + [place_id]
        )
        self.conn.commit()

    def count(self) -> int:
        return self.conn.execute('SELECT COUNT(*) FROM businesses').fetchone()[0]
