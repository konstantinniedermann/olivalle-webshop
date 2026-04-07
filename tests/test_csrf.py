import time

import pytest
from fastapi import HTTPException

from app.csrf import generiere_csrf_token, require_csrf, validiere_csrf_token


def test_csrf_token_roundtrip():
    token = generiere_csrf_token("test-secret")
    assert validiere_csrf_token(token, "test-secret")


def test_csrf_token_ungueltig():
    assert not validiere_csrf_token("fake-token", "test-secret")


def test_csrf_token_abgelaufen():
    # Token mit max_age=-1 sofort abgelaufen (itsdangerous: age > max_age)
    token = generiere_csrf_token("test-secret", max_age=-1)
    time.sleep(0.1)
    assert not validiere_csrf_token(token, "test-secret", max_age=-1)


def test_require_csrf_akzeptiert_gueltiges_token():
    from app.config import settings

    token = generiere_csrf_token(settings.secret_key)
    require_csrf(csrf_token=token)


def test_require_csrf_wirft_bei_leerem_token():
    with pytest.raises(HTTPException) as exc:
        require_csrf(csrf_token="")
    assert exc.value.status_code == 403


def test_require_csrf_wirft_bei_ungueltigem_token():
    with pytest.raises(HTTPException) as exc:
        require_csrf(csrf_token="garbage")
    assert exc.value.status_code == 403


def test_bestellen_ohne_csrf_abgelehnt(client):
    import json
    cart = json.dumps([{"produkt_id": 1, "menge": 1}])
    response = client.post("/bestellen", data={
        "vorname": "Max", "nachname": "Muster",
        "email": "max@test.ch", "strasse": "Str. 1",
        "plz": "4600", "ort": "Olten",
        "versandart": "versand", "zahlungsart": "rechnung",
        "cart_data": cart, "kommentar": "",
        "csrf_token": "ungueltig",
    })
    assert response.status_code == 403
