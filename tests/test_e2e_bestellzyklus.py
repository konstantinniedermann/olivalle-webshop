"""E2E-Tests: Kompletter Bestellzyklus durch alle Schichten."""

import json
from unittest.mock import MagicMock, patch

import bcrypt
import pytest
from fastapi.testclient import TestClient


def _make_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


@pytest.fixture()
def e2e_client(tmp_path, monkeypatch):
    """TestClient mit Admin-Credentials und eigener DB."""
    pw_hash = _make_hash("testpass")
    monkeypatch.setattr("app.config.settings.database_path", str(tmp_path / "test.db"))
    monkeypatch.setattr("app.config.settings.admin_credentials", f"dev:{pw_hash}")
    from app.database import init_db

    init_db()
    from app.main import app

    return TestClient(app)


@patch("app.services.email_service.resend.Emails.send", return_value={"id": "test"})
@patch("app.routers.webhooks.stripe.Webhook.construct_event")
@patch("app.services.stripe_service.stripe.checkout.Session.create")
def test_e2e_stripe_flow(mock_stripe_create, mock_construct, mock_email, e2e_client):
    """Kompletter Stripe-Zyklus: Bestellen -> Webhook -> Admin-Statuswechsel."""
    client = e2e_client

    # --- CSRF-Token holen ---
    from app.csrf import generiere_csrf_token

    csrf = generiere_csrf_token("change-me")

    # --- 1. POST /bestellen mit zahlungsart=stripe ---
    stripe_session_id = "cs_test_e2e_123"
    mock_stripe_create.return_value = MagicMock(
        id=stripe_session_id,
        url="https://checkout.stripe.com/test",
    )

    cart = json.dumps([{"produkt_id": 1, "menge": 2}])
    resp_bestellen = client.post(
        "/bestellen",
        data={
            "vorname": "Anna",
            "nachname": "Tester",
            "email": "anna@test.ch",
            "strasse": "Testweg 5",
            "plz": "8000",
            "ort": "Zuerich",
            "versandart": "versand",
            "zahlungsart": "stripe",
            "cart_data": cart,
            "kommentar": "",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )

    # Erwartung: Redirect zu Stripe
    assert resp_bestellen.status_code == 303
    assert "checkout.stripe.com" in resp_bestellen.headers["location"]
    mock_stripe_create.assert_called_once()

    # Bestellung pruefen: Status muss 'neu' sein, stripe_session_id gesetzt
    from app.database import get_db

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, status, stripe_session_id FROM bestellungen WHERE stripe_session_id = ?",
            (stripe_session_id,),
        ).fetchone()
        assert row is not None
        bestell_id = row["id"]
        assert row["status"] == "neu"
        assert row["stripe_session_id"] == stripe_session_id
    finally:
        conn.close()

    # --- 2. Stripe-Webhook simulieren (checkout.session.completed) ---
    mock_construct.return_value = MagicMock(
        type="checkout.session.completed",
        data=MagicMock(object=MagicMock(id=stripe_session_id)),
    )

    resp_webhook = client.post(
        "/webhook/stripe",
        content=b'{"type": "checkout.session.completed"}',
        headers={"stripe-signature": "test_sig"},
    )
    assert resp_webhook.status_code == 200
    mock_email.assert_called_once()

    # Status muss jetzt 'bezahlt' sein
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT status FROM bestellungen WHERE id = ?", (bestell_id,)
        ).fetchone()
        assert row["status"] == "bezahlt"

        # Webhook-Log pruefen: neu -> bezahlt durch system
        log_webhook = conn.execute(
            "SELECT * FROM admin_log WHERE bestellung_id = ? AND aktion = 'status_geaendert'",
            (bestell_id,),
        ).fetchone()
        assert log_webhook is not None
        details = json.loads(log_webhook["details"])
        assert details["von"] == "neu"
        assert details["nach"] == "bezahlt"
        assert log_webhook["admin_label"] == "system"
    finally:
        conn.close()

    # --- 3. Admin-Login ---
    resp_login = client.post(
        "/admin/login",
        data={"password": "testpass", "csrf_token": ""},
        follow_redirects=False,
    )
    assert resp_login.status_code == 303
    client.cookies = resp_login.cookies

    # --- 4. Admin sieht Bestellung im Dashboard ---
    resp_dashboard = client.get("/admin/")
    assert resp_dashboard.status_code == 200

    # --- 5. Admin aendert Status zu 'versendet' ---
    resp_status = client.post(
        f"/admin/bestellungen/{bestell_id}/status",
        data={"neuer_status": "versendet", "csrf_token": ""},
        follow_redirects=False,
    )
    assert resp_status.status_code == 303

    # --- 6. Verifikation: Status-Historie im admin_log ---
    conn = get_db()
    try:
        # Finaler Status
        row = conn.execute(
            "SELECT status FROM bestellungen WHERE id = ?", (bestell_id,)
        ).fetchone()
        assert row["status"] == "versendet"

        # Alle Status-Aenderungen chronologisch
        logs = conn.execute(
            "SELECT * FROM admin_log WHERE bestellung_id = ? AND aktion = 'status_geaendert' "
            "ORDER BY zeitpunkt ASC",
            (bestell_id,),
        ).fetchall()
        assert len(logs) == 2

        # Erster Eintrag: Webhook (neu -> bezahlt, system)
        d1 = json.loads(logs[0]["details"])
        assert d1["von"] == "neu"
        assert d1["nach"] == "bezahlt"
        assert logs[0]["admin_label"] == "system"

        # Zweiter Eintrag: Admin (bezahlt -> versendet, dev)
        d2 = json.loads(logs[1]["details"])
        assert d2["von"] == "bezahlt"
        assert d2["nach"] == "versendet"
        assert logs[1]["admin_label"] == "dev"
    finally:
        conn.close()


