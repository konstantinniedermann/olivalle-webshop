# Manuelles Testprotokoll — Olivalle Webshop

> Dieses Protokoll dient als Checkliste für manuelle Browser-Tests vor dem Go-Live.
> Stripe Test-Keys verwenden (Dashboard → Developers → Test mode).

## Voraussetzungen

- [ ] Server läuft lokal (`make dev`)
- [ ] Stripe Test-Keys konfiguriert in `.env`
- [ ] Resend API-Key konfiguriert (oder Resend Dashboard offen zum Prüfen)
- [ ] Stripe Webhook lokal weiterleiten (`stripe listen --forward-to localhost:8000/webhook/stripe`)

---

## 1. Stripe-Flow

### Bestellung aufgeben
- [ ] Startseite öffnen → Produkte werden angezeigt
- [ ] Produkt in Warenkorb legen → Warenkorb-Icon zeigt Anzahl
- [ ] Weiteres Produkt hinzufügen, Menge ändern
- [ ] Warenkorb öffnen → Produkte, Mengen und Preise stimmen
- [ ] "Zur Kasse" klicken → Checkout-Seite öffnet sich
- [ ] Kundendaten eingeben (alle Pflichtfelder)
- [ ] Versandart "Postversand" wählen
- [ ] Zahlungsart "Kreditkarte / Twint" wählen
- [ ] Bestellung absenden → Weiterleitung zu Stripe

### Stripe-Zahlung
- [ ] Stripe Checkout zeigt korrekte Produkte und Beträge
- [ ] Mit Testkarte bezahlen: `4242 4242 4242 4242`, Ablauf beliebig, CVC beliebig
- [ ] Nach Zahlung: Bestätigungsseite mit Bestellnummer wird angezeigt

### E-Mail-Bestätigung
- [ ] Bestätigungs-E-Mail erhalten (Resend Dashboard prüfen)
- [ ] E-Mail enthält: Bestellnummer, Produkte, Mengen, Preise, Total
- [ ] Absender: `bestellung@olivalle.ch`

### Admin-Prüfung
- [ ] Admin-Login → Dashboard
- [ ] Bestellung mit Status "bezahlt" sichtbar
- [ ] Bestelldetail öffnen → Positionen, Kundendaten, Total stimmen
- [ ] Log zeigt: "status_geaendert" von "neu" nach "bezahlt"

---

## 2. Rechnungs-Flow

### Bestellung aufgeben
- [ ] Produkt in Warenkorb legen
- [ ] Checkout: Versandart "Abholung vor Ort" wählen
- [ ] Zahlungsart "Rechnung" wählen
- [ ] Bestellung absenden → Bestätigungsseite direkt angezeigt

### E-Mail mit QR-Rechnung
- [ ] Bestätigungs-E-Mail erhalten
- [ ] E-Mail enthält QR-Rechnung als Anhang (SVG)
- [ ] QR-Code ist scannbar (z.B. mit Banking-App im Testmodus)

### Admin-Prüfung
- [ ] Bestellung im Dashboard mit Status "neu" sichtbar
- [ ] Status manuell auf "bezahlt" ändern → Log-Eintrag erstellt
- [ ] Status auf "abholbereit" ändern → Log-Eintrag erstellt

---

## 3. Admin-Aktionen

### Login / Logout
- [ ] Admin-Login-Seite erreichbar unter `/admin/login`
- [ ] Login mit korrektem Passwort → Dashboard
- [ ] Logout → zurück zur Login-Seite
- [ ] Dashboard nicht erreichbar ohne Login

### Bestellverwaltung
- [ ] Bestellungen nach Status filtern
- [ ] Bestellungen nach Kundenname suchen
- [ ] Bestelldetail öffnen → alle Infos korrekt
- [ ] Notiz hinzufügen → erscheint im Aktivitäts-Log
- [ ] Mehrere Statusänderungen → alle im Log sichtbar

---

## 4. Fehlerfälle

- [ ] Leeren Warenkorb bestellen → Fehlermeldung "Warenkorb ist leer"
- [ ] Checkout ohne Pflichtfelder absenden → Validierungsfehler
- [ ] Admin-Login mit falschem Passwort → "Ungültiges Passwort"
- [ ] Nicht existierende Bestellung öffnen (`/admin/bestellungen/99999`) → 404
- [ ] Stripe-Zahlung abbrechen (zurück-Button) → Bestellung bleibt "neu"

---

## 5. Storno

- [ ] Bestellung über Stripe aufgeben und bezahlen
- [ ] Admin: Status auf "storniert" ändern
- [ ] Log zeigt Verlauf: neu → bezahlt → storniert
- [ ] (Stripe-Refund manuell im Stripe Dashboard durchführen)

---

## Testergebnis

| Datum | Tester | Ergebnis | Anmerkungen |
|-------|--------|----------|-------------|
| | | | |
