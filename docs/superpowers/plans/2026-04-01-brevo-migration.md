# Brevo-Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** E-Mail-Provider von Resend auf Brevo umstellen (Issue #60)

**Architecture:** Austausch des Resend SDK durch `brevo-python` v4 im E-Mail-Service. Die Schnittstelle (`sende_bestellbestaetigung`) bleibt identisch — nur die interne Implementierung ändert sich. Config, .env.example und alle Test-Mocks werden angepasst.

**Tech Stack:** brevo-python v4 (PyPI: `brevo-python`), FastAPI, pytest

---

### Task 1: Dependency austauschen

**Files:**
- Modify: `pyproject.toml:11` (`resend>=2` → `brevo-python>=4`)

- [ ] **Step 1: pyproject.toml anpassen**

```toml
# Zeile 11 ändern von:
    "resend>=2",
# zu:
    "brevo-python>=4",
```

- [ ] **Step 2: Dependencies installieren**

Run: `uv sync`
Expected: brevo-python wird installiert, resend entfernt

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "refactor: resend durch brevo-python in Dependencies ersetzen"
```

---

### Task 2: Config anpassen

**Files:**
- Modify: `app/config.py:14` (`resend_api_key` → `brevo_api_key`)
- Modify: `.env.example:6-7` (Resend → Brevo Sektion)

- [ ] **Step 1: Config-Klasse anpassen**

In `app/config.py`, Zeile 14 ändern:

```python
# Von:
    resend_api_key: str = ""
# Zu:
    brevo_api_key: str = ""
```

- [ ] **Step 2: .env.example anpassen**

```env
# Von:
# Resend
RESEND_API_KEY=re_...

# Zu:
# Brevo (E-Mail-Provider)
BREVO_API_KEY=xkeysib-...
```

- [ ] **Step 3: Commit**

```bash
git add app/config.py .env.example
git commit -m "refactor: Config von Resend auf Brevo umbenennen"
```

---

### Task 3: E-Mail-Service umschreiben (TDD)

**Files:**
- Modify: `tests/test_email_service.py` (Mock-Pfad + Assertions anpassen)
- Modify: `app/services/email_service.py` (Resend → Brevo SDK)

- [ ] **Step 1: Test anpassen — neuer Mock-Pfad**

`tests/test_email_service.py` komplett ersetzen:

```python
from unittest.mock import MagicMock, patch

from app.services.email_service import sende_bestellbestaetigung


@patch("app.services.email_service.brevo_client")
def test_sende_bestellbestaetigung(mock_client):
    mock_client.transactional_emails.send_transac_email.return_value = MagicMock(
        message_id="email_123"
    )
    result = sende_bestellbestaetigung(
        empfaenger="max@test.ch",
        bestell_id=1,
        kunde={"vorname": "Max", "nachname": "Muster"},
        positionen=[{"name": "Olivenöl 250ml", "menge": 2, "einzelpreis_chf": 8.0}],
        versandkosten=9.90,
        total=25.90,
    )
    assert result is not None
    mock_client.transactional_emails.send_transac_email.assert_called_once()
    call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
    assert call_kwargs["to"][0]["email"] == "max@test.ch"
    assert "Bestellbestätigung" in call_kwargs["subject"]


@patch("app.services.email_service.brevo_client")
def test_sende_bestellbestaetigung_mit_anhang(mock_client):
    mock_client.transactional_emails.send_transac_email.return_value = MagicMock(
        message_id="email_456"
    )
    svg_bytes = b"<svg>test</svg>"
    result = sende_bestellbestaetigung(
        empfaenger="max@test.ch",
        bestell_id=2,
        kunde={"vorname": "Max", "nachname": "Muster"},
        positionen=[{"name": "Olivenöl 750ml", "menge": 1, "einzelpreis_chf": 18.0}],
        versandkosten=0.0,
        total=18.0,
        anhang=svg_bytes,
    )
    assert result is not None
    call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
    assert call_kwargs["attachment"][0]["name"] == "rechnung-2.svg"
    assert "content" in call_kwargs["attachment"][0]
```

- [ ] **Step 2: Test laufen lassen — soll fehlschlagen**

Run: `pytest tests/test_email_service.py -v`
Expected: FAIL — `brevo_client` existiert noch nicht in email_service

- [ ] **Step 3: E-Mail-Service implementieren**

`app/services/email_service.py` komplett ersetzen:

```python
import base64
import sqlite3
from pathlib import Path

from brevo import Brevo
from jinja2 import Environment, FileSystemLoader

from app.config import settings

brevo_client = Brevo(api_key=settings.brevo_api_key)

TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "emails"
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


