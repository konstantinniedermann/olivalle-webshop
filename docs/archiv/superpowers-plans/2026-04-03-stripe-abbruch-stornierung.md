# Stripe-Abbruch/Fehler Stornierung — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bei Stripe-Checkout-Abbruch oder Zahlungsfehler die Bestellung automatisch als `storniert` markieren mit Log-Eintrag.

**Architecture:** Den bestehenden Webhook-Handler um zwei Stripe-Events erweitern (`checkout.session.expired`, `checkout.session.async_payment_failed`). Bei diesen Events wird die Bestellung auf `storniert` gesetzt und ein Log-Eintrag geschrieben. TDD-Ansatz: Tests zuerst.

**Tech Stack:** Python, FastAPI, SQLite, Stripe Webhooks, pytest

---

### Task 1: Tests fuer Stornierung bei Session-Ablauf

**Files:**
- Modify: `tests/test_api_webhooks.py`

- [ ] **Step 1: Test schreiben — checkout.session.expired storniert Bestellung**

Am Ende von `tests/test_api_webhooks.py` anfuegen:

```python
@patch("app.routers.webhooks.stripe.Webhook.construct_event")
def test_webhook_checkout_expired_storniert_bestellung(mock_construct, client, db):
    """Abgelaufene/abgebrochene Stripe-Session → Bestellung wird storniert."""
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('Max', 'Muster', 'max@test.ch', 'Str 1', '4600', 'Olten')"
    )
    db.execute(
        "INSERT INTO bestellungen"
        " (kunde_id, zahlungsart, versandart, total_chf,"
        " stripe_session_id, status) "
        "VALUES (1, 'stripe', 'versand', 25.90, 'cs_expired_123', 'neu')"
    )
    db.commit()

    mock_construct.return_value = MagicMock(
        type="checkout.session.expired",
        data=MagicMock(object=MagicMock(id="cs_expired_123")),
    )

    response = client.post(
        "/webhook/stripe",
        content=b'{"type": "checkout.session.expired"}',
        headers={"stripe-signature": "test_sig"},
    )
    assert response.status_code == 200

    row = db.execute("SELECT status FROM bestellungen WHERE id = 1").fetchone()
    assert dict(row)["status"] == "storniert"

    log = db.execute(
        "SELECT * FROM admin_log WHERE bestellung_id = 1"
    ).fetchone()
    assert log is not None
    assert "abgebrochen" in dict(log)["details"].lower() or "abgelaufen" in dict(log)["details"].lower()
```

- [ ] **Step 2: Test ausfuehren — muss fehlschlagen**

Run: `python -m pytest tests/test_api_webhooks.py::test_webhook_checkout_expired_storniert_bestellung -v`
Expected: FAIL — der Webhook behandelt `checkout.session.expired` noch nicht, Status bleibt `neu`.

- [ ] **Step 3: Commit**

```bash
git add tests/test_api_webhooks.py
git commit -m "test: failing Test fuer Stornierung bei Stripe-Session-Ablauf"
```

---

### Task 2: Tests fuer Stornierung bei Zahlungsfehler

**Files:**
- Modify: `tests/test_api_webhooks.py`

- [ ] **Step 1: Test schreiben — async_payment_failed storniert Bestellung**

Am Ende von `tests/test_api_webhooks.py` anfuegen:

```python
@patch("app.routers.webhooks.stripe.Webhook.construct_event")
def test_webhook_payment_failed_storniert_bestellung(mock_construct, client, db):
    """Fehlgeschlagene Zahlung → Bestellung wird storniert."""
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('Max', 'Muster', 'max@test.ch', 'Str 1', '4600', 'Olten')"
    )
    db.execute(
        "INSERT INTO bestellungen"
        " (kunde_id, zahlungsart, versandart, total_chf,"
        " stripe_session_id, status) "
        "VALUES (1, 'stripe', 'versand', 25.90, 'cs_failed_456', 'neu')"
    )
    db.commit()

    mock_construct.return_value = MagicMock(
        type="checkout.session.async_payment_failed",
        data=MagicMock(object=MagicMock(id="cs_failed_456")),
    )

    response = client.post(
        "/webhook/stripe",
        content=b'{"type": "checkout.session.async_payment_failed"}',
        headers={"stripe-signature": "test_sig"},
    )
    assert response.status_code == 200

    row = db.execute("SELECT status FROM bestellungen WHERE id = 1").fetchone()
    assert dict(row)["status"] == "storniert"

    log = db.execute(
        "SELECT * FROM admin_log WHERE bestellung_id = 1"
    ).fetchone()
    assert log is not None
    assert "fehlgeschlagen" in dict(log)["details"].lower()
```

