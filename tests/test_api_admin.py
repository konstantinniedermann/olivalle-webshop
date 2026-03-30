import bcrypt
import pytest
from fastapi.testclient import TestClient


def _make_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


@pytest.fixture()
def admin_client(tmp_path, monkeypatch):
    pw_hash = _make_hash("testpass")
    monkeypatch.setattr("app.config.settings.database_path", str(tmp_path / "test.db"))
    monkeypatch.setattr("app.config.settings.admin_credentials", f"dev:{pw_hash}")
    from app.database import init_db

    init_db()
    from app.main import app

    return TestClient(app)


class TestAdminLogin:
    def test_login_page_renders(self, admin_client):
        resp = admin_client.get("/admin/login")
        assert resp.status_code == 200
        assert "Passwort" in resp.text

    def test_login_success_redirects_to_dashboard(self, admin_client):
        resp = admin_client.post(
            "/admin/login",
            data={"password": "testpass", "csrf_token": ""},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        assert resp.headers["location"] == "/admin/"
        assert "admin_session" in resp.cookies

    def test_login_wrong_password(self, admin_client):
        resp = admin_client.post(
            "/admin/login",
            data={"password": "falsch", "csrf_token": ""},
        )
        assert resp.status_code == 200
        assert "Ungültig" in resp.text

    def test_dashboard_requires_login(self, admin_client):
        resp = admin_client.get("/admin/", follow_redirects=False)
        assert resp.status_code == 303
        assert "/admin/login" in resp.headers["location"]


class TestAdminDashboard:
    def _login(self, client):
        resp = client.post(
            "/admin/login",
            data={"password": "testpass", "csrf_token": ""},
            follow_redirects=False,
        )
        return resp.cookies

    def test_dashboard_renders(self, admin_client):
        cookies = self._login(admin_client)
        admin_client.cookies = cookies
        resp = admin_client.get("/admin/")
        assert resp.status_code == 200
        assert "Dashboard" in resp.text

    def test_logout_clears_session(self, admin_client):
        cookies = self._login(admin_client)
        admin_client.cookies = cookies
        resp = admin_client.post(
            "/admin/logout",
            data={"csrf_token": ""},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        admin_client.cookies = resp.cookies
        resp2 = admin_client.get("/admin/", follow_redirects=False)
        assert resp2.status_code == 303


class TestEmailLogging:
    def test_email_service_logs_ausgang(self, db, monkeypatch):
        """After sending an email, an email_ausgang log entry should exist."""
        monkeypatch.setattr(
            "app.services.email_service.resend.Emails.send", lambda **kw: {"id": "mock"}
        )

        from app.services.email_service import sende_bestellbestaetigung

        db.execute(
            "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
            "VALUES ('Max', 'Muster', 'max@test.ch', 'Str 1', '4600', 'Olten')"
        )
        db.execute(
            "INSERT INTO bestellungen (kunde_id, zahlungsart, versandart, total_chf) "
            "VALUES (1, 'stripe', 'versand', 50.00)"
        )
        db.commit()

        sende_bestellbestaetigung(
            empfaenger="max@test.ch",
            bestell_id=1,
            kunde={"vorname": "Max", "nachname": "Muster"},
            positionen=[{"name": "Öl 250ml", "menge": 2, "einzelpreis_chf": 8.0}],
            versandkosten=9.90,
            total=25.90,
            conn=db,
        )

        log = db.execute(
            "SELECT * FROM admin_log WHERE aktion = 'email_ausgang'"
        ).fetchone()
        assert log is not None
        assert "max@test.ch" in log["details"]
