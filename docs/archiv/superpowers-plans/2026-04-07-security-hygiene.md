# Security-Hygiene Sammelissue (#78) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fünf kleine Security-Hygiene-Fixes für Olivalle umsetzen (Issue #78).

**Architecture:** Drei Code-Änderungen (health, parse_credentials, login-oracle), zwei Doku-Ergänzungen (Template-Audit, DSG-Logging). Alle in einem Branch / einem PR.

**Tech Stack:** FastAPI, pytest, bcrypt, Jinja2.

**Spec:** `docs/superpowers/specs/2026-04-07-security-hygiene-design.md`

---

## File Structure

| Datei | Action | Verantwortung |
|---|---|---|
| `app/main.py` | modify L25-27 | `/health` ohne `version` |
| `app/services/auth_service.py` | modify L7-15 | Fail-Fast in `parse_credentials` |
| `app/routers/admin.py` | modify L106-112 | Lockout-Response = Invalid-Password-Response |
| `tests/test_health.py` | modify | kein `version`-Assertion |
| `tests/test_auth_service.py` | add test | `parse_credentials` ValueError |
| `tests/test_admin_login_rate_limit.py` | add test | Lockout-Body == Invalid-Password-Body |
| `docs/security.md` | create | Template-Audit-Notiz |
| `docs/datenschutz.md` | create | DSG-Eintrag client_ip-Logging |

---

## Task 1: `/health` minimieren

**Files:**
- Modify: `app/main.py:25-27`
- Test: `tests/test_health.py`

- [ ] **Step 1: Test anpassen (failing)**

Ersetze `tests/test_health.py` komplett:

```python
from fastapi.testclient import TestClient


def test_health_gibt_nur_status_zurueck(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}
    assert "version" not in data
```

- [ ] **Step 2: Test laufen lassen — soll fehlschlagen**

Run: `pytest tests/test_health.py -v`
Expected: FAIL — `version` ist noch in Response.

- [ ] **Step 3: Implementation**

In `app/main.py` Zeile 25-27 ersetzen:

```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

`from app.config import settings` wird ggf. weiter unten noch gebraucht — nicht entfernen, nur prüfen mit `grep settings app/main.py`.

- [ ] **Step 4: Test grün**

Run: `pytest tests/test_health.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/main.py tests/test_health.py
git commit -m "fix: /health exponiert app_version nicht mehr (#78)"
```

---

## Task 2: `parse_credentials` Fail-Fast

**Files:**
- Modify: `app/services/auth_service.py:7-15`
- Test: `tests/test_auth_service.py` (in `class TestParseCredentials`)

- [ ] **Step 1: Failing Test ergänzen**

In `tests/test_auth_service.py` innerhalb `class TestParseCredentials` ergänzen:

```python
    def test_parse_invalid_entry_raises(self):
        import pytest

        from app.services.auth_service import parse_credentials

        with pytest.raises(ValueError, match="enthält kein ':'"):
            parse_credentials("kein-doppelpunkt")
```

- [ ] **Step 2: Test laufen lassen — soll fehlschlagen**

Run: `pytest tests/test_auth_service.py::TestParseCredentials::test_parse_invalid_entry_raises -v`
Expected: FAIL — aktuell wirft `split(":", 1)` zwar ValueError beim Unpacking, aber ohne die erwartete Meldung.

- [ ] **Step 3: Implementation**

In `app/services/auth_service.py` Funktion `parse_credentials` ersetzen:

```python
def parse_credentials(credentials_str: str) -> list[tuple[str, str]]:
    """Parse 'label:hash,label:hash' into [(label, hash), ...]."""
    if not credentials_str.strip():
        return []
    result = []
    for entry in credentials_str.split(","):
        if ":" not in entry:
            raise ValueError(
                f"ADMIN_CREDENTIALS: Eintrag '{entry}' enthält kein ':' "
                f"(Format: label:bcrypt_hash)"
            )
        label, bcrypt_hash = entry.split(":", 1)
        result.append((label.strip(), bcrypt_hash.strip()))
    return result
```

- [ ] **Step 4: Tests grün**

Run: `pytest tests/test_auth_service.py -v`
Expected: PASS (alle Tests inkl. neuer)

- [ ] **Step 5: Commit**

```bash
git add app/services/auth_service.py tests/test_auth_service.py
git commit -m "fix: parse_credentials Fail-Fast mit klarer Fehlermeldung (#78)"
```

---

## Task 3: Lockout-Oracle schliessen

**Files:**
- Modify: `app/routers/admin.py:106-112`
- Test: `tests/test_admin_login_rate_limit.py`

- [ ] **Step 1: Failing Test ergänzen**

Am Ende von `tests/test_admin_login_rate_limit.py` ergänzen:

```python
def test_lockout_response_indistinguishable_from_invalid_password():
    """Lockout darf nicht durch Polling erkennbar sein."""
    from app.services.auth_service import login_guard

    client = TestClient(app)
    csrf = _login_csrf(client)

    # Erster Versuch mit falschem Passwort -> Invalid-Password-Body
    r1 = client.post("/admin/login", data={"password": "x", "csrf_token": csrf})
    assert r1.status_code == 200
    assert "Ungültiges Passwort" in r1.text

    # Lockout erzwingen (BruteForceGuard direkt füttern, IP = testclient)
    for _ in range(10):
        login_guard.record_failure("testclient")

    # Zweiter Versuch -> Lockout, aber gleicher Body
    r2 = client.post("/admin/login", data={"password": "x", "csrf_token": csrf})
    assert "Ungültiges Passwort" in r2.text
    assert "Zu viele Fehlversuche" not in r2.text

    login_guard.reset("testclient")
