def test_produkte_hat_aktions_spalten(db):
    cols = {row[1] for row in db.execute("PRAGMA table_info(produkte)")}
    assert {"aktionspreis_chf", "aktionstext", "aktion_von", "aktion_bis"} <= cols
