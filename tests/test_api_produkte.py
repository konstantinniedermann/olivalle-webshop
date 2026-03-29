def test_startseite_status(client):
    response = client.get("/")
    assert response.status_code == 200


def test_startseite_enthaelt_produkte(client):
    response = client.get("/")
    assert "Olivenöl 250ml" in response.text
    assert "CHF 8" in response.text
    assert "ideal zum Kennenlernen" in response.text


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


def test_warenkorb_card_struktur(client):
    """Warenkorb nutzt Card-basiertes Layout statt Tabelle."""
    response = client.get("/warenkorb")
    # Keine Tabelle mehr
    assert "<table" not in response.text
    assert "<thead" not in response.text
    # Card-Klassen vorhanden
    assert "cart-card" in response.text


def test_checkout_autocomplete(client):
    """Checkout-Formular hat autocomplete-Attribute für Browser-Autofill."""
    response = client.get("/checkout")
    assert 'autocomplete="given-name"' in response.text
    assert 'autocomplete="family-name"' in response.text
    assert 'autocomplete="email"' in response.text
    assert 'autocomplete="street-address"' in response.text
    assert 'autocomplete="postal-code"' in response.text
    assert 'autocomplete="address-level2"' in response.text


def test_checkout_optional_hinweise(client):
    """Optionale Felder sind als solche gekennzeichnet."""
    response = client.get("/checkout")
    assert "(optional)" in response.text


def test_checkout_card_sektionen(client):
    """Checkout-Sektionen sind als Cards gestaltet."""
    response = client.get("/checkout")
    assert response.text.count("bg-stone-700 rounded-lg") >= 3


def test_bestaetigung_card(client):
    """Bestätigungsseite zeigt Inhalt in einer Card."""
    response = client.get("/bestaetigung")
    assert response.status_code == 200
    assert "bg-stone-700 rounded-lg" in response.text
    assert "shadow-md" in response.text
