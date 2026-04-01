# Bezahlung bei Abholung + Stakeholder-Benachrichtigung — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Neue Zahlungsoption "Bezahlung bei Abholung" im Checkout + Stakeholder-Mail bei jeder Bestellung.

**Architecture:** Dritter Wert `abholung_bar` in der bestehenden `zahlungsart`-Spalte. Neuer Zweig im Checkout-Handler. Zwei neue E-Mail-Templates + eine neue Funktion `sende_stakeholder_benachrichtigung`. Frontend: Radio-Button per JS ein-/ausblenden. Admin: Prozess-Leiste um neuen Workflow erweitern.

**Tech Stack:** Python/FastAPI, Jinja2, Brevo (E-Mail), Tailwind CSS, SQLite

**Spec:** `docs/superpowers/specs/2026-04-01-bezahlung-abholung-design.md`

---

## File Map

| Aktion | Datei | Verantwortung |
|--------|-------|---------------|
| Modify | `app/models.py:29-34` | `BestellungInput` Kommentar aktualisieren |
| Modify | `app/routers/bestellungen.py:25-143` | Dritter Checkout-Zweig `abholung_bar` |
| Modify | `app/services/email_service.py` | `sende_stakeholder_benachrichtigung()` + Anpassung `sende_status_email()` |
| Create | `templates/emails/bestellbestaetigung_abholung_bar.html` | Kunden-Mail bei Barzahlung |
| Create | `templates/emails/bestellung_stakeholder.html` | Stakeholder-Benachrichtigung |
| Modify | `app/routers/webhooks.py:47-76` | Stakeholder-Mail nach Stripe-Webhook |
| Modify | `templates/checkout.html:64-76` | Radio-Button + JS |
| Modify | `templates/bestaetigung.html:13-17` | Bestätigungstext für `abholung_bar` |
| Modify | `templates/admin/bestellung_detail.html:254-264` | Prozess-Leiste Workflow |
| Modify | `templates/admin/dashboard.html:90` | Zahlungsart-Label |
| Create | `tests/test_abholung_bar.py` | Unit-Tests für neuen Flow |
| Modify | `tests/test_email_service.py` | Tests für Stakeholder-Mail + Status-Email-Logik |
| Modify | `tests/test_e2e_bestellzyklus.py` | E2E-Test für abholung_bar |

---

### Task 1: E-Mail-Templates erstellen

**Files:**
- Create: `templates/emails/bestellbestaetigung_abholung_bar.html`
- Create: `templates/emails/bestellung_stakeholder.html`

- [ ] **Step 1: Kunden-Mail-Template erstellen**

```html
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
    <h1 style="color: #f1d600;">Bestellbestätigung</h1>
    <p>Hallo {{ kunde.vorname }},</p>
    <p>vielen Dank für deine Bestellung bei Olivalle!</p>

    <h2>Bestellung #{{ bestell_id }}</h2>
    <table style="width: 100%; border-collapse: collapse;">
        {% for pos in positionen %}
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 8px;">{{ pos.name }}</td>
            <td style="padding: 8px; text-align: right;">{{ pos.menge }}x</td>
            <td style="padding: 8px; text-align: right;">CHF {{ "%.2f"|format(pos.einzelpreis_chf * pos.menge) }}</td>
        </tr>
        {% endfor %}
        <tr>
            <td style="padding: 8px; font-weight: bold;" colspan="2">Total</td>
            <td style="padding: 8px; text-align: right; font-weight: bold;">CHF {{ "%.2f"|format(total) }}</td>
        </tr>
    </table>

    <p style="margin-top: 20px; padding: 12px; background: #f5f5f5; border-radius: 4px;">
        <strong>Bezahlung bei Abholung:</strong> Der Inhaber wird sich bei dir für einen Abholtermin melden.
        Die Bezahlung erfolgt direkt vor Ort.
    </p>

    <p style="margin-top: 12px; color: #666; font-size: 14px;">
        Möchtest du deine Bestellung stornieren? Kontaktiere uns unter
        <a href="mailto:olivalle.olten@outlook.com">olivalle.olten@outlook.com</a>.
    </p>

    <p style="margin-top: 20px;">Liebe Grüsse<br>Olivalle</p>
</body>
</html>
```

- [ ] **Step 2: Stakeholder-Mail-Template erstellen**

