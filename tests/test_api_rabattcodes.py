def test_rabattcode_pruefen_gueltig(client):
    from app.database import get_db

    conn = get_db()
    conn.execute(
        "INSERT INTO rabattcodes "
        "(code, rabattart, rabattwert, gueltig_von, gueltig_bis) "
        "VALUES ('AKTION10', 'prozent', 10.0, '2026-01-01', '2026-12-31')"
    )
    conn.commit()
    conn.close()

    response = client.post(
        "/api/rabattcode/pruefen",
        json={"code": "AKTION10", "email": "test@example.com", "subtotal": 26.00},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["gueltig"] is True
    assert data["rabattbetrag"] == 2.60


def test_rabattcode_pruefen_ungueltig(client):
    response = client.post(
        "/api/rabattcode/pruefen",
        json={"code": "GIBTSNICHT", "email": "test@example.com", "subtotal": 26.00},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["gueltig"] is False
    assert "fehler" in data


def test_bestellung_mit_rabattcode(client, csrf_token):
    from app.database import get_db

    conn = get_db()
    conn.execute(
        "INSERT INTO rabattcodes "
        "(code, rabattart, rabattwert, gueltig_von, gueltig_bis) "
        "VALUES ('WILLKOMMEN', 'fixbetrag', 5.0, '2026-01-01', '2026-12-31')"
    )
    conn.commit()
    conn.close()

    import json

    cart_data = json.dumps([{"produkt_id": 1, "menge": 2}])  # 2x CHF 8 = 16
    response = client.post(
        "/bestellen",
        data={
            "vorname": "Test",
            "nachname": "User",
            "email": "test@example.com",
            "strasse": "Teststr. 1",
            "plz": "4600",
            "ort": "Olten",
            "versandart": "abholung",
            "zahlungsart": "abholung_bar",
            "cart_data": cart_data,
            "rabattcode": "WILLKOMMEN",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    assert response.status_code in (200, 303)

    conn = get_db()
    row = conn.execute(
        "SELECT rabattbetrag_chf, total_chf FROM bestellungen WHERE id = 1"
    ).fetchone()
    conn.close()
    assert row["rabattbetrag_chf"] == 5.00
    assert row["total_chf"] == 11.00  # 16 - 5 + 0 Versand


def test_bestellung_ohne_rabattcode(client, csrf_token):
    import json

    from app.database import get_db

    cart_data = json.dumps([{"produkt_id": 1, "menge": 1}])
    response = client.post(
        "/bestellen",
        data={
            "vorname": "Test",
            "nachname": "User",
            "email": "test@example.com",
            "strasse": "Teststr. 1",
            "plz": "4600",
            "ort": "Olten",
            "versandart": "abholung",
            "zahlungsart": "abholung_bar",
            "cart_data": cart_data,
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    assert response.status_code in (200, 303)

    conn = get_db()
    row = conn.execute(
        "SELECT rabattbetrag_chf, total_chf FROM bestellungen WHERE id = 1"
    ).fetchone()
    conn.close()
    assert row["rabattbetrag_chf"] == 0
    assert row["total_chf"] == 8.00


def test_rabattcode_race_wird_am_limit_abgelehnt(client, csrf_token, monkeypatch):
    """#168: Trifft die Einlösung auf ein bereits erreichtes globales Limit
    (Race), lehnt der Bestell-Endpoint mit 400 ab und persistiert nichts —
    auch wenn die vorherige Prüfung den Code noch als gültig gesehen hat.
    """
    import json

    from app.database import get_db

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO rabattcodes "
        "(code, rabattart, rabattwert, gueltig_von, gueltig_bis, "
        "max_einloesungen, aktuelle_einloesungen) "
        "VALUES ('RACE', 'fixbetrag', 5.0, '2026-01-01', '2026-12-31', 1, 1)"
    )
    code_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Simuliere das Race-Fenster: die Prüfung sah den Code noch als gültig,
    # obwohl das Limit inzwischen belegt ist.
    monkeypatch.setattr(
        "app.services.rabattcode_service.pruefe_rabattcode",
        lambda conn, code, email, subtotal: {
            "gueltig": True,
            "rabattbetrag": 5.0,
            "rabattcode_id": code_id,
            "code": "RACE",
        },
    )

    cart_data = json.dumps([{"produkt_id": 1, "menge": 2}])
    response = client.post(
        "/bestellen",
        data={
            "vorname": "Race",
            "nachname": "Tester",
            "email": "race@example.com",
            "strasse": "Teststr. 1",
            "plz": "4600",
            "ort": "Olten",
            "versandart": "abholung",
            "zahlungsart": "abholung_bar",
            "cart_data": cart_data,
            "rabattcode": "RACE",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    assert response.status_code == 400

    conn = get_db()
    try:
        kunden = conn.execute("SELECT COUNT(*) c FROM kunden").fetchone()["c"]
        best = conn.execute("SELECT COUNT(*) c FROM bestellungen").fetchone()["c"]
        aktuell = conn.execute(
            "SELECT aktuelle_einloesungen a FROM rabattcodes WHERE id = ?",
            (code_id,),
        ).fetchone()["a"]
    finally:
        conn.close()
    assert kunden == 0, "Kunde darf bei aufgebrauchtem Code nicht persistiert werden"
    assert best == 0, "Bestellung darf bei aufgebrauchtem Code nicht persistiert werden"
    assert aktuell == 1, "Kein Overshoot über max_einloesungen"


def _make_admin_client(tmp_path, monkeypatch):
    import bcrypt
    from fastapi.testclient import TestClient

    pw_hash = bcrypt.hashpw(b"testpass", bcrypt.gensalt()).decode()
    monkeypatch.setattr(
        "app.config.settings.database_path", str(tmp_path / "admin_test.db")
    )
    monkeypatch.setattr("app.config.settings.admin_credentials", f"dev:{pw_hash}")
    monkeypatch.setattr("app.config.settings.cookie_secure", False)
    from app.database import init_db

    init_db()
    from app.main import app

    return TestClient(app)


def _admin_login(admin_client):
    from app.config import settings
    from app.csrf import generiere_csrf_token

    get_resp = admin_client.get("/admin/login")
    csrf_id = get_resp.cookies.get("csrf_id", "")
    csrf = generiere_csrf_token(settings.secret_key, identity=f"anon:{csrf_id}")
    resp = admin_client.post(
        "/admin/login",
        data={"password": "testpass", "csrf_token": csrf},
        follow_redirects=False,
    )
    return resp.cookies


def test_admin_rabattcodes_uebersicht(tmp_path, monkeypatch):
    admin_client = _make_admin_client(tmp_path, monkeypatch)
    admin_client.cookies = _admin_login(admin_client)
    response = admin_client.get("/admin/rabattcodes")
    assert response.status_code == 200
    assert "Rabattcodes" in response.text
