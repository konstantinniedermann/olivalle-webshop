# CSRF-Token an Identität binden (Issue #77)

## Problem
`app/csrf.py` signiert immer den festen String `"csrf"`. Jedes Token ist bis zum Ablauf (1h) für jeden Nutzer gültig — kein echter CSRF-Schutz, nur ein Token mit Ablaufdatum. Ein Angreifer, der einmal ein gültiges Token kennt (z. B. aus einer fremden Session), kann es im Namen eines anderen Nutzers verwenden.

## Ziel
Tokens an eine pro-Nutzer eindeutige Identität binden, sodass ein Token von Nutzer A bei Nutzer B abgelehnt wird. Eine einheitliche API für beide Kontexte (anonymer Checkout, eingeloggter Admin).

## Design

### Neue API in `app/csrf.py`
```python
def generiere_csrf_token(secret: str, identity: str, max_age: int = 3600) -> str
def validiere_csrf_token(token: str, secret: str, expected_identity: str, max_age: int = 3600) -> bool
def require_csrf(request: Request, csrf_token: str = Form("")) -> None
```

- `generiere_csrf_token` signiert die übergebene `identity` statt `"csrf"`.
- `validiere_csrf_token` lädt den Payload und vergleicht ihn mit `expected_identity` (constant-time, `hmac.compare_digest`).
- `require_csrf` ermittelt die Identity aus dem `Request` (siehe unten) und ruft die Validierung auf.

### Identity-Quelle pro Kontext

**Admin (eingeloggt):** `identity = sha256(admin_session_cookie)[:32]`. Solange das Session-Cookie existiert, ist die Identity stabil; ein Angreifer ohne dieses Cookie kann kein passendes Token erzeugen. Hash, damit Token-Payload den Session-Wert nicht im Klartext enthält.

**Anonym (Checkout `/bestellen`):** Beim GET wird ein `csrf_id`-Cookie gesetzt, falls noch keines existiert: 16 random bytes, hex, `httponly`, `samesite=lax`, `secure` analog zu bestehenden Cookies, Lebensdauer = `max_age`. `identity = csrf_id`. Beim POST kommt der Cookie automatisch mit, der Server vergleicht ihn mit dem Token-Payload (Double-Submit über Signatur).

`require_csrf` wählt die Quelle automatisch: ist `admin_session` vorhanden und gültig → Admin-Identity, sonst `csrf_id`-Cookie → Anonym-Identity. Fehlt beides oder passt nichts → 403.

### Aufrufstellen anpassen
- `app/routers/admin.py`: alle `generiere_csrf_token(settings.secret_key)`-Aufrufe bekommen die Admin-Identity (Helper `_admin_csrf_identity(admin_session)`).
- `app/routers/rabattcodes.py`: dito.
- `app/routers/bestellungen.py`:
  - GET `/bestellen`: `csrf_id`-Cookie sicherstellen (setzen falls nicht da), Token mit dieser Identity erzeugen.
  - POST `/bestellen`: Identity aus Cookie lesen, validieren. Manuelle `validiere_csrf_token`-Stelle nutzt die neue Signatur.

Templates bleiben unverändert (`{{ csrf_token }}` Hidden-Field).

## Tests (`tests/test_csrf.py` erweitern + neu)
- Token von Identity A wird bei Identity B abgelehnt.
- Gültiges Token + passende Identity = ok.
- Abgelaufenes Token = abgelehnt.
- Manipulierter Payload = abgelehnt.
- Integration:
  - Admin POST mit Token aus *anderem* Login-Session-Cookie → 403.
  - Checkout POST ohne `csrf_id`-Cookie → 403.
  - Checkout POST mit Token, das zu einem fremden `csrf_id` gehört → 403.
- Bestehender Happy-Path Login + Checkout darf nicht brechen.

## Out of Scope
- Kein neuer Storage, keine DB-Tabelle.
- Keine Änderung an Cookie-Namen für `admin_session`.
- Keine Rotation des Tokens nach Login (kann später als separates Issue).

## Risiken / Hinweise
- `csrf_id` muss vor dem Rendern des GET-Templates gesetzt werden, damit Token und Cookie zur selben Identity gehören. Tests müssen den Cookie-Roundtrip via `TestClient` machen.
- `require_csrf` benötigt Zugriff auf `Request` (Cookies). Bisherige `Depends(require_csrf)`-Aufrufe funktionieren weiter, weil FastAPI `Request` injiziert.
