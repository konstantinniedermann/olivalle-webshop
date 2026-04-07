from fastapi.testclient import TestClient

from app.config import settings
from app.csrf import generiere_csrf_token
from app.main import app


def test_admin_login_rate_limit_429():
    client = TestClient(app)
    csrf = generiere_csrf_token(settings.secret_key)
    for _ in range(5):
        r = client.post("/admin/login", data={"password": "x", "csrf_token": csrf})
        assert r.status_code != 429
    r = client.post("/admin/login", data={"password": "x", "csrf_token": csrf})
    assert r.status_code == 429
