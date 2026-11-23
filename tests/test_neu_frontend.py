"""Neues Kunden-Frontend unter /neu (parallel zur bestehenden Seite)."""

import re
from html import unescape

import pytest

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


# --- alle Seiten erreichbar ---

NEU_SEITEN = [
    "/neu",
    "/neu/ueber-das-oel",
    "/neu/warenkorb",
    "/neu/checkout",
    "/neu/bestaetigung",
    "/neu/impressum",
    "/neu/datenschutz",
    "/neu/agb",
]


@pytest.mark.parametrize("pfad", NEU_SEITEN)
def test_neu_seite_erreichbar_und_gesperrt(client, pfad):
    response = client.get(pfad)
    assert response.status_code == 200
    assert 'content="noindex, nofollow"' in response.text


@pytest.mark.parametrize("pfad", NEU_SEITEN)
def test_neu_seiten_verlinken_nur_ins_neue_frontend(client, pfad):
    """Kein interner Link darf aus /neu zurück auf die alte Fassung führen."""
    html = client.get(pfad).text
    ziele = re.findall(r'href="(/[^"]*)"', html)
    fremd = [z for z in ziele if not z.startswith(("/neu", "/static/"))]
    assert fremd == []


# --- gleicher Inhalt ---


def _sichtbarer_text(html: str) -> str:
    """Text innerhalb von <main>, ohne Tags/Skripte, Leerraum normalisiert."""
    haupt = html[html.index("<main") : html.index("</main>")]
    haupt = re.sub(r"<script.*?</script>", " ", haupt, flags=re.S)
    haupt = re.sub(r"<[^>]+>", " ", haupt)
    return " ".join(unescape(haupt).split())


@pytest.mark.parametrize("seite", ["impressum", "datenschutz", "agb"])
def test_rechtstexte_sind_in_beiden_fassungen_wortgleich(client, seite):
    alt = _sichtbarer_text(client.get(f"/{seite}").text)
    neu = _sichtbarer_text(client.get(f"/neu/{seite}").text)
    assert neu == alt


def test_ueber_das_oel_enthaelt_alle_absaetze_der_alten_seite(client):
    alt_html = client.get("/ueber-das-oel").text
    alt_html = alt_html[alt_html.index("<main") : alt_html.index("</main>")]
    neu = _sichtbarer_text(client.get("/neu/ueber-das-oel").text)
    treffer = re.findall(
        r"<(p|td|blockquote|h[123])\b[^>]*>(.*?)</\1>", alt_html, flags=re.S
    )
    assert len(treffer) > 20
    for _tag, absatz in treffer:
        text = " ".join(unescape(re.sub(r"<[^>]+>", " ", absatz)).split())
        assert text in neu, text


def test_kasse_neu_hat_alle_formularfelder_der_alten_kasse(client):
    def felder(html: str) -> list[str]:
        formular = html[html.index("<form") : html.index("</form>")]
        return sorted(set(re.findall(r'name="([a-z_]+)"', formular)))

    alt = felder(client.get("/checkout").text)
    neu = felder(client.get("/neu/checkout").text)
    assert neu == sorted([*alt, "variante"])


# --- Bestellstrecke bleibt in der gewählten Fassung ---


def _bestellung(csrf_token, **extra):
    return {
        "vorname": "Anna",
        "nachname": "Muster",
        "email": "anna@example.com",
        "strasse": "Hauptstrasse",
        "plz": "4600",
        "ort": "Olten",
        "versandart": "versand",
        "zahlungsart": "rechnung",
        "cart_data": '[{"produkt_id": 1, "menge": 2}]',
        "csrf_token": csrf_token,
        **extra,
    }


def test_bestellung_aus_neu_zeigt_neue_bestaetigung(client, csrf_token):
    response = client.post("/bestellen", data=_bestellung(csrf_token, variante="neu"))
    assert response.status_code == 200
    assert "Vielen Dank!" in response.text
    assert 'href="/neu"' in response.text
    assert "noindex" in response.text


def test_bestellung_ohne_variante_zeigt_alte_bestaetigung(client, csrf_token):
    response = client.post("/bestellen", data=_bestellung(csrf_token))
    assert response.status_code == 200
    assert "noindex" not in response.text


