# Design: Frontend-Redesign — Sticky Header, "Über das Öl"-Seite, Font-System

**Datum:** 2026-03-30
**Status:** Approved

## Kontext

Feedback zur aktuellen Produktseite:
1. Der lange Produkttext wirkt steril und schiebt die Produkte nach unten — man muss scrollen
2. Der Header scrollt nicht mit, deshalb sieht man das Warenkorb-Flyout nicht wenn man ein Produkt hinzufügt
3. Es fehlt eine einladende, atmosphärische Seite die die Geschichte des Öls erzählt

## Entscheidungen aus dem Brainstorming

| Frage | Entscheidung |
|-------|-------------|
| Produktseite nach Textauslagerung | Kurzer Teaser (1-2 Sätze) + Link "Mehr erfahren →", Produkte sofort sichtbar |
| "Über das Öl"-Layout | Scrollender Olivenbaum-Hintergrund, halbtransparente Kacheln einspaltig |
| Font-Paarung | Amatic SC (Titel) + Lora (Fliesstext) — global auf allen Seiten |
| Header-Layout | Sticky, minimalistisch: Logo links, Navigation rechts |
| Hintergrundbild Produktseite | Offener Punkt für spätere Session (Stimmungsbild z.B. Lehmwand) |

## 1. Sticky Header (alle Seiten)

Der Header in `base.html` wird sticky mit halbtransparentem Hintergrund und Backdrop-Blur.

### Aufbau

```
┌──────────────────────────────────────────────────┐
│  Olivalle          Über das Öl │ Produkte │ 🛒(0) │
└──────────────────────────────────────────────────┘
```

- **Links:** "Olivalle" (Logo, Amatic SC, gelb, Link zu `/`)
- **Rechts:** `Über das Öl` | `Produkte` | `Warenkorb (0)`
- Aktiver Link wird gelb hervorgehoben, restliche Links in stone-300
- CSS: `sticky top-0 z-50`, Hintergrund `bg-stone-800/90 backdrop-blur-sm`
- Border-bottom bleibt: `border-b border-stone-700`

### Warenkorb-Flyout

Bleibt wie bisher, ist aber jetzt immer sichtbar dank Sticky Header. Keine Änderung an der Flyout-Logik.

### Technische Umsetzung

- Änderung in `templates/base.html`: `<header>` bekommt `sticky top-0 z-50` + Blur-Klassen
- Navigation-Links als Liste im Header ergänzen
- Aktiver Link: Jinja2-Block oder Template-Variable `active_page` pro Route setzen

## 2. Produktseite (überarbeitet)

Der lange Hero-Text wird durch einen kurzen Teaser ersetzt.

### Aufbau (von oben nach unten)

1. **Sticky Header** (siehe oben)
2. **Kurzer Teaser** — 1-2 Sätze über Olivalle + Link "Mehr erfahren →" zu `/ueber-das-oel`
3. **Gebinde-Auswahl** — drei Produktkarten wie bisher (Bild, Name, Beschreibung, Preis, Button)
4. **Footer**

### Teaser-Text (Entwurf)

> Biologisches Olivenöl extra virgen aus dem Herzen Andalusiens. [Mehr erfahren →](/ueber-das-oel)

Kurz, einladend, verlinkt zur ausführlichen Geschichte.

### Hintergrund

Vorerst bleibt das bestehende dunkle Stone-Design. In einer späteren Session wird ein Stimmungsbild als Hintergrund gewählt (z.B. Lehmwand oder ähnlich), das nicht von den Produkten ablenkt.

### Technische Umsetzung

- `templates/produkte.html`: Hero-Section durch Teaser ersetzen (1 Zeile statt ganzer Absatz)
- Rest der Produktkarten bleibt unverändert

## 3. Neue Seite "Über das Öl" (`/ueber-das-oel`)

Eine einladende Informationsseite für Besucher die bewusst die Geschichte des Öls suchen.

### Visuelles Konzept

- **Olivenbaum-Foto** (`static/images/olive-tree-hero.jpg`, von olivalle.ch) als durchgehender, scrollender Hintergrund
- **Halbtransparente Kacheln** einspaltig (max-width ~560px, zentriert)
- Kacheln: `bg-stone-900/75 backdrop-blur-[4px]` + subtiler Rand `border border-stone-600/15`
- Schlicht — kein Hover-Effekt, kein Schatten
- Kachel-Titel in Amatic SC (gelb), Fliesstext in Lora

### Seitenstruktur

1. **Seitentitel** — "Unser Olivenöl" (Amatic SC, gelb, zentriert) + Untertitel "Biologisch · Extra Virgen · Andalusien"
2. **Kachel: Die Herkunft** — Nevadillo Blanco, Sierra Morena, Córdoba, Landschaft, Handernte
3. **Kachel: Die Kooperative OLIPE** — 800 Bauernfamilien, seit 1957, faire Preise, Bio-Zertifizierung
4. **Kachel: Die Qualität** — 12-24h Kaltpressung, Polyphenolgehalt, Geschmacksprofil (fruchtig, bitter, scharf)
5. **Kachel: Von Andalusien in die Schweiz** — 20 Jahre Generalimporteur, direkt ohne Zwischenhändler
6. **CTA-Button** — "Zu unseren Produkten →" (gelb, Link zu `/`)

### Texte

Die Texte basieren auf dem bestehenden Variante-B-Produkttext aus `produkte.html`, aufgeteilt und erweitert in die 4 Abschnitte. Die finalen Texte werden aus `docs/produkttexte.md` abgeleitet.

### Technische Umsetzung

- Neues Template: `templates/ueber-das-oel.html` (extends `base.html`)
- Neuer Router: `app/routers/seiten.py` mit Route `GET /ueber-das-oel`
- Router in `app/main.py` einbinden
- Bild bereits vorhanden: `static/images/olive-tree-hero.jpg` (4000x2666px, 523KB)
- Hintergrund via Tailwind: `bg-[url('/static/images/olive-tree-hero.jpg')] bg-cover bg-center`

## 4. Font-System (global)

Zwei Fonts für den gesamten Webshop:

| Font | Rolle | Einsatz |
|------|-------|---------|
| **Amatic SC** | Display/Titel | Logo, Seitentitel, Kachel-Überschriften, Produktnamen |
| **Lora** | Body/Fliesstext | Beschreibungen, Navigation, Buttons, Preise, Formulare |

### Technische Umsetzung

- Google Fonts Import in `base.html` erweitern: Lora (400, 600, 400 italic) hinzufügen
- Tailwind-Config erweitern: `fontFamily.body: ['Lora', 'serif']`
- `<body>` bekommt `font-body` als Default-Klasse
- Betrifft alle Seiten: Produkte, Warenkorb, Checkout, Bestätigung, Über das Öl

## Offene Punkte (spätere Sessions)

- **Hintergrundbild Produktseite:** Stimmungsbild wählen (z.B. Lehmwand), das nicht von Produkten ablenkt
- **Texte finalisieren:** Die 4 Abschnitte auf der "Über das Öl"-Seite inhaltlich mit dem Auftraggeber abstimmen

## Betroffene Dateien

| Datei | Änderung |
|-------|----------|
| `templates/base.html` | Sticky Header, Navigation, Lora-Font laden, Tailwind-Config |
| `templates/produkte.html` | Hero durch Teaser ersetzen |
| `templates/ueber-das-oel.html` | Neue Datei — "Über das Öl"-Seite |
| `app/routers/seiten.py` | Neue Datei — Route für statische Seiten |
| `app/main.py` | Neuen Router einbinden |
| `static/images/olive-tree-hero.jpg` | Bereits vorhanden |