```html
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
    <h1 style="color: #f1d600;">Neue Bestellung #{{ bestell_id }}</h1>

    <table style="width: 100%; border-collapse: collapse; margin-bottom: 16px;">
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 8px; color: #666;">Kunde</td>
            <td style="padding: 8px;">{{ kunde.vorname }} {{ kunde.nachname }}</td>
        </tr>
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 8px; color: #666;">E-Mail</td>
            <td style="padding: 8px;"><a href="mailto:{{ kunde.email }}">{{ kunde.email }}</a></td>
        </tr>
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 8px; color: #666;">Zahlungsart</td>
            <td style="padding: 8px;">{{ zahlungsart_label }}</td>
        </tr>
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 8px; color: #666;">Versandart</td>
            <td style="padding: 8px;">{{ versandart_label }}</td>
        </tr>
    </table>

    <h2>Positionen</h2>
    <table style="width: 100%; border-collapse: collapse;">
        {% for pos in positionen %}
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 8px;">{{ pos.name }}</td>
            <td style="padding: 8px; text-align: right;">{{ pos.menge }}x</td>
            <td style="padding: 8px; text-align: right;">CHF {{ "%.2f"|format(pos.einzelpreis_chf * pos.menge) }}</td>
        </tr>
        {% endfor %}
        {% if versandkosten > 0 %}
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 8px;" colspan="2">Versandkosten</td>
            <td style="padding: 8px; text-align: right;">CHF {{ "%.2f"|format(versandkosten) }}</td>
        </tr>
        {% endif %}
        <tr>
            <td style="padding: 8px; font-weight: bold;" colspan="2">Total</td>
            <td style="padding: 8px; text-align: right; font-weight: bold;">CHF {{ "%.2f"|format(total) }}</td>
        </tr>
    </table>

    {% if zahlungsart == "abholung_bar" %}
    <p style="margin-top: 16px; padding: 12px; background: #fff3cd; border-radius: 4px; border: 1px solid #ffc107;">
        <strong>Aktion nötig:</strong> Bitte kontaktiere den Kunden für einen Abholtermin.
    </p>
    {% endif %}
</body>
</html>
```

- [ ] **Step 3: Commit**

```bash
git add templates/emails/bestellbestaetigung_abholung_bar.html templates/emails/bestellung_stakeholder.html
git commit -m "feat: E-Mail-Templates für Abholung-Bar und Stakeholder-Benachrichtigung (#59)"
```

---

### Task 2: Stakeholder-Benachrichtigung im Email-Service

**Files:**
- Modify: `app/services/email_service.py`
- Create: `tests/test_abholung_bar.py`

- [ ] **Step 1: Failing Test schreiben**

Datei `tests/test_abholung_bar.py` erstellen:

```python
"""Tests für Bezahlung bei Abholung und Stakeholder-Benachrichtigung."""

from unittest.mock import MagicMock, patch

from app.services.email_service import sende_stakeholder_benachrichtigung


@patch("app.services.email_service.brevo_client")
def test_stakeholder_mail_wird_gesendet(mock_client):
    """Stakeholder-Mail enthält Bestelldaten und wird an SH-Adresse geschickt."""
    mock_client.transactional_emails.send_transac_email.return_value = MagicMock(
        message_id="sh_1"
    )
    sende_stakeholder_benachrichtigung(
        bestell_id=42,
        kunde={"vorname": "Anna", "nachname": "Test", "email": "anna@test.ch"},
        positionen=[{"name": "Olivenöl 750ml", "menge": 2, "einzelpreis_chf": 18.0}],
        versandkosten=0.0,
        total=36.0,
        zahlungsart="abholung_bar",
        versandart="abholung",
    )
    mock_client.transactional_emails.send_transac_email.assert_called_once()
    call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
    assert call_kwargs["to"][0]["email"] == "olivalle.olten@outlook.com"
    assert "#42" in call_kwargs["subject"]


@patch("app.services.email_service.brevo_client")
def test_stakeholder_mail_stripe(mock_client):
    """Stakeholder-Mail funktioniert auch für Stripe-Bestellungen."""
    mock_client.transactional_emails.send_transac_email.return_value = MagicMock(
        message_id="sh_2"
    )
    sende_stakeholder_benachrichtigung(
        bestell_id=43,
        kunde={"vorname": "Beat", "nachname": "Stripe", "email": "beat@test.ch"},
        positionen=[{"name": "Olivenöl 250ml", "menge": 1, "einzelpreis_chf": 8.0}],
        versandkosten=9.90,
        total=17.90,
        zahlungsart="stripe",
        versandart="versand",
    )
    mock_client.transactional_emails.send_transac_email.assert_called_once()
    call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
    assert call_kwargs["to"][0]["email"] == "olivalle.olten@outlook.com"
```

- [ ] **Step 2: Test ausführen — muss fehlschlagen**

Run: `python -m pytest tests/test_abholung_bar.py -v`
Expected: FAIL mit `ImportError: cannot import name 'sende_stakeholder_benachrichtigung'`

- [ ] **Step 3: `sende_stakeholder_benachrichtigung` implementieren**

Am Ende von `app/services/email_service.py` hinzufügen:

