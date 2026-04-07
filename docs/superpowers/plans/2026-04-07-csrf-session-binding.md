# CSRF Session-Binding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** CSRF-Tokens an eine pro-Nutzer eindeutige Identity binden, sodass Token von Nutzer A bei Nutzer B abgelehnt werden (Issue #77).

**Architecture:** `app/csrf.py` signiert künftig eine Identity statt `"csrf"`. Admin-Identity = `sha256(admin_session_cookie)[:32]`, anonyme Identity = neues `csrf_id`-Cookie (16 random bytes hex). `require_csrf` ermittelt die Identity automatisch aus `Request`. Templates bleiben unverändert.

**Tech Stack:** FastAPI, itsdangerous, pytest, TestClient.

**Spec:** `docs/superpowers/specs/2026-04-07-csrf-session-binding-design.md`

---

## File Structure

- Modify `app/csrf.py` — neue Signatur mit Identity, Helper für Identity-Resolution.
- Modify `app/routers/admin.py` — Admin-Identity beim Token-Erzeugen verwenden.
- Modify `app/routers/rabattcodes.py` — dito.
- Modify `app/routers/bestellungen.py` — `csrf_id`-Cookie + Identity beim Checkout.
- Modify `tests/test_csrf.py` — Identity-Tests, alte Tests anpassen.
- Modify `tests/test_admin_csrf.py` — Cross-Identity-Test ergänzen.

---

## Task 1: Neue csrf.py mit Identity-Binding (TDD)

**Files:**
- Modify: `app/csrf.py`
- Modify: `tests/test_csrf.py`

- [ ] **Step 1: Failing Tests schreiben**

Ersetze `tests/test_csrf.py` Inhalt durch:

```python
import time

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.csrf import (
    admin_identity,
    generiere_csrf_token,
    require_csrf,
    validiere_csrf_token,
)


def _make_request(cookies: dict[str, str]) -> Request:
    cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items()).encode()
    scope = {
        "type": "http",
        "headers": [(b"cookie", cookie_header)] if cookie_header else [],
    }
    return Request(scope)


def test_token_roundtrip_mit_identity():
    token = generiere_csrf_token("secret", identity="user-A")
    assert validiere_csrf_token(token, "secret", expected_identity="user-A")


def test_token_andere_identity_abgelehnt():
    token = generiere_csrf_token("secret", identity="user-A")
    assert not validiere_csrf_token(token, "secret", expected_identity="user-B")


def test_token_leere_identity_abgelehnt():
    token = generiere_csrf_token("secret", identity="user-A")
    assert not validiere_csrf_token(token, "secret", expected_identity="")


def test_token_ungueltig():
    assert not validiere_csrf_token("garbage", "secret", expected_identity="x")


def test_token_abgelaufen():
    token = generiere_csrf_token("secret", identity="x", max_age=-1)
    time.sleep(0.1)
    assert not validiere_csrf_token(
        token, "secret", expected_identity="x", max_age=-1
    )


def test_admin_identity_stabil_und_unterschiedlich():
    a = admin_identity("session-token-a")
    b = admin_identity("session-token-b")
    assert a == admin_identity("session-token-a")
    assert a != b
    assert "session-token-a" not in a  # nicht im Klartext


def test_require_csrf_admin_kontext_ok():
    from app.config import settings

    identity = admin_identity("admin-cookie-1")
    token = generiere_csrf_token(settings.secret_key, identity=identity)
    request = _make_request({"admin_session": "admin-cookie-1"})
    require_csrf(request=request, csrf_token=token)


def test_require_csrf_admin_kontext_falsche_session_403():
    from app.config import settings

    identity = admin_identity("admin-cookie-1")
    token = generiere_csrf_token(settings.secret_key, identity=identity)
    request = _make_request({"admin_session": "admin-cookie-OTHER"})
    with pytest.raises(HTTPException) as exc:
        require_csrf(request=request, csrf_token=token)
    assert exc.value.status_code == 403


def test_require_csrf_anonym_kontext_ok():
    from app.config import settings

    token = generiere_csrf_token(settings.secret_key, identity="anon-1")
    request = _make_request({"csrf_id": "anon-1"})
    require_csrf(request=request, csrf_token=token)


def test_require_csrf_anonym_kontext_fremder_cookie_403():
    from app.config import settings

    token = generiere_csrf_token(settings.secret_key, identity="anon-1")
    request = _make_request({"csrf_id": "anon-OTHER"})
    with pytest.raises(HTTPException) as exc:
        require_csrf(request=request, csrf_token=token)
    assert exc.value.status_code == 403


def test_require_csrf_ohne_identity_403():
    from app.config import settings

    token = generiere_csrf_token(settings.secret_key, identity="x")
    request = _make_request({})
    with pytest.raises(HTTPException) as exc:
        require_csrf(request=request, csrf_token=token)
    assert exc.value.status_code == 403


def test_require_csrf_leeres_token_403():
    request = _make_request({"csrf_id": "anon-1"})
    with pytest.raises(HTTPException) as exc:
        require_csrf(request=request, csrf_token="")
    assert exc.value.status_code == 403
```

