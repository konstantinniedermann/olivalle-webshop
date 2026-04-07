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
