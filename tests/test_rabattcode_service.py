import pytest

from app.repositories.rabattcode_repo import (
    RabattcodeAufgebrauchtError,
    einloesung_speichern,
    ist_bereits_eingeloest,
    rabattcode_anlegen,
    rabattcode_laden,
    rabattcode_laden_by_code,
)
from app.services.rabattcode_service import berechne_rabatt, pruefe_rabattcode


def _kunde_und_bestellung(db, *, kunde_id, email, bestell_id):
    db.execute(
        "INSERT INTO kunden (id, vorname, nachname, email, strasse, plz, ort) "
        "VALUES (?, 'A', 'B', ?, 'Str 1', '4600', 'Olten')",
        (kunde_id, email),
    )
    db.execute(
        "INSERT INTO bestellungen "
        "(id, kunde_id, zahlungsart, versandart, versandkosten_chf, total_chf) "
        "VALUES (?, ?, 'stripe', 'versand', 0, 50)",
        (bestell_id, kunde_id),
    )


# --- Migration Tests ---


def test_rabattcodes_tabelle_existiert(db):
    db.execute(
        "INSERT INTO rabattcodes "
        "(code, rabattart, rabattwert, gueltig_von, gueltig_bis) "
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
        "INSERT INTO rabattcodes "
        "(code, rabattart, rabattwert, gueltig_von, gueltig_bis) "
        "VALUES ('TEST5', 'fixbetrag', 5.0, '2026-01-01', '2026-12-31')"
    )
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('Test', 'User', 'test@example.com', 'Teststr. 1', '4600', 'Olten')"
    )
    db.execute(
        "INSERT INTO bestellungen "
        "(kunde_id, zahlungsart, versandart, versandkosten_chf, total_chf) "
        "VALUES (1, 'stripe', 'versand', 9.90, 25.90)"
    )
    db.commit()
    db.execute(
        "INSERT INTO code_einloesungen (rabattcode_id, email, bestellung_id) "
        "VALUES (1, 'test@example.com', 1)"
    )
    db.commit()
    row = db.execute(
        "SELECT * FROM code_einloesungen WHERE email = 'test@example.com'"
    ).fetchone()
    assert row is not None


def test_bestellungen_hat_rabattfelder(db):
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('Test', 'User', 'test@example.com', 'Teststr. 1', '4600', 'Olten')"
    )
    db.execute(
        "INSERT INTO bestellungen "
        "(kunde_id, zahlungsart, versandart, versandkosten_chf, "
        "total_chf, rabattcode_id, rabattbetrag_chf) "
        "VALUES (1, 'stripe', 'versand', 9.90, 20.90, NULL, 5.00)"
    )
    db.commit()
    row = db.execute(
        "SELECT rabattbetrag_chf FROM bestellungen WHERE id = 1"
    ).fetchone()
    assert row["rabattbetrag_chf"] == 5.00


# --- Repository Tests ---


def test_rabattcode_anlegen_und_laden(db):
    code_id = rabattcode_anlegen(
        db,
        code="SOMMER20",
        rabattart="prozent",
        rabattwert=20.0,
        gueltig_von="2026-06-01",
        gueltig_bis="2026-08-31",
    )
    assert code_id > 0
    loaded = rabattcode_laden(db, code_id)
    assert loaded["code"] == "SOMMER20"
    assert loaded["rabattwert"] == 20.0


def test_rabattcode_laden_by_code(db):
    rabattcode_anlegen(
        db,
        code="HERBST5",
        rabattart="fixbetrag",
        rabattwert=5.0,
        gueltig_von="2026-09-01",
        gueltig_bis="2026-11-30",
    )
    loaded = rabattcode_laden_by_code(db, "herbst5")
    assert loaded is not None
    assert loaded["code"] == "HERBST5"


