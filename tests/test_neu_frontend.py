"""Neues Kunden-Frontend unter /neu (parallel zur bestehenden Seite)."""

from app.config import settings


def test_neu_startseite_erreichbar(client):
    response = client.get("/neu")
    assert response.status_code == 200
    assert "Olivenöl 750ml" in response.text


def test_neu_ist_fuer_suchmaschinen_gesperrt(client):
    html = client.get("/neu").text
    assert '<meta name="robots" content="noindex, nofollow">' in html


def test_alte_startseite_bleibt_indexierbar(client):
    assert "noindex" not in client.get("/").text


def test_neu_assets_sind_cache_bustend(client):
    html = client.get("/neu").text
    v = settings.app_version
    assert f"css/app.css?v={v}" in html
    assert f"/static/js/cart.js?v={v}" in html
    assert f"/static/js/neu.js?v={v}" in html


def test_neu_versandwerte_am_body(client):
    """cart.js liest Versandkosten und Gratis-Schwelle vom <body>."""
    html = client.get("/neu").text
    assert "data-versandkosten=" in html
    assert "data-gratis-ab=" in html


def test_neu_produktkarte_traegt_warenkorb_daten(client):
    html = client.get("/neu").text
    assert "data-neu-add" in html
    assert 'data-product-name="Olivenöl 750ml"' in html
