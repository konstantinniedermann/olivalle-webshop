# User Stories — Manueller Testplan

> Zum manuellen Durchspielen in der laufenden App.
> Jeder Schritt hat eine Checkbox zum Abhaken.

---

## Story 1: Bestellung per QR-Rechnung (Versand)

**Als** Kunde möchte ich Olivenöl bestellen und per Rechnung bezahlen, damit ich per Banküberweisung zahlen kann.

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| [ ] 1 | Startseite `/` öffnen | 4 Produkte werden angezeigt (250ml, 500ml, 750ml, 3L) mit Preisen |
| [ ] 2 | 1x 750ml und 2x 3L in den Warenkorb legen | Kurze "Hinzugefügt"-Bestätigung, Warenkorb-Zähler zeigt 3 |
| [ ] 3 | Mini-Flyout im Header prüfen | Zeigt die hinzugefügten Produkte an |
| [ ] 4 | Warenkorb-Seite `/warenkorb` öffnen | 750ml (CHF 18), 3L x2 (CHF 100), Zwischensumme CHF 118 |
| [ ] 5 | Versandkosten prüfen | Gratis (ab CHF 100) |
| [ ] 6 | "Zur Kasse" klicken | Checkout-Formular erscheint |
| [ ] 7 | Kundendaten eingeben (Vorname, Nachname, E-Mail, Strasse, Hausnummer, PLZ, Ort) | Felder werden akzeptiert |
| [ ] 8 | Versandart: **Postversand** wählen | Versand ausgewählt |
| [ ] 9 | Zahlungsart: **Rechnung** wählen | Rechnung ausgewählt |
| [ ] 10 | Bestellung abschicken | Bestätigungsseite erscheint |
| [ ] 11 | E-Mail-Postfach prüfen | Bestellbestätigung mit QR-Rechnung als Anhang (SVG) |
| [ ] 12 | Admin: Login unter `/admin/login` | Dashboard öffnet sich |
| [ ] 13 | Admin: Neue Bestellung in der Liste finden | Status "neu", korrekte Artikel und Totale |
| [ ] 14 | Admin: Bestelldetail öffnen | Kundendaten, Positionen, Zahlungsart "Rechnung" sichtbar |
| [ ] 15 | Admin: Status auf **"bezahlt"** ändern | Status wird aktualisiert, Log-Eintrag erstellt |
| [ ] 16 | Kunde: E-Mail prüfen | Zahlungseingangsbestätigung erhalten |
| [ ] 17 | Admin: Status auf **"versendet"** ändern | Status wird aktualisiert |
| [ ] 18 | Kunde: E-Mail prüfen | Versandbestätigung erhalten |
| [ ] 19 | Admin: Status auf **"abgeschlossen"** ändern | Status wird aktualisiert |

---

## Story 2: Bestellung per Stripe (Kreditkarte/Twint) mit Versand

**Als** Kunde möchte ich online mit Twint oder Kreditkarte bezahlen, damit die Zahlung sofort verarbeitet wird.

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| [ ] 1 | 1x 250ml in den Warenkorb legen | Warenkorb-Zähler zeigt 1 |
| [ ] 2 | Warenkorb öffnen | 250ml (CHF 8), Versandkosten CHF 9.90, Total CHF 17.90 |
| [ ] 3 | Zur Kasse gehen, Kundendaten ausfüllen | Formular akzeptiert Eingaben |
| [ ] 4 | Versandart: **Postversand** | Versand ausgewählt |
| [ ] 5 | Zahlungsart: **Stripe (Twint/Kreditkarte)** | Stripe ausgewählt |
| [ ] 6 | Bestellung abschicken | Weiterleitung zu Stripe Checkout |
| [ ] 7 | Bei Stripe mit Testkarte bezahlen (4242 4242 4242 4242) | Zahlung erfolgreich |
| [ ] 8 | Zurück zur Bestätigungsseite `/bestaetigung` | Bestellung bestätigt |
| [ ] 9 | E-Mail prüfen | Bestellbestätigung erhalten (ohne QR-Rechnung) |
| [ ] 10 | Admin: Bestellung prüfen | Status automatisch "bezahlt" (via Webhook) |
| [ ] 11 | Admin: Status auf **"versendet"** ändern | Versandbestätigung-E-Mail wird ausgelöst |
| [ ] 12 | Kunde: E-Mail prüfen | Versandbestätigung erhalten |