```python
# Labels für menschenlesbare Anzeige in E-Mails
_ZAHLUNGSART_LABELS: dict[str, str] = {
    "stripe": "Twint / Kreditkarte",
    "rechnung": "Rechnung (QR)",
    "abholung_bar": "Bezahlung bei Abholung",
}

_VERSANDART_LABELS: dict[str, str] = {
    "versand": "Postversand",
    "abholung": "Abholung vor Ort",
}


def sende_stakeholder_benachrichtigung(
    bestell_id: int,
    kunde: dict,
    positionen: list[dict],
    versandkosten: float,
    total: float,
    zahlungsart: str,
    versandart: str,
    conn: sqlite3.Connection | None = None,
) -> object:
    """Benachrichtigt den Stakeholder über eine neue Bestellung."""
    template = env.get_template("bestellung_stakeholder.html")
    html = template.render(
        bestell_id=bestell_id,
        kunde=kunde,
        positionen=positionen,
        versandkosten=versandkosten,
        total=total,
        zahlungsart=zahlungsart,
        zahlungsart_label=_ZAHLUNGSART_LABELS.get(zahlungsart, zahlungsart),
        versandart_label=_VERSANDART_LABELS.get(versandart, versandart),
    )

    result = brevo_client.transactional_emails.send_transac_email(
        sender={"email": "bestellung@olivalle.ch", "name": "Olivalle"},
        to=[{"email": "olivalle.olten@outlook.com"}],
        subject=f"Neue Bestellung #{bestell_id}",
        html_content=html,
    )

    if conn:
        from app.repositories.admin_repo import log_eintrag_schreiben

        log_eintrag_schreiben(
            conn,
            admin_label="system",
            aktion="email_ausgang",
            details=f"An: olivalle.olten@outlook.com — Neue Bestellung #{bestell_id}",
            bestellung_id=bestell_id,
        )

    return result
```

- [ ] **Step 4: Tests ausführen — müssen grün sein**

Run: `python -m pytest tests/test_abholung_bar.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add app/services/email_service.py tests/test_abholung_bar.py
git commit -m "feat: Stakeholder-Benachrichtigung bei neuen Bestellungen (#59)"
```

---

### Task 3: Status-Email-Logik für abholung_bar erweitern

**Files:**
- Modify: `app/services/email_service.py:106`
- Modify: `tests/test_email_service.py`

- [ ] **Step 1: Failing Test schreiben**

In `tests/test_email_service.py` am Ende der Klasse `TestSendeStatusEmail` hinzufügen:

```python
    def test_bezahlt_abholung_bar_sendet_email(self, db):
        """bezahlt + abholung_bar → Zahlungseingangsbestätigung (Admin hat Bar-Zahlung bestätigt)."""
        self._make_bestellung(db, zahlungsart="abholung_bar", versandart="abholung")
        with patch("app.services.email_service.brevo_client") as mock_client:
            mock_client.transactional_emails.send_transac_email.return_value = MagicMock(
                message_id="s_bar"
            )
            sende_status_email(bestellung_id=1, neuer_status="bezahlt", conn=db)
            mock_client.transactional_emails.send_transac_email.assert_called_once()
            call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
            assert "Zahlungseingang" in call_kwargs["subject"]
```

- [ ] **Step 2: Test ausführen — muss fehlschlagen**

Run: `python -m pytest tests/test_email_service.py::TestSendeStatusEmail::test_bezahlt_abholung_bar_sendet_email -v`
Expected: FAIL — die aktuelle Logik in Zeile 106 prüft `zahlungsart != "rechnung"` und gibt bei `abholung_bar` vorzeitig zurück.

- [ ] **Step 3: Logik in `sende_status_email` anpassen**

In `app/services/email_service.py`, Zeile 106 ändern von:

```python
    if neuer_status == "bezahlt" and zahlungsart != "rechnung":
        return
```

zu:

```python
    if neuer_status == "bezahlt" and zahlungsart not in ("rechnung", "abholung_bar"):
        return
```

- [ ] **Step 4: Tests ausführen — alle müssen grün sein**

Run: `python -m pytest tests/test_email_service.py -v`
Expected: Alle Tests bestanden (inkl. neuer Test)

- [ ] **Step 5: Commit**

```bash
git add app/services/email_service.py tests/test_email_service.py
git commit -m "feat: Status-Email-Logik für abholung_bar erweitern (#59)"
```

---

### Task 4: Checkout-Backend — dritter Zahlungs-Zweig

**Files:**
- Modify: `app/routers/bestellungen.py:25-143`
- Modify: `app/models.py:33`
- Modify: `tests/test_abholung_bar.py`

- [ ] **Step 1: Failing Test schreiben**

In `tests/test_abholung_bar.py` hinzufügen:

