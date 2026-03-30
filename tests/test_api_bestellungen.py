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


@patch("app.services.email_service.resend.Emails.send", return_value={"id": "test"})
@patch("app.services.qr_service.QRBill")
def test_bestellen_rechnung_erfolgreich(
    mock_qrbill, mock_email, client, monkeypatch, csrf_token
):
    # Set QR settings for test
    monkeypatch.setattr("app.config.settings.qr_iban", "CH4431999123000889012")
    monkeypatch.setattr("app.config.settings.qr_name", "Test GmbH")
    monkeypatch.setattr("app.config.settings.qr_address", "Teststr. 1")
    monkeypatch.setattr("app.config.settings.qr_zip", "3000")
    monkeypatch.setattr("app.config.settings.qr_city", "Bern")

    # Mock QRBill to return SVG bytes
    mock_bill_instance = mock_qrbill.return_value
    mock_bill_instance.as_svg.side_effect = lambda buf: buf.write("<svg>test</svg>")

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