---

## Story 3: Bestellung mit Abholung und QR-Rechnung

**Als** Kunde möchte ich die Ware vor Ort abholen, damit ich keine Versandkosten zahle.

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| [ ] 1 | 1x 750ml in den Warenkorb | Warenkorb-Zähler zeigt 1 |
| [ ] 2 | Warenkorb öffnen | 750ml (CHF 18), Versandkosten CHF 0 (Abholung) |
| [ ] 3 | Checkout: Daten ausfüllen | OK |
| [ ] 4 | Versandart: **Abholung** | Versandkosten entfallen |
| [ ] 5 | Zahlungsart: **Rechnung** | OK |
| [ ] 6 | Bestellung abschicken | Bestätigungsseite erscheint |
| [ ] 7 | E-Mail prüfen | Bestellbestätigung mit QR-Rechnung |
| [ ] 8 | Admin: Bestellung prüfen | Versandart "Abholung", Versandkosten CHF 0 |
| [ ] 9 | Admin: Status auf **"bezahlt"** ändern | Zahlungseingangs-E-Mail an Kunden |
| [ ] 10 | Admin: Status auf **"abholbereit"** ändern | E-Mail "Abholbereit" mit Abholadresse (Hegibergstrasse 98, Trimbach) |
| [ ] 11 | Kunde: E-Mail prüfen | Abholbereit-Bestätigung mit Adresse und Hinweis, Abholzeit per Mail zu vereinbaren |

---

## Story 3b: Bestellung mit Bezahlung bei Abholung (bar)

**Als** Kunde möchte ich bei Abholung in der Region Olten bar bezahlen können, ohne online eine Zahlung abzuschliessen.

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| [ ] 1 | 1x 3L-Kanister in den Warenkorb | Warenkorb-Zähler zeigt 1 |
| [ ] 2 | Warenkorb öffnen | 3L (CHF 50), Versandkosten CHF 9.90 |
| [ ] 3 | Checkout: Daten ausfüllen | OK |
| [ ] 4 | Versandart: **Abholung in der Region Olten** wählen | Versandkosten entfallen, "Bezahlung bei Abholung" erscheint und ist vorausgewählt |
| [ ] 5 | Prüfen: andere Zahlungsarten (Stripe, Rechnung) bleiben wählbar | Alle 3 Optionen sichtbar |
| [ ] 6 | Versandart zurück auf **Postversand** wechseln | "Bezahlung bei Abholung" verschwindet, Stripe ist gewählt |
| [ ] 7 | Versandart wieder auf **Abholung** wählen | "Bezahlung bei Abholung" erscheint erneut und ist vorausgewählt |
| [ ] 8 | Bestellung mit "Bezahlung bei Abholung" abschicken | Bestätigungsseite: "Nadine & Sandro melden sich bei dir für einen Abholtermin" |
| [ ] 9 | Kunde: E-Mail prüfen | Bestellbestätigung mit Abholhinweis + Stornierungsinfo (olivalle.olten@outlook.com) |
| [ ] 10 | Stakeholder: E-Mail prüfen | Benachrichtigung mit Bestelldetails + "Aktion nötig: Kontaktiere den Kunden für Abholtermin" |
| [ ] 11 | Admin: Bestellung im Dashboard | Status "neu", Zahlungsart "Bar bei Abholung" |
| [ ] 12 | Admin: Bestelldetail öffnen | Prozess-Leiste zeigt: neu → in_bearbeitung → abholbereit → bezahlt → abgeschlossen |
| [ ] 13 | Admin: Status auf **"abholbereit"** ändern | Status aktualisiert, Kunde erhält Abholbereit-E-Mail mit Adresse |
| [ ] 14 | Admin: Status auf **"bezahlt"** ändern (Bar-Zahlung erhalten) | Status aktualisiert, Kunde erhält Zahlungseingangsbestätigung |
| [ ] 15 | Admin: Status auf **"abgeschlossen"** ändern | Bestellung abgeschlossen |