```python
import json

import bcrypt
import pytest
from fastapi.testclient import TestClient


def _make_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    pw_hash = _make_hash("testpass")
    monkeypatch.setattr("app.config.settings.database_path", str(tmp_path / "test.db"))
    monkeypatch.setattr("app.config.settings.admin_credentials", f"dev:{pw_hash}")
    from app.database import init_db

    init_db()
    from app.main import app

    return TestClient(app)


@patch("app.services.email_service.brevo_client")
def test_bestellen_abholung_bar(mock_email, client):
    """POST /bestellen mit zahlungsart=abholung_bar speichert Bestellung und sendet Mails."""
    from app.config import settings
    from app.csrf import generiere_csrf_token

    csrf = generiere_csrf_token(settings.secret_key)

    cart = json.dumps([{"produkt_id": 1, "menge": 2}])
    resp = client.post(
        "/bestellen",
        data={
            "vorname": "Clara",
            "nachname": "Bar",
            "email": "clara@test.ch",
            "strasse": "Barweg 1",
            "plz": "4600",
            "ort": "Olten",
            "versandart": "abholung",
            "zahlungsart": "abholung_bar",
            "cart_data": cart,
            "kommentar": "Bitte nachmittags",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )

    # Bestätigungsseite direkt (kein Redirect)
    assert resp.status_code == 200
    assert "bestell" in resp.text.lower()

    # 2 E-Mails: Kundenbestätigung + Stakeholder-Benachrichtigung
    assert mock_email.transactional_emails.send_transac_email.call_count == 2

    # DB prüfen
    from app.database import get_db

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT status, zahlungsart, versandart, versandkosten_chf "
            "FROM bestellungen WHERE id = 1"
        ).fetchone()
        assert row["status"] == "neu"
        assert row["zahlungsart"] == "abholung_bar"
        assert row["versandart"] == "abholung"
        assert row["versandkosten_chf"] == 0
    finally:
        conn.close()


@patch("app.services.email_service.brevo_client")
def test_bestellen_abholung_bar_mit_versand_abgelehnt(mock_email, client):
    """abholung_bar + versandart=versand wird abgelehnt (HTTP 400)."""
    from app.config import settings
    from app.csrf import generiere_csrf_token

    csrf = generiere_csrf_token(settings.secret_key)

    cart = json.dumps([{"produkt_id": 1, "menge": 1}])
    resp = client.post(
        "/bestellen",
        data={
            "vorname": "David",
            "nachname": "Fehler",
            "email": "david@test.ch",
            "strasse": "Fehlerweg 1",
            "plz": "8000",
            "ort": "Zürich",
            "versandart": "versand",
            "zahlungsart": "abholung_bar",
            "cart_data": cart,
            "kommentar": "",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )

    assert resp.status_code == 400
```

- [ ] **Step 2: Tests ausführen — müssen fehlschlagen**

Run: `python -m pytest tests/test_abholung_bar.py::test_bestellen_abholung_bar tests/test_abholung_bar.py::test_bestellen_abholung_bar_mit_versand_abgelehnt -v`
Expected: FAIL

- [ ] **Step 3: Model-Kommentar aktualisieren**

In `app/models.py`, Zeile 33 ändern von:

```python
    zahlungsart: str  # "stripe" oder "rechnung"
```

zu:

```python
    zahlungsart: str  # "stripe", "rechnung" oder "abholung_bar"
```

- [ ] **Step 4: Checkout-Handler erweitern**

In `app/routers/bestellungen.py`, nach dem Import-Block (Zeile 12) hinzufügen:

```python
from app.services.email_service import sende_bestellbestaetigung, sende_stakeholder_benachrichtigung
```

Dann den bestehenden Import in Zeile 100 (`from app.services.email_service import sende_bestellbestaetigung`) entfernen (wird jetzt oben importiert).

Den Handler `bestellen` erweitern — nach dem `if zahlungsart == "rechnung":` Block (nach Zeile 128), vor dem `return templates.TemplateResponse` (Zeile 130), einfügen:

```python
        if zahlungsart == "abholung_bar":
            if versandart != "abholung":
                raise HTTPException(400, "Bezahlung bei Abholung nur mit Abholung vor Ort möglich")
            # Produktnamen für E-Mail holen
            for pos in positionen:
                row = conn.execute(
                    "SELECT name FROM produkte WHERE id = ?", (pos["produkt_id"],)
                ).fetchone()
                pos["name"] = row["name"]
            sende_bestellbestaetigung(
                empfaenger=kunde_input.email,
                bestell_id=bestell_id,
                kunde={
                    "vorname": kunde_input.vorname,
                    "nachname": kunde_input.nachname,
                },
                positionen=positionen,
                versandkosten=versandkosten,
                total=gesamt,
                conn=conn,
                template_name="bestellbestaetigung_abholung_bar.html",
            )
```

**Wichtig:** Die Funktion `sende_bestellbestaetigung` braucht einen neuen optionalen Parameter `template_name`. In `app/services/email_service.py`, Signatur ändern (Zeile 17-26):

