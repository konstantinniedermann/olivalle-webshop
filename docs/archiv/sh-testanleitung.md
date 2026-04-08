# Olivalle Webshop — Testanleitung für Stakeholder

## Links

| Seite | URL |
|-------|-----|
| **Webshop** | [olivalle.fly.dev](https://olivalle.fly.dev/) |
| **Admin-Login** | [olivalle.fly.dev/admin/login](https://olivalle.fly.dev/admin/login) |
| **Stripe Dashboard (Testmodus)** | [Stripe Test-Dashboard öffnen](https://dashboard.stripe.com/acct_1TGdIDJidBPs4UgF/test/dashboard) |
| **User Stories (Testplan)** | [user-stories-testplan.md auf GitHub](https://github.com/konstantinniedermann/olivalle-webshop/blob/main/docs/user-stories-testplan.md) |

## Seiten im Webshop

| Seite | Pfad | Was du dort findest |
|-------|------|---------------------|
| Startseite / Produkte | `/` | Alle 3 Produkte (250ml, 750ml, 3L) mit Preisen und Warenkorb-Buttons |
| Über das Öl | `/ueber-das-oel` | Infos zum Olivenöl und zur Herkunft |
| Warenkorb | `/warenkorb` | Produkte, Mengen, Versandkosten, Total |
| Checkout | `/checkout` | Bestellformular (Kundendaten, Versandart, Zahlungsart) |
| Bestätigung | `/bestaetigung` | Bestellbestätigung nach Abschluss |
| Impressum | `/impressum` | Kontaktdaten, rechtliche Angaben |
| Datenschutz | `/datenschutz` | Datenschutzerklärung |
| AGB | `/agb` | Allgemeine Geschäftsbedingungen |

## Admin-Bereich

### Login

- **URL:** [olivalle.fly.dev/admin/login](https://olivalle.fly.dev/admin/login)
- **Benutzername:** `owner`
- **Passwort:** Schicke ich dir separat.

### Was du im Admin siehst

| Bereich | Was es zeigt |
|---------|--------------|
| **Dashboard** | Übersicht mit Statistiken: offene Bestellungen, Monatsumsatz, heutige Bestellungen |
| **Bestellliste** | Alle Bestellungen mit Status, Filter nach Status/Datum, Suche nach Name oder Bestell-ID |
| **Bestelldetail** | Kundendaten, Positionen, Zahlungsart, Versandart, Aktivitätslog |
| **Status ändern** | Bestellung durch die Status führen: neu → bezahlt → versendet/abholbereit → abgeschlossen (oder storniert) |
| **Notizen** | Notizen zu Bestellungen hinterlegen (z.B. "Kunde hat angerufen") |
| **Aktivitätslog** | Chronologische Übersicht aller Aktionen pro Bestellung |

## Stripe-Testumgebung

Der gesamte Shop läuft aktuell in einer **Stripe-Testumgebung**. Das heisst: Es werden keine echten Zahlungen abgewickelt und kein Geld belastet. Du kannst alles genau so testen, wie du es später im Echtbetrieb machen würdest — Bestellungen aufgeben, bezahlen, Status ändern. Alles ist eine Simulation.

Die "Zahlungen" tauchen auch im Stripe Dashboard auf, damit du siehst, wie das später aussieht:
**[Stripe Dashboard (Testmodus)](https://dashboard.stripe.com/acct_1TGdIDJidBPs4UgF/test/dashboard)**

### Gültige Testkarte (Zahlung erfolgreich)

| Feld | Wert |
|------|------|
| Kartennummer | `4242 4242 4242 4242` |
| Ablaufdatum | Beliebiges Datum in der Zukunft (z.B. `12/30`) |
| CVC | Beliebige 3 Ziffern (z.B. `123`) |
| Name | Beliebig |

### Ungültige Testkarte (Zahlung wird abgelehnt)

| Feld | Wert |
|------|------|
| Kartennummer | `4000 0000 0000 0002` |
| Rest | Wie oben (beliebig) |

### Twint im Testmodus

Twint wird auf der Stripe-Checkout-Seite als Zahlungsoption angezeigt. Im Testmodus kannst du Twint auswählen und die Testzahlung direkt bestätigen — es öffnet sich keine echte Twint-App.

## User Stories zum Durchtesten

Der vollständige Testplan mit 13 User Stories ist hier: [user-stories-testplan.md auf GitHub](https://github.com/konstantinniedermann/olivalle-webshop/blob/main/docs/user-stories-testplan.md)

**Empfohlene Reihenfolge:**

1. **Story 1** — Bestellung per QR-Rechnung (Versand)
2. **Story 2** — Bestellung per Stripe (Kreditkarte)
3. **Story 3** — Bestellung mit Abholung
4. **Story 4** — Gratisversand ab CHF 100
5. **Story 5** — Warenkorb bearbeiten
6. **Story 6** — Ungültige Eingaben testen
7. **Story 7–10** — Admin-Funktionen (braucht Testdaten aus Story 1–3)
8. **Story 11** — Stripe-Abbruch
9. **Story 12** — Infoseiten prüfen
10. **Story 13** — Auf dem Handy testen

> **Tipp:** Am besten Story 1–3 zuerst durchspielen. Dann hast du Testdaten im Admin für die weiteren Stories.