---

## Story 4: Gratisversand-Schwelle

**Als** Kunde möchte ich ab CHF 100 gratis Versand erhalten.

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| [ ] 1 | 1x 3L-Kanister (CHF 50) in den Warenkorb | Subtotal CHF 50 |
| [ ] 2 | Warenkorb öffnen | Versandkosten: CHF 9.90, Total: CHF 59.90 |
| [ ] 3 | Menge auf 2 erhöhen (+ Button) | Subtotal CHF 100, Versandkosten: **gratis**, Total: CHF 100 |
| [ ] 4 | Menge auf 1 zurücksetzen (- Button) | Versandkosten: CHF 9.90 zurück |
| [ ] 5 | 5x 250ml hinzufügen (CHF 40) + 1x 3L (CHF 50) = CHF 90 | Versandkosten: CHF 9.90 |
| [ ] 6 | 1x 250ml mehr → Total CHF 98 | Versandkosten: CHF 9.90 |
| [ ] 7 | Noch 1x 250ml → Total CHF 106 | Versandkosten: **gratis** |

---

## Story 5: Warenkorb-Verwaltung

**Als** Kunde möchte ich meinen Warenkorb bearbeiten können, bevor ich bestelle.

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| [ ] 1 | Alle 3 Produkte in den Warenkorb legen | Zähler zeigt 3 |
| [ ] 2 | Warenkorb öffnen | Alle 3 Produkte aufgelistet |
| [ ] 3 | Menge von 250ml auf 5 erhöhen (+ klicken) | Menge 5, Zwischenpreis aktualisiert |
| [ ] 4 | 750ml entfernen (Entfernen-Button) | Nur noch 250ml und 3L im Warenkorb |
| [ ] 5 | Seite neu laden (F5) | Warenkorb bleibt erhalten (localStorage) |
| [ ] 6 | Menge auf 1 verringern, dann nochmal - drücken | Produkt wird entfernt (Minimum ist 1) oder bleibt bei 1 |
| [ ] 7 | Alle Produkte entfernen | Leerer Warenkorb, Hinweis "Warenkorb ist leer" |

---

## Story 6: Checkout-Validierung

**Als** System möchte ich ungültige Eingaben abfangen, damit keine fehlerhaften Bestellungen entstehen.

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| [ ] 1 | Checkout ohne Warenkorb aufrufen | Hinweis oder Redirect (leerer Warenkorb) |
| [ ] 2 | Formular ohne Pflichtfelder abschicken | Browser-Validierung verhindert Absenden |
| [ ] 3 | PLZ mit 3 Stellen eingeben (z.B. "123") | Validierungsfehler (muss 4-stellig sein) |
| [ ] 4 | PLZ mit 5 Stellen eingeben (z.B. "12345") | Validierungsfehler |
| [ ] 5 | Ungültige E-Mail eingeben (z.B. "test@") | Validierungsfehler |
| [ ] 6 | Gültige Daten eingeben, Bestellung abschicken | Bestellung wird korrekt erstellt |

---

## Story 7: Admin-Dashboard und Filterfunktionen

**Als** Admin möchte ich Bestellungen filtern und durchsuchen, damit ich den Überblick behalte.

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| [ ] 1 | Admin-Login mit korrektem Passwort | Dashboard mit Statistiken (offene Bestellungen, Monatsumsatz, heutige Bestellungen) |
| [ ] 2 | Statistik-Kacheln prüfen | Zahlen stimmen mit der Bestellliste überein |
| [ ] 3 | Filter: Status "neu" | Nur Bestellungen mit Status "neu" angezeigt |
| [ ] 4 | Filter: Datumsbereich von heute bis heute | Nur heutige Bestellungen |
| [ ] 5 | Suche: Kundenname eingeben | Treffer für den gesuchten Kunden |
| [ ] 6 | Suche: Bestell-ID eingeben | Bestellung wird gefunden |
| [ ] 7 | Auf eine Bestellung klicken | Detail-Ansicht öffnet sich |

