"""Regressionsschutz: get_db() muss WAL-Modus aktivieren.

Litestream repliziert über das SQLite-WAL. Fällt der WAL-Modus aus,
funktioniert das Backup stillschweigend nicht mehr.
"""


def test_get_db_aktiviert_wal_modus(monkeypatch, tmp_path):
    db_path = tmp_path / "olivalle-test.db"
    monkeypatch.setattr("app.config.settings.database_path", str(db_path))

    from app.database import get_db

    conn = get_db()
    try:
        row = conn.execute("PRAGMA journal_mode").fetchone()
        assert row[0].lower() == "wal", (
            f"journal_mode ist {row[0]}, erwartet 'wal' — "
            "ohne WAL funktioniert die Litestream-Replikation nicht"
        )
    finally:
        conn.close()
