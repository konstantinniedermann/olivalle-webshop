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
    monkeypatch.setattr("app.config.settings.cookie_secure", False)
    from app.database import init_db

    init_db()
    from app.main import app

    return TestClient(app)


@patch("app.services.email_service.brevo_client")
@patch("app.routers.webhooks.stripe.Webhook.construct_event")
@patch("app.services.stripe_service.stripe.checkout.Session.create")
def test_e2e_stripe_flow(mock_stripe_create, mock_construct, mock_email, e2e_client):
    """Kompletter Stripe-Zyklus: Bestellen -> Webhook -> Admin-Statuswechsel."""
    client = e2e_client

    # --- CSRF-Token holen ---
    from tests.conftest import _admin_csrf, _checkout_csrf

    csrf = _checkout_csrf(client)

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
    # 2 E-Mails: Bestellbestätigung + Stakeholder-Benachrichtigung
    assert mock_email.transactional_emails.send_transac_email.call_count == 2

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
        data={"password": "testpass", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert resp_login.status_code == 303
    client.cookies = resp_login.cookies
    admin_csrf = _admin_csrf(resp_login.cookies.get("admin_session", ""))

    # --- 4. Admin sieht Bestellung im Dashboard ---
    resp_dashboard = client.get("/admin/")
    assert resp_dashboard.status_code == 200

    # --- 5. Admin aendert Status zu 'versendet' ---
    resp_status = client.post(
        f"/admin/bestellungen/{bestell_id}/status",
        data={"neuer_status": "versendet", "csrf_token": admin_csrf},
        follow_redirects=False,
    )
    assert resp_status.status_code == 303

    # Versandbestätigungs-E-Mail (3. Aufruf: Bestätigung + Stakeholder + Versand)
    assert mock_email.transactional_emails.send_transac_email.call_count == 3
    zweiter_call = mock_email.transactional_emails.send_transac_email.call_args_list[
        2
    ].kwargs
    assert "unterwegs" in zweiter_call["subject"]
    assert zweiter_call["to"][0]["email"] == "anna@test.ch"

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


@patch("app.services.qr_service.generiere_qr_rechnung", return_value=b"%PDF-fake")
@patch("app.services.email_service.brevo_client")
def test_e2e_rechnungs_flow(mock_email, mock_qr, e2e_client):
    """Kompletter Rechnungs-Zyklus: Bestellen -> QR-Rechnung -> Admin-Statuswechsel."""
    client = e2e_client

    # --- CSRF-Token holen ---
    from tests.conftest import _admin_csrf, _checkout_csrf

    csrf = _checkout_csrf(client)

    # --- 1. POST /bestellen mit zahlungsart=rechnung, versandart=abholung ---
    cart = json.dumps([{"produkt_id": 2, "menge": 1}])
    resp_bestellen = client.post(
        "/bestellen",
        data={
            "vorname": "Beat",
            "nachname": "Rechnung",
            "email": "beat@test.ch",
            "strasse": "Rechnungsweg",
            "hausnummer": "7",
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
    # Beim Rechnungs-Checkout: 2 E-Mails (Kundenbestätigung + Stakeholder-Benachrichtigung)
    assert mock_email.transactional_emails.send_transac_email.call_count == 2

    # Bestellung in DB pruefen
    from app.database import get_db

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT b.id, b.status, b.zahlungsart, b.versandkosten_chf, "
            "k.strasse, k.hausnummer "
            "FROM bestellungen b JOIN kunden k ON b.kunde_id = k.id "
            "WHERE k.email = 'beat@test.ch'"
        ).fetchone()
        assert row is not None
        bestell_id = row["id"]
        assert row["status"] == "neu"
        assert row["zahlungsart"] == "rechnung"
        assert row["versandkosten_chf"] == 0  # Abholung = keine Versandkosten
        assert row["strasse"] == "Rechnungsweg"
        assert row["hausnummer"] == "7"
    finally:
        conn.close()

    # --- 2. Admin-Login ---
    resp_login = client.post(
        "/admin/login",
        data={"password": "testpass", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert resp_login.status_code == 303
    client.cookies = resp_login.cookies
    admin_csrf = _admin_csrf(resp_login.cookies.get("admin_session", ""))

    # Bestellung im Dashboard sichtbar
    resp_dashboard = client.get("/admin/")
    assert resp_dashboard.status_code == 200

    # --- 3. Admin aendert Status zu 'bezahlt' (manuelle Zahlungsbestaetigung) ---
    resp_status1 = client.post(
        f"/admin/bestellungen/{bestell_id}/status",
        data={"neuer_status": "bezahlt", "csrf_token": admin_csrf},
        follow_redirects=False,
    )
    assert resp_status1.status_code == 303

    # Zahlungseingangs-E-Mail muss gesendet worden sein (3. Aufruf, nach 2 Checkout-Mails)
    assert mock_email.transactional_emails.send_transac_email.call_count == 3
    dritter_call = mock_email.transactional_emails.send_transac_email.call_args_list[
        2
    ].kwargs
    assert "Zahlungseingang" in dritter_call["subject"]
    assert dritter_call["to"][0]["email"] == "beat@test.ch"

    # --- 4. Admin aendert Status zu 'abholbereit' ---
    resp_status2 = client.post(
        f"/admin/bestellungen/{bestell_id}/status",
        data={"neuer_status": "abholbereit", "csrf_token": admin_csrf},
        follow_redirects=False,
    )
    assert resp_status2.status_code == 303

    # Abholbereit-E-Mail muss gesendet worden sein (4. Aufruf)
    assert mock_email.transactional_emails.send_transac_email.call_count == 4
    vierter_call = mock_email.transactional_emails.send_transac_email.call_args_list[
        3
    ].kwargs
    assert "abholbereit" in vierter_call["subject"]
    assert vierter_call["to"][0]["email"] == "beat@test.ch"

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


@patch("app.services.email_service.brevo_client")
@patch("app.routers.webhooks.stripe.Webhook.construct_event")
@patch("app.services.stripe_service.stripe.checkout.Session.create")
def test_e2e_storno_nach_zahlung(
    mock_stripe_create, mock_construct, mock_email, e2e_client
):
    """E2E-Storno: Bestellen (Stripe) -> Webhook (bezahlt) -> Admin storniert."""
    client = e2e_client

    # --- CSRF-Token holen ---
    from tests.conftest import _admin_csrf, _checkout_csrf

    csrf = _checkout_csrf(client)

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
    assert mock_email.transactional_emails.send_transac_email.call_count == 2

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
        data={"password": "testpass", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert resp_login.status_code == 303
    client.cookies = resp_login.cookies
    admin_csrf = _admin_csrf(resp_login.cookies.get("admin_session", ""))

    # --- 4. Admin aendert Status zu 'storniert' ---
    resp_status = client.post(
        f"/admin/bestellungen/{bestell_id}/status",
        data={"neuer_status": "storniert", "csrf_token": admin_csrf},
        follow_redirects=False,
    )
    assert resp_status.status_code == 303

    # Stornierung darf KEINE zusätzliche E-Mail auslösen (nur Webhook-Mails von vorher)
    assert mock_email.transactional_emails.send_transac_email.call_count == 2

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


@patch("app.services.email_service.brevo_client")
def test_e2e_abholung_bar_flow(mock_email, e2e_client):
    """Kompletter Abholung-Bar-Zyklus: Bestellen -> Admin-Statuswechsel -> bezahlt."""
    client = e2e_client

    from tests.conftest import _admin_csrf, _checkout_csrf

    csrf = _checkout_csrf(client)

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
        data={"password": "testpass", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert resp_login.status_code == 303
    client.cookies = resp_login.cookies
    admin_csrf = _admin_csrf(resp_login.cookies.get("admin_session", ""))

    # --- 3. Admin setzt auf 'abholbereit' ---
    resp_status1 = client.post(
        f"/admin/bestellungen/{bestell_id}/status",
        data={"neuer_status": "abholbereit", "csrf_token": admin_csrf},
        follow_redirects=False,
    )
    assert resp_status1.status_code == 303

    # Abholbereit-E-Mail gesendet (3. Aufruf)
    assert mock_email.transactional_emails.send_transac_email.call_count == 3
    dritter_call = mock_email.transactional_emails.send_transac_email.call_args_list[
        2
    ].kwargs
    assert "abholbereit" in dritter_call["subject"]

    # --- 4. Admin markiert als 'bezahlt' (Bar-Zahlung erhalten) ---
    resp_status2 = client.post(
        f"/admin/bestellungen/{bestell_id}/status",
        data={"neuer_status": "bezahlt", "csrf_token": admin_csrf},
        follow_redirects=False,
    )
    assert resp_status2.status_code == 303

    # Zahlungseingangs-E-Mail gesendet (4. Aufruf)
    assert mock_email.transactional_emails.send_transac_email.call_count == 4
    vierter_call = mock_email.transactional_emails.send_transac_email.call_args_list[
        3
    ].kwargs
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
