class TestLogEintrag:
    def test_log_eintrag_schreiben(self, db):
        from app.repositories.admin_repo import log_eintrag_schreiben

        log_id = log_eintrag_schreiben(
            db,
            admin_label="dev",
            aktion="login",
            details="127.0.0.1",
        )
        assert log_id > 0
        row = db.execute("SELECT * FROM admin_log WHERE id = ?", (log_id,)).fetchone()
        assert row["admin_label"] == "dev"
        assert row["aktion"] == "login"
        assert row["details"] == "127.0.0.1"
        assert row["bestellung_id"] is None

    def test_log_eintrag_mit_bestellung(self, db):
        from app.repositories.admin_repo import log_eintrag_schreiben

        db.execute(
            "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
            "VALUES ('Max', 'Muster', 'max@test.ch', 'Str 1', '4600', 'Olten')"
        )
        db.execute(
            "INSERT INTO bestellungen (kunde_id, zahlungsart, versandart, total_chf) "
            "VALUES (1, 'stripe', 'versand', 50.00)"
        )
        db.commit()

        log_id = log_eintrag_schreiben(
            db,
            admin_label="owner",
            aktion="status_geaendert",
            details='{"von": "neu", "nach": "bezahlt"}',
            bestellung_id=1,
        )
        row = db.execute("SELECT * FROM admin_log WHERE id = ?", (log_id,)).fetchone()
        assert row["bestellung_id"] == 1


def _seed_bestellungen(db, count=3):
    """Seed-Daten: ein Kunde und mehrere Bestellungen."""
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('Max', 'Muster', 'max@test.ch', 'Str 1', '4600', 'Olten')"
    )
    stati = ["neu", "bezahlt", "versendet"]
    for i in range(count):
        db.execute(
            "INSERT INTO bestellungen "
            "(kunde_id, status, zahlungsart, versandart, total_chf, erstellt_am) "
            "VALUES (1, ?, 'stripe', 'versand', ?, datetime('now'))",
            (stati[i % len(stati)], 50.00 + i * 10),
        )
        db.execute(
            "INSERT INTO bestellpositionen "
            "(bestellung_id, produkt_id, menge, einzelpreis_chf) "
            "VALUES (?, 1, 2, 8.00)",
            (i + 1,),
        )
    db.commit()


class TestDashboardQueries:
    def test_get_dashboard_stats(self, db):
        from app.repositories.admin_repo import get_dashboard_stats

        _seed_bestellungen(db, 3)
        stats = get_dashboard_stats(db)
        assert stats["offene_bestellungen"] == 2  # neu + bezahlt
        assert stats["umsatz_monat"] > 0
        assert stats["bestellungen_heute"] == 3

    def test_get_bestellungen_liste(self, db):
        from app.repositories.admin_repo import get_bestellungen_liste

        _seed_bestellungen(db, 3)
        rows = get_bestellungen_liste(db)
        assert len(rows) == 3
        assert rows[0]["id"] >= rows[1]["id"]

    def test_get_bestellungen_liste_filter_status(self, db):
        from app.repositories.admin_repo import get_bestellungen_liste

        _seed_bestellungen(db, 3)
        rows = get_bestellungen_liste(db, status="neu")
        assert len(rows) == 1
        assert rows[0]["status"] == "neu"

    def test_get_bestellungen_liste_suche(self, db):
        from app.repositories.admin_repo import get_bestellungen_liste

        _seed_bestellungen(db, 3)
        rows = get_bestellungen_liste(db, suche="Muster")
        assert len(rows) == 3
        rows = get_bestellungen_liste(db, suche="gibts-nicht")
        assert len(rows) == 0


class TestBestellDetail:
    def test_get_bestellung_detail(self, db):
        from app.repositories.admin_repo import get_bestellung_detail

        _seed_bestellungen(db, 1)
        detail = get_bestellung_detail(db, 1)
        assert detail is not None
        assert detail["id"] == 1
        assert detail["vorname"] == "Max"
        assert len(detail["positionen"]) == 1

    def test_get_bestellung_detail_nicht_gefunden(self, db):
        from app.repositories.admin_repo import get_bestellung_detail

        assert get_bestellung_detail(db, 999) is None

    def test_update_status(self, db):
        from app.repositories.admin_repo import update_bestellung_status

        _seed_bestellungen(db, 1)
        update_bestellung_status(db, bestellung_id=1, neuer_status="versendet")
        row = db.execute("SELECT status FROM bestellungen WHERE id = 1").fetchone()
        assert row["status"] == "versendet"

    def test_get_log_fuer_bestellung(self, db):
        from app.repositories.admin_repo import (
            get_log_fuer_bestellung,
            log_eintrag_schreiben,
        )

        _seed_bestellungen(db, 1)
        log_eintrag_schreiben(
            db,
            admin_label="dev",
            aktion="notiz_hinzugefuegt",
            details="Testnotiz",
            bestellung_id=1,
        )
        logs = get_log_fuer_bestellung(db, 1)
        assert len(logs) == 1
        assert logs[0]["aktion"] == "notiz_hinzugefuegt"
