from fastapi.testclient import TestClient


def test_health_gibt_nur_status_zurueck(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}
    assert "version" not in data
