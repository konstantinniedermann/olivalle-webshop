# E-Mail-Versand: Evaluation Alternativen zu Resend

**Datum:** 01.04.2026
**Anlass:** Stakeholder-Anfrage nach EU-basierter Alternative

---

## Ausgangslage

Für den Olivalle-Webshop brauchen wir einen E-Mail-Dienst, der automatisch Bestellbestätigungen und Rechnungen an Kunden verschickt. Bisher war **Resend** (USA) vorgesehen. Der Stakeholder wünscht eine Alternative mit **Datenstandort in der EU**, um dem Schweizer Datenschutzgesetz (DSG) besser gerecht zu werden.

**Geschätztes Volumen:** ca. 100 Bestellungen/Monat = ca. 200–400 E-Mails/Monat.

---

## Verglichene Anbieter

| | **Lettermint** | **Brevo** (ex-Sendinblue) | **Mailjet** | **Resend** (bisherig) |
|---|---|---|---|---|
| **Firmensitz** | EU | Frankreich | Frankreich | USA |
| **Datenstandort** | EU/EWR (explizit keine Daten ausserhalb) | EU | EU | USA |
| **Gratis-Kontingent** | 300 E-Mails/Mt | 9'000 E-Mails/Mt | 6'000 E-Mails/Mt | 3'000 E-Mails/Mt |
| **Nächstes Abo** | €10/Mt (10'000 E-Mails) | €9/Mt (5'000+) | €17/Mt (15'000) | $20/Mt (50'000) |
| **Kosten bei unserem Volumen** | CHF 0 (knapp) | CHF 0 | CHF 0 | CHF 0 |
| **E-Mail-Vorlagen** | Im Code | Im Browser bearbeitbar | Im Browser bearbeitbar | Im Code |
| **Newsletter-Funktion** | Nein | Ja, inklusive | Ja, inklusive | Nein |
| **Technische Anbindung** | Sehr gut (async Python SDK) | Gut (sync Python SDK) | Gut (sync Python SDK) | Sehr gut (Python SDK) |

---

## Gegenüberstellung: Lettermint vs. Brevo

Die beiden stärksten EU-Kandidaten im direkten Vergleich:

### Lettermint

**Vorteile:**

- **Strikte EU-Datenhaltung** — keine Daten ausserhalb EU/EWR, DSGVO als Kernversprechen
- **Fokussierter Dienst** — nur Transaktions-Mails, keine unnötige Komplexität
- **Moderne Technik** — async-fähiges Python SDK, passt optimal zu unserem Tech-Stack (FastAPI)
- **Startup-Rabatt** — €60 Guthaben verfügbar (entspricht 6 Monaten Starter-Plan)

**Nachteile:**

- **Kleines Gratis-Kontingent** — 300 E-Mails/Mt reicht nur knapp bei ~100 Bestellungen (Bestätigung + Rechnung = 2 Mails pro Bestellung). Bei Wachstum wird das kostenpflichtige Abo nötig (€10/Mt)
- **Jüngerer Anbieter** — weniger Erfahrungswerte am Markt als Brevo
- **Keine Newsletter-Funktion** — falls später ein Newsletter gewünscht wird, braucht es einen zweiten Dienst
- **Vorlagen nur im Code** — E-Mail-Texte können nicht ohne Entwickler angepasst werden

### Brevo

**Vorteile:**

- **Sehr grosszügiges Gratis-Kontingent** — 9'000 E-Mails/Mt, mehr als genug Spielraum
- **Newsletter inklusive** — falls Olivalle später Kunden informieren will (neue Ernte, Angebote)
- **E-Mail-Vorlagen im Browser** — der Inhaber kann Texte selbst anpassen
- **Etablierter Anbieter** — seit 2012 am Markt, über 500'000 Kunden

**Nachteile:**

- **Grössere Plattform** — viele Funktionen die wir nicht brauchen, Oberfläche etwas unübersichtlicher
- **Brevo-Logo im Footer** bei Gratis-Konto — entfernbar ab €9/Mt
- **Synchrones Python SDK** — funktioniert, ist aber technisch weniger elegant für unseren Stack

---

## Empfehlung

Beide Anbieter erfüllen die Anforderung nach EU-Datenstandort und funktionieren für Olivalle.

**Lettermint** ist die bessere Wahl wenn:

- EU-Datenhaltung höchste Priorität hat
- Der Dienst schlank und fokussiert sein soll
- Bei Wachstum ein kleines Budget (€10/Mt) akzeptabel ist

**Brevo** ist die bessere Wahl wenn:

- Kosten auf absehbare Zeit bei CHF 0 bleiben sollen
- Newsletter eine Option für die Zukunft sind
- Der Inhaber E-Mail-Texte selbst anpassen möchte

## Entscheid (01.04.2026)

**Brevo** wird als E-Mail-Provider eingesetzt. Die Entscheidung fiel auf Basis von drei Abwägungen:

1. **Pro DSG / gegen Resend:** Resend speichert Daten in den USA. Brevo speichert alle Daten in der EU (Frankreich) — besser für die Einhaltung des Schweizer Datenschutzgesetzes.

2. **Pro Datenvolumen und Newsletter / gegen Lettermint:** Lettermint hat nur 300 E-Mails/Mt im Free Tier (knapp für ~100 Bestellungen). Brevo bietet 9'000/Mt und eine integrierte Newsletter-Funktion, die für Olivalle künftig nützlich sein könnte.

3. **Trotz async Python SDK:** Lettermint bietet ein async-fähiges Python SDK, das technisch besser zu FastAPI passt als Brevo's synchrones SDK. Bei Olivalle's Volumen (~100 Bestellungen/Mt) ist dieser Unterschied jedoch vernachlässigbar. Die praktischen Vorteile von Brevo (Volumen, Newsletter, bearbeitbare Vorlagen) überwiegen.

Detaillierte Entscheidungsdokumentation: [adr-email-provider.md](../adr-email-provider.md)
