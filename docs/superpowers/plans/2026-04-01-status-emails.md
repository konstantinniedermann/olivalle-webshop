# Status-E-Mails Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatische E-Mail-Benachrichtigung an Kunden bei Statusänderungen (bezahlt, versendet, abholbereit) im Admin-Interface.

**Architecture:** Zentrale Dispatch-Funktion `sende_status_email()` im `email_service.py`, die anhand von Status + Zahlungsart/Versandart entscheidet ob und welche E-Mail gesendet wird. Der Admin-Router ruft nach der Statusänderung nur diese eine Funktion auf. Drei neue Jinja2-Templates für die E-Mails.

**Tech Stack:** Python, FastAPI, Jinja2, Brevo SDK, pytest

**Spec:** `docs/superpowers/specs/2026-04-01-status-emails-design.md`

---

## File Structure

| Datei | Aktion | Verantwortung |
|---|---|---|
| `templates/emails/zahlungseingang.html` | Create | E-Mail-Template: Zahlungseingangsbestätigung |
| `templates/emails/versandbestaetigung.html` | Create | E-Mail-Template: Versandbestätigung |
| `templates/emails/abholbereit.html` | Create | E-Mail-Template: Abholbenachrichtigung mit Adresse |
| `app/services/email_service.py` | Modify | Neue Funktion `sende_status_email()` |
| `app/routers/admin.py` | Modify | Aufruf von `sende_status_email()` nach Statusänderung |
| `tests/test_email_service.py` | Modify | Unit-Tests für `sende_status_email()` |
| `tests/test_e2e_bestellzyklus.py` | Modify | E2E-Tests um E-Mail-Versand bei Statusänderung prüfen |

---

### Task 1: E-Mail-Templates erstellen

**Files:**
- Create: `templates/emails/zahlungseingang.html`
- Create: `templates/emails/versandbestaetigung.html`
- Create: `templates/emails/abholbereit.html`

- [ ] **Step 1: Template `zahlungseingang.html` erstellen**

```html
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
    <h1 style="color: #f1d600;">Zahlungseingang bestätigt</h1>
    <p>Hallo {{ kunde_vorname }},</p>
    <p>wir haben deine Zahlung für Bestellung #{{ bestell_id }} erhalten. Vielen Dank!</p>
    <p>Deine Bestellung wird nun bearbeitet.</p>
    <p style="margin-top: 20px;">Liebe Grüsse<br>Olivalle</p>
</body>
</html>
```

- [ ] **Step 2: Template `versandbestaetigung.html` erstellen**

```html
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
    <h1 style="color: #f1d600;">Deine Bestellung ist unterwegs</h1>
    <p>Hallo {{ kunde_vorname }},</p>
    <p>deine Bestellung #{{ bestell_id }} wurde versendet und sollte in den nächsten Tagen bei dir eintreffen.</p>
    <p style="margin-top: 20px;">Liebe Grüsse<br>Olivalle</p>
</body>
</html>
```

- [ ] **Step 3: Template `abholbereit.html` erstellen**

```html
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
    <h1 style="color: #f1d600;">Deine Bestellung ist abholbereit</h1>
    <p>Hallo {{ kunde_vorname }},</p>
    <p>deine Bestellung #{{ bestell_id }} liegt zur Abholung bereit.</p>
    <p><strong>Abholadresse:</strong><br>Hegibergstrasse 98<br>4632 Trimbach</p>
    <p>Bitte nimm vorgängig per E-Mail Kontakt mit uns auf, um einen Abholtermin zu vereinbaren.</p>
    <p style="margin-top: 20px;">Liebe Grüsse<br>Olivalle</p>
</body>
</html>
```

- [ ] **Step 4: Commit**

```bash
git add templates/emails/zahlungseingang.html templates/emails/versandbestaetigung.html templates/emails/abholbereit.html
git commit -m "feat: E-Mail-Templates für Statusänderungen (bezahlt, versendet, abholbereit)"
```

---

### Task 2: Dispatch-Funktion `sende_status_email` — Tests

**Files:**
- Modify: `tests/test_email_service.py`

- [ ] **Step 1: Tests für `sende_status_email` schreiben**

