import sqlite3

import pytest

from app.database import get_db


def test_get_db_wirft_operational_error_bei_fehlender_db(tmp_path, monkeypatch):
    """Fehlt die DB-Datei, MUSS get_db() OperationalError werfen und DARF
    keine leere DB anlegen (sonst wird der entrypoint.sh-Auto-Restore durch
    die Existenz einer leeren Datei blockiert — Bug aus Issue #115 / #122).
    """
    db_path = tmp_path / "does_not_exist.db"
    monkeypatch.setattr("app.config.settings.database_path", str(db_path))

    assert not db_path.exists()

    with pytest.raises(sqlite3.OperationalError):
        get_db()

    # Kern des Bugs: nach dem Aufruf darf kein File entstanden sein.
    assert not db_path.exists()


from fastapi.testclient import TestClient


def test_request_handler_antwortet_500_bei_fehlender_db(tmp_path, monkeypatch):
    """GET / nutzt get_db() → muss bei fehlender DB 500 antworten und darf
    keine leere DB anlegen."""
    from app.main import app  # Import zuerst — init_db läuft auf Default-DB

    db_path = tmp_path / "does_not_exist.db"
    monkeypatch.setattr("app.config.settings.database_path", str(db_path))
    monkeypatch.setattr("app.config.settings.cookie_secure", False)

    assert not db_path.exists()

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/")

    assert response.status_code == 500
    assert not db_path.exists()
