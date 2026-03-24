from unittest.mock import MagicMock, patch

from app.services.stripe_service import erstelle_checkout_session


@patch("app.services.stripe_service.stripe")
def test_erstelle_checkout_session(mock_stripe):
    mock_stripe.checkout.Session.create.return_value = MagicMock(
        id="cs_test_123", url="https://checkout.stripe.com/test"
    )
    session = erstelle_checkout_session(
        positionen=[
            {"produkt_id": 1, "menge": 2, "einzelpreis_chf": 8.0, "name": "Olivenöl 250ml"},
        ],
        versandkosten=9.90,
        bestell_id=1,
    )
    assert session.url == "https://checkout.stripe.com/test"
    mock_stripe.checkout.Session.create.assert_called_once()
    call_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
    assert len(call_kwargs["line_items"]) == 2  # 1 Produkt + Versand