- [ ] **Step 2: Tests laufen lassen, müssen scheitern**

Run: `pytest tests/test_csrf.py -x`
Expected: ImportError / Fail (admin_identity existiert noch nicht, Signaturen passen nicht).

- [ ] **Step 3: Neue csrf.py implementieren**

Ersetze `app/csrf.py` durch:

```python
import hashlib
import hmac

from fastapi import Form, HTTPException, Request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import settings

CSRF_COOKIE_NAME = "csrf_id"


def generiere_csrf_token(secret: str, identity: str, max_age: int = 3600) -> str:
    s = URLSafeTimedSerializer(secret)
    return s.dumps(identity)


def validiere_csrf_token(
    token: str,
    secret: str,
    expected_identity: str,
    max_age: int = 3600,
) -> bool:
    if not token or not expected_identity:
        return False
    s = URLSafeTimedSerializer(secret)
    try:
        payload = s.loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return False
    if not isinstance(payload, str):
        return False
    return hmac.compare_digest(payload, expected_identity)


def admin_identity(admin_session_cookie: str) -> str:
    """Stabile, nicht-reversible Identity aus dem Admin-Session-Cookie."""
    digest = hashlib.sha256(admin_session_cookie.encode("utf-8")).hexdigest()
    return f"admin:{digest[:32]}"


def resolve_identity(request: Request) -> str | None:
    """Wählt Admin- oder Anonym-Identity passend zum Request."""
    admin_cookie = request.cookies.get("admin_session")
    if admin_cookie:
        return admin_identity(admin_cookie)
    csrf_id = request.cookies.get(CSRF_COOKIE_NAME)
    if csrf_id:
        return f"anon:{csrf_id}"
    return None


def require_csrf(request: Request, csrf_token: str = Form("")) -> None:
    identity = resolve_identity(request)
    if not identity or not validiere_csrf_token(
        csrf_token, settings.secret_key, expected_identity=identity
    ):
        raise HTTPException(status_code=403, detail="Ungültiges CSRF-Token")
```

Note: `resolve_identity` matcht das `f"anon:{csrf_id}"`-Muster — Aufrufer in `bestellungen.py` müssen denselben Prefix verwenden (siehe Task 3).

- [ ] **Step 4: Tests anpassen — anonyme Tests müssen Prefix nutzen**

In den drei Tests `test_require_csrf_anonym_*` den Token mit `identity=f"anon:anon-1"` erzeugen, statt `"anon-1"`. Konkret:

```python
def test_require_csrf_anonym_kontext_ok():
    from app.config import settings

    token = generiere_csrf_token(settings.secret_key, identity="anon:anon-1")
    request = _make_request({"csrf_id": "anon-1"})
    require_csrf(request=request, csrf_token=token)


def test_require_csrf_anonym_kontext_fremder_cookie_403():
    from app.config import settings

    token = generiere_csrf_token(settings.secret_key, identity="anon:anon-1")
    request = _make_request({"csrf_id": "anon-OTHER"})
    with pytest.raises(HTTPException) as exc:
        require_csrf(request=request, csrf_token=token)
    assert exc.value.status_code == 403
```

- [ ] **Step 5: Tests laufen lassen**

Run: `pytest tests/test_csrf.py -v`
Expected: alle PASS.

- [ ] **Step 6: Commit**

```bash
git add app/csrf.py tests/test_csrf.py
git commit -m "feat: CSRF-Token an Identity binden (#77)"
```

---

## Task 2: Admin-Router auf Identity umstellen

**Files:**
- Modify: `app/routers/admin.py`
- Modify: `app/routers/rabattcodes.py`

- [ ] **Step 1: Tests laufen lassen, sehen was bricht**

Run: `pytest tests/test_admin_csrf.py tests/test_api_admin.py tests/test_api_rabattcodes.py -x`
Expected: TypeError — `generiere_csrf_token()` braucht jetzt `identity`.

- [ ] **Step 2: admin.py anpassen**

In `app/routers/admin.py`:

Import erweitern:
```python
from app.csrf import admin_identity, generiere_csrf_token, require_csrf
```

