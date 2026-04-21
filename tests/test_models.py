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


def test_kunde_input_mit_hausnummer():
    """KundeInput akzeptiert optionales Feld hausnummer."""
    from app.models import KundeInput

    kunde = KundeInput(
        vorname="Max",
        nachname="Muster",
        email="max@test.ch",
        strasse="Musterstrasse",
        hausnummer="42",
        plz="4600",
        ort="Olten",
    )
    assert kunde.hausnummer == "42"


def test_kunde_input_hausnummer_default_leer():
    """Ohne hausnummer ist der Default ein leerer String."""
    from app.models import KundeInput

    kunde = KundeInput(
        vorname="Max",
        nachname="Muster",
        email="max@test.ch",
        strasse="Musterstr. 1",
        plz="4600",
        ort="Olten",
    )
    assert kunde.hausnummer == ""


def test_kunde_input_hausnummer_max_length():
    """Hausnummer über 16 Zeichen wirft ValidationError (qrbill-Limit)."""
    from pydantic import ValidationError

    from app.models import KundeInput

    try:
        KundeInput(
            vorname="Max",
            nachname="Muster",
            email="max@test.ch",
            strasse="Musterstr.",
            hausnummer="x" * 17,
            plz="4600",
            ort="Olten",
        )
        raise AssertionError("ValidationError erwartet")
    except ValidationError:
        pass
