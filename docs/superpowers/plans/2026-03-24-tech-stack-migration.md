# Tech-Stack Migration — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Olivalle Webshop von Next.js/Supabase/Vercel auf FastAPI+Jinja2+SQLite+fly.io migrieren.

**Architecture:** Ein Python-Monolith (FastAPI) liefert HTML via Jinja2-Templates mit Tailwind CSS. SQLite als eingebettete DB. Warenkorb clientseitig in Vanilla JS (localStorage). Stripe Checkout als Redirect, QR-Rechnung via swiss-qr-bill, E-Mail via Resend. Deployment als Docker-Container auf fly.io.

**Tech Stack:** Python 3.13, FastAPI, Jinja2, Tailwind CSS (CDN), Vanilla JS, SQLite, Stripe, swiss-qr-bill, Resend, pytest, Ruff, Docker, fly.io

**Spec:** `docs/superpowers/specs/2026-03-24-tech-stack-design.md`

---

## File Structure

```
olivalle/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI-Instanz, Middleware, Mount static/templates
│   ├── config.py             # Settings via pydantic-settings (.env)
│   ├── templating.py         # Jinja2Templates-Instanz (vermeidet zirkuläre Imports)
│   ├── database.py           # SQLite-Verbindung, Schema-Init
│   ├── csrf.py               # CSRF-Middleware + Token-Generierung
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── produkte.py       # GET / (Startseite = Produktliste)
│   │   ├── warenkorb.py      # GET /warenkorb
│   │   ├── bestellungen.py   # GET /checkout, POST /bestellen
│   │   └── webhooks.py       # POST /webhook/stripe
│   ├── services/
│   │   ├── __init__.py
│   │   ├── bestell_service.py    # Bestelllogik, Preisberechnung, Versandkosten
│   │   ├── stripe_service.py     # Stripe Checkout Session erstellen
│   │   ├── email_service.py      # Resend-Integration
│   │   └── qr_service.py         # swiss-qr-bill PDF-Generierung
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── produkt_repo.py       # SELECT produkte
│   │   └── bestell_repo.py       # INSERT/SELECT bestellungen + positionen + kunden
│   └── models.py             # Pydantic-Schemas (Produkt, Kunde, Bestellung, etc.)
├── templates/
│   ├── base.html             # Layout: Head, Nav, Footer, Tailwind CDN
│   ├── produkte.html         # Produktkarten (Startseite)
│   ├── warenkorb.html        # Warenkorb-Übersicht
│   ├── checkout.html         # Adressformular + Versand + Zahlungsart
│   ├── bestaetigung.html     # Bestellbestätigung nach Zahlung
│   └── emails/
│       └── bestellbestaetigung.html  # E-Mail-Template
├── static/
│   ├── js/
│   │   └── cart.js           # Warenkorb-Logik (localStorage, ~80 Zeilen)
│   └── images/               # Produktbilder (aus frontend/public/images übernehmen)
├── tests/
│   ├── conftest.py           # Fixtures: Test-DB, TestClient
│   ├── test_models.py
│   ├── test_produkt_repo.py
│   ├── test_bestell_repo.py
│   ├── test_bestell_service.py
│   ├── test_stripe_service.py
│   ├── test_qr_service.py
│   ├── test_email_service.py
│   ├── test_api_produkte.py
│   ├── test_api_bestellungen.py
│   ├── test_api_webhooks.py
│   └── test_csrf.py
├── migrations/
│   └── 001_initial.sql       # CREATE TABLE Statements
├── pyproject.toml            # Dependencies, Ruff-Config, pytest-Config
├── Dockerfile
├── fly.toml
├── .env.example
├── Makefile                  # Aktualisiert: dev, test, lint, migrate, docs
├── mkdocs.yml                # MkDocs-Konfiguration (Material-Theme)
└── docs-serve.command        # macOS Doppelklick → MkDocs im Browser
```

---

## Task 1: Projekt-Scaffold + Abhängigkeiten

**Files:**
- Create: `pyproject.toml`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/config.py`
- Create: `.env.example`
- Modify: `Makefile`
- Modify: `.gitignore`
- Remove: `frontend/` (nur public/images behalten → nach `static/images/` verschieben)

- [ ] **Step 1: pyproject.toml erstellen**

```toml
[project]
name = "olivalle"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "jinja2>=3.1",
    "pydantic-settings>=2.7",
    "stripe>=12",
    "resend>=2",
    "qrbill>=1.1",
    "python-multipart>=0.0.18",
    "itsdangerous>=2.2",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "httpx>=0.28",
    "ruff>=0.9",
]

[tool.ruff]
target-version = "py313"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 2: .env.example erstellen**

```env
# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Resend
RESEND_API_KEY=re_...

# App
SECRET_KEY=change-me-in-production
BASE_URL=http://localhost:8000

# IBAN für QR-Rechnung (aus NOTES.local.md)
QR_IBAN=CH...
QR_NAME=...
QR_ADDRESS=...
QR_ZIP=...
QR_CITY=...
```

- [ ] **Step 3: app/config.py erstellen**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env"}

    secret_key: str = "change-me"
    base_url: str = "http://localhost:8000"

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    resend_api_key: str = ""

    qr_iban: str = ""
    qr_name: str = ""
    qr_address: str = ""
    qr_zip: str = ""
    qr_city: str = ""

    database_path: str = "olivalle.db"


settings = Settings()
```

- [ ] **Step 4: app/templating.py erstellen (vermeidet zirkuläre Imports)**

```python
from pathlib import Path

from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
```

- [ ] **Step 5: app/main.py erstellen (minimaler FastAPI-Server)**

```python
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Olivalle Webshop")

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 6: app/__init__.py erstellen (leer)**

```python
```

- [ ] **Step 7: Verzeichnisse + Platzhalter anlegen**

```bash
mkdir -p app/routers app/services app/repositories templates/emails static/js static/images tests migrations
touch app/routers/__init__.py app/services/__init__.py app/repositories/__init__.py
```

- [ ] **Step 8: Bilder von frontend/public/images nach static/images verschieben**

```bash
cp -r frontend/public/images/* static/images/ 2>/dev/null || true
```

- [ ] **Step 9: .gitignore aktualisieren**

Folgendes hinzufügen:
```
# Python
__pycache__/
*.pyc
.venv/

# SQLite
*.db

# Environment
.env

# MkDocs
site/

# Node (nicht mehr aktiv, aber sicherheitshalber)
node_modules/
```

- [ ] **Step 10: Makefile aktualisieren**

```makefile
.DEFAULT_GOAL := help

.PHONY: help dev test lint migrate docs

help: ## Alle verfügbaren Befehle anzeigen
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

dev: ## FastAPI-Server mit Auto-Reload starten
	uv run uvicorn app.main:app --reload --port 8000

test: ## Tests ausführen (pytest)
	uv run pytest -v

lint: ## Linting (Ruff)
	uv run ruff check .

format: ## Code formatieren (Ruff)
	uv run ruff format .

migrate: ## Datenbank-Migration ausführen
	uv run python -c "from app.database import init_db; init_db()"

docs: ## MkDocs Dokumentation lokal starten
	uv run mkdocs serve
```

- [ ] **Step 11: Abhängigkeiten installieren + Server testen**

```bash
uv sync --dev
uv run uvicorn app.main:app --port 8000 &
curl http://localhost:8000/health
# Expected: {"status":"ok"}
kill %1
```

- [ ] **Step 12: Commit**

```bash
git add pyproject.toml app/ .env.example Makefile .gitignore static/ templates/ tests/ migrations/
git commit -m "feat: Projekt-Scaffold für neuen Python-Stack

FastAPI + Jinja2 + SQLite ersetzt Next.js + Supabase.
Referenz: docs/superpowers/specs/2026-03-24-tech-stack-design.md"
```

---

## Task 2: Datenbank (SQLite) + Models

**Files:**
- Create: `app/database.py`
- Create: `app/models.py`
- Create: `migrations/001_initial.sql`
- Create: `tests/conftest.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Migration-SQL schreiben**

`migrations/001_initial.sql`:
```sql
CREATE TABLE IF NOT EXISTS produkte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    menge_ml INTEGER NOT NULL,
    preis_chf REAL NOT NULL,
    beschreibung TEXT NOT NULL DEFAULT '',
    bild_pfad TEXT NOT NULL DEFAULT '',
    aktiv INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS kunden (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vorname TEXT NOT NULL,
    nachname TEXT NOT NULL,
    email TEXT NOT NULL,
    telefon TEXT NOT NULL DEFAULT '',
    strasse TEXT NOT NULL,
    plz TEXT NOT NULL,
    ort TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bestellungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kunde_id INTEGER NOT NULL REFERENCES kunden(id),
    status TEXT NOT NULL DEFAULT 'neu',
    zahlungsart TEXT NOT NULL,
    versandart TEXT NOT NULL,
    versandkosten_chf REAL NOT NULL DEFAULT 0,
    total_chf REAL NOT NULL,
    stripe_session_id TEXT,
    kommentar TEXT NOT NULL DEFAULT '',
    erstellt_am TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS bestellpositionen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bestellung_id INTEGER NOT NULL REFERENCES bestellungen(id),
    produkt_id INTEGER NOT NULL REFERENCES produkte(id),
    menge INTEGER NOT NULL,
    einzelpreis_chf REAL NOT NULL
);

