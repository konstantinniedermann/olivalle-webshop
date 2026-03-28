def test_startseite_status(client):
    response = client.get("/")
    assert response.status_code == 200


def test_startseite_enthaelt_produkte(client):
    response = client.get("/")
    assert "Olivenöl 250ml" in response.text
    assert "CHF 8" in response.text


def test_warenkorb_seite(client):
    response = client.get("/warenkorb")
    assert response.status_code == 200
    assert "Warenkorb" in response.text


def test_produkte_responsive_grid(client):
    """Produktgrid nutzt stufenweise Breakpoints: 1 → 2 → 3 Spalten."""
    response = client.get("/")
    assert "sm:grid-cols-2" in response.text
    assert "lg:grid-cols-3" in response.text


def test_produkte_karten_hover(client):
    """Produktkarten haben Schatten und Hover-Effekte."""
    response = client.get("/")
    assert "shadow-md" in response.text
    assert "hover:shadow-lg" in response.text
    assert "hover:-translate-y-1" in response.text
