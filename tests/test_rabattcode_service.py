

# --- Migration Tests ---


def test_rabattcodes_tabelle_existiert(db):
    db.execute(
        "INSERT INTO rabattcodes (code, rabattart, rabattwert, gueltig_von, gueltig_bis) "
        "VALUES ('TEST10', 'prozent', 10.0, '2026-01-01', '2026-12-31')"
    )
    db.commit()
    row = db.execute("SELECT * FROM rabattcodes WHERE code = 'TEST10'").fetchone()
    assert row is not None
    assert row["rabattart"] == "prozent"
    assert row["aktuelle_einloesungen"] == 0
    assert row["aktiv"] == 1


def test_code_einloesungen_tabelle_existiert(db):
    db.execute(
        "INSERT INTO rabattcodes (code, rabattart, rabattwert, gueltig_von, gueltig_bis) "
        "VALUES ('TEST5', 'fixbetrag', 5.0, '2026-01-01', '2026-12-31')"
    )
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('Test', 'User', 'test@example.com', 'Teststr. 1', '4600', 'Olten')"
    )
    db.execute(
        "INSERT INTO bestellungen (kunde_id, zahlungsart, versandart, versandkosten_chf, total_chf) "
        "VALUES (1, 'stripe', 'versand', 9.90, 25.90)"
    )
    db.commit()
    db.execute(
        "INSERT INTO code_einloesungen (rabattcode_id, email, bestellung_id) "
        "VALUES (1, 'test@example.com', 1)"
    )
    db.commit()
    row = db.execute("SELECT * FROM code_einloesungen WHERE email = 'test@example.com'").fetchone()
    assert row is not None


def test_bestellungen_hat_rabattfelder(db):
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('Test', 'User', 'test@example.com', 'Teststr. 1', '4600', 'Olten')"
    )
    db.execute(
        "INSERT INTO bestellungen (kunde_id, zahlungsart, versandart, versandkosten_chf, "
        "total_chf, rabattcode_id, rabattbetrag_chf) "
        "VALUES (1, 'stripe', 'versand', 9.90, 20.90, NULL, 5.00)"
    )
    db.commit()
    row = db.execute("SELECT rabattbetrag_chf FROM bestellungen WHERE id = 1").fetchone()
    assert row["rabattbetrag_chf"] == 5.00


# --- Repository Tests ---


from app.repositories.rabattcode_repo import (
    einloesung_speichern,
    ist_bereits_eingeloest,
    rabattcode_anlegen,
    rabattcode_laden,
    rabattcode_laden_by_code,
)


def test_rabattcode_anlegen_und_laden(db):
    code_id = rabattcode_anlegen(
        db, code="SOMMER20", rabattart="prozent", rabattwert=20.0,
        gueltig_von="2026-06-01", gueltig_bis="2026-08-31",
    )
    assert code_id > 0
    loaded = rabattcode_laden(db, code_id)
    assert loaded["code"] == "SOMMER20"
    assert loaded["rabattwert"] == 20.0


def test_rabattcode_laden_by_code(db):
    rabattcode_anlegen(
        db, code="HERBST5", rabattart="fixbetrag", rabattwert=5.0,
        gueltig_von="2026-09-01", gueltig_bis="2026-11-30",
    )
    loaded = rabattcode_laden_by_code(db, "herbst5")
    assert loaded is not None
    assert loaded["code"] == "HERBST5"


def test_einloesung_speichern_und_pruefen(db):
    code_id = rabattcode_anlegen(
        db, code="EINMAL", rabattart="fixbetrag", rabattwert=5.0,
        gueltig_von="2026-01-01", gueltig_bis="2026-12-31",
    )
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('A', 'B', 'a@b.ch', 'Str. 1', '4600', 'Olten')"
    )
    db.execute(
        "INSERT INTO bestellungen (kunde_id, zahlungsart, versandart, versandkosten_chf, total_chf) "
        "VALUES (1, 'stripe', 'versand', 0, 50)"
    )
    db.commit()
    assert ist_bereits_eingeloest(db, code_id, "a@b.ch") is False
    einloesung_speichern(db, rabattcode_id=code_id, email="a@b.ch", bestellung_id=1)
    assert ist_bereits_eingeloest(db, code_id, "a@b.ch") is True
    loaded = rabattcode_laden(db, code_id)
    assert loaded["aktuelle_einloesungen"] == 1
