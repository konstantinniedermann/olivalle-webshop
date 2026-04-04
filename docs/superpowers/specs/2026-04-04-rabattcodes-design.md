# Rabattcodes & Gutscheine — Design Spec

> **Issue:** #62
> **Datum:** 2026-04-04
> **Status:** Approved

## Zusammenfassung

Rabattcodes im Olivalle Webshop: Admin erstellt Codes im Admin-Portal, Kunden geben sie im Checkout ein, Preis aktualisiert sich automatisch. Einmalige und mehrmalige Codes mit Zeithorizont.

## Entscheide

| Frage | Entscheid |
|---|---|
| Wertgutscheine? | Nein, nur Rabattcodes (prozentual oder Fixbetrag) |
| Mehrere Codes pro Bestellung? | Nein, ein Code pro Bestellung |
| Pro Kunde einmalig? | Ja, einmal pro E-Mail-Adresse (Tracking via `code_einloesungen`) |
| Rundung | Schweizer 5-Rappen-Rundung: `round(betrag * 20) / 20` |
| Rabatt vor/nach Versand? | Rabatt auf Subtotal vor Versandkosten |
| Versandkosten-Schwelle? | Basiert auf Subtotal vor Rabatt (CHF 100 Grenze bleibt unverändert) |
| Ansatz | Serverseitig mit AJAX-Validierung im Checkout |

## 1. Datenbank-Schema

### Neue Tabelle `rabattcodes`

| Spalte | Typ | Beschreibung |
|---|---|---|
| id | INTEGER PK | Auto-Increment |
| code | TEXT UNIQUE NOT NULL | Uppercase, z.B. `FRUEHLING10` |
| rabattart | TEXT NOT NULL | `prozent` oder `fixbetrag` |
| rabattwert | REAL NOT NULL | z.B. 10.0 (= 10% oder CHF 10) |
| mindestbestellwert_chf | REAL NULL | Optional, z.B. CHF 50 |
| max_einloesungen | INTEGER NULL | NULL = unbegrenzt |
| aktuelle_einloesungen | INTEGER DEFAULT 0 | Counter |
| gueltig_von | TEXT NOT NULL | ISO-Datum |
| gueltig_bis | TEXT NOT NULL | ISO-Datum |
| aktiv | INTEGER DEFAULT 1 | Admin kann deaktivieren |
| erstellt_am | TEXT NOT NULL | Timestamp |

### Neue Tabelle `code_einloesungen`

| Spalte | Typ | Beschreibung |
|---|---|---|
| id | INTEGER PK | Auto-Increment |
| rabattcode_id | INTEGER FK NOT NULL | → `rabattcodes.id` |
| email | TEXT NOT NULL | Kunden-E-Mail |
| bestellung_id | INTEGER FK NOT NULL | → `bestellungen.id` |
| eingeloest_am | TEXT NOT NULL | Timestamp |

UNIQUE Constraint auf `(rabattcode_id, email)` — verhindert doppelte Einlösung.

### Erweiterung `bestellungen`

| Neue Spalte | Typ | Beschreibung |
|---|---|---|
| rabattcode_id | INTEGER NULL FK | → `rabattcodes.id` |
| rabattbetrag_chf | REAL DEFAULT 0 | Tatsächlich abgezogener Betrag |

## 2. Backend-Logik

### Neuer Service: `app/services/rabattcode_service.py`

**`pruefe_rabattcode(conn, code: str, email: str, subtotal: float) -> dict`**

Validierungsreihenfolge:
1. Code existiert und ist aktiv
2. Aktuelles Datum liegt zwischen `gueltig_von` und `gueltig_bis`
3. `max_einloesungen` nicht erreicht (falls gesetzt)
4. E-Mail hat diesen Code noch nicht eingelöst
5. `mindestbestellwert_chf` erreicht (falls gesetzt)

Rückgabe bei Erfolg:
```python
{"gueltig": True, "rabattbetrag": 5.00, "rabattart": "fixbetrag", "rabattcode_id": 1}
```

Rückgabe bei Fehler:
```python
{"gueltig": False, "fehler": "Code abgelaufen"}
```

**`berechne_rabatt(rabattart: str, rabattwert: float, subtotal: float) -> float`**

- Prozent: `round(subtotal * rabattwert / 100 * 20) / 20` (5-Rappen-Rundung)
- Fixbetrag: `min(rabattwert, subtotal)` (nicht mehr als Subtotal)
- Ergebnis nie negativ

**`loesche_code_ein(conn, rabattcode_id: int, email: str, bestellung_id: int)`**

- Eintrag in `code_einloesungen` erstellen
- `aktuelle_einloesungen` in `rabattcodes` hochzählen

### Neuer API-Endpoint: `POST /api/rabattcode/pruefen`

