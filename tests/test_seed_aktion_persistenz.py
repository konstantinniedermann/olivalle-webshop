"""Regressionsschutz: Der Produkt-Seed darf admin-gesetzte Aktionen nicht
bei jedem Neustart überschreiben (Bug #137, Fix zu #134).

init_db() läuft bei jedem Container-Start und führt den Seed erneut aus.
Mit INSERT OR REPLACE fielen die admin-editierbaren Aktions-Spalten dabei
auf NULL zurück — eine im Admin gesetzte Aktion verschwand stillschweigend
bei jedem Deploy/Maschinenneustart. Der Seed nutzt deshalb ein UPSERT, das
nur die Katalog-Spalten aktualisiert.
"""

import sqlite3

from app.database import init_db
from app.repositories.produkt_repo import aktion_setzen, produkt_laden


def test_seed_ueberschreibt_admin_aktion_nicht(monkeypatch, tmp_path):
    db_path = str(tmp_path / "olivalle-test.db")
    monkeypatch.setattr("app.config.settings.database_path", db_path)

    # Erster Boot: DB anlegen und seeden.
    init_db()

    # Inhaber setzt im Admin eine Aktion auf das 250ml-Produkt.
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    aktion_setzen(
        conn,
        1,
        aktionspreis_chf=6.0,
        aktionstext="Sommeraktion",
        aktion_von=None,
        aktion_bis=None,
    )
    conn.close()

    # Zweiter Boot (z. B. Deploy, fly.io-Neustart, Litestream-Restore).
    init_db()

    # Aktion muss den Neustart überleben.
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    produkt = produkt_laden(conn, 1)
    conn.close()

    assert produkt is not None
    assert produkt["aktionspreis_chf"] == 6.0
    assert produkt["aktionstext"] == "Sommeraktion"


def test_seed_aktualisiert_katalog_spalten_weiterhin(monkeypatch, tmp_path):
    """Gegenprobe: Katalog-Korrekturen per Migration greifen weiterhin bei
    jedem Boot (sonst wäre INSERT OR IGNORE gewählt worden)."""
    db_path = str(tmp_path / "olivalle-test.db")
    monkeypatch.setattr("app.config.settings.database_path", db_path)

    init_db()

    # Katalog-Spalte von Hand verfälschen, dann Neustart simulieren.
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE produkte SET preis_chf = 999 WHERE id = 1")
    conn.commit()
    conn.close()

    init_db()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    produkt = produkt_laden(conn, 1)
    conn.close()

    # Seed stellt den Katalog-Preis wieder her.
    assert produkt["preis_chf"] == 8.0
