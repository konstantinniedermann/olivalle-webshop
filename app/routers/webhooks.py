
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
            # Atomarer Doppelt-Webhook-Schutz: nur EIN paralleler Aufruf
            # bekommt rowcount == 1, alle weiteren werden ignoriert.
            cur = conn.execute(
                "UPDATE bestellungen SET status = 'bezahlt' "
                "WHERE stripe_session_id = ? AND status = 'neu'",
                (session.id,),
            )
            conn.commit()
            if cur.rowcount != 1:
                return {"status": "ok"}
            # Bestelldetails für E-Mail laden
            bestellung = conn.execute(
                "SELECT b.*, k.vorname, k.nachname, k.email "
                "FROM bestellungen b JOIN kunden k ON b.kunde_id = k.id "
                "WHERE b.stripe_session_id = ?",
                (session.id,),
            ).fetchone()
            if bestellung:
                best = dict(bestellung)

                # Log status change
                from app.repositories.admin_repo import log_eintrag_schreiben

                log_eintrag_schreiben(
                    conn,
                    admin_label="system",
                    aktion="status_geaendert",
                    details='{"von": "neu", "nach": "bezahlt"}',
                    bestellung_id=best["id"],
                )

                positionen = conn.execute(
                    "SELECT bp.*, p.name FROM bestellpositionen bp "
                    "JOIN produkte p ON bp.produkt_id = p.id "
                    "WHERE bp.bestellung_id = ?",
                    (best["id"],),
                ).fetchall()
                # Rabattcode-Name laden falls vorhanden
                rabattcode_name = ""
                if best.get("rabattcode_id"):
                    rc_row = conn.execute(
                        "SELECT code FROM rabattcodes WHERE id = ?",
                        (best["rabattcode_id"],),
                    ).fetchone()
                    if rc_row:
                        rabattcode_name = rc_row["code"]

                from app.services.email_service import sende_bestellbestaetigung
                sende_bestellbestaetigung(
                    empfaenger=best["email"],
                    bestell_id=best["id"],
                    kunde={"vorname": best["vorname"], "nachname": best["nachname"]},
                    positionen=[dict(p) for p in positionen],
                    versandkosten=best["versandkosten_chf"],
                    total=best["total_chf"],
                    conn=conn,
                    rabattbetrag=best.get("rabattbetrag_chf", 0),
                    rabattcode=rabattcode_name,
                )
                from app.services.email_service import (
                    sende_stakeholder_benachrichtigung,
                )
                sende_stakeholder_benachrichtigung(
                    bestell_id=best["id"],
                    kunde={
                        "vorname": best["vorname"],
                        "nachname": best["nachname"],
                        "email": best["email"],
                    },
                    positionen=[dict(p) for p in positionen],
                    versandkosten=best["versandkosten_chf"],
                    total=best["total_chf"],
                    zahlungsart=best["zahlungsart"],
                    versandart=best["versandart"],
                    conn=conn,
                    rabattbetrag=best.get("rabattbetrag_chf", 0),
                    rabattcode=rabattcode_name,
                )
            # TODO (Task 9): QR-Rechnung generieren falls nötig
        finally:
            conn.close()

    if event.type in (
        "checkout.session.expired",
        "checkout.session.async_payment_failed",
    ):
        session = event.data.object
        conn = get_db()
        try:
            cur = conn.execute(
                "UPDATE bestellungen SET status = 'storniert' "
                "WHERE stripe_session_id = ? AND status = 'neu'",
                (session.id,),
            )
            conn.commit()
            if cur.rowcount == 1:
                row = conn.execute(
                    "SELECT id FROM bestellungen WHERE stripe_session_id = ?",
                    (session.id,),
                ).fetchone()
                bestell_id = dict(row)["id"]

                import json

                from app.repositories.admin_repo import log_eintrag_schreiben

                grund = (
                    "Stripe Checkout abgebrochen oder abgelaufen"
                    if event.type == "checkout.session.expired"
                    else "Zahlung fehlgeschlagen"
                )
                log_eintrag_schreiben(
                    conn,
                    admin_label="system",
                    aktion="status_geaendert",
                    details=json.dumps({"von": "neu", "nach": "storniert", "grund": grund}),
                    bestellung_id=bestell_id,
                )
        finally:
            conn.close()

    return {"status": "ok"}
