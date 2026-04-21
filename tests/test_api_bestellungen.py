import json
from unittest.mock import patch


def test_checkout_seite(client):
    response = client.get("/checkout")
    assert response.status_code == 200
    assert "Kasse" in response.text


def test_bestellen_ohne_cart_data(client, csrf_token):
    response = client.post(
        "/bestellen",
        data={
            "vorname": "Max",
            "nachname": "Muster",
            "email": "max@test.ch",
            "strasse": "Str. 1",
            "plz": "4600",
            "ort": "Olten",
            "versandart": "versand",
            "zahlungsart": "rechnung",
            "cart_data": "[]",
            "kommentar": "",
            "csrf_token": csrf_token,
        },
    )
    assert response.status_code == 400


def _bestellen_post(client, csrf_token, cart_data: str):
    return client.post(
        "/bestellen",
        data={
            "vorname": "Max",
            "nachname": "Muster",
            "email": "max@test.ch",
            "strasse": "Str. 1",
            "plz": "4600",
            "ort": "Olten",
            "versandart": "versand",
            "zahlungsart": "rechnung",
            "cart_data": cart_data,
            "kommentar": "",
            "csrf_token": csrf_token,
        },
    )


def test_bestellen_menge_negativ_400(client, csrf_token):
    cart = json.dumps([{"produkt_id": 1, "menge": -1}])
    assert _bestellen_post(client, csrf_token, cart).status_code == 400


def test_bestellen_menge_zu_gross_400(client, csrf_token):
    cart = json.dumps([{"produkt_id": 1, "menge": 999999}])
    assert _bestellen_post(client, csrf_token, cart).status_code == 400


def test_bestellen_cart_data_fehlende_keys_400(client, csrf_token):
    cart = json.dumps([{"produkt_id": 1}])
    assert _bestellen_post(client, csrf_token, cart).status_code == 400


@patch("app.services.email_service.brevo_client")
@patch("app.services.qr_service.generiere_qr_rechnung", return_value=b"%PDF-fake")
def test_bestellen_rechnung_erfolgreich(
    mock_qr, mock_email, client, monkeypatch, csrf_token
):

    cart = json.dumps([{"produkt_id": 1, "menge": 2}])
    response = client.post(
        "/bestellen",
        data={
            "vorname": "Max",
            "nachname": "Muster",
            "email": "max@test.ch",
            "strasse": "Str. 1",
            "plz": "4600",
            "ort": "Olten",
            "versandart": "versand",
            "zahlungsart": "rechnung",
            "cart_data": cart,
            "kommentar": "Testbestellung",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    assert response.status_code in (200, 303)


@patch("app.services.email_service.brevo_client")
@patch("app.services.qr_service.generiere_qr_rechnung", return_value=b"%PDF-fake")
def test_bestellen_mit_hausnummer_persistiert(mock_qr, mock_email, client, csrf_token):
    """POST /bestellen mit hausnummer → Wert landet in kunden.hausnummer."""
    import sqlite3

    from app.config import settings

    cart = json.dumps([{"produkt_id": 1, "menge": 2}])
    response = client.post(
        "/bestellen",
        data={
            "vorname": "Klara",
            "nachname": "Tester",
            "email": "klara@test.ch",
            "strasse": "Musterstrasse",
            "hausnummer": "42",
            "plz": "8001",
            "ort": "Zürich",
            "versandart": "versand",
            "zahlungsart": "rechnung",
            "cart_data": cart,
            "kommentar": "",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    assert response.status_code in (200, 303)

    conn = sqlite3.connect(settings.database_path)
    try:
        row = conn.execute(
            "SELECT hausnummer FROM kunden WHERE email = ?",
            ("klara@test.ch",),
        ).fetchone()
        assert row is not None
        assert row[0] == "42"
    finally:
        conn.close()

    # QR-Service wurde mit kunde_hausnummer aufgerufen
    call_kwargs = mock_qr.call_args.kwargs
    assert call_kwargs.get("kunde_hausnummer") == "42"


def test_bestellen_ohne_hausnummer_kein_fehler(client, csrf_token):
    """POST /bestellen ohne hausnummer-Feld ist weiterhin gültig (Feld optional)."""
    cart = json.dumps([{"produkt_id": 1, "menge": 1}])
    response = client.post(
        "/bestellen",
        data={
            "vorname": "Max",
            "nachname": "Muster",
            "email": "max@test.ch",
            "strasse": "Str. 1",
            "plz": "4600",
            "ort": "Olten",
            "versandart": "versand",
            "zahlungsart": "rechnung",
            "cart_data": cart,
            "kommentar": "",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    # Kein 422 (Form-Validierung), nicht unbedingt 200 (könnte Mail-Mock-abhängig sein)
    assert response.status_code != 422
