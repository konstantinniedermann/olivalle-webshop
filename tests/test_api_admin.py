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