Helper direkt nach `_get_admin_label` einfügen:
```python
def _csrf_for(admin_session: str | None) -> str:
    """Identity für CSRF-Token: Admin-Session falls vorhanden, sonst leerer String → Login-Flow."""
    return admin_identity(admin_session) if admin_session else "anon-pending"
```

Login-GET (Zeile ~62) nutzt anonymen Flow — wir brauchen `csrf_id`-Cookie. Ersetze die Funktion:
```python
@router.get("/login")
def admin_login_page(
    request: Request,
    response: Response,
    csrf_id: str | None = Cookie(None),
):
    from app.csrf import CSRF_COOKIE_NAME
    import secrets

    if not csrf_id:
        csrf_id = secrets.token_hex(16)
    csrf_token = generiere_csrf_token(
        settings.secret_key, identity=f"anon:{csrf_id}"
    )
    rendered = templates.TemplateResponse(
        request, "admin/login.html", {"csrf_token": csrf_token}
    )
    rendered.set_cookie(
        CSRF_COOKIE_NAME,
        csrf_id,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=3600,
    )
    return rendered
```

`Response` ggf. importieren: `from fastapi import Cookie, Depends, Form, Request, Response`.

In `admin_login` (POST) — die Fehler-Renderings (Zeilen ~80, ~100) brauchen ebenfalls Identity. Da hier `require_csrf` schon validiert hat, ist `csrf_id` im Request vorhanden. Helper:

```python
def _anon_csrf(request: Request) -> str:
    csrf_id = request.cookies.get("csrf_id", "")
    return generiere_csrf_token(settings.secret_key, identity=f"anon:{csrf_id}")
```

Ersetze die zwei `csrf = generiere_csrf_token(settings.secret_key)` in `admin_login` durch `csrf = _anon_csrf(request)`.

In `admin_dashboard` (~177) und `admin_log` (~214): Token mit Admin-Identity:
```python
csrf = generiere_csrf_token(
    settings.secret_key, identity=admin_identity(admin_session or "")
)
```

- [ ] **Step 3: rabattcodes.py anpassen**

In `app/routers/rabattcodes.py`:

Import:
```python
from app.csrf import admin_identity, generiere_csrf_token
```

Alle drei `csrf = generiere_csrf_token(settings.secret_key)` ersetzen durch:
```python
csrf = generiere_csrf_token(
    settings.secret_key, identity=admin_identity(admin_session or "")
)
```

(Die Funktion `admin_session` Cookie-Param ist in jeder dieser Routen schon vorhanden — siehe `app/routers/rabattcodes.py`.)

- [ ] **Step 4: Tests laufen lassen**

Run: `pytest tests/test_admin_csrf.py tests/test_api_admin.py tests/test_api_rabattcodes.py -x`
Expected: PASS. Falls einer der Tests einen vorgenerierten Token nutzt, muss er den Cookie-Roundtrip verwenden — TestClient persistiert Cookies automatisch zwischen GET/POST, also sollte es funktionieren.

- [ ] **Step 5: Commit**

```bash
git add app/routers/admin.py app/routers/rabattcodes.py
git commit -m "feat: Admin-CSRF an Session-Identity binden (#77)"
```

---

## Task 3: Checkout-Router auf csrf_id-Cookie umstellen

**Files:**
- Modify: `app/routers/bestellungen.py`
- Modify: `tests/test_csrf.py` (Integration-Test)

- [ ] **Step 1: Failing Test schreiben**

In `tests/test_csrf.py` ans Ende anhängen:

```python
def test_bestellen_csrf_id_roundtrip(client):
    import json

    # GET setzt csrf_id-Cookie und liefert passendes Token
    get_resp = client.get("/checkout")
    assert get_resp.status_code == 200
    assert "csrf_id" in client.cookies

    # Token aus HTML extrahieren
    import re
    match = re.search(r'name="csrf_token" value="([^"]+)"', get_resp.text)
    assert match, "csrf_token nicht im Template gefunden"
    token = match.group(1)

    cart = json.dumps([{"produkt_id": 1, "menge": 1}])
    payload = {
        "vorname": "Max", "nachname": "Muster",
        "email": "max@test.ch", "strasse": "Str. 1",
        "plz": "4600", "ort": "Olten",
        "versandart": "abholung", "zahlungsart": "rechnung",
        "cart_data": cart, "kommentar": "",
        "csrf_token": token,
    }
    resp = client.post("/bestellen", data=payload)
    # Akzeptiert (200/303) oder Folgefehler — wichtig: NICHT 403
    assert resp.status_code != 403


def test_bestellen_fremdes_token_abgelehnt(client):
    import json
    from app.config import settings
    from app.csrf import generiere_csrf_token

    # Token gehört zu csrf_id "fremd", Client hat aber anderen Cookie
    fremdes_token = generiere_csrf_token(
        settings.secret_key, identity="anon:fremd"
    )
    client.get("/checkout")  # setzt eigenen csrf_id
    cart = json.dumps([{"produkt_id": 1, "menge": 1}])
    resp = client.post("/bestellen", data={
        "vorname": "Max", "nachname": "Muster",
        "email": "max@test.ch", "strasse": "Str. 1",
        "plz": "4600", "ort": "Olten",
        "versandart": "abholung", "zahlungsart": "rechnung",
        "cart_data": cart, "kommentar": "",
        "csrf_token": fremdes_token,
    })
    assert resp.status_code == 403
```