-- Seed: Olivalle-Produkte
INSERT OR IGNORE INTO produkte (id, name, menge_ml, preis_chf, beschreibung, bild_pfad) VALUES
    (1, 'Olivenöl 250ml', 250, 8.00, 'Biologisches Olivenöl aus Andalusien — kleine Flasche', 'olivenoel-250ml.jpg'),
    (2, 'Olivenöl 750ml', 750, 18.00, 'Biologisches Olivenöl aus Andalusien — grosse Flasche', 'olivenoel-750ml.jpg'),
    (3, 'Olivenöl 3l Kanister', 3000, 50.00, 'Biologisches Olivenöl aus Andalusien — Kanister', 'olivenoel-3l.jpg');
```

- [ ] **Step 2: app/database.py erstellen**

```python
import sqlite3
from pathlib import Path

from app.config import settings

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_db()
    try:
        for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            conn.executescript(sql_file.read_text())
        conn.commit()
    finally:
        conn.close()
```

- [ ] **Step 3: app/models.py erstellen (Pydantic-Schemas)**

```python
from pydantic import BaseModel, Field


class Produkt(BaseModel):
    id: int
    name: str
    menge_ml: int
    preis_chf: float
    beschreibung: str
    bild_pfad: str
    aktiv: bool = True


class KundeInput(BaseModel):
    vorname: str = Field(max_length=100)
    nachname: str = Field(max_length=100)
    email: str = Field(max_length=254)
    telefon: str = Field(default="", max_length=30)
    strasse: str = Field(max_length=200)
    plz: str = Field(max_length=10)
    ort: str = Field(max_length=100)


class WarenkorbItem(BaseModel):
    produkt_id: int
    menge: int = Field(ge=1, le=100)


class BestellungInput(BaseModel):
    kunde: KundeInput
    items: list[WarenkorbItem]
    versandart: str  # "versand" oder "abholung"
    zahlungsart: str  # "stripe" oder "rechnung"
    kommentar: str = Field(default="", max_length=1000)
```

- [ ] **Step 4: Test-Fixtures erstellen**

`tests/conftest.py`:
```python
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import MIGRATIONS_DIR
from app.main import app


@pytest.fixture()
def db(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        conn.executescript(sql_file.read_text())
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("app.config.settings.database_path", db_path)
    from app.database import init_db
    init_db()
    return TestClient(app)
```

- [ ] **Step 5: Failing test schreiben**

`tests/test_models.py`:
```python
from app.models import BestellungInput, KundeInput, Produkt, WarenkorbItem


def test_produkt_from_db_row():
    row = {
        "id": 1,
        "name": "Olivenöl 250ml",
        "menge_ml": 250,
        "preis_chf": 8.0,
        "beschreibung": "Bio",
        "bild_pfad": "bild.jpg",
        "aktiv": 1,
    }
    produkt = Produkt(**row)
    assert produkt.preis_chf == 8.0
    assert produkt.aktiv is True


def test_bestellung_input_minimal():
    data = BestellungInput(
        kunde=KundeInput(
            vorname="Max",
            nachname="Muster",
            email="max@example.com",
            strasse="Musterstr. 1",
            plz="4600",
            ort="Olten",
        ),
        items=[WarenkorbItem(produkt_id=1, menge=2)],
        versandart="versand",
        zahlungsart="stripe",
    )
    assert len(data.items) == 1
    assert data.kommentar == ""
```

- [ ] **Step 6: Tests ausführen**

```bash
uv run pytest tests/test_models.py -v
# Expected: 2 passed
```

- [ ] **Step 7: DB-Migration testen**

```python
# tests/test_models.py — hinzufügen:
def test_seed_data_exists(db):
    rows = db.execute("SELECT * FROM produkte").fetchall()
    assert len(rows) == 3
    assert dict(rows[0])["preis_chf"] == 8.0
```

- [ ] **Step 8: Test ausführen**

```bash
uv run pytest tests/test_models.py -v
# Expected: 3 passed
```

- [ ] **Step 9: Commit**

```bash
git add app/database.py app/models.py migrations/ tests/conftest.py tests/test_models.py
git commit -m "feat: SQLite-Datenbank mit Schema, Seed-Daten und Pydantic-Models"
```

---

## Task 3: Produkt-Repository + API-Endpoint

**Files:**
- Create: `app/repositories/produkt_repo.py`
- Create: `tests/test_produkt_repo.py`
- Create: `tests/test_api_produkte.py`
- Create: `app/routers/produkte.py`
- Modify: `app/main.py` (Router einbinden)

- [ ] **Step 1: Failing test für Produkt-Repository**

`tests/test_produkt_repo.py`:
```python
from app.repositories.produkt_repo import get_alle_produkte


def test_get_alle_produkte(db):
    produkte = get_alle_produkte(db)
    assert len(produkte) == 3
    assert produkte[0].name == "Olivenöl 250ml"


def test_get_alle_produkte_nur_aktive(db):
    db.execute("UPDATE produkte SET aktiv = 0 WHERE id = 1")
    db.commit()
    produkte = get_alle_produkte(db)
    assert len(produkte) == 2
```

- [ ] **Step 2: Test ausführen — muss fehlschlagen**

```bash
uv run pytest tests/test_produkt_repo.py -v
# Expected: FAIL — ModuleNotFoundError
```

- [ ] **Step 3: Repository implementieren**

`app/repositories/produkt_repo.py`:
```python
import sqlite3

from app.models import Produkt


def get_alle_produkte(conn: sqlite3.Connection) -> list[Produkt]:
    rows = conn.execute(
        "SELECT id, name, menge_ml, preis_chf, beschreibung, bild_pfad, aktiv "
        "FROM produkte WHERE aktiv = 1 ORDER BY menge_ml"
    ).fetchall()
    return [Produkt(**dict(row)) for row in rows]
```

- [ ] **Step 4: Test ausführen — muss bestehen**

```bash
uv run pytest tests/test_produkt_repo.py -v
# Expected: 2 passed
```

- [ ] **Step 5: Failing test für API-Endpoint**

`tests/test_api_produkte.py`:
```python
def test_startseite_status(client):
    response = client.get("/")
    assert response.status_code == 200


def test_startseite_enthaelt_produkte(client):
    response = client.get("/")
    assert "Olivenöl 250ml" in response.text
    assert "CHF 8" in response.text
```

- [ ] **Step 6: Test ausführen — muss fehlschlagen**

```bash
uv run pytest tests/test_api_produkte.py -v
# Expected: FAIL — 404 Not Found
```

- [ ] **Step 7: Jinja2-Base-Template erstellen**

`templates/base.html`:
```html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Olivalle{% endblock %} — Biologisches Olivenöl</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: { accent: '#f1d600' },
                    fontFamily: { display: ['"Amatic SC"', 'cursive'] },
                }
            }
        }
    </script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Amatic+SC:wght@400;700&display=swap" rel="stylesheet">
</head>
<body class="bg-stone-900 text-white min-h-screen flex flex-col">
    <header class="border-b border-stone-700 py-4">
        <div class="max-w-4xl mx-auto px-4 flex items-center justify-between">
            <a href="/" class="font-display text-4xl font-bold text-accent">Olivalle</a>
            <a href="/warenkorb" class="text-stone-300 hover:text-accent">
                Warenkorb (<span id="cart-count">0</span>)
            </a>
        </div>
    </header>
    <main class="flex-1 max-w-4xl mx-auto px-4 py-8 w-full">
        {% block content %}{% endblock %}
    </main>
    <footer class="border-t border-stone-700 py-6 text-center text-stone-400 text-sm">
        <div class="max-w-4xl mx-auto px-4">
            <p>&copy; Olivalle — Biologisches Olivenöl aus Andalusien</p>
            <p class="mt-1">
                <a href="/impressum" class="hover:text-accent">Impressum</a> ·
                <a href="/datenschutz" class="hover:text-accent">Datenschutz</a> ·
                <a href="/agb" class="hover:text-accent">AGB</a>
            </p>
        </div>
    </footer>
    <script src="/static/js/cart.js"></script>