```python
def sende_bestellbestaetigung(
    empfaenger: str,
    bestell_id: int,
    kunde: dict,
    positionen: list[dict],
    versandkosten: float,
    total: float,
    anhang: bytes | None = None,
    conn: sqlite3.Connection | None = None,
    template_name: str = "bestellbestaetigung.html",
) -> object:
    template = env.get_template(template_name)
```

Und in Zeile 27 ändern von:

```python
    template = env.get_template("bestellbestaetigung.html")
```

zu:

```python
    template = env.get_template(template_name)
```

- [ ] **Step 5: Stakeholder-Mail im Checkout-Handler aufrufen**

Für alle drei Zahlungsarten muss die Stakeholder-Mail gesendet werden. In `app/routers/bestellungen.py`:

**Bei `abholung_bar`** (direkt nach dem `sende_bestellbestaetigung`-Aufruf):

```python
            sende_stakeholder_benachrichtigung(
                bestell_id=bestell_id,
                kunde={
                    "vorname": kunde_input.vorname,
                    "nachname": kunde_input.nachname,
                    "email": kunde_input.email,
                },
                positionen=positionen,
                versandkosten=versandkosten,
                total=gesamt,
                zahlungsart=zahlungsart,
                versandart=versandart,
                conn=conn,
            )
```

**Bei `rechnung`** (nach `sende_bestellbestaetigung` in Zeile 128, vor dem `return`):

```python
            sende_stakeholder_benachrichtigung(
                bestell_id=bestell_id,
                kunde={
                    "vorname": kunde_input.vorname,
                    "nachname": kunde_input.nachname,
                    "email": kunde_input.email,
                },
                positionen=positionen,
                versandkosten=versandkosten,
                total=gesamt,
                zahlungsart=zahlungsart,
                versandart=versandart,
                conn=conn,
            )
```

**Bei `stripe`:** Die Stakeholder-Mail wird erst im Webhook gesendet (Task 5), weil die Zahlung erst nach der Stripe-Session bestätigt ist.

- [ ] **Step 6: Tests ausführen — müssen grün sein**

Run: `python -m pytest tests/test_abholung_bar.py -v`
Expected: Alle Tests bestanden

- [ ] **Step 7: Bestehende Tests prüfen**

Run: `python -m pytest tests/ -v`
Expected: Alle Tests bestanden (keine Regression)

- [ ] **Step 8: Commit**

```bash
git add app/models.py app/routers/bestellungen.py app/services/email_service.py tests/test_abholung_bar.py
git commit -m "feat: Checkout-Zweig für Bezahlung bei Abholung + Stakeholder-Mail (#59)"
```

---

### Task 5: Stakeholder-Mail im Stripe-Webhook

**Files:**
- Modify: `app/routers/webhooks.py:47-76`
- Modify: `tests/test_e2e_bestellzyklus.py`

- [ ] **Step 1: Failing Test schreiben**

In `tests/test_e2e_bestellzyklus.py`, im Test `test_e2e_stripe_flow`, nach Zeile 101 (`mock_email.transactional_emails.send_transac_email.assert_called_once()`) ändern zu:

```python
    # 2 E-Mails: Bestellbestätigung + Stakeholder-Benachrichtigung
    assert mock_email.transactional_emails.send_transac_email.call_count == 2
```

Und den späteren Count in Zeile 146 von `== 2` auf `== 3` ändern:

```python
    # Versandbestätigungs-E-Mail (3. Aufruf: Bestätigung + Stakeholder + Versand)
    assert mock_email.transactional_emails.send_transac_email.call_count == 3
    zweiter_call = mock_email.transactional_emails.send_transac_email.call_args_list[2].kwargs
```

Und in `test_e2e_storno_nach_zahlung`, Zeile 383 ändern von `assert_called_once()` zu:

```python
    assert mock_email.transactional_emails.send_transac_email.call_count == 2
```

Und Zeile 413 ändern von `call_count == 1` zu:

```python
    assert mock_email.transactional_emails.send_transac_email.call_count == 2
```

- [ ] **Step 2: Tests ausführen — müssen fehlschlagen**

Run: `python -m pytest tests/test_e2e_bestellzyklus.py::test_e2e_stripe_flow -v`
Expected: FAIL — aktuell wird nur 1 Mail gesendet, nicht 2

- [ ] **Step 3: Stakeholder-Mail im Webhook einbauen**

In `app/routers/webhooks.py`, nach dem `sende_bestellbestaetigung`-Aufruf (Zeile 76), vor dem Kommentar `# TODO` (Zeile 77), einfügen:

