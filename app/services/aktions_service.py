"""Zentrale Logik für produktbezogene Aktionspreise (Issue #134).

Einzige Stelle, die entscheidet, ob und welcher Aktionspreis zu einem
gegebenen Datum gilt. Rein funktional, ohne DB-Zugriff.
"""

from __future__ import annotations

from datetime import date
from typing import NamedTuple


class EffektivPreis(NamedTuple):
    preis: float
    ist_aktion: bool
    original_preis: float
    prozent: int


def _aktion_aktiv(
    aktionspreis_chf: float | None,
    aktion_von: str | None,
    aktion_bis: str | None,
    heute: date,
) -> bool:
    if aktionspreis_chf is None:
        return False
    h = heute.isoformat()
    if aktion_von and h < aktion_von:
        return False
    return not (aktion_bis and h > aktion_bis)


def effektiver_preis(
    preis_chf: float,
    aktionspreis_chf: float | None,
    aktion_von: str | None,
    aktion_bis: str | None,
    heute: date,
) -> EffektivPreis:
    """Liefert den gültigen Preis samt Aktions-Metadaten für ein Datum."""
    if _aktion_aktiv(aktionspreis_chf, aktion_von, aktion_bis, heute):
        prozent = round((1 - aktionspreis_chf / preis_chf) * 100)
        return EffektivPreis(
            preis=aktionspreis_chf,
            ist_aktion=True,
            original_preis=preis_chf,
            prozent=prozent,
        )
    return EffektivPreis(
        preis=preis_chf,
        ist_aktion=False,
        original_preis=preis_chf,
        prozent=0,
    )
