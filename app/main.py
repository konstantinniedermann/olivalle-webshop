from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.middleware.security_headers import SecurityHeadersMiddleware

app = FastAPI(title="Olivalle Webshop")


@app.middleware("http")
async def redirect_www(request: Request, call_next):
    host = request.headers.get("host", "")
    if host.startswith("www."):
        proto = request.headers.get("x-forwarded-proto", request.url.scheme)
        new_url = request.url.replace(netloc=host[4:], scheme=proto)
        return RedirectResponse(url=str(new_url), status_code=301)
    return await call_next(request)


app.add_middleware(SecurityHeadersMiddleware)

init_db()

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/health")
def health():
    return {"status": "ok", "version": settings.app_version}


from app.routers import (  # noqa: E402
    admin,
    bestellungen,
    produkte,
    rabattcodes,
    seiten,
    warenkorb,
    webhooks,
)

app.include_router(admin.router)
app.include_router(produkte.router)
app.include_router(warenkorb.router)
app.include_router(bestellungen.router)
app.include_router(webhooks.router)
app.include_router(seiten.router)
app.include_router(rabattcodes.router)
