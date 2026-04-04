import stripe

from app.config import settings

stripe.api_key = settings.stripe_secret_key


def erstelle_checkout_session(
    positionen: list[dict],
    versandkosten: float,
    bestell_id: int,
    rabattbetrag: float = 0,
) -> stripe.checkout.Session:
    line_items = []
    for pos in positionen:
        line_items.append({
            "price_data": {
                "currency": "chf",
                "product_data": {"name": pos["name"]},
                "unit_amount": int(pos["einzelpreis_chf"] * 100),
            },
            "quantity": pos["menge"],
        })

    if versandkosten > 0:
        line_items.append({
            "price_data": {
                "currency": "chf",
                "product_data": {"name": "Versandkosten"},
                "unit_amount": int(versandkosten * 100),
            },
            "quantity": 1,
        })

    discounts = []
    if rabattbetrag > 0:
        coupon = stripe.Coupon.create(
            amount_off=int(rabattbetrag * 100),
            currency="chf",
            duration="once",
            name=f"Rabatt Bestellung #{bestell_id}",
        )
        discounts = [{"coupon": coupon.id}]

    session_params = {
        "payment_method_types": ["card", "twint"],
        "line_items": line_items,
        "mode": "payment",
        "success_url": f"{settings.base_url}/bestaetigung?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{settings.base_url}/checkout",
        "metadata": {"bestell_id": str(bestell_id)},
    }
    if discounts:
        session_params["discounts"] = discounts
    return stripe.checkout.Session.create(**session_params)
