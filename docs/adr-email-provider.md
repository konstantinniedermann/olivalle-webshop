# ADR: E-Mail-Provider — Brevo statt Resend

**Status:** Entschieden (01.04.2026)
**Beteiligte:** Stakeholder (SH), Entwickler (KN)

## Kontext

Für den Olivalle-Webshop wird ein E-Mail-Dienst benötigt, der automatisch Bestellbestätigungen und Rechnungen verschickt. Ursprünglich war Resend (USA) vorgesehen. Der Stakeholder hat eine Alternative mit EU-Datenstandort angefragt.

## Evaluierte Optionen

| Option | Standort | Free Tier | Entscheidung |
|---|---|---|---|
| **Resend** | USA | 3'000/Mt | Verworfen — kein EU-Datenstandort |
| **Lettermint** | EU/EWR | 300/Mt | Verworfen — zu kleines Gratis-Kontingent, kein Newsletter |
| **Brevo** | Frankreich (EU) | 9'000/Mt | Gewählt |

Detaillierte Evaluation: [email-provider-evaluation.md](archiv/email-provider-evaluation.md)

## Entscheidung

**Brevo (ehemals Sendinblue)** als E-Mail-Provider.

### Entscheidungsfindung

Die Entscheidung fiel auf Basis von drei Abwägungen:

1. **Pro DSG / gegen Resend:** Resend speichert Daten in den USA. Für die Einhaltung des Schweizer Datenschutzgesetzes (DSG) ist ein EU-Datenstandort vorzuziehen. Brevo speichert alle Daten in der EU (Frankreich).

2. **Pro Datenvolumen und Newsletter / gegen Lettermint:** Lettermint bietet zwar eine striktere EU-Positionierung, hat aber nur 300 E-Mails/Mt im Free Tier (knapp für ~100 Bestellungen). Brevo bietet 9'000/Mt und eine integrierte Newsletter-Funktion, die für Olivalle künftig nützlich sein könnte (neue Ernte, Angebote).

3. **Trotz async Python SDK:** Lettermint bietet ein async-fähiges Python SDK, das besser zu FastAPI passt als Brevo's synchrones SDK. Dieser technische Vorteil wurde bewusst zugunsten der praktischen Vorteile (Volumen, Newsletter, Templates im Browser) in Kauf genommen. Bei Olivalle's Volumen (~100 Bestellungen/Mt) ist der Performance-Unterschied zwischen sync und async vernachlässigbar.

## Konsequenzen

- E-Mail-Service (`app/services/email_service.py`) muss auf Brevo SDK umgestellt werden
- `.env`-Variablen: `RESEND_API_KEY` → `BREVO_API_KEY`
- Alle Test-Mocks müssen angepasst werden
- DNS: SPF/DKIM-Einträge für Brevo statt Resend
- Datenschutzerklärung: Brevo (Frankreich/EU) statt Resend (USA)
- Brevo-Account muss eingerichtet werden (Phase 3)
