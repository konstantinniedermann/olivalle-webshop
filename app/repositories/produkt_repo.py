import sqlite3

from app.models import Produkt


def get_alle_produkte(conn: sqlite3.Connection) -> list[Produkt]:
    rows = conn.execute(
        "SELECT id, name, menge_ml, preis_chf, beschreibung, bild_pfad, aktiv, "
        "aktionspreis_chf, aktionstext, aktion_von, aktion_bis "
        "FROM produkte WHERE aktiv = 1 ORDER BY menge_ml"
    ).fetchall()
    return [Produkt(**dict(row)) for row in rows]


def alle_produkte_admin(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, name, menge_ml, preis_chf, beschreibung, bild_pfad, aktiv, "
        "aktionspreis_chf, aktionstext, aktion_von, aktion_bis "
        "FROM produkte ORDER BY menge_ml"
    ).fetchall()
    return [dict(row) for row in rows]


def produkt_laden(conn: sqlite3.Connection, produkt_id: int) -> dict | None:
    row = conn.execute(
        "SELECT id, name, menge_ml, preis_chf, beschreibung, bild_pfad, aktiv, "
        "aktionspreis_chf, aktionstext, aktion_von, aktion_bis "
        "FROM produkte WHERE id = ?",
        (produkt_id,),
    ).fetchone()
    return dict(row) if row else None


def aktion_setzen(
    conn: sqlite3.Connection,
    produkt_id: int,
    *,
    aktionspreis_chf: float,
    aktionstext: str,
    aktion_von: str | None,
    aktion_bis: str | None,
) -> None:
    conn.execute(
        "UPDATE produkte SET aktionspreis_chf = ?, aktionstext = ?, "
        "aktion_von = ?, aktion_bis = ? WHERE id = ?",
        (
            aktionspreis_chf,
            aktionstext,
            aktion_von or None,
            aktion_bis or None,
            produkt_id,
        ),
    )
    conn.commit()


def aktion_entfernen(conn: sqlite3.Connection, produkt_id: int) -> None:
    conn.execute(
        "UPDATE produkte SET aktionspreis_chf = NULL, aktionstext = NULL, "
        "aktion_von = NULL, aktion_bis = NULL WHERE id = ?",
        (produkt_id,),
    )
    conn.commit()
