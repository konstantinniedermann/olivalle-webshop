import pytest

from app.models import WarenkorbItem
from app.services.bestell_service import berechne_total, berechne_versandkosten


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
