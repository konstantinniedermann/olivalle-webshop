# Design: Bezahlung bei Abholung + Stakeholder-Benachrichtigung

**Issue:** #59
**Datum:** 2026-04-01
**Status:** Genehmigt

## Zusammenfassung

Neue Zahlungsoption "Bezahlung bei Abholung" im Checkout, plus Stakeholder-Benachrichtigung bei jeder Bestellung.

## Entscheidungen

- Kein neuer DB-Status nötig — `"neu"` reicht als Initialstatus
- Kein Zeitlimit für unbezahlte Bestellungen — Admin storniert manuell bei Bedarf
- Admin markiert Barzahlung manuell als "bezahlt" (Funktion existiert bereits)
- Stakeholder bekommt bei **jeder** Bestellung eine Mail (nicht nur bei Abholung)
- Kunde kann per E-Mail-Hinweis stornieren (kein Self-Service-Link)
- Bei Abholung wird "Bezahlung bei Abholung" vorausgewählt, andere Optionen bleiben wählbar

## 1. Datenmodell

Kein Schema-Change. Neuer Wert `"abholung_bar"` in der bestehenden `zahlungsart`-Spalte (TEXT).

## 2. Checkout-Flow (Backend)

**Datei:** `app/routers/bestellungen.py`

Dritter Zweig im `POST /bestellen`-Handler:

```
if zahlungsart == "stripe":
    → Stripe Session, Redirect
elif zahlungsart == "rechnung":
    → QR-Rechnung, E-Mail mit PDF
elif zahlungsart == "abholung_bar":
    → Bestellung speichern (Status "neu"), Bestätigungsmail, Bestätigungsseite
```

**Validierung:** `abholung_bar` nur akzeptiert wenn `versandart == "abholung"`. Sonst HTTP 400.

**Pydantic-Model:** `BestellungInput.zahlungsart` akzeptiert `"stripe" | "rechnung" | "abholung_bar"`.

## 3. Checkout-Flow (Frontend)

**Dateien:** `templates/checkout.html`, `static/js/cart.js`

- Neuer Radio-Button "Bezahlung bei Abholung" in Zahlungsart-Gruppe
- JavaScript: Bei Versandart "Abholung" → Option einblenden und vorauswählen
- Bei Wechsel auf "Postversand" → Option ausblenden, Auswahl zurücksetzen
- Versandkosten-Logik bleibt gleich (Abholung = CHF 0)

## 4. E-Mails

### A) Bestätigungsmail Kunde bei "abholung_bar"

**Neues Template:** `templates/emails/bestellbestaetigung_abholung_bar.html`

Inhalt:
- Bestellübersicht (Produkte, Total)
- "Der Inhaber wird sich bei dir für einen Abholtermin melden"
- "Zum Stornieren kontaktiere uns unter olivalle.olten@outlook.com"

Gesendet direkt nach Bestellabschluss. Kein PDF-Anhang.

### B) Stakeholder-Benachrichtigung (neu, alle Zahlungsarten)

**Neues Template:** `templates/emails/bestellung_stakeholder.html`

Empfänger: `olivalle.olten@outlook.com`

Inhalt:
- Bestellübersicht (Kunde, Produkte, Total, Zahlungs-/Versandart)
- Bei `abholung_bar` zusätzlich: "Kontaktaufnahme mit Kunde für Abholtermin nötig"

Timing:
- Bei `rechnung` und `abholung_bar`: direkt nach Bestellabschluss
- Bei `stripe`: erst nach Webhook (nach erfolgreicher Zahlung)

### C) Bestehende Mails

Bleiben unverändert (Zahlungseingang, Versandbestätigung, Abholbereit).

## 5. Admin-Bereich

### Prozess-Leiste

Neuer Workflow für `abholung_bar + abholung`:

```
neu → in_bearbeitung → abholbereit → bezahlt → abgeschlossen
```

### Dashboard

- Spalte "Zahlungsart" zeigt "Bar bei Abholung" (statt `abholung_bar`)
- Kein neuer Filter nötig

### Bestelldetail

- Status manuell auf "bezahlt" setzen funktioniert bereits
- Prozess-Leiste zeigt neuen Workflow

## Nicht im Scope

- Automatische Stornierung nach Zeitlimit
- Self-Service-Stornierung per Link
- Neuer DB-Status (bestehendes `"neu"` reicht)
