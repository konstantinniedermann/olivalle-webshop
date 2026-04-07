import json
from unittest.mock import MagicMock

from tests.conftest import _admin_csrf, _login_csrf


class TestAdminLogin:
    def test_login_page_renders(self, admin_client):
        resp = admin_client.get("/admin/login")
        assert resp.status_code == 200
        assert "Passwort" in resp.text

    def test_login_success_redirects_to_dashboard(self, admin_client):
        csrf = _login_csrf(admin_client)
        resp = admin_client.post(
            "/admin/login",
            data={"password": "testpass", "csrf_token": csrf},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        assert resp.headers["location"] == "/admin/"
        assert "admin_session" in resp.cookies

    def test_login_cookie_secure_flag(self, admin_client, monkeypatch):
        # GET zuerst (mit cookie_secure=False), damit csrf_id im Jar landet.
        csrf = _login_csrf(admin_client)
        monkeypatch.setattr("app.config.settings.cookie_secure", True)
        resp = admin_client.post(
            "/admin/login",
            data={"password": "testpass", "csrf_token": csrf},
            follow_redirects=False,
        )
        assert resp.status_code == 303, resp.text
        set_cookie = " ".join(resp.headers.get_list("set-cookie"))
        assert "admin_session=" in set_cookie
        assert "Secure" in set_cookie
        assert "HttpOnly" in set_cookie
        assert "SameSite=strict" in set_cookie.lower() or "samesite=strict" in set_cookie.lower()

    def test_login_wrong_password(self, admin_client):
        csrf = _login_csrf(admin_client)
        resp = admin_client.post(
            "/admin/login",
            data={"password": "falsch", "csrf_token": csrf},
        )
        assert resp.status_code == 200
        assert "Ungültig" in resp.text

    def test_dashboard_requires_login(self, admin_client):
        resp = admin_client.get("/admin/", follow_redirects=False)
        assert resp.status_code == 303
        assert "/admin/login" in resp.headers["location"]


def _admin_login(client, csrf_token=None):
    """Login as admin, return session cookies."""
    csrf = _login_csrf(client)
    resp = client.post(
        "/admin/login",
        data={"password": "testpass", "csrf_token": csrf},
        follow_redirects=False,
    )
    return resp.cookies


def _insert_test_order(order_id=99):
    """Insert a customer and order directly into the DB, return order ID."""
    from app.database import get_db

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO kunden (id, vorname, nachname, email, strasse, plz, ort) "
            "VALUES (?, 'Test', 'Kunde', 'test@example.ch', 'Teststr 1', '3000', 'Bern')",
            (order_id,),
        )
        conn.execute(
            "INSERT INTO bestellungen (id, kunde_id, zahlungsart, versandart, total_chf, status) "
            "VALUES (?, ?, 'stripe', 'versand', 50.00, 'neu')",
            (order_id, order_id),
        )
        conn.commit()
    finally:
        conn.close()
    return order_id


class TestAdminDashboard:
    def test_dashboard_renders(self, admin_client):
        cookies = _admin_login(admin_client)
        admin_client.cookies = cookies
        resp = admin_client.get("/admin/")
        assert resp.status_code == 200
        assert "Dashboard" in resp.text

    def test_dashboard_ungueltiges_datum_400(self, admin_client):
        admin_client.cookies = _admin_login(admin_client)
        resp = admin_client.get("/admin/?datum_von=abc")
        assert resp.status_code == 400

    def test_logout_clears_session(self, admin_client):
        cookies = _admin_login(admin_client)
        admin_client.cookies = cookies
        csrf = _admin_csrf(cookies.get("admin_session", ""))
        resp = admin_client.post(
            "/admin/logout",
            data={"csrf_token": csrf},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        admin_client.cookies = resp.cookies
        resp2 = admin_client.get("/admin/", follow_redirects=False)
        assert resp2.status_code == 303


class TestEmailLogging:
    def test_email_service_logs_ausgang(self, db, monkeypatch):
        """After sending an email, an email_ausgang log entry should exist."""
        monkeypatch.setattr(
            "app.services.email_service.brevo_client", MagicMock()
        )

        from app.services.email_service import sende_bestellbestaetigung

        db.execute(
            "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
            "VALUES ('Max', 'Muster', 'max@test.ch', 'Str 1', '4600', 'Olten')"
        )
        db.execute(
            "INSERT INTO bestellungen (kunde_id, zahlungsart, versandart, total_chf) "
            "VALUES (1, 'stripe', 'versand', 50.00)"
        )
        db.commit()

        sende_bestellbestaetigung(
            empfaenger="max@test.ch",
            bestell_id=1,
            kunde={"vorname": "Max", "nachname": "Muster"},
            positionen=[{"name": "Öl 250ml", "menge": 2, "einzelpreis_chf": 8.0}],
            versandkosten=9.90,
            total=25.90,
            conn=db,
        )

        log = db.execute(
            "SELECT * FROM admin_log WHERE aktion = 'email_ausgang'"
        ).fetchone()
        assert log is not None
        assert "max@test.ch" in log["details"]


class TestAdminStatusAenderung:
    def test_status_aendern_erfolgreich(self, admin_client):
        cookies = _admin_login(admin_client)
        admin_client.cookies = cookies
        csrf = _admin_csrf(cookies.get("admin_session", ""))
        order_id = _insert_test_order()

        resp = admin_client.post(
            f"/admin/bestellungen/{order_id}/status",
            data={"neuer_status": "bezahlt", "csrf_token": csrf},
            follow_redirects=False,
        )
        assert resp.status_code == 303

        # Verify status updated in DB
        from app.database import get_db

        conn = get_db()
        try:
            row = conn.execute(
                "SELECT status FROM bestellungen WHERE id = ?", (order_id,)
            ).fetchone()
            assert row["status"] == "bezahlt"

            # Verify log entry
            log = conn.execute(
                "SELECT * FROM admin_log WHERE bestellung_id = ? AND aktion = 'status_geaendert'",
                (order_id,),
            ).fetchone()
            assert log is not None
            details = json.loads(log["details"])
            assert details["von"] == "neu"
            assert details["nach"] == "bezahlt"
        finally:
            conn.close()

    def test_status_aendern_bestellung_nicht_gefunden(self, admin_client):
        cookies = _admin_login(admin_client)
        admin_client.cookies = cookies
        csrf = _admin_csrf(cookies.get("admin_session", ""))

        resp = admin_client.post(
            "/admin/bestellungen/999/status",
            data={"neuer_status": "bezahlt", "csrf_token": csrf},
            follow_redirects=False,
        )
        assert resp.status_code == 404


class TestAdminNotiz:
    def test_notiz_hinzufuegen_erfolgreich(self, admin_client):
        cookies = _admin_login(admin_client)
        admin_client.cookies = cookies
        csrf = _admin_csrf(cookies.get("admin_session", ""))
        order_id = _insert_test_order()

        resp = admin_client.post(
            f"/admin/bestellungen/{order_id}/notiz",
            data={
                "typ": "notiz_hinzugefuegt",
                "text": "Kunde hat angerufen",
                "csrf_token": csrf,
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303

        from app.database import get_db

        conn = get_db()
        try:
            log = conn.execute(
                "SELECT * FROM admin_log WHERE bestellung_id = ? AND aktion = 'notiz_hinzugefuegt'",
                (order_id,),
            ).fetchone()
            assert log is not None
            assert "Kunde hat angerufen" in log["details"]
            assert log["bestellung_id"] == order_id
        finally:
            conn.close()
