"""
Memory store for deduplication.

Why SQLite: it's a single committed file, needs no external database
service, survives perfectly in a GitHub Actions workflow (checked out,
modified, committed back), and gives us real querying instead of hand-
rolled JSON diffing. This is the "simplest reliable option" for a
weekly-cadence, single-recipient agent.

Dedup logic (per the requirement "must not repeat information already
shared"):
  1. URL-level: an article URL we've already sent is never sent again.
  2. Content-level: articles are fingerprinted by a normalized hash of
     their title, so the same story re-reported by a different outlet
     under a different URL is still caught.
  3. Historical: the dedup table is never pruned automatically, so the
     check is against the FULL history of everything ever sent, not just
     last week.
"""

import hashlib
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

DB_PATH = "strategy_agent_memory.db"


def _normalize_title(title: str) -> str:
    """Lowercase, strip punctuation/extra whitespace so near-identical
    headlines from different outlets hash the same."""
    t = title.lower()
    t = re.sub(r"[^a-z0-9\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def fingerprint(title: str) -> str:
    return hashlib.sha256(_normalize_title(title).encode("utf-8")).hexdigest()


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sent_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                tier TEXT NOT NULL,
                source TEXT NOT NULL,
                sent_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fingerprint ON sent_items(fingerprint)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_url ON sent_items(url)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS report_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at TEXT NOT NULL,
                items_included INTEGER NOT NULL,
                items_filtered_duplicate INTEGER NOT NULL
            )
        """)


def is_duplicate(url: str, title: str) -> bool:
    """True if this exact URL OR this normalized title has been sent before."""
    fp = fingerprint(title)
    with _connect() as conn:
        cur = conn.execute(
            "SELECT 1 FROM sent_items WHERE url = ? OR fingerprint = ? LIMIT 1",
            (url, fp),
        )
        return cur.fetchone() is not None


def record_sent(items: list[dict]):
    """items: list of dicts with keys url, title, tier, source"""
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        for item in items:
            try:
                conn.execute(
                    "INSERT INTO sent_items (url, title, fingerprint, tier, source, sent_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (item["url"], item["title"], fingerprint(item["title"]),
                     item["tier"], item["source"], now),
                )
            except sqlite3.IntegrityError:
                # Already present (race or re-run) - fine, skip.
                pass


def record_run(items_included: int, items_filtered_duplicate: int):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO report_runs (run_at, items_included, items_filtered_duplicate) "
            "VALUES (?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), items_included, items_filtered_duplicate),
        )


if __name__ == "__main__":
    init_db()
    print(f"Initialized {DB_PATH}")
