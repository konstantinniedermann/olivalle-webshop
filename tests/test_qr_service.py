from app.services.qr_service import generiere_qr_rechnung


def test_generiere_qr_rechnung(monkeypatch):
    # QR-Settings für Tests setzen
    monkeypatch.setattr("app.config.settings.qr_iban", "CH5604835012345678009")
    monkeypatch.setattr("app.config.settings.qr_name", "Test GmbH")
    monkeypatch.setattr("app.config.settings.qr_address", "Teststr. 1")
    monkeypatch.setattr("app.config.settings.qr_zip", "3000")
    monkeypatch.setattr("app.config.settings.qr_city", "Bern")

    pdf_bytes = generiere_qr_rechnung(
        betrag=25.90,
        bestell_id=1,
        kunde_name="Max Muster",
        kunde_adresse="Musterstr. 1",
        kunde_plz="4600",
        kunde_ort="Olten",
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 100
    assert pdf_bytes[:5] == b"%PDF-"


def test_qr_rechnung_mit_hausnummer_in_nutzlast(monkeypatch):
    """Wenn kunde_hausnummer gesetzt ist, landet sie in QR-Zeile 24 (Index 23)."""
    from qrbill import QRBill

    monkeypatch.setattr("app.config.settings.qr_iban", "CH5604835012345678009")
    monkeypatch.setattr("app.config.settings.qr_name", "Test GmbH")
    monkeypatch.setattr("app.config.settings.qr_address", "Teststr. 1")
    monkeypatch.setattr("app.config.settings.qr_zip", "3000")
    monkeypatch.setattr("app.config.settings.qr_city", "Bern")

    bill = QRBill(
        account="CH5604835012345678009",
        creditor={
            "name": "Test GmbH", "street": "Teststr.", "house_num": "1",
            "pcode": "3000", "city": "Bern", "country": "CH",
        },
        debtor={
            "name": "Klara Tester", "street": "Musterstrasse", "house_num": "42",
            "pcode": "8001", "city": "Zürich", "country": "CH",
        },
        amount="25.90", currency="CHF",
    )
    zeilen = bill.qr_data().split("\r\n")
    # Zeile 23 = Strasse (Index 22), Zeile 24 = Hausnummer (Index 23)
    assert zeilen[22] == "Musterstrasse"
    assert zeilen[23] == "42"


def test_generiere_qr_rechnung_mit_hausnummer(monkeypatch):
    """generiere_qr_rechnung akzeptiert kunde_hausnummer und gibt gültiges PDF zurück."""
    monkeypatch.setattr("app.config.settings.qr_iban", "CH5604835012345678009")
    monkeypatch.setattr("app.config.settings.qr_name", "Test GmbH")
    monkeypatch.setattr("app.config.settings.qr_address", "Teststr. 1")
    monkeypatch.setattr("app.config.settings.qr_zip", "3000")
    monkeypatch.setattr("app.config.settings.qr_city", "Bern")

    pdf_bytes = generiere_qr_rechnung(
        betrag=25.90, bestell_id=1,
        kunde_name="Klara Tester",
        kunde_adresse="Musterstrasse",
        kunde_hausnummer="42",
        kunde_plz="8001", kunde_ort="Zürich",
    )
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:5] == b"%PDF-"
