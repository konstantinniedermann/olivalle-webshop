# Frontend-Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sticky Header mit Navigation, neue "Über das Öl"-Seite mit Olivenbaum-Hintergrund, und Lora als globaler Body-Font.

**Architecture:** Änderungen am base.html-Template (Header sticky, Font-System), neues Template + Router für die "Über das Öl"-Seite, Produktseite Hero durch Teaser ersetzen. Alle Routen setzen `active_page` für die Navigation.

**Tech Stack:** FastAPI, Jinja2, Tailwind CSS (CDN), Google Fonts (Amatic SC + Lora)

**Spec:** `docs/superpowers/specs/2026-03-30-frontend-redesign-design.md`

---

### Task 1: Font-System global einführen (Lora + Tailwind-Config)

**Files:**
- Modify: `templates/base.html:7-19` (Tailwind-Config + Google Fonts)
- Modify: `templates/base.html:21` (Body-Klasse)

- [ ] **Step 1: Google Fonts Link um Lora erweitern**

In `templates/base.html`, Zeile 19 ersetzen:

```html
<!-- ALT -->
<link href="https://fonts.googleapis.com/css2?family=Amatic+SC:wght@400;700&display=swap" rel="stylesheet">

<!-- NEU -->
<link href="https://fonts.googleapis.com/css2?family=Amatic+SC:wght@400;700&family=Lora:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
```

- [ ] **Step 2: Tailwind-Config um body-Font erweitern**

In `templates/base.html`, Zeile 13 ersetzen:

```javascript
// ALT
fontFamily: { display: ['"Amatic SC"', 'cursive'] },

// NEU
fontFamily: {
    display: ['"Amatic SC"', 'cursive'],
    body: ['Lora', 'serif'],
},
```

- [ ] **Step 3: Body-Element um font-body Klasse erweitern**

In `templates/base.html`, Zeile 21 ersetzen:

```html
<!-- ALT -->
<body class="bg-stone-800 text-white min-h-screen flex flex-col">

<!-- NEU -->
<body class="bg-stone-800 text-white min-h-screen flex flex-col font-body">
```

- [ ] **Step 4: Manuell prüfen — Dev-Server starten und Font kontrollieren**

Run: `make dev` (oder `uvicorn app.main:app --reload`)

Prüfen: Auf `http://localhost:8000` sollte der Fliesstext (Beschreibungen, Footer) jetzt in Lora (Serifenschrift) gerendert werden. Titel und Logo bleiben in Amatic SC.

- [ ] **Step 5: Commit**

```bash
git add templates/base.html
git commit -m "feat: Lora als globaler Body-Font (Amatic SC + Lora Font-System)"
```

---

### Task 2: Sticky Header mit Navigation

**Files:**
- Modify: `templates/base.html:22-42` (Header-Bereich)
- Modify: `app/routers/produkte.py:17-19` (active_page setzen)
- Modify: `app/routers/warenkorb.py:10` (active_page setzen)
- Modify: `app/routers/bestellungen.py` (active_page setzen in allen Templates)
- Test: `tests/test_api_produkte.py`

- [ ] **Step 1: Test für Sticky Header und Navigation schreiben**

In `tests/test_api_produkte.py`, am Ende hinzufügen:

```python
def test_header_sticky(client):
    """Header ist sticky mit Backdrop-Blur."""
    response = client.get("/")
    assert "sticky" in response.text
    assert "top-0" in response.text
    assert "backdrop-blur" in response.text


def test_header_navigation_links(client):
    """Header enthält Navigation: Über das Öl, Produkte, Warenkorb."""
    response = client.get("/")
    assert 'href="/ueber-das-oel"' in response.text
    assert "Über das Öl" in response.text
    assert 'href="/"' in response.text
    assert "Produkte" in response.text
    assert "Warenkorb" in response.text


def test_header_active_page_produkte(client):
    """Auf der Startseite ist 'Produkte' als aktiv markiert."""
    response = client.get("/")
    # Der aktive Link hat text-accent Klasse
    assert "text-accent" in response.text
```

- [ ] **Step 2: Tests ausführen — sie müssen fehlschlagen**