def sende_bestellbestaetigung(
    empfaenger: str,
    bestell_id: int,
    kunde: dict,
    positionen: list[dict],
    versandkosten: float,
    total: float,
    anhang: bytes | None = None,
    conn: sqlite3.Connection | None = None,
) -> object:
    template = env.get_template("bestellbestaetigung.html")
    html = template.render(
        kunde=kunde,
        bestell_id=bestell_id,
        positionen=positionen,
        versandkosten=versandkosten,
        total=total,
    )

    params: dict = {
        "sender": {"email": "bestellung@olivalle.ch", "name": "Olivalle"},
        "to": [{"email": empfaenger}],
        "reply_to": {"email": "olivalle.olten@outlook.com"},
        "subject": f"Olivalle — Bestellbestätigung #{bestell_id}",
        "html_content": html,
    }

    if anhang:
        params["attachment"] = [
            {
                "content": base64.b64encode(anhang).decode("utf-8"),
                "name": f"rechnung-{bestell_id}.svg",
            }
        ]

    result = brevo_client.transactional_emails.send_transac_email(**params)

    if conn:
        from app.repositories.admin_repo import log_eintrag_schreiben

        log_eintrag_schreiben(
            conn,
            admin_label="system",
            aktion="email_ausgang",
            details=f"An: {empfaenger} — Olivalle — Bestellbestätigung #{bestell_id}",
            bestellung_id=bestell_id,
        )

    return result
```

**Wichtige Unterschiede zu Resend:**
- Anhänge: `base64.b64encode(bytes)` statt `list(bytes)` — Brevo erwartet Base64-String
- Sender: Dict mit `email` + `name` statt Freeform-String
- Reply-To: Dict mit `email` statt String
- To: Liste von Dicts mit `email`-Key statt Liste von Strings

- [ ] **Step 4: Tests laufen lassen — sollen grün sein**

Run: `pytest tests/test_email_service.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add app/services/email_service.py tests/test_email_service.py
git commit -m "feat: E-Mail-Service von Resend auf Brevo SDK umstellen"
```

---

### Task 4: Mock-Pfad in allen anderen Tests anpassen

**Files:**
- Modify: `tests/test_api_webhooks.py` (3 Stellen)
- Modify: `tests/test_e2e_bestellzyklus.py` (3 Stellen)
- Modify: `tests/test_api_bestellungen.py` (1 Stelle)
- Modify: `tests/test_api_admin.py` (1 Stelle)

Jede Zeile mit `"app.services.email_service.resend.Emails.send"` ersetzen durch `"app.services.email_service.brevo_client"`.

- [ ] **Step 1: test_api_webhooks.py — 3 Mocks anpassen**

Alle 3 Vorkommen (Zeilen 6, 58, 76) ersetzen:

```python
# Von:
@patch("app.services.email_service.resend.Emails.send", return_value={"id": "test"})
# Zu:
@patch("app.services.email_service.brevo_client")
```

In den Testfunktionen: `mock_send` Parameter bleibt, da er nur als Platzhalter dient und nicht direkt geprüft wird.

- [ ] **Step 2: test_e2e_bestellzyklus.py — 3 Mocks anpassen**

Alle 3 Vorkommen (Zeilen 29, 177, 296) gleich ersetzen:

```python
# Von:
@patch("app.services.email_service.resend.Emails.send", return_value={"id": "test"})
# Zu:
@patch("app.services.email_service.brevo_client")
```

- [ ] **Step 3: test_api_bestellungen.py — 1 Mock anpassen**

Zeile 23:

```python
# Von:
@patch("app.services.email_service.resend.Emails.send", return_value={"id": "test"})
# Zu:
@patch("app.services.email_service.brevo_client")
```

- [ ] **Step 4: test_api_admin.py — 1 Mock anpassen**

Zeile 113:

```python
# Von:
            "app.services.email_service.resend.Emails.send", lambda **kw: {"id": "mock"}
# Zu:
            "app.services.email_service.brevo_client"
```

- [ ] **Step 5: Alle Tests laufen lassen**

Run: `pytest -v`
Expected: Alle Tests grün

- [ ] **Step 6: Commit**

```bash
git add tests/
git commit -m "refactor: Resend-Mocks in allen Tests durch Brevo-Mock ersetzen"
```

---

### Task 5: GitHub Issue aktualisieren

**Files:** Keine Code-Dateien

- [ ] **Step 1: Issue #60 kommentieren — was erledigt ist und was noch offen**

Kommentar auf Issue #60:

```markdown
## Code-Umstellung erledigt ✅

- [x] `pyproject.toml`: `resend>=2` → `brevo-python>=4`
- [x] `app/config.py`: `resend_api_key` → `brevo_api_key`
- [x] `app/services/email_service.py`: Resend SDK → Brevo SDK
- [x] `.env.example`: `RESEND_API_KEY` → `BREVO_API_KEY`
- [x] Tests angepasst (alle Mock-Pfade)

## Noch offen (manuelle Setup-Schritte, eigene Session)

- [ ] Brevo-Account einrichten und API-Key generieren
- [ ] DNS: SPF/DKIM-Einträge für Brevo bei Infomaniak setzen
- [ ] `.env` lokal mit echtem BREVO_API_KEY befüllen
- [ ] Test-Mail über Brevo versenden und verifizieren
- [ ] fly.io Secret: `BREVO_API_KEY` setzen (→ Issue #45)
```

- [ ] **Step 2: Issue-Abhängigkeiten prüfen**

Issue #24 (Rechnungsstellung) referenziert `#50 (Resend Account)` — muss auf Brevo-Account angepasst werden.
Issue #45 (fly.io Secrets) listet `RESEND_API_KEY` — muss auf `BREVO_API_KEY` angepasst werden.
