import sqlite3

import bcrypt
import pytest
from fastapi.testclient import TestClient

from app.database import MIGRATIONS_DIR, _add_column_if_not_exists
from app.main import app
from app.services.auth_service import login_guard
from app.services.rate_limit import bestellung_limiter, login_limiter


@pytest.fixture(autouse=True)
def _disable_cookie_secure(monkeypatch):
    """Tests laufen über http://testserver — Secure-Cookies würden sonst verworfen."""
    monkeypatch.setattr("app.config.settings.cookie_secure", False)


@pytest.fixture(autouse=True)
def _reset_rate_limit_state():
    login_limiter.reset()
    bestellung_limiter.reset()
    login_guard._failures.clear()
    yield
    login_limiter.reset()
    bestellung_limiter.reset()
    login_guard._failures.clear()


@pytest.fixture()
def db(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        conn.executescript(sql_file.read_text())
    # ALTER TABLE Spalten fuer Rabattcodes (idempotent)
    _add_column_if_not_exists(
        conn, "bestellungen", "rabattcode_id",
        "INTEGER REFERENCES rabattcodes(id)",
    )
    _add_column_if_not_exists(
        conn, "bestellungen", "rabattbetrag_chf",
        "REAL NOT NULL DEFAULT 0",
    )
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("app.config.settings.database_path", db_path)
    monkeypatch.setattr("app.config.settings.cookie_secure", False)
    monkeypatch.setattr(
        "app.routers.bestellungen.sende_bestellbestaetigung", lambda **kw: None
    )
    monkeypatch.setattr(
        "app.routers.bestellungen.sende_stakeholder_benachrichtigung", lambda **kw: None
    )
    from app.database import init_db
    init_db()
    return TestClient(app)


@pytest.fixture()
def csrf_token(client):
    from app.config import settings
    from app.csrf import generiere_csrf_token

    resp = client.get("/checkout")
    csrf_id = resp.cookies.get("csrf_id", "")
    if not csrf_id:
        for header in resp.headers.get_list("set-cookie"):
            if header.startswith("csrf_id="):
                csrf_id = header.split(";", 1)[0].split("=", 1)[1]
                client.cookies.set("csrf_id", csrf_id)
                break
    return generiere_csrf_token(
        settings.secret_key, identity=f"anon:{csrf_id}"
    )


def _checkout_csrf(client):
    """GET /checkout, persist csrf_id cookie, return matching token."""
    from app.config import settings
    from app.csrf import generiere_csrf_token

    resp = client.get("/checkout")
    csrf_id = resp.cookies.get("csrf_id", "")
    if not csrf_id:
        for header in resp.headers.get_list("set-cookie"):
            if header.startswith("csrf_id="):
                csrf_id = header.split(";", 1)[0].split("=", 1)[1]
                client.cookies.set("csrf_id", csrf_id)
                break
    return generiere_csrf_token(
        settings.secret_key, identity=f"anon:{csrf_id}"
    )


def _login_csrf(client):
    """Hilfsfunktion: GET /admin/login durchführen und passendes CSRF-Token zurückgeben.

    Stellt sicher, dass csrf_id auch bei Secure-Cookies im TestClient-Jar landet.
    """
    from app.config import settings
    from app.csrf import generiere_csrf_token

    resp = client.get("/admin/login")
    csrf_id = resp.cookies.get("csrf_id", "")
    if not csrf_id:
        # Secure-Cookie wurde von httpx verworfen — aus Set-Cookie-Header parsen.
        for header in resp.headers.get_list("set-cookie"):
            if header.startswith("csrf_id="):
                csrf_id = header.split(";", 1)[0].split("=", 1)[1]
                client.cookies.set("csrf_id", csrf_id)
                break
    return generiere_csrf_token(settings.secret_key, identity=f"anon:{csrf_id}")


def _admin_csrf(admin_session_cookie: str):
    """Hilfsfunktion: CSRF-Token gebunden an Admin-Session-Identity."""
    from app.config import settings
    from app.csrf import admin_identity, generiere_csrf_token

    return generiere_csrf_token(
        settings.secret_key, identity=admin_identity(admin_session_cookie)
    )


@pytest.fixture()
def admin_client(tmp_path, monkeypatch):
    pw_hash = bcrypt.hashpw(b"testpass", bcrypt.gensalt()).decode()
    monkeypatch.setattr("app.config.settings.database_path", str(tmp_path / "test.db"))
    monkeypatch.setattr("app.config.settings.admin_credentials", f"dev:{pw_hash}")
    monkeypatch.setattr("app.config.settings.cookie_secure", False)
    from app.database import init_db

    init_db()
    from app.main import app

    return TestClient(app)
