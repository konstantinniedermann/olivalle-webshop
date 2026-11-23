# Neues Kunden-Frontend unter `/neu` — Design

Datum: 2026-11-23 · Branch: `feat/neues-frontend`

## Absicht
Der Kundenauftritt soll frischer und moderner wirken und stärker zum Kauf anregen. Die neue
Fassung entsteht **parallel** zur bestehenden Seite unter `/neu`, damit der Inhaber beide
Fassungen nebeneinander vergleichen kann. Die Gestaltung ist an den Entwickler delegiert
(„optisch muss nichts mehr an die jetzige Seite erinnern").

## Ziele
- Alle Kundenseiten in neuer Gestaltung unter `/neu/…`: Startseite/Produkte, Über das Öl,
  Warenkorb, Kasse, Bestätigung, Impressum, Datenschutz, AGB.
- Gleiche Inhalte und gleiche Funktionen wie heute; gleicher Warenkorb (localStorage), gleiche
  Bestelllogik, gleiche Preise, gleiche Zahlungsarten.
- Verkaufsfördernde Elemente, ausschliesslich aus Fakten, die heute schon auf der Seite stehen.

## Nicht-Ziele
- Admin-Portal, E-Mail-Vorlagen, Texte, Preise, Fachlogik, Datenbank.
- Umstellung der Hauptadresse auf die neue Fassung (späterer, eigener Schritt).
- Neue Abhängigkeiten (kein JS-Framework, keine Bild-Bibliothek).

## Anti-Ziele
- Erfundene Bewertungen, Siegel, Knappheit („nur noch 3 Stück") oder neue Produktbehauptungen.
- Generierte Bilder der Produkte oder generierte Bilder, die als „unser Hain" ausgegeben werden.
- Jede Verhaltensänderung der bestehenden Seite.

## Ansätze
| Ansatz | Bewertung |
|---|---|
| **A — Unterseite `/neu` (gewählt)** | Beide Fassungen nebeneinander vergleichbar; echte Bestellungen; alte Seite unverändert. Bestellstrecke braucht eine „Variante". |
| B — Umschalter per Cookie | Schlanker, aber kein Vergleich nebeneinander im selben Browser. |
| C — separate Vorschau-App | Eigene DB, eigenes Stripe-Setup, laufende Pflege — zu viel für einen Vergleich. |

Vom Nutzer gewählt: A mit Adresse `/neu`.

## Gestaltung (Entscheid des Entwicklers)
**Leitidee:** hell, mediterran, redaktionell — „Feinkost-Magazin" statt „dunkle Taverne".

- **Farben:** warmes Creme als Grund, tiefes Olivgrün für Text und dunkle Abschnitte, Ölgold als
  Akzent, Terrakotta nur für Rabatt-Elemente. Produktflächen weiss (die Produktfotos haben
  weissen Hintergrund; so wirken sie freigestellt, ohne Bildbearbeitung).
- **Schrift:** Fraunces (Serif, Titel) + DM Sans (Text), via Google Fonts wie bisher.
- **Breite:** volle Breite mit grosszügigen Abschnitten statt schmaler Spalte; Mobile-first.

**Startseite**
1. Hinweisleiste: Gratisversand ab Schwelle · Abholung Region Olten.
2. Kopfzeile hell, Warenkorb-Knopf mit Zähler; Warenkorb öffnet als seitliche Schublade.
3. Einstieg (Hero): grosse Aussage, Kauf-Knopf (springt zu den Produkten), Zweitlink „Über das Öl",
   Stimmungsbild.
4. Faktenband: Bio-zertifiziert (ES-ECO-001-AN) · Sorte Picual · Handernte · kalt gepresst in
   12–24 h · seit rund 20 Jahren direkt importiert.
5. Produkte: grosse Karten, Mengenwahl direkt auf der Karte, Aktionspreis-Darstellung wie heute
   (Streichpreis, Prozent, Aktionstext).
6. Herkunfts-Abschnitt mit Kurzfassung aus „Über das Öl" (bestehende Sätze) und Link.
7. „So bestellst du": Postversand / Abholung / Zahlungsarten (Twint, Karte, Rechnung).
8. Fusszeile.

**Verkaufselemente:** Fortschrittsbalken „noch CHF X bis Gratisversand" (Schublade, Warenkorb),
Faktenband, Zahlungsarten sichtbar vor der Kasse, auf Mobile eine fixe Warenkorb-Leiste sobald
etwas im Korb liegt, Bestellübersicht mit Artikeln neben dem Kassenformular.

**Übrige Seiten:** Über das Öl als Magazin-Seite mit Bildern und Nährwerttabelle; Warenkorb und
Kasse zweispaltig (Formular + mitlaufende Zusammenfassung); Rechtstexte als ruhige Leseseite.

## Technik
- Routen: neuer Router `app/routers/neu.py` mit Präfix `/neu`; Vorlagen in `templates/neu/`.
- **Variante in der Bestellstrecke:** verstecktes Formularfeld `variante` (Whitelist: leer | `neu`,
  nie eine freie URL). `POST /bestellen` bleibt der einzige Endpunkt (CSRF, Rate-Limit
  unverändert) und wählt damit Bestätigungs-Vorlage sowie Stripe-`success_url`/`cancel_url`.
  Neue Route `GET /neu/bestaetigung` für die Stripe-Rückkehr.
- `cart.js` wird unverändert mitbenutzt (Speicher, Summen, Versandkosten). Die neue Oberfläche
  bekommt ein eigenes `static/js/neu.js` mit eigenen Klassen/IDs, damit die Handler der alten
  Seite nicht greifen. `<body>` trägt weiterhin `data-versandkosten` / `data-gratis-ab`.
- Tailwind: neue Farben/Schriften werden **ergänzt** (`accent`, `display`, `body` bleiben).
- CSP unverändert: Inline-Skripte nur mit Nonce, Bilder lokal.
- `/neu` trägt `noindex` und wird von der alten Seite nicht verlinkt.
- Bilder: Stimmungsbilder generiert, lokal als WebP unter `static/images/neu/`.

## Nachweis
- Routentests für alle `/neu`-Seiten; Test auf `noindex` und Cache-Busting.
- Test: sichtbarer Text von AGB, Datenschutz, Impressum ist in alter und neuer Fassung identisch.
- Unit-Test: Stripe-URLs je Variante; Bestätigungs-Vorlage je Variante (Rechnung, Abholung bar).
- Bestehende Testsuite bleibt grün.
- Screenshots der laufenden App, Mobile und Desktop.

## Reihenfolge
1. Fundament + Startseite, lokal, Screenshot an den Nutzer.
2. Übrige Seiten und Bestellstrecke.
3. Review, danach Freigabe für Merge/Deploy durch den Nutzer.

## Nachtrag 2026-11-23 — nach Rückmeldung des Nutzers

Der Abschnitt «Gestaltung» oben beschreibt den ersten Entwurf. Nach zwei Rückmeldungen gilt:

- **Massgeblich für die Gestaltung ist `docs/designleitbild.md`** (feste Bausteine statt Einzelwerte; Wächtertest `tests/test_neu_designleitbild.py`).
- **Startseite verschlankt:** Einstieg → Produkte → Herkunft → Abschluss. Faktenband und der Abschnitt «So bestellst du» sind entfallen, weil sie Informationen wiederholten; Versand/Abholung stehen in der Hinweisleiste, Zahlungsarten an der Kasse.
- **Texte nur von der bestehenden Seite:** keine neu formulierten Überschriften oder Aussagen (Test in `tests/test_neu_frontend.py`).
- **Produktkarten zweispaltig** statt vierspaltig, damit Preis, Mengenwahl und Knopf je Reihe auf einer Linie stehen.
- **Dockerfile:** `static/js` wird in die CSS-Build-Stufe kopiert, weil `neu.js` Klassen setzt, die Tailwind sonst entfernt.
