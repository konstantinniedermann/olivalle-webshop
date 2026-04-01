from unittest.mock import MagicMock, patch

from app.services.email_service import sende_bestellbestaetigung, sende_status_email


@patch("app.services.email_service.brevo_client")
def test_sende_bestellbestaetigung(mock_client):
    mock_client.transactional_emails.send_transac_email.return_value = MagicMock(
        message_id="email_123"
    )
    result = sende_bestellbestaetigung(
        empfaenger="max@test.ch",
        bestell_id=1,
        kunde={"vorname": "Max", "nachname": "Muster"},
        positionen=[{"name": "Olivenöl 250ml", "menge": 2, "einzelpreis_chf": 8.0}],
        versandkosten=9.90,
        total=25.90,
    )
    assert result is not None
    mock_client.transactional_emails.send_transac_email.assert_called_once()
    call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
    assert call_kwargs["to"][0]["email"] == "max@test.ch"
    assert "Bestellbestätigung" in call_kwargs["subject"]


@patch("app.services.email_service.brevo_client")
def test_sende_bestellbestaetigung_mit_anhang(mock_client):
    mock_client.transactional_emails.send_transac_email.return_value = MagicMock(
        message_id="email_456"
    )
    pdf_bytes = b"%PDF-fake"
    result = sende_bestellbestaetigung(
        empfaenger="max@test.ch",
        bestell_id=2,
        kunde={"vorname": "Max", "nachname": "Muster"},
        positionen=[{"name": "Olivenöl 750ml", "menge": 1, "einzelpreis_chf": 18.0}],
        versandkosten=0.0,
        total=18.0,
        anhang=pdf_bytes,
    )
    assert result is not None
    call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
    assert call_kwargs["attachment"][0]["name"] == "rechnung-2.pdf"
    assert "content" in call_kwargs["attachment"][0]


class TestSendeStatusEmail:
    """Tests für sende_status_email Dispatch-Logik."""

    def _make_bestellung(self, db, zahlungsart="rechnung", versandart="versand"):
        """Hilfsfunktion: Kunde + Bestellung in DB anlegen."""
        db.execute(
            "INSERT INTO kunden (id, vorname, nachname, email, telefon, strasse, plz, ort) "
            "VALUES (1, 'Max', 'Muster', 'max@test.ch', '', 'Teststr 1', '8000', 'Zürich')"
        )
        db.execute(
            "INSERT INTO bestellungen (id, kunde_id, status, zahlungsart, versandart, "
            "versandkosten_chf, total_chf) "
            "VALUES (1, 1, 'neu', ?, ?, 0, 50.00)",
            (zahlungsart, versandart),
        )
        db.commit()

    def test_bezahlt_rechnung_sendet_email(self, db):
        """bezahlt + rechnung → Zahlungseingangsbestätigung."""
        self._make_bestellung(db, zahlungsart="rechnung")
        with patch("app.services.email_service.brevo_client") as mock_client:
            mock_client.transactional_emails.send_transac_email.return_value = MagicMock(
                message_id="s1"
            )
            sende_status_email(bestellung_id=1, neuer_status="bezahlt", conn=db)
            mock_client.transactional_emails.send_transac_email.assert_called_once()
            call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
            assert call_kwargs["to"][0]["email"] == "max@test.ch"
            assert "Zahlungseingang" in call_kwargs["subject"]

    def test_bezahlt_stripe_keine_email(self, db):
        """bezahlt + stripe → keine E-Mail (Stripe schickt eigene)."""
        self._make_bestellung(db, zahlungsart="stripe")
        with patch("app.services.email_service.brevo_client") as mock_client:
            sende_status_email(bestellung_id=1, neuer_status="bezahlt", conn=db)
            mock_client.transactional_emails.send_transac_email.assert_not_called()

    def test_versendet_versand_sendet_email(self, db):
        """versendet + versand → Versandbestätigung."""
        self._make_bestellung(db, versandart="versand")
        with patch("app.services.email_service.brevo_client") as mock_client:
            mock_client.transactional_emails.send_transac_email.return_value = MagicMock(
                message_id="s2"
            )
            sende_status_email(bestellung_id=1, neuer_status="versendet", conn=db)
            mock_client.transactional_emails.send_transac_email.assert_called_once()
            call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
            assert "unterwegs" in call_kwargs["subject"]

    def test_versendet_abholung_keine_email(self, db):
        """versendet + abholung → keine E-Mail."""
        self._make_bestellung(db, versandart="abholung")
        with patch("app.services.email_service.brevo_client") as mock_client:
            sende_status_email(bestellung_id=1, neuer_status="versendet", conn=db)
            mock_client.transactional_emails.send_transac_email.assert_not_called()

    def test_abholbereit_abholung_sendet_email(self, db):
        """abholbereit + abholung → Abholbenachrichtigung."""
        self._make_bestellung(db, versandart="abholung")
        with patch("app.services.email_service.brevo_client") as mock_client:
            mock_client.transactional_emails.send_transac_email.return_value = MagicMock(
                message_id="s3"
            )
            sende_status_email(bestellung_id=1, neuer_status="abholbereit", conn=db)
            mock_client.transactional_emails.send_transac_email.assert_called_once()
            call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
            assert "abholbereit" in call_kwargs["subject"]

    def test_abholbereit_versand_keine_email(self, db):
        """abholbereit + versand → keine E-Mail."""
        self._make_bestellung(db, versandart="versand")
        with patch("app.services.email_service.brevo_client") as mock_client:
            sende_status_email(bestellung_id=1, neuer_status="abholbereit", conn=db)
            mock_client.transactional_emails.send_transac_email.assert_not_called()

    def test_storniert_keine_email(self, db):
        """storniert → keine E-Mail."""
        self._make_bestellung(db)
        with patch("app.services.email_service.brevo_client") as mock_client:
            sende_status_email(bestellung_id=1, neuer_status="storniert", conn=db)
            mock_client.transactional_emails.send_transac_email.assert_not_called()

    def test_bezahlt_abholung_bar_sendet_email(self, db):
        """bezahlt + abholung_bar → Zahlungseingangsbestätigung (Admin hat Bar-Zahlung bestätigt)."""
        self._make_bestellung(db, zahlungsart="abholung_bar", versandart="abholung")
        with patch("app.services.email_service.brevo_client") as mock_client:
            mock_client.transactional_emails.send_transac_email.return_value = MagicMock(
                message_id="s_bar"
            )
            sende_status_email(bestellung_id=1, neuer_status="bezahlt", conn=db)
            mock_client.transactional_emails.send_transac_email.assert_called_once()
            call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
            assert "Zahlungseingang" in call_kwargs["subject"]
