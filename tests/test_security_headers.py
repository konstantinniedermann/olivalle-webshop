import re

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


def test_security_headers_auch_auf_www_redirect(client: TestClient):
    # 301-Redirect von www → apex soll ebenfalls Security-Headers tragen
    response = client.get(
        "/", headers={"host": "www.olivalle.ch"}, follow_redirects=False
    )
    assert response.status_code == 301
    assert "x-content-type-options" in response.headers
    assert "content-security-policy" in response.headers


def test_admin_login_frame_ancestors(client: TestClient):
    response = client.get("/admin/login")
    assert response.status_code == 200
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_csp_enthaelt_nonce_und_kein_unsafe_inline(client: TestClient):
    response = client.get("/")
    csp = response.headers["content-security-policy"]
    script_src = next(p for p in csp.split(";") if p.strip().startswith("script-src"))
    assert "'unsafe-inline'" not in script_src
    assert re.search(r"'nonce-[A-Za-z0-9_\-]{16,}'", script_src), script_src


def test_csp_nonce_pro_request_unterschiedlich(client: TestClient):
    r1 = client.get("/").headers["content-security-policy"]
    r2 = client.get("/").headers["content-security-policy"]
    n1 = re.search(r"'nonce-([A-Za-z0-9_\-]+)'", r1).group(1)
    n2 = re.search(r"'nonce-([A-Za-z0-9_\-]+)'", r2).group(1)
    assert n1 != n2


def test_csp_nonce_im_html_vorhanden_und_passt_zum_header(client: TestClient):
    response = client.get("/")
    csp = response.headers["content-security-policy"]
    header_nonce = re.search(r"'nonce-([A-Za-z0-9_\-]+)'", csp).group(1)
    assert f'nonce="{header_nonce}"' in response.text
