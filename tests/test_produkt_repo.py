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
