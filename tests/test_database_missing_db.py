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
