# Rate-Limit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Per-IP Rate-Limit auf `POST /bestellen` (10/min) und `POST /admin/login` (5/min) gegen Spam und Brevo-Quota-Verbrennen.

**Architecture:** Eigene `RateLimiter`-Klasse (sliding window, in-memory) analog zum bestehenden `BruteForceGuard`. Zwei Modul-Singletons in `app/services/rate_limit.py`. Aufruf direkt im Router via `get_client_ip()`, bei Überschreitung `HTTPException(429)`.

**Tech Stack:** Python, FastAPI, pytest.

---

## File Structure

- **Create:** `app/services/rate_limit.py` — `RateLimiter`-Klasse + Singletons `bestellung_limiter`, `login_limiter`
- **Create:** `tests/test_rate_limit.py` — Unit-Tests für `RateLimiter`
- **Modify:** `app/routers/bestellungen.py` — Limit-Check am Anfang von `bestellen()`
- **Modify:** `app/routers/admin.py` — Limit-Check am Anfang von `admin_login()`
- **Modify:** `tests/test_bestellen_endpoint.py` (oder neu falls fehlt) — Integrationstest 429
- **Modify:** `tests/test_admin.py` (oder ähnlich) — Integrationstest 429

---

### Task 1: RateLimiter-Klasse mit Tests

**Files:**
- Create: `app/services/rate_limit.py`
- Create: `tests/test_rate_limit.py`

- [ ] **Step 1: Failing Test schreiben**

`tests/test_rate_limit.py`:
```python
import time
import pytest
from app.services.rate_limit import RateLimiter


def test_allows_up_to_limit():
    rl = RateLimiter(max_requests=3, window_seconds=60)
    assert rl.check("1.1.1.1") is True
    assert rl.check("1.1.1.1") is True
    assert rl.check("1.1.1.1") is True


def test_blocks_over_limit():
    rl = RateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        rl.check("1.1.1.1")
    assert rl.check("1.1.1.1") is False


def test_separate_ips_independent():
    rl = RateLimiter(max_requests=2, window_seconds=60)
    assert rl.check("1.1.1.1") is True
    assert rl.check("2.2.2.2") is True
    assert rl.check("1.1.1.1") is True
    assert rl.check("2.2.2.2") is True
    assert rl.check("1.1.1.1") is False
    assert rl.check("2.2.2.2") is False


def test_window_expires(monkeypatch):
    current = [1000.0]
    monkeypatch.setattr("app.services.rate_limit.time.time", lambda: current[0])
    rl = RateLimiter(max_requests=2, window_seconds=60)
    assert rl.check("1.1.1.1") is True
    assert rl.check("1.1.1.1") is True
    assert rl.check("1.1.1.1") is False
    current[0] += 61
    assert rl.check("1.1.1.1") is True
```

- [ ] **Step 2: Tests laufen — müssen fehlschlagen**

Run: `pytest tests/test_rate_limit.py -v`
Expected: ImportError / ModuleNotFoundError für `app.services.rate_limit`.

- [ ] **Step 3: RateLimiter implementieren**

`app/services/rate_limit.py`:
```python
"""In-memory per-IP rate limiter (sliding window)."""
import time


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    def check(self, ip: str) -> bool:
        """Registriert Request. True = erlaubt, False = Limit überschritten."""
        now = time.time()
        recent = [
            t for t in self._requests.get(ip, [])
            if now - t < self.window_seconds
        ]
        if len(recent) >= self.max_requests:
            self._requests[ip] = recent
            return False
        recent.append(now)
        self._requests[ip] = recent
        return True


# Module-level singletons
bestellung_limiter = RateLimiter(max_requests=10, window_seconds=60)
login_limiter = RateLimiter(max_requests=5, window_seconds=60)
```

- [ ] **Step 4: Tests laufen — müssen passen**

Run: `pytest tests/test_rate_limit.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add app/services/rate_limit.py tests/test_rate_limit.py
git commit -m "feat: RateLimiter (sliding window, in-memory) (#75)"
```

---

### Task 2: Rate-Limit auf /bestellen

**Files:**
- Modify: `app/routers/bestellungen.py` (am Anfang von `bestellen()`, vor CSRF-Check)
- Test: `tests/test_bestellen_endpoint.py` (falls existiert, sonst neu)

- [ ] **Step 1: Vorhandenen Bestellen-Test prüfen**

Run: `ls tests/ | grep -i bestell`
Falls eine Datei existiert (z.B. `test_bestellen_endpoint.py`), Integrationstest dort ergänzen. Falls nicht, neu anlegen.

- [ ] **Step 2: Failing Integrationstest schreiben**

In `tests/test_bestellen_rate_limit.py` (neu, falls keine geeignete Datei existiert):
```python
from fastapi.testclient import TestClient
from app.main import app
from app.services.rate_limit import bestellung_limiter


def test_bestellen_rate_limit_429(monkeypatch):
    bestellung_limiter._requests.clear()
    client = TestClient(app)
    # 10 erlaubt, 11. blockiert. Body egal — Limit-Check ist erste Zeile.
    for _ in range(10):
        r = client.post("/bestellen", data={})
        assert r.status_code != 429
    r = client.post("/bestellen", data={})
    assert r.status_code == 429
    bestellung_limiter._requests.clear()
```

