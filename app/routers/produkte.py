from fastapi import APIRouter, Request

from app.database import get_db
from app.repositories.produkt_repo import get_alle_produkte
from app.templating import templates

router = APIRouter()


@router.get("/")
def startseite(request: Request):
    conn = get_db()
    try:
        produkte = get_alle_produkte(conn)
    finally:
        conn.close()
    return templates.TemplateResponse(
        request, "produkte.html", {"produkte": produkte, "active_page": "produkte"}
    )
