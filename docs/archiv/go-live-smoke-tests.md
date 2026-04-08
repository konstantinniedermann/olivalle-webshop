# Go-Live Smoke-Tests (Issue #67)

Finaler End-to-End-Test auf der Produktiv-Domain `https://olivalle.ch` vor dem offiziellen Launch.

## Stripe-Zugriff klären

- **Entwickler kann:** Bestellungen/Zahlungen sehen, Webhooks prüfen, Logs lesen, Test-Zahlungen refundieren — sofern die Stripe-Rolle "Developer" oder "Administrator" ist (bei "Read only" nicht).
- **Nur Stakeholder kann:** Bankkonto/Auszahlungen, Account-Verifizierung, Steuerangaben, neue Zahlungsmethoden freischalten (z. B. TWINT, siehe #68).
- **Vor dem Smoke-Test:** Im Stripe-Dashboard prüfen, ob der Refund-Button sichtbar ist. Falls nicht -> SH muss refunden oder kurz Admin-Rechte geben.

## Vorbereitung

- [ ] Stripe Dashboard offen (Live-Modus), Refund-Rechte verifiziert
- [ ] Brevo Dashboard offen (E-Mail-Logs)
- [ ] `fly logs -a olivalle` offen
- [ ] Eigene E-Mail-Adresse als Testkunde
- [ ] **Hinweis:** TWINT ist noch nicht aktiv (siehe #68) — wird in diesem Smoke-Test nicht getestet

## Durchgang 1 — Kreditkarte + Postversand

- [ ] olivalle.ch öffnen, SSL-Schloss prüfen
- [ ] 1× 250ml + 1× 750ml + 1× 3l in Warenkorb
- [ ] Checkout: Postversand wählen, Formular ausfüllen
- [ ] Bezahlen mit echter Kreditkarte
- [ ] Redirect auf Erfolgsseite
- [ ] Bestellbestätigungs-Mail empfangen
- [ ] QR-Rechnung im Mail-Anhang prüfen (IBAN, Betrag, Referenz)
- [ ] Stripe Dashboard: Zahlung sichtbar
- [ ] Admin-Bereich: Bestellung sichtbar mit korrektem Status

## Durchgang 2 — Kreditkarte + Abholung

- [ ] 1× 750ml in Warenkorb
- [ ] Checkout: Abholung Region Olten wählen
- [ ] Bezahlen mit Kreditkarte
- [ ] Erfolgsseite + Mail + Admin prüfen
- [ ] Versandkosten = CHF 0

## Edge-Cases

- [ ] Gratis-Versand ab CHF 100: 6× 750ml -> Versand sollte CHF 0 sein
- [ ] www.olivalle.ch -> Redirect auf olivalle.ch
- [ ] Mobile-Ansicht (Handy) durchklicken
- [ ] Checkout zeigt **TWINT NICHT** an (erst nach #68)

## Aufräumen

- [ ] Alle Test-Bestellungen in Stripe refundieren
- [ ] Test-Bestellungen im Admin markieren/löschen (falls nötig)

## Stakeholder-Freigabe

- [ ] Mail an SH senden (Vorlage unten)
- [ ] Freigabe schriftlich erhalten
- [ ] Issue #67 schliessen, #49 prüfen

---

## Stakeholder-Mail (Vorlage)

> **Betreff:** Olivalle-Webshop bereit zum Launch — deine Freigabe
>
> Hoi [Name],
>
> der Webshop läuft jetzt live unter **https://olivalle.ch**. Ich habe heute alle End-to-End-Tests durchgespielt:
>
> - Bestellung mit Kreditkarte + Postversand
> - Bestellung mit Kreditkarte + Abholung
> - Bestellbestätigung per E-Mail mit QR-Rechnung
> - Zahlungen im Stripe-Dashboard sichtbar
> - Bestellungen im Admin-Bereich sichtbar
>
> Die Test-Zahlungen habe ich anschliessend refundiert.
>
> **Hinweis TWINT:** TWINT ist im Stripe-Account aktuell noch nicht freigeschaltet (Stripe hat die Aktivierung abgelehnt, vermutlich fehlen noch Verifizierungsdaten). Der Launch kann trotzdem erfolgen — Kreditkarte funktioniert. TWINT reichen wir nach, sobald Stripe es freigibt (offenes Ticket #68).
>
> **Bitte schau dir den Shop in Ruhe an** und gib mir Bescheid, sobald du grünes Licht für den offiziellen Launch gibst. Konkret bitte prüfen:
>
> 1. Produkte, Preise, Texte korrekt?
> 2. Checkout-Ablauf verständlich?
> 3. Bestellbestätigungs-Mail in Ordnung? (gib gerne eine Test-Bestellung auf — ich refundiere sie)
> 4. Admin-Zugang funktioniert?
>
> Sobald dein OK kommt, kommunizieren wir den Launch.
>
> Liebe Grüsse
> Konstantin