---

## Story 8: Admin-Notizen und Aktivitätslog

**Als** Admin möchte ich Notizen zu Bestellungen hinterlegen und alle Aktivitäten nachvollziehen können.

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| [ ] 1 | Bestelldetail öffnen | Aktivitätslog sichtbar (mindestens Bestelleingang) |
| [ ] 2 | Notiz hinzufügen: "Kunde hat angerufen, Lieferung auf nächste Woche verschoben" | Notiz erscheint im Aktivitätslog mit Zeitstempel |
| [ ] 3 | Status ändern (z.B. "neu" → "bezahlt") | Statusänderung im Log dokumentiert |
| [ ] 4 | Nochmals Status ändern | Alle Änderungen chronologisch im Log |
| [ ] 5 | Typ "E-Mail eingegangen" als Notiz-Typ wählen | Notiz mit korrektem Typ gespeichert |

---

## Story 9: Admin-Login Sicherheit

**Als** System möchte ich den Admin-Bereich vor unbefugtem Zugriff schützen.

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| [ ] 1 | `/admin/` ohne Login aufrufen | Redirect zu `/admin/login` |
| [ ] 2 | Falsches Passwort eingeben | Fehlermeldung, kein Zugang |
| [ ] 3 | Mehrfach falsches Passwort (5+ Versuche) | Rate-Limiting greift, temporäre Sperre |
| [ ] 4 | Korrektes Passwort eingeben | Dashboard öffnet sich |
| [ ] 5 | Logout klicken | Session beendet, zurück zu Login |
| [ ] 6 | Browser-Zurück-Button nach Logout | Kein Zugriff auf Admin, erneut Login nötig |

---

## Story 10: Bestellung stornieren

**Als** Admin möchte ich eine Bestellung stornieren können.

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| [ ] 1 | Bestelldetail einer neuen Bestellung öffnen | Status "neu" |
| [ ] 2 | Status auf **"storniert"** ändern | Status wird aktualisiert |
| [ ] 3 | Dashboard-Statistik prüfen | Stornierte Bestellung wird NICHT im Monatsumsatz gezählt |
| [ ] 4 | Filter: Status "storniert" | Stornierte Bestellung erscheint |

---

## Story 11: Stripe-Zahlung abbrechen oder fehlgeschlagen

**Als** Shopbetreiber möchte ich, dass abgebrochene oder fehlgeschlagene Stripe-Zahlungen automatisch als storniert markiert werden, damit keine Geister-Bestellungen im Dashboard erscheinen.

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| [ ] 1 | Bestellung mit Stripe-Zahlung starten | Weiterleitung zu Stripe Checkout |
| [ ] 2 | Bei Stripe auf "Zurück" klicken oder Browser schliessen | Keine Bestätigung |
| [ ] 3 | Admin: Bestellung prüfen (nach Session-Ablauf, max. 24h) | Status **"storniert"**, Log-Eintrag mit Begründung |
| [ ] 4 | Bestellung mit ungültiger Kreditkarte versuchen | Zahlung wird abgelehnt |
| [ ] 5 | Admin: Bestellung prüfen | Status **"storniert"**, Log-Eintrag "Zahlung fehlgeschlagen" |
| [ ] 6 | Dashboard-Statistik prüfen | Stornierte Bestellungen werden NICHT als "offene Bestellungen" gezählt |

---

## Story 12: Informationsseiten