- [ ] **Step 2: Test ausfuehren — muss fehlschlagen**

Run: `python -m pytest tests/test_api_webhooks.py::test_webhook_payment_failed_storniert_bestellung -v`
Expected: FAIL — der Webhook behandelt `checkout.session.async_payment_failed` noch nicht.

- [ ] **Step 3: Commit**

```bash
git add tests/test_api_webhooks.py
git commit -m "test: failing Test fuer Stornierung bei Stripe-Zahlungsfehler"
```

---

### Task 3: Test fuer Idempotenz — bereits stornierte Bestellung

**Files:**
- Modify: `tests/test_api_webhooks.py`

- [ ] **Step 1: Test schreiben — expired bei bereits bezahlter Bestellung aendert nichts**

Am Ende von `tests/test_api_webhooks.py` anfuegen:

```python
@patch("app.routers.webhooks.stripe.Webhook.construct_event")
def test_webhook_expired_ignoriert_nicht_neue_bestellung(mock_construct, client, db):
    """Expired-Event bei bereits bezahlter Bestellung → keine Aenderung."""
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('Max', 'Muster', 'max@test.ch', 'Str 1', '4600', 'Olten')"
    )
    db.execute(
        "INSERT INTO bestellungen"
        " (kunde_id, zahlungsart, versandart, total_chf,"
        " stripe_session_id, status) "
        "VALUES (1, 'stripe', 'versand', 25.90, 'cs_bezahlt_789', 'bezahlt')"
    )
    db.commit()

    mock_construct.return_value = MagicMock(
        type="checkout.session.expired",
        data=MagicMock(object=MagicMock(id="cs_bezahlt_789")),
    )

    response = client.post(
        "/webhook/stripe",
        content=b'{"type": "checkout.session.expired"}',
        headers={"stripe-signature": "test_sig"},
    )
    assert response.status_code == 200

    row = db.execute("SELECT status FROM bestellungen WHERE id = 1").fetchone()
    assert dict(row)["status"] == "bezahlt"
```

- [ ] **Step 2: Test ausfuehren — muss fehlschlagen**

Run: `python -m pytest tests/test_api_webhooks.py::test_webhook_expired_ignoriert_nicht_neue_bestellung -v`
Expected: FAIL — `checkout.session.expired` wird noch nicht behandelt.

- [ ] **Step 3: Commit**

```bash
git add tests/test_api_webhooks.py
git commit -m "test: failing Test fuer Idempotenz bei Stornierung"
```

---

### Task 4: Webhook-Handler implementieren

**Files:**
- Modify: `app/routers/webhooks.py`

- [ ] **Step 1: Stornierungslogik im Webhook implementieren**

In `app/routers/webhooks.py`, nach dem bestehenden `if event.type == "checkout.session.completed":` Block (vor `return {"status": "ok"}`), folgendes einfuegen:

```python
    if event.type in (
        "checkout.session.expired",
        "checkout.session.async_payment_failed",
    ):
        session = event.data.object
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT id, status FROM bestellungen "
                "WHERE stripe_session_id = ?",
                (session.id,),
            ).fetchone()
            if row and dict(row)["status"] == "neu":
                bestell_id = dict(row)["id"]
                conn.execute(
                    "UPDATE bestellungen SET status = 'storniert' "
                    "WHERE id = ?",
                    (bestell_id,),
                )
                conn.commit()

                from app.repositories.admin_repo import log_eintrag_schreiben

                grund = (
                    "Stripe Checkout abgebrochen oder abgelaufen"
                    if event.type == "checkout.session.expired"
                    else "Zahlung fehlgeschlagen"
                )
                log_eintrag_schreiben(
                    conn,
                    admin_label="system",
                    aktion="status_geaendert",
                    details=f'{{"von": "neu", "nach": "storniert", "grund": "{grund}"}}',
                    bestellung_id=bestell_id,
                )
        finally:
            conn.close()
```

- [ ] **Step 2: Alle Tests ausfuehren**

Run: `python -m pytest tests/test_api_webhooks.py -v`
Expected: Alle Tests PASS — inklusive der drei neuen.

- [ ] **Step 3: Commit**

```bash
git add app/routers/webhooks.py
git commit -m "feat: Stripe-Abbruch/Zahlungsfehler storniert Bestellung automatisch"
```

---

### Task 5: Manueller Smoke-Test

- [ ] **Step 1: Dev-Server starten und pruefen**

Run: `make dev` (oder `uvicorn app.main:app --reload`)

- [ ] **Step 2: Gesamte Test-Suite ausfuehren**

Run: `python -m pytest -v`
Expected: Alle Tests PASS.

- [ ] **Step 3: Finaler Commit falls noetig**

Nur falls Korrekturen noetig waren.
