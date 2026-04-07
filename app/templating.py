import json
from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.config import settings
from app.labels import zahlungsart_admin

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.globals["app_version"] = settings.app_version
templates.env.globals["active_page"] = ""
templates.env.filters["from_json"] = json.loads
templates.env.filters["zahlungsart_admin"] = zahlungsart_admin
