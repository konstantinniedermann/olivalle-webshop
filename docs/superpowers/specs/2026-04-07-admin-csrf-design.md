# Admin CSRF-Validierung erzwingen (#70)

## Problem

In `app/routers/admin.py` werden CSRF-Tokens als Form-Feld angenommen, aber nie validiert. Betroffene Endpoints:

- `POST /admin/login`
- `POST /admin/logout`
- `POST /admin/bestellungen/{id}/status`
- `POST /admin/bestellungen/{id}/notiz`

Nur `POST /bestellen` (`app/routers/bestellungen.py`) validiert das Token tatsächlich. `samesite=strict` mildert das Risiko, ist aber kein vollwertiger Schutz.

**Auswirkung:** Ein eingeloggter Admin kann via CSRF zu Statusänderungen, Notizen oder Logout gezwungen werden.

## Lösung

Eine FastAPI-Dependency `require_csrf` validiert das Token einheitlich und wird per `dependencies=[Depends(require_csrf)]` an jeden betroffenen Endpoint gehängt.

### Neue Dependency

Definiert in `app/csrf.py` (bestehende Datei, hält CSRF-Logik beieinander):

```python
from fastapi import Form, HTTPException

def require_csrf(csrf_token: str = Form("")) -> None:
    if not validiere_csrf_token(csrf_token, settings.secret_key):
        raise HTTPException(403, "Ungültiges CSRF-Token")
```

### Änderungen in `app/routers/admin.py`

Vier POST-Endpoints erhalten `dependencies=[Depends(require_csrf)]`. Der `csrf_token: str = Form("")`-Parameter wird aus den Handler-Signaturen entfernt — die Dependency liest ihn selbst:

- `POST /admin/login`
- `POST /admin/logout`
- `POST /admin/bestellungen/{bestellung_id}/status`
- `POST /admin/bestellungen/{bestellung_id}/notiz`

### Login-Endpoint: Lockout-Verhalten

Dependencies laufen **vor** dem Handler. Konsequenz: Bei Login-Brute-Force mit ungültigem CSRF-Token wird 403 zurückgegeben, bevor der `login_guard.is_locked`-Pfad erreicht wird. Das ist akzeptabel (sogar härter), muss aber in Tests berücksichtigt werden: Login-Lockout-Tests müssen ein gültiges Token mitsenden.

## Tests

Neue Datei `tests/test_admin_csrf.py`:

Pro betroffenem Endpoint:
- POST ohne Token → 403
- POST mit ungültigem Token → 403
- POST mit gültigem Token → erwarteter Erfolg (303 Redirect bzw. 200)

Bestehende Tests, die diese Endpoints aufrufen, müssen ein gültiges CSRF-Token mitsenden — falls bisher nicht der Fall, anpassen.

## Nicht im Scope

- Migration von `POST /bestellen` auf `require_csrf` (separater Refactor-Issue, wenn gewünscht)
- Weitere Admin-Refactorings

## Definition of Done

- [ ] `require_csrf`-Dependency in `app/csrf.py` definiert
- [ ] Vier Admin-POST-Endpoints nutzen die Dependency
- [ ] `csrf_token`-Form-Parameter aus den Handler-Signaturen entfernt
- [ ] Neue Tests in `tests/test_admin_csrf.py` (3 Fälle × 4 Endpoints)
- [ ] Bestehende Tests laufen grün
- [ ] Ruff sauber