- [ ] **Step 3: Test laufen — muss fehlschlagen**

Run: `pytest tests/test_bestellen_rate_limit.py -v`
Expected: FAIL — kein 429, weil noch nicht implementiert.

- [ ] **Step 4: Limit-Check in Router einbauen**

`app/routers/bestellungen.py` — Imports ergänzen (oben):
```python
from app.client_ip import get_client_ip
from app.services.rate_limit import bestellung_limiter
```

In `bestellen()` direkt nach der Signatur, **vor** dem CSRF-Check:
```python
    if not bestellung_limiter.check(get_client_ip(request)):
        raise HTTPException(429, "Zu viele Anfragen, bitte später erneut versuchen.")

    if not validiere_csrf_token(csrf_token, settings.secret_key):
        raise HTTPException(403, "Ungültiges CSRF-Token")
```

- [ ] **Step 5: Test laufen — muss passen**

Run: `pytest tests/test_bestellen_rate_limit.py -v`
Expected: 1 passed.

- [ ] **Step 6: Volle Test-Suite laufen**

Run: `pytest -q`
Expected: alle grün. Falls bestehende Bestell-Tests jetzt 429 werfen (gemeinsame Singleton-State), `bestellung_limiter._requests.clear()` als Fixture/Setup ergänzen.

- [ ] **Step 7: Commit**

```bash
git add app/routers/bestellungen.py tests/test_bestellen_rate_limit.py
git commit -m "feat: Rate-Limit 10/min auf /bestellen (#75)"
```

---

### Task 3: Rate-Limit auf /admin/login

**Files:**
- Modify: `app/routers/admin.py` (am Anfang von `admin_login()`)
- Test: `tests/test_admin_login_rate_limit.py` (neu)

- [ ] **Step 1: Failing Integrationstest schreiben**

`tests/test_admin_login_rate_limit.py`:
```python
from fastapi.testclient import TestClient
from app.main import app
from app.services.rate_limit import login_limiter
from app.csrf import generiere_csrf_token
from app.config import settings


def test_admin_login_rate_limit_429():
    login_limiter._requests.clear()
    client = TestClient(app)
    csrf = generiere_csrf_token(settings.secret_key)
    for _ in range(5):
        r = client.post("/admin/login", data={"password": "x", "csrf_token": csrf})
        assert r.status_code != 429
    r = client.post("/admin/login", data={"password": "x", "csrf_token": csrf})
    assert r.status_code == 429
    login_limiter._requests.clear()
```

- [ ] **Step 2: Test laufen — muss fehlschlagen**

Run: `pytest tests/test_admin_login_rate_limit.py -v`
Expected: FAIL — kein 429.

- [ ] **Step 3: Limit-Check in Router einbauen**

`app/routers/admin.py` — Import ergänzen:
```python
from app.services.rate_limit import login_limiter
```

In `admin_login()` als allererste Zeile (vor `login_guard.is_locked`):
```python
    client_ip = get_client_ip(request)
    if not login_limiter.check(client_ip):
        raise HTTPException(429, "Zu viele Anfragen, bitte später erneut versuchen.")

    if login_guard.is_locked(client_ip):
        ...
```
(Die bestehende `client_ip = get_client_ip(request)`-Zeile wird durch obige ersetzt — nicht doppelt aufrufen.)

- [ ] **Step 4: Test laufen — muss passen**

Run: `pytest tests/test_admin_login_rate_limit.py -v`
Expected: 1 passed.

- [ ] **Step 5: Volle Test-Suite**

Run: `pytest -q`
Expected: alle grün. Falls bestehende Admin-Login-Tests betroffen sind (Singleton-State), `login_limiter._requests.clear()` in Setup einfügen.

- [ ] **Step 6: Commit**

```bash
git add app/routers/admin.py tests/test_admin_login_rate_limit.py
git commit -m "feat: Rate-Limit 5/min auf /admin/login (#75)"
```

---

### Task 4: Doku & Issue-Update

- [ ] **Step 1: README/arc42 prüfen**

Run: `grep -n "BruteForceGuard\|Rate-Limit\|rate.limit" README.md docs/arc42.md 2>/dev/null`
Falls Security-Sektion existiert, dort kurzen Hinweis ergänzen: "Rate-Limit (in-memory): 10/min auf /bestellen, 5/min auf /admin/login".

- [ ] **Step 2: Issue #75 schliessen**

```bash
gh issue comment 75 --body "Implementiert via RateLimiter (in-memory, sliding window). 10/min auf /bestellen, 5/min auf /admin/login."
gh issue close 75
```

- [ ] **Step 3: Final Commit (falls Doku-Änderungen)**

```bash
git add README.md docs/arc42.md
git commit -m "docs: Rate-Limit dokumentiert (#75)"
```
