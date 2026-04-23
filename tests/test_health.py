from fastapi.testclient import TestClient


def test_health_gibt_200_und_status_ok_bei_erreichbarer_db(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_gibt_503_bei_fehlender_db(tmp_path, monkeypatch):
    """Wenn die DB-Datei weg ist, MUSS /health 503 antworten statt
    fälschlicherweise 'ok' zu melden. Konsistent mit Issue #122."""
    from app.main import app

    db_path = tmp_path / "does_not_exist.db"
    monkeypatch.setattr("app.config.settings.database_path", str(db_path))
    monkeypatch.setattr("app.config.settings.cookie_secure", False)

    test_client = TestClient(app, raise_server_exceptions=False)
    response = test_client.get("/health")

    assert response.status_code == 503
    assert not db_path.exists(), "DB darf nicht angelegt werden"
