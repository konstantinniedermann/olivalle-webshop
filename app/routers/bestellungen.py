import json

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.database import get_db
from app.models import KundeInput, WarenkorbItem
from app.repositories.bestell_repo import bestellung_anlegen, kunde_anlegen
from app.services.bestell_service import berechne_total, berechne_versandkosten
from app.templating import templates

router = APIRouter()


@router.get("/checkout")
def checkout_seite(request: Request):
    return templates.TemplateResponse(
        request, "checkout.html", {"csrf_token": "TODO"}
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
    csrf_token: str = Form(""),
):
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
        versandkosten = berechne_versandkosten(total, versandart)
        gesamt = total + versandkosten

        # Kunde + Bestellung speichern
        kunde_id = kunde_anlegen(conn, kunde_input)
        bestell_id = bestellung_anlegen(
            conn, kunde_id=kunde_id, positionen=positionen,
            zahlungsart=zahlungsart, versandart=versandart,
            versandkosten=versandkosten, total=gesamt,
            kommentar=kommentar,
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
            )
            conn.execute(
                "UPDATE bestellungen SET stripe_session_id = ? WHERE id = ?",
                (session.id, bestell_id),
            )
            conn.commit()
            return RedirectResponse(session.url, status_code=303)

        return templates.TemplateResponse(
            request, "bestaetigung.html",
            {"bestell_id": bestell_id, "zahlungsart": zahlungsart},
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
                    },
                )
        return templates.TemplateResponse(
            request, "bestaetigung.html",
            {"bestell_id": "?", "zahlungsart": "stripe"},
        )
    finally:
        conn.close()
