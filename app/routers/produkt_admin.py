from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.config import settings
from app.csrf import admin_identity, generiere_csrf_token, require_csrf
from app.database import get_db
from app.repositories.admin_repo import log_eintrag_schreiben
from app.repositories.produkt_repo import (
    aktion_entfernen,
    aktion_setzen,
    alle_produkte_admin,
    produkt_laden,
)
from app.services.auth_service import validate_session
from app.templating import templates

router = APIRouter()


def _get_admin_label(admin_session: str | None) -> str | None:
    if not admin_session:
        return None
    return validate_session(
        admin_session,
        secret=settings.secret_key,
        max_age=settings.admin_session_max_age,
    )


@router.get("/admin/produkte")
def admin_produkte_liste(request: Request, admin_session: str | None = Cookie(None)):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)
    conn = get_db()
    try:
        produkte = alle_produkte_admin(conn)
    finally:
        conn.close()
    csrf = generiere_csrf_token(
        settings.secret_key, identity=admin_identity(admin_session or "")
    )
    return templates.TemplateResponse(
        request,
        "admin/produkte.html",
        {"admin_label": label, "csrf_token": csrf, "produkte": produkte},
    )


@router.get("/admin/produkte/{produkt_id}/aktion")
def admin_aktion_formular(
    request: Request, produkt_id: int, admin_session: str | None = Cookie(None)
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)
    conn = get_db()
    try:
        produkt = produkt_laden(conn, produkt_id)
    finally:
        conn.close()
    if not produkt:
        return RedirectResponse("/admin/produkte", status_code=303)
    csrf = generiere_csrf_token(
        settings.secret_key, identity=admin_identity(admin_session or "")
    )
    return templates.TemplateResponse(
        request,
        "admin/produkt_aktion_form.html",
        {"admin_label": label, "csrf_token": csrf, "produkt": produkt},
    )


@router.post(
    "/admin/produkte/{produkt_id}/aktion", dependencies=[Depends(require_csrf)]
)
def admin_aktion_speichern(
    request: Request,
    produkt_id: int,
    aktionspreis_chf: str = Form(""),
    aktionstext: str = Form(""),
    aktion_von: str = Form(""),
    aktion_bis: str = Form(""),
    csrf_token: str = Form(""),
    admin_session: str | None = Cookie(None),
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)
    conn = get_db()
    try:
        produkt = produkt_laden(conn, produkt_id)
        if not produkt:
            raise HTTPException(404, "Produkt nicht gefunden")
        if not aktionspreis_chf.strip():
            aktion_entfernen(conn, produkt_id)
            log_eintrag_schreiben(
                conn, admin_label=label, aktion="aktion_entfernt",
                details=produkt["name"],
            )
        else:
            preis = float(aktionspreis_chf)
            if preis <= 0 or preis >= produkt["preis_chf"]:
                raise HTTPException(
                    400, "Aktionspreis muss grösser als 0 und kleiner als der "
                    "Normalpreis sein.",
                )
            aktion_setzen(
                conn, produkt_id,
                aktionspreis_chf=preis,
                aktionstext=aktionstext.strip(),
                aktion_von=aktion_von.strip() or None,
                aktion_bis=aktion_bis.strip() or None,
            )
            log_eintrag_schreiben(
                conn, admin_label=label, aktion="aktion_gesetzt",
                details=f"{produkt['name']}: CHF {preis:.2f}",
            )
    finally:
        conn.close()
    return RedirectResponse("/admin/produkte", status_code=303)
