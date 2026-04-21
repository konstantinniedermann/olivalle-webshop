# SH-Feedback: Textüberarbeitung Öl-Seite und Hintergrund Produktseite

## Kontext

Rückmeldung des Stakeholders (SH) nach erfolgreichen Smoke-Tests auf `olivalle.ch`:

1. Titel der Text-Kacheln auf `/ueber-das-oel` ohne bestimmten Artikel ("Die Herkunft" → "Herkunft").
2. Haupttexte der ersten vier Kacheln komplett überarbeitet — ausführlichere Darstellung, ausformulierter Genossenschaftsname, gendergerechte Sprache ("Produzierenden").
3. Hintergrund der Produktseite soll visuell zur Öl-Seite passen (Olivenbaum/Zweige statt Terracotta).

## Entscheidungen

| Frage | Entscheid | Begründung |
|---|---|---|
| Produktseiten-Hintergrund | `olive-tree-hero.jpg` (selbes Bild wie `ueber-das-oel`) | SH-Wortlaut "vom Stil her gleich"; kein neues Asset nötig; Karten mit `bg-stone-900/75` heben sich vom Hintergrund ab. |
| "Berghainen" | Bleibt stehen | Vom SH bewusst gewählt (Hain am Berg, analog Olivenhain). Kein Typo. |
| "jahrzentelang" | Stillschweigend zu "jahrzehntelang" korrigiert | Eindeutiger Typo. |
| Bio-Kontrollstelle-Zeile (OLIPE-Kachel) | Bleibt unverändert | Rechtlich relevante Deklaration (Art. 39 LIV / EU-VO), SH hat sie nicht aktiv entfernt. |
| Produktinformation-Kachel + CTA | Bleibt unverändert | Nicht Teil des SH-Feedbacks. |
| Tailwind-Rebuild | Nicht nötig | Hintergrund wird per Inline-`style`-Attribut gesetzt, nicht per `bg-[url(...)]`-Klasse. |
| Bindestrich-Stil | Geviertstrich `—` in Einschüben | Konsistent zum Rest des Templates. SH-Text nutzt teils `-`, wir harmonisieren auf `—`. |

## Änderungen

### 1. `templates/ueber-das-oel.html` — Vier Text-Kacheln aktualisieren

**Kachel 1 — Herkunft**

Titel: `Die Herkunft` → `Herkunft`

Neuer Text:

> Die Oliven der Sorte Nevadillo Blanco wachsen in den Berghainen der Sierra Morena bei Córdoba. Die Region ist geprägt von heissen Sommern, milden Wintern und kargen Böden — ideale Bedingungen für aromatische Oliven mit hohem Ölgehalt. Die Bäume stehen oft an steilen Hängen, wo maschinelle Ernte unmöglich ist. Hier wird seit Generationen von Hand gearbeitet und geerntet.

*(Bindestrich nach "Böden" als Geviertstrich `—` gesetzt, wie im Rest der Seite.)*

**Kachel 2 — Kooperative OLIPE**

Titel: `Die Kooperative OLIPE` → `Kooperative OLIPE`

Neuer Text (Bindestriche konsistent als Geviertstrich `—`; "jahrzentelang" → "jahrzehntelang"):

> Seit 1957 arbeiten rund 800 Bauernfamilien gemeinsam im Namen der Kooperative Olivarera Los Pedroches (OLIPE). Die Kooperative garantiert faire Preise für die Produzierenden und kontrolliert die gesamte Kette von der Ernte bis zur Abfüllung des Öls. Bio-Zertifizierung und Nachhaltigkeit sind dabei keine Marketing-Begriffe, sondern jahrzehntelang gelebte Praxis.

Bio-Kontrollstelle-Zeile darunter **bleibt unverändert**:

> Bio-Kontrollstelle: C.A.A.E. · ES-ECO-001-AN

**Kachel 3 — Qualität**

Titel: `Die Qualität` → `Qualität`

Neuer Text:

> Innerhalb von 12 bis 24 Stunden nach der Ernte werden die Oliven schonend kalt gepresst. Diese schnelle Verarbeitung bewahrt einen besonders hohen Polyphenolgehalt — natürliche Antioxidantien, die das Öl nicht nur gesund, sondern auch geschmacklich einzigartig machen. Das Ergebnis: fruchtig, leicht bitter und mit einer angenehmen Schärfe im Abgang.

