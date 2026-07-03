import sqlite3
from datetime import date

from app.models import WarenkorbItem
from app.services.aktions_service import effektiver_preis

# Single Source of Truth für Versandkosten (Issue #167).
# Templates erhalten diese Werte via app/templating.py (env.globals),
# cart.js via data-Attribute in base.html.
VERSANDKOSTEN_CHF = 9.90
GRATIS_AB_CHF = 100


def berechne_versandkosten(warenwert: float, versandart: str = "versand") -> float:
    if versandart == "abholung":
        return 0.0
    return 0.0 if warenwert >= GRATIS_AB_CHF else VERSANDKOSTEN_CHF


def berechne_total(
    conn: sqlite3.Connection,
    items: list[WarenkorbItem],
    heute: date | None = None,
) -> tuple[float, list[dict]]:
    """Validiert Items gegen DB und berechnet Total mit Effektiv-Preis.

    Returns: (total, positionen) wobei jede Position
    {"produkt_id", "menge", "einzelpreis_chf", "ist_aktion",
     "original_preis_chf"} enthält.
    """
    if heute is None:
        heute = date.today()
    positionen = []
    total = 0.0
    for item in items:
        row = conn.execute(
            "SELECT id, preis_chf, aktionspreis_chf, aktion_von, aktion_bis "
            "FROM produkte WHERE id = ? AND aktiv = 1",
            (item.produkt_id,),
        ).fetchone()
        if not row:
            raise ValueError(f"Produkt {item.produkt_id} nicht gefunden")
        ep = effektiver_preis(
            row["preis_chf"],
            row["aktionspreis_chf"],
            row["aktion_von"],
            row["aktion_bis"],
            heute,
        )
        positionen.append(
            {
                "produkt_id": item.produkt_id,
                "menge": item.menge,
                "einzelpreis_chf": ep.preis,
                "ist_aktion": ep.ist_aktion,
                "original_preis_chf": ep.original_preis,
            }
        )
        total += ep.preis * item.menge
    return total, positionen


def rabattfaehiger_subtotal(positionen: list[dict]) -> float:
    """Summe der Nicht-Aktions-Positionen — Basis für Rabattcodes."""
    return sum(
        p["einzelpreis_chf"] * p["menge"] for p in positionen if not p["ist_aktion"]
    )
