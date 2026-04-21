from fastapi import APIRouter, Cookie, Form, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.config import settings
from app.csrf import admin_identity, generiere_csrf_token
from app.database import get_db
from app.repositories.rabattcode_repo import (
    alle_rabattcodes,
    rabattcode_aktualisieren,
    rabattcode_anlegen,
    rabattcode_laden,
)
from app.services.auth_service import validate_session
from app.services.rabattcode_service import pruefe_rabattcode
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


class RabattcodeRequest(BaseModel):
    code: str
    email: str
    subtotal: float


@router.post("/api/rabattcode/pruefen")
def rabattcode_pruefen(req: RabattcodeRequest):
    conn = get_db()
    try:
        result = pruefe_rabattcode(conn, req.code, req.email, req.subtotal)
        if result["gueltig"]:
            if result["rabattart"] == "prozent":
                beschreibung = f"{result['rabattwert']:.0f}% Rabatt"
            else:
                beschreibung = f"CHF {result['rabattbetrag']:.2f} Rabatt"
            return {
                "gueltig": True,
                "rabattbetrag": result["rabattbetrag"],
                "rabattart": result["rabattart"],
                "beschreibung": beschreibung,
                "code": result["code"],
            }
        return {"gueltig": False, "fehler": result["fehler"]}
    finally:
        conn.close()


@router.get("/admin/rabattcodes")
def admin_rabattcodes_liste(request: Request, admin_session: str | None = Cookie(None)):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)
    conn = get_db()
    try:
        codes = alle_rabattcodes(conn)
    finally:
        conn.close()
    from datetime import date as _date

    csrf = generiere_csrf_token(
        settings.secret_key, identity=admin_identity(admin_session or "")
    )
    heute = _date.today().isoformat()
    return templates.TemplateResponse(
        request,
        "admin/rabattcodes.html",
        {"admin_label": label, "csrf_token": csrf, "codes": codes, "heute": heute},
    )


@router.get("/admin/rabattcodes/neu")
def admin_rabattcode_neu(request: Request, admin_session: str | None = Cookie(None)):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)
    csrf = generiere_csrf_token(
        settings.secret_key, identity=admin_identity(admin_session or "")
    )
    return templates.TemplateResponse(
        request,
        "admin/rabattcode_form.html",
        {"admin_label": label, "csrf_token": csrf, "code": None},
    )


@router.post("/admin/rabattcodes/neu")
def admin_rabattcode_erstellen(
    request: Request,
    code: str = Form(),
    rabattart: str = Form(),
    rabattwert: float = Form(),
    gueltig_von: str = Form(),
    gueltig_bis: str = Form(),
    mindestbestellwert_chf: str = Form(""),
    max_einloesungen: str = Form(""),
    aktiv: str = Form("0"),
    csrf_token: str = Form(""),
    admin_session: str | None = Cookie(None),
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)
    conn = get_db()
    try:
        from app.repositories.admin_repo import log_eintrag_schreiben

        rabattcode_anlegen(
            conn,
            code=code,
            rabattart=rabattart,
            rabattwert=rabattwert,
            gueltig_von=gueltig_von,
            gueltig_bis=gueltig_bis,
            mindestbestellwert_chf=float(mindestbestellwert_chf)
            if mindestbestellwert_chf
            else None,
            max_einloesungen=int(max_einloesungen) if max_einloesungen else None,
        )
        log_eintrag_schreiben(
            conn,
            admin_label=label,
            aktion="rabattcode_erstellt",
            details=code.upper().strip(),
        )
    finally:
        conn.close()
    return RedirectResponse("/admin/rabattcodes", status_code=303)


@router.get("/admin/rabattcodes/{code_id}/bearbeiten")
def admin_rabattcode_bearbeiten(
    request: Request,
    code_id: int,
    admin_session: str | None = Cookie(None),
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)
    conn = get_db()
    try:
        rc = rabattcode_laden(conn, code_id)
    finally:
        conn.close()
    if not rc:
        return RedirectResponse("/admin/rabattcodes", status_code=303)
    csrf = generiere_csrf_token(
        settings.secret_key, identity=admin_identity(admin_session or "")
    )
    return templates.TemplateResponse(
        request,
        "admin/rabattcode_form.html",
        {"admin_label": label, "csrf_token": csrf, "code": rc},
    )


@router.post("/admin/rabattcodes/{code_id}/bearbeiten")
def admin_rabattcode_speichern(
    request: Request,
    code_id: int,
    code: str = Form(),
    rabattart: str = Form(),
    rabattwert: float = Form(),
    gueltig_von: str = Form(),
    gueltig_bis: str = Form(),
    mindestbestellwert_chf: str = Form(""),
    max_einloesungen: str = Form(""),
    aktiv: str = Form("0"),
    csrf_token: str = Form(""),
    admin_session: str | None = Cookie(None),
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)
    conn = get_db()
    try:
        rabattcode_aktualisieren(
            conn,
            code_id,
            code=code.upper().strip(),
            rabattart=rabattart,
            rabattwert=rabattwert,
            gueltig_von=gueltig_von,
            gueltig_bis=gueltig_bis,
            mindestbestellwert_chf=float(mindestbestellwert_chf)
            if mindestbestellwert_chf
            else None,
            max_einloesungen=int(max_einloesungen) if max_einloesungen else None,
            aktiv=1 if aktiv == "1" else 0,
        )
    finally:
        conn.close()
    return RedirectResponse("/admin/rabattcodes", status_code=303)
