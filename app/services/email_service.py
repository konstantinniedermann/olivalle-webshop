import base64
import logging
import sqlite3
from pathlib import Path

from brevo import Brevo
from jinja2 import Environment, FileSystemLoader

from app.config import settings

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
) -> object:
    template = env.get_template("bestellbestaetigung.html")
    html = template.render(
        kunde=kunde,
        bestell_id=bestell_id,
        positionen=positionen,
        versandkosten=versandkosten,
        total=total,
    )

    params: dict = {
        "sender": {"email": "bestellung@olivalle.ch", "name": "Olivalle"},
        "to": [{"email": empfaenger}],
        "reply_to": {"email": "olivalle.olten@outlook.com"},
        "subject": f"Olivalle — Bestellbestätigung #{bestell_id}",
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

    if conn:
        from app.repositories.admin_repo import log_eintrag_schreiben

        log_eintrag_schreiben(
            conn,
            admin_label="system",
            aktion="email_ausgang",
            details=f"An: {empfaenger} — Olivalle — Bestellbestätigung #{bestell_id}",
            bestellung_id=bestell_id,
        )

    return result


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

logger = logging.getLogger(__name__)


def sende_status_email(
    bestellung_id: int,
    neuer_status: str,
    conn: sqlite3.Connection,
) -> None:
    """Sendet eine Status-E-Mail an den Kunden, falls für diesen Status vorgesehen."""
    config = _STATUS_EMAIL_CONFIG.get(neuer_status)
    if not config:
        return

    from app.repositories.admin_repo import get_bestellung_detail, log_eintrag_schreiben

    bestellung = get_bestellung_detail(conn, bestellung_id)
    if not bestellung:
        return

    zahlungsart = bestellung["zahlungsart"]
    versandart = bestellung["versandart"]

    if neuer_status == "bezahlt" and zahlungsart != "rechnung":
        return
    if neuer_status == "versendet" and versandart != "versand":
        return
    if neuer_status == "abholbereit" and versandart != "abholung":
        return

    template_datei, betreff_vorlage = config
    betreff = betreff_vorlage.format(bestell_id=bestellung_id)

    template = env.get_template(template_datei)
    html = template.render(
        kunde_vorname=bestellung["vorname"],
        bestell_id=bestellung_id,
    )

    try:
        brevo_client.transactional_emails.send_transac_email(
            sender={"email": "bestellung@olivalle.ch", "name": "Olivalle"},
            to=[{"email": bestellung["email"]}],
            reply_to={"email": "olivalle.olten@outlook.com"},
            subject=betreff,
            html_content=html,
        )

        log_eintrag_schreiben(
            conn,
            admin_label="system",
            aktion="email_ausgang",
            details=f"An: {bestellung['email']} — {betreff}",
            bestellung_id=bestellung_id,
        )
    except Exception:
        logger.exception("Status-E-Mail konnte nicht gesendet werden: %s", betreff)
        log_eintrag_schreiben(
            conn,
            admin_label="system",
            aktion="email_fehler",
            details=f"Versand fehlgeschlagen an: {bestellung['email']} — {betreff}",
            bestellung_id=bestellung_id,
        )


# Labels für menschenlesbare Anzeige in E-Mails
_ZAHLUNGSART_LABELS: dict[str, str] = {
    "stripe": "Twint / Kreditkarte",
    "rechnung": "Rechnung (QR)",
    "abholung_bar": "Bezahlung bei Abholung",
}

_VERSANDART_LABELS: dict[str, str] = {
    "versand": "Postversand",
    "abholung": "Abholung vor Ort",
}


def sende_stakeholder_benachrichtigung(
    bestell_id: int,
    kunde: dict,
    positionen: list[dict],
    versandkosten: float,
    total: float,
    zahlungsart: str,
    versandart: str,
    conn: sqlite3.Connection | None = None,
) -> object:
    """Benachrichtigt den Stakeholder über eine neue Bestellung."""
    template = env.get_template("bestellung_stakeholder.html")
    html = template.render(
        bestell_id=bestell_id,
        kunde=kunde,
        positionen=positionen,
        versandkosten=versandkosten,
        total=total,
        zahlungsart=zahlungsart,
        zahlungsart_label=_ZAHLUNGSART_LABELS.get(zahlungsart, zahlungsart),
        versandart_label=_VERSANDART_LABELS.get(versandart, versandart),
    )

    result = brevo_client.transactional_emails.send_transac_email(
        sender={"email": "bestellung@olivalle.ch", "name": "Olivalle"},
        to=[{"email": "olivalle.olten@outlook.com"}],
        subject=f"Neue Bestellung #{bestell_id}",
        html_content=html,
    )

    if conn:
        from app.repositories.admin_repo import log_eintrag_schreiben

        log_eintrag_schreiben(
            conn,
            admin_label="system",
            aktion="email_ausgang",
            details=f"An: olivalle.olten@outlook.com — Neue Bestellung #{bestell_id}",
            bestellung_id=bestell_id,
        )

    return result
