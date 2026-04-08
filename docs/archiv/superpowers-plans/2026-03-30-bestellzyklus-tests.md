# Bestellzyklus-Tests — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Den gesamten Bestellzyklus automatisiert testen (E2E-Tests, Admin-API-Tests, Webhook-Fehlerszenarien) und ein manuelles Testprotokoll für Browser-Tests erstellen.

**Architecture:** Bestehende pytest-Infrastruktur (conftest.py Fixtures, in-memory SQLite, monkeypatch für externe Services) wird wiederverwendet. Neue E2E-Tests in eigener Datei, Admin- und Webhook-Tests in bestehende Dateien integriert. Manuelles Testprotokoll als Markdown-Dokument.

**Tech Stack:** pytest, FastAPI TestClient, monkeypatch/unittest.mock, SQLite in-memory

---

## Datei-Übersicht

| Datei | Aktion | Verantwortung |
|-------|--------|---------------|
| `tests/test_e2e_bestellzyklus.py` | **Neu** | 3 E2E-Tests: Stripe-Flow, Rechnungs-Flow, Storno |
| `tests/test_api_admin.py` | **Erweitern** | Statusänderung + Notiz API-Tests |
| `tests/test_api_webhooks.py` | **Erweitern** | Webhook-Fehlerszenarien |
| `docs/testprotokoll.md` | **Neu** | Manuelles Testprotokoll |

---

## Task 1: Admin-Statusänderung testen

**Files:**
- Modify: `tests/test_api_admin.py`

Neue Testklasse `TestAdminStatusAenderung` in bestehende Datei einfügen. Nutzt `admin_client`-Fixture und Login-Helper aus bestehenden Tests.

- [ ] **Step 1: Tests schreiben**

Am Ende von `tests/test_api_admin.py` folgende Klasse hinzufügen:

```python
class TestAdminStatusAenderung:
    def _login(self, client):
        resp = client.post(
            "/admin/login",
            data={"password": "testpass", "csrf_token": ""},
            follow_redirects=False,
        )
        return resp.cookies

    def _create_order(self, client):
        """Create a test order directly via DB."""
        from app.database import get_db

        conn = get_db()
        conn.execute(
            "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
            "VALUES ('Max', 'Muster', 'max@test.ch', 'Str 1', '4600', 'Olten')"
        )
        conn.execute(
            "INSERT INTO bestellungen"
            " (kunde_id, zahlungsart, versandart, total_chf, status) "
            "VALUES (1, 'stripe', 'versand', 25.90, 'neu')"
        )
        conn.execute(
            "INSERT INTO bestellpositionen"
            " (bestellung_id, produkt_id, menge, einzelpreis_chf) "
            "VALUES (1, 1, 2, 8.0)"
        )
        conn.commit()
        conn.close()

    def test_status_aendern_erfolgreich(self, admin_client):
        self._create_order(admin_client)
        cookies = self._login(admin_client)
        admin_client.cookies = cookies

        resp = admin_client.post(
            "/admin/bestellungen/1/status",
            data={"neuer_status": "bezahlt", "csrf_token": ""},
            follow_redirects=False,
        )
        assert resp.status_code == 303

        # Status in DB prüfen
        from app.database import get_db

        conn = get_db()
        row = conn.execute("SELECT status FROM bestellungen WHERE id = 1").fetchone()
        assert dict(row)["status"] == "bezahlt"

        # Log-Eintrag prüfen
        log = conn.execute(
            "SELECT * FROM admin_log WHERE aktion = 'status_geaendert'"
        ).fetchone()
        assert log is not None
        assert '"von": "neu"' in log["details"]
        assert '"nach": "bezahlt"' in log["details"]
        conn.close()

    def test_status_aendern_bestellung_nicht_gefunden(self, admin_client):
        cookies = self._login(admin_client)
        admin_client.cookies = cookies

        resp = admin_client.post(
            "/admin/bestellungen/999/status",
            data={"neuer_status": "bezahlt", "csrf_token": ""},
        )
        assert resp.status_code == 404
```