Am Ende von `tests/test_email_service.py` folgende Tests ergänzen:

```python
from app.services.email_service import sende_status_email


class TestSendeStatusEmail:
    """Tests für sende_status_email Dispatch-Logik."""

    def _make_bestellung(self, db, zahlungsart="rechnung", versandart="versand"):
        """Hilfsfunktion: Kunde + Bestellung in DB anlegen."""
        db.execute(
            "INSERT INTO kunden (id, vorname, nachname, email, telefon, strasse, plz, ort) "
            "VALUES (1, 'Max', 'Muster', 'max@test.ch', '', 'Teststr 1', '8000', 'Zürich')"
        )
        db.execute(
            "INSERT INTO bestellungen (id, kunde_id, status, zahlungsart, versandart, "
            "versandkosten_chf, total_chf) "
            "VALUES (1, 1, 'neu', ?, ?, 0, 50.00)",
            (zahlungsart, versandart),
        )
        db.commit()

    @patch("app.services.email_service.brevo_client")
    def test_bezahlt_rechnung_sendet_email(self, mock_client, db):
        """bezahlt + rechnung → Zahlungseingangsbestätigung."""
        self._make_bestellung(db, zahlungsart="rechnung")
        mock_client.transactional_emails.send_transac_email.return_value = MagicMock(
            message_id="s1"
        )
        sende_status_email(bestellung_id=1, neuer_status="bezahlt", conn=db)
        mock_client.transactional_emails.send_transac_email.assert_called_once()
        call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
        assert call_kwargs["to"][0]["email"] == "max@test.ch"
        assert "Zahlungseingang" in call_kwargs["subject"]

    @patch("app.services.email_service.brevo_client")
    def test_bezahlt_stripe_keine_email(self, mock_client, db):
        """bezahlt + stripe → keine E-Mail (Stripe schickt eigene)."""
        self._make_bestellung(db, zahlungsart="stripe")
        sende_status_email(bestellung_id=1, neuer_status="bezahlt", conn=db)
        mock_client.transactional_emails.send_transac_email.assert_not_called()

    @patch("app.services.email_service.brevo_client")
    def test_versendet_versand_sendet_email(self, mock_client, db):
        """versendet + versand → Versandbestätigung."""
        self._make_bestellung(db, versandart="versand")
        mock_client.transactional_emails.send_transac_email.return_value = MagicMock(
            message_id="s2"
        )
        sende_status_email(bestellung_id=1, neuer_status="versendet", conn=db)
        mock_client.transactional_emails.send_transac_email.assert_called_once()
        call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
        assert "unterwegs" in call_kwargs["subject"]

    @patch("app.services.email_service.brevo_client")
    def test_versendet_abholung_keine_email(self, mock_client, db):
        """versendet + abholung → keine E-Mail."""
        self._make_bestellung(db, versandart="abholung")
        sende_status_email(bestellung_id=1, neuer_status="versendet", conn=db)
        mock_client.transactional_emails.send_transac_email.assert_not_called()

    @patch("app.services.email_service.brevo_client")
    def test_abholbereit_abholung_sendet_email(self, mock_client, db):
        """abholbereit + abholung → Abholbenachrichtigung."""
        self._make_bestellung(db, versandart="abholung")
        mock_client.transactional_emails.send_transac_email.return_value = MagicMock(
            message_id="s3"
        )
        sende_status_email(bestellung_id=1, neuer_status="abholbereit", conn=db)
        mock_client.transactional_emails.send_transac_email.assert_called_once()
        call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
        assert "abholbereit" in call_kwargs["subject"]

    @patch("app.services.email_service.brevo_client")
    def test_abholbereit_versand_keine_email(self, mock_client, db):
        """abholbereit + versand → keine E-Mail."""
        self._make_bestellung(db, versandart="versand")
        sende_status_email(bestellung_id=1, neuer_status="abholbereit", conn=db)
        mock_client.transactional_emails.send_transac_email.assert_not_called()

    @patch("app.services.email_service.brevo_client")
    def test_storniert_keine_email(self, mock_client, db):
        """storniert → keine E-Mail."""
        self._make_bestellung(db)
        sende_status_email(bestellung_id=1, neuer_status="storniert", conn=db)
        mock_client.transactional_emails.send_transac_email.assert_not_called()
```

