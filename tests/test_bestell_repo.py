from app.models import KundeInput
from app.repositories.bestell_repo import bestellung_anlegen, kunde_anlegen


def test_kunde_anlegen(db):
    kunde = KundeInput(
        vorname="Max", nachname="Muster", email="max@test.ch",
        strasse="Musterstr. 1", plz="4600", ort="Olten",
    )
    kunde_id = kunde_anlegen(db, kunde)
    assert kunde_id == 1


def test_bestellung_anlegen(db):
    kunde = KundeInput(
        vorname="Max", nachname="Muster", email="max@test.ch",
        strasse="Musterstr. 1", plz="4600", ort="Olten",
    )
    kunde_id = kunde_anlegen(db, kunde)
    positionen = [
        {"produkt_id": 1, "menge": 2, "einzelpreis_chf": 8.0},
    ]
    bestell_id = bestellung_anlegen(
        db, kunde_id=kunde_id, positionen=positionen,
        zahlungsart="stripe", versandart="versand",
        versandkosten=9.90, total=25.90, kommentar="",
    )
    assert bestell_id == 1
    row = db.execute(
        "SELECT * FROM bestellungen WHERE id = ?", (bestell_id,)
    ).fetchone()
    assert dict(row)["total_chf"] == 25.90