- [ ] **Step 2: Tests ausführen und prüfen**

Run: `source .venv/bin/activate && python -m pytest tests/test_api_admin.py::TestAdminStatusAenderung -v`
Expected: 2 Tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_api_admin.py
git commit -m "test: Admin-Statusänderung API-Tests"
```

---

## Task 2: Admin-Notiz testen

**Files:**
- Modify: `tests/test_api_admin.py`

Neue Testklasse `TestAdminNotiz` hinzufügen.

- [ ] **Step 1: Tests schreiben**

Am Ende von `tests/test_api_admin.py` hinzufügen:

```python
class TestAdminNotiz:
    def _login(self, client):
        resp = client.post(
            "/admin/login",
            data={"password": "testpass", "csrf_token": ""},
            follow_redirects=False,
        )
        return resp.cookies

    def _create_order(self, client):
        from app.database import get_db

        conn = get_db()
        conn.execute(
            "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
            "VALUES ('Max', 'Muster', 'max@test.ch', 'Str 1', '4600', 'Olten')"
        )
        conn.execute(
            "INSERT INTO bestellungen"
            " (kunde_id, zahlungsart, versandart, total_chf, status) "
            "VALUES (1, 'stripe', 'versand', 25.90, 'neu')"
        )
        conn.execute(
            "INSERT INTO bestellpositionen"
            " (bestellung_id, produkt_id, menge, einzelpreis_chf) "
            "VALUES (1, 1, 2, 8.0)"
        )
        conn.commit()
        conn.close()

    def test_notiz_hinzufuegen_erfolgreich(self, admin_client):
        self._create_order(admin_client)
        cookies = self._login(admin_client)
        admin_client.cookies = cookies

        resp = admin_client.post(
            "/admin/bestellungen/1/notiz",
            data={
                "typ": "notiz_hinzugefuegt",
                "text": "Kunde hat angerufen",
                "csrf_token": "",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303

        from app.database import get_db

        conn = get_db()
        log = conn.execute(
            "SELECT * FROM admin_log WHERE aktion = 'notiz_hinzugefuegt'"
        ).fetchone()
        assert log is not None
        assert "Kunde hat angerufen" in log["details"]
        assert log["bestellung_id"] == 1
        conn.close()
```

- [ ] **Step 2: Tests ausführen**

Run: `source .venv/bin/activate && python -m pytest tests/test_api_admin.py::TestAdminNotiz -v`
Expected: 1 Test PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_api_admin.py
git commit -m "test: Admin-Notiz API-Tests"
```

---

## Task 3: Webhook-Fehlerszenarien testen

**Files:**
- Modify: `tests/test_api_webhooks.py`

Drei neue Tests für Fehlerszenarien hinzufügen.

- [ ] **Step 1: Tests schreiben**

Am Ende von `tests/test_api_webhooks.py` hinzufügen:

```python
@patch("app.routers.webhooks.stripe.Webhook.construct_event")
def test_webhook_ungueltige_signatur(mock_construct, client):
    mock_construct.side_effect = stripe.SignatureVerificationError(
        "Invalid signature", "sig_header"
    )

    response = client.post(
        "/webhook/stripe",
        content=b'{"type": "test"}',
        headers={"stripe-signature": "bad_sig"},
    )
    assert response.status_code == 400


@patch("app.services.email_service.resend.Emails.send", return_value={"id": "test"})
@patch("app.routers.webhooks.stripe.Webhook.construct_event")
def test_webhook_bestellung_nicht_gefunden(mock_construct, mock_email, client):
    """Webhook mit session_id die zu keiner Bestellung passt — kein Crash."""
    mock_construct.return_value = MagicMock(
        type="checkout.session.completed",
        data=MagicMock(object=MagicMock(id="cs_unknown_999")),
    )

    response = client.post(
        "/webhook/stripe",
        content=b'{"type": "checkout.session.completed"}',
        headers={"stripe-signature": "test_sig"},
    )
    assert response.status_code == 200
    mock_email.assert_not_called()


@patch("app.services.email_service.resend.Emails.send", return_value={"id": "test"})
@patch("app.routers.webhooks.stripe.Webhook.construct_event")
def test_webhook_doppelt_kein_doppelte_email(mock_construct, mock_email, client, db):
    """Zweiter Webhook für gleiche session_id — keine doppelte E-Mail."""
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('Max', 'Muster', 'max@test.ch', 'Str 1', '4600', 'Olten')"
    )
    db.execute(
        "INSERT INTO bestellungen"
        " (kunde_id, zahlungsart, versandart, total_chf,"
        " stripe_session_id, status) "
        "VALUES (1, 'stripe', 'versand', 25.90, 'cs_test_doppelt', 'neu')"
    )
    db.execute(
        "INSERT INTO bestellpositionen"
        " (bestellung_id, produkt_id, menge, einzelpreis_chf) "
        "VALUES (1, 1, 2, 8.0)"
    )
    db.commit()

    mock_construct.return_value = MagicMock(
        type="checkout.session.completed",
        data=MagicMock(object=MagicMock(id="cs_test_doppelt")),
    )

    # Erster Webhook
    client.post(
        "/webhook/stripe",
        content=b'{"type": "checkout.session.completed"}',
        headers={"stripe-signature": "test_sig"},
    )
    assert mock_email.call_count == 1

    # Zweiter Webhook — keine weitere E-Mail
    client.post(
        "/webhook/stripe",
        content=b'{"type": "checkout.session.completed"}',
        headers={"stripe-signature": "test_sig"},
    )
    assert mock_email.call_count == 1
```

Wichtig: Der Import `import stripe` und `from unittest.mock import MagicMock, patch` muss am Anfang der Datei stehen. Der `MagicMock`-Import existiert bereits, `stripe` muss ergänzt werden.

- [ ] **Step 2: Tests ausführen**

Run: `source .venv/bin/activate && python -m pytest tests/test_api_webhooks.py -v`
Expected: 4 Tests (1 bestehend + 3 neu). Der **doppelte-Webhook-Test wird vermutlich FAIL** — der aktuelle Code hat keinen Schutz gegen doppelte Webhooks. Das ist erwartet und wird in Step 3 gefixt.

- [ ] **Step 3: Doppelt-Webhook-Schutz implementieren**

In `app/routers/webhooks.py` vor dem Status-Update prüfen, ob die Bestellung noch Status `neu` hat:

```python
# Zeile 26-31 ersetzen mit:
row = conn.execute(
    "SELECT status FROM bestellungen WHERE stripe_session_id = ?",
    (session.id,),
).fetchone()
if not row or dict(row)["status"] != "neu":
    conn.close()
    return {"status": "ok"}

conn.execute(
    "UPDATE bestellungen SET status = 'bezahlt' "
    "WHERE stripe_session_id = ?",
    (session.id,),
)
conn.commit()
```

- [ ] **Step 4: Alle Webhook-Tests erneut ausführen**

Run: `source .venv/bin/activate && python -m pytest tests/test_api_webhooks.py -v`
Expected: 4 Tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_api_webhooks.py app/routers/webhooks.py
git commit -m "test: Webhook-Fehlerszenarien + Doppelt-Webhook-Schutz"
```

---

## Task 4: E2E Stripe-Flow

**Files:**
- Create: `tests/test_e2e_bestellzyklus.py`

Kompletter Durchlauf: Bestellen → Stripe-Webhook → Admin-Statusänderung.

- [ ] **Step 1: Testdatei erstellen mit Stripe-Flow-Test**

```python
"""End-to-End Tests für den gesamten Bestellzyklus."""

import json

import bcrypt
from unittest.mock import MagicMock, patch


def _make_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _admin_login(client):
    """Admin einloggen, Cookies zurückgeben."""
    resp = client.post(
        "/admin/login",
        data={"password": "testpass", "csrf_token": ""},
        follow_redirects=False,
    )
    return resp.cookies


@patch("app.services.stripe_service.stripe.checkout.Session.create")
@patch("app.services.email_service.resend.Emails.send", return_value={"id": "test"})
@patch("app.routers.webhooks.stripe.Webhook.construct_event")
def test_e2e_stripe_flow(
    mock_webhook, mock_email, mock_stripe_session, tmp_path, monkeypatch
):
    """Stripe-Flow: Bestellen → Webhook → bezahlt → Admin setzt versendet."""
    pw_hash = _make_hash("testpass")
    monkeypatch.setattr("app.config.settings.database_path", str(tmp_path / "test.db"))
    monkeypatch.setattr("app.config.settings.admin_credentials", f"dev:{pw_hash}")

    from app.database import init_db
    init_db()
    from app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # --- Schritt 1: Bestellung aufgeben ---
    mock_stripe_session.return_value = MagicMock(
        id="cs_e2e_stripe",
        url="https://checkout.stripe.com/test",
    )

    from app.csrf import generiere_csrf_token
    csrf = generiere_csrf_token("change-me")

    cart_data = json.dumps([{"produkt_id": 1, "menge": 2}])
    resp = client.post(
        "/bestellen",
        data={
            "vorname": "Max",
            "nachname": "Muster",
            "email": "max@test.ch",
            "strasse": "Musterstr. 1",
            "plz": "4600",
            "ort": "Olten",
            "versandart": "versand",
            "zahlungsart": "stripe",
            "cart_data": cart_data,
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "stripe.com" in resp.headers["location"]

    # --- Schritt 2: Stripe-Webhook simulieren ---
    mock_webhook.return_value = MagicMock(
        type="checkout.session.completed",
        data=MagicMock(object=MagicMock(id="cs_e2e_stripe")),
    )

    resp = client.post(
        "/webhook/stripe",
        content=b'{"type": "checkout.session.completed"}',
        headers={"stripe-signature": "test_sig"},
    )
    assert resp.status_code == 200
    assert mock_email.call_count == 1  # Bestätigungs-E-Mail gesendet

    # --- Schritt 3: Admin sieht Bestellung als bezahlt ---
    cookies = _admin_login(client)
    client.cookies = cookies

    resp = client.get("/admin/")
    assert resp.status_code == 200
    assert "bezahlt" in resp.text

    # --- Schritt 4: Admin setzt auf versendet ---
    resp = client.post(
        "/admin/bestellungen/1/status",
        data={"neuer_status": "versendet", "csrf_token": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    # --- Schritt 5: Status-Verlauf prüfen ---
    from app.database import get_db

    conn = get_db()
    row = conn.execute("SELECT status FROM bestellungen WHERE id = 1").fetchone()
    assert dict(row)["status"] == "versendet"

    logs = conn.execute(
        "SELECT * FROM admin_log WHERE bestellung_id = 1 "
        "AND aktion = 'status_geaendert' ORDER BY id"
    ).fetchall()
    assert len(logs) == 2  # neu→bezahlt (Webhook) + bezahlt→versendet (Admin)
    conn.close()
```

- [ ] **Step 2: Test ausführen**

Run: `source .venv/bin/activate && python -m pytest tests/test_e2e_bestellzyklus.py::test_e2e_stripe_flow -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_e2e_bestellzyklus.py
git commit -m "test: E2E Stripe-Flow (Bestellen → Webhook → Admin)"
```

---

## Task 5: E2E Rechnungs-Flow

**Files:**
- Modify: `tests/test_e2e_bestellzyklus.py`

- [ ] **Step 1: Rechnungs-Flow-Test hinzufügen**

Am Ende der Datei hinzufügen:

```python
@patch("app.services.qr_service.QRBill")
@patch("app.services.email_service.resend.Emails.send", return_value={"id": "test"})
def test_e2e_rechnungs_flow(mock_email, mock_qr, tmp_path, monkeypatch):
    """Rechnungs-Flow: Bestellen → E-Mail mit QR → Admin bezahlt → abholbereit."""
    pw_hash = _make_hash("testpass")
    monkeypatch.setattr("app.config.settings.database_path", str(tmp_path / "test.db"))
    monkeypatch.setattr("app.config.settings.admin_credentials", f"dev:{pw_hash}")

    from app.database import init_db
    init_db()
    from app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # QR-Mock: gibt Bytes zurück
    mock_qr_instance = MagicMock()
    mock_qr_instance.as_svg.return_value = b"<svg>mock</svg>"
    mock_qr.return_value = mock_qr_instance

    # --- Schritt 1: Bestellung mit Rechnung aufgeben ---
    from app.csrf import generiere_csrf_token
    csrf = generiere_csrf_token("change-me")

    cart_data = json.dumps([{"produkt_id": 2, "menge": 1}])
    resp = client.post(
        "/bestellen",
        data={
            "vorname": "Anna",
            "nachname": "Test",
            "email": "anna@test.ch",
            "strasse": "Testweg 5",
            "plz": "3000",
            "ort": "Bern",
            "versandart": "abholung",
            "zahlungsart": "rechnung",
            "cart_data": cart_data,
            "csrf_token": csrf,
        },
    )
    assert resp.status_code == 200
    assert "Bestellbestätigung" in resp.text or "bestell" in resp.text.lower()
    assert mock_email.call_count == 1  # Bestätigungs-E-Mail sofort gesendet

    # --- Schritt 2: Admin setzt auf bezahlt ---
    cookies = _admin_login(client)
    client.cookies = cookies

    resp = client.post(
        "/admin/bestellungen/1/status",
        data={"neuer_status": "bezahlt", "csrf_token": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    # --- Schritt 3: Admin setzt auf abholbereit ---
    resp = client.post(
        "/admin/bestellungen/1/status",
        data={"neuer_status": "abholbereit", "csrf_token": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    # --- Schritt 4: Status-Verlauf prüfen ---
    from app.database import get_db

    conn = get_db()
    row = conn.execute("SELECT status FROM bestellungen WHERE id = 1").fetchone()
    assert dict(row)["status"] == "abholbereit"

    logs = conn.execute(
        "SELECT * FROM admin_log WHERE bestellung_id = 1 "
        "AND aktion = 'status_geaendert' ORDER BY id"
    ).fetchall()
    assert len(logs) == 2  # neu→bezahlt + bezahlt→abholbereit
    conn.close()
```

- [ ] **Step 2: Test ausführen**

Run: `source .venv/bin/activate && python -m pytest tests/test_e2e_bestellzyklus.py::test_e2e_rechnungs_flow -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_e2e_bestellzyklus.py
git commit -m "test: E2E Rechnungs-Flow (Bestellen → QR-Rechnung → Admin)"
```

---

## Task 6: E2E Storno nach Zahlung

**Files:**
- Modify: `tests/test_e2e_bestellzyklus.py`

- [ ] **Step 1: Storno-Test hinzufügen**

Am Ende der Datei hinzufügen:

```python
@patch("app.services.stripe_service.stripe.checkout.Session.create")
@patch("app.services.email_service.resend.Emails.send", return_value={"id": "test"})
@patch("app.routers.webhooks.stripe.Webhook.construct_event")
def test_e2e_storno_nach_zahlung(
    mock_webhook, mock_email, mock_stripe_session, tmp_path, monkeypatch
):
    """Storno: Bestellen → Webhook bezahlt → Admin storniert."""
    pw_hash = _make_hash("testpass")
    monkeypatch.setattr("app.config.settings.database_path", str(tmp_path / "test.db"))
    monkeypatch.setattr("app.config.settings.admin_credentials", f"dev:{pw_hash}")

    from app.database import init_db
    init_db()
    from app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # --- Bestellen ---
    mock_stripe_session.return_value = MagicMock(
        id="cs_e2e_storno",
        url="https://checkout.stripe.com/test",
    )

    from app.csrf import generiere_csrf_token
    csrf = generiere_csrf_token("change-me")

    cart_data = json.dumps([{"produkt_id": 3, "menge": 1}])
    client.post(
        "/bestellen",
        data={
            "vorname": "Peter",
            "nachname": "Storno",
            "email": "peter@test.ch",
            "strasse": "Stornoweg 1",
            "plz": "8000",
            "ort": "Zürich",
            "versandart": "versand",
            "zahlungsart": "stripe",
            "cart_data": cart_data,
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )

    # --- Webhook: bezahlt ---
    mock_webhook.return_value = MagicMock(
        type="checkout.session.completed",
        data=MagicMock(object=MagicMock(id="cs_e2e_storno")),
    )
    client.post(
        "/webhook/stripe",
        content=b'{"type": "checkout.session.completed"}',
        headers={"stripe-signature": "test_sig"},
    )

    # --- Admin: stornieren ---
    cookies = _admin_login(client)
    client.cookies = cookies

    resp = client.post(
        "/admin/bestellungen/1/status",
        data={"neuer_status": "storniert", "csrf_token": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    # --- Status-Verlauf prüfen ---
    from app.database import get_db

    conn = get_db()
    row = conn.execute("SELECT status FROM bestellungen WHERE id = 1").fetchone()
    assert dict(row)["status"] == "storniert"

    logs = conn.execute(
        "SELECT * FROM admin_log WHERE bestellung_id = 1 "
        "AND aktion = 'status_geaendert' ORDER BY id"
    ).fetchall()
    assert len(logs) == 2  # neu→bezahlt (Webhook) + bezahlt→storniert (Admin)
    details = [l["details"] for l in logs]
    assert '"nach": "bezahlt"' in details[0]
    assert '"nach": "storniert"' in details[1]
    conn.close()
```

- [ ] **Step 2: Alle E2E-Tests ausführen**

Run: `source .venv/bin/activate && python -m pytest tests/test_e2e_bestellzyklus.py -v`
Expected: 3 Tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_e2e_bestellzyklus.py
git commit -m "test: E2E Storno nach Zahlung"
```

---

## Task 7: Manuelles Testprotokoll

**Files:**
- Create: `docs/testprotokoll.md`

- [ ] **Step 1: Testprotokoll schreiben**

```markdown
# Manuelles Testprotokoll — Olivalle Webshop

> Dieses Protokoll dient als Checkliste für manuelle Browser-Tests vor dem Go-Live.
> Stripe Test-Keys verwenden (Dashboard → Developers → Test mode).

## Voraussetzungen

- [ ] Server läuft lokal (`make dev`)
- [ ] Stripe Test-Keys konfiguriert in `.env`
- [ ] Resend API-Key konfiguriert (oder Resend Dashboard offen zum Prüfen)
- [ ] Stripe Webhook lokal weiterleiten (`stripe listen --forward-to localhost:8000/webhook/stripe`)

---

## 1. Stripe-Flow

### Bestellung aufgeben
- [ ] Startseite öffnen → Produkte werden angezeigt
- [ ] Produkt in Warenkorb legen → Warenkorb-Icon zeigt Anzahl
- [ ] Weiteres Produkt hinzufügen, Menge ändern
- [ ] Warenkorb öffnen → Produkte, Mengen und Preise stimmen
- [ ] "Zur Kasse" klicken → Checkout-Seite öffnet sich
- [ ] Kundendaten eingeben (alle Pflichtfelder)
- [ ] Versandart "Postversand" wählen
- [ ] Zahlungsart "Kreditkarte / Twint" wählen
- [ ] Bestellung absenden → Weiterleitung zu Stripe

### Stripe-Zahlung
- [ ] Stripe Checkout zeigt korrekte Produkte und Beträge
- [ ] Mit Testkarte bezahlen: `4242 4242 4242 4242`, Ablauf beliebig, CVC beliebig
- [ ] Nach Zahlung: Bestätigungsseite mit Bestellnummer wird angezeigt

### E-Mail-Bestätigung
- [ ] Bestätigungs-E-Mail erhalten (Resend Dashboard prüfen)
- [ ] E-Mail enthält: Bestellnummer, Produkte, Mengen, Preise, Total
- [ ] Absender: `bestellung@olivalle.ch`

### Admin-Prüfung
- [ ] Admin-Login → Dashboard
- [ ] Bestellung mit Status "bezahlt" sichtbar
- [ ] Bestelldetail öffnen → Positionen, Kundendaten, Total stimmen
- [ ] Log zeigt: "status_geaendert" von "neu" nach "bezahlt"

---

## 2. Rechnungs-Flow

### Bestellung aufgeben
- [ ] Produkt in Warenkorb legen
- [ ] Checkout: Versandart "Abholung vor Ort" wählen
- [ ] Zahlungsart "Rechnung" wählen
- [ ] Bestellung absenden → Bestätigungsseite direkt angezeigt

### E-Mail mit QR-Rechnung
- [ ] Bestätigungs-E-Mail erhalten
- [ ] E-Mail enthält QR-Rechnung als Anhang (SVG)
- [ ] QR-Code ist scannbar (z.B. mit Banking-App im Testmodus)

### Admin-Prüfung
- [ ] Bestellung im Dashboard mit Status "neu" sichtbar
- [ ] Status manuell auf "bezahlt" ändern → Log-Eintrag erstellt
- [ ] Status auf "abholbereit" ändern → Log-Eintrag erstellt

---

## 3. Admin-Aktionen

### Login / Logout
- [ ] Admin-Login-Seite erreichbar unter `/admin/login`
- [ ] Login mit korrektem Passwort → Dashboard
- [ ] Logout → zurück zur Login-Seite
- [ ] Dashboard nicht erreichbar ohne Login

### Bestellverwaltung
- [ ] Bestellungen nach Status filtern
- [ ] Bestellungen nach Kundenname suchen
- [ ] Bestelldetail öffnen → alle Infos korrekt
- [ ] Notiz hinzufügen → erscheint im Aktivitäts-Log
- [ ] Mehrere Statusänderungen → alle im Log sichtbar

---

## 4. Fehlerfälle

- [ ] Leeren Warenkorb bestellen → Fehlermeldung "Warenkorb ist leer"
- [ ] Checkout ohne Pflichtfelder absenden → Validierungsfehler
- [ ] Admin-Login mit falschem Passwort → "Ungültiges Passwort"
- [ ] Nicht existierende Bestellung öffnen (`/admin/bestellungen/99999`) → 404
- [ ] Stripe-Zahlung abbrechen (zurück-Button) → Bestellung bleibt "neu"

---

## 5. Storno

- [ ] Bestellung über Stripe aufgeben und bezahlen
- [ ] Admin: Status auf "storniert" ändern
- [ ] Log zeigt Verlauf: neu → bezahlt → storniert
- [ ] (Stripe-Refund manuell im Stripe Dashboard durchführen)

---

## Testergebnis

| Datum | Tester | Ergebnis | Anmerkungen |
|-------|--------|----------|-------------|
| | | | |
```

- [ ] **Step 2: Commit**

```bash
git add docs/testprotokoll.md
git commit -m "docs: Manuelles Testprotokoll für Bestellzyklus"
```

---

## Task 8: Gesamtlauf aller Tests

- [ ] **Step 1: Alle Tests ausführen**

Run: `source .venv/bin/activate && python -m pytest tests/ -v`
Expected: Alle Tests PASS (76 bestehende + ~9 neue = ~85 Tests)

- [ ] **Step 2: Finaler Commit falls Anpassungen nötig waren**

Nur falls Fixes nötig waren.
