# Admin CSRF-Validierung Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** CSRF-Tokens in allen vier Admin-POST-Endpoints serverseitig validieren (#70).

**Architecture:** Eine FastAPI-Dependency `require_csrf` in `app/csrf.py` liest das Form-Feld `csrf_token`, validiert via bestehendem `validiere_csrf_token` und wirft bei Misserfolg `HTTPException(403)`. Pro betroffenem Endpoint per `dependencies=[Depends(require_csrf)]` eingehängt. Bestehende Admin-Tests werden auf gültiges Token umgestellt; neue Tests decken die 403-Pfade ab.

**Tech Stack:** FastAPI, pytest, itsdangerous (bereits im Einsatz).

**Spec:** `docs/superpowers/specs/2026-04-07-admin-csrf-design.md`

---

## File Structure

- **Modify** `app/csrf.py` — neue Dependency `require_csrf` hinzufügen
- **Modify** `app/routers/admin.py` — Dependency an 4 Endpoints hängen, alte `csrf_token`-Form-Parameter entfernen
- **Modify** `tests/test_api_admin.py` — bestehende Tests senden gültiges Token via `csrf_token`-Fixture
- **Create** `tests/test_admin_csrf.py` — neue Tests für 403-Pfade (fehlendes/ungültiges Token)

---

## Task 1: Dependency `require_csrf` in `app/csrf.py`

**Files:**
- Modify: `app/csrf.py`
- Test: `tests/test_csrf.py` (bestehende Datei erweitern)

- [ ] **Step 1: Failing-Test schreiben**

In `tests/test_csrf.py` ans Ende anhängen:

```python
import pytest
from fastapi import HTTPException
from app.csrf import require_csrf, generiere_csrf_token
from app.config import settings


def test_require_csrf_akzeptiert_gueltiges_token():
    token = generiere_csrf_token(settings.secret_key)
    # Darf nicht werfen
    require_csrf(csrf_token=token)


def test_require_csrf_wirft_bei_leerem_token():
    with pytest.raises(HTTPException) as exc:
        require_csrf(csrf_token="")
    assert exc.value.status_code == 403


def test_require_csrf_wirft_bei_ungueltigem_token():
    with pytest.raises(HTTPException) as exc:
        require_csrf(csrf_token="garbage")
    assert exc.value.status_code == 403
```

- [ ] **Step 2: Tests laufen lassen, müssen scheitern**

Run: `pytest tests/test_csrf.py -v`
Expected: ImportError für `require_csrf`.

- [ ] **Step 3: Dependency implementieren**

In `app/csrf.py` ergänzen:

```python
from fastapi import Form, HTTPException

from app.config import settings


def require_csrf(csrf_token: str = Form("")) -> None:
    if not validiere_csrf_token(csrf_token, settings.secret_key):
        raise HTTPException(status_code=403, detail="Ungültiges CSRF-Token")
```

- [ ] **Step 4: Tests laufen lassen, müssen grün sein**

Run: `pytest tests/test_csrf.py -v`
Expected: alle drei neuen Tests PASS.

- [ ] **Step 5: Commit**

```bash
git add app/csrf.py tests/test_csrf.py
git commit -m "feat: require_csrf Dependency für CSRF-Validierung (#70)"
```

---

## Task 2: Dependency an Admin-POST-Endpoints hängen

**Files:**
- Modify: `app/routers/admin.py`
- Modify: `tests/test_api_admin.py`

- [ ] **Step 1: Bestehende Admin-Tests auf gültiges CSRF-Token umstellen**

In `tests/test_api_admin.py` für jeden POST-Aufruf das leere `csrf_token` durch die `csrf_token`-Fixture ersetzen. Die Fixture existiert in `tests/conftest.py:48`.

Beispiele:

```python
# Vorher
admin_client.post(
    "/admin/login",
    data={"password": "testpass", "csrf_token": ""},
)

# Nachher
def test_login(admin_client, csrf_token):
    resp = admin_client.post(
        "/admin/login",
        data={"password": "testpass", "csrf_token": csrf_token},
    )
```

