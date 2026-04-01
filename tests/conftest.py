import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.database import MIGRATIONS_DIR
from app.main import app


@pytest.fixture()
def db(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        conn.executescript(sql_file.read_text())
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("app.config.settings.database_path", db_path)
    from app.database import init_db
    init_db()
    return TestClient(app)


@pytest.fixture()
def csrf_token():
    from app.config import settings
    from app.csrf import generiere_csrf_token
    return generiere_csrf_token(settings.secret_key)
