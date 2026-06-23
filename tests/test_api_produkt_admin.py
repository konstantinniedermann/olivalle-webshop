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


def _csrf_fuer_session(cookies):
    from app.config import settings
    from app.csrf import admin_identity, generiere_csrf_token

    return generiere_csrf_token(
        settings.secret_key, identity=admin_identity(cookies.get("admin_session"))
    )


def test_admin_produkte_liste(tmp_path, monkeypatch):
    admin_client = _make_admin_client(tmp_path, monkeypatch)
    admin_client.cookies = _admin_login(admin_client)
    resp = admin_client.get("/admin/produkte")
    assert resp.status_code == 200
    assert "Olivenöl 750ml" in resp.text


def test_admin_aktion_setzen(tmp_path, monkeypatch):
    admin_client = _make_admin_client(tmp_path, monkeypatch)
    cookies = _admin_login(admin_client)
    admin_client.cookies = cookies
    csrf = _csrf_fuer_session(cookies)
    resp = admin_client.post(
        "/admin/produkte/2/aktion",
        data={
            "aktionspreis_chf": "12.00", "aktionstext": "MHD 09/2026",
            "aktion_von": "", "aktion_bis": "", "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    from app.database import get_db

    conn = get_db()
    row = conn.execute(
        "SELECT aktionspreis_chf, aktionstext FROM produkte WHERE id = 2"
    ).fetchone()
    conn.close()
    assert row["aktionspreis_chf"] == 12.0
    assert row["aktionstext"] == "MHD 09/2026"


def test_admin_aktion_groesser_als_preis_abgelehnt(tmp_path, monkeypatch):
    admin_client = _make_admin_client(tmp_path, monkeypatch)
    cookies = _admin_login(admin_client)
    admin_client.cookies = cookies
    csrf = _csrf_fuer_session(cookies)
    resp = admin_client.post(
        "/admin/produkte/2/aktion",
        data={
            "aktionspreis_chf": "20.00", "aktionstext": "zu teuer",
            "aktion_von": "", "aktion_bis": "", "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert resp.status_code == 400
    from app.database import get_db

    conn = get_db()
    row = conn.execute("SELECT aktionspreis_chf FROM produkte WHERE id = 2").fetchone()
    conn.close()
    assert row["aktionspreis_chf"] is None


def test_admin_aktion_entfernen(tmp_path, monkeypatch):
    admin_client = _make_admin_client(tmp_path, monkeypatch)
    cookies = _admin_login(admin_client)
    admin_client.cookies = cookies
    csrf = _csrf_fuer_session(cookies)
    # erst setzen
    admin_client.post(
        "/admin/produkte/2/aktion",
        data={"aktionspreis_chf": "12.00", "aktionstext": "x",
              "aktion_von": "", "aktion_bis": "", "csrf_token": csrf},
        follow_redirects=False,
    )
    # dann leerer Aktionspreis = entfernen
    resp = admin_client.post(
        "/admin/produkte/2/aktion",
        data={"aktionspreis_chf": "", "aktionstext": "",
              "aktion_von": "", "aktion_bis": "", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    from app.database import get_db

    conn = get_db()
    row = conn.execute("SELECT aktionspreis_chf FROM produkte WHERE id = 2").fetchone()
    conn.close()
    assert row["aktionspreis_chf"] is None


def test_admin_produkte_ohne_login_redirect(tmp_path, monkeypatch):
    admin_client = _make_admin_client(tmp_path, monkeypatch)
    resp = admin_client.get("/admin/produkte", follow_redirects=False)
    assert resp.status_code == 303


def test_admin_aktion_ungueltige_eingabe(tmp_path, monkeypatch):
    admin_client = _make_admin_client(tmp_path, monkeypatch)
    cookies = _admin_login(admin_client)
    admin_client.cookies = cookies
    csrf = _csrf_fuer_session(cookies)
    resp = admin_client.post(
        "/admin/produkte/2/aktion",
        data={
            "aktionspreis_chf": "abc", "aktionstext": "invalid",
            "aktion_von": "", "aktion_bis": "", "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert resp.status_code == 400


def test_admin_aktion_datum_invertiert_abgelehnt(tmp_path, monkeypatch):
    """F2: aktion_von > aktion_bis muss HTTP 400 liefern; DB bleibt unverändert."""
    admin_client = _make_admin_client(tmp_path, monkeypatch)
    cookies = _admin_login(admin_client)
    admin_client.cookies = cookies
    csrf = _csrf_fuer_session(cookies)
    resp = admin_client.post(
        "/admin/produkte/2/aktion",
        data={
            "aktionspreis_chf": "12.00",
            "aktionstext": "Test",
            "aktion_von": "2026-12-31",
            "aktion_bis": "2026-01-01",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert resp.status_code == 400
    from app.database import get_db

    conn = get_db()
    row = conn.execute("SELECT aktionspreis_chf FROM produkte WHERE id = 2").fetchone()
    conn.close()
    assert row["aktionspreis_chf"] is None


def test_admin_aktion_ungueliges_datum_format_abgelehnt(tmp_path, monkeypatch):
    """F3: Ungültiges ISO-Datum in aktion_von muss HTTP 400 liefern."""
    admin_client = _make_admin_client(tmp_path, monkeypatch)
    cookies = _admin_login(admin_client)
    admin_client.cookies = cookies
    csrf = _csrf_fuer_session(cookies)
    resp = admin_client.post(
        "/admin/produkte/2/aktion",
        data={
            "aktionspreis_chf": "12.00",
            "aktionstext": "Test",
            "aktion_von": "notadate",
            "aktion_bis": "",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert resp.status_code == 400