Request: `{"code": "FRUEHLING10", "email": "kunde@example.com", "subtotal": 26.00}`

Response (Erfolg):
```json
{"gueltig": true, "rabattbetrag": 5.00, "rabattart": "fixbetrag", "beschreibung": "CHF 5.00 Rabatt"}
```

Response (Fehler):
```json
{"gueltig": false, "fehler": "Code abgelaufen"}
```

### Anpassung Bestellprozess (`/bestellen` in `bestellungen.py`)

1. Falls Rabattcode mitgeschickt: nochmal serverseitig validieren
2. Rabatt berechnen: `gesamt = subtotal - rabattbetrag + versandkosten`
3. `rabattcode_id` und `rabattbetrag_chf` in `bestellungen` speichern
4. Eintrag in `code_einloesungen` erstellen
5. `aktuelle_einloesungen` hochzählen

Versandkosten-Schwelle (gratis ab CHF 100) basiert auf Subtotal **vor** Rabatt.

### Anpassung Stripe-Session (`stripe_service.py`)

Dynamisch einen Stripe Coupon erstellen für den konkreten Rabattbetrag und auf die Checkout-Session anwenden.

## 3. Frontend — Checkout

### Rabattcode-Eingabe in `checkout.html`

Position: nach Warenkorb-Zusammenfassung, vor Zahlungsart-Auswahl.

- Textfeld + Button "Einlösen"
- AJAX-Call an `POST /api/rabattcode/pruefen`
- Erfolg: grüne Meldung, Preiszusammenfassung aktualisiert
- Fehler: rote Meldung mit spezifischem Grund
- Button zum Entfernen des Codes (Preis zurücksetzen)
- Code wird als Hidden-Field im Formular mitgeschickt

### Preiszusammenfassung

```
Warenkorb:              CHF 26.00
Rabatt (FRUEHLING10):   - CHF 5.00
Versandkosten:          CHF  9.90
────────────────────────────────────
Total:                  CHF 30.90
```

Rabattzeile erscheint nur bei gültigem Code.

## 4. Admin-Portal

### Übersichtsseite `/admin/rabattcodes`

Tabelle mit allen Codes: Code, Art, Wert, Gültig bis, Einlösungen (x/max), Status, Aktionen (Bearbeiten, Deaktivieren).

Status automatisch berechnet: **aktiv**, **abgelaufen**, **aufgebraucht**, **deaktiviert**.

### Erstellen/Bearbeiten

Formulare unter `/admin/rabattcodes/neu` und `/admin/rabattcodes/{id}/bearbeiten`:
- Code (Text, automatisch Uppercase)
- Rabattart (Dropdown: Prozent / Fixbetrag)
- Rabattwert (Zahl)
- Gültig von / bis (Datumsfelder)
- Max. Einlösungen (optional)
- Mindestbestellwert (optional)
- Aktiv (Checkbox)

### Bestelldetail-Erweiterung

In `/admin/bestellungen/{id}`: falls Rabattcode verwendet, anzeigen als "Rabattcode: FRUEHLING10 (- CHF 5.00)".

Navigation: Link "Rabattcodes" in der Admin-Navigation. Gleiches Styling (Card-UI, `bg-stone-700`).

## 5. E-Mail-Templates

### Anpassungen nötig

- **`bestellbestaetigung.html`**: Rabattzeile in Preiszusammenfassung
- **`bestellung_stakeholder.html`**: Rabattzeile + verwendeter Code
- **`zahlungseingang.html`**: Rabattzeile in Preiszusammenfassung

### Keine Anpassung nötig

- `versandbestaetigung.html` — keine Preisdetails
- `abholbereit.html` — keine Preisdetails

### QR-Rechnung

Betrag auf QR-Rechnung ist bereits der rabattierte Total. Keine separate Rabattzeile nötig.

## 6. Testing (pytest)

- **Validierung:** Alle Fälle (gültig, abgelaufen, aufgebraucht, E-Mail bereits eingelöst, Mindestbestellwert nicht erreicht, deaktiviert, ungültiger Code)
- **Berechnung:** Prozent- und Fixrabatt, 5-Rappen-Rundung, Total nicht unter 0
- **Bestellprozess:** Rabatt korrekt gespeichert, `code_einloesungen` angelegt, Counter hochgezählt
- **Stripe:** Coupon korrekt an Session übergeben
- **Admin CRUD:** Erstellen, Bearbeiten, Deaktivieren, Statusberechnung
- **E-Mail pro Kunde:** Doppelte Einlösung wird verhindert

## Nicht im Scope

- Wertgutscheine (festes Guthaben über mehrere Bestellungen)
- Kombination mehrerer Codes
- Automatische Code-Generierung (Batch)
- Kategorien-/produktspezifische Rabatte
