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
            # Bestelldetails für E-Mail laden
            bestellung = conn.execute(
                "SELECT b.*, k.vorname, k.nachname, k.email "
                "FROM bestellungen b JOIN kunden k ON b.kunde_id = k.id "
                "WHERE b.stripe_session_id = ?",
                (session.id,),
            ).fetchone()
            if bestellung:
                best = dict(bestellung)
                positionen = conn.execute(
                    "SELECT bp.*, p.name FROM bestellpositionen bp "
                    "JOIN produkte p ON bp.produkt_id = p.id "
                    "WHERE bp.bestellung_id = ?",
                    (best["id"],),
                ).fetchall()
                from app.services.email_service import sende_bestellbestaetigung
                sende_bestellbestaetigung(
                    empfaenger=best["email"],
                    bestell_id=best["id"],
                    kunde={"vorname": best["vorname"], "nachname": best["nachname"]},
                    positionen=[dict(p) for p in positionen],
                    versandkosten=best["versandkosten_chf"],
                    total=best["total_chf"],
                )
            # TODO (Task 9): QR-Rechnung generieren falls nötig
        finally:
            conn.close()

    return {"status": "ok"}
