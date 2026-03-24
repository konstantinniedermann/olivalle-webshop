import stripe
from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.database import get_db

router = APIRouter()


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.stripe_webhook_secret
        )
    except (ValueError, stripe.SignatureVerificationError) as err:
        raise HTTPException(400, "Ungültige Webhook-Signatur") from err

    if event.type == "checkout.session.completed":
        session = event.data.object
        conn = get_db()
        try:
            conn.execute(
                "UPDATE bestellungen SET status = 'bezahlt' "
                "WHERE stripe_session_id = ?",
                (session.id,),
            )
            conn.commit()
            # TODO (Task 8): E-Mail senden
            # TODO (Task 9): QR-Rechnung generieren falls nötig
        finally:
            conn.close()

    return {"status": "ok"}