Betroffene Stellen (siehe `grep -n csrf tests/test_api_admin.py`): Zeilen ~34, ~44, ~59, ~100, ~152, ~184, ~197. Jede Test-Funktion, die einen dieser POSTs aufruft, bekommt `csrf_token` als Parameter und sendet ihn als Wert.

- [ ] **Step 2: Tests laufen lassen — sollten weiterhin grün sein (Validierung noch nicht aktiv)**

Run: `pytest tests/test_api_admin.py -v`
Expected: PASS (Endpoints akzeptieren das Token, validieren es aber noch nicht).

- [ ] **Step 3: Failing-Test für 403 ohne Token schreiben**

Neue Datei `tests/test_admin_csrf.py`:

```python
"""Tests: Admin-POST-Endpoints lehnen Requests ohne/ungültiges CSRF-Token ab."""

import pytest


@pytest.fixture
def order_id(admin_client, csrf_token):
    """Erstellt eine Bestellung über den Test-Helper für Detail-Endpoints."""
    from tests.test_api_admin import _seed_bestellung
    return _seed_bestellung()


@pytest.mark.parametrize(
    "method,path,data",
    [
        ("post", "/admin/login", {"password": "testpass"}),
        ("post", "/admin/logout", {}),
    ],
)
def test_admin_post_ohne_csrf_token_403(admin_client, method, path, data):
    resp = admin_client.request(method, path, data=data)
    assert resp.status_code == 403


@pytest.mark.parametrize(
    "method,path,data",
    [
        ("post", "/admin/login", {"password": "testpass", "csrf_token": "garbage"}),
        ("post", "/admin/logout", {"csrf_token": "garbage"}),
    ],
)
def test_admin_post_ungueltiges_csrf_token_403(admin_client, method, path, data):
    resp = admin_client.request(method, path, data=data)
    assert resp.status_code == 403


def test_status_endpoint_ohne_csrf_403(admin_client, order_id):
    resp = admin_client.post(
        f"/admin/bestellungen/{order_id}/status",
        data={"neuer_status": "bezahlt"},
    )
    assert resp.status_code == 403


def test_status_endpoint_ungueltiges_csrf_403(admin_client, order_id):
    resp = admin_client.post(
        f"/admin/bestellungen/{order_id}/status",
        data={"neuer_status": "bezahlt", "csrf_token": "garbage"},
    )
    assert resp.status_code == 403


def test_notiz_endpoint_ohne_csrf_403(admin_client, order_id):
    resp = admin_client.post(
        f"/admin/bestellungen/{order_id}/notiz",
        data={"typ": "notiz_hinzugefuegt", "text": "x"},
    )
    assert resp.status_code == 403


def test_notiz_endpoint_ungueltiges_csrf_403(admin_client, order_id):
    resp = admin_client.post(
        f"/admin/bestellungen/{order_id}/notiz",
        data={"typ": "notiz_hinzugefuegt", "text": "x", "csrf_token": "garbage"},
    )
    assert resp.status_code == 403
```

**Hinweis:** Falls `tests/test_api_admin.py` keine `_seed_bestellung`-Helper-Funktion bietet, prüfe die existierenden Tests dort und kopiere die Setup-Logik direkt in die Fixture (bestellung in DB schreiben, ID zurückgeben). Keine TODO-Verweise hinterlassen.

- [ ] **Step 4: Tests laufen lassen, müssen scheitern**

Run: `pytest tests/test_admin_csrf.py -v`
Expected: FAIL — Endpoints liefern 303/200 statt 403, weil Validierung noch nicht aktiv.

- [ ] **Step 5: Dependency in `app/routers/admin.py` einhängen**

Imports oben ergänzen:

```python
from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Request

from app.csrf import generiere_csrf_token, require_csrf
```

(`Depends` neu, `require_csrf` neu, `generiere_csrf_token` bleibt.)

Dann an jedem der vier POST-Endpoints `dependencies=[Depends(require_csrf)]` hinzufügen und den `csrf_token: str = Form("")`-Parameter aus der Signatur entfernen.

