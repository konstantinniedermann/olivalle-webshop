from unittest.mock import MagicMock, patch

from app.services.email_service import sende_bestellbestaetigung


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
    svg_bytes = b"<svg>test</svg>"
    result = sende_bestellbestaetigung(
        empfaenger="max@test.ch",
        bestell_id=2,
        kunde={"vorname": "Max", "nachname": "Muster"},
        positionen=[{"name": "Olivenöl 750ml", "menge": 1, "einzelpreis_chf": 18.0}],
        versandkosten=0.0,
        total=18.0,
        anhang=svg_bytes,
    )
    assert result is not None
    call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
    assert call_kwargs["attachment"][0]["name"] == "rechnung-2.svg"
    assert "content" in call_kwargs["attachment"][0]
