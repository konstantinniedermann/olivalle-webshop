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


def test_ueber_das_oel_bio_code(client):
    """Die OLIPE-Kachel enthält den Bio-Kontrollstellen-Code."""
    response = client.get("/ueber-das-oel")
    assert "ES-ECO-001-AN" in response.text
    assert "C.A.A.E." in response.text


def test_ueber_das_oel_produktinformation(client):
    """Die Seite enthält die Kachel 'Produktinformation'."""
    response = client.get("/ueber-das-oel")
    assert "Produktinformation" in response.text


def test_ueber_das_oel_sachbezeichnung(client):
    """Sachbezeichnung ist auf der Seite deklariert."""
    response = client.get("/ueber-das-oel")
    assert "Natives Olivenöl extra" in response.text


def test_ueber_das_oel_gueteklasse(client):
    """Güteklasse-Pflichtsatz ist vorhanden."""
    response = client.get("/ueber-das-oel")
    assert "ausschliesslich mit mechanischen Verfahren" in response.text


def test_ueber_das_oel_naehrwerte(client):
    """Nährwerttabelle ist vorhanden mit allen Pflichtangaben."""
    response = client.get("/ueber-das-oel")
    assert "Nährwerte pro 100 g" in response.text
    assert "3700 kJ" in response.text
    assert "900 kcal" in response.text
    assert "Vitamin E" in response.text


def test_ueber_das_oel_lagerhinweis(client):
    """Lagerhinweis ist vorhanden."""
    response = client.get("/ueber-das-oel")
    assert "Kühl und dunkel lagern" in response.text
