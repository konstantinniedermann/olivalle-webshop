from datetime import date

from fastapi import APIRouter, Request

from app.database import get_db
from app.repositories.produkt_repo import get_alle_produkte
from app.services.aktions_service import effektiver_preis
from app.templating import templates

router = APIRouter()


@router.get("/")
def startseite(request: Request):
    conn = get_db()
    try:
        produkte = get_alle_produkte(conn)
    finally:
        conn.close()
    heute = date.today()
    ansichten = []
    for p in produkte:
        ep = effektiver_preis(
            p.preis_chf, p.aktionspreis_chf, p.aktion_von, p.aktion_bis, heute
        )
        ansichten.append(
            {
                "id": p.id,
                "name": p.name,
                "beschreibung": p.beschreibung,
                "bild_pfad": p.bild_pfad,
                "preis": ep.preis,
                "ist_aktion": ep.ist_aktion,
                "original_preis": ep.original_preis,
                "prozent": ep.prozent,
                "aktionstext": p.aktionstext,
            }
        )
    return templates.TemplateResponse(
        request, "produkte.html", {"produkte": ansichten, "active_page": "produkte"}
    )
