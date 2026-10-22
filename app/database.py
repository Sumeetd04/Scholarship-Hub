"""SQLite connection handling and schema bootstrap."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from . import config

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def now_iso() -> str:
    """Timezone-aware ISO timestamp used consistently across the app."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect() -> sqlite3.Connection:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    # check_same_thread=False is safe here: every request opens its own
    # connection and work is sequential within a request, even when FastAPI
    # runs an async handler on the event loop after the dependency was
    # resolved in the threadpool.
    conn = sqlite3.connect(config.DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def get_db():
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def db_dependency():
    """FastAPI dependency that yields a request-scoped connection."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> bool:
    """Create tables and seed the catalogue once. Returns True if seeded."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = connect()
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
        already_seeded = conn.execute("SELECT COUNT(*) AS n FROM scholarships").fetchone()["n"] > 0
        if not already_seeded:
            from .seed import seed_all

            seed_all(conn)
            conn.commit()
        return not already_seeded
    finally:
        conn.close()
