# Tailwind lokal builden (CDN entfernen) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tailwind CSS zur Build-Zeit kompilieren statt via CDN zur Laufzeit, damit `'unsafe-eval'` und `cdn.tailwindcss.com` aus der CSP entfernt werden können.

**Architecture:** Tailwind CLI via npm, pinned in `package.json`. Lokal: `make css-build` / `make css-watch`. In Docker: Multi-Stage-Build mit `node:20-alpine` als Build-Stage, gebautes `static/css/app.css` wird in das finale Python-Image kopiert. Finales Image bleibt Python-only (kein Node zur Laufzeit). `tailwind.config.js` ersetzt die bisherige Inline-Konfiguration in `base.html`.

**Tech Stack:** Tailwind CSS v3.4 (CLI), Node 20 (nur Build), bestehend: FastAPI + Jinja2, Docker Multi-Stage.

---

## Hintergrund

Design-Spec: `docs/superpowers/specs/2026-04-08-csp-haertung-design.md` (Teil 1 — #88).

Aktueller Zustand:
- `templates/base.html:7`, `templates/admin/base.html:8`, `templates/admin/login.html:8` laden `https://cdn.tailwindcss.com`
- `templates/base.html:8-20` enthält einen Inline-Script-Block `tailwind.config = {…}` mit Farben und Fonts (dieser Block wird hinfällig — zieht in `tailwind.config.js` um)
- `app/middleware/security_headers.py:10-22` enthält `'unsafe-eval'` und `https://cdn.tailwindcss.com` in `script-src`
- `tests/test_security_headers.py` prüft CSP-Header-Inhalte

Gebaute Datei landet unter `static/css/app.css` und wird per `<link>` eingebunden. `static/css/app.css` und `node_modules/` sind gitignoriert; in Docker wird die Datei innerhalb der Build-Stage erzeugt.

## Dateien

**Create:**
- `package.json` — Tailwind-Version pinnen
- `package-lock.json` — wird automatisch durch `npm install` erzeugt, eingecheckt
- `tailwind.config.js` — Farben, Fonts, content-Globs
- `static/css/input.css` — Tailwind-Direktiven (`@tailwind base/components/utilities`)
- `tests/test_static_css_build.py` — Smoke-Test, dass gebautes CSS vorhanden und sinnvoll ist (lokaler Dev-Hinweis)

**Modify:**
- `.gitignore` — `static/css/app.css` hinzufügen
- `Makefile` — `css-build`, `css-watch`, `dev` nutzt Watch
- `templates/base.html` — CDN-Script weg, Inline-Config weg, `<link rel="stylesheet" href="{{ url_for('static', path='css/app.css') }}">` rein
- `templates/admin/base.html` — analog
- `templates/admin/login.html` — analog
- `app/middleware/security_headers.py` — `'unsafe-eval'` und `cdn.tailwindcss.com` aus `script-src` entfernen
- `tests/test_security_headers.py` — Assertions anpassen: `'unsafe-eval'` und `cdn.tailwindcss.com` dürfen *nicht* mehr im CSP-Header stehen
- `Dockerfile` — Multi-Stage mit Node-Stage
- `docs/arc42.md` (falls Build-Pipeline erwähnt) — kurzer Hinweis auf CSS-Build-Step
- `README.md` — Setup-Hinweis: `npm install` vor erstem `make dev`

---

## Task 1: Tailwind npm-Setup

**Files:**
- Create: `package.json`
- Create: `tailwind.config.js`
- Create: `static/css/input.css`
- Modify: `.gitignore`

- [ ] **Step 1: `package.json` anlegen**

```json
{
  "name": "olivalle-webshop",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "css:build": "tailwindcss -i ./static/css/input.css -o ./static/css/app.css --minify",
    "css:watch": "tailwindcss -i ./static/css/input.css -o ./static/css/app.css --watch"
  },
  "devDependencies": {
    "tailwindcss": "3.4.17"
  }
}
```

Begründung Version: Tailwind v3.4 ist die letzte stabile Minor-Release, die eine eigenständige `tailwindcss`-CLI als npm-Paket bereitstellt. v4 hat einen anderen CLI-Workflow — bewusst nicht gewählt, um den Umfang klein zu halten.

- [ ] **Step 2: `tailwind.config.js` anlegen**

Diese Konfiguration übernimmt exakt die Werte aus dem bisherigen Inline-Block in `templates/base.html:8-20`.

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './app/**/*.py',
  ],
  theme: {
    extend: {
      colors: {
        accent: '#f1d600',
      },
      fontFamily: {
        display: ['"Amatic SC"', 'cursive'],
        body: ['Lora', 'serif'],
      },
    },
  },
  plugins: [],
}
```

- [ ] **Step 3: `static/css/input.css` anlegen**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 4: `.gitignore` ergänzen**

Im Python-Block nach der Zeile `.ruff_cache/` einfügen:

```
# Gebautes CSS (wird via `make css-build` erzeugt)
static/css/app.css
```

- [ ] **Step 5: Abhängigkeiten installieren und Build testen**

Run:
```bash
npm install
npx tailwindcss -i ./static/css/input.css -o ./static/css/app.css --minify
ls -lh static/css/app.css
```

Expected: Datei existiert, ca. 10–30 KB, minifiziert. `package-lock.json` ist entstanden.

- [ ] **Step 6: Commit**

```bash
git add package.json package-lock.json tailwind.config.js static/css/input.css .gitignore
git commit -m "feat: Tailwind CLI-Setup mit package.json und tailwind.config.js"
```

---

## Task 2: Makefile-Targets für CSS-Build

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Neue Targets hinzufügen**

In `Makefile` das `.PHONY`-Directive erweitern und zwei Targets ergänzen (vor `dev:`):

```makefile
.PHONY: help dev test lint format migrate docs css-build css-watch
```

Und nach `help:` (vor `dev:`) einfügen:

```makefile
css-build: ## Tailwind-CSS einmalig bauen (minifiziert)
	npx tailwindcss -i ./static/css/input.css -o ./static/css/app.css --minify