- [ ] **Step 2: Tests laufen lassen — müssen scheitern**

Run: `pytest tests/test_csrf.py::test_bestellen_csrf_id_roundtrip tests/test_csrf.py::test_bestellen_fremdes_token_abgelehnt -v`
Expected: FAIL (kein csrf_id-Cookie, falsche Identity).

- [ ] **Step 3: bestellungen.py anpassen**

In `app/routers/bestellungen.py`:

Import:
```python
import secrets
from app.csrf import (
    CSRF_COOKIE_NAME,
    generiere_csrf_token,
    validiere_csrf_token,
)
```

`Cookie` und `Response` aus fastapi importieren falls noch nicht.

`checkout_seite` ersetzen:
```python
@router.get("/checkout")
def checkout_seite(
    request: Request,
    csrf_id: str | None = Cookie(None),
):
    if not csrf_id:
        csrf_id = secrets.token_hex(16)
    csrf_token = generiere_csrf_token(
        settings.secret_key, identity=f"anon:{csrf_id}"
    )
    response = templates.TemplateResponse(
        request,
        "checkout.html",
        {"csrf_token": csrf_token, "active_page": "checkout"},
    )
    response.set_cookie(
        CSRF_COOKIE_NAME,
        csrf_id,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=3600,
    )
    return response
```

In `bestellen` (POST): `csrf_id`-Cookie als Param ergänzen und Validierung umstellen:
```python
def bestellen(
    request: Request,
    ...
    csrf_token: str = Form(""),
    csrf_id: str | None = Cookie(None),
):
    if not csrf_id or not validiere_csrf_token(
        csrf_token, settings.secret_key, expected_identity=f"anon:{csrf_id}"
    ):
        raise HTTPException(403, "Ungültiges CSRF-Token")
    ...
```

Hinweis: Das `/checkout`-Template muss vor jedem Bestell-POST aufgerufen worden sein, damit der Cookie existiert. Bei Direktaufruf von `/bestellen` ohne vorherigen GET → 403 (gewollt).

- [ ] **Step 4: Tests laufen lassen**

Run: `pytest tests/test_csrf.py -v`
Expected: alle PASS.

- [ ] **Step 5: Restliche Suite laufen lassen**

Run: `pytest -x`
Expected: alle PASS. Falls `test_e2e_bestellzyklus` oder `test_api_bestellungen` brechen: prüfen ob sie `/checkout` GET vor `/bestellen` POST aufrufen und denselben TestClient verwenden — sonst entsprechend ergänzen (Cookie-Persistenz im TestClient erledigt den Rest).

- [ ] **Step 6: Commit**

```bash
git add app/routers/bestellungen.py tests/test_csrf.py
git commit -m "feat: Checkout-CSRF an csrf_id-Cookie binden (#77)"
```

---

## Task 4: Verifikation & Doku

- [ ] **Step 1: Volle Suite + Lint**

Run: `pytest && ruff check app tests`
Expected: alle grün.

- [ ] **Step 2: arc42 Sicherheitskapitel ergänzen**

In `docs/arc42.md` im Sicherheits-/Querschnittskapitel einen Absatz ergänzen (falls vorhanden — sonst überspringen):

> **CSRF-Schutz:** Tokens werden an eine pro-Nutzer eindeutige Identity gebunden — Admin-Routen an `sha256(admin_session)`, anonyme Routen an ein `csrf_id`-Cookie (Double-Submit). Dadurch ist ein Token nicht mehr universell wiederverwendbar (Issue #77).

- [ ] **Step 3: Commit & Issue schliessen**

```bash
git add docs/arc42.md
git commit -m "docs: CSRF-Identity-Binding in arc42 (#77)"
```

PR erstellen mit `gh pr create`, Body referenziert "Closes #77".