def test_einloesung_speichern_und_pruefen(db):
    code_id = rabattcode_anlegen(
        db,
        code="EINMAL",
        rabattart="fixbetrag",
        rabattwert=5.0,
        gueltig_von="2026-01-01",
        gueltig_bis="2026-12-31",
    )
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('A', 'B', 'a@b.ch', 'Str. 1', '4600', 'Olten')"
    )
    db.execute(
        "INSERT INTO bestellungen "
        "(kunde_id, zahlungsart, versandart, versandkosten_chf, total_chf) "
        "VALUES (1, 'stripe', 'versand', 0, 50)"
    )
    db.commit()
    assert ist_bereits_eingeloest(db, code_id, "a@b.ch") is False
    einloesung_speichern(db, rabattcode_id=code_id, email="a@b.ch", bestellung_id=1)
    assert ist_bereits_eingeloest(db, code_id, "a@b.ch") is True
    loaded = rabattcode_laden(db, code_id)
    assert loaded["aktuelle_einloesungen"] == 1


def test_einloesung_unter_limit_bucht(db):
    """Unter dem Limit: bedingtes Increment greift, Einlösung wird protokolliert."""
    code_id = rabattcode_anlegen(
        db,
        code="ZWEI",
        rabattart="fixbetrag",
        rabattwert=5.0,
        gueltig_von="2026-01-01",
        gueltig_bis="2026-12-31",
        max_einloesungen=2,
    )
    _kunde_und_bestellung(db, kunde_id=1, email="a@b.ch", bestell_id=1)
    db.commit()
    einloesung_speichern(db, rabattcode_id=code_id, email="a@b.ch", bestellung_id=1)
    assert rabattcode_laden(db, code_id)["aktuelle_einloesungen"] == 1
    assert ist_bereits_eingeloest(db, code_id, "a@b.ch") is True


def test_globales_limit_ueber_verschiedene_mails(db):
    """#168: max_einloesungen greift atomar auch über verschiedene E-Mails.

    Die per-E-Mail-UNIQUE-Grenze würde die zweite (andere) Mail durchlassen —
    das bedingte UPDATE deckelt das globale Limit trotzdem hart.
    """
    code_id = rabattcode_anlegen(
        db,
        code="EINS",
        rabattart="fixbetrag",
        rabattwert=5.0,
        gueltig_von="2026-01-01",
        gueltig_bis="2026-12-31",
        max_einloesungen=1,
    )
    _kunde_und_bestellung(db, kunde_id=1, email="a@b.ch", bestell_id=1)
    _kunde_und_bestellung(db, kunde_id=2, email="c@d.ch", bestell_id=2)
    db.commit()

    einloesung_speichern(db, rabattcode_id=code_id, email="a@b.ch", bestellung_id=1)
    assert rabattcode_laden(db, code_id)["aktuelle_einloesungen"] == 1

    # Zweite Mail über dem Limit: hart abgelehnt, kein Overshoot
    with pytest.raises(RabattcodeAufgebrauchtError):
        einloesung_speichern(db, rabattcode_id=code_id, email="c@d.ch", bestellung_id=2)
    assert rabattcode_laden(db, code_id)["aktuelle_einloesungen"] == 1
    assert ist_bereits_eingeloest(db, code_id, "c@d.ch") is False


# --- Service Tests ---


def test_berechne_rabatt_prozent():
    assert berechne_rabatt("prozent", 10.0, 26.00) == 2.60


def test_berechne_rabatt_prozent_5rappen_rundung():
    assert berechne_rabatt("prozent", 7.0, 18.00) == 1.25


def test_berechne_rabatt_fixbetrag():
    assert berechne_rabatt("fixbetrag", 5.0, 26.00) == 5.00


def test_berechne_rabatt_fixbetrag_nicht_mehr_als_subtotal():
    assert berechne_rabatt("fixbetrag", 50.0, 26.00) == 26.00


def test_berechne_rabatt_prozent_5rappen_weitere():
    assert berechne_rabatt("prozent", 15.0, 8.00) == 1.20
    assert berechne_rabatt("prozent", 10.0, 9.90) == 1.00
    assert berechne_rabatt("prozent", 3.0, 7.00) == 0.20


