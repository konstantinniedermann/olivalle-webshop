import sqlite3

from app.models import KundeInput


def kunde_anlegen(conn: sqlite3.Connection, kunde: KundeInput) -> int:
    cursor = conn.execute(
        "INSERT INTO kunden (vorname, nachname, email, telefon, strasse, plz, ort) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (kunde.vorname, kunde.nachname, kunde.email, kunde.telefon,
         kunde.strasse, kunde.plz, kunde.ort),
    )
    conn.commit()
    return cursor.lastrowid


def bestellung_anlegen(
    conn: sqlite3.Connection,
    *,
    kunde_id: int,
    positionen: list[dict],
    zahlungsart: str,
    versandart: str,
    versandkosten: float,
    total: float,
    kommentar: str = "",
    stripe_session_id: str | None = None,
) -> int:
    cursor = conn.execute(
        "INSERT INTO bestellungen "
        "(kunde_id, zahlungsart, versandart, versandkosten_chf, "
        "total_chf, kommentar, stripe_session_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            kunde_id,
            zahlungsart,
            versandart,
            versandkosten,
            total,
            kommentar,
            stripe_session_id,
        ),
    )
    bestell_id = cursor.lastrowid
    for pos in positionen:
        conn.execute(
            "INSERT INTO bestellpositionen "
            "(bestellung_id, produkt_id, menge, einzelpreis_chf) "
            "VALUES (?, ?, ?, ?)",
            (
                bestell_id,
                pos["produkt_id"],
                pos["menge"],
                pos["einzelpreis_chf"],
            ),
        )
    conn.commit()
    return bestell_id