css-watch: ## Tailwind-CSS im Watch-Mode (für lokale Entwicklung)
	npx tailwindcss -i ./static/css/input.css -o ./static/css/app.css --watch
```

- [ ] **Step 2: Targets testen**

Run: `make css-build && ls -lh static/css/app.css`
Expected: CSS-Datei wird neu erzeugt, Make-Target läuft ohne Fehler.

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "feat: make css-build und css-watch Targets"
```

---

## Task 3: Templates — CDN-Script entfernen, gebautes CSS einbinden

**Files:**
- Modify: `templates/base.html`
- Modify: `templates/admin/base.html`
- Modify: `templates/admin/login.html`

- [ ] **Step 1: `templates/base.html` umstellen**

Zeilen 7–20 (der CDN-Script-Tag und der Inline-Tailwind-Config-Block) durch einen `<link>`-Tag ersetzen:

Alt:
```html
    <script src="https://cdn.tailwindcss.com"></script>
    <script nonce="{{ csp_nonce }}">
        tailwind.config = {
            theme: {
                extend: {
                    colors: { accent: '#f1d600' },
                    fontFamily: {
                        display: ['"Amatic SC"', 'cursive'],
                        body: ['Lora', 'serif'],
                    },
                }
            }
        }
    </script>
```

Neu:
```html
    <link rel="stylesheet" href="{{ url_for('static', path='css/app.css') }}">
```

- [ ] **Step 2: `templates/admin/base.html` umstellen**

Die Zeile `<script src="https://cdn.tailwindcss.com"></script>` (Zeile 8) durch ersetzen:

```html
    <link rel="stylesheet" href="{{ url_for('static', path='css/app.css') }}">
```

Falls die Datei ebenfalls einen Inline-`tailwind.config`-Block hat: entfernen.

- [ ] **Step 3: `templates/admin/login.html` umstellen**

Analog Task 3 Step 2.

- [ ] **Step 4: Visuell prüfen**

Run:
```bash
make css-build
make dev
```

Im Browser `http://localhost:8000/` und `http://localhost:8000/admin/login` aufrufen. Expected: Styles (Farben, Fonts, Layout) sehen identisch aus wie vorher — insbesondere die Akzentfarbe `#f1d600` und die Schriften Amatic SC / Lora. Falls etwas fehlt: prüfen, ob die entsprechenden Klassen in `content`-Globs von `tailwind.config.js` gefunden werden.