@patch("app.services.qr_service.QRBill")
@patch("app.services.email_service.resend.Emails.send", return_value={"id": "test"})
def test_e2e_rechnungs_flow(mock_email, mock_qr, e2e_client):
    """Kompletter Rechnungs-Zyklus: Bestellen -> QR-Rechnung -> Admin-Statuswechsel."""
    client = e2e_client

    # QR-Bill Mock konfigurieren
    mock_qr_instance = MagicMock()
    mock_qr_instance.as_svg.return_value = b"<svg>mock</svg>"
    mock_qr.return_value = mock_qr_instance

    # --- CSRF-Token holen ---
    from app.csrf import generiere_csrf_token

    csrf = generiere_csrf_token("change-me")

    # --- 1. POST /bestellen mit zahlungsart=rechnung, versandart=abholung ---
    cart = json.dumps([{"produkt_id": 2, "menge": 1}])
    resp_bestellen = client.post(
        "/bestellen",
        data={
            "vorname": "Beat",
            "nachname": "Rechnung",
            "email": "beat@test.ch",
            "strasse": "Rechnungsweg 7",
            "plz": "3000",
            "ort": "Bern",
            "versandart": "abholung",
            "zahlungsart": "rechnung",
            "cart_data": cart,
            "kommentar": "",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )

    # Rechnung liefert direkt die Bestaetigungsseite (Status 200)
    assert resp_bestellen.status_code == 200
    assert "bestell" in resp_bestellen.text.lower()
    mock_email.assert_called_once()

    # Bestellung in DB pruefen
    from app.database import get_db

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT b.id, b.status, b.zahlungsart, b.versandkosten_chf "
            "FROM bestellungen b JOIN kunden k ON b.kunde_id = k.id "
            "WHERE k.email = 'beat@test.ch'"
        ).fetchone()
        assert row is not None
        bestell_id = row["id"]
        assert row["status"] == "neu"
        assert row["zahlungsart"] == "rechnung"
        assert row["versandkosten_chf"] == 0  # Abholung = keine Versandkosten
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

    # Bestellung im Dashboard sichtbar
    resp_dashboard = client.get("/admin/")
    assert resp_dashboard.status_code == 200

    # --- 3. Admin aendert Status zu 'bezahlt' (manuelle Zahlungsbestaetigung) ---
    resp_status1 = client.post(
        f"/admin/bestellungen/{bestell_id}/status",
        data={"neuer_status": "bezahlt", "csrf_token": ""},
        follow_redirects=False,
    )
    assert resp_status1.status_code == 303

    # --- 4. Admin aendert Status zu 'abholbereit' ---
    resp_status2 = client.post(
        f"/admin/bestellungen/{bestell_id}/status",
        data={"neuer_status": "abholbereit", "csrf_token": ""},
        follow_redirects=False,
    )
    assert resp_status2.status_code == 303

    # --- 5. Verifikation: Status und Log pruefen ---
    conn = get_db()
    try:
        # Finaler Status
        row = conn.execute(
            "SELECT status FROM bestellungen WHERE id = ?", (bestell_id,)
        ).fetchone()
        assert row["status"] == "abholbereit"

        # Alle Status-Aenderungen chronologisch
        logs = conn.execute(
            "SELECT * FROM admin_log WHERE bestellung_id = ? AND aktion = 'status_geaendert' "
            "ORDER BY zeitpunkt ASC",
            (bestell_id,),
        ).fetchall()
        assert len(logs) == 2

        # Erster Eintrag: neu -> bezahlt (Admin)
        d1 = json.loads(logs[0]["details"])
        assert d1["von"] == "neu"
        assert d1["nach"] == "bezahlt"
        assert logs[0]["admin_label"] == "dev"

        # Zweiter Eintrag: bezahlt -> abholbereit (Admin)
        d2 = json.loads(logs[1]["details"])
        assert d2["von"] == "bezahlt"
        assert d2["nach"] == "abholbereit"
        assert logs[1]["admin_label"] == "dev"
    finally:
        conn.close()


