import sqlite3

from app.models import Produkt


def get_alle_produkte(conn: sqlite3.Connection) -> list[Produkt]:
    rows = conn.execute(
        "SELECT id, name, menge_ml, preis_chf, beschreibung, bild_pfad, aktiv "
        "FROM produkte WHERE aktiv = 1 ORDER BY menge_ml"
    ).fetchall()
    return [Produkt(**dict(row)) for row in rows]
