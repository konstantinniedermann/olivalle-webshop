"""Tests für Bezahlung bei Abholung und Stakeholder-Benachrichtigung."""

from unittest.mock import MagicMock, patch

from app.services.email_service import sende_stakeholder_benachrichtigung


@patch("app.services.email_service.brevo_client")
def test_stakeholder_mail_wird_gesendet(mock_client):
    """Stakeholder-Mail enthält Bestelldaten und wird an SH-Adresse geschickt."""
    mock_client.transactional_emails.send_transac_email.return_value = MagicMock(
        message_id="sh_1"
    )
    sende_stakeholder_benachrichtigung(
        bestell_id=42,
        kunde={"vorname": "Anna", "nachname": "Test", "email": "anna@test.ch"},
        positionen=[{"name": "Olivenöl 750ml", "menge": 2, "einzelpreis_chf": 18.0}],
        versandkosten=0.0,
        total=36.0,
        zahlungsart="abholung_bar",
        versandart="abholung",
    )
    mock_client.transactional_emails.send_transac_email.assert_called_once()
    call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
    assert call_kwargs["to"][0]["email"] == "olivalle.olten@outlook.com"
    assert "#42" in call_kwargs["subject"]


@patch("app.services.email_service.brevo_client")
def test_stakeholder_mail_stripe(mock_client):
    """Stakeholder-Mail funktioniert auch für Stripe-Bestellungen."""
    mock_client.transactional_emails.send_transac_email.return_value = MagicMock(
        message_id="sh_2"
    )
    sende_stakeholder_benachrichtigung(
        bestell_id=43,
        kunde={"vorname": "Beat", "nachname": "Stripe", "email": "beat@test.ch"},
        positionen=[{"name": "Olivenöl 250ml", "menge": 1, "einzelpreis_chf": 8.0}],
        versandkosten=9.90,
        total=17.90,
        zahlungsart="stripe",
        versandart="versand",
    )
    mock_client.transactional_emails.send_transac_email.assert_called_once()
    call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
    assert call_kwargs["to"][0]["email"] == "olivalle.olten@outlook.com"
