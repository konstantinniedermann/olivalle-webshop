# Rate-Limit auf /bestellen und /admin/login (Issue #75)

## Problem
- `/bestellen` (POST) hat kein Rate-Limit → DB-Spam, Brevo-Quota (300/Tag Free) kann verbrannt werden.
- `/admin/login` hat zwar `BruteForceGuard` (Lockout nach 5 Fehlversuchen), aber kein generelles Anfragen-Limit pro Zeitfenster.

## Lösung
Eigener `RateLimiter` analog `BruteForceGuard` — sliding window in-memory, pro IP. Konsistent mit bestehendem Pattern, keine neue Dependency.

## Komponenten

### `app/services/rate_limit.py` (neu)
```python
class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int): ...
    def check(self, ip: str) -> bool:
        """True wenn erlaubt, False wenn Limit überschritten.
        Registriert den Request beim Aufruf."""
```

Implementierung: dict[ip, list[timestamp]], alte Einträge ausserhalb Window werden bei jedem `check` gepruned.

Modul-Singletons:
- `bestellung_limiter = RateLimiter(max_requests=10, window_seconds=60)`
- `login_limiter = RateLimiter(max_requests=5, window_seconds=60)`

### Integration

**`app/routers/bestellungen.py`** — POST-Handler:
```python
ip = get_client_ip(request)
if not bestellung_limiter.check(ip):
    raise HTTPException(429, "Zu viele Anfragen, bitte später erneut versuchen.")
```

**`app/routers/admin.py`** — Login-Handler: gleiche Logik mit `login_limiter`, *vor* der bestehenden BruteForceGuard-Prüfung.

### Tests (`tests/test_rate_limit.py`)
- 10 erlaubte Requests, 11. → False
- Unterschiedliche IPs interferieren nicht
- Ablauf des Windows (mit `monkeypatch` auf `time.time`) → wieder erlaubt
- Integrationstest: 11 POSTs auf `/bestellen` via TestClient → letzter ist 429
- Integrationstest: 6 POSTs auf `/admin/login` → letzter ist 429

## Out of Scope
- Persistenter Storage (Redis o.ä.) — in-memory reicht für 1-Container fly.io.
- Globale Middleware — gezielte Anwendung pro Endpoint ist flexibler.
- Rate-Limit für GET-Endpoints.

## Abhängigkeiten
- Bereits gemerged: #71 (echte Client-IP via `get_client_ip`).