- [ ] **Step 2: Tests laufen lassen — alle neuen Tests müssen fehlschlagen**

Run: `python -m pytest tests/test_email_service.py::TestSendeStatusEmail -v`
Expected: FAIL — `ImportError: cannot import name 'sende_status_email'`

- [ ] **Step 3: Commit**

```bash
git add tests/test_email_service.py
git commit -m "test: Unit-Tests für sende_status_email Dispatch-Logik"
```

---

### Task 3: Dispatch-Funktion `sende_status_email` — Implementation

**Files:**
- Modify: `app/services/email_service.py`

- [ ] **Step 1: `sende_status_email` implementieren**

Am Ende von `app/services/email_service.py` folgende Funktion ergänzen:

```python
# Mapping: Status → (Template-Datei, Betreff-Text)
_STATUS_EMAIL_CONFIG: dict[str, tuple[str, str]] = {
    "bezahlt": (
        "zahlungseingang.html",
        "Zahlungseingang bestätigt — Bestellung #{bestell_id}",
    ),
    "versendet": (
        "versandbestaetigung.html",
        "Deine Bestellung #{bestell_id} ist unterwegs",
    ),
    "abholbereit": (
        "abholbereit.html",
        "Deine Bestellung #{bestell_id} ist abholbereit",
    ),
}


def sende_status_email(
    bestellung_id: int,
    neuer_status: str,
    conn: sqlite3.Connection,
) -> None:
    """Sendet eine Status-E-Mail an den Kunden, falls für diesen Status vorgesehen."""
    config = _STATUS_EMAIL_CONFIG.get(neuer_status)
    if not config:
        return

    from app.repositories.admin_repo import get_bestellung_detail, log_eintrag_schreiben

    bestellung = get_bestellung_detail(conn, bestellung_id)
    if not bestellung:
        return

    # Bedingungen prüfen: nicht jeder Status löst bei jeder Bestell-Konstellation eine Mail aus
    zahlungsart = bestellung["zahlungsart"]
    versandart = bestellung["versandart"]

    if neuer_status == "bezahlt" and zahlungsart != "rechnung":
        return
    if neuer_status == "versendet" and versandart != "versand":
        return
    if neuer_status == "abholbereit" and versandart != "abholung":
        return

    template_datei, betreff_vorlage = config
    betreff = betreff_vorlage.format(bestell_id=bestellung_id)

    template = env.get_template(template_datei)
    html = template.render(
        kunde_vorname=bestellung["vorname"],
        bestell_id=bestellung_id,
    )

    brevo_client.transactional_emails.send_transac_email(
        sender={"email": "bestellung@olivalle.ch", "name": "Olivalle"},
        to=[{"email": bestellung["email"]}],
        reply_to={"email": "olivalle.olten@outlook.com"},
        subject=betreff,
        html_content=html,
    )

    log_eintrag_schreiben(
        conn,
        admin_label="system",
        aktion="email_ausgang",
        details=f"An: {bestellung['email']} — {betreff}",
        bestellung_id=bestellung_id,
    )
```

- [ ] **Step 2: Tests laufen lassen — alle neuen Tests müssen bestehen**

Run: `python -m pytest tests/test_email_service.py -v`
Expected: PASS — alle Tests grün

- [ ] **Step 3: Commit**

```bash
git add app/services/email_service.py
git commit -m "feat: sende_status_email Dispatch-Funktion für Statusänderungs-Mails"
```

---

### Task 4: Admin-Router Integration

**Files:**
- Modify: `app/routers/admin.py:230-240`

- [ ] **Step 1: Import und Aufruf in `admin.py` ergänzen**

In `app/routers/admin.py` in der Funktion `admin_status_aendern` (Zeile 230-240), nach dem `log_eintrag_schreiben()`-Aufruf und vor dem `finally:`-Block, den E-Mail-Versand einfügen:

```python
            log_eintrag_schreiben(
                conn,
                admin_label=label,
                aktion="status_geaendert",
                details=json.dumps({"von": alter_status, "nach": neuer_status}),
                bestellung_id=bestellung_id,
            )

            from app.services.email_service import sende_status_email

            sende_status_email(bestellung_id, neuer_status, conn)
```

