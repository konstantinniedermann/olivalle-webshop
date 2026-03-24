import sqlite3
from pathlib import Path

from app.config import settings

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_db()
    try:
        for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            conn.executescript(sql_file.read_text())
        conn.commit()
    finally:
        conn.close()