```python
                from app.services.email_service import sende_stakeholder_benachrichtigung
                sende_stakeholder_benachrichtigung(
                    bestell_id=best["id"],
                    kunde={
                        "vorname": best["vorname"],
                        "nachname": best["nachname"],
                        "email": best["email"],
                    },
                    positionen=[dict(p) for p in positionen],
                    versandkosten=best["versandkosten_chf"],
                    total=best["total_chf"],
                    zahlungsart=best["zahlungsart"],
                    versandart=best["versandart"],
                    conn=conn,
                )
```

- [ ] **Step 4: Tests ausführen — müssen grün sein**

Run: `python -m pytest tests/test_e2e_bestellzyklus.py -v`
Expected: Alle Tests bestanden

- [ ] **Step 5: Commit**

```bash
git add app/routers/webhooks.py tests/test_e2e_bestellzyklus.py
git commit -m "feat: Stakeholder-Mail nach Stripe-Webhook (#59)"
```

---

### Task 6: Checkout-Frontend — Radio-Button + JS

**Files:**
- Modify: `templates/checkout.html:64-76`

- [ ] **Step 1: Zahlungs-Sektion im Checkout erweitern**

In `templates/checkout.html`, den Zahlungs-Block (Zeile 64-76) ersetzen durch:

```html
    <div class="bg-stone-700 rounded-lg p-6 shadow-md">
        <h2 class="text-xl font-bold mb-4">Zahlung</h2>
        <div class="space-y-2">
            <label class="flex items-center gap-2">
                <input type="radio" name="zahlungsart" value="stripe" checked
                       class="text-accent"> Twint / Kreditkarte (via Stripe)
            </label>
            <label class="flex items-center gap-2">
                <input type="radio" name="zahlungsart" value="rechnung"
                       class="text-accent"> Auf Rechnung (QR-Rechnung per E-Mail)
            </label>
            <label id="abholung-bar-option" class="flex items-center gap-2 hidden">
                <input type="radio" name="zahlungsart" value="abholung_bar"
                       class="text-accent"> Bezahlung bei Abholung (bar vor Ort)
            </label>
        </div>
    </div>
```

- [ ] **Step 2: JavaScript für Ein-/Ausblenden und Vorauswahl**

In `templates/checkout.html`, im `<script>`-Block am Ende (vor `{% endblock %}`), den bestehenden Event-Listener erweitern:

```html
<script>
document.getElementById("checkout-form").addEventListener("submit", function() {
    document.getElementById("cart-data").value = JSON.stringify(getCart());
});

// Bezahlung bei Abholung: ein-/ausblenden je nach Versandart
document.querySelectorAll('input[name="versandart"]').forEach(function(radio) {
    radio.addEventListener("change", function() {
        var abholungOption = document.getElementById("abholung-bar-option");
        var abholungRadio = abholungOption.querySelector("input");
        if (this.value === "abholung") {
            abholungOption.classList.remove("hidden");
            abholungRadio.checked = true;
        } else {
            abholungOption.classList.add("hidden");
            if (abholungRadio.checked) {
                document.querySelector('input[name="zahlungsart"][value="stripe"]').checked = true;
            }
        }
    });
});
</script>
```

- [ ] **Step 3: Manuell im Browser testen**

Erwartetes Verhalten:
1. Seite laden → "Bezahlung bei Abholung" ist ausgeblendet
2. "Abholung vor Ort" wählen → Option erscheint und ist vorausgewählt
3. Zurück auf "Postversand" → Option verschwindet, "Twint/Kreditkarte" ist wieder gewählt
4. "Abholung" wählen → "Bezahlung bei Abholung" vorausgewählt, aber Stripe/Rechnung bleibt klickbar

- [ ] **Step 4: Commit**

```bash
git add templates/checkout.html
git commit -m "feat: Checkout-UI für Bezahlung bei Abholung (#59)"
```

---

### Task 7: Bestätigungsseite anpassen

**Files:**
- Modify: `templates/bestaetigung.html:13-17`

- [ ] **Step 1: Text für abholung_bar hinzufügen**

In `templates/bestaetigung.html`, Zeile 13-17 ersetzen durch:

```html
        {% if zahlungsart == "rechnung" %}
        <p class="text-stone-400">Du erhältst in Kürze eine E-Mail mit der QR-Rechnung.</p>
        {% elif zahlungsart == "abholung_bar" %}
        <p class="text-stone-400">Der Inhaber wird sich bei dir für einen Abholtermin melden. Die Bezahlung erfolgt vor Ort.</p>
        {% else %}
        <p class="text-stone-400">Du erhältst in Kürze eine Bestellbestätigung per E-Mail.</p>
        {% endif %}
```

- [ ] **Step 2: Commit**

```bash
git add templates/bestaetigung.html
git commit -m "feat: Bestätigungsseite für Bezahlung bei Abholung (#59)"
```

---

### Task 8: Admin — Prozess-Leiste und Dashboard-Labels