</body>
</html>
```

- [ ] **Step 8: Produkte-Template erstellen**

`templates/produkte.html`:
```html
{% extends "base.html" %}
{% block title %}Produkte{% endblock %}
{% block content %}
<h1 class="font-display text-5xl font-bold text-accent mb-8">Unser Olivenöl</h1>
<div class="grid gap-6 md:grid-cols-3">
    {% for produkt in produkte %}
    <div class="bg-stone-800 rounded-lg p-6 flex flex-col">
        {% if produkt.bild_pfad %}
        <img src="/static/images/{{ produkt.bild_pfad }}" alt="{{ produkt.name }}"
             class="w-full h-48 object-contain mb-4">
        {% endif %}
        <h2 class="font-display text-2xl font-bold text-accent">{{ produkt.name }}</h2>
        <p class="text-stone-300 mt-2 flex-1">{{ produkt.beschreibung }}</p>
        <div class="mt-4 flex items-center justify-between">
            <span class="text-xl font-bold">CHF {{ "%.2f"|format(produkt.preis_chf) }}</span>
            <button onclick="addToCart({{ produkt.id }}, '{{ produkt.name }}', {{ produkt.preis_chf }})"
                    class="bg-accent text-stone-900 px-4 py-2 rounded font-bold hover:bg-yellow-400">
                In den Warenkorb
            </button>
        </div>
    </div>
    {% endfor %}
</div>
{% endblock %}
```

- [ ] **Step 9: Router implementieren**

`app/routers/produkte.py`:
```python
from fastapi import APIRouter, Request

from app.database import get_db
from app.templating import templates
from app.repositories.produkt_repo import get_alle_produkte

router = APIRouter()


@router.get("/")
def startseite(request: Request):
    conn = get_db()
    try:
        produkte = get_alle_produkte(conn)
    finally:
        conn.close()
    return templates.TemplateResponse(
        request, "produkte.html", {"produkte": produkte}
    )
```

- [ ] **Step 10: Router in main.py einbinden**

`app/main.py` erweitern — nach `templates = ...`:
```python
from app.routers import produkte

app.include_router(produkte.router)
```

Hinweis: `templates` lebt in `app/templating.py` (nicht `app/main.py`), um zirkuläre Imports zu vermeiden.

- [ ] **Step 11: Platzhalter cart.js erstellen (damit Template keine 404 wirft)**

`static/js/cart.js`:
```javascript
// Warenkorb-Logik — wird in Task 4 implementiert
function addToCart(id, name, price) {
    console.log("TODO: addToCart", id, name, price);
}

function updateCartCount() {
    const cart = JSON.parse(localStorage.getItem("olivalle-cart") || "[]");
    const count = cart.reduce((sum, item) => sum + item.menge, 0);
    const el = document.getElementById("cart-count");
    if (el) el.textContent = count;
}

document.addEventListener("DOMContentLoaded", updateCartCount);
```

- [ ] **Step 12: Tests ausführen**

```bash
uv run pytest tests/test_api_produkte.py tests/test_produkt_repo.py -v
# Expected: 4 passed
```

- [ ] **Step 13: Manuell im Browser testen**

```bash
uv run python -c "from app.database import init_db; init_db()"
uv run uvicorn app.main:app --reload --port 8000
# Browser: http://localhost:8000 → 3 Produktkarten sichtbar
```

- [ ] **Step 14: Commit**

```bash
git add app/routers/produkte.py app/repositories/produkt_repo.py templates/ static/js/cart.js tests/test_produkt_repo.py tests/test_api_produkte.py
git commit -m "feat: Produktseite mit Jinja2-Template und Tailwind CSS"
```

---

## Task 4: Warenkorb (Vanilla JS + localStorage)

**Files:**
- Modify: `static/js/cart.js`
- Create: `templates/warenkorb.html`
- Create: `app/routers/warenkorb.py`
- Modify: `app/main.py` (Router einbinden)

Hinweis: Warenkorb ist rein clientseitig (localStorage). Kein Backend-Test nötig für die JS-Logik. Der API-Test prüft nur dass die Seite rendert.

- [ ] **Step 1: cart.js implementieren**

`static/js/cart.js`:
```javascript
const CART_KEY = "olivalle-cart";

function getCart() {
    return JSON.parse(localStorage.getItem(CART_KEY) || "[]");
}

function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
    updateCartCount();
}

function addToCart(id, name, price) {
    const cart = getCart();
    const existing = cart.find((item) => item.produkt_id === id);
    if (existing) {
        existing.menge += 1;
    } else {
        cart.push({ produkt_id: id, name: name, preis: price, menge: 1 });
    }
    saveCart(cart);
}

function removeFromCart(id) {
    const cart = getCart().filter((item) => item.produkt_id !== id);
    saveCart(cart);
    if (typeof renderCart === "function") renderCart();
}

function updateMenge(id, menge) {
    const cart = getCart();
    const item = cart.find((item) => item.produkt_id === id);
    if (item) {
        item.menge = Math.max(1, menge);
    }
    saveCart(cart);
    if (typeof renderCart === "function") renderCart();
}

function updateCartCount() {
    const cart = getCart();
    const count = cart.reduce((sum, item) => sum + item.menge, 0);
    const el = document.getElementById("cart-count");
    if (el) el.textContent = count;
}

function getCartTotal() {
    return getCart().reduce((sum, item) => sum + item.preis * item.menge, 0);
}

function getVersandkosten(total) {
    return total >= 100 ? 0 : 9.90;
}

document.addEventListener("DOMContentLoaded", updateCartCount);
```

- [ ] **Step 2: Warenkorb-Template erstellen**

`templates/warenkorb.html`:
```html
{% extends "base.html" %}
{% block title %}Warenkorb{% endblock %}
{% block content %}
<h1 class="font-display text-5xl font-bold text-accent mb-8">Warenkorb</h1>
<div id="cart-content">
    <p class="text-stone-400">Dein Warenkorb ist leer.</p>
</div>
<template id="cart-template">
    <table class="w-full mb-6">
        <thead>
            <tr class="border-b border-stone-700 text-left">
                <th class="py-2">Produkt</th>
                <th class="py-2 w-24">Menge</th>
                <th class="py-2 w-32 text-right">Preis</th>
                <th class="py-2 w-16"></th>
            </tr>
        </thead>
        <tbody id="cart-items"></tbody>
    </table>
    <div class="border-t border-stone-700 pt-4 text-right">
        <p class="text-stone-400">Versandkosten: CHF <span id="versand">9.90</span></p>
        <p class="text-stone-400 text-sm">(Ab CHF 100 gratis Versand)</p>
        <p class="text-xl font-bold mt-2">Total: CHF <span id="cart-total">0.00</span></p>
        <a href="/checkout" class="inline-block mt-4 bg-accent text-stone-900 px-6 py-3 rounded font-bold hover:bg-yellow-400">
            Zur Kasse
        </a>
    </div>
