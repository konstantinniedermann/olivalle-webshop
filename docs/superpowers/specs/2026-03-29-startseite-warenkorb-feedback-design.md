# Design: Startseite als Produktseite + Warenkorb-Feedback

**Datum:** 2026-03-29
**Status:** Approved

## Kontext

Drei Verbesserungen am Webshop:
1. Startseite zeigt bisher nur Produktkarten mit Einzeilern — der ausgearbeitete Produkttext (Variante B) fehlt
2. Kein visuelles Feedback beim Hinzufügen zum Warenkorb
3. Unklar wie man von der Startseite zum Checkout kommt

## 1. Startseite = Produktseite (`/`)

Die bestehende `produkte.html` wird zur kombinierten Produkt- und Startseite umgebaut.

### Aufbau (von oben nach unten)

1. **Header** — wie bisher
2. **Hero-Bereich** — grosses Produktbild + Variante-B-Text (allgemeine Info zu Olivalle, Kooperative OLIPE, Geschmacksprofil)
3. **Gebinde-Auswahl** — drei Karten nebeneinander (250ml / 750ml / 3l):
   - Produktbild
   - Name + Preis
   - Produktspezifischer Kurztext aus `docs/produkttexte.md` (Abschnitt "Produktbeschreibungen")
   - "In den Warenkorb"-Button
4. **Footer** — wie bisher

### Technische Umsetzung

- Variante-B-Text kommt **statisch ins Template** (kein DB-Feld nötig — ein Text für alle Produkte)
- Produktspezifische Kurztexte (250ml/750ml/3l) ersetzen die bisherigen Einzeiler in der DB-Spalte `beschreibung`
- Migration-SQL aktualisieren: neue `beschreibung`-Werte aus `produkttexte.md`
- Bestehende Route `GET /` bleibt, Template wird umgebaut

### Responsive

- Mobile: Karten stapeln sich vertikal (wie bisher)
- Tablet/Desktop: Karten nebeneinander im Grid
- Nutzer prüft nach Implementierung ob Layout auf allen Geräten passt

## 2. Button-Animation beim Hinzufügen

Nach Klick auf "In den Warenkorb":
- Button wird kurz grün, Text wechselt zu "Hinzugefügt ✓"
- Nach ~1 Sekunde springt er zurück zum Originalzustand
- Reines CSS + JS, keine Library

## 3. Mini-Warenkorb-Flyout

Erscheint direkt nach der Button-Animation:
- Kleines Dropdown-Overlay unterhalb des Warenkorb-Links im Header
- Inhalt: Liste der Produkte im Warenkorb (Name, Menge, Preis), Gesamtbetrag
- Zwei Links: "Warenkorb anzeigen" + "Zur Kasse"
- Schliesst sich automatisch nach **2 Sekunden** oder bei Klick ausserhalb
- Reines CSS + JS in `base.html` (da Header auf allen Seiten sichtbar)

## 4. Was sich nicht ändert

- Warenkorb-Seite (`/warenkorb`) bleibt unverändert
- Checkout-Flow bleibt unverändert
- Cart-Logik bleibt clientseitig (localStorage)
- Header-Navigation bleibt gleich (Warenkorb-Link mit Zähler)

## Betroffene Dateien

| Datei | Änderung |
|---|---|
| `templates/produkte.html` | Umbau: Hero-Bereich + Variante-B-Text + Gebinde-Karten |
| `templates/base.html` | Flyout-HTML + CSS unter Warenkorb-Link |
| `static/js/cart.js` | `addToCart()` erweitern: Button-Animation + Flyout triggern |
| `migrations/001_initial.sql` | `beschreibung`-Werte aktualisieren (produktspezifische Kurztexte) |
