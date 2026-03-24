# Design: Produkttexte Olivalle

## Ziel

Produkttexte für den Olivalle Webshop erstellen und als Markdown-Datei im Repo ablegen. Die Texte dienen als Grundlage für die spätere Produktseite (Issue #15).

## Kontext

- Issue #38: Produkttexte und -bilder vom Stakeholder einholen
- Produktbilder sind bereits im Repo (`frontend/public/images/products/`)
- Texte sind der letzte offene Punkt (Bilder erledigt via Commit 05833b9)

## Entscheidungen

| Frage | Entscheidung |
|---|---|
| Stil/Ton | Warm & persönlich |
| Speicherort | `docs/produkttexte.md` (Markdown) |
| Umfang gemeinsamer Text | Mittel (1 Absatz, 5-8 Sätze) — 3 Varianten (kurz/mittel/ausführlich) für SH-Entscheid |
| Sprache | Hochdeutsch mit Schweizer Konvention (kein ß, immer ss; "Franken" statt "Euro") |

## Struktur der Datei

### 1. Gemeinsamer Text (3 Varianten)

Erzählt die Geschichte des Olivenöls:
- Bio Olivenöl extra virgen, Sorte Nevadillo Blanco
- Herkunft: Kooperative OLIPE, Sierra Morena bei Córdoba, Andalusien
- Gegründet 1957, 800 Bauernfamilien, 15'000 Hektar
- 12-24h von Ernte bis Pressung, hoher Polyphenolgehalt
- Generalimporteur in die Schweiz seit ~20 Jahren

**Variante A** — Kurz (3 Sätze): Fakten kompakt
**Variante B** — Mittel (6 Sätze): Default, erzählt die Geschichte ⭐
**Variante C** — Ausführlich (3 Absätze): Volle Geschichte mit Details zur Kooperative

### 2. Produktbeschreibungen (je 2-3 Sätze)

Die Produkte unterscheiden sich nur durch die Verpackung. Jede Beschreibung nennt Verwendungszweck und Zielgruppe:

- **250ml Flasche (CHF 8)** — Kennenlernen, Geschenk, Feinkostläden
- **750ml Flasche (CHF 18)** — Täglicher Gebrauch, Restaurants und Betriebe
- **3l Kanister (CHF 50)** — Vielbraucher, Gastronomiebetriebe, bestes Preis-Leistungs-Verhältnis

## Umsetzung

1. `docs/produkttexte.md` erstellen mit allen 3 Varianten + Produktbeschreibungen
2. Issue #38 schliessen mit Verweis auf den Commit
3. SH entscheidet später welche Variante verwendet wird (Default: B)

## Abhängigkeiten

- **Blocks:** #15 (Produktseite Frontend) — Texte werden dort ins Frontend übernommen
