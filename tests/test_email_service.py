from unittest.mock import patch

from app.services.email_service import sende_bestellbestaetigung


@patch("app.services.email_service.resend.Emails.send")
def test_sende_bestellbestaetigung(mock_send):
    mock_send.return_value = {"id": "email_123"}
    result = sende_bestellbestaetigung(
        empfaenger="max@test.ch",
        bestell_id=1,
        kunde={"vorname": "Max", "nachname": "Muster"},
        positionen=[{"name": "Olivenöl 250ml", "menge": 2, "einzelpreis_chf": 8.0}],
        versandkosten=9.90,
        total=25.90,
    )
    assert result is not None
    mock_send.assert_called_once()
    call_kwargs = mock_send.call_args.kwargs
    assert call_kwargs["to"] == ["max@test.ch"]
    assert "Bestellbestätigung" in call_kwargs["subject"]
