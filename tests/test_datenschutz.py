def test_datenschutz_status(client):
    """Die Datenschutzseite ist erreichbar."""
    response = client.get("/datenschutz")
    assert response.status_code == 200


def test_datenschutz_verantwortlich(client):
    """Abschnitt 'Verantwortlich' mit Link zum Impressum."""
    response = client.get("/datenschutz")
    assert "Verantwortlich" in response.text
    assert "/impressum" in response.text


def test_datenschutz_rechtsgrundlage(client):
    """Zweck-Abschnitt nennt Kaufvertrag als Rechtsgrundlage."""
    response = client.get("/datenschutz")
    assert "Kaufvertrag" in response.text


def test_datenschutz_ausland(client):
    """Hinweis auf Datenbekanntgabe in die USA (Stripe)."""
    response = client.get("/datenschutz")
    assert "Bekanntgabe ins Ausland" in response.text
    assert "Standardvertragsklauseln" in response.text


def test_datenschutz_stripe_cookies(client):
    """Stripe Fraud-Detection-Cookies erwähnt."""
    response = client.get("/datenschutz")
    assert "Betrugserkennung" in response.text


def test_datenschutz_server_logs(client):
    """Abschnitt Server-Logs vorhanden."""
    response = client.get("/datenschutz")
    assert "Server-Logs" in response.text
    assert "IP-Adresse" in response.text


def test_datenschutz_datenherausgabe(client):
    """Recht auf Datenherausgabe (Art. 28 DSG) aufgeführt."""
    response = client.get("/datenschutz")
    assert "Datenherausgabe" in response.text
    assert "Art. 28 DSG" in response.text


def test_datenschutz_stand_datum(client):
    """Stand-Datum am Ende der Seite."""
    response = client.get("/datenschutz")
    assert "Stand: 16. April 2026" in response.text
