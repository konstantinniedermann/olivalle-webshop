def test_ueber_das_oel_status(client):
    """Die 'Über das Öl'-Seite ist erreichbar."""
    response = client.get("/ueber-das-oel")
    assert response.status_code == 200


def test_ueber_das_oel_inhalt(client):
    """Die Seite enthält die vier Abschnitte mit neuen Titeln
    (ohne bestimmten Artikel)."""
    response = client.get("/ueber-das-oel")
    assert "Unser Olivenöl" in response.text
    # Neue Titel ohne bestimmten Artikel (SH-Feedback 2026-04-21)
    assert ">Herkunft<" in response.text
    assert ">Kooperative OLIPE<" in response.text
    assert ">Qualität<" in response.text
    assert "Von Andalusien in die Schweiz" in response.text
    # Alte Titel mit "Die" sind entfernt
    assert ">Die Herkunft<" not in response.text
    assert ">Die Kooperative OLIPE<" not in response.text
    assert ">Die Qualität<" not in response.text


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


def test_ueber_das_oel_herkunft_text(client):
    """Der Herkunft-Text enthält die vom SH überarbeitete Formulierung."""
    response = client.get("/ueber-das-oel")
    assert "Nevadillo Blanco" in response.text
    assert "Berghainen" in response.text  # bewusst so gewählt (Hain am Berg)
    assert "Sierra Morena" in response.text
    # "geerntet" ist neu (alter Text endete mit "von Hand gearbeitet,
    # wie seit Generationen")
    assert "geerntet" in response.text


def test_ueber_das_oel_kooperative_vollname(client):
    """Die Kooperative-Kachel nennt den ausformulierten Namen."""
    response = client.get("/ueber-das-oel")
    assert "Olivarera Los Pedroches" in response.text
    assert "800 Bauernfamilien" in response.text
    assert "Produzierenden" in response.text


def test_ueber_das_oel_typo_korrigiert(client):
    """Der Typo 'jahrzentelang' ist zu 'jahrzehntelang' korrigiert."""
    response = client.get("/ueber-das-oel")
    assert "jahrzehntelang" in response.text
    assert "jahrzentelang" not in response.text


def test_ueber_das_oel_qualitaet_text(client):
    """Der Qualität-Text beschreibt das Geschmacksprofil."""
    response = client.get("/ueber-das-oel")
    assert "12 bis 24 Stunden" in response.text
    assert "Polyphenolgehalt" in response.text
    assert "fruchtig, leicht bitter" in response.text
    # "angenehmen Schärfe" single-line (im Abgang folgt in separater Jinja-Zeile)
    assert "angenehmen Schärfe" in response.text


def test_ueber_das_oel_andalusien_text(client):
    """Der Andalusien-Text endet mit dem neuen SH-Schlusssatz."""
    response = client.get("/ueber-das-oel")
    assert "Generalimporteur" in response.text
    assert "Ohne Zwischenhändler, ohne Umwege" in response.text
    assert "Leidenschaft für ein wunderbares Produkt" in response.text
