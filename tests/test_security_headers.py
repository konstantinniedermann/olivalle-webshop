from fastapi.testclient import TestClient


def test_basis_security_header_auf_homepage(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    csp = response.headers["content-security-policy"]
    assert "default-src 'self'" in csp
    assert "https://js.stripe.com" in csp
    assert "frame-ancestors 'none'" in csp


def test_hsts_nur_bei_https(client: TestClient):
    # ohne x-forwarded-proto: kein HSTS
    response = client.get("/health")
    assert "strict-transport-security" not in response.headers

    # mit x-forwarded-proto: https → HSTS
    response = client.get("/health", headers={"x-forwarded-proto": "https"})
    hsts = response.headers["strict-transport-security"]
    assert "max-age=31536000" in hsts
    assert "includeSubDomains" in hsts


def test_admin_login_frame_ancestors(client: TestClient):
    response = client.get("/admin/login")
    assert response.status_code == 200
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
