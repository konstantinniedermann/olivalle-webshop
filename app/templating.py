import json
from pathlib import Path

from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.config import settings
from app.labels import zahlungsart_admin


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
templates.env.filters["from_json"] = json.loads
templates.env.filters["zahlungsart_admin"] = zahlungsart_admin
