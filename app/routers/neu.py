"""Neues Kunden-Frontend, parallel zur bestehenden Seite unter /neu.

Gleiche Inhalte und Funktionen wie die bestehenden Kundenseiten, andere
Gestaltung (Vorlagen in templates/neu/). Bestellt wird über denselben
Endpunkt POST /bestellen.
"""

from fastapi import APIRouter, Cookie, Request

from app.routers.bestellungen import bestaetigung_antwort, checkout_antwort
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


@router.get("/ueber-das-oel")
def ueber_das_oel(request: Request):
    return templates.TemplateResponse(
        request, "neu/ueber-das-oel.html", {"active_page": "ueber-das-oel"}
    )


@router.get("/warenkorb")
def warenkorb(request: Request):
    return templates.TemplateResponse(
        request, "neu/warenkorb.html", {"active_page": "warenkorb"}
    )


@router.get("/checkout")
def checkout(request: Request, csrf_id: str | None = Cookie(None)):
    return checkout_antwort(request, csrf_id, variante="neu")


@router.get("/bestaetigung")
def bestaetigung(request: Request, session_id: str = ""):
    return bestaetigung_antwort(request, session_id, variante="neu")


@router.get("/impressum")
def impressum(request: Request):
    return templates.TemplateResponse(request, "neu/impressum.html")


@router.get("/datenschutz")
def datenschutz(request: Request):
    return templates.TemplateResponse(request, "neu/datenschutz.html")


@router.get("/agb")
def agb(request: Request):
    return templates.TemplateResponse(request, "neu/agb.html")
