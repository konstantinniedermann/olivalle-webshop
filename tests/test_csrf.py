import time

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.csrf import (
    admin_identity,
    generiere_csrf_token,
    require_csrf,
    validiere_csrf_token,
)


def _make_request(cookies: dict[str, str]) -> Request:
    cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items()).encode()
    scope = {
        "type": "http",
        "headers": [(b"cookie", cookie_header)] if cookie_header else [],
    }
    return Request(scope)


def test_token_roundtrip_mit_identity():
    token = generiere_csrf_token("secret", identity="user-A")
    assert validiere_csrf_token(token, "secret", expected_identity="user-A")


def test_token_andere_identity_abgelehnt():
    token = generiere_csrf_token("secret", identity="user-A")
    assert not validiere_csrf_token(token, "secret", expected_identity="user-B")


def test_token_leere_identity_abgelehnt():
    token = generiere_csrf_token("secret", identity="user-A")
    assert not validiere_csrf_token(token, "secret", expected_identity="")


def test_token_ungueltig():
    assert not validiere_csrf_token("garbage", "secret", expected_identity="x")


def test_token_abgelaufen():
    token = generiere_csrf_token("secret", identity="x", max_age=-1)
    time.sleep(0.1)
    assert not validiere_csrf_token(
        token, "secret", expected_identity="x", max_age=-1
    )


def test_admin_identity_stabil_und_unterschiedlich():
    a = admin_identity("session-token-a")
    b = admin_identity("session-token-b")
    assert a == admin_identity("session-token-a")
    assert a != b
    assert "session-token-a" not in a  # nicht im Klartext


def test_require_csrf_admin_kontext_ok():
    from app.config import settings

    identity = admin_identity("admin-cookie-1")
    token = generiere_csrf_token(settings.secret_key, identity=identity)
    request = _make_request({"admin_session": "admin-cookie-1"})
    require_csrf(request=request, csrf_token=token)


def test_require_csrf_admin_kontext_falsche_session_403():
    from app.config import settings

    identity = admin_identity("admin-cookie-1")
    token = generiere_csrf_token(settings.secret_key, identity=identity)
    request = _make_request({"admin_session": "admin-cookie-OTHER"})
    with pytest.raises(HTTPException) as exc:
        require_csrf(request=request, csrf_token=token)
    assert exc.value.status_code == 403


def test_require_csrf_anonym_kontext_ok():
    from app.config import settings

    token = generiere_csrf_token(settings.secret_key, identity="anon:anon-1")
    request = _make_request({"csrf_id": "anon-1"})
    require_csrf(request=request, csrf_token=token)


def test_require_csrf_anonym_kontext_fremder_cookie_403():
    from app.config import settings

    token = generiere_csrf_token(settings.secret_key, identity="anon:anon-1")
    request = _make_request({"csrf_id": "anon-OTHER"})
    with pytest.raises(HTTPException) as exc:
        require_csrf(request=request, csrf_token=token)
    assert exc.value.status_code == 403


def test_require_csrf_ohne_identity_403():
    from app.config import settings

    token = generiere_csrf_token(settings.secret_key, identity="x")
    request = _make_request({})
    with pytest.raises(HTTPException) as exc:
        require_csrf(request=request, csrf_token=token)
    assert exc.value.status_code == 403


def test_require_csrf_leeres_token_403():
    request = _make_request({"csrf_id": "anon-1"})
    with pytest.raises(HTTPException) as exc:
        require_csrf(request=request, csrf_token="")
    assert exc.value.status_code == 403


def test_bestellen_csrf_id_roundtrip(client):
    import json
    import re

    get_resp = client.get("/checkout")
    assert get_resp.status_code == 200
    assert "csrf_id" in client.cookies

    match = re.search(r'name="csrf_token" value="([^"]+)"', get_resp.text)
    assert match, "csrf_token nicht im Template gefunden"
    token = match.group(1)

    cart = json.dumps([{"produkt_id": 1, "menge": 1}])
    payload = {
        "vorname": "Max", "nachname": "Muster",
        "email": "max@test.ch", "strasse": "Str. 1",
        "plz": "4600", "ort": "Olten",
        "versandart": "abholung", "zahlungsart": "rechnung",
        "cart_data": cart, "kommentar": "",
        "csrf_token": token,
    }
    resp = client.post("/bestellen", data=payload)
    assert resp.status_code != 403


def test_bestellen_fremdes_token_abgelehnt(client):
    import json

    from app.config import settings
    from app.csrf import generiere_csrf_token

    fremdes_token = generiere_csrf_token(
        settings.secret_key, identity="anon:fremd"
    )
    client.get("/checkout")
    cart = json.dumps([{"produkt_id": 1, "menge": 1}])
    resp = client.post("/bestellen", data={
        "vorname": "Max", "nachname": "Muster",
        "email": "max@test.ch", "strasse": "Str. 1",
        "plz": "4600", "ort": "Olten",
        "versandart": "abholung", "zahlungsart": "rechnung",
        "cart_data": cart, "kommentar": "",
        "csrf_token": fremdes_token,
    })
    assert resp.status_code == 403