Run: `pytest tests/test_api_produkte.py::test_header_sticky tests/test_api_produkte.py::test_header_navigation_links -v`

Expected: FAIL — "sticky" und "Über das Öl" nicht im Response.

- [ ] **Step 3: Header in base.html umbauen**

In `templates/base.html`, den gesamten `<header>...</header>` Block (Zeilen 22-42) ersetzen durch:

```html
<header class="sticky top-0 z-50 bg-stone-800/90 backdrop-blur-sm border-b border-stone-700 py-4">
    <div class="max-w-4xl mx-auto px-4 flex items-center justify-between">
        <a href="/" class="font-display text-4xl font-bold text-accent">Olivalle</a>
        <div class="flex items-center gap-6">
            <nav class="flex items-center gap-4 text-sm">
                <a href="/ueber-das-oel"
                   class="{% if active_page == 'ueber-das-oel' %}text-accent{% else %}text-stone-300 hover:text-accent{% endif %} transition-colors">
                    Über das Öl
                </a>
                <a href="/"
                   class="{% if active_page == 'produkte' %}text-accent{% else %}text-stone-300 hover:text-accent{% endif %} transition-colors">
                    Produkte
                </a>
            </nav>
            <div class="relative">
                <a href="/warenkorb"
                   class="{% if active_page == 'warenkorb' %}text-accent{% else %}text-stone-300 hover:text-accent{% endif %} transition-colors">
                    Warenkorb (<span id="cart-count">0</span>)
                </a>
                <div id="cart-flyout" class="hidden absolute right-0 top-full mt-2 w-72 bg-stone-700 rounded-lg shadow-lg border border-stone-600 z-50 p-4">
                    <div id="cart-flyout-items" class="text-sm space-y-2 mb-3"></div>
                    <div class="border-t border-stone-600 pt-2 flex justify-between font-bold text-sm">
                        <span>Total</span>
                        <span id="cart-flyout-total"></span>
                    </div>
                    <div class="mt-3 flex gap-2 text-sm">
                        <a href="/warenkorb" class="flex-1 text-center py-2 border border-stone-500 rounded hover:bg-stone-600 transition-colors">Warenkorb</a>
                        <a href="/checkout" class="flex-1 text-center py-2 bg-accent text-stone-900 rounded font-bold hover:bg-yellow-400 transition-colors">Zur Kasse</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</header>
```

- [ ] **Step 4: active_page als globalen Template-Default setzen**

In `app/templating.py`, Zeile 9 nach `app_version` hinzufügen:

```python
templates.env.globals["active_page"] = ""
```

- [ ] **Step 5: active_page in produkte.py setzen**

In `app/routers/produkte.py`, Zeile 18 ändern:

```python
# ALT
return templates.TemplateResponse(
    request, "produkte.html", {"produkte": produkte}
)

# NEU
return templates.TemplateResponse(
    request, "produkte.html", {"produkte": produkte, "active_page": "produkte"}
)
```

- [ ] **Step 6: active_page in warenkorb.py setzen**

In `app/routers/warenkorb.py`, Zeile 10 ändern:

```python
# ALT
return templates.TemplateResponse(request, "warenkorb.html")

# NEU
return templates.TemplateResponse(request, "warenkorb.html", {"active_page": "warenkorb"})
```

- [ ] **Step 7: active_page in bestellungen.py setzen**

In `app/routers/bestellungen.py`, für jede `TemplateResponse` den Context um `"active_page": "checkout"` bzw. `"active_page": "bestaetigung"` erweitern. Betrifft alle Stellen wo `templates.TemplateResponse` aufgerufen wird.

- [ ] **Step 8: Tests ausführen**

Run: `pytest tests/test_api_produkte.py -v`

Expected: Alle Tests PASS (auch die bestehenden).

- [ ] **Step 9: Bestehenden Test anpassen falls nötig**

Der Test `test_startseite_hero_variante_b` prüft auf "Kooperative OLIPE" und "Nevadillo Blanco" — diese Texte werden in Task 3 entfernt. Noch nicht anpassen, erst in Task 3.

- [ ] **Step 10: Commit**

