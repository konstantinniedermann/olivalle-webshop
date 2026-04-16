# Lebensmittel-Deklaration auf Produktseite (Issue #100)

## Kontext

Art. 39 LIV verlangt für den Lebensmittel-Fernabsatz, dass alle Pflichtangaben vor Kaufabschluss online verfügbar sind. Aktuell fehlen auf der Website: Sachbezeichnung, Güteklasse-Pflichtsatz, Nährwerttabelle, Bio-Kontrollstellen-Code und Lagerhinweis.

Die Nährwerte und der Bio-Code stammen vom Etikett des Produkts (Foto: `static/images/Information_nutricional.jpg`).

## Entscheidungen

| Frage | Entscheid | Begründung |
|---|---|---|
| Platzierung | `ueber-das-oel.html` | Einprodukt-Shop, Nährwerte gelten für alle Gebinde. Art. 39 LIV erlaubt verlinkte Unterseiten, sofern leicht zugänglich. |
| Nährwerte-Bezug | Pro 100 g | Direkt vom Etikett übernommen, keine eigene Umrechnung. |
| Vitamin E | Ja, aufnehmen | Auf Etikett vorhanden, Verkaufsargument. |
| Bio-Code | In OLIPE-Kachel integrieren | Kachel erwähnt bereits Bio-Zertifizierung, natürliche Ergänzung. |
| Übrige Pflichtangaben | Neue kombinierte Kachel „Produktinformation" | Sachbezeichnung, Güteklasse, Lagerhinweis + Nährwerte in einer Kachel. |

## Änderungen

### 1. `templates/ueber-das-oel.html` — OLIPE-Kachel anpassen

Bestehenden Text beibehalten. Am Ende des Absatzes ergänzen:

> Bio-Kontrollstelle: C.A.A.E. · ES-ECO-001-AN

### 2. `templates/ueber-das-oel.html` — Neue Kachel „Produktinformation"

Position: nach der letzten Inhaltskachel („Von Andalusien in die Schweiz"), vor dem CTA-Button.

Styling: gleiche Klassen wie bestehende Kacheln (`bg-stone-900/75 backdrop-blur-[4px] rounded-lg p-6 border border-stone-600/15`).

Inhalt, oberer Teil:
- **Sachbezeichnung:** Natives Olivenöl extra (biologisch)
- **Güteklasse-Pflichtsatz** als eingerücktes Zitat: «Olivenöl höchster Qualität, direkt aus Oliven ausschliesslich mit mechanischen Verfahren gewonnen.»
- **Lagerhinweis:** Kühl und dunkel lagern, vor Licht schützen.

Trennlinie (`border-t border-stone-600/15`).

Inhalt, unterer Teil — **Nährwerte pro 100 g** als Tabelle:

| Nährstoff | Wert |
|---|---|
| Energie | 3700 kJ / 900 kcal |
| Fett | 100 g |
| davon gesättigte Fettsäuren | 16 g |
| Kohlenhydrate | 0,0 g |
| davon Zucker | 0,0 g |
| Eiweiss | 0,0 g |
| Salz | 0,0 g |
| Vitamin E | 20 mg (167% NRV*) |

Fussnote: * NRV = Nährstoffreferenzwert

### 3. `templates/produkte.html` — Link anpassen

Bestehenden Link-Text ändern von:
> Mehr erfahren →

zu:
> Mehr über das Öl erfahren — inkl. Nährwerte & Deklaration →

### Nicht betroffen

- Kein neues JavaScript
- Keine neuen Routen oder API-Endpunkte
- Keine Datenbankänderungen
- Keine neuen Abhängigkeiten

## Rechtliche Grundlage

- **Art. 39 LIV:** Pflichtangaben müssen vor Kaufabschluss zugänglich sein, nicht zwingend auf derselben Seite. Verlinkte Unterseiten sind zulässig bei leichter Zugänglichkeit (kein Zusatzaufwand, klarer Verweis).
- **EU-VO 29/2012:** Güteklasse-Pflichtsatz für „Natives Olivenöl extra".

## Issue-Checkliste (aus #100)

- [x] Sachbezeichnung „Natives Olivenöl extra" — Kachel „Produktinformation"
- [x] Güteklasse-Pflichtsatz — Kachel „Produktinformation"
- [x] Nährwerttabelle pro 100 g — Kachel „Produktinformation"
- [x] Bio-Zertifizierung mit Code ES-ECO-001-AN — OLIPE-Kachel
- [x] Lagerhinweis — Kachel „Produktinformation"
