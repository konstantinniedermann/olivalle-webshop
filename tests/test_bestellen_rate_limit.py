from fastapi.testclient import TestClient

from app.main import app
from app.services.rate_limit import bestellung_limiter


def test_bestellen_rate_limit_429():
    bestellung_limiter._requests.clear()
    client = TestClient(app)
    # 10 erlaubt, 11. blockiert. Body egal — Limit-Check ist erste Zeile.
    for _ in range(10):
        r = client.post("/bestellen", data={})
        assert r.status_code != 429
    r = client.post("/bestellen", data={})
    assert r.status_code == 429
    bestellung_limiter._requests.clear()
