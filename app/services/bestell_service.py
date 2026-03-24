import sqlite3

from app.models import WarenkorbItem


def berechne_versandkosten(
    warenwert: float, versandart: str = "versand"
) -> float:
    if versandart == "abholung":
        return 0.0
    return 0.0 if warenwert >= 100 else 9.90


def berechne_total(
    conn: sqlite3.Connection, items: list[WarenkorbItem]
) -> tuple[float, list[dict]]:
    """Validiert Items gegen DB und berechnet Total.

    Returns: (total, positionen) wobei positionen eine Liste von
    {"produkt_id", "menge", "einzelpreis_chf"} ist.
    """
    positionen = []
    total = 0.0
    for item in items:
        row = conn.execute(
            "SELECT id, preis_chf FROM produkte WHERE id = ? AND aktiv = 1",
            (item.produkt_id,),
        ).fetchone()
        if not row:
            raise ValueError(f"Produkt {item.produkt_id} nicht gefunden")
        preis = row["preis_chf"]
        positionen.append(
            {
                "produkt_id": item.produkt_id,
                "menge": item.menge,
                "einzelpreis_chf": preis,
            }
        )
        total += preis * item.menge
    return total, positionen
