import json


def test_checkout_seite(client):
    response = client.get("/checkout")
    assert response.status_code == 200
    assert "Kasse" in response.text


def test_bestellen_ohne_cart_data(client):
    response = client.post("/bestellen", data={
        "vorname": "Max", "nachname": "Muster",
        "email": "max@test.ch", "strasse": "Str. 1",
        "plz": "4600", "ort": "Olten",
        "versandart": "versand", "zahlungsart": "rechnung",
        "cart_data": "[]", "kommentar": "",
        "csrf_token": "test",
    })
    assert response.status_code == 400


def test_bestellen_rechnung_erfolgreich(client):
    cart = json.dumps([{"produkt_id": 1, "menge": 2}])
    response = client.post("/bestellen", data={
        "vorname": "Max", "nachname": "Muster",
        "email": "max@test.ch", "strasse": "Str. 1",
        "plz": "4600", "ort": "Olten",
        "versandart": "versand", "zahlungsart": "rechnung",
        "cart_data": cart, "kommentar": "Testbestellung",
        "csrf_token": "test",
    }, follow_redirects=False)
    # Redirect to Bestätigung oder direkte Anzeige
    assert response.status_code in (200, 303)
