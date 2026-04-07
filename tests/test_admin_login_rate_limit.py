from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import _login_csrf


def test_admin_login_rate_limit_429():
    client = TestClient(app)
    csrf = _login_csrf(client)
    for _ in range(5):
        r = client.post("/admin/login", data={"password": "x", "csrf_token": csrf})
        assert r.status_code != 429
    r = client.post("/admin/login", data={"password": "x", "csrf_token": csrf})
    assert r.status_code == 429


def test_lockout_response_indistinguishable_from_invalid_password():
    """Lockout darf nicht durch Polling erkennbar sein."""
    from app.services.auth_service import login_guard

    client = TestClient(app)
    csrf = _login_csrf(client)

    # Erster Versuch mit falschem Passwort -> Invalid-Password-Body
    r1 = client.post("/admin/login", data={"password": "x", "csrf_token": csrf})
    assert r1.status_code == 200
    assert "Ungültiges Passwort" in r1.text

    # Lockout erzwingen (BruteForceGuard direkt füttern)
    # TestClient setzt request.client.host = "testclient"
    for _ in range(10):
        login_guard.record_failure("testclient")

    # Zweiter Versuch -> Lockout, aber gleicher Body wie Invalid-Password
    r2 = client.post("/admin/login", data={"password": "x", "csrf_token": csrf})
    assert "Ungültiges Passwort" in r2.text
    assert "Zu viele Fehlversuche" not in r2.text

    login_guard.reset("testclient")