**Files:**
- Modify: `templates/admin/bestellung_detail.html:254-264`
- Modify: `templates/admin/dashboard.html:90`

- [ ] **Step 1: Prozess-Leiste um abholung_bar-Workflow erweitern**

In `templates/admin/bestellung_detail.html`, in der JavaScript-Funktion `getProcess()` (Zeile 255-264), vor dem `return`-Fallback (Zeile 264) einfügen:

```javascript
        if (zahlungsart === "abholung_bar" && versandart === "abholung")
            return ["neu", "in_bearbeitung", "abholbereit", "bezahlt", "abgeschlossen"];
```

- [ ] **Step 2: Dashboard Zahlungsart-Label**

In `templates/admin/dashboard.html`, Zeile 90 ändern von:

```html
                <td class="px-4 py-3">{{ b.zahlungsart }}</td>
```

zu:

```html
                <td class="px-4 py-3">{% if b.zahlungsart == "abholung_bar" %}Bar bei Abholung{% elif b.zahlungsart == "rechnung" %}Rechnung{% elif b.zahlungsart == "stripe" %}Stripe{% else %}{{ b.zahlungsart }}{% endif %}</td>
```

- [ ] **Step 3: Bestelldetail Zahlungsart-Label**

In `templates/admin/bestellung_detail.html`, Zeile 133 ändern von:

```html
                Zahlungsart: {{ bestellung.zahlungsart }} · Erstellt: {{ bestellung.erstellt_am[:16] }}
```

zu:

```html
                Zahlungsart: {% if bestellung.zahlungsart == "abholung_bar" %}Bar bei Abholung{% elif bestellung.zahlungsart == "rechnung" %}Rechnung{% elif bestellung.zahlungsart == "stripe" %}Stripe{% else %}{{ bestellung.zahlungsart }}{% endif %} · Erstellt: {{ bestellung.erstellt_am[:16] }}
```

- [ ] **Step 4: Commit**

```bash
git add templates/admin/bestellung_detail.html templates/admin/dashboard.html
git commit -m "feat: Admin-Prozessleiste und Labels für abholung_bar (#59)"
```

---

### Task 9: E2E-Test für den kompletten abholung_bar-Zyklus

**Files:**
- Modify: `tests/test_e2e_bestellzyklus.py`

- [ ] **Step 1: E2E-Test schreiben**

In `tests/test_e2e_bestellzyklus.py` am Ende hinzufügen:

```python
@patch("app.services.email_service.brevo_client")
def test_e2e_abholung_bar_flow(mock_email, e2e_client):
    """Kompletter Abholung-Bar-Zyklus: Bestellen -> Admin-Statuswechsel -> bezahlt."""
    client = e2e_client

    from app.config import settings
    from app.csrf import generiere_csrf_token

    csrf = generiere_csrf_token(settings.secret_key)

    # --- 1. POST /bestellen mit zahlungsart=abholung_bar ---
    cart = json.dumps([{"produkt_id": 1, "menge": 3}])
    resp_bestellen = client.post(
        "/bestellen",
        data={
            "vorname": "Eva",
            "nachname": "Abholung",
            "email": "eva@test.ch",
            "strasse": "Abholweg 3",
            "plz": "4600",
            "ort": "Olten",
            "versandart": "abholung",
            "zahlungsart": "abholung_bar",
            "cart_data": cart,
            "kommentar": "Nachmittags bitte",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )

    # Direkt Bestätigungsseite (kein Redirect)
    assert resp_bestellen.status_code == 200
    assert "bestell" in resp_bestellen.text.lower()

    # 2 E-Mails: Kundenbestätigung + Stakeholder
    assert mock_email.transactional_emails.send_transac_email.call_count == 2

    # DB prüfen
    from app.database import get_db

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, status, zahlungsart, versandart, versandkosten_chf "
            "FROM bestellungen WHERE id = 1"
        ).fetchone()
        bestell_id = row["id"]
        assert row["status"] == "neu"
        assert row["zahlungsart"] == "abholung_bar"
        assert row["versandart"] == "abholung"
        assert row["versandkosten_chf"] == 0
    finally:
        conn.close()

    # --- 2. Admin-Login ---
    resp_login = client.post(
        "/admin/login",
        data={"password": "testpass", "csrf_token": ""},
        follow_redirects=False,
    )
    assert resp_login.status_code == 303
    client.cookies = resp_login.cookies

    # --- 3. Admin setzt auf 'abholbereit' ---
    resp_status1 = client.post(
        f"/admin/bestellungen/{bestell_id}/status",
        data={"neuer_status": "abholbereit", "csrf_token": ""},
        follow_redirects=False,
    )
    assert resp_status1.status_code == 303

    # Abholbereit-E-Mail gesendet (3. Aufruf)
    assert mock_email.transactional_emails.send_transac_email.call_count == 3
    dritter_call = mock_email.transactional_emails.send_transac_email.call_args_list[2].kwargs
    assert "abholbereit" in dritter_call["subject"]

    # --- 4. Admin markiert als 'bezahlt' (Bar-Zahlung erhalten) ---
    resp_status2 = client.post(
        f"/admin/bestellungen/{bestell_id}/status",
        data={"neuer_status": "bezahlt", "csrf_token": ""},
        follow_redirects=False,
    )
    assert resp_status2.status_code == 303

    # Zahlungseingangs-E-Mail gesendet (4. Aufruf)
    assert mock_email.transactional_emails.send_transac_email.call_count == 4
    vierter_call = mock_email.transactional_emails.send_transac_email.call_args_list[3].kwargs
    assert "Zahlungseingang" in vierter_call["subject"]

    # --- 5. Verifikation ---
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT status FROM bestellungen WHERE id = ?", (bestell_id,)
        ).fetchone()
        assert row["status"] == "bezahlt"

        logs = conn.execute(
            "SELECT * FROM admin_log WHERE bestellung_id = ? AND aktion = 'status_geaendert' "
            "ORDER BY zeitpunkt ASC",
            (bestell_id,),
        ).fetchall()
        assert len(logs) == 2

        d1 = json.loads(logs[0]["details"])
        assert d1["von"] == "neu"
        assert d1["nach"] == "abholbereit"

        d2 = json.loads(logs[1]["details"])
        assert d2["von"] == "abholbereit"
        assert d2["nach"] == "bezahlt"
    finally:
        conn.close()
```