- [ ] **Step 5: Commit**

```bash
git add templates/base.html templates/admin/base.html templates/admin/login.html
git commit -m "feat: gebautes Tailwind-CSS statt CDN in Templates"
```

---

## Task 4: CSP-Middleware härten (`unsafe-eval` und CDN raus)

**Files:**
- Modify: `app/middleware/security_headers.py`
- Modify: `tests/test_security_headers.py`

- [ ] **Step 1: Failing Test zuerst — CSP darf `unsafe-eval` nicht mehr enthalten**

In `tests/test_security_headers.py` einen neuen Test ergänzen:

```python
def test_csp_kein_unsafe_eval_und_kein_tailwind_cdn(client: TestClient):
    response = client.get("/")
    csp = response.headers["content-security-policy"]
    script_src = next(p for p in csp.split(";") if p.strip().startswith("script-src"))
    assert "'unsafe-eval'" not in script_src
    assert "cdn.tailwindcss.com" not in csp
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag erwartet**

Run: `uv run pytest tests/test_security_headers.py::test_csp_kein_unsafe_eval_und_kein_tailwind_cdn -v`
Expected: FAIL, weil `'unsafe-eval'` und `cdn.tailwindcss.com` noch im Header stehen.

- [ ] **Step 3: `CSP_TEMPLATE` anpassen**

In `app/middleware/security_headers.py` den Kommentarblock ab Zeile 7 und das Template ersetzen:

```python
# CSP ohne 'unsafe-eval': Tailwind wird zur Build-Zeit kompiliert (Issue #88),
# Inline-Scripts laufen über Nonces (Issue #89).
CSP_TEMPLATE = (
    "default-src 'self'; "
    "script-src 'self' 'nonce-{nonce}' https://js.stripe.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "img-src 'self' data:; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "connect-src 'self' https://api.stripe.com; "
    "frame-src https://js.stripe.com https://hooks.stripe.com; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self' https://checkout.stripe.com"
)
```

- [ ] **Step 4: Alle Security-Header-Tests laufen lassen**

Run: `uv run pytest tests/test_security_headers.py -v`
Expected: Alle Tests (inkl. neuem) PASS. Falls ein bestehender Test `'unsafe-eval'` oder `cdn.tailwindcss.com` positiv assertet hatte, diese Assertion entfernen.

- [ ] **Step 5: Gesamte Test-Suite laufen lassen**

Run: `uv run pytest`
Expected: alle Tests PASS.

- [ ] **Step 6: Commit**

```bash
git add app/middleware/security_headers.py tests/test_security_headers.py
git commit -m "feat: unsafe-eval und cdn.tailwindcss.com aus CSP entfernt"
```

---

## Task 5: Dockerfile — Multi-Stage mit Node-Build

**Files:**
- Modify: `Dockerfile`

- [ ] **Step 1: Dockerfile auf Multi-Stage umstellen**

Kompletter Inhalt (ersetzt das bisherige Dockerfile):

```dockerfile
# Stage 1: CSS-Build mit Node (nur Build-Zeit, nicht im finalen Image)
FROM node:20-alpine AS css-builder
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci
COPY tailwind.config.js ./
COPY static/css/input.css ./static/css/input.css
COPY templates ./templates
COPY app ./app
RUN npx tailwindcss -i ./static/css/input.css -o ./static/css/app.css --minify

# Stage 2: Python-Runtime
FROM python:3.13-slim
WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .
COPY --from=css-builder /build/static/css/app.css ./static/css/app.css

EXPOSE 8000

ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

