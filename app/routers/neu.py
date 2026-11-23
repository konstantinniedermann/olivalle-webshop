"""Neues Kunden-Frontend, parallel zur bestehenden Seite unter /neu.

Gleiche Inhalte und Funktionen wie die bestehenden Kundenseiten, andere
Gestaltung (Vorlagen in templates/neu/). Bestellt wird über denselben
Endpunkt POST /bestellen.
"""

from fastapi import APIRouter, Request

from app.routers.produkte import lade_produkt_ansichten
from app.templating import templates

router = APIRouter(prefix="/neu")


@router.get("")
def startseite(request: Request):
    return templates.TemplateResponse(
        request,
        "neu/produkte.html",
        {"produkte": lade_produkt_ansichten(), "active_page": "produkte"},
    )
