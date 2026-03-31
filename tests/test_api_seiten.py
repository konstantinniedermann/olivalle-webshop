def test_ueber_das_oel_status(client):
    """Die 'Über das Öl'-Seite ist erreichbar."""
    response = client.get("/ueber-das-oel")
    assert response.status_code == 200


def test_ueber_das_oel_inhalt(client):
    """Die Seite enthält die vier Abschnitte."""
    response = client.get("/ueber-das-oel")
    assert "Unser Olivenöl" in response.text
    assert "Die Herkunft" in response.text
    assert "Die Kooperative OLIPE" in response.text
    assert "Die Qualität" in response.text
    assert "Von Andalusien in die Schweiz" in response.text


def test_ueber_das_oel_hintergrundbild(client):
    """Die Seite verwendet das Olivenbaum-Hintergrundbild."""
    response = client.get("/ueber-das-oel")
    assert "backgrounds/olive-tree-hero.jpg" in response.text


def test_ueber_das_oel_cta(client):
    """Die Seite enthält einen CTA-Link zu den Produkten."""
    response = client.get("/ueber-das-oel")
    assert "Zu unseren Produkten" in response.text
    assert 'href="/"' in response.text


def test_ueber_das_oel_active_page(client):
    """Die Navigation markiert 'Über das Öl' als aktiv."""
    response = client.get("/ueber-das-oel")
    assert "ueber-das-oel" in response.text
