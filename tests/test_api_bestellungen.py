import json
from unittest.mock import patch


def test_checkout_seite(client):
    response = client.get("/checkout")
    assert response.status_code == 200
    assert "Kasse" in response.text


def test_bestellen_ohne_cart_data(client, csrf_token):
    response = client.post("/bestellen", data={
        "vorname": "Max", "nachname": "Muster",
        "email": "max@test.ch", "strasse": "Str. 1",
        "plz": "4600", "ort": "Olten",
        "versandart": "versand", "zahlungsart": "rechnung",
        "cart_data": "[]", "kommentar": "",
        "csrf_token": csrf_token,
    })
    assert response.status_code == 400


@patch("app.services.email_service.brevo_client")
@patch("app.services.qr_service.generiere_qr_rechnung", return_value=b"%PDF-fake")
def test_bestellen_rechnung_erfolgreich(
    mock_qr, mock_email, client, monkeypatch, csrf_token
):

    cart = json.dumps([{"produkt_id": 1, "menge": 2}])
    response = client.post("/bestellen", data={
        "vorname": "Max", "nachname": "Muster",
        "email": "max@test.ch", "strasse": "Str. 1",
        "plz": "4600", "ort": "Olten",
        "versandart": "versand", "zahlungsart": "rechnung",
        "cart_data": cart, "kommentar": "Testbestellung",
        "csrf_token": csrf_token,
    }, follow_redirects=False)
    assert response.status_code in (200, 303)
