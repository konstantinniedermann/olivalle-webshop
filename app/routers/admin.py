import json
import secrets
from datetime import date

from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.client_ip import get_client_ip
from app.config import settings
from app.csrf import (
    CSRF_COOKIE_NAME,
    admin_identity,
    generiere_csrf_token,
    require_csrf,
)
from app.database import get_db
from app.repositories.admin_repo import (
    get_bestellung_detail,
    get_bestellungen_liste,
    get_dashboard_stats,
    get_log_fuer_bestellung,
    log_eintrag_schreiben,
    update_bestellung_status,
)
from app.services.auth_service import (
    create_session,
    login_guard,
    parse_credentials,
    validate_session,
    verify_password,
)
from app.services.rate_limit import RATE_LIMIT_MESSAGE, login_limiter
from app.templating import templates

router = APIRouter(prefix="/admin")

ALLE_STATUS = [
    "neu",
    "bezahlt",
    "in_bearbeitung",
    "versendet",
    "abholbereit",
    "abgeschlossen",
    "storniert",
]


def _login_rate_limit(request: Request) -> None:
    if not login_limiter.check(get_client_ip(request)):
        raise HTTPException(429, RATE_LIMIT_MESSAGE)


def _get_admin_label(admin_session: str | None) -> str | None:
    """Validate session cookie and return admin label or None."""
    if not admin_session:
        return None
    return validate_session(
        admin_session,
        secret=settings.secret_key,
        max_age=settings.admin_session_max_age,
    )


# --- Routes ---


def _anon_csrf(request: Request) -> str:
    csrf_id = request.cookies.get("csrf_id", "")
    return generiere_csrf_token(settings.secret_key, identity=f"anon:{csrf_id}")


@router.get("/login")
def admin_login_page(
    request: Request,
    csrf_id: str | None = Cookie(None),
):
    if not csrf_id:
        csrf_id = secrets.token_hex(16)
    csrf_token = generiere_csrf_token(
        settings.secret_key, identity=f"anon:{csrf_id}"
    )
    response = templates.TemplateResponse(
        request, "admin/login.html", {"csrf_token": csrf_token}
    )
    response.set_cookie(
        CSRF_COOKIE_NAME,
        csrf_id,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=3600,
    )
    return response


@router.post(
    "/login",
    dependencies=[Depends(require_csrf), Depends(_login_rate_limit)],
)
def admin_login(
    request: Request,
    password: str = Form(),
):
    client_ip = get_client_ip(request)

    if login_guard.is_locked(client_ip):
        csrf = _anon_csrf(request)
        return templates.TemplateResponse(
            request,
            "admin/login.html",
            {"csrf_token": csrf, "error": "Zu viele Fehlversuche. Bitte warten."},
        )

    credentials = parse_credentials(settings.admin_credentials)
    label = verify_password(password, credentials)

    conn = get_db()
    try:
        if not label:
            login_guard.record_failure(client_ip)
            log_eintrag_schreiben(
                conn,
                admin_label="?",
                aktion="login_fehlgeschlagen",
                details=client_ip,
            )
            csrf = _anon_csrf(request)
            return templates.TemplateResponse(
                request,
                "admin/login.html",
                {"csrf_token": csrf, "error": "Ungültiges Passwort."},
            )

        login_guard.reset(client_ip)
        log_eintrag_schreiben(
            conn, admin_label=label, aktion="login", details=client_ip
        )
    finally:
        conn.close()

    token = create_session(label, secret=settings.secret_key)
    response = RedirectResponse("/admin/", status_code=303)
    response.set_cookie(
        "admin_session",
        token,
        httponly=True,
        samesite="strict",
        secure=settings.cookie_secure,
        max_age=settings.admin_session_max_age,
    )
    return response