```bash
git add templates/base.html app/routers/produkte.py app/routers/warenkorb.py app/routers/bestellungen.py app/templating.py tests/test_api_produkte.py
git commit -m "feat: Sticky Header mit Navigation (Über das Öl, Produkte, Warenkorb)"
```

---

### Task 3: Produktseite — Hero durch Teaser ersetzen

**Files:**
- Modify: `templates/produkte.html:4-22` (Hero-Section)
- Modify: `tests/test_api_produkte.py` (Tests anpassen)

- [ ] **Step 1: Test für den neuen Teaser schreiben + alten Hero-Test anpassen**

In `tests/test_api_produkte.py`:

```python
# ALT — ersetzen:
def test_startseite_hero_variante_b(client):
    """Startseite zeigt den Variante-B Produkttext im Hero-Bereich."""
    response = client.get("/")
    assert "Kooperative OLIPE" in response.text
    assert "Nevadillo Blanco" in response.text

# NEU:
def test_startseite_teaser(client):
    """Startseite zeigt kurzen Teaser mit Link zu 'Über das Öl'."""
    response = client.get("/")
    assert "Biologisches Olivenöl extra virgen" in response.text
    assert 'href="/ueber-das-oel"' in response.text
    assert "Mehr erfahren" in response.text


def test_startseite_kein_langer_hero(client):
    """Der lange Variante-B Text ist nicht mehr auf der Startseite."""
    response = client.get("/")
    assert "Kooperative OLIPE" not in response.text
```

- [ ] **Step 2: Tests ausführen — sie müssen fehlschlagen**

Run: `pytest tests/test_api_produkte.py::test_startseite_teaser tests/test_api_produkte.py::test_startseite_kein_langer_hero -v`

Expected: FAIL — "Kooperative OLIPE" ist noch vorhanden, "Mehr erfahren" fehlt.

- [ ] **Step 3: Hero-Section in produkte.html durch Teaser ersetzen**

In `templates/produkte.html`, die gesamte Hero-Section (Zeilen 4-22) ersetzen:

```html
{# Kurzer Teaser mit Link zur "Über das Öl"-Seite #}
<section class="mb-8">
    <h1 class="font-display text-5xl font-bold text-accent mb-4">Unsere Produkte</h1>
    <p class="text-stone-300 text-lg">
        Biologisches Olivenöl extra virgen aus dem Herzen Andalusiens.
        <a href="/ueber-das-oel" class="text-accent hover:underline">Mehr erfahren →</a>
    </p>
</section>
```

- [ ] **Step 4: Tests ausführen**

Run: `pytest tests/test_api_produkte.py -v`

Expected: Alle Tests PASS.

- [ ] **Step 5: Commit**

```bash
git add templates/produkte.html tests/test_api_produkte.py
git commit -m "feat: Produktseite Hero durch kurzen Teaser mit Link ersetzen"
```

---

### Task 4: Neue Seite "Über das Öl" — Route + Template

**Files:**
- Create: `app/routers/seiten.py`
- Modify: `app/main.py:22-27` (Router einbinden)
- Create: `templates/ueber-das-oel.html`
- Create: `tests/test_api_seiten.py`

- [ ] **Step 1: Test für die neue Route schreiben**

Neue Datei `tests/test_api_seiten.py`:

```python
def test_ueber_das_oel_status(client):
    """Die 'Über das Öl'-Seite ist erreichbar."""
    response = client.get("/ueber-das-oel")
    assert response.status_code == 200


def test_ueber_das_oel_inhalt(client):
    """Die Seite enthält die vier Abschnitte."""
    response = client.get("/ueber-das-oel")
    assert "Unser Olivenöl" in response.text
    assert "Die Herkunft" in response.text
    assert "Die Kooperative OLIPE" in response.text
    assert "Die Qualität" in response.text
    assert "Von Andalusien in die Schweiz" in response.text


def test_ueber_das_oel_hintergrundbild(client):
    """Die Seite verwendet das Olivenbaum-Hintergrundbild."""
    response = client.get("/ueber-das-oel")
    assert "olive-tree-hero.jpg" in response.text


def test_ueber_das_oel_cta(client):
    """Die Seite enthält einen CTA-Link zu den Produkten."""
    response = client.get("/ueber-das-oel")
    assert "Zu unseren Produkten" in response.text
    assert 'href="/"' in response.text


def test_ueber_das_oel_active_page(client):
    """Die Navigation markiert 'Über das Öl' als aktiv."""
    response = client.get("/ueber-das-oel")
    # active_page wird gesetzt, der Link bekommt text-accent
    assert "ueber-das-oel" in response.text
```