- [ ] **Step 2: Test ausführen — muss grün sein**

Run: `python -m pytest tests/test_e2e_bestellzyklus.py::test_e2e_abholung_bar_flow -v`
Expected: PASS (alle vorherigen Tasks müssen abgeschlossen sein)

- [ ] **Step 3: Alle Tests ausführen**

Run: `python -m pytest tests/ -v`
Expected: Alle Tests bestanden

- [ ] **Step 4: Commit**

```bash
git add tests/test_e2e_bestellzyklus.py
git commit -m "test: E2E-Test für Bezahlung bei Abholung (#59)"
```

---

### Task 10: Stakeholder-Mail auch bei Rechnung im E2E-Test

**Files:**
- Modify: `tests/test_e2e_bestellzyklus.py`

- [ ] **Step 1: Rechnungs-E2E-Test anpassen**

In `tests/test_e2e_bestellzyklus.py`, im Test `test_e2e_rechnungs_flow`:

Zeile 218 ändern von:

```python
    mock_email.transactional_emails.send_transac_email.assert_called_once()
```

zu:

```python
    # 2 E-Mails: Bestellbestätigung + Stakeholder
    assert mock_email.transactional_emails.send_transac_email.call_count == 2
```

Zeile 260 ändern von `call_count == 2` zu `call_count == 3`:

```python
    assert mock_email.transactional_emails.send_transac_email.call_count == 3
    zweiter_call = mock_email.transactional_emails.send_transac_email.call_args_list[2].kwargs
```

Zeile 274 ändern von `call_count == 3` zu `call_count == 4`:

```python
    assert mock_email.transactional_emails.send_transac_email.call_count == 4
    dritter_call = mock_email.transactional_emails.send_transac_email.call_args_list[3].kwargs
```

- [ ] **Step 2: Tests ausführen**

Run: `python -m pytest tests/test_e2e_bestellzyklus.py -v`
Expected: Alle Tests bestanden

- [ ] **Step 3: Commit**

```bash
git add tests/test_e2e_bestellzyklus.py
git commit -m "test: E2E-Tests an Stakeholder-Mail anpassen (#59)"
```

---

### Task 11: User-Stories-Testplan aktualisieren

**Files:**
- Modify: `docs/user-stories-testplan.md` (falls vorhanden)

- [ ] **Step 1: Testplan prüfen und aktualisieren**

Prüfe ob `docs/user-stories-testplan.md` existiert. Falls ja, folgende Szenarien ergänzen:

- Kunde wählt "Abholung vor Ort" → "Bezahlung bei Abholung" erscheint und ist vorausgewählt
- Kunde wählt "Postversand" → "Bezahlung bei Abholung" ist nicht sichtbar
- Kunde bestellt mit "Bezahlung bei Abholung" → Bestätigungsseite mit Abholhinweis
- Kunde erhält E-Mail mit Abholhinweis und Stornierungsinfo
- Stakeholder erhält E-Mail bei jeder Bestellung
- Admin sieht "Bar bei Abholung" im Dashboard
- Admin kann Bestellung manuell als "bezahlt" markieren

- [ ] **Step 2: Commit**

```bash
git add docs/user-stories-testplan.md
git commit -m "docs: Testplan um Bezahlung bei Abholung erweitern (#59)"
```
