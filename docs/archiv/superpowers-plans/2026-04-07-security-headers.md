# Security-Header Middleware Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eine FastAPI-Middleware setzt fünf Standard-Security-Header (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy) auf jede Response.

**Architecture:** Eine `BaseHTTPMiddleware`-Klasse in `app/middleware/security_headers.py`, registriert in `app/main.py` direkt nach `redirect_www`. Keine externe Library. HSTS nur, wenn Request via HTTPS (X-Forwarded-Proto). CSP pragmatisch — Inline-Scripts/Tailwind-CDN/Stripe/Google-Fonts erlaubt, da Refactoring im Folge-Issue.

**Tech Stack:** FastAPI, Starlette `BaseHTTPMiddleware`, pytest, `fastapi.testclient.TestClient`.

**Spec:** `docs/superpowers/specs/2026-04-07-security-headers-design.md`

---

## File Structure

- **Create:** `app/middleware/__init__.py` — leeres Package-Init.
- **Create:** `app/middleware/security_headers.py` — `SecurityHeadersMiddleware` Klasse + CSP-Konstante.
- **Modify:** `app/main.py` — Middleware importieren und via `app.add_middleware(...)` registrieren.
- **Create:** `tests/test_security_headers.py` — Header-Checks via TestClient.

---

### Task 1: Middleware-Modul mit Tests anlegen

**Files:**
- Create: `app/middleware/__init__.py`
- Create: `app/middleware/security_headers.py`
- Test: `tests/test_security_headers.py`

- [ ] **Step 1: Failing Test schreiben**

Datei `tests/test_security_headers.py`:

```python
from fastapi.testclient import TestClient


def test_basis_security_header_auf_homepage(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    csp = response.headers["content-security-policy"]
    assert "default-src 'self'" in csp
    assert "https://js.stripe.com" in csp
    assert "frame-ancestors 'none'" in csp


def test_hsts_nur_bei_https(client: TestClient):
    # ohne x-forwarded-proto: kein HSTS
    response = client.get("/health")
    assert "strict-transport-security" not in response.headers

    # mit x-forwarded-proto: https → HSTS
    response = client.get("/health", headers={"x-forwarded-proto": "https"})
    hsts = response.headers["strict-transport-security"]
    assert "max-age=31536000" in hsts
    assert "includeSubDomains" in hsts


def test_admin_login_frame_ancestors(client: TestClient):
    response = client.get("/admin/login")
    assert response.status_code == 200
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
```

- [ ] **Step 2: Test laufen lassen, Fehler bestätigen**

Run: `pytest tests/test_security_headers.py -v`
Expected: FAIL — Header fehlen (`KeyError: 'x-content-type-options'`).

- [ ] **Step 3: Package-Init anlegen**

Datei `app/middleware/__init__.py`:

```python
```

(Leere Datei.)

- [ ] **Step 4: Middleware implementieren**

Datei `app/middleware/security_headers.py`:

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
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
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = CSP

        proto = request.headers.get("x-forwarded-proto", request.url.scheme)
        if proto == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response
```

- [ ] **Step 5: Middleware in `app/main.py` registrieren**

Datei `app/main.py`, nach Zeile 20 (nach `redirect_www`-Middleware), folgende Zeilen einfügen:

```python
from app.middleware.security_headers import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
```

Den Import oben zu den anderen Imports verschieben (Ruff-konform).

Resultierende Import-Sektion in `app/main.py`:

```python
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.middleware.security_headers import SecurityHeadersMiddleware
```

Und nach der `redirect_www`-Middleware:

```python
app.add_middleware(SecurityHeadersMiddleware)
```

- [ ] **Step 6: Tests laufen lassen**

Run: `pytest tests/test_security_headers.py -v`
Expected: PASS — alle drei Tests grün.

- [ ] **Step 7: Volle Testsuite laufen lassen**

Run: `pytest -q`
Expected: alle bisherigen Tests weiterhin grün (keine Regressions durch neue Header).

- [ ] **Step 8: Ruff-Check**

Run: `ruff check app/middleware/security_headers.py app/main.py tests/test_security_headers.py`
Expected: keine Fehler.

Run: `ruff format app/middleware/security_headers.py app/main.py tests/test_security_headers.py`

- [ ] **Step 9: Commit**

```bash
git add app/middleware/__init__.py app/middleware/security_headers.py app/main.py tests/test_security_headers.py
git commit -m "feat: Security-Header Middleware (#74)"
```

---

### Task 2: Folge-Issue für CSP-Härtung anlegen

- [ ] **Step 1: GitHub Issue erstellen**

Run:

```bash
gh issue create \
  --title "Security: Inline-Scripts entfernen, Tailwind builden, CSP mit Nonces härten" \
  --label "phase-3,technisch,security" \
  --body "Folge zu #74. Aktuell erlaubt die CSP 'unsafe-inline' und 'unsafe-eval' für Scripts, weil:

- Tailwind via cdn.tailwindcss.com zur Laufzeit evaluiert
- Mehrere Templates Inline-<script>-Blöcke enthalten (checkout.html, warenkorb.html, bestaetigung.html, admin/*, base.html)

## Aufgaben
- [ ] Tailwind als Build-Step (lokales CSS statt CDN)
- [ ] Inline-Scripts in externe JS-Dateien auslagern ODER per CSP-Nonce erlauben
- [ ] CSP härten: 'unsafe-inline' und 'unsafe-eval' aus script-src entfernen
- [ ] Tests anpassen

Blocked by: #74"
```

- [ ] **Step 2: Issue-Nummer notieren**

Die zurückgegebene Issue-URL/Nummer im Plan-Status oder als Kommentar im Original-Issue #74 vermerken.

- [ ] **Step 3: Issue #74 schliessen**

```bash
gh issue close 74 --comment "Erledigt via PR. Folge-Issue für CSP-Härtung mit Nonces angelegt."
```

(Erst nach Merge ausführen.)

---

## Self-Review

- **Spec coverage:** Alle 5 Header aus der Spec sind in `SecurityHeadersMiddleware.dispatch` gesetzt. CSP-Direktiven matchen 1:1 die Spec. HSTS-Bedingung (nur HTTPS) abgedeckt. Tests decken alle drei in der Spec genannten Cases ab. Folge-Issue als Task 2 vorhanden.
- **Placeholders:** Keine TODOs/TBDs.
- **Type/Naming consistency:** `SecurityHeadersMiddleware` und `CSP` durchgängig identisch verwendet.