@patch("app.services.email_service.resend.Emails.send", return_value={"id": "test"})
@patch("app.routers.webhooks.stripe.Webhook.construct_event")
@patch("app.services.stripe_service.stripe.checkout.Session.create")
def test_e2e_storno_nach_zahlung(mock_stripe_create, mock_construct, mock_email, e2e_client):
    """E2E-Storno: Bestellen (Stripe) -> Webhook (bezahlt) -> Admin storniert."""
    client = e2e_client

    # --- CSRF-Token holen ---
    from app.csrf import generiere_csrf_token

    csrf = generiere_csrf_token("change-me")

    # --- 1. POST /bestellen mit zahlungsart=stripe ---
    stripe_session_id = "cs_e2e_storno"
    mock_stripe_create.return_value = MagicMock(
        id=stripe_session_id,
        url="https://checkout.stripe.com/storno",
    )

    cart = json.dumps([{"produkt_id": 3, "menge": 1}])
    resp_bestellen = client.post(
        "/bestellen",
        data={
            "vorname": "Peter",
            "nachname": "Storno",
            "email": "peter@storno.ch",
            "strasse": "Stornoweg 1",
            "plz": "9000",
            "ort": "St. Gallen",
            "versandart": "versand",
            "zahlungsart": "stripe",
            "cart_data": cart,
            "kommentar": "",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )

    # Erwartung: Redirect zu Stripe
    assert resp_bestellen.status_code == 303
    assert "checkout.stripe.com" in resp_bestellen.headers["location"]
    mock_stripe_create.assert_called_once()

    # Bestellung pruefen: Status muss 'neu' sein
    from app.database import get_db

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, status, stripe_session_id FROM bestellungen WHERE stripe_session_id = ?",
            (stripe_session_id,),
        ).fetchone()
        assert row is not None
        bestell_id = row["id"]
        assert row["status"] == "neu"
        assert row["stripe_session_id"] == stripe_session_id
    finally:
        conn.close()

    # --- 2. Stripe-Webhook simulieren (checkout.session.completed) ---
    mock_construct.return_value = MagicMock(
        type="checkout.session.completed",
        data=MagicMock(object=MagicMock(id=stripe_session_id)),
    )

    resp_webhook = client.post(
        "/webhook/stripe",
        content=b'{"type": "checkout.session.completed"}',
        headers={"stripe-signature": "test_sig"},
    )
    assert resp_webhook.status_code == 200
    mock_email.assert_called_once()

    # Status muss jetzt 'bezahlt' sein
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT status FROM bestellungen WHERE id = ?", (bestell_id,)
        ).fetchone()
        assert row["status"] == "bezahlt"
    finally:
        conn.close()

    # --- 3. Admin-Login ---
    resp_login = client.post(
        "/admin/login",
        data={"password": "testpass", "csrf_token": ""},
        follow_redirects=False,
    )
    assert resp_login.status_code == 303
    client.cookies = resp_login.cookies

    # --- 4. Admin aendert Status zu 'storniert' ---
    resp_status = client.post(
        f"/admin/bestellungen/{bestell_id}/status",
        data={"neuer_status": "storniert", "csrf_token": ""},
        follow_redirects=False,
    )
    assert resp_status.status_code == 303

    # --- 5. Verifikation: Finaler Status und Log-Eintraege ---
    conn = get_db()
    try:
        # Finaler Status muss 'storniert' sein
        row = conn.execute(
            "SELECT status FROM bestellungen WHERE id = ?", (bestell_id,)
        ).fetchone()
        assert row["status"] == "storniert"

        # Genau 2 Log-Eintraege in chronologischer Reihenfolge
        logs = conn.execute(
            "SELECT * FROM admin_log WHERE bestellung_id = ? AND aktion = 'status_geaendert' "
            "ORDER BY zeitpunkt ASC",
            (bestell_id,),
        ).fetchall()
        assert len(logs) == 2

        # Erster Eintrag: Webhook (neu -> bezahlt, system)
        d1 = json.loads(logs[0]["details"])
        assert d1["von"] == "neu"
        assert d1["nach"] == "bezahlt"
        assert logs[0]["admin_label"] == "system"

        # Zweiter Eintrag: Admin (bezahlt -> storniert, dev)
        d2 = json.loads(logs[1]["details"])
        assert d2["von"] == "bezahlt"
        assert d2["nach"] == "storniert"
        assert logs[1]["admin_label"] == "dev"
    finally:
        conn.close()
