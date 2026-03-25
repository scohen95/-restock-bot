"""
storage/state_store.py

Lightweight SQLite-backed state tracker.
Stores whether each URL was last seen in-stock or out-of-stock.
This prevents duplicate alerts — we only alert on state CHANGES.
"""

import sqlite3
import logging
from pathlib import Path

log = logging.getLogger("store")

DB_PATH = Path("data/state.db")


class StateStore:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._create_table()
        log.info(f"StateStore ready at {DB_PATH}")

    def _create_table(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS product_state (
                url       TEXT PRIMARY KEY,
                in_stock  INTEGER NOT NULL DEFAULT 0,
                updated   TEXT DEFAULT (datetime('now'))
            )
        """)
        self._conn.commit()

    def get_state(self, url: str) -> bool:
        """Return True if this URL was last seen in-stock. Defaults to False."""
        row = self._conn.execute(
            "SELECT in_stock FROM product_state WHERE url = ?", (url,)
        ).fetchone()
        return bool(row[0]) if row else False

    def set_state(self, url: str, in_stock: bool):
        self._conn.execute("""
            INSERT INTO product_state (url, in_stock, updated)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(url) DO UPDATE SET
                in_stock = excluded.in_stock,
                updated  = excluded.updated
        """, (url, int(in_stock)))
        self._conn.commit()

    def all_states(self) -> list[dict]:
        """Return all tracked URLs and their current known state."""
        rows = self._conn.execute(
            "SELECT url, in_stock, updated FROM product_state ORDER BY updated DESC"
        ).fetchall()
        return [{"url": r[0], "in_stock": bool(r[1]), "updated": r[2]} for r in rows]

    def reset(self, url: str):
        """Force-clear a URL's state (useful for testing alerts)."""
        self._conn.execute("DELETE FROM product_state WHERE url = ?", (url,))
        self._conn.commit()
        log.info(f"State reset for: {url}")
