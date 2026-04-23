import sqlite3
from pathlib import Path

from app.config import settings

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def get_db() -> sqlite3.Connection:
    """Connection für Request-Handler. mode=rw — keine Auto-Creation.

    Fehlt die DB-Datei, wirft sqlite3 OperationalError → FastAPI antwortet mit
    500. Das verhindert, dass ein Volume-Glitch silent eine leere DB hinterlässt
    und dadurch den entrypoint.sh-Auto-Restore blockiert (Issue #122).
    """
    conn = sqlite3.connect(
        f"file:{settings.database_path}?mode=rw", uri=True
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _connect_bootstrap() -> sqlite3.Connection:
    """Connection für init_db — mode=rwc, erstellt DB falls nicht vorhanden.

    Wird nur beim Bootstrap aufgerufen (entrypoint.sh Schritt 2 → init_db;
    zusätzlich läuft init_db auch beim FastAPI-Import in app.main — idempotent).
    """
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _add_column_if_not_exists(
    conn: sqlite3.Connection, table: str, column: str, col_def: str
) -> None:
    """Spalte hinzufuegen, falls sie noch nicht existiert (SQLite-Workaround)."""
    columns = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]  # noqa: S608
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")  # noqa: S608


def init_db() -> None:
    conn = _connect_bootstrap()
    try:
        for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            conn.executescript(sql_file.read_text())
        # ALTER TABLE Spalten fuer Rabattcodes (idempotent)
        _add_column_if_not_exists(
            conn,
            "bestellungen",
            "rabattcode_id",
            "INTEGER REFERENCES rabattcodes(id)",
        )
        _add_column_if_not_exists(
            conn,
            "bestellungen",
            "rabattbetrag_chf",
            "REAL NOT NULL DEFAULT 0",
        )
        _add_column_if_not_exists(
            conn,
            "kunden",
            "hausnummer",
            "TEXT NOT NULL DEFAULT ''",
        )
        conn.commit()
    finally:
        conn.close()
