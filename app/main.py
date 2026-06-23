import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app.database import get_db, init_db
from app.middleware.redirect_www import RedirectWwwMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

app = FastAPI(title="Olivalle Webshop")

# Reihenfolge: add_middleware wird LIFO verarbeitet – SecurityHeaders zuletzt
# hinzugefügt bedeutet es ist der äusserste Wrapper und sieht alle Responses,
# inklusive 301-Redirects von RedirectWwwMiddleware.
app.add_middleware(RedirectWwwMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

init_db()

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/health")
def health():
    try:
        conn = get_db()
        try:
            conn.execute("SELECT 1")
        finally:
            conn.close()
    except sqlite3.Error as err:
        raise HTTPException(status_code=503, detail="db unavailable") from err
    return {"status": "ok"}


from app.routers import (  # noqa: E402
    admin,
    bestellungen,
    produkt_admin,
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
app.include_router(produkt_admin.router)
