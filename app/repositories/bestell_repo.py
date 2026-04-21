import sqlite3

from app.models import KundeInput


def produktnamen_anreichern(conn: sqlite3.Connection, positionen: list[dict]) -> None:
    """Ergänzt jede Position in-place um den Produktnamen aus der DB."""
    for pos in positionen:
        row = conn.execute(
            "SELECT name FROM produkte WHERE id = ?", (pos["produkt_id"],)
        ).fetchone()
        pos["name"] = row["name"]


def kunde_anlegen(conn: sqlite3.Connection, kunde: KundeInput) -> int:
    cursor = conn.execute(
        "INSERT INTO kunden (vorname, nachname, email, telefon, "
        "strasse, hausnummer, plz, ort) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            kunde.vorname,
            kunde.nachname,
            kunde.email,
            kunde.telefon,
            kunde.strasse,
            kunde.hausnummer,
            kunde.plz,
            kunde.ort,
        ),
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
    rabattcode_id: int | None = None,
    rabattbetrag_chf: float = 0,
) -> int:
    cursor = conn.execute(
        "INSERT INTO bestellungen "
        "(kunde_id, zahlungsart, versandart, versandkosten_chf, "
        "total_chf, kommentar, stripe_session_id, rabattcode_id, rabattbetrag_chf) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            kunde_id,
            zahlungsart,
            versandart,
            versandkosten,
            total,
            kommentar,
            stripe_session_id,
            rabattcode_id,
            rabattbetrag_chf,
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
