# Design-Spec: Produktkarte — Rabatt-Stil vereinheitlichen, Layout-Fix, 4er-Raster

**Datum:** 2026-06-23
**Issue:** #135 (Folgeanpassungen zu den #134-Aktionspreisen)
**Branch:** feat/produkt-500ml-135

## Kontext & Problem

Mit dem in #135 eingeführten 4. Produkt (Olivenöl 500ml Geschenkflasche) zeigt
die Produktseite (`templates/produkte.html`, gerendert unter `/`) im Desktop-
Raster `lg:grid-cols-3` eine unausgewogene Verteilung (3 + 1). Gleichzeitig sind
mit den #134-Aktionspreisen mehrere rabattbezogene Elemente entstanden, die
optisch uneinheitlich sind, und das schmalere Raster verschärft ein Layout-
Problem in der Preiszeile.

Konkrete Mängel:

1. **Uneinheitlicher Rabatt-Stil.** Das `RABATT`-Badge ist eine rote Box mit
   weisser Schrift (`bg-red-600 text-white`). Der Aktionstext (gelb,
   `text-accent`) und der `−%`-Chip (gelbe Box, `bg-accent text-stone-900`)
   folgen einem anderen Stil.
2. **Button wird weggedrückt.** Die Preiszeile nutzt
   `flex … justify-between` mit der Preis-Gruppe (alter Preis + neuer Preis +
   `−%`-Chip) links und dem „In den Warenkorb"-Button rechts. Bei schmaler
   Karte wächst die Preis-Gruppe und drückt den Button optisch aus dem Element.
3. **3er-Raster passt nicht mehr** zu 4 Produkten.

## Entscheidungen (mit Stakeholder/Nutzer abgestimmt)

- **Rabatt-Stil:** Aktionstext und `−%`-Chip erhalten den roten Stil (rote Box,
  weisse Schrift) analog zum `RABATT`-Badge. Der **alte, durchgestrichene Preis
  bleibt schlicht grau durchgestrichen** (keine Box) — Rot bleibt dem aktiven
  Deal vorbehalten.
- **Layout-Fix:** Button rückt auf **volle Kartenbreite unter die Preiszeile**
  (einheitlich für alle Karten, mit und ohne Aktion). Kein horizontales
  Gedränge mehr.
- **Raster:** `lg:grid-cols-3` → `lg:grid-cols-4` (Mobile 1, Tablet 2×2,
  Desktop alle 4 nebeneinander).
- **Beschreibung:** minimal `text-sm` (weniger dominant im schmalen Raster).
  Kein Blocksatz (schlechte Lesbarkeit in schmalen Spalten). Kein `line-clamp`
  (würde bewusst geschriebene Verkaufs-Copy abschneiden).
- **Ausgeklammert (separates Issue):** echter Kachel-Overhaul mit ausklappbarem
  Beschreibungstext („mehr anzeigen", JS + Accessibility). Eigenes Brainstorming.

## Umsetzung

Alle Änderungen in **`templates/produkte.html`** (einzige Stelle der
Kartenmarkup; auch unter `/` gerendert) plus Doku.

### 1. Raster (Z. 23)

```
- grid gap-6 sm:grid-cols-2 lg:grid-cols-3
+ grid gap-6 sm:grid-cols-2 lg:grid-cols-4
```

### 2. Aktionstext (Z. 36) — roter Stil

```
- <p class="text-accent text-sm mt-2">{{ produkt.aktionstext }}</p>
+ <p class="bg-red-600 text-white text-xs font-bold px-2 py-1 rounded inline-block mt-2">{{ produkt.aktionstext }}</p>
```

`inline-block`, damit die rote Box den Text umschliesst statt über die volle
Kartenbreite zu laufen.

### 3. `−%`-Chip (Z. 43) — roter Stil

```
- <span class="bg-accent text-stone-900 text-xs font-bold px-1.5 py-0.5 rounded">−{{ produkt.prozent }}%</span>
+ <span class="bg-red-600 text-white text-xs font-bold px-1.5 py-0.5 rounded">−{{ produkt.prozent }}%</span>
```

### 4. Alter Preis (Z. 41) — unverändert

Bleibt `text-stone-400 line-through text-sm`.

### 5. Beschreibung (Z. 34) — `text-sm`

```
- <p class="text-stone-200 mt-2 flex-1">{{ produkt.beschreibung }}</p>
+ <p class="text-stone-200 text-sm mt-2 flex-1">{{ produkt.beschreibung }}</p>
```

`flex-1` bleibt erhalten (hält Preis/Button bei allen Karten unten bündig).

### 6. Layout-Fix Preiszeile + Button (Z. 38–57)

```
- <div class="mt-4 flex items-center justify-between">
-     <div class="flex items-baseline gap-2">
+ <div class="mt-4">
+     <div class="flex items-baseline flex-wrap gap-2 mb-3">
        … Preise/Chip unverändert …
      </div>
      <button … class="add-to-cart-btn … w-full …">In den Warenkorb</button>
  </div>
```

- Container: nur noch `mt-4` (kein `flex justify-between`).
- Preis-Gruppe: `flex-wrap` (Sicherheitsnetz) + `mb-3` (Abstand zum Button).
- Button: `w-full`.

## Tests (TDD)

Bestehende Text-Asserts in `tests/test_api_produkte.py` (RABATT, Aktionstext,
`CHF 12.00`, `−0` versteckt) bleiben grün — Textinhalt unverändert.

Neuer Regressions-Test: Bei aktiver Aktion enthält die gerenderte Seite den
`−%`-Chip im roten Stil (`bg-red-600`) und **nicht mehr** `bg-accent` für den
Chip/Aktionstext. Sichert die neue Stil-Konvention.

## Doku-Folgeänderungen

- **`olivalle/CLAUDE.md`** — Tabelle „Tailwind Card-UI Klassen": Responsive-Grid
  auf `lg:grid-cols-4` aktualisieren.
- Prüfen, ob `../CLAUDE.md` (Design-Prinzipien) oder `docs/arc42.md` die Grid-
  Klasse referenzieren → ggf. konsistent halten (Redundanz-Check).
- `docs/user-stories-testplan.md` gegenchecken (reine Stil-/Layout-Änderung,
  voraussichtlich keine Story betroffen).

## Nicht-Ziele

- Ausklappbarer/gekürzter Beschreibungstext (separates Issue).
- Änderungen an Datenmodell, Aktions-Logik oder Preisberechnung.
