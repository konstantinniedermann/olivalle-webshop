# Security-Hygiene Sammelissue (#78)

**Datum:** 2026-04-07
**Issue:** #78
**Scope:** 5 kleine Security-Hygiene-Fixes in einem PR.

## Kontext

Sammelissue mit fünf voneinander unabhängigen Findings aus dem laufenden Security-Audit (Phase 3). Jeder Punkt ist klein, gemeinsam getrackt für Effizienz.

## Änderungen

### 1. `/health` minimieren — `app/main.py:27`

`app_version` aus der Health-Response entfernen, um Footprinting-Vektor zu schliessen.

**Vorher:** `{"status": "ok", "version": settings.app_version}`
**Nachher:** `{"status": "ok"}`

Test in `tests/test_health.py` anpassen (kein `version`-Key in Response).

### 2. `parse_credentials` Fail-Fast — `app/services/auth_service.py:13`

`entry.split(":", 1)` crasht mit `ValueError` bei fehlendem `:`, was zur Login-Zeit eine 500er produziert. Validierung ergänzen, die mit klarer Meldung scheitert:

```python
if ":" not in entry:
    raise ValueError(
        f"ADMIN_CREDENTIALS: Eintrag '{entry}' enthält kein ':' (Format: label:bcrypt_hash)"
    )
```

Damit ist die Fehlermeldung eindeutig und zeigt direkt auf die Konfiguration. Der Crash erfolgt weiterhin beim ersten Login (lazy parse) — kein Startup-Hard-Fail nötig, da die Funktion nur dort aufgerufen wird.

Test: `test_auth_service.py::test_parse_credentials_invalid` — `parse_credentials("kein-doppelpunkt")` raises ValueError mit erwarteter Meldung.

### 3. Template-Audit dokumentieren

`grep -rn "|safe\|Markup(" templates/ app/` findet **keine Treffer** (Stand 2026-04-07). Kein Code-Change nötig.

Eintrag in `docs/security.md` (Datei neu anlegen falls nicht vorhanden):

> **Template-XSS-Audit (2026-04-07):** Keine Verwendung von `|safe` oder `Markup()` in Templates. Bei zukünftigem Einsatz: prüfen, ob Userinput erreicht werden kann; nur statische, vertrauenswürdige Strings markupen.

### 4. DSG-Dokumentation `client_ip`-Logging

`admin_repo.log_eintrag_schreiben` schreibt `client_ip` in die `admin_log`-Tabelle. DSG-relevant (Personenbezug möglich).

Abschnitt in `docs/datenschutz.md` ergänzen oder Datei neu anlegen:

- **Zweck:** Brute-Force-Schutz, Audit-Trail für Admin-Aktionen
- **Daten:** Zeitstempel, admin_label, Aktion, client_ip
- **Aufbewahrung:** 90 Tage (Vorschlag)
- **Löschkonzept:** Aktuell manuell. TODO: Cleanup-Job in späterer Iteration (separates Issue).
- **Rechtsgrundlage:** Berechtigtes Interesse (Sicherheit)

Kein Code-Change in dieser Iteration.

### 5. Lockout-Oracle schliessen — `app/routers/admin.py:106-132`

Aktuell unterscheidet die Login-Antwort zwischen Lockout (`"Zu viele Fehlversuche..."`) und falschem Passwort (`"Ungültiges Passwort."`). Ein Angreifer kann den Lockout-Status pollen, ohne ein gültiges Passwort senden zu müssen.

**Fix (Variante A):** Beide Branches geben **dieselbe** Fehlermeldung zurück: `"Ungültiges Passwort."`. Lockout-Logik bleibt aktiv (verhindert weiterhin bcrypt-Arbeit während Lockout). Lockout-Status ist von aussen nicht mehr unterscheidbar von einem normalen Fehlversuch.

```python
if login_guard.is_locked(client_ip):
    csrf = _anon_csrf(request)
    return templates.TemplateResponse(
        request,
        "admin/login.html",
        {"csrf_token": csrf, "error": "Ungültiges Passwort."},
    )
```

Test: `test_admin_login.py::test_lockout_response_indistinguishable` — nach max_attempts Fehlversuchen ist der Response-Body identisch zum Body bei einem normalen Fehlversuch (gleicher Error-String).

## Tests

| Datei | Neu/Anpassung | Inhalt |
|---|---|---|
| `tests/test_health.py` | Anpassung | kein `version`-Key |
| `tests/test_auth_service.py` | Neu/Anpassung | `parse_credentials` Fail-Fast |
| `tests/test_admin_login.py` | Neu | Lockout-Response = Invalid-Password-Response |

## Out of Scope

- Persistenter Lockout (bleibt in-memory)
- Automatischer Log-Cleanup-Job (nur Doku)
- CSP / Inline-Scripts (Issue #79)
- Startup-Hard-Fail für `parse_credentials` (Lazy-Validation reicht)

## Definition of Done

- [ ] 5 Änderungen umgesetzt (3 Code, 2 Doku)
- [ ] Tests grün (`make test`)
- [ ] Ruff clean
- [ ] PR erstellt, Issue #78 referenziert
