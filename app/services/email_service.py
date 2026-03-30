import sqlite3
from pathlib import Path

import resend
from jinja2 import Environment, FileSystemLoader

from app.config import settings

resend.api_key = settings.resend_api_key

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
) -> dict:
    template = env.get_template("bestellbestaetigung.html")
    html = template.render(
        kunde=kunde,
        bestell_id=bestell_id,
        positionen=positionen,
        versandkosten=versandkosten,
        total=total,
    )

    params = {
        "from": "Olivalle <bestellung@olivalle.ch>",
        "to": [empfaenger],
        "reply_to": "olivalle.olten@outlook.com",
        "subject": f"Olivalle — Bestellbestätigung #{bestell_id}",
        "html": html,
    }

    if anhang:
        params["attachments"] = [
            {
                "filename": f"rechnung-{bestell_id}.svg",
                "content": list(anhang),
            }
        ]

    result = resend.Emails.send(**params)

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
