"""Die Vorlagen unter templates/neu/ halten sich an docs/designleitbild.md.

Gestaltet wird über die Bausteine (`ol-…` in static/css/input.css). Dieser Test
schlägt an, wenn eine Vorlage daran vorbei eigene Grössen, Radien, Schatten
oder Knöpfe einführt.
"""

import re
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parent.parent
VORLAGEN = sorted((WURZEL / "templates" / "neu").glob("*.html"))
QUELLEN = [*VORLAGEN, WURZEL / "static" / "js" / "neu.js"]

# Was das Leitbild nicht kennt — Bausteine verwenden statt Einzelwerte.
VERBOTEN = {
    "Schriftgrösse (ol-display/ol-h1/ol-h2/ol-h3/ol-lead verwenden)": (
        r"(?<![\w-])(?:sm:|md:|lg:)?text-(?:lg|xl|[2-9]xl)\b"
    ),
    "Schrift (Titel nur über ol-h*, ol-preis)": r"\bfont-titel\b",
    "Fett/Kursiv (nur normal und font-medium)": (
        r"\bfont-(?:bold|semibold|extrabold)\b|\bitalic\b"
    ),
    "Radius (nur rounded-full, rounded-3xl, rounded-xl)": (
        r"\brounded-(?:sm|md|lg|2xl|\[)|\brounded\b(?!-)"
    ),
    "Schatten (nur ol-schwebend)": r"(?<![\w-])shadow-",
    "Textton (nur Hain, /70, /50)": r"\btext-hain/(?!70\b|50\b)\d+",
    "Knopf von Hand (ol-btn verwenden)": r"\bbg-hain\b[^\"]*\btext-creme\b",
    "Ölgold als Fläche": r"\bbg-oel\b",
}


@pytest.mark.parametrize("quelle", QUELLEN, ids=lambda p: p.name)
@pytest.mark.parametrize("regel", VERBOTEN, ids=lambda r: r.split(" (")[0])
def test_vorlage_haelt_leitbild_ein(quelle, regel):
    text = quelle.read_text(encoding="utf-8")
    # Jinja-Kommentare beschreiben nur
    text = re.sub(r"\{#.*?#\}", "", text, flags=re.S)
    treffer = re.findall(VERBOTEN[regel], text)
    assert treffer == [], f"{quelle.name}: {regel}"


def test_jede_seite_hat_genau_einen_seitentitel(client):
    for pfad in [
        "/neu",
        "/neu/ueber-das-oel",
        "/neu/warenkorb",
        "/neu/checkout",
        "/neu/bestaetigung",
        "/neu/impressum",
        "/neu/datenschutz",
        "/neu/agb",
    ]:
        assert len(re.findall(r"<h1\b", client.get(pfad).text)) == 1, pfad


def test_alle_knoepfe_sind_bausteine(client):
    """Jedes <button> ist ol-btn, ol-icon-btn oder Teil der Mengenwahl."""
    for pfad in ["/neu", "/neu/warenkorb", "/neu/checkout"]:
        html = client.get(pfad).text
        html = re.sub(r'<div class="ol-stepper">.*?</div>', "", html, flags=re.S)
        for button in re.findall(r"<button\b[^>]*>", html):
            assert re.search(r"\bol-(?:btn|icon-btn)\b", button), (pfad, button)