</template>
<script>
function renderCart() {
    const cart = getCart();
    const container = document.getElementById("cart-content");
    if (cart.length === 0) {
        container.innerHTML = '<p class="text-stone-400">Dein Warenkorb ist leer.</p>';
        return;
    }
    const tmpl = document.getElementById("cart-template").content.cloneNode(true);
    const tbody = tmpl.querySelector("#cart-items");
    cart.forEach(item => {
        const tr = document.createElement("tr");
        tr.className = "border-b border-stone-800";
        tr.innerHTML = `
            <td class="py-3">${item.name}</td>
            <td class="py-3">
                <input type="number" min="1" value="${item.menge}"
                       onchange="updateMenge(${item.produkt_id}, parseInt(this.value))"
                       class="w-16 bg-stone-800 border border-stone-600 rounded px-2 py-1 text-center">
            </td>
            <td class="py-3 text-right">CHF ${(item.preis * item.menge).toFixed(2)}</td>
            <td class="py-3 text-right">
                <button onclick="removeFromCart(${item.produkt_id})" class="text-red-400 hover:text-red-300">✕</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    const subtotal = getCartTotal();
    const versand = getVersandkosten(subtotal);
    tmpl.querySelector("#versand").textContent = versand.toFixed(2);
    tmpl.querySelector("#cart-total").textContent = (subtotal + versand).toFixed(2);
    container.innerHTML = "";
    container.appendChild(tmpl);
}
document.addEventListener("DOMContentLoaded", renderCart);
</script>
{% endblock %}
```

- [ ] **Step 3: Warenkorb-Router erstellen**

`app/routers/warenkorb.py`:
```python
from fastapi import APIRouter, Request

from app.templating import templates

router = APIRouter()


@router.get("/warenkorb")
def warenkorb(request: Request):
    return templates.TemplateResponse(request, "warenkorb.html")
```

- [ ] **Step 4: Router in main.py einbinden**

```python
from app.routers import produkte, warenkorb

app.include_router(produkte.router)
app.include_router(warenkorb.router)
```

- [ ] **Step 5: API-Test**

```python
# tests/test_api_produkte.py — hinzufügen:
def test_warenkorb_seite(client):
    response = client.get("/warenkorb")
    assert response.status_code == 200
    assert "Warenkorb" in response.text
```

- [ ] **Step 6: Tests ausführen**

```bash
uv run pytest tests/test_api_produkte.py -v
# Expected: 3 passed
```

- [ ] **Step 7: Manuell testen**

```bash
uv run uvicorn app.main:app --reload --port 8000
# Browser: Produkt hinzufügen → /warenkorb → Artikel sichtbar
```

- [ ] **Step 8: Commit**

```bash
git add static/js/cart.js templates/warenkorb.html app/routers/warenkorb.py app/main.py tests/test_api_produkte.py
git commit -m "feat: Warenkorb mit Vanilla JS und localStorage"
```

---

## Task 5: Bestellservice + Preisberechnung

**Files:**
- Create: `app/services/bestell_service.py`
- Create: `app/repositories/bestell_repo.py`
- Create: `tests/test_bestell_service.py`

- [ ] **Step 1: Failing test für Preisberechnung**

`tests/test_bestell_service.py`:
```python
import pytest

from app.models import WarenkorbItem
from app.services.bestell_service import berechne_total, berechne_versandkosten


def test_versandkosten_unter_100():
    assert berechne_versandkosten(99.99) == 9.90


def test_versandkosten_ab_100_gratis():
    assert berechne_versandkosten(100.0) == 0.0


def test_versandkosten_abholung():
    assert berechne_versandkosten(50.0, versandart="abholung") == 0.0


def test_berechne_total(db):
    items = [
        WarenkorbItem(produkt_id=1, menge=2),  # 2x CHF 8 = 16
        WarenkorbItem(produkt_id=2, menge=1),  # 1x CHF 18 = 18
    ]
    total, positionen = berechne_total(db, items)
    assert total == 34.0
    assert len(positionen) == 2


def test_berechne_total_ungueltige_produkt_id(db):
    items = [WarenkorbItem(produkt_id=999, menge=1)]
    with pytest.raises(ValueError, match="Produkt 999 nicht gefunden"):
        berechne_total(db, items)
```

- [ ] **Step 2: Test ausführen — muss fehlschlagen**

```bash
uv run pytest tests/test_bestell_service.py -v
# Expected: FAIL — ModuleNotFoundError
```

- [ ] **Step 3: bestell_service.py implementieren**

```python
import sqlite3

from app.models import WarenkorbItem


def berechne_versandkosten(
    warenwert: float, versandart: str = "versand"
) -> float:
    if versandart == "abholung":
        return 0.0
    return 0.0 if warenwert >= 100 else 9.90


def berechne_total(
    conn: sqlite3.Connection, items: list[WarenkorbItem]
) -> tuple[float, list[dict]]:
    """Validiert Items gegen DB und berechnet Total.

    Returns: (total, positionen) wobei positionen eine Liste von
    {"produkt_id", "menge", "einzelpreis_chf"} ist.
    """
    positionen = []
    total = 0.0
    for item in items:
        row = conn.execute(
            "SELECT id, preis_chf FROM produkte WHERE id = ? AND aktiv = 1",
            (item.produkt_id,),
        ).fetchone()
        if not row:
            raise ValueError(f"Produkt {item.produkt_id} nicht gefunden")
        preis = row["preis_chf"]
        positionen.append(
            {
                "produkt_id": item.produkt_id,
                "menge": item.menge,
                "einzelpreis_chf": preis,
            }
        )
        total += preis * item.menge
    return total, positionen
```

- [ ] **Step 4: Test ausführen — muss bestehen**

```bash
uv run pytest tests/test_bestell_service.py -v
# Expected: 5 passed
```

- [ ] **Step 5: Failing test für Bestell-Repository**

`tests/test_bestell_repo.py` (neue Datei):
```python
from app.models import KundeInput
from app.repositories.bestell_repo import kunde_anlegen, bestellung_anlegen


def test_kunde_anlegen(db):
    kunde = KundeInput(
        vorname="Max", nachname="Muster", email="max@test.ch",
        strasse="Musterstr. 1", plz="4600", ort="Olten",
    )
    kunde_id = kunde_anlegen(db, kunde)
    assert kunde_id == 1


def test_bestellung_anlegen(db):
    kunde = KundeInput(
        vorname="Max", nachname="Muster", email="max@test.ch",
        strasse="Musterstr. 1", plz="4600", ort="Olten",
    )
    kunde_id = kunde_anlegen(db, kunde)
    positionen = [
        {"produkt_id": 1, "menge": 2, "einzelpreis_chf": 8.0},
    ]
    bestell_id = bestellung_anlegen(
        db, kunde_id=kunde_id, positionen=positionen,
        zahlungsart="stripe", versandart="versand",
        versandkosten=9.90, total=25.90, kommentar="",
    )
    assert bestell_id == 1
    row = db.execute("SELECT * FROM bestellungen WHERE id = ?", (bestell_id,)).fetchone()
    assert dict(row)["total_chf"] == 25.90
```

- [ ] **Step 6: Test ausführen — muss fehlschlagen**

```bash
uv run pytest tests/test_bestell_repo.py -v
# Expected: FAIL
```

- [ ] **Step 7: bestell_repo.py implementieren**

```python
import sqlite3

from app.models import KundeInput


def kunde_anlegen(conn: sqlite3.Connection, kunde: KundeInput) -> int:
    cursor = conn.execute(
        "INSERT INTO kunden (vorname, nachname, email, telefon, strasse, plz, ort) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (kunde.vorname, kunde.nachname, kunde.email, kunde.telefon,
         kunde.strasse, kunde.plz, kunde.ort),
    )
    conn.commit()
    return cursor.lastrowid


def bestellung_anlegen(
    conn: sqlite3.Connection,
    *,
    kunde_id: int,
    positionen: list[dict],
    zahlungsart: str,
    versandart: str,
    versandkosten: float,
    total: float,
    kommentar: str = "",
    stripe_session_id: str | None = None,
) -> int:
    cursor = conn.execute(
        "INSERT INTO bestellungen "
        "(kunde_id, zahlungsart, versandart, versandkosten_chf, total_chf, kommentar, stripe_session_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (kunde_id, zahlungsart, versandart, versandkosten, total, kommentar, stripe_session_id),
    )
    bestell_id = cursor.lastrowid
    for pos in positionen:
        conn.execute(
            "INSERT INTO bestellpositionen (bestellung_id, produkt_id, menge, einzelpreis_chf) "
            "VALUES (?, ?, ?, ?)",
            (bestell_id, pos["produkt_id"], pos["menge"], pos["einzelpreis_chf"]),
        )
    conn.commit()
    return bestell_id
```

- [ ] **Step 8: Test ausführen — muss bestehen**

```bash
uv run pytest tests/test_bestell_repo.py tests/test_bestell_service.py -v
# Expected: 7 passed
```

- [ ] **Step 9: Commit**

```bash
git add app/services/bestell_service.py app/repositories/bestell_repo.py tests/test_bestell_service.py tests/test_bestell_repo.py
git commit -m "feat: Bestellservice mit Preisberechnung und Versandkosten-Logik"
```

---

## Task 6: Checkout-Formular + Bestellungserstellung

**Files:**
- Create: `templates/checkout.html`
- Create: `templates/bestaetigung.html`
- Create: `app/routers/bestellungen.py`
- Create: `tests/test_api_bestellungen.py`
- Modify: `app/main.py` (Router einbinden)

- [ ] **Step 1: Checkout-Template erstellen**

`templates/checkout.html`:
```html
{% extends "base.html" %}
{% block title %}Kasse{% endblock %}
{% block content %}
<h1 class="font-display text-5xl font-bold text-accent mb-8">Kasse</h1>
<form method="POST" action="/bestellen" id="checkout-form" class="max-w-lg">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <input type="hidden" name="cart_data" id="cart-data">

    <h2 class="text-xl font-bold mb-4">Lieferadresse</h2>
    <div class="grid grid-cols-2 gap-4 mb-6">
        <div>
            <label class="block text-stone-400 text-sm mb-1">Vorname *</label>
            <input type="text" name="vorname" required
                   class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
        </div>
        <div>
            <label class="block text-stone-400 text-sm mb-1">Nachname *</label>
            <input type="text" name="nachname" required
                   class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
        </div>
        <div class="col-span-2">
            <label class="block text-stone-400 text-sm mb-1">E-Mail *</label>
            <input type="email" name="email" required
                   class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
        </div>
        <div class="col-span-2">
            <label class="block text-stone-400 text-sm mb-1">Strasse *</label>
            <input type="text" name="strasse" required
                   class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
        </div>
        <div>
            <label class="block text-stone-400 text-sm mb-1">PLZ *</label>
            <input type="text" name="plz" required pattern="[0-9]{4}"
                   class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
        </div>
        <div>
            <label class="block text-stone-400 text-sm mb-1">Ort *</label>
            <input type="text" name="ort" required
                   class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
        </div>
        <div class="col-span-2">
            <label class="block text-stone-400 text-sm mb-1">Telefon</label>
            <input type="tel" name="telefon"
                   class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
        </div>
    </div>

    <h2 class="text-xl font-bold mb-4">Versand</h2>
    <div class="mb-6 space-y-2">
        <label class="flex items-center gap-2">
            <input type="radio" name="versandart" value="versand" checked
                   class="text-accent"> Postversand (CHF 9.90, ab CHF 100 gratis)
        </label>
        <label class="flex items-center gap-2">
            <input type="radio" name="versandart" value="abholung"
                   class="text-accent"> Abholung vor Ort (Details per E-Mail)
        </label>
    </div>

    <h2 class="text-xl font-bold mb-4">Zahlung</h2>
    <div class="mb-6 space-y-2">
        <label class="flex items-center gap-2">
            <input type="radio" name="zahlungsart" value="stripe" checked
                   class="text-accent"> Twint / Kreditkarte (via Stripe)
        </label>
        <label class="flex items-center gap-2">
            <input type="radio" name="zahlungsart" value="rechnung"
                   class="text-accent"> Auf Rechnung (QR-Rechnung per E-Mail)
        </label>
    </div>

    <div class="mb-6">
        <label class="block text-stone-400 text-sm mb-1">Kommentar</label>
        <textarea name="kommentar" rows="3"
                  class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2"></textarea>
    </div>

    <button type="submit"
            class="w-full bg-accent text-stone-900 py-3 rounded font-bold text-lg hover:bg-yellow-400">
        Kostenpflichtig bestellen
    </button>
</form>
<script>
document.getElementById("checkout-form").addEventListener("submit", function() {
    document.getElementById("cart-data").value = JSON.stringify(getCart());
});
</script>
{% endblock %}
```

- [ ] **Step 2: Bestätigungs-Template erstellen**

`templates/bestaetigung.html`:
```html
{% extends "base.html" %}
{% block title %}Bestellbestätigung{% endblock %}
{% block content %}
<div class="max-w-lg mx-auto text-center">
    <h1 class="font-display text-5xl font-bold text-accent mb-4">Vielen Dank!</h1>
    <p class="text-lg text-stone-300 mb-2">Deine Bestellung #{{ bestell_id }} wurde erfolgreich aufgenommen.</p>
    {% if zahlungsart == "rechnung" %}
    <p class="text-stone-400">Du erhältst in Kürze eine E-Mail mit der QR-Rechnung.</p>
    {% else %}
    <p class="text-stone-400">Du erhältst in Kürze eine Bestellbestätigung per E-Mail.</p>
    {% endif %}
    <a href="/" class="inline-block mt-8 text-accent hover:underline">Zurück zum Shop</a>
</div>
<script>localStorage.removeItem("olivalle-cart");</script>
{% endblock %}
```

- [ ] **Step 3: Failing test für Bestell-API**

`tests/test_api_bestellungen.py`:
```python
import json


def test_checkout_seite(client):
    response = client.get("/checkout")
    assert response.status_code == 200
    assert "Kasse" in response.text


def test_bestellen_ohne_cart_data(client):
    response = client.post("/bestellen", data={
        "vorname": "Max", "nachname": "Muster",
        "email": "max@test.ch", "strasse": "Str. 1",
        "plz": "4600", "ort": "Olten",
        "versandart": "versand", "zahlungsart": "rechnung",
        "cart_data": "[]", "kommentar": "",
        "csrf_token": "test",
    })
    assert response.status_code == 400


def test_bestellen_rechnung_erfolgreich(client):
    cart = json.dumps([{"produkt_id": 1, "menge": 2}])
    response = client.post("/bestellen", data={
        "vorname": "Max", "nachname": "Muster",
        "email": "max@test.ch", "strasse": "Str. 1",
        "plz": "4600", "ort": "Olten",
        "versandart": "versand", "zahlungsart": "rechnung",
        "cart_data": cart, "kommentar": "Testbestellung",
        "csrf_token": "test",
    }, follow_redirects=False)
    # Redirect to Bestätigung oder direkte Anzeige
    assert response.status_code in (200, 303)
```

- [ ] **Step 4: Test ausführen — muss fehlschlagen**

```bash
uv run pytest tests/test_api_bestellungen.py -v
# Expected: FAIL — 404
```

- [ ] **Step 5: Bestell-Router implementieren**

`app/routers/bestellungen.py`:
```python
import json

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.database import get_db
from app.templating import templates
from app.models import KundeInput, WarenkorbItem
from app.repositories.bestell_repo import bestellung_anlegen, kunde_anlegen
from app.services.bestell_service import berechne_total, berechne_versandkosten

router = APIRouter()


@router.get("/checkout")
def checkout_seite(request: Request):
    return templates.TemplateResponse(
        request, "checkout.html", {"csrf_token": "TODO"}
    )


@router.post("/bestellen")
def bestellen(
    request: Request,
    vorname: str = Form(),
    nachname: str = Form(),
    email: str = Form(),
    strasse: str = Form(),
    plz: str = Form(),
    ort: str = Form(),
    telefon: str = Form(""),
    versandart: str = Form(),
    zahlungsart: str = Form(),
    cart_data: str = Form(),
    kommentar: str = Form(""),
    csrf_token: str = Form(""),
):
    # Parse Warenkorb
    try:
        raw_items = json.loads(cart_data)
    except json.JSONDecodeError:
        raise HTTPException(400, "Ungültige Warenkorb-Daten")

    if not raw_items:
        raise HTTPException(400, "Warenkorb ist leer")

    items = [WarenkorbItem(produkt_id=i["produkt_id"], menge=i["menge"]) for i in raw_items]

    kunde_input = KundeInput(
        vorname=vorname, nachname=nachname, email=email,
        telefon=telefon, strasse=strasse, plz=plz, ort=ort,
    )

    conn = get_db()
    try:
        # Preise serverseitig validieren
        total, positionen = berechne_total(conn, items)
        versandkosten = berechne_versandkosten(total, versandart)
        gesamt = total + versandkosten

        # Kunde + Bestellung speichern
        kunde_id = kunde_anlegen(conn, kunde_input)
        bestell_id = bestellung_anlegen(
            conn, kunde_id=kunde_id, positionen=positionen,
            zahlungsart=zahlungsart, versandart=versandart,
            versandkosten=versandkosten, total=gesamt,
            kommentar=kommentar,
        )

        if zahlungsart == "stripe":
            # Stripe Checkout Session → wird in Task 7 implementiert
            # Vorerst: Redirect zur Bestätigung
            pass

        return templates.TemplateResponse(
            request, "bestaetigung.html",
            {"bestell_id": bestell_id, "zahlungsart": zahlungsart},
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    finally:
        conn.close()


@router.get("/bestaetigung")
def bestaetigung_seite(request: Request, session_id: str = ""):
    """GET-Endpoint für Stripe-Redirect-Rückkehr nach erfolgreicher Zahlung."""
    conn = get_db()
    try:
        if session_id:
            row = conn.execute(
                "SELECT id, zahlungsart FROM bestellungen WHERE stripe_session_id = ?",
                (session_id,),
            ).fetchone()
            if row:
                return templates.TemplateResponse(
                    request, "bestaetigung.html",
                    {"bestell_id": dict(row)["id"], "zahlungsart": dict(row)["zahlungsart"]},
                )
        return templates.TemplateResponse(
            request, "bestaetigung.html",
            {"bestell_id": "?", "zahlungsart": "stripe"},
        )
    finally:
        conn.close()
```

- [ ] **Step 6: Router in main.py einbinden**

```python
from app.routers import produkte, warenkorb, bestellungen

app.include_router(bestellungen.router)
```

- [ ] **Step 7: Tests ausführen**

```bash
uv run pytest tests/test_api_bestellungen.py -v
# Expected: 3 passed
```

- [ ] **Step 8: Commit**

```bash
git add templates/checkout.html templates/bestaetigung.html app/routers/bestellungen.py tests/test_api_bestellungen.py app/main.py
git commit -m "feat: Checkout-Formular mit Bestellungserstellung und serverseitiger Validierung"
```

---

## Task 7: Stripe Checkout Integration

**Files:**
- Create: `app/services/stripe_service.py`
- Create: `app/routers/webhooks.py`
- Create: `tests/test_stripe_service.py`
- Create: `tests/test_api_webhooks.py`
- Modify: `app/routers/bestellungen.py` (Stripe-Redirect einbauen)
- Modify: `app/main.py` (Webhook-Router einbinden)

- [ ] **Step 1: Failing test für Stripe-Service**

`tests/test_stripe_service.py`:
```python
from unittest.mock import MagicMock, patch

from app.services.stripe_service import erstelle_checkout_session


@patch("app.services.stripe_service.stripe")
def test_erstelle_checkout_session(mock_stripe):
    mock_stripe.checkout.Session.create.return_value = MagicMock(
        id="cs_test_123", url="https://checkout.stripe.com/test"
    )
    session = erstelle_checkout_session(
        positionen=[
            {"produkt_id": 1, "menge": 2, "einzelpreis_chf": 8.0, "name": "Olivenöl 250ml"},
        ],
        versandkosten=9.90,
        bestell_id=1,
    )
    assert session.url == "https://checkout.stripe.com/test"
    mock_stripe.checkout.Session.create.assert_called_once()
    call_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
    assert len(call_kwargs["line_items"]) == 2  # 1 Produkt + Versand
```

- [ ] **Step 2: Test ausführen — muss fehlschlagen**

```bash
uv run pytest tests/test_stripe_service.py -v
# Expected: FAIL
```

- [ ] **Step 3: stripe_service.py implementieren**

```python
import stripe

from app.config import settings

stripe.api_key = settings.stripe_secret_key


def erstelle_checkout_session(
    positionen: list[dict],
    versandkosten: float,
    bestell_id: int,
) -> stripe.checkout.Session:
    line_items = []
    for pos in positionen:
        line_items.append({
            "price_data": {
                "currency": "chf",
                "product_data": {"name": pos["name"]},
                "unit_amount": int(pos["einzelpreis_chf"] * 100),
            },
            "quantity": pos["menge"],
        })

    if versandkosten > 0:
        line_items.append({
            "price_data": {
                "currency": "chf",
                "product_data": {"name": "Versandkosten"},
                "unit_amount": int(versandkosten * 100),
            },
            "quantity": 1,
        })

    return stripe.checkout.Session.create(
        payment_method_types=["card", "twint"],
        line_items=line_items,
        mode="payment",
        success_url=f"{settings.base_url}/bestaetigung?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.base_url}/checkout",
        metadata={"bestell_id": str(bestell_id)},
    )
```

- [ ] **Step 4: Test ausführen — muss bestehen**

```bash
uv run pytest tests/test_stripe_service.py -v
# Expected: 1 passed
```

- [ ] **Step 5: Stripe-Redirect in bestellungen.py einbauen**

In `app/routers/bestellungen.py`, den `if zahlungsart == "stripe"` Block ersetzen:

```python
        if zahlungsart == "stripe":
            from app.services.stripe_service import erstelle_checkout_session
            # Produktnamen für Stripe holen
            for pos in positionen:
                row = conn.execute(
                    "SELECT name FROM produkte WHERE id = ?", (pos["produkt_id"],)
                ).fetchone()
                pos["name"] = row["name"]
            session = erstelle_checkout_session(
                positionen=positionen,
                versandkosten=versandkosten,
                bestell_id=bestell_id,
            )
            conn.execute(
                "UPDATE bestellungen SET stripe_session_id = ? WHERE id = ?",
                (session.id, bestell_id),
            )
            conn.commit()
            return RedirectResponse(session.url, status_code=303)
```

- [ ] **Step 6: Failing test für Webhook**

`tests/test_api_webhooks.py`:
```python
from unittest.mock import patch, MagicMock


@patch("app.services.email_service.resend.Emails.send", return_value={"id": "test"})
@patch("app.routers.webhooks.stripe.Webhook.construct_event")
def test_webhook_checkout_completed(mock_construct, mock_email, client, db):
    # Testbestellung anlegen
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('Max', 'Muster', 'max@test.ch', 'Str 1', '4600', 'Olten')"
    )
    db.execute(
        "INSERT INTO bestellungen (kunde_id, zahlungsart, versandart, total_chf, stripe_session_id, status) "
        "VALUES (1, 'stripe', 'versand', 25.90, 'cs_test_123', 'neu')"
    )
    db.commit()

    mock_construct.return_value = MagicMock(
        type="checkout.session.completed",
        data=MagicMock(object=MagicMock(id="cs_test_123")),
    )

    response = client.post(
        "/webhook/stripe",
        content=b'{"type": "checkout.session.completed"}',
        headers={"stripe-signature": "test_sig"},
    )
    assert response.status_code == 200

    row = db.execute("SELECT status FROM bestellungen WHERE id = 1").fetchone()
    assert dict(row)["status"] == "bezahlt"
```

- [ ] **Step 7: Test ausführen — muss fehlschlagen**

```bash
uv run pytest tests/test_api_webhooks.py -v
# Expected: FAIL — 404
```

- [ ] **Step 8: Webhook-Router implementieren**

`app/routers/webhooks.py`:
```python
import stripe
from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.database import get_db

router = APIRouter()


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.stripe_webhook_secret
        )
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(400, "Ungültige Webhook-Signatur")

    if event.type == "checkout.session.completed":
        session = event.data.object
        conn = get_db()
        try:
            conn.execute(
                "UPDATE bestellungen SET status = 'bezahlt' "
                "WHERE stripe_session_id = ?",
                (session.id,),
            )
            conn.commit()
            # TODO (Task 8): E-Mail senden
            # TODO (Task 9): QR-Rechnung generieren falls nötig
        finally:
            conn.close()

    return {"status": "ok"}
```

- [ ] **Step 9: Router in main.py einbinden**

```python
from app.routers import produkte, warenkorb, bestellungen, webhooks

app.include_router(webhooks.router)
```

- [ ] **Step 10: Tests ausführen**

```bash
uv run pytest tests/test_stripe_service.py tests/test_api_webhooks.py -v
# Expected: 2 passed
```

- [ ] **Step 11: Commit**

```bash
git add app/services/stripe_service.py app/routers/webhooks.py app/routers/bestellungen.py tests/test_stripe_service.py tests/test_api_webhooks.py app/main.py
git commit -m "feat: Stripe Checkout Integration mit Webhook-Verarbeitung"
```

---

## Task 8: E-Mail via Resend

**Files:**
- Create: `app/services/email_service.py`
- Create: `templates/emails/bestellbestaetigung.html`
- Create: `tests/test_email_service.py`
- Modify: `app/routers/webhooks.py` (E-Mail nach Zahlung senden)

- [ ] **Step 1: E-Mail-Template erstellen**

`templates/emails/bestellbestaetigung.html`:
```html
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
    <h1 style="color: #f1d600;">Bestellbestätigung</h1>
    <p>Hallo {{ kunde.vorname }},</p>
    <p>vielen Dank für deine Bestellung bei Olivalle!</p>

    <h2>Bestellung #{{ bestell_id }}</h2>
    <table style="width: 100%; border-collapse: collapse;">
        {% for pos in positionen %}
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 8px;">{{ pos.name }}</td>
            <td style="padding: 8px; text-align: right;">{{ pos.menge }}x</td>
            <td style="padding: 8px; text-align: right;">CHF {{ "%.2f"|format(pos.einzelpreis_chf * pos.menge) }}</td>
        </tr>
        {% endfor %}
        {% if versandkosten > 0 %}
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 8px;" colspan="2">Versandkosten</td>
            <td style="padding: 8px; text-align: right;">CHF {{ "%.2f"|format(versandkosten) }}</td>
        </tr>
        {% endif %}
        <tr>
            <td style="padding: 8px; font-weight: bold;" colspan="2">Total</td>
            <td style="padding: 8px; text-align: right; font-weight: bold;">CHF {{ "%.2f"|format(total) }}</td>
        </tr>
    </table>

    <p style="margin-top: 20px;">Liebe Grüsse<br>Olivalle</p>
</body>
</html>
```

- [ ] **Step 2: Failing test für E-Mail-Service**

`tests/test_email_service.py`:
```python
from unittest.mock import patch, MagicMock

from app.services.email_service import sende_bestellbestaetigung


@patch("app.services.email_service.resend.Emails.send")
def test_sende_bestellbestaetigung(mock_send):
    mock_send.return_value = {"id": "email_123"}
    result = sende_bestellbestaetigung(
        empfaenger="max@test.ch",
        bestell_id=1,
        kunde={"vorname": "Max", "nachname": "Muster"},
        positionen=[{"name": "Olivenöl 250ml", "menge": 2, "einzelpreis_chf": 8.0}],
        versandkosten=9.90,
        total=25.90,
    )
    assert result is not None
    mock_send.assert_called_once()
    call_kwargs = mock_send.call_args.kwargs
    assert call_kwargs["to"] == ["max@test.ch"]
    assert "Bestellbestätigung" in call_kwargs["subject"]
```

- [ ] **Step 3: Test ausführen — muss fehlschlagen**

```bash
uv run pytest tests/test_email_service.py -v
# Expected: FAIL
```

- [ ] **Step 4: email_service.py implementieren**

```python
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
) -> dict:
    template = env.get_template("bestellbestaetigung.html")
    html = template.render(
        kunde=kunde, bestell_id=bestell_id,
        positionen=positionen, versandkosten=versandkosten, total=total,
    )

    params = {
        "from": "Olivalle <bestellung@olivalle.ch>",
        "to": [empfaenger],
        "reply_to": "olivalle.olten@outlook.com",
        "subject": f"Olivalle — Bestellbestätigung #{bestell_id}",
        "html": html,
    }

    if anhang:
        import base64
        params["attachments"] = [{
            "filename": f"rechnung-{bestell_id}.svg",
            "content": list(anhang),
        }]

    return resend.Emails.send(**params)
```

- [ ] **Step 5: Test ausführen — muss bestehen**

```bash
uv run pytest tests/test_email_service.py -v
# Expected: 1 passed
```

- [ ] **Step 6: E-Mail in Webhook einbauen**

In `app/routers/webhooks.py`, nach `conn.commit()` den TODO ersetzen:

```python
            # Bestelldetails für E-Mail laden
            bestellung = conn.execute(
                "SELECT b.*, k.vorname, k.nachname, k.email "
                "FROM bestellungen b JOIN kunden k ON b.kunde_id = k.id "
                "WHERE b.stripe_session_id = ?",
                (session.id,),
            ).fetchone()
            if bestellung:
                best = dict(bestellung)
                positionen = conn.execute(
                    "SELECT bp.*, p.name FROM bestellpositionen bp "
                    "JOIN produkte p ON bp.produkt_id = p.id "
                    "WHERE bp.bestellung_id = ?",
                    (best["id"],),
                ).fetchall()
                from app.services.email_service import sende_bestellbestaetigung
                sende_bestellbestaetigung(
                    empfaenger=best["email"],
                    bestell_id=best["id"],
                    kunde={"vorname": best["vorname"], "nachname": best["nachname"]},
                    positionen=[dict(p) for p in positionen],
                    versandkosten=best["versandkosten_chf"],
                    total=best["total_chf"],
                )
```

- [ ] **Step 7: Commit**

```bash
git add app/services/email_service.py templates/emails/ tests/test_email_service.py app/routers/webhooks.py
git commit -m "feat: Bestellbestätigung per E-Mail via Resend"
```

---

## Task 9: QR-Rechnung (swiss-qr-bill)

**Files:**
- Create: `app/services/qr_service.py`
- Create: `tests/test_qr_service.py`
- Modify: `app/routers/bestellungen.py` (QR-Rechnung bei Rechnungskauf generieren + per E-Mail senden)

- [ ] **Step 1: Failing test für QR-Service**

`tests/test_qr_service.py`:
```python
from app.services.qr_service import generiere_qr_rechnung


def test_generiere_qr_rechnung(monkeypatch):
    # QR-Settings für Tests setzen
    monkeypatch.setattr("app.config.settings.qr_iban", "CH4431999123000889012")
    monkeypatch.setattr("app.config.settings.qr_name", "Test GmbH")
    monkeypatch.setattr("app.config.settings.qr_address", "Teststr. 1")
    monkeypatch.setattr("app.config.settings.qr_zip", "3000")
    monkeypatch.setattr("app.config.settings.qr_city", "Bern")

    svg_bytes = generiere_qr_rechnung(
        betrag=25.90,
        bestell_id=1,
        kunde_name="Max Muster",
        kunde_adresse="Musterstr. 1",
        kunde_plz="4600",
        kunde_ort="Olten",
    )
    assert isinstance(svg_bytes, bytes)
    assert len(svg_bytes) > 100
    assert b"<svg" in svg_bytes or svg_bytes[:4] == b"%PDF"
```

- [ ] **Step 2: Test ausführen — muss fehlschlagen**

```bash
uv run pytest tests/test_qr_service.py -v
# Expected: FAIL
```

- [ ] **Step 3: qr_service.py implementieren**

```python
from io import BytesIO

from qrbill import QRBill

from app.config import settings


def generiere_qr_rechnung(
    betrag: float,
    bestell_id: int,
    kunde_name: str,
    kunde_adresse: str,
    kunde_plz: str,
    kunde_ort: str,
) -> bytes:
    bill = QRBill(
        account=settings.qr_iban,
        creditor={
            "name": settings.qr_name,
            "street": settings.qr_address,
            "pcode": settings.qr_zip,
            "city": settings.qr_city,
            "country": "CH",
        },
        debtor={
            "name": kunde_name,
            "street": kunde_adresse,
            "pcode": kunde_plz,
            "city": kunde_ort,
            "country": "CH",
        },
        amount=f"{betrag:.2f}",
        currency="CHF",
        additional_information=f"Bestellung #{bestell_id}",
    )
    buffer = BytesIO()
    bill.as_svg(buffer)
    return buffer.getvalue()
```

Hinweis: Die `qrbill`-Bibliothek erzeugt SVG. Falls PDF nötig: svglib + reportlab einsetzen. Für den Start reicht SVG als Anhang (Browser kann SVG anzeigen). Falls PDF zwingend: als separater Schritt nachrüsten.

- [ ] **Step 4: Test ausführen — muss bestehen**

```bash
uv run pytest tests/test_qr_service.py -v
# Expected: 1 passed
```

Hinweis: Test braucht gültige QR_IBAN in `.env` oder Test-Fixture. Falls fehlschlägt: `monkeypatch` in conftest.py für QR-Settings ergänzen.

- [ ] **Step 5: QR-Rechnung bei Rechnungskauf in bestellungen.py einbauen**

In `app/routers/bestellungen.py`, nach der Bestellungserstellung und vor dem Template-Return für `zahlungsart != "stripe"`:

```python
        if zahlungsart == "rechnung":
            from app.services.qr_service import generiere_qr_rechnung
            from app.services.email_service import sende_bestellbestaetigung
            qr_pdf = generiere_qr_rechnung(
                betrag=gesamt,
                bestell_id=bestell_id,
                kunde_name=f"{kunde_input.vorname} {kunde_input.nachname}",
                kunde_adresse=kunde_input.strasse,
                kunde_plz=kunde_input.plz,
                kunde_ort=kunde_input.ort,
            )
            # Produktnamen für E-Mail holen
            for pos in positionen:
                row = conn.execute(
                    "SELECT name FROM produkte WHERE id = ?", (pos["produkt_id"],)
                ).fetchone()
                pos["name"] = row["name"]
            sende_bestellbestaetigung(
                empfaenger=kunde_input.email,
                bestell_id=bestell_id,
                kunde={"vorname": kunde_input.vorname, "nachname": kunde_input.nachname},
                positionen=positionen,
                versandkosten=versandkosten,
                total=gesamt,
                anhang=qr_pdf,
            )
```

- [ ] **Step 6: Tests ausführen (alle)**

```bash
uv run pytest -v
# Expected: all passed
```

- [ ] **Step 7: Commit**

```bash
git add app/services/qr_service.py tests/test_qr_service.py app/routers/bestellungen.py
git commit -m "feat: QR-Rechnung via swiss-qr-bill mit E-Mail-Versand"
```

---

## Task 10: CSRF-Schutz

**Files:**
- Create: `app/csrf.py`
- Create: `tests/test_csrf.py`
- Modify: `app/main.py` (Middleware einbinden)
- Modify: `app/routers/bestellungen.py` (CSRF-Token generieren + validieren)
- Modify: `templates/checkout.html` (Token einfügen)

- [ ] **Step 1: Failing test**

`tests/test_csrf.py`:
```python
from app.csrf import generiere_csrf_token, validiere_csrf_token


def test_csrf_token_roundtrip():
    token = generiere_csrf_token("test-secret")
    assert validiere_csrf_token(token, "test-secret")


def test_csrf_token_ungueltig():
    assert not validiere_csrf_token("fake-token", "test-secret")


def test_csrf_token_abgelaufen():
    # Token mit max_age=0 sofort abgelaufen
    token = generiere_csrf_token("test-secret", max_age=0)
    import time; time.sleep(0.1)
    assert not validiere_csrf_token(token, "test-secret", max_age=0)
```

- [ ] **Step 2: Test ausführen — muss fehlschlagen**

```bash
uv run pytest tests/test_csrf.py -v
# Expected: FAIL
```

- [ ] **Step 3: csrf.py implementieren**

```python
import time

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def generiere_csrf_token(secret: str, max_age: int = 3600) -> str:
    s = URLSafeTimedSerializer(secret)
    return s.dumps("csrf")


def validiere_csrf_token(
    token: str, secret: str, max_age: int = 3600
) -> bool:
    s = URLSafeTimedSerializer(secret)
    try:
        s.loads(token, max_age=max_age)
        return True
    except (BadSignature, SignatureExpired):
        return False
```

- [ ] **Step 4: Test ausführen — muss bestehen**

```bash
uv run pytest tests/test_csrf.py -v
# Expected: 3 passed
```

- [ ] **Step 5: CSRF in Checkout-Router einbauen**

In `app/routers/bestellungen.py`:
- GET `/checkout`: Token generieren und an Template übergeben
- POST `/bestellen`: Token validieren, bei Fehler 403 zurückgeben

```python
from app.csrf import generiere_csrf_token, validiere_csrf_token
from app.config import settings

# In checkout_seite():
    csrf_token = generiere_csrf_token(settings.secret_key)
    return templates.TemplateResponse(
        request, "checkout.html", {"csrf_token": csrf_token}
    )

# In bestellen(), am Anfang:
    if not validiere_csrf_token(csrf_token, settings.secret_key):
        raise HTTPException(403, "Ungültiges CSRF-Token")
```

- [ ] **Step 6: Test: POST ohne gültiges Token wird abgelehnt**

```python
# tests/test_csrf.py — hinzufügen:
def test_bestellen_ohne_csrf_abgelehnt(client):
    import json
    cart = json.dumps([{"produkt_id": 1, "menge": 1}])
    response = client.post("/bestellen", data={
        "vorname": "Max", "nachname": "Muster",
        "email": "max@test.ch", "strasse": "Str. 1",
        "plz": "4600", "ort": "Olten",
        "versandart": "versand", "zahlungsart": "rechnung",
        "cart_data": cart, "kommentar": "",
        "csrf_token": "ungueltig",
    })
    assert response.status_code == 403
```

- [ ] **Step 7: Tests ausführen**

```bash
uv run pytest tests/test_csrf.py -v
# Expected: 4 passed
```

- [ ] **Step 8: conftest.py anpassen — CSRF in Bestell-Tests umgehen**

In `tests/conftest.py` den CSRF-Validierung für Tests mocken oder einen gültigen Token erzeugen:

```python
@pytest.fixture()
def csrf_token():
    from app.csrf import generiere_csrf_token
    return generiere_csrf_token("change-me")  # settings.secret_key default
```

Bestehende Bestell-Tests in `test_api_bestellungen.py` aktualisieren: `csrf_token`-Fixture verwenden.

- [ ] **Step 9: Alle Tests ausführen**

```bash
uv run pytest -v
# Expected: all passed
```

- [ ] **Step 10: Commit**

```bash
git add app/csrf.py tests/test_csrf.py app/routers/bestellungen.py tests/conftest.py tests/test_api_bestellungen.py
git commit -m "feat: CSRF-Schutz für POST-Endpoints"
```

---

## Task 11: Deployment (Docker + fly.io)

**Files:**
- Create: `Dockerfile`
- Create: `fly.toml`
- Create: `.dockerignore`

- [ ] **Step 1: Dockerfile erstellen**

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

EXPOSE 8000

# DB-Migration beim Container-Start (nicht Build), damit sie auf das persistente Volume schreibt
CMD ["sh", "-c", "python -c 'from app.database import init_db; init_db()' && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

Hinweis: `DATABASE_PATH=/data/olivalle.db` wird via `fly.toml` env gesetzt → DB liegt auf persistentem Volume.

- [ ] **Step 2: .dockerignore erstellen**

```
.venv/
__pycache__/
*.pyc
.env
*.db
site/
.git/
docs/
tests/
frontend/
```

- [ ] **Step 3: fly.toml erstellen**

```toml
app = "olivalle"
primary_region = "cdg"

[build]

[env]
  DATABASE_PATH = "/data/olivalle.db"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 0

[mounts]
  source = "olivalle_data"
  destination = "/data"

[[vm]]
  memory = "256mb"
  cpu_kind = "shared"
  cpus = 1
```

- [ ] **Step 4: Docker-Image lokal testen**

```bash
docker build -t olivalle .
docker run -p 8000:8000 --env-file .env olivalle
# Browser: http://localhost:8000 → Shop sollte laden
```

- [ ] **Step 5: fly.io Setup (einmalig)**

```bash
fly apps create olivalle
fly volumes create olivalle_data --region cdg --size 1
fly secrets set STRIPE_SECRET_KEY=sk_... STRIPE_WEBHOOK_SECRET=whsec_... RESEND_API_KEY=re_... SECRET_KEY=... QR_IBAN=... QR_NAME=... QR_ADDRESS=... QR_ZIP=... QR_CITY=...
```

- [ ] **Step 6: Deployment**

```bash
fly deploy
fly status
# Expected: 1 Machine running
```

- [ ] **Step 7: Health-Check**

```bash
curl https://olivalle.fly.dev/health
# Expected: {"status":"ok"}
```

- [ ] **Step 8: Commit**

```bash
git add Dockerfile fly.toml .dockerignore
git commit -m "feat: Docker + fly.io Deployment-Konfiguration"
```

---

## Task 12: MkDocs einrichten

**Files:**
- Create: `mkdocs.yml`
- Create: `docs-serve.command`
- Modify: `pyproject.toml` (mkdocs Dependencies)

Referenz: Memory `project_mkdocs_pending.md`, Vorlage: `/Users/KN/Dropbox/Privat/CAS/projekte/Munica/mkdocs.yml`

- [ ] **Step 1: mkdocs.yml erstellen**

```yaml
site_name: Olivalle Webshop — Dokumentation
theme:
  name: material
  language: de
  palette:
    scheme: slate
    primary: amber
    accent: amber
  font:
    text: Roboto

plugins:
  - search
  - mermaid2

markdown_extensions:
  - admonition
  - tables
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:mermaid2.fence_mermaid_custom

nav:
  - Übersicht: index.md
  - Architektur (arc42): arc42.md
  - Systemarchitektur: systemarchitektur.md
  - Datenbankschema: datenbankschema.md
  - Bestellprozess: bestellprozess.md
  - Produkttexte: produkttexte.md
  - Roadmap: roadmap.md
  - Rechtliches:
    - Datenschutz: legal/datenschutz.md
    - Impressum: legal/impressum.md
    - AGB: legal/agb.md
```

- [ ] **Step 2: Dependencies in pyproject.toml ergänzen**

In `[project.optional-dependencies]` hinzufügen:
```toml
docs = [
    "mkdocs>=1.6",
    "mkdocs-material>=9",
    "mkdocs-mermaid2-plugin>=1",
]
```

- [ ] **Step 3: docs-serve.command erstellen**

```bash
#!/bin/bash
cd "$(dirname "$0")"
uv run mkdocs serve --open
```

Dann ausführbar machen: `chmod +x docs-serve.command`

- [ ] **Step 4: Testen**

```bash
uv sync --extra docs
uv run mkdocs serve
# Browser: http://127.0.0.1:8000 → Dokumentation sichtbar
```

- [ ] **Step 5: Commit**

```bash
git add mkdocs.yml docs-serve.command pyproject.toml
git commit -m "docs: MkDocs mit Material-Theme einrichten"
```

---

## Task 13: Dokumentation aktualisieren

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/arc42.md`
- Modify: `docs/systemarchitektur.md`
- Modify: `docs/datenbankschema.md`

Referenz: Spec Abschnitt 14 listet alle nötigen Änderungen.

- [ ] **Step 1: CLAUDE.md aktualisieren**

Änderungen gemäss Spec:
- Tech-Stack-Tabelle: Next.js → Jinja2, Supabase → SQLite, Vercel/Railway → fly.io, shadcn/ui entfernen
- Test-Strategie: Vitest entfernen, nur pytest + Ruff
- Context-Scopes: Frontend-Scope entfernen, Backend-Scope anpassen
- Phasen: Abos (Phase 3) streichen, Versandkosten eintragen
- Code-Qualität: ESLint/Prettier entfernen

- [ ] **Step 2: docs/arc42.md aktualisieren**

Änderungen:
- Abschnitt 1: FA-009 (Abos) streichen, Ziel 4 anpassen
- Abschnitt 3: Externe Systeme → Supabase/Vercel/Railway entfernen, fly.io + Resend + SQLite einsetzen
- Abschnitt 4: Kernentscheidungen aktualisieren (Jinja2, SQLite, fly.io)
- Abschnitt 5: Bausteinsicht komplett neu (kein Frontend/Backend Split mehr)
- Abschnitt 7: Verteilungssicht → ein Container auf fly.io
- Abschnitt 9: ADR-002 aktualisieren (SQLite statt Supabase), neuer ADR für Jinja2 statt Next.js
- Abschnitt 11: Risiken anpassen (Supabase-Risiko weg, SQLite-Backup-Risiko rein)

- [ ] **Step 3: docs/systemarchitektur.md aktualisieren**

Mermaid-Diagramm ersetzen durch Version aus Spec (Abschnitt 4).

- [ ] **Step 4: docs/datenbankschema.md aktualisieren**

Schema gemäss Spec Abschnitt 5 anpassen:
- `zahlungsart` und `versandkosten_chf` Spalte in bestellungen hinzufügen
- `stripe_payment_id` → `stripe_session_id` umbenennen

- [ ] **Step 5: Alle Docs auf Konsistenz prüfen**

Prüfen dass keine Referenzen auf Next.js, Supabase, Vercel, React, TypeScript, shadcn/ui, Stripe Billing mehr vorhanden sind.

```bash
uv run ruff check . && uv run pytest -v
```

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md docs/arc42.md docs/systemarchitektur.md docs/datenbankschema.md
git commit -m "docs: Dokumentation an neuen Tech-Stack anpassen (FastAPI+Jinja2+SQLite+fly.io)"
```

---

## Task 14: GitHub Issues aktualisieren

- [ ] **Step 1: Bestehende Issues prüfen**

```bash
gh issue list --state open --label phase-1
```

- [ ] **Step 2: Issues schliessen die durch den neuen Stack obsolet werden**

Issues mit Next.js, Supabase, Vercel, TypeScript-Bezug als "wontfix" schliessen mit Kommentar zum Stack-Wechsel.

- [ ] **Step 3: Neue Issues erstellen falls nötig**

Prüfen ob der Plan Arbeit enthält die noch nicht als Issue existiert.

- [ ] **Step 4: Labels und Milestones aktualisieren**

Phase-1-Issues dem neuen Stack zuordnen.

- [ ] **Step 5: TODO.md aktualisieren**

`O-HOST` und `O-WEBARCH` als erledigt markieren (durch Spec abgedeckt).

- [ ] **Step 6: Commit**

```bash
git add ../TODO.md
git commit -m "docs: TODO.md und GitHub Issues an neuen Stack anpassen"
```