- [ ] **Step 2: Tests ausführen — sie müssen fehlschlagen**

Run: `pytest tests/test_api_seiten.py -v`

Expected: FAIL — 404, Route existiert nicht.

- [ ] **Step 3: Router erstellen**

Neue Datei `app/routers/seiten.py`:

```python
from fastapi import APIRouter, Request

from app.templating import templates

router = APIRouter()


@router.get("/ueber-das-oel")
def ueber_das_oel(request: Request):
    return templates.TemplateResponse(
        request, "ueber-das-oel.html", {"active_page": "ueber-das-oel"}
    )
```

- [ ] **Step 4: Router in main.py einbinden**

In `app/main.py`, Zeile 22 ändern:

```python
# ALT
from app.routers import bestellungen, produkte, warenkorb, webhooks

# NEU
from app.routers import bestellungen, produkte, seiten, warenkorb, webhooks
```

Und nach Zeile 25 (nach `app.include_router(warenkorb.router)`) einfügen:

```python
app.include_router(seiten.router)
```

- [ ] **Step 5: Template erstellen**

Neue Datei `templates/ueber-das-oel.html`:

```html
{% extends "base.html" %}
{% block title %}Über das Öl{% endblock %}
{% block content %}
<div class="relative -mx-4 -mt-8 px-4 pt-8 pb-12 bg-[url('/static/images/olive-tree-hero.jpg')] bg-cover bg-center min-h-screen">
    {# Leichtes Overlay für Lesbarkeit #}
    <div class="absolute inset-0 bg-stone-900/30"></div>

    <div class="relative max-w-xl mx-auto">
        {# Seitentitel #}
        <div class="text-center mb-10">
            <h1 class="font-display text-6xl font-bold text-accent drop-shadow-lg">Unser Olivenöl</h1>
            <p class="text-stone-200 mt-2 text-lg drop-shadow">Biologisch · Extra Virgen · Andalusien</p>
        </div>

        {# Inhaltskacheln #}
        <div class="flex flex-col gap-6">
            <div class="bg-stone-900/75 backdrop-blur-[4px] rounded-lg p-6 border border-stone-600/15">
                <h2 class="font-display text-3xl text-accent mb-3">Die Herkunft</h2>
                <p class="text-stone-200 leading-relaxed">
                    Die Oliven der Sorte Nevadillo Blanco wachsen in den Berghainen der
                    Sierra Morena bei Córdoba. Die Region ist geprägt von heissen Sommern,
                    milden Wintern und kargen Böden — ideale Bedingungen für aromatische
                    Oliven mit hohem Ölgehalt. Die Bäume stehen oft an steilen Hängen,
                    wo maschinelle Ernte unmöglich ist. Hier wird von Hand gearbeitet,
                    wie seit Generationen.
                </p>
            </div>

            <div class="bg-stone-900/75 backdrop-blur-[4px] rounded-lg p-6 border border-stone-600/15">
                <h2 class="font-display text-3xl text-accent mb-3">Die Kooperative OLIPE</h2>
                <p class="text-stone-200 leading-relaxed">
                    Rund 800 Bauernfamilien der Kooperative OLIPE arbeiten seit 1957
                    gemeinsam. Die Kooperative garantiert faire Preise für die Produzenten
                    und kontrolliert die gesamte Kette von der Ernte bis zur Abfüllung.
                    Bio-Zertifizierung und Nachhaltigkeit sind dabei keine Marketing-Begriffe,
                    sondern gelebte Praxis seit Jahrzehnten.
                </p>
            </div>

            <div class="bg-stone-900/75 backdrop-blur-[4px] rounded-lg p-6 border border-stone-600/15">
                <h2 class="font-display text-3xl text-accent mb-3">Die Qualität</h2>
                <p class="text-stone-200 leading-relaxed">
                    Innerhalb von 12 bis 24 Stunden nach der Ernte werden die Oliven
                    schonend kalt gepresst. Diese schnelle Verarbeitung bewahrt einen
                    besonders hohen Polyphenolgehalt — natürliche Antioxidantien, die
                    das Öl nicht nur gesund, sondern auch geschmacklich einzigartig machen.
                    Das Ergebnis: fruchtig, leicht bitter und mit einer angenehmen Schärfe
                    im Abgang.
                </p>
            </div>

            <div class="bg-stone-900/75 backdrop-blur-[4px] rounded-lg p-6 border border-stone-600/15">
                <h2 class="font-display text-3xl text-accent mb-3">Von Andalusien in die Schweiz</h2>
                <p class="text-stone-200 leading-relaxed">
                    Seit rund 20 Jahren bringen wir dieses Olivenöl als Generalimporteur
                    direkt von Andalusien in die Schweiz. Ohne Zwischenhändler, ohne Umwege.
                    Jede Flasche erzählt die Geschichte einer Landschaft, einer Gemeinschaft
                    und einer Leidenschaft für ehrliches Handwerk.
                </p>
            </div>

            {# CTA #}
            <div class="text-center pt-4">
                <a href="/"
                   class="inline-block bg-accent text-stone-900 px-8 py-3 rounded-lg font-bold text-lg hover:bg-yellow-400 transition-colors">
                    Zu unseren Produkten →
                </a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 6: Tests ausführen**

Run: `pytest tests/test_api_seiten.py tests/test_api_produkte.py -v`

Expected: Alle Tests PASS.

- [ ] **Step 7: Manuell prüfen**

Auf `http://localhost:8000/ueber-das-oel` prüfen:
- Olivenbaum-Hintergrundbild sichtbar?
- Kacheln halbtransparent, Text lesbar?
- Titel in Amatic SC (gelb), Fliesstext in Lora?
- CTA-Button führt zu `/`?
- Sticky Header zeigt "Über das Öl" als aktiven Link?

