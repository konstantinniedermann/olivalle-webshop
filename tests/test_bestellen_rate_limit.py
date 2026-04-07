from fastapi.testclient import TestClient

from app.main import app


def test_bestellen_rate_limit_429():
    client = TestClient(app)
    # 10 erlaubt, 11. blockiert. Body egal — Limit-Check als Dependency.
    for _ in range(10):
        r = client.post("/bestellen", data={})
        assert r.status_code != 429
    r = client.post("/bestellen", data={})
    assert r.status_code == 429