Beispiel `/admin/login`:

```python
@router.post("/login", dependencies=[Depends(require_csrf)])
def admin_login(
    request: Request,
    password: str = Form(),
):
    ...
```

Beispiel `/admin/logout`:

```python
@router.post("/logout", dependencies=[Depends(require_csrf)])
def admin_logout(
    request: Request,
    admin_session: str | None = Cookie(None),
):
    ...
```

Beispiel `/admin/bestellungen/{bestellung_id}/status`:

```python
@router.post(
    "/bestellungen/{bestellung_id}/status",
    dependencies=[Depends(require_csrf)],
)
def admin_status_aendern(
    request: Request,
    bestellung_id: int,
    neuer_status: str = Form(),
    admin_session: str | None = Cookie(None),
):
    ...
```

Beispiel `/admin/bestellungen/{bestellung_id}/notiz`:

```python
@router.post(
    "/bestellungen/{bestellung_id}/notiz",
    dependencies=[Depends(require_csrf)],
)
def admin_notiz_hinzufuegen(
    request: Request,
    bestellung_id: int,
    typ: str = Form(),
    text: str = Form(),
    admin_session: str | None = Cookie(None),
):
    ...
```

- [ ] **Step 6: Neue Tests laufen lassen, müssen grün sein**

Run: `pytest tests/test_admin_csrf.py -v`
Expected: alle 8 Tests PASS.

- [ ] **Step 7: Komplette Test-Suite laufen lassen**

Run: `pytest -q`
Expected: alle Tests PASS. Falls bestehende Admin-Tests fehlschlagen, weil sie noch ein leeres `csrf_token` senden → in Step 1 übersehen, jetzt nachziehen.

- [ ] **Step 8: Ruff prüfen**

Run: `ruff check app/ tests/`
Expected: keine Fehler.

- [ ] **Step 9: Commit**

```bash
git add app/routers/admin.py tests/test_api_admin.py tests/test_admin_csrf.py
git commit -m "feat: CSRF-Validierung in Admin-POST-Endpoints (#70)"
```

---

## Task 3: Issue schliessen & Dokumentation

- [ ] **Step 1: Issue-Verweis im Commit prüfen**

Der Commit-Message in Task 2 referenziert `(#70)`. GitHub schliesst das Issue beim Merge nicht automatisch — Issue wird beim PR via "Closes #70" im Body geschlossen.

- [ ] **Step 2: Smoke-Test manuell (optional, falls lokaler Admin-Account vorhanden)**

```bash
make dev
# Browser: http://localhost:8000/admin/login
# Login → Bestellung-Detail → Status ändern: muss funktionieren
# Mit DevTools csrf_token aus Form entfernen → POST muss 403 liefern
```

- [ ] **Step 3: Push & PR**

```bash
git push -u origin <branch>
gh pr create --title "fix: CSRF-Validierung in Admin-POSTs erzwingen (#70)" --body "Closes #70

## Summary
- Neue \`require_csrf\` Dependency in \`app/csrf.py\`
- Vier Admin-POST-Endpoints validieren CSRF jetzt serverseitig
- Tests für 403-Pfade in \`tests/test_admin_csrf.py\`

## Test plan
- [ ] \`pytest -q\` grün
- [ ] Manueller Smoke-Test im Admin-Bereich"
```

---

## Self-Review Notes

- Spec-Coverage: alle 4 Endpoints abgedeckt (Task 2 Step 5), Tests für 3 Fälle × 4 Endpoints (Task 2 Step 3, plus DoD-Punkt im Spec).
- Login-Lockout-Hinweis aus Spec: bestehende Login-Tests in `test_api_admin.py` müssen gültiges Token mitsenden — Task 2 Step 1 erledigt das.
- Keine Platzhalter; alle Code-Blöcke vollständig.
- `_seed_bestellung`-Helper: falls nicht existent, in Task 2 Step 3 Hinweis auf Inline-Setup gegeben.
