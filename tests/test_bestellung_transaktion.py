"""Issue #169: Ein Bestellvorgang = eine Transaktion.

Kunde + Bestellung + Positionen + Session-ID werden atomar committet.
Ein Fehler (z.B. Stripe-Session-Erstellung) rollt alles zurück — keine
Waisen (Kunde ohne Bestellung, Bestellung ohne Session-ID).
"""

import json
from unittest.mock import MagicMock

import pytest

from app.database import get_db
from tests.conftest import _checkout_csrf

_KUNDE = {
    "vorname": "Rollback",
    "nachname": "Test",
    "email": "rollback@test.ch",
    "strasse": "Teststr 1",
    "plz": "4600",
    "ort": "Olten",
}


def _post_stripe_bestellung(client, csrf):
    return client.post(
        "/bestellen",
        data={
            **_KUNDE,
            "versandart": "versand",
            "zahlungsart": "stripe",
            "cart_data": json.dumps([{"produkt_id": 1, "menge": 2}]),
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )


def test_stripe_fehler_rollt_kunde_und_bestellung_zurueck(client, monkeypatch):
    def boom(**kwargs):
        raise RuntimeError("Stripe nicht erreichbar")

    monkeypatch.setattr("app.services.stripe_service.erstelle_checkout_session", boom)
    csrf = _checkout_csrf(client)

    with pytest.raises(RuntimeError):
        _post_stripe_bestellung(client, csrf)

    conn = get_db()
    try:
        kunden = conn.execute("SELECT COUNT(*) c FROM kunden").fetchone()["c"]
        best = conn.execute("SELECT COUNT(*) c FROM bestellungen").fetchone()["c"]
    finally:
        conn.close()
    assert kunden == 0, "Kunde darf bei Stripe-Fehler nicht persistiert werden"
    assert best == 0, "Bestellung darf bei Stripe-Fehler nicht persistiert werden"


def test_erfolgreiche_stripe_bestellung_persistiert_atomar(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.stripe_service.erstelle_checkout_session",
        lambda **kw: MagicMock(id="cs_test_169", url="https://checkout.stripe.com/x"),
    )
    csrf = _checkout_csrf(client)

    resp = _post_stripe_bestellung(client, csrf)
    assert resp.status_code == 303

    conn = get_db()
    try:
        row = conn.execute("SELECT stripe_session_id FROM bestellungen").fetchone()
        kunden = conn.execute("SELECT COUNT(*) c FROM kunden").fetchone()["c"]
    finally:
        conn.close()
    assert kunden == 1
    assert row is not None
    # Session-ID im selben Commit wie Kunde/Bestellung persistiert
    assert row["stripe_session_id"] == "cs_test_169"
