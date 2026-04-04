from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db

app = FastAPI(title="Olivalle Webshop")

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
