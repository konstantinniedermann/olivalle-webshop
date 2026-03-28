# Design Spec: Card-UI & Responsive Design (Issue #51)

**Datum:** 2026-03-28
**Issue:** #51 — Card-UI & Responsive Design auf bestehendes Frontend anwenden
**TODO:** O-UI (Personas & UI-Karten-Entwurf)
**Scope:** Alle 4 Kundenseiten (Produkte, Warenkorb, Checkout, Bestätigung)

## Personas (UX-Kontext)

| Persona | Beschreibung | Design-Relevanz |
|---|---|---|
| **Marco, 45** | Kauft gelegentlich für Familie/Freunde, will unkomplizierten Checkout ohne Registrierung | Validiert Warenkorb- und Checkout-Design: einfach, schnell, keine Hürden |
| **Lisa, 32** | Will regelmässige Lieferung, will Bestellhistorie sehen | Validiert, dass UI-Entscheidungen spätere Phase-3-Features nicht verbauen |

## Entscheidungen

### 1. Responsive Breakpoints

**Gewählt:** Stufenweise 1 → 2 → 3 Spalten

| Breakpoint | Spalten | Tailwind-Klasse |
|---|---|---|
| Mobile (<640px) | 1 | `grid-cols-1` (default) |
| Tablet (640px+) | 2 | `sm:grid-cols-2` |
| Desktop (1024px+) | 3 | `lg:grid-cols-3` |

**Begründung:** Skaliert besser als der aktuelle Sprung 1 → 3 (bei `md:grid-cols-3`). Bei nur 3 Produkten bleibt auf Tablets eine Karte allein in der zweiten Reihe — akzeptabel und zukunftssicher falls Produkte dazukommen.

### 2. Produktkarten — Dezent & elegant

Aktuell: `bg-stone-700 rounded-lg p-6`, kein Schatten, kein Hover.

Neu:
- Subtiler Schatten: `shadow-md`
- Hover: leichtes Anheben (`hover:-translate-y-1`) und verstärkter Schatten (`hover:shadow-lg`)
- Sanfte Transition: `transition-all duration-200`
- Abstände und Rundungen konsistent halten

### 3. Warenkorb — Card-basiert mit Mengensteuerung

Aktuell: Tabelle (`<table>`) mit einfachem Number-Input.

Neu:
- Jede Position als eigene Card (`bg-stone-700/800`, Schatten, Rundung)
- Produktbild links (klein, 64px)
- Einzelpreis sichtbar ("CHF 18.00 pro Stück")
- +/− Buttons für Mengensteuerung (statt reinem Number-Input)
- Entfernen-Button (✕) rechts
- Summary-Card unten: Versandkosten, Total, "Zur Kasse"-Button
- Responsive: auf Mobile stapeln sich Bild/Info und Menge/Preis untereinander

### 4. Checkout — Sektionen als Cards

Aktuell: Flaches Formular ohne visuelle Gruppierung.

Neu:
- Jede Sektion (Lieferadresse, Versand, Zahlung, Kommentar) als eigene Card
- `autocomplete`-Attribute auf allen Feldern:
  - `given-name`, `family-name`, `email`, `street-address`, `postal-code`, `address-level2`, `tel`
- Optionale Felder (Telefon, Kommentar) mit "(optional)"-Hinweis
- Cards mit gleichem Stil wie Warenkorb (konsistenter Look)

### 5. Bestätigung — Einzelne Card

Aktuell: Zentrierter Text ohne Container.

Neu:
- Bestätigungstext in einer zentrierten Card
- Häkchen-Icon oben (CSS/SVG, kein externes Asset)
- Gleicher Card-Stil wie andere Seiten

## Nicht im Scope

- Font-Änderungen (wird am Endergebnis beurteilt)
- Abo-Feature (mit Stakeholder verworfen)
- PLZ → Ort Autocomplete (eigenes Issue #52)
- Header/Footer-Änderungen

## Referenz

- Design-Prinzipien: `../CLAUDE.md` → Sektion "Design-Prinzipien"
- Allgemeine Card-UI Spec: `docs/superpowers/specs/2026-03-28-card-ui-guidelines-design.md`
- Warenkorb-Mockup: `.superpowers/brainstorm/82427-1774694050/content/warenkorb-v2.html`
