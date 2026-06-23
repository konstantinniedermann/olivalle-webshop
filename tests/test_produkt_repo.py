from app.repositories.produkt_repo import get_alle_produkte


def test_get_alle_produkte(db):
    produkte = get_alle_produkte(db)
    assert len(produkte) == 3
    assert produkte[0].name == "Olivenöl 250ml"


def test_get_alle_produkte_nur_aktive(db):
    db.execute("UPDATE produkte SET aktiv = 0 WHERE id = 1")
    db.commit()
    produkte = get_alle_produkte(db)
    assert len(produkte) == 2


def test_get_alle_produkte_liefert_aktions_felder(db):
    from app.repositories.produkt_repo import get_alle_produkte

    db.execute(
        "UPDATE produkte SET aktionspreis_chf = 12.0, aktionstext = 'MHD 09/2026', "
        "aktion_von = '2026-06-01', aktion_bis = '2026-06-30' WHERE id = 2"
    )
    db.commit()
    produkte = get_alle_produkte(db)
    p2 = next(p for p in produkte if p.id == 2)
    assert p2.aktionspreis_chf == 12.0
    assert p2.aktionstext == "MHD 09/2026"
    assert p2.aktion_von == "2026-06-01"
    assert p2.aktion_bis == "2026-06-30"


def test_get_alle_produkte_ohne_aktion_felder_none(db):
    from app.repositories.produkt_repo import get_alle_produkte

    produkte = get_alle_produkte(db)
    p1 = next(p for p in produkte if p.id == 1)
    assert p1.aktionspreis_chf is None


def test_aktion_setzen_und_laden(db):
    from app.repositories.produkt_repo import aktion_setzen, produkt_laden

    aktion_setzen(
        db, 2, aktionspreis_chf=12.0, aktionstext="MHD 09/2026",
        aktion_von="2026-06-01", aktion_bis="2026-06-30",
    )
    p = produkt_laden(db, 2)
    assert p["aktionspreis_chf"] == 12.0
    assert p["aktionstext"] == "MHD 09/2026"
    assert p["aktion_von"] == "2026-06-01"
    assert p["aktion_bis"] == "2026-06-30"


def test_aktion_entfernen_setzt_null(db):
    from app.repositories.produkt_repo import (
        aktion_entfernen,
        aktion_setzen,
        produkt_laden,
    )

    aktion_setzen(db, 2, aktionspreis_chf=12.0, aktionstext="x",
                  aktion_von=None, aktion_bis=None)
    aktion_entfernen(db, 2)
    p = produkt_laden(db, 2)
    assert p["aktionspreis_chf"] is None
    assert p["aktionstext"] is None
    assert p["aktion_von"] is None
    assert p["aktion_bis"] is None


def test_alle_produkte_admin_enthaelt_alle(db):
    from app.repositories.produkt_repo import alle_produkte_admin

    produkte = alle_produkte_admin(db)
    assert len(produkte) == 3
    assert produkte[0]["menge_ml"] <= produkte[-1]["menge_ml"]