- [ ] **Step 8: Commit**

```bash
git add app/routers/seiten.py app/main.py templates/ueber-das-oel.html tests/test_api_seiten.py
git commit -m "feat: Neue 'Über das Öl'-Seite mit Olivenbaum-Hintergrund und Infokacheln"
```

---

### Task 5: Gesamttest und Feinschliff

**Files:**
- Alle bisherigen Dateien

- [ ] **Step 1: Gesamte Testsuite ausführen**

Run: `pytest -v`

Expected: Alle Tests PASS. Falls Tests fehlschlagen die sich auf den alten Hero-Text beziehen, diese anpassen (z.B. `test_startseite_enthaelt_produkte` falls Produktbeschreibungen sich geändert haben).

- [ ] **Step 2: Alle Seiten manuell durchklicken**

Checkliste:
- [ ] `/` — Sticky Header, Teaser, Produktkarten, Warenkorb-Flyout sichtbar beim Scrollen
- [ ] `/ueber-das-oel` — Hintergrundbild, Kacheln, Fonts, CTA
- [ ] `/warenkorb` — Header korrekt, Lora-Font
- [ ] `/checkout` — Header korrekt, Lora-Font, Formular unverändert
- [ ] Navigation: aktiver Link jeweils gelb hervorgehoben
- [ ] Mobile: Header-Navigation auf kleinem Bildschirm prüfen (ggf. Textgrösse anpassen)

- [ ] **Step 3: Falls Anpassungen nötig — umsetzen und testen**

Typische Korrekturen:
- `main`-Container `max-w-4xl` könnte auf der "Über das Öl"-Seite das Hintergrundbild einschränken → prüfen ob der `content`-Block korrekt aus dem Container ausbricht
- Mobile Navigation: falls zu eng, `gap-4` auf `gap-3` und `text-sm` auf `text-xs` reduzieren

- [ ] **Step 4: Finaler Commit falls Korrekturen**

```bash
git add -A
git commit -m "fix: Feinschliff Frontend-Redesign (Layout, Mobile, Tests)"
```