```

- [ ] **Step 2: Test laufen lassen — soll fehlschlagen**

Run: `pytest tests/test_admin_login_rate_limit.py::test_lockout_response_indistinguishable_from_invalid_password -v`
Expected: FAIL — aktuell zeigt Lockout-Branch `"Zu viele Fehlversuche..."`.

Hinweis: Falls `get_client_ip` nicht `"testclient"` zurückliefert, muss die IP angepasst werden. Vor dem Implementation-Step kurz prüfen via `print(get_client_ip(request))` oder `app/middleware`-Inspektion. Falls TestClient die IP nicht setzt, das Test-Setup mit `client = TestClient(app, client=("testclient", 50000))` initialisieren.

- [ ] **Step 3: Implementation**

In `app/routers/admin.py` die Zeilen 106-112 ersetzen:

```python
    if login_guard.is_locked(client_ip):
        csrf = _anon_csrf(request)
        return templates.TemplateResponse(
            request,
            "admin/login.html",
            {"csrf_token": csrf, "error": "Ungültiges Passwort."},
        )
```

(Nur die Error-Message ändert sich von `"Zu viele Fehlversuche. Bitte warten."` auf `"Ungültiges Passwort."`.)

- [ ] **Step 4: Tests grün**

Run: `pytest tests/test_admin_login_rate_limit.py -v`
Expected: PASS (beide Tests).

Run: `pytest -q` — Vollsuite muss grün bleiben.

- [ ] **Step 5: Commit**

```bash
git add app/routers/admin.py tests/test_admin_login_rate_limit.py
git commit -m "fix: Login-Lockout-Status nicht mehr durch Response leakbar (#78)"
```

---

## Task 4: Template-Audit dokumentieren

**Files:**
- Create: `docs/security.md`

- [ ] **Step 1: Verifizieren dass Audit aktuell ist**

Run: `grep -rn "|safe\|Markup(" templates/ app/ || echo "no matches"`
Expected: `no matches`

Falls Treffer: STOPP, im Spec ist dokumentiert dass nichts da ist — neue Findings müssen erst geprüft werden.

- [ ] **Step 2: `docs/security.md` anlegen**

```markdown
# Security-Notizen

Querschnittsdokumentation zu Security-relevanten Entscheidungen und Audits.

## Template-XSS-Audit

**Stand:** 2026-04-07

`grep -rn "|safe\|Markup(" templates/ app/` findet keine Treffer. Es gibt
aktuell keine Stelle, an der Jinja2-Autoescape umgangen wird.

**Regel für die Zukunft:** Bei jeder neuen Verwendung von `|safe` oder
`Markup()` prüfen, ob Userinput in den markupten String fliessen kann.
Nur statische, vertrauenswürdige Strings markupen. Im Zweifel: stattdessen
escapen lassen.
```

- [ ] **Step 3: Commit**

```bash
git add docs/security.md
git commit -m "docs: Template-XSS-Audit-Notiz (#78)"
```

---

## Task 5: DSG-Dokumentation client_ip-Logging

**Files:**
- Create: `docs/datenschutz.md`

- [ ] **Step 1: `docs/datenschutz.md` anlegen**

```markdown
# Datenschutz — interne Notizen

Diese Datei dokumentiert Personenbezug-relevante Datenverarbeitungen im
Olivalle-Webshop. Grundlage: Schweizer DSG.

## Admin-Log: client_ip

**Speicherort:** Tabelle `admin_log`, Spalte `details` (via
`admin_repo.log_eintrag_schreiben`).

**Daten:** Zeitstempel, `admin_label`, `aktion`, `client_ip`.

**Zweck:**
- Brute-Force-Schutz (Lockout pro IP)
- Audit-Trail für administrative Aktionen

**Rechtsgrundlage:** Berechtigtes Interesse (IT-Sicherheit, Nachvollzieh-
barkeit von Admin-Eingriffen).

**Aufbewahrungsfrist:** 90 Tage (Vorschlag, noch nicht automatisiert).

**Löschkonzept:** Aktuell manuell. TODO: automatischer Cleanup-Job in
einer späteren Iteration (separates Issue tracken).

**Betroffenenrechte:** Auf Anfrage Einsicht/Löschung über den Inhaber
möglich. Da nur Admin-Aktionen geloggt werden und Admins identisch mit
dem Inhaber sind, ist der Personenbezug auf Drittpersonen minimal.
```

- [ ] **Step 2: Commit**

```bash
git add docs/datenschutz.md
git commit -m "docs: DSG-Notiz zu client_ip-Logging (#78)"
```

---

## Task 6: Final Check + PR

- [ ] **Step 1: Vollsuite + Linter**

Run: `pytest -q && ruff check app tests`
Expected: alles grün.

- [ ] **Step 2: PR erstellen**

```bash
gh pr create --title "Security: Hygiene-Sammelissue (#78)" --body "$(cat <<'EOF'
## Summary
- /health exponiert app_version nicht mehr
- parse_credentials Fail-Fast mit klarer Fehlermeldung
- Login-Lockout-Status nicht mehr durch Response leakbar
- Template-XSS-Audit dokumentiert (docs/security.md)
- DSG-Notiz zu client_ip-Logging (docs/datenschutz.md)

Closes #78

## Test plan
- [x] pytest -q grün
- [x] ruff check grün
EOF
)"
```

- [ ] **Step 3: Issue-Status updaten**

Sobald PR gemerged: Issue #78 schliesst automatisch via `Closes #78`.