**Als** Besucher möchte ich die rechtlichen und informativen Seiten einsehen können.

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| [ ] 1 | `/ueber-das-oel` aufrufen | Seite "Über das Öl" wird angezeigt |
| [ ] 2 | `/impressum` aufrufen | Impressum mit Kontaktdaten |
| [ ] 3 | `/datenschutz` aufrufen | Datenschutzerklärung |
| [ ] 4 | `/agb` aufrufen | AGB angezeigt |
| [ ] 5 | Links im Footer prüfen | Alle 4 Seiten sind verlinkt und erreichbar |

---

## Story 13: Responsive Design (Mobile)

**Als** Kunde möchte ich den Shop auch auf dem Handy benutzen können.

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| [ ] 1 | Startseite auf Mobile öffnen (oder DevTools Responsive) | Produkte untereinander (1 Spalte), kein horizontales Scrollen |
| [ ] 2 | Header/Navigation prüfen | Navigierbar, Warenkorb-Icon sichtbar |
| [ ] 3 | Warenkorb auf Mobile | Produkte lesbar, +/- Buttons bedienbar |
| [ ] 4 | Checkout-Formular auf Mobile | Felder voll ausfüllbar, kein Overflow |
| [ ] 5 | Admin-Dashboard auf Mobile | Tabelle lesbar oder scrollbar |

---

## Story 14: Rabattcodes

**Als** Kunde möchte ich einen Rabattcode beim Checkout eingeben, damit ich einen Preisnachlass erhalte.

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| [ ] 1 | Admin: `/admin/rabattcodes` aufrufen | Übersicht aller Rabattcodes |
| [ ] 2 | Admin: Neuen Code erstellen (z.B. "SOMMER10", 10%, unbegrenzt, kein Ablaufdatum) | Code erscheint in der Liste |
| [ ] 3 | Admin: Neuen Code erstellen (z.B. "FEST5", CHF 5 Fixbetrag, 1 Einlösung, min. CHF 20) | Code erscheint in der Liste |
| [ ] 4 | Checkout: Produkte in den Warenkorb legen (z.B. 1x 750ml = CHF 18) | Warenkorb korrekt |
| [ ] 5 | Checkout: Rabattcode "SOMMER10" eingeben und bestätigen | Rabatt von CHF 1.80 wird abgezogen, Total aktualisiert |
| [ ] 6 | Checkout: Rabatt im Totale prüfen | Anzeige "Rabatt (SOMMER10): -CHF 1.80", Total CHF 16.20 |
| [ ] 7 | Checkout: Ablaufdatum-Code testen (abgelaufener Code) | Fehlermeldung "Code abgelaufen" |
| [ ] 8 | Checkout: Bereits erschöpften Code testen (Einlösungen aufgebraucht) | Fehlermeldung "Code nicht mehr gültig" |
| [ ] 9 | Checkout: Code testen, der die Mindestbestellmenge nicht erfüllt | Fehlermeldung mit Mindestbetrag |
| [ ] 10 | Checkout: Gleichen Code zweimal mit gleicher E-Mail einlösen | Fehlermeldung "Code wurde von dieser E-Mail-Adresse bereits verwendet" |
| [ ] 11 | Bestellung abschicken (mit Code "SOMMER10") | Bestätigungsseite zeigt Rabatt |
| [ ] 12 | E-Mail prüfen | Bestellbestätigung enthält Rabattzeile (Code + Betrag) |
| [ ] 13 | 5-Rappen-Rundung prüfen (z.B. 10% auf CHF 18 = CHF 1.80 → Total CHF 16.20) | Total auf 5 Rappen gerundet (CHF 16.20) |
| [ ] 14 | Zweiten Code "FEST5" bei einer Bestellung versuchen (nach "SOMMER10") | Fehlermeldung "Pro Bestellung nur ein Code erlaubt" |
| [ ] 15 | Admin: Code "SOMMER10" in der Übersicht prüfen | Anzahl Einlösungen wurde erhöht |
| [ ] 16 | Checkout: Eingelösten Code über "Entfernen" wieder entfernen | Rabatt verschwindet, Total zurück auf Originalpreis, Eingabefeld wieder editierbar, Button zeigt "Einlösen" |
| [ ] 17 | Checkout: Nach dem Entfernen denselben Code erneut eingeben und einlösen | Rabatt wird erneut korrekt angewendet (kein hängender/gesperrter Zustand) |

