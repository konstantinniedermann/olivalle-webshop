"""Statische Assets (JS/CSS) müssen pro Deploy cache-bustend referenziert werden.

Hintergrund: Ohne Versions-Query darf der Browser eine veraltete `cart.js`
ausliefern. Fehlt darin eine Funktion (z.B. getRabattSubtotal, eingeführt mit
#134), bricht der Rabattcode-Handler im Checkout lautlos ab — der Button "tut
nichts". Ein `?v={app_version}` an JS/CSS erzwingt nach jedem Deploy einen
Neuladen.
"""

from app.config import settings


def test_cart_js_ist_cache_bustend_referenziert(client):
    """base.html muss cart.js mit ?v=<app_version> einbinden."""
    html = client.get("/").text
    assert f"/static/js/cart.js?v={settings.app_version}" in html


def test_app_css_ist_cache_bustend_referenziert(client):
    """base.html muss app.css mit ?v=<app_version> einbinden."""
    html = client.get("/").text
    assert f"css/app.css?v={settings.app_version}" in html
