from app.models import BestellungInput, KundeInput, Produkt, WarenkorbItem


def test_produkt_from_db_row():
    row = {
        "id": 1,
        "name": "Olivenöl 250ml",
        "menge_ml": 250,
        "preis_chf": 8.0,
        "beschreibung": "Bio",
        "bild_pfad": "bild.jpg",
        "aktiv": 1,
    }
    produkt = Produkt(**row)
    assert produkt.preis_chf == 8.0
    assert produkt.aktiv is True


def test_bestellung_input_minimal():
    data = BestellungInput(
        kunde=KundeInput(
            vorname="Max",
            nachname="Muster",
            email="max@example.com",
            strasse="Musterstr. 1",
            plz="4600",
            ort="Olten",
        ),
        items=[WarenkorbItem(produkt_id=1, menge=2)],
        versandart="versand",
        zahlungsart="stripe",
    )
    assert len(data.items) == 1
    assert data.kommentar == ""


def test_seed_data_exists(db):
    rows = db.execute("SELECT * FROM produkte").fetchall()
    assert len(rows) == 3
    assert dict(rows[0])["preis_chf"] == 8.0
