"""Repository-Funktionen fuer Rabattcodes und Einloesungen."""

from __future__ import annotations

import sqlite3


class RabattcodeAufgebrauchtError(ValueError):
    """Das globale Einlöse-Limit (max_einloesungen) ist bereits erreicht.

    Erbt von ValueError, damit der Bestell-Router den Fehler wie andere
    fachliche Fehler als 400 an den Kunden zurückgibt (#168).
    """


class RabattcodeBereitsEingeloestError(ValueError):
    """Diese E-Mail hat den Code bereits eingelöst (UNIQUE-Kollision).

    Fängt den Race ab, in dem zwei parallele Requests derselben Mail beide
    ist_bereits_eingeloest passieren; erbt von ValueError für die 400-Antwort.
    """


def rabattcode_anlegen(
    conn: sqlite3.Connection,
    *,
    code: str,
    rabattart: str,
    rabattwert: float,
    gueltig_von: str,
    gueltig_bis: str,
    mindestbestellwert_chf: float | None = None,
    max_einloesungen: int | None = None,
) -> int:
    """Neuen Rabattcode anlegen. Gibt die ID zurueck."""
    cursor = conn.execute(
        "INSERT INTO rabattcodes "
        "(code, rabattart, rabattwert, gueltig_von, gueltig_bis, "
        "mindestbestellwert_chf, max_einloesungen) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            code.upper(),
            rabattart,
            rabattwert,
            gueltig_von,
            gueltig_bis,
            mindestbestellwert_chf,
            max_einloesungen,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def rabattcode_laden(conn: sqlite3.Connection, code_id: int) -> dict | None:
    """Rabattcode anhand der ID laden."""
    row = conn.execute("SELECT * FROM rabattcodes WHERE id = ?", (code_id,)).fetchone()
    return dict(row) if row else None


def rabattcode_laden_by_code(conn: sqlite3.Connection, code: str) -> dict | None:
    """Rabattcode anhand des Code-Strings laden (case-insensitive)."""
    row = conn.execute(
        "SELECT * FROM rabattcodes WHERE code = ?", (code.upper(),)
    ).fetchone()
    return dict(row) if row else None


def alle_rabattcodes(conn: sqlite3.Connection) -> list[dict]:
    """Alle Rabattcodes laden."""
    rows = conn.execute(
        "SELECT * FROM rabattcodes ORDER BY erstellt_am DESC"
    ).fetchall()
    return [dict(r) for r in rows]


# Spalten, die ueber rabattcode_aktualisieren() geschrieben werden duerfen.
# Verhindert SQL-Injection ueber Feldnamen (dynamische SET-Klausel).
_AKTUALISIERBARE_FELDER = frozenset(
    {
        "code",
        "rabattart",
        "rabattwert",
        "gueltig_von",
        "gueltig_bis",
        "mindestbestellwert_chf",
        "max_einloesungen",
        "aktiv",
    }
)


def rabattcode_aktualisieren(conn: sqlite3.Connection, code_id: int, **felder) -> None:
    """Rabattcode-Felder aktualisieren.

    Nur Spalten aus _AKTUALISIERBARE_FELDER sind erlaubt; ein unbekannter
    Feldname loest einen ValueError aus (Schutz vor SQL-Injection ueber
    dynamisch zusammengesetzte Spaltennamen).
    """
    if not felder:
        return
    unbekannt = set(felder) - _AKTUALISIERBARE_FELDER
    if unbekannt:
        raise ValueError(f"Unerlaubte Rabattcode-Felder: {sorted(unbekannt)}")
    set_clause = ", ".join(f"{k} = ?" for k in felder)
    values = list(felder.values()) + [code_id]
    # S608 ok: Spaltennamen oben whitelisted, Werte parametrisiert via ?
    conn.execute(
        f"UPDATE rabattcodes SET {set_clause} WHERE id = ?",  # noqa: S608
        values,
    )
    conn.commit()


def einloesung_speichern(
    conn: sqlite3.Connection,
    *,
    rabattcode_id: int,
    email: str,
    bestellung_id: int,
) -> None:
    """Einlösung atomar buchen: Increment und Limit-Check in einem Statement.

    Das bedingte UPDATE inkrementiert nur, solange ``aktuelle_einloesungen <
    max_einloesungen`` (oder kein Limit gesetzt ist). Trifft eine parallele
    Einlösung zwischen ``pruefe_rabattcode`` und hier ein, greift ``rowcount
    == 0`` und der Code wird nicht überbucht (#168). Wirft dann
    ``RabattcodeAufgebrauchtError`` — der Aufrufer rollt die Transaktion zurück.

    Kein commit: Teil der Bestell-Transaktion des Aufrufers (#169).
    """
    cursor = conn.execute(
        "UPDATE rabattcodes SET aktuelle_einloesungen = aktuelle_einloesungen + 1 "
        "WHERE id = ? "
        "AND (max_einloesungen IS NULL OR aktuelle_einloesungen < max_einloesungen)",
        (rabattcode_id,),
    )
    if cursor.rowcount == 0:
        raise RabattcodeAufgebrauchtError("Rabattcode ist aufgebraucht.")

    try:
        conn.execute(
            "INSERT INTO code_einloesungen (rabattcode_id, email, bestellung_id) "
            "VALUES (?, ?, ?)",
            (rabattcode_id, email.lower().strip(), bestellung_id),
        )
    except sqlite3.IntegrityError as err:
        # Per-Mail-UNIQUE-Kollision (Race): fachlicher Fehler statt roher
        # IntegrityError, damit der Router 400 statt 500 liefert (#168).
        raise RabattcodeBereitsEingeloestError(
            "Du hast diesen Code bereits eingelöst."
        ) from err


def ist_bereits_eingeloest(
    conn: sqlite3.Connection, rabattcode_id: int, email: str
) -> bool:
    """Pruefen ob eine E-Mail diesen Code bereits eingeloest hat."""
    row = conn.execute(
        "SELECT 1 FROM code_einloesungen WHERE rabattcode_id = ? AND email = ?",
        (rabattcode_id, email.lower().strip()),
    ).fetchone()
    return row is not None
