from fastapi.testclient import TestClient


def test_www_wird_auf_apex_umgeleitet(client: TestClient):
    response = client.get(
        "/health", headers={"host": "www.olivalle.ch"}, follow_redirects=False
    )
    assert response.status_code == 301
    assert response.headers["location"] == "http://olivalle.ch/health"


def test_www_respektiert_x_forwarded_proto(client: TestClient):
    response = client.get(
        "/health",
        headers={"host": "www.olivalle.ch", "x-forwarded-proto": "https"},
        follow_redirects=False,
    )
    assert response.status_code == 301
    assert response.headers["location"] == "https://olivalle.ch/health"


def test_apex_wird_nicht_umgeleitet(client: TestClient):
    response = client.get(
        "/health", headers={"host": "olivalle.ch"}, follow_redirects=False
    )
    assert response.status_code == 200