# DB-Migration beim Container-Start (nicht Build), damit sie auf das persistente Volume schreibt
CMD ["sh", "-c", "python -c 'from app.database import init_db; init_db()' && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

Begründung: Die Node-Stage enthält nur die Dateien, die Tailwind für den Content-Scan braucht (Templates + Python-Sourcen wegen der `content`-Globs). Das finale Image bleibt Python-only; Node landet nicht in der Runtime.

- [ ] **Step 2: Docker-Build lokal testen**

Run:
```bash
docker build -t olivalle-test .
```

Expected: Build läuft durch, beide Stages erfolgreich. Die Ausgabe zeigt, dass Tailwind CSS erzeugt wurde.

- [ ] **Step 3: Container starten und HTML-Response prüfen**

Run:
```bash
docker run --rm -p 8000:8000 olivalle-test &
sleep 3
curl -s http://localhost:8000/ | grep -E 'app\.css|tailwindcss\.com' || echo "keine Treffer"
curl -sI http://localhost:8000/static/css/app.css | head -1
docker ps -q --filter ancestor=olivalle-test | xargs -r docker stop
```

Expected: `app.css`-Link wird im HTML gefunden, kein `tailwindcss.com` mehr; `/static/css/app.css` liefert `HTTP/1.1 200 OK`.

- [ ] **Step 4: Commit**

```bash
git add Dockerfile
git commit -m "feat: Multi-Stage Dockerfile mit Node-CSS-Build"
```

---

## Task 6: Dokumentation aktualisieren

**Files:**
- Modify: `README.md`
- Modify: `docs/arc42.md` (falls Build-Pipeline beschrieben)

- [ ] **Step 1: README — Setup-Abschnitt ergänzen**

Im Setup-Abschnitt der README (dort wo `make dev` oder `uv sync` erklärt wird) einen Hinweis einfügen:

```markdown
### Frontend-CSS

Tailwind wird zur Build-Zeit kompiliert. Einmalig installieren:

```bash
npm install
make css-build
```

Während der Entwicklung parallel zum FastAPI-Server laufen lassen:

```bash
make css-watch
```
```

- [ ] **Step 2: arc42 prüfen und ggf. aktualisieren**

Run: `grep -n -i "tailwind\|cdn" docs/arc42.md || echo "kein Treffer"`

Falls Treffer: den entsprechenden Abschnitt anpassen (CDN → lokaler Build, Docker Multi-Stage). Falls kein Treffer: überspringen.

- [ ] **Step 3: Commit**

```bash
git add README.md docs/arc42.md
git commit -m "docs: Tailwind-Build-Step in README und arc42 dokumentiert"
```

---

## Task 7: Abschluss-Verifikation

- [ ] **Step 1: Tests komplett**

Run: `uv run pytest`
Expected: alle Tests PASS.

- [ ] **Step 2: Lint**

Run: `make lint`
Expected: keine Ruff-Fehler.

- [ ] **Step 3: End-to-End Docker-Check**

Run:
```bash
docker build -t olivalle-test . && \
docker run --rm -d -p 8000:8000 --name olivalle-verify olivalle-test && \
sleep 3 && \
curl -sI http://localhost:8000/ | grep -i 'content-security-policy' && \
curl -sI http://localhost:8000/static/css/app.css | head -1 ; \
docker stop olivalle-verify
```

Expected:
- CSP-Header enthält **kein** `'unsafe-eval'` und **kein** `cdn.tailwindcss.com`
- `/static/css/app.css` → `HTTP/1.1 200 OK`

- [ ] **Step 4: CSP mit Browser DevTools prüfen**

Seiten `/`, `/warenkorb`, `/admin/login` aufrufen, in DevTools prüfen dass:
- keine CSP-Verstösse in der Console
- Styles korrekt angewendet werden

- [ ] **Step 5: Issue #88 schliessen**

Im GitHub-Issue #88 alle Checkboxen abhaken und PR referenzieren.

---

## Self-Review Notizen

**Spec coverage:**
- Tailwind CLI als Build-Step → Task 1+2
- CDN aus `base.html` entfernen → Task 3
- Dockerfile Node-Stage → Task 5
- CSP `unsafe-eval` + CDN raus → Task 4
- Tests anpassen → Task 4
- Offene Fragen (Version pinnen → v3.4.17; Watch-Mode → Task 2; CI → im Docker-Build, kein separater CI-Step nötig da GitHub Actions das Image via `docker build-push-action` baut)

**Nicht im Scope (bewusst ausgelassen):**
- Tailwind v4 Migration
- Auslagern von Inline-Scripts (das macht #89, bereits gemerged)
- `style-src 'unsafe-inline'` härten — separater Task
