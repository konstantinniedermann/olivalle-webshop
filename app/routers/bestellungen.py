import json

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.config import settings
from app.csrf import generiere_csrf_token, validiere_csrf_token
from app.database import get_db
from app.models import KundeInput, WarenkorbItem
from app.repositories.bestell_repo import bestellung_anlegen, kunde_anlegen
from app.services.bestell_service import berechne_total, berechne_versandkosten
from app.services.email_service import (
    sende_bestellbestaetigung,
    sende_stakeholder_benachrichtigung,
)
from app.templating import templates

router = APIRouter()


@router.get("/checkout")
def checkout_seite(request: Request):
    csrf_token = generiere_csrf_token(settings.secret_key)
    return templates.TemplateResponse(
        request, "checkout.html", {"csrf_token": csrf_token, "active_page": "checkout"}
    )


@router.post("/bestellen")
def bestellen(
    request: Request,
    vorname: str = Form(),
    nachname: str = Form(),
    email: str = Form(),
    strasse: str = Form(),
    plz: str = Form(),
    ort: str = Form(),
    telefon: str = Form(""),
    versandart: str = Form(),
    zahlungsart: str = Form(),
    cart_data: str = Form(),
    kommentar: str = Form(""),
    rabattcode: str = Form(""),
    csrf_token: str = Form(""),
):
    if not validiere_csrf_token(csrf_token, settings.secret_key):
        raise HTTPException(403, "Ungültiges CSRF-Token")

    # Parse Warenkorb
    try:
        raw_items = json.loads(cart_data)
    except json.JSONDecodeError as err:
        raise HTTPException(400, "Ungültige Warenkorb-Daten") from err

    if not raw_items:
        raise HTTPException(400, "Warenkorb ist leer")

    items = [
        WarenkorbItem(produkt_id=i["produkt_id"], menge=i["menge"])
        for i in raw_items
    ]

    kunde_input = KundeInput(
        vorname=vorname, nachname=nachname, email=email,
        telefon=telefon, strasse=strasse, plz=plz, ort=ort,
    )

    conn = get_db()
    try:
        # Preise serverseitig validieren
        total, positionen = berechne_total(conn, items)

        # Rabattcode pruefen und anwenden
        rabattcode_id = None
        rabattbetrag = 0.0
        if rabattcode:
            from app.services.rabattcode_service import pruefe_rabattcode
            rc_result = pruefe_rabattcode(conn, rabattcode, email, total)
            if rc_result["gueltig"]:
                rabattcode_id = rc_result["rabattcode_id"]
                rabattbetrag = rc_result["rabattbetrag"]

        versandkosten = berechne_versandkosten(total, versandart)
        gesamt = total - rabattbetrag + versandkosten

        # Kunde + Bestellung speichern
        kunde_id = kunde_anlegen(conn, kunde_input)
        bestell_id = bestellung_anlegen(
            conn, kunde_id=kunde_id, positionen=positionen,
            zahlungsart=zahlungsart, versandart=versandart,
            versandkosten=versandkosten, total=gesamt,
            kommentar=kommentar,
            rabattcode_id=rabattcode_id,
            rabattbetrag_chf=rabattbetrag,
        )

        if rabattcode_id:
            from app.repositories.rabattcode_repo import einloesung_speichern
            einloesung_speichern(
                conn, rabattcode_id=rabattcode_id,
                email=email, bestellung_id=bestell_id,
            )

        if zahlungsart == "stripe":
            from app.services.stripe_service import erstelle_checkout_session
            # Produktnamen für Stripe holen
            for pos in positionen:
                row = conn.execute(
                    "SELECT name FROM produkte WHERE id = ?", (pos["produkt_id"],)
                ).fetchone()
                pos["name"] = row["name"]
            session = erstelle_checkout_session(
                positionen=positionen,
                versandkosten=versandkosten,
                bestell_id=bestell_id,
                rabattbetrag=rabattbetrag,
            )
            conn.execute(
                "UPDATE bestellungen SET stripe_session_id = ? WHERE id = ?",
                (session.id, bestell_id),
            )
            conn.commit()
            return RedirectResponse(session.url, status_code=303)

        if zahlungsart == "rechnung":
            from app.services.qr_service import generiere_qr_rechnung

            qr_pdf = generiere_qr_rechnung(
                betrag=gesamt,
                bestell_id=bestell_id,
                kunde_name=f"{kunde_input.vorname} {kunde_input.nachname}",
                kunde_adresse=kunde_input.strasse,
                kunde_plz=kunde_input.plz,
                kunde_ort=kunde_input.ort,
            )
            # Produktnamen für E-Mail holen
            for pos in positionen:
                row = conn.execute(
                    "SELECT name FROM produkte WHERE id = ?", (pos["produkt_id"],)
                ).fetchone()
                pos["name"] = row["name"]
            sende_bestellbestaetigung(
                empfaenger=kunde_input.email,
                bestell_id=bestell_id,
                kunde={
                    "vorname": kunde_input.vorname,
                    "nachname": kunde_input.nachname,
                },
                positionen=positionen,
                versandkosten=versandkosten,
                total=gesamt,
                anhang=qr_pdf,
                conn=conn,
                rabattbetrag=rabattbetrag,
                rabattcode=rabattcode.upper().strip() if rabattcode else "",
            )
            sende_stakeholder_benachrichtigung(
                bestell_id=bestell_id,
                kunde={
                    "vorname": kunde_input.vorname,
                    "nachname": kunde_input.nachname,
                    "email": kunde_input.email,
                },
                positionen=positionen,
                versandkosten=versandkosten,
                total=gesamt,
                zahlungsart=zahlungsart,
                versandart=versandart,
                conn=conn,
                rabattbetrag=rabattbetrag,
                rabattcode=rabattcode.upper().strip() if rabattcode else "",
            )

        if zahlungsart == "abholung_bar":
            if versandart != "abholung":
                raise HTTPException(400, "Bezahlung bei Abholung nur mit Abholung vor Ort möglich")
            # Produktnamen für E-Mail holen
            for pos in positionen:
                row = conn.execute(
                    "SELECT name FROM produkte WHERE id = ?", (pos["produkt_id"],)
                ).fetchone()
                pos["name"] = row["name"]
            sende_bestellbestaetigung(
                empfaenger=kunde_input.email,
                bestell_id=bestell_id,
                kunde={
                    "vorname": kunde_input.vorname,
                    "nachname": kunde_input.nachname,
                },
                positionen=positionen,
                versandkosten=versandkosten,
                total=gesamt,
                conn=conn,
                template_name="bestellbestaetigung_abholung_bar.html",
                rabattbetrag=rabattbetrag,
                rabattcode=rabattcode.upper().strip() if rabattcode else "",
            )
            sende_stakeholder_benachrichtigung(
                bestell_id=bestell_id,
                kunde={
                    "vorname": kunde_input.vorname,
                    "nachname": kunde_input.nachname,
                    "email": kunde_input.email,
                },
                positionen=positionen,
                versandkosten=versandkosten,
                total=gesamt,
                zahlungsart=zahlungsart,
                versandart=versandart,
                conn=conn,
                rabattbetrag=rabattbetrag,
                rabattcode=rabattcode.upper().strip() if rabattcode else "",
            )

        return templates.TemplateResponse(
            request,
            "bestaetigung.html",
            {
                "bestell_id": bestell_id,
                "zahlungsart": zahlungsart,
                "active_page": "bestaetigung",
            },
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    finally:
        conn.close()


@router.get("/bestaetigung")
def bestaetigung_seite(request: Request, session_id: str = ""):
    """GET-Endpoint für Stripe-Redirect-Rückkehr nach erfolgreicher Zahlung."""
    conn = get_db()
    try:
        if session_id:
            row = conn.execute(
                "SELECT id, zahlungsart FROM bestellungen WHERE stripe_session_id = ?",
                (session_id,),
            ).fetchone()
            if row:
                row_dict = dict(row)
                return templates.TemplateResponse(
                    request, "bestaetigung.html",
                    {
                        "bestell_id": row_dict["id"],
                        "zahlungsart": row_dict["zahlungsart"],
                        "active_page": "bestaetigung",
                    },
                )
        return templates.TemplateResponse(
            request, "bestaetigung.html",
            {"bestell_id": "?", "zahlungsart": "stripe", "active_page": "bestaetigung"},
        )
    finally:
        conn.close()
