from datetime import date

from app.services.aktions_service import effektiver_preis

HEUTE = date(2026, 6, 23)


def test_keine_aktion_wenn_aktionspreis_none():
    ep = effektiver_preis(18.0, None, None, None, HEUTE)
    assert ep.ist_aktion is False
    assert ep.preis == 18.0
    assert ep.original_preis == 18.0
    assert ep.prozent == 0


def test_aktion_ohne_datumsgrenzen_gilt():
    ep = effektiver_preis(18.0, 12.0, None, None, HEUTE)
    assert ep.ist_aktion is True
    assert ep.preis == 12.0
    assert ep.original_preis == 18.0
    assert ep.prozent == 33  # round((1-12/18)*100) = 33


def test_aktion_vor_beginn_inaktiv():
    ep = effektiver_preis(18.0, 12.0, "2026-07-01", None, HEUTE)
    assert ep.ist_aktion is False
    assert ep.preis == 18.0


def test_aktion_nach_ende_inaktiv():
    ep = effektiver_preis(18.0, 12.0, None, "2026-06-22", HEUTE)
    assert ep.ist_aktion is False
    assert ep.preis == 18.0


def test_aktion_innerhalb_zeitraum_aktiv():
    ep = effektiver_preis(18.0, 12.0, "2026-06-01", "2026-06-30", HEUTE)
    assert ep.ist_aktion is True
    assert ep.preis == 12.0


def test_aktion_grenze_von_inklusive():
    ep = effektiver_preis(18.0, 12.0, "2026-06-23", "2026-06-30", HEUTE)
    assert ep.ist_aktion is True


def test_aktion_grenze_bis_inklusive():
    ep = effektiver_preis(18.0, 12.0, "2026-06-01", "2026-06-23", HEUTE)
    assert ep.ist_aktion is True


def test_leere_strings_wie_none_behandelt():
    ep = effektiver_preis(18.0, 12.0, "", "", HEUTE)
    assert ep.ist_aktion is True
