import base64
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
                "name": f"rechnung-{bestell_id}.svg",
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
