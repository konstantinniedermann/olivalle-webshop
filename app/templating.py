import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.config import settings
from app.labels import zahlungsart_admin
from app.services.bestell_service import GRATIS_AB_CHF, VERSANDKOSTEN_CHF

_ZURICH_TZ = ZoneInfo("Europe/Zurich")
_UTC = ZoneInfo("UTC")


def zurich_time(value: str | None) -> str:
    """Konvertiert einen UTC-Timestamp-String (SQLite-Format) nach Europe/Zurich.

    Format der Ausgabe: ``YYYY-MM-DD HH:MM`` in Schweizer Lokalzeit.
    """
    if not value:
        return ""
    try:
        dt = datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return value
    dt_utc = dt.replace(tzinfo=_UTC)
    return dt_utc.astimezone(_ZURICH_TZ).strftime("%Y-%m-%d %H:%M")


def csp_nonce_processor(request: Request) -> dict:
    # Fallback auf leeren String, falls ein Template ausserhalb eines
    # Requests mit Middleware gerendert wird (z.B. statische Fehlerseiten).
    return {"csp_nonce": getattr(request.state, "csp_nonce", "")}


BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(
    directory=BASE_DIR / "templates",
    context_processors=[csp_nonce_processor],
)
templates.env.globals["app_version"] = settings.app_version
templates.env.globals["active_page"] = ""
templates.env.globals["versandkosten_chf"] = VERSANDKOSTEN_CHF
templates.env.globals["gratis_ab_chf"] = GRATIS_AB_CHF
templates.env.filters["from_json"] = json.loads
templates.env.filters["zahlungsart_admin"] = zahlungsart_admin
templates.env.filters["zurich_time"] = zurich_time