def test_unbekannte_variante_faellt_auf_alte_fassung_zurueck(client, csrf_token):
    daten = _bestellung(csrf_token, variante="https://boese.example/")
    response = client.post("/bestellen", data=daten)
    assert response.status_code == 200
    assert "noindex" not in response.text
    assert "boese.example" not in response.text


@pytest.mark.parametrize(
    ("praefix", "erwartet"), [("", "/bestaetigung"), ("/neu", "/neu/bestaetigung")]
)
def test_stripe_ruecksprung_je_variante(monkeypatch, praefix, erwartet):
    from app.services import stripe_service

    aufruf = {}
    monkeypatch.setattr(
        stripe_service.stripe.checkout.Session,
        "create",
        lambda **kw: aufruf.update(kw),
    )
    stripe_service.erstelle_checkout_session(
        positionen=[{"name": "Öl", "einzelpreis_chf": 18.0, "menge": 1}],
        versandkosten=0,
        bestell_id=1,
        url_praefix=praefix,
    )
    basis = settings.base_url
    assert aufruf["success_url"] == (
        f"{basis}{erwartet}?session_id={{CHECKOUT_SESSION_ID}}"
    )
    assert aufruf["cancel_url"] == f"{basis}{praefix}/checkout"


def test_abholung_bar_aus_neu_zeigt_neue_bestaetigung(client, csrf_token):
    daten = _bestellung(
        csrf_token, variante="neu", versandart="abholung", zahlungsart="abholung_bar"
    )
    response = client.post("/bestellen", data=daten)
    assert response.status_code == 200
    assert "Nadine &amp; Sandro" in response.text or "Nadine & Sandro" in response.text
    assert "noindex" in response.text


@pytest.mark.parametrize(("variante", "erwartet"), [("", ""), ("neu", "/neu")])
def test_bestellen_reicht_variante_an_stripe_weiter(
    client, csrf_token, monkeypatch, variante, erwartet
):
    from types import SimpleNamespace

    aufruf = {}

    def fake_session(**kw):
        aufruf.update(kw)
        return SimpleNamespace(id="cs_test_1", url="https://checkout.stripe.com/c/x")

    monkeypatch.setattr(
        "app.services.stripe_service.erstelle_checkout_session", fake_session
    )
    daten = _bestellung(csrf_token, zahlungsart="stripe", variante=variante)
    response = client.post("/bestellen", data=daten, follow_redirects=False)
    assert response.status_code == 303
    assert aufruf["url_praefix"] == erwartet


def test_neu_startseite_zeigt_aktionspreis(client):
    from app.database import get_db

    conn = get_db()
    conn.execute(
        "UPDATE produkte SET aktionspreis_chf = 12.0, "
        "aktionstext = 'MHD 09/2026' WHERE id = 2"
    )
    conn.commit()
    conn.close()
    html = client.get("/neu").text
    assert "RABATT" in html
    assert "MHD 09/2026" in html
    assert "CHF 12.00" in html
    assert "CHF 18.00" in html  # Streichpreis
    karte = html[html.index('data-product-id="2"') :][:400]
    assert 'data-product-price="12.0"' in karte
    assert 'data-product-aktion="1"' in karte


def test_neu_startseite_ohne_aktion_kein_badge(client):
    assert "RABATT" not in client.get("/neu").text


# --- Inhalt nur von der bestehenden Seite ---


def _textstuecke(html: str) -> list[str]:
    haupt = html[html.index("<main") : html.index("</main>")]
    haupt = re.sub(r"<script.*?</script>", " ", haupt, flags=re.S)
    stuecke = [" ".join(unescape(s).split()) for s in re.split(r"<[^>]+>", haupt)]
    return [s for s in stuecke if s]


def test_startseite_neu_verwendet_nur_texte_der_bestehenden_seite(client):
    """Jeder sichtbare Text der neuen Startseite steht wörtlich auf der alten Seite."""
    quelle = " ".join(
        " ".join(unescape(re.sub(r"<[^>]+>", " ", client.get(pfad).text)).split())
        for pfad in ["/", "/ueber-das-oel"]
    ).lower()
    bedienung = {"−", "+", "1"}  # Mengenwahl
    fremd = [
        s
        for s in _textstuecke(client.get("/neu").text)
        if s not in bedienung and s.lower() not in quelle
    ]
    assert fremd == []
