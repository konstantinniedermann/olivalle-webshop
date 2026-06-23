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


def test_startseite_warenkorb_flyout(client):
    """Startseite enthält das Mini-Warenkorb-Flyout."""
    response = client.get("/")
    assert 'id="cart-flyout"' in response.text
    assert "Zur Kasse" in response.text


def test_startseite_teaser(client):
    """Startseite zeigt kurzen Teaser mit Link zu 'Über das Öl'."""
    response = client.get("/")
    assert "Biologisches Olivenöl extra virgen" in response.text
    assert 'href="/ueber-das-oel"' in response.text
    assert "Nährwerte" in response.text


def test_startseite_kein_langer_hero(client):
    """Der lange Variante-B Text ist nicht mehr auf der Startseite."""
    response = client.get("/")
    assert "Kooperative OLIPE" not in response.text


def test_header_sticky(client):
    """Header ist sticky mit Backdrop-Blur."""
    response = client.get("/")
    assert "sticky" in response.text
    assert "top-0" in response.text
    assert "backdrop-blur" in response.text


def test_header_navigation_links(client):
    """Header enthält Navigation: Über das Öl, Produkte, Warenkorb."""
    response = client.get("/")
    assert 'href="/ueber-das-oel"' in response.text
    assert "Über das Öl" in response.text
    assert 'href="/"' in response.text
    assert "Produkte" in response.text
    assert "Warenkorb" in response.text


def test_header_active_page_produkte(client):
    """Auf der Startseite ist 'Produkte' als aktiv markiert."""
    response = client.get("/")
    # Der aktive Link hat text-accent Klasse
    assert "text-accent" in response.text


def test_startseite_hintergrund_olivenbaum(client):
    """Die Produktseite nutzt den Olivenbaum-Hintergrund (SH-Feedback 2026-04-21)."""
    response = client.get("/")
    assert "backgrounds/olive-tree-hero.jpg" in response.text
    # Vorheriger Terracotta-Hintergrund ist ersetzt
    assert "backgrounds/terracotta-texture.webp" not in response.text


def test_startseite_zeigt_aktionspreis(client):
    from app.database import get_db

    conn = get_db()
    conn.execute(
        "UPDATE produkte SET aktionspreis_chf = 12.0, "
        "aktionstext = 'MHD 09/2026' WHERE id = 2"
    )
    conn.commit()
    conn.close()
    resp = client.get("/")
    assert resp.status_code == 200
    assert "RABATT" in resp.text
    assert "MHD 09/2026" in resp.text
    assert "CHF 12.00" in resp.text


def test_startseite_ohne_aktion_kein_badge(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "RABATT" not in resp.text


def test_startseite_aktion_null_prozent_badge_versteckt(client):
    """F4: Aktionspreis der auf 0% rundet zeigt kein '−0%'-Badge.

    750ml kostet CHF 18.00. Aktionspreis CHF 17.95 → Rabatt 0.28% → rundet
    zu 0 (round(0.28) == 0). Das RABATT-Badge und der durchgestrichene Preis
    bleiben erhalten, aber der Prozent-Chip '−0%' darf nicht sichtbar sein.
    """
    from app.database import get_db

    conn = get_db()
    conn.execute("UPDATE produkte SET aktionspreis_chf = 17.95 WHERE id = 2")
    conn.commit()
    conn.close()
    resp = client.get("/")
    assert resp.status_code == 200
    # RABATT-Badge bleibt sichtbar
    assert "RABATT" in resp.text
    # Prozent-Chip mit −0% darf nicht erscheinen (U+2212 Minus)
    assert "−0" not in resp.text