**Kachel 4 — Von Andalusien in die Schweiz**

Titel bleibt. Neuer Text:

> Seit rund 20 Jahren bringen wir dieses Olivenöl als Generalimporteur direkt von Andalusien in die Schweiz. Ohne Zwischenhändler, ohne Umwege. Jede Flasche erzählt die Geschichte einer Landschaft, einer Gemeinschaft und einer Leidenschaft für ein wunderbares Produkt.

### 2. `templates/produkte.html` — Hintergrund wechseln

Einzige Änderung im Inline-`style`-Attribut des `#bg-container`:

```
style="background-image: url('/static/images/backgrounds/olive-tree-hero.jpg');"
```

Alles andere (Overlay `bg-stone-900/30`, Card-Klassen, Layout) bleibt **unverändert**.

### Nicht betroffen

- Produktinformation-Kachel (Sachbezeichnung, Güteklasse, Nährwerte) — außerhalb SH-Scope
- CTA-Button am Seitenende
- `base.html`, `admin/*`, E-Mail-Templates
- `static/css/tailwind.css` — kein Rebuild
- `static/images/backgrounds/terracotta-texture.webp` — Datei bleibt im Repo (falls SH umschwenkt)
- Keine neuen Abhängigkeiten, keine Datenbankänderungen

## Test-Strategie

TDD nach superpowers-Regel: failing Tests zuerst.

### Test A — Öl-Seite Texte (`tests/test_routes.py`)

GET `/ueber-das-oel` (HTML) prüft:

**Positiv (muss enthalten sein):**
- `Kooperative Olivarera Los Pedroches (OLIPE)`
- `jahrzehntelang gelebte Praxis`
- `fruchtig, leicht bitter und mit einer angenehmen Schärfe im Abgang`
- `Leidenschaft für ein wunderbares Produkt`
- `von Hand gearbeitet und geerntet`
- `Bio-Kontrollstelle: C.A.A.E.` (Regression-Schutz)

**Negativ (darf nicht mehr enthalten sein):**
- `>Die Herkunft<` (als h2-Inhalt)
- `>Die Qualität<`
- `>Die Kooperative OLIPE<`
- `jahrzentelang` (Typo)
- `Rund 800 Bauernfamilien der Kooperative OLIPE arbeiten seit 1957` (alter Text)

### Test B — Produktseite Hintergrund (`tests/test_routes.py`)

GET `/` (HTML) prüft:

- Enthält `backgrounds/olive-tree-hero.jpg`
- Enthält **nicht** mehr `backgrounds/terracotta-texture.webp`

### Manuelle Smoke-Tests vor Merge

- `make dev` → `/` visuell: Produktkarten lesbar, Hintergrund passt zur Öl-Seite
- `/ueber-das-oel` visuell: Typografie, Zeilenumbrüche, Kontrast OK
- Mobile-Breakpoint: beide Seiten bleiben lesbar

## Issue-Checkliste

Wird im GitHub-Issue abgebildet:

- [ ] Titel "Die Herkunft" → "Herkunft" + neuer Haupttext
- [ ] Titel "Die Kooperative OLIPE" → "Kooperative OLIPE" + neuer Haupttext (Typo gefixt)
- [ ] Titel "Die Qualität" → "Qualität" + neuer Haupttext
- [ ] Neuer Haupttext "Von Andalusien in die Schweiz"
- [ ] Bio-Kontrollstelle-Zeile bleibt unverändert
- [ ] Produktseiten-Hintergrund auf `olive-tree-hero.jpg`
- [ ] Failing Tests geschrieben (Test A + B)
- [ ] Implementierung grün
- [ ] Smoke-Test lokal ausgeführt

## Referenzen

- SH-Feedback vom 2026-04-21 (Nachricht im Claude-Code-Chat)
- Template-Konventionen: `../../../CLAUDE.md` (Olivalle-Projektebene)
- Vorheriger Lebensmittel-Deklaration-Scope: `2026-04-16-lebensmittel-deklaration-design.md` (definiert Produktinformation-Kachel, bleibt hier unberührt)