# Helper functions for pruefe_rabattcode tests
def _erstelle_testcode(db, **overrides):
    defaults = {
        "code": "TEST10",
        "rabattart": "prozent",
        "rabattwert": 10.0,
        "gueltig_von": "2026-01-01",
        "gueltig_bis": "2026-12-31",
    }
    defaults.update(overrides)
    return rabattcode_anlegen(db, **defaults)


def _erstelle_testbestellung(db):
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('A', 'B', 'a@b.ch', 'Str. 1', '4600', 'Olten')"
    )
    db.execute(
        "INSERT INTO bestellungen "
        "(kunde_id, zahlungsart, versandart, versandkosten_chf, total_chf) "
        "VALUES (1, 'stripe', 'versand', 0, 50)"
    )
    db.commit()


def test_pruefe_rabattcode_gueltig(db):
    _erstelle_testcode(db)
    result = pruefe_rabattcode(db, "TEST10", "kunde@test.ch", 26.00)
    assert result["gueltig"] is True
    assert result["rabattbetrag"] == 2.60


def test_pruefe_rabattcode_unbekannt(db):
    result = pruefe_rabattcode(db, "GIBTSNICHT", "kunde@test.ch", 26.00)
    assert result["gueltig"] is False


def test_pruefe_rabattcode_deaktiviert(db):
    code_id = _erstelle_testcode(db)
    db.execute("UPDATE rabattcodes SET aktiv = 0 WHERE id = ?", (code_id,))
    db.commit()
    result = pruefe_rabattcode(db, "TEST10", "kunde@test.ch", 26.00)
    assert result["gueltig"] is False


def test_pruefe_rabattcode_abgelaufen(db):
    _erstelle_testcode(db, gueltig_von="2025-01-01", gueltig_bis="2025-12-31")
    result = pruefe_rabattcode(db, "TEST10", "kunde@test.ch", 26.00)
    assert result["gueltig"] is False
    assert "abgelaufen" in result["fehler"].lower()


def test_pruefe_rabattcode_noch_nicht_gueltig(db):
    _erstelle_testcode(db, gueltig_von="2027-01-01", gueltig_bis="2027-12-31")
    result = pruefe_rabattcode(db, "TEST10", "kunde@test.ch", 26.00)
    assert result["gueltig"] is False


def test_pruefe_rabattcode_max_einloesungen_erreicht(db):
    _erstelle_testcode(db, max_einloesungen=1)
    db.execute("UPDATE rabattcodes SET aktuelle_einloesungen = 1 WHERE code = 'TEST10'")
    db.commit()
    result = pruefe_rabattcode(db, "TEST10", "kunde@test.ch", 26.00)
    assert result["gueltig"] is False
    assert "aufgebraucht" in result["fehler"].lower()


def test_pruefe_rabattcode_bereits_eingeloest(db):
    code_id = _erstelle_testcode(db)
    _erstelle_testbestellung(db)
    einloesung_speichern(db, rabattcode_id=code_id, email="a@b.ch", bestellung_id=1)
    result = pruefe_rabattcode(db, "TEST10", "a@b.ch", 26.00)
    assert result["gueltig"] is False
    assert "bereits" in result["fehler"].lower()


def test_pruefe_rabattcode_mindestbestellwert_nicht_erreicht(db):
    _erstelle_testcode(db, mindestbestellwert_chf=50.0)
    result = pruefe_rabattcode(db, "TEST10", "kunde@test.ch", 26.00)
    assert result["gueltig"] is False
    assert "mindestbestellwert" in result["fehler"].lower()


def test_pruefe_rabattcode_mindestbestellwert_erreicht(db):
    _erstelle_testcode(db, mindestbestellwert_chf=25.0)
    result = pruefe_rabattcode(db, "TEST10", "kunde@test.ch", 26.00)
    assert result["gueltig"] is True
