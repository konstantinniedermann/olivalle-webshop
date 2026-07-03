import base64
import logging
import sqlite3
from pathlib import Path

from brevo import Brevo
from jinja2 import Environment, FileSystemLoader

from app.config import settings
from app.labels import VERSANDART_LABELS, ZAHLUNGSART_LABELS_EMAIL

logger = logging.getLogger(__name__)

brevo_client = Brevo(api_key=settings.brevo_api_key)

TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "emails"
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


def sende_bestellbestaetigung(
    empfaenger: str,
    bestell_id: int,
    kunde: dict,
    positionen: list[dict],
    versandkosten: float,
    total: float,
    anhang: bytes | None = None,
    conn: sqlite3.Connection | None = None,
    template_name: str = "bestellbestaetigung.html",
    rabattbetrag: float = 0,
    rabattcode: str = "",
) -> object:
    betreff = f"Olivalle — Bestellbestätigung #{bestell_id}"
    try:
        template = env.get_template(template_name)
        html = template.render(
            kunde=kunde,
            bestell_id=bestell_id,
            positionen=positionen,
            versandkosten=versandkosten,
            total=total,
            rabattbetrag=rabattbetrag,
            rabattcode=rabattcode,
        )

        params: dict = {
            "sender": {"email": "bestellung@olivalle.ch", "name": "Olivalle"},
            "to": [{"email": empfaenger}],
            "reply_to": {"email": "olivalle.olten@outlook.com"},
            "subject": betreff,
            "html_content": html,
        }

        if anhang:
            params["attachment"] = [
                {
                    "content": base64.b64encode(anhang).decode("utf-8"),
                    "name": f"rechnung-{bestell_id}.pdf",
                }
            ]

        result = brevo_client.transactional_emails.send_transac_email(**params)
    except Exception:
        # Weder Brevo-Ausfall noch Template-Fehler dürfen den Bestellablauf
        # kippen: die Bestellung ist zu diesem Zeitpunkt bereits persistiert.
        # Fehler protokollieren (email_fehler), damit der Betreiber die Mail
        # manuell nachsenden kann.
        logger.exception("Bestellbestätigung konnte nicht gesendet werden: %s", betreff)
        _log_email(
            conn,
            "email_fehler",
            f"Versand fehlgeschlagen an: {empfaenger} — {betreff}",
            bestell_id,
        )
        return None

    _log_email(conn, "email_ausgang", f"An: {empfaenger} — {betreff}", bestell_id)
    return result


def _log_email(
    conn: sqlite3.Connection | None,
    aktion: str,
    details: str,
    bestellung_id: int,
) -> None:
    """Schreibt einen E-Mail-Logeintrag (email_ausgang / email_fehler), falls conn."""
    if not conn:
        return
    from app.repositories.admin_repo import log_eintrag_schreiben

    log_eintrag_schreiben(
        conn,
        admin_label="system",
        aktion=aktion,
        details=details,
        bestellung_id=bestellung_id,
    )


# Mapping: Status → (Template-Datei, Betreff-Text)
_STATUS_EMAIL_CONFIG: dict[str, tuple[str, str]] = {
    "bezahlt": (
        "zahlungseingang.html",
        "Zahlungseingang bestätigt — Bestellung #{bestell_id}",
    ),
    "versendet": (
        "versandbestaetigung.html",
        "Deine Bestellung #{bestell_id} ist unterwegs",
    ),
    "abholbereit": (
        "abholbereit.html",
        "Deine Bestellung #{bestell_id} ist abholbereit",
    ),
}


def sende_status_email(
    bestellung_id: int,
    neuer_status: str,
    conn: sqlite3.Connection,
) -> None:
    """Sendet eine Status-E-Mail an den Kunden, falls für diesen Status vorgesehen."""
    config = _STATUS_EMAIL_CONFIG.get(neuer_status)
    if not config:
        return

    from app.repositories.admin_repo import get_bestellung_detail

    bestellung = get_bestellung_detail(conn, bestellung_id)
    if not bestellung:
        return

    zahlungsart = bestellung["zahlungsart"]
    versandart = bestellung["versandart"]

    if neuer_status == "bezahlt" and zahlungsart not in ("rechnung", "abholung_bar"):
        return
    if neuer_status == "versendet" and versandart != "versand":
        return
    if neuer_status == "abholbereit" and versandart != "abholung":
        return

    template_datei, betreff_vorlage = config
    betreff = betreff_vorlage.format(bestell_id=bestellung_id)

    try:
        template = env.get_template(template_datei)
        html = template.render(
            kunde_vorname=bestellung["vorname"],
            bestell_id=bestellung_id,
        )
        brevo_client.transactional_emails.send_transac_email(
            sender={"email": "bestellung@olivalle.ch", "name": "Olivalle"},
            to=[{"email": bestellung["email"]}],
            reply_to={"email": "olivalle.olten@outlook.com"},
            subject=betreff,
            html_content=html,
        )
    except Exception:
        logger.exception("Status-E-Mail konnte nicht gesendet werden: %s", betreff)
        _log_email(
            conn,
            "email_fehler",
            f"Versand fehlgeschlagen an: {bestellung['email']} — {betreff}",
            bestellung_id,
        )
        return

    _log_email(
        conn, "email_ausgang", f"An: {bestellung['email']} — {betreff}", bestellung_id
    )


def sende_stakeholder_benachrichtigung(
    bestell_id: int,
    kunde: dict,
    positionen: list[dict],
    versandkosten: float,
    total: float,
    zahlungsart: str,
    versandart: str,
    conn: sqlite3.Connection | None = None,
    rabattbetrag: float = 0,
    rabattcode: str = "",
) -> object:
    """Benachrichtigt den Stakeholder über eine neue Bestellung."""
    betreff = f"Neue Bestellung #{bestell_id}"
    try:
        template = env.get_template("bestellung_stakeholder.html")
        html = template.render(
            bestell_id=bestell_id,
            kunde=kunde,
            positionen=positionen,
            versandkosten=versandkosten,
            total=total,
            zahlungsart=zahlungsart,
            zahlungsart_label=ZAHLUNGSART_LABELS_EMAIL.get(zahlungsart, zahlungsart),
            versandart_label=VERSANDART_LABELS.get(versandart, versandart),
            rabattbetrag=rabattbetrag,
            rabattcode=rabattcode,
        )
        result = brevo_client.transactional_emails.send_transac_email(
            sender={"email": "bestellung@olivalle.ch", "name": "Olivalle"},
            to=[{"email": "olivalle.olten@outlook.com"}],
            subject=betreff,
            html_content=html,
        )
    except Exception:
        logger.exception("Stakeholder-Mail konnte nicht gesendet werden: %s", betreff)
        _log_email(
            conn,
            "email_fehler",
            f"Versand fehlgeschlagen an: olivalle.olten@outlook.com — {betreff}",
            bestell_id,
        )
        return None

    _log_email(
        conn,
        "email_ausgang",
        f"An: olivalle.olten@outlook.com — {betreff}",
        bestell_id,
    )
    return result
