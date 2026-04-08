# CSP-Nonce für Inline-Scripts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `'unsafe-inline'` aus `script-src` der CSP entfernen, indem jeder Inline-`<script>`-Block per Request-spezifischem Nonce autorisiert wird.

**Architecture:** `SecurityHeadersMiddleware` generiert pro Request einen kryptografisch zufälligen Nonce (`secrets.token_urlsafe(16)`), legt ihn in `request.state.csp_nonce` ab und setzt ihn im `Content-Security-Policy`-Header als `'nonce-<value>'` in `script-src`. Jinja2 erhält den Nonce via `context_processors` als Template-Variable `csp_nonce`. Alle Inline-`<script>`-Blöcke tragen `nonce="{{ csp_nonce }}"`.

**Tech Stack:** FastAPI, Starlette (BaseHTTPMiddleware, Jinja2Templates), pytest, Python `secrets`.

**Referenz-Design:** `docs/superpowers/specs/2026-04-08-csp-haertung-design.md` (Teil 2, #89)

---

## Betroffene Dateien

**Code (modify):**
- `app/middleware/security_headers.py` — Nonce erzeugen, in `request.state`, CSP-Header dynamisch bauen, `'unsafe-inline'` raus
- `app/templating.py` — `context_processors=[csp_nonce_processor]` an `Jinja2Templates` übergeben

**Templates (modify) — `nonce="{{ csp_nonce }}"` an jeden Inline-`<script>`-Block:**
- `templates/base.html:8` (tailwind.config)
- `templates/admin/base.html:9`
- `templates/admin/login.html:9`
- `templates/bestaetigung.html:23`
- `templates/warenkorb.html:37`
- `templates/checkout.html:129`
- `templates/admin/bestellung_detail.html:230`

**Tests (modify):**
- `tests/test_security_headers.py` — Nonce-Assertions, kein `'unsafe-inline'` in `script-src`, Nonce pro Request eindeutig, Nonce im gerenderten HTML

---

## Task 1: CSP-Middleware mit Nonce

**Files:**
- Modify: `app/middleware/security_headers.py`
- Test: `tests/test_security_headers.py`

- [ ] **Step 1: Failing Test für Nonce-Präsenz im CSP-Header schreiben**

In `tests/test_security_headers.py` am Ende anhängen:

```python
import re


def test_csp_enthaelt_nonce_und_kein_unsafe_inline(client: TestClient):
    response = client.get("/")
    csp = response.headers["content-security-policy"]
    # script-src-Teil isolieren
    script_src = next(p for p in csp.split(";") if p.strip().startswith("script-src"))
    assert "'unsafe-inline'" not in script_src
    assert re.search(r"'nonce-[A-Za-z0-9_\-]{16,}'", script_src), script_src


def test_csp_nonce_pro_request_unterschiedlich(client: TestClient):
    r1 = client.get("/").headers["content-security-policy"]
    r2 = client.get("/").headers["content-security-policy"]
    n1 = re.search(r"'nonce-([A-Za-z0-9_\-]+)'", r1).group(1)
    n2 = re.search(r"'nonce-([A-Za-z0-9_\-]+)'", r2).group(1)
    assert n1 != n2
```

- [ ] **Step 2: Test laufen lassen, FAIL erwarten**

Run: `pytest tests/test_security_headers.py::test_csp_enthaelt_nonce_und_kein_unsafe_inline tests/test_security_headers.py::test_csp_nonce_pro_request_unterschiedlich -v`
Expected: FAIL — `'unsafe-inline'` noch in CSP, kein Nonce.

- [ ] **Step 3: Middleware anpassen**

Ersetze den Inhalt von `app/middleware/security_headers.py` komplett durch:

```python
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# CSP-Template mit Platzhalter {nonce}. 'unsafe-eval' bleibt vorerst wegen
# cdn.tailwindcss.com (Runtime-JIT) — wird in Issue #88 entfernt, sobald
# Tailwind als Build-Step gebaut wird.
CSP_TEMPLATE = (
    "default-src 'self'; "
    "script-src 'self' 'nonce-{nonce}' 'unsafe-eval' "
    "https://cdn.tailwindcss.com https://js.stripe.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "img-src 'self' data:; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "connect-src 'self' https://api.stripe.com; "
    "frame-src https://js.stripe.com https://hooks.stripe.com; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self' https://checkout.stripe.com"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Nonce vor dem Downstream-Handler setzen, damit Templates ihn
        # via request.state.csp_nonce im Context-Processor lesen koennen.
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce

        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = CSP_TEMPLATE.format(nonce=nonce)

        proto = request.headers.get("x-forwarded-proto", request.url.scheme)
        if proto == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response
```

- [ ] **Step 4: Tests laufen lassen, PASS erwarten**

Run: `pytest tests/test_security_headers.py -v`
Expected: Alle Tests PASS (inkl. der beiden neuen und der bestehenden). Der bestehende `test_basis_security_header_auf_homepage` bleibt grün, weil die geprüften Substrings (`default-src 'self'`, `https://js.stripe.com`, `frame-ancestors 'none'`) unverändert im CSP stehen.

- [ ] **Step 5: Commit**

```bash
git add app/middleware/security_headers.py tests/test_security_headers.py
git commit -m "feat: CSP-Nonce pro Request, unsafe-inline aus script-src entfernt (#89)"
```

---

## Task 2: Jinja2 Context-Processor für `csp_nonce`

**Files:**
- Modify: `app/templating.py`
- Test: `tests/test_security_headers.py`

- [ ] **Step 1: Failing Test für Nonce im gerenderten HTML**

In `tests/test_security_headers.py` anhängen:

```python
def test_csp_nonce_im_html_vorhanden_und_passt_zum_header(client: TestClient):
    response = client.get("/")
    csp = response.headers["content-security-policy"]
    header_nonce = re.search(r"'nonce-([A-Za-z0-9_\-]+)'", csp).group(1)
    # Der Nonce muss als Attribut im gerenderten <script>-Tag in base.html stehen
    assert f'nonce="{header_nonce}"' in response.text
```

- [ ] **Step 2: Test laufen lassen, FAIL erwarten**

Run: `pytest tests/test_security_headers.py::test_csp_nonce_im_html_vorhanden_und_passt_zum_header -v`
Expected: FAIL — `csp_nonce` ist in Templates nicht verfügbar bzw. noch nicht eingebaut.

- [ ] **Step 3: `app/templating.py` um Context-Processor erweitern**

Ersetze den Inhalt von `app/templating.py` komplett durch:

```python
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
```

- [ ] **Step 4: Inline-Script in `templates/base.html` mit Nonce versehen**

In `templates/base.html` Zeile 8 ändern von:

```html
    <script>
```

zu:

```html
    <script nonce="{{ csp_nonce }}">
```

- [ ] **Step 5: Test laufen lassen, PASS erwarten**

Run: `pytest tests/test_security_headers.py::test_csp_nonce_im_html_vorhanden_und_passt_zum_header -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/templating.py templates/base.html tests/test_security_headers.py
git commit -m "feat: Jinja2 context-processor fuer csp_nonce, base.html annotiert (#89)"
```

---

## Task 3: Nonce in allen restlichen Inline-`<script>`-Blöcken

**Files:**
- Modify: `templates/admin/base.html:9`
- Modify: `templates/admin/login.html:9`
- Modify: `templates/bestaetigung.html:23`
- Modify: `templates/warenkorb.html:37`
- Modify: `templates/checkout.html:129`
- Modify: `templates/admin/bestellung_detail.html:230`

- [ ] **Step 1: Manueller Smoke-Test — App starten und betroffene Seiten aufrufen**

Ziel: Vor der Änderung sehen, dass die Inline-Scripts funktionieren (cart counter, checkout etc.), damit wir nach der Änderung Regressionen erkennen.

Run: `make dev` (oder `uvicorn app.main:app --reload`) und in einem zweiten Terminal:

```bash
curl -s http://localhost:8000/ | grep -c '<script'
```

Kein Assert — nur zur Kontrolle, dass Dev-Server läuft. Server wieder stoppen.

- [ ] **Step 2: `templates/admin/base.html` — Zeile 9 `<script>` → `<script nonce="{{ csp_nonce }}">`**

In `templates/admin/base.html` ändern:

```html
    <script>
```

zu:

```html
    <script nonce="{{ csp_nonce }}">
```

(Nur der zweite `<script>`-Block; der erste auf Zeile 8 ist `<script src="https://cdn.tailwindcss.com"></script>` und braucht keinen Nonce, da externe URL via `script-src` whitelisted ist.)

- [ ] **Step 3: `templates/admin/login.html` — Zeile 9 gleich ändern**

```html
    <script>
```

zu:

```html
    <script nonce="{{ csp_nonce }}">
```

- [ ] **Step 4: `templates/bestaetigung.html` Zeile 23**

Ändern von:

```html
<script>localStorage.removeItem("olivalle-cart");</script>
```

zu:

```html
<script nonce="{{ csp_nonce }}">localStorage.removeItem("olivalle-cart");</script>
```

- [ ] **Step 5: `templates/warenkorb.html` Zeile 37**

```html
<script>
```

zu:

```html
<script nonce="{{ csp_nonce }}">
```

- [ ] **Step 6: `templates/checkout.html` Zeile 129**

```html
<script>
```

zu:

```html
<script nonce="{{ csp_nonce }}">
```

- [ ] **Step 7: `templates/admin/bestellung_detail.html` Zeile 230**

```html
<script>
```

zu:

```html
<script nonce="{{ csp_nonce }}">
```

- [ ] **Step 8: Kein verbleibendes nackter `<script>` ohne `src` oder `nonce`**

Run:

```bash
grep -rn '<script>' templates/
```

Expected: keine Treffer (alle Inline-Scripts haben jetzt `nonce="..."`; `<script src="...">` bleibt erlaubt und wird nicht gematcht).

- [ ] **Step 9: Volle Test-Suite**

Run: `pytest -q`
Expected: Alle Tests PASS.

- [ ] **Step 10: Manueller Smoke-Test in DevTools**

`make dev`, Browser öffnen, folgende Seiten aufrufen und jeweils Console auf CSP-Verletzungen prüfen (sollten keine erscheinen):
- `/` (Produkte)
- `/warenkorb`
- `/checkout` (mit mindestens einem Produkt im Warenkorb)
- `/bestaetigung/...` (nur strukturell)
- `/admin/login`
- `/admin/` (nach Login)

Expected: keine `Refused to execute inline script because it violates the following Content Security Policy directive`-Meldungen.

- [ ] **Step 11: Commit**

```bash
git add templates/
git commit -m "feat: nonce-Attribut an alle verbleibenden Inline-Scripts (#89)"
```

---

## Task 4: Dokumentation & Issue-Abschluss

**Files:**
- Modify: `app/middleware/security_headers.py` (Kommentar ganz oben aktualisieren)
- Modify: `docs/arc42.md` falls CSP dort referenziert

- [ ] **Step 1: Prüfen, ob arc42 CSP erwähnt**

Run: `grep -n "CSP\|Content-Security\|unsafe-inline" docs/arc42.md || true`

Falls Treffer: Abschnitt entsprechend aktualisieren (`'unsafe-inline'` entfernt, Nonce-Mechanismus beschrieben, Referenz auf Issue #89).

- [ ] **Step 2: Altkommentar in `security_headers.py` prüfen**

Der technische-Schuld-Kommentar ist bereits in Task 1 entfallen (komplette Neufassung der Datei). Nichts zu tun. Weiter.

- [ ] **Step 3: `user-stories-testplan.md` gegenchecken**

Run: `grep -n "CSP\|Inline-Script\|nonce" docs/user-stories-testplan.md || true`
Falls Treffer, aktualisieren. Sonst: keine Aktion.

- [ ] **Step 4: Abschluss-Commit (falls Doku-Änderungen)**

```bash
git add docs/
git commit -m "docs: CSP-Nonce-Haertung in arc42 dokumentiert (#89)"
```

- [ ] **Step 5: Issue-Referenz & Memory-Check**

- GitHub Issue #89 wird erst nach Review/Merge geschlossen (per PR).
- Keine neue Memory nötig (technische Änderung, aus Code/Git ableitbar).
- #88 bleibt offen und unabhängig.

---

## Self-Review

- **Spec coverage (Design #89 Teil 2):**
  - Nonce-Generierung + `request.state` + Header → Task 1 ✓
  - Jinja2 Context-Processor `csp_nonce` → Task 2 ✓
  - Alle Inline-Scripts annotiert → Task 2 (base.html) + Task 3 (rest) ✓
  - `'unsafe-inline'` aus `script-src` raus → Task 1 ✓
  - Tests: Header-Präsenz, Nonce pro Request unterschiedlich, Nonce im Template → Task 1 + Task 2 ✓
- **Edge-Case Error-Pages:** Fallback auf leeren String im Context-Processor (siehe Task 2, Step 3) — Template rendert ohne Crash, nicht-middleware-bedingte Renderpfade funktionieren weiter.
- **`'unsafe-eval'` bleibt drin:** Bewusst — entfällt erst mit #88 (Tailwind lokal builden). Im Plan-Header + CSP-Kommentar explizit gemacht.
- **Placeholder-Scan:** keine TBDs/TODOs; jede Änderung zeigt exaktes Before/After.
- **Typ-/Namenskonsistenz:** `request.state.csp_nonce` ↔ `csp_nonce_processor` ↔ `{{ csp_nonce }}` durchgehend identisch.
