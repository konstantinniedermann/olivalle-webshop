from datetime import date

import pytest

from app.models import WarenkorbItem
from app.services.bestell_service import (
    berechne_total,
    berechne_versandkosten,
    rabattfaehiger_subtotal,
)


def test_versandkosten_unter_100():
    assert berechne_versandkosten(99.99) == 9.90


def test_versandkosten_ab_100_gratis():
    assert berechne_versandkosten(100.0) == 0.0


def test_versandkosten_abholung():
    assert berechne_versandkosten(50.0, versandart="abholung") == 0.0


def test_berechne_total(db):
    items = [
        WarenkorbItem(produkt_id=1, menge=2),  # 2x CHF 8 = 16
        WarenkorbItem(produkt_id=2, menge=1),  # 1x CHF 18 = 18
    ]
    total, positionen = berechne_total(db, items)
    assert total == 34.0
    assert len(positionen) == 2


def test_berechne_total_ungueltige_produkt_id(db):
    items = [WarenkorbItem(produkt_id=999, menge=1)]
    with pytest.raises(ValueError, match="Produkt 999 nicht gefunden"):
        berechne_total(db, items)


def test_berechne_total_mit_aktionspreis(db):
    db.execute(
        "UPDATE produkte SET aktionspreis_chf = 12.0, aktion_von = '2026-06-01', "
        "aktion_bis = '2026-06-30' WHERE id = 2"
    )
    db.commit()
    items = [WarenkorbItem(produkt_id=2, menge=1)]  # statt 18 jetzt 12
    total, positionen = berechne_total(db, items, heute=date(2026, 6, 23))
    assert total == 12.0
    assert positionen[0]["einzelpreis_chf"] == 12.0
    assert positionen[0]["ist_aktion"] is True
    assert positionen[0]["original_preis_chf"] == 18.0


def test_berechne_total_aktion_abgelaufen_normalpreis(db):
    db.execute(
        "UPDATE produkte SET aktionspreis_chf = 12.0, aktion_bis = '2026-06-22' "
        "WHERE id = 2"
    )
    db.commit()
    items = [WarenkorbItem(produkt_id=2, menge=1)]
    total, positionen = berechne_total(db, items, heute=date(2026, 6, 23))
    assert total == 18.0
    assert positionen[0]["ist_aktion"] is False


def test_rabattfaehiger_subtotal_nur_nicht_aktion():
    positionen = [
        {"einzelpreis_chf": 8.0, "menge": 2, "ist_aktion": False},  # 16
        {"einzelpreis_chf": 12.0, "menge": 1, "ist_aktion": True},  # ausgeschlossen
    ]
    assert rabattfaehiger_subtotal(positionen) == 16.0


def test_rabattfaehiger_subtotal_reine_aktion_null():
    positionen = [{"einzelpreis_chf": 12.0, "menge": 1, "ist_aktion": True}]
    assert rabattfaehiger_subtotal(positionen) == 0.0
