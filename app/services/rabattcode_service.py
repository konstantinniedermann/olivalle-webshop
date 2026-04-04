"""Service fuer Rabattcode-Validierung und -Berechnung."""

from __future__ import annotations

import sqlite3
from datetime import date

from app.repositories.rabattcode_repo import (
    ist_bereits_eingeloest,
    rabattcode_laden_by_code,
)


def berechne_rabatt(rabattart: str, rabattwert: float, subtotal: float) -> float:
    """Rabattbetrag berechnen mit Schweizer 5-Rappen-Rundung."""
    if rabattart == "prozent":
        betrag = subtotal * rabattwert / 100
    else:
        betrag = min(rabattwert, subtotal)
    return round(betrag * 20) / 20


def pruefe_rabattcode(
    conn: sqlite3.Connection, code: str, email: str, subtotal: float
) -> dict:
    """Rabattcode validieren und Rabattbetrag berechnen.

    Gibt ein Dict zurueck:
    - Bei Fehler: {"gueltig": False, "fehler": "..."}
    - Bei Erfolg: {"gueltig": True, "rabattbetrag": float, ...}
    """
    rc = rabattcode_laden_by_code(conn, code)
    if not rc or not rc["aktiv"]:
        return {"gueltig": False, "fehler": "Rabattcode ungültig oder nicht gefunden."}

    heute = date.today().isoformat()
    if heute < rc["gueltig_von"]:
        return {"gueltig": False, "fehler": "Rabattcode ist noch nicht gültig."}
    if heute > rc["gueltig_bis"]:
        return {"gueltig": False, "fehler": "Rabattcode ist abgelaufen."}

    if (
        rc["max_einloesungen"] is not None
        and rc["aktuelle_einloesungen"] >= rc["max_einloesungen"]
    ):
        return {"gueltig": False, "fehler": "Rabattcode ist aufgebraucht."}

    if ist_bereits_eingeloest(conn, rc["id"], email):
        return {"gueltig": False, "fehler": "Du hast diesen Code bereits eingelöst."}

    if (
        rc["mindestbestellwert_chf"] is not None
        and subtotal < rc["mindestbestellwert_chf"]
    ):
        return {
            "gueltig": False,
            "fehler": f"Mindestbestellwert CHF {rc['mindestbestellwert_chf']:.2f} nicht erreicht.",
        }

    rabattbetrag = berechne_rabatt(rc["rabattart"], rc["rabattwert"], subtotal)
    return {
        "gueltig": True,
        "rabattbetrag": rabattbetrag,
        "rabattart": rc["rabattart"],
        "rabattwert": rc["rabattwert"],
        "rabattcode_id": rc["id"],
        "code": rc["code"],
    }