- [ ] **Step 2: Bestehende Tests laufen lassen**

Run: `python -m pytest tests/test_api_admin.py -v`
Expected: PASS — bestehende Admin-Tests dürfen nicht brechen. Die Tests mocken Brevo bereits oder der Aufruf wird übersprungen weil die Testdaten keine passende Kombination haben.

- [ ] **Step 3: Commit**

```bash
git add app/routers/admin.py
git commit -m "feat: Status-E-Mail-Versand im Admin-Router bei Statusänderung auslösen"
```

---

### Task 5: E2E-Tests erweitern

**Files:**
- Modify: `tests/test_e2e_bestellzyklus.py`

- [ ] **Step 1: Rechnungs-Flow-Test um E-Mail-Prüfung erweitern**

In `test_e2e_rechnungs_flow` (Zeile 176-293): Nach dem Admin-Statuswechsel auf "bezahlt" (Zeile 249-254) prüfen, dass eine zweite E-Mail (Zahlungseingang) gesendet wurde. Und nach "abholbereit" (Zeile 257-262) eine dritte.

Ersetze den bestehenden E-Mail-Assert (Zeile 215) und ergänze nach den Statuswechseln:

Nach Zeile 254 (`assert resp_status1.status_code == 303`) einfügen:

```python
    # Zahlungseingangs-E-Mail muss gesendet worden sein (2. Aufruf)
    assert mock_email.transactional_emails.send_transac_email.call_count == 2
    zweiter_call = mock_email.transactional_emails.send_transac_email.call_args_list[1].kwargs
    assert "Zahlungseingang" in zweiter_call["subject"]
    assert zweiter_call["to"][0]["email"] == "beat@test.ch"
```

Nach Zeile 262 (`assert resp_status2.status_code == 303`) einfügen:

```python
    # Abholbereit-E-Mail muss gesendet worden sein (3. Aufruf)
    assert mock_email.transactional_emails.send_transac_email.call_count == 3
    dritter_call = mock_email.transactional_emails.send_transac_email.call_args_list[2].kwargs
    assert "abholbereit" in dritter_call["subject"]
    assert dritter_call["to"][0]["email"] == "beat@test.ch"
```

- [ ] **Step 2: Stripe-Flow-Test um Versand-E-Mail-Prüfung erweitern**

In `test_e2e_stripe_flow` (Zeile 32-173): Nach dem Admin-Statuswechsel auf "versendet" (Zeile 137-142) prüfen, dass eine Versand-E-Mail gesendet wurde.

Nach Zeile 142 (`assert resp_status.status_code == 303`) einfügen:

```python
    # Versandbestätigungs-E-Mail muss gesendet worden sein (2. Aufruf, nach Webhook-Mail)
    assert mock_email.transactional_emails.send_transac_email.call_count == 2
    zweiter_call = mock_email.transactional_emails.send_transac_email.call_args_list[1].kwargs
    assert "unterwegs" in zweiter_call["subject"]
    assert zweiter_call["to"][0]["email"] == "anna@test.ch"
```

- [ ] **Step 3: Storno-Test prüfen — keine E-Mail bei Stornierung**

In `test_e2e_storno_nach_zahlung` (Zeile 299-425): Nach dem Admin-Statuswechsel auf "storniert" (Zeile 389-394) prüfen, dass KEINE zusätzliche E-Mail gesendet wurde.

Nach Zeile 394 (`assert resp_status.status_code == 303`) einfügen:

```python
    # Stornierung darf KEINE zusätzliche E-Mail auslösen (nur Webhook-Mail von vorher)
    assert mock_email.transactional_emails.send_transac_email.call_count == 1
```

- [ ] **Step 4: Alle Tests laufen lassen**

Run: `python -m pytest tests/ -v`
Expected: PASS — alle Tests grün

- [ ] **Step 5: Commit**

```bash
git add tests/test_e2e_bestellzyklus.py
git commit -m "test: E2E-Tests um Status-E-Mail-Prüfung erweitern"
```
