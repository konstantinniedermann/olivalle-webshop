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