---

## Story 15: Aktionspreise

**Als** Shopbetreiber möchte ich einem Produkt einen befristeten Aktionspreis mit Begründungstext geben, damit ich zeitlich begrenzte Angebote anbieten kann, ohne manuell eingreifen zu müssen.

| Schritt | Aktion | Erwartetes Ergebnis |
|---------|--------|---------------------|
| [ ] 1 | Admin: `/admin/produkte` aufrufen | Produktliste mit "Aktionspreis setzen"-Formular je Produkt |
| [ ] 2 | Admin: Für 250ml Flasche Aktionspreis CHF 6, Text "Frühlingsaktion", Zeitraum heute bis in 7 Tagen setzen | Erfolgsmeldung, Audit-Log-Eintrag sichtbar |
| [ ] 3 | Startseite `/` aufrufen | 250ml-Karte zeigt: RABATT-Badge; obere Preiszeile = durchgestrichener Originalpreis CHF 8 + –25%-Badge; darunter Aktionspreis CHF 6 (gross, als Resultat); Text "Frühlingsaktion" |
| [ ] 4 | Warenkorb: 1x 250ml hinzufügen und Warenkorb öffnen | Einzelpreis CHF 6 (nicht CHF 8), Summe korrekt |
| [ ] 5 | Checkout: Bestellung mit Aktionsprodukt abschicken (QR-Rechnung) | Bestätigungsseite zeigt CHF 6 pro 250ml |
| [ ] 6 | E-Mail prüfen | Bestellbestätigung und QR-Rechnung enthalten Aktionspreis CHF 6 |
| [ ] 7 | Admin: Bestelldetail prüfen | Bestellposition zeigt Einzelpreis CHF 6 |
| [ ] 8 | Warenkorb: 1x 250ml (CHF 6, Aktionsartikel) + 1x 750ml (CHF 18, normal) | Rabattfähiger Subtotal = CHF 18 (nur 750ml) |
| [ ] 9 | Checkout: Rabattcode (z. B. "SOMMER10", 10%) eingeben | Rabatt 10% auf CHF 18 = CHF 1.80; Aktionsartikel nicht rabattiert |
| [ ] 10 | Checkout: Warenkorb nur mit Aktionsartikel (1x 250ml) und Rabattcode eingeben | Fehlermeldung "Code gilt nicht für Aktionsartikel" (oder sinngemäss) |
| [ ] 11 | Admin: Aktionspreis entfernen | Produktkarte zeigt wieder Normalpreis CHF 8, kein Badge |
| [ ] 12 | Admin: Aktionspreis mit `aktion_bis` = gestern setzen (abgelaufene Aktion) | Produktkarte zeigt sofort Normalpreis — Aktion automatisch abgelaufen |
| [ ] 13 | Admin: Aktionspreis setzen, danach App neu deployen/neustarten (simuliert fly.io-Neustart) | Aktion ist nach dem Neustart **weiterhin gesetzt** — der Seed überschreibt sie nicht (Bug #137; automatisch abgedeckt durch `tests/test_seed_aktion_persistenz.py`) |

---

## Hinweise zum Testen

- **Stripe-Testkarte:** `4242 4242 4242 4242`, beliebiges Ablaufdatum in der Zukunft, beliebige CVC
- **Stripe-Testkarte abgelehnt:** `4000 0000 0000 0002`
- **E-Mails:** Kommen nur an wenn Brevo konfiguriert ist — sonst im Server-Log prüfen
- **Admin-Passwort:** Steht in `.env` als `ADMIN_PASSWORD`
- **Reihenfolge:** Am besten Story 1-3 zuerst, damit für Story 7-8 bereits Testdaten vorhanden sind