@router.post("/logout", dependencies=[Depends(require_csrf)])
def admin_logout(
    request: Request,
    admin_session: str | None = Cookie(None),
):
    label = _get_admin_label(admin_session) or "?"
    conn = get_db()
    try:
        log_eintrag_schreiben(conn, admin_label=label, aktion="logout")
    finally:
        conn.close()

    response = RedirectResponse("/admin/login", status_code=303)
    response.delete_cookie("admin_session")
    return response


@router.get("/")
def admin_dashboard(
    request: Request,
    admin_session: str | None = Cookie(None),
    status: str = "",
    suche: str = "",
    datum_von: str = "",
    datum_bis: str = "",
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)

    for wert in (datum_von, datum_bis):
        if wert:
            try:
                date.fromisoformat(wert)
            except ValueError as err:
                raise HTTPException(400, "Ungültiges Datum") from err

    conn = get_db()
    try:
        stats = get_dashboard_stats(conn)
        bestellungen = get_bestellungen_liste(
            conn,
            status=status,
            suche=suche,
            datum_von=datum_von,
            datum_bis=datum_bis,
        )
    finally:
        conn.close()

    csrf = generiere_csrf_token(
        settings.secret_key, identity=admin_identity(admin_session or "")
    )
    return templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        {
            "admin_label": label,
            "csrf_token": csrf,
            "stats": stats,
            "bestellungen": bestellungen,
            "alle_status": ALLE_STATUS,
            "filter_status": status,
            "filter_suche": suche,
            "filter_datum_von": datum_von,
            "filter_datum_bis": datum_bis,
        },
    )


@router.get("/bestellungen/{bestellung_id}")
def admin_bestellung_detail(
    request: Request,
    bestellung_id: int,
    admin_session: str | None = Cookie(None),
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)

    conn = get_db()
    try:
        bestellung = get_bestellung_detail(conn, bestellung_id)
        if not bestellung:
            raise HTTPException(404, "Bestellung nicht gefunden")
        logs = get_log_fuer_bestellung(conn, bestellung_id)
    finally:
        conn.close()

    csrf = generiere_csrf_token(
        settings.secret_key, identity=admin_identity(admin_session or "")
    )
    return templates.TemplateResponse(
        request,
        "admin/bestellung_detail.html",
        {
            "admin_label": label,
            "csrf_token": csrf,
            "bestellung": bestellung,
            "logs": logs,
            "alle_status": ALLE_STATUS,
        },
    )


@router.post(
    "/bestellungen/{bestellung_id}/status",
    dependencies=[Depends(require_csrf)],
)
def admin_status_aendern(
    request: Request,
    bestellung_id: int,
    neuer_status: str = Form(),
    admin_session: str | None = Cookie(None),
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)

    conn = get_db()
    try:
        bestellung = get_bestellung_detail(conn, bestellung_id)
        if not bestellung:
            raise HTTPException(404, "Bestellung nicht gefunden")

        alter_status = bestellung["status"]
        if alter_status != neuer_status:
            update_bestellung_status(
                conn, bestellung_id=bestellung_id, neuer_status=neuer_status
            )
            log_eintrag_schreiben(
                conn,
                admin_label=label,
                aktion="status_geaendert",
                details=json.dumps({"von": alter_status, "nach": neuer_status}),
                bestellung_id=bestellung_id,
            )

            from app.services.email_service import sende_status_email

            sende_status_email(bestellung_id, neuer_status, conn)
    finally:
        conn.close()

    return RedirectResponse(f"/admin/bestellungen/{bestellung_id}", status_code=303)


@router.post(
    "/bestellungen/{bestellung_id}/notiz",
    dependencies=[Depends(require_csrf)],
)
def admin_notiz_hinzufuegen(
    request: Request,
    bestellung_id: int,
    typ: str = Form(),
    text: str = Form(),
    admin_session: str | None = Cookie(None),
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)

    conn = get_db()
    try:
        log_eintrag_schreiben(
            conn,
            admin_label=label,
            aktion=typ,
            details=text,
            bestellung_id=bestellung_id,
        )
    finally:
        conn.close()

    return RedirectResponse(f"/admin/bestellungen/{bestellung_id}", status_code=303)
