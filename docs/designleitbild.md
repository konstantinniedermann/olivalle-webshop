# Designleitbild — Kundenseite `/neu`

**Zweck:** Dieses Leitbild legt fest, aus welchen Bausteinen die neue Kundenseite besteht. Wer eine Seite baut oder ändert, nimmt einen Baustein von hier — und erfindet keinen neuen. Die Bausteine sind als CSS-Klassen mit Präfix `ol-` in `static/css/input.css` umgesetzt, wiederkehrende Strukturen als Makros in `templates/neu/_bausteine.html`. Der Test `tests/test_neu_designleitbild.py` schlägt an, wenn eine Vorlage am Leitbild vorbei gestaltet.

**Leitidee:** hell, ruhig, mediterran. Viel Fläche, wenige Elemente, eine klare Handlung pro Ansicht.

## 1. Farben

Fünf Farben, jede mit genau einer Aufgabe.

| Farbe | Wert | Aufgabe |
|---|---|---|
| Creme | `#FAF6EC` | Seitengrund |
| Weiss | `#FFFFFF` | Karten (Produktfotos haben weissen Grund) |
| Sand | `#F0E8D6` | ruhige Flächen: Faktenband, Fortschritt, Hover |
| Hain | `#25301A` | Text, dunkle Abschnitte, Hauptknopf |
| Ölgold | `#C9A227` | kleiner Akzent: Unterstreichung, Fortschrittsbalken, Zähler |
| Terrakotta | `#B8482B` | ausschliesslich Rabatt und Fehlermeldungen |

Text hat **drei Stufen**: Hain (Haupttext), Hain 70 % (Begleittext), Hain 50 % (Hinweise). Auf dunklem Grund: Creme und Creme 75 %. Linien: Hain 10 %; Rahmen von Bedienelementen: Hain 20 %.

## 2. Schrift

Zwei Schriften, zwei Schnitte (normal 400, mittel 500). Kein Fett, kein Kursiv.

- **Fraunces** (Serif): Titel, Preise.
- **DM Sans**: alles andere.

| Stufe | Klasse | Grösse (Handy → Desktop) | Einsatz |
|---|---|---|---|
| Auftakt | `ol-display` | 48 → 60 → 72 px | nur Startseite, einmal |
| Seitentitel | `ol-h1` | 36 → 48 px | einmal pro Seite |
| Abschnittstitel | `ol-h2` | 30 → 36 px | einmal pro Abschnitt |
| Kartentitel | `ol-h3` | 24 px | Karten, Faktenpunkte, Preise |
| Einleitung | `ol-lead` | 18 px | ein Absatz unter einem Titel |
| Text | `ol-text` | 16 px | Fliesstext |
| Klein | `ol-klein` | 14 px | Begleitangaben |
| Hinweis | `ol-hinweis` | 12 px | Fussnoten |
| Rubrik | `ol-label` | 12 px, Versalien, gesperrt | über jedem Titel |

Jeder Abschnitt beginnt gleich: **Rubrik → Titel → (Einleitung)**. Dafür gibt es das Makro `kopf()`.

## 3. Form

- **Ecken:** drei Radien. Rund (`rounded-full`) für alles Klickbare und Plaketten; 24 px (`rounded-3xl`) für Karten und Bilder; 12 px (`rounded-xl`) für Eingabefelder und Auswahlzeilen.
- **Schatten:** nur einer (`ol-schwebend`), und nur für das, was über der Seite liegt oder die Kaufentscheidung trägt: Einstiegsbild, Zusammenfassung, Warenkorb-Schublade, Handy-Leiste. Karten haben eine feine Linie, keinen Schatten.
- **Abstände:** Seitenbreite `ol-container` (max. 1152 px). Abschnitt `ol-abschnitt` (64 → 96 px oben und unten). Karten-Innenabstand 24 → 32 px (`ol-karte`), kompakt 20 px (`ol-karte-kompakt`) für Produkt- und Warenkorbkarten. Raster: 24 px zwischen Karten, 40 → 64 px zwischen Text und Bild.
- **Bewegung:** eine Dauer (300 ms) für Farbwechsel; Abschnitte blenden beim Scrollen einmal sanft ein. Nur Produktkarten heben sich beim Überfahren.

## 4. Bausteine

### Knöpfe

Drei Arten, zwei Grössen. **Pro Ansicht genau ein Hauptknopf.**

| Art | Klasse | Einsatz |
|---|---|---|
| Hauptknopf | `ol-btn ol-btn-primaer` | die eine Handlung der Ansicht (bestellen, in den Warenkorb, zur Kasse) |
| Nebenknopf | `ol-btn ol-btn-sekundaer` | zweite Wahl (Rabattcode einlösen) |
| Heller Knopf | `ol-btn ol-btn-hell` | jeder Knopf auf dunklem Grund oder Bild |

Grössen: normal (48 px hoch), klein `ol-btn-klein` (40 px; Kopfzeile). `ol-btn-block` zieht den Knopf auf volle Breite. Verweise im Text sind `ol-link` (Ölgold unterstrichen).

### Weitere Bausteine

| Baustein | Klasse / Makro | Hinweis |
|---|---|---|
| Karte | `ol-karte` (+ `ol-karte-kompakt`, `ol-schwebend`) | weiss, 24 px Ecken, feine Linie |
| Bild | `ol-bild` | 24 px Ecken; Stimmungsbilder sind Symbolbilder |
| Dunkler Abschnitt | `ol-dunkel` | stellt Text, Rubrik und Linien automatisch um |
| Mengenwahl | `ol-stepper` / Makro `stepper()` | überall dieselbe: Produktkarte, Schublade, Warenkorb |
| Plakette | `ol-pill` + `ol-pill-rabatt` / `ol-pill-rabatt-ruhig` | nur für Rabatt |
| Faktenpunkt | Makro `fakt()` | Kartentitel + kleiner Text; Faktenband, Herkunft |
| Eingabefeld | `ol-feld`, `ol-feldlabel` | 48 px hoch, 12 px Ecken |
| Auswahlzeile | `ol-option` (+ `ol-option-aktiv`) | Versand- und Zahlungsart |
| Fortschritt | `ol-fortschritt` | «Noch CHF … bis zum Gratis-Versand» |
| Summenzeilen | `ol-summe`, `ol-total` | Zusammenfassung in Schublade, Warenkorb, Kasse |
| Symbolknopf | `ol-icon-btn` | schliessen, entfernen |

## 5. Aufbau der Seiten

- **Jede Seite:** Hinweisleiste → Kopfzeile → Inhalt → Fusszeile.
- **Startseite:** Einstieg → Faktenband → Produkte → Herkunft (dunkel) → Bestellen → Abschluss (Bild).
- **Inhaltsseiten:** Seitentitel mit Rubrik, danach Abschnitte im Wechsel hell/dunkel, jeder mit `kopf()`.
- **Warenkorb und Kasse:** links der Inhalt in Karten, rechts die schwebende Zusammenfassung mit dem Hauptknopf.

## 6. Was es nicht gibt

Keine weiteren Schriftgrössen, Radien, Schatten oder Knopfarten. Kein Fett- oder Kursivdruck. Kein Ölgold als Fläche hinter Text. Kein Terrakotta ausserhalb von Rabatt und Fehlern. Keine erfundenen Bewertungen, Siegel oder Verknappung.
