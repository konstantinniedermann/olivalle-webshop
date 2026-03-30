# ADR: Domain-Registrar für olivalle.ch

**Status:** Entschieden (2026-03-30)
**Kontext:** Domain-Transfer & Go-Live

## Ausgangslage

Die Domain olivalle.ch liegt beim bisherigen Administrator auf einem Hosttech-Account, der auch andere Domains enthält. Ein direkter Zugang zum Account ist daher nicht möglich. Für Go-Live brauchen wir DNS-Kontrolle (fly.io-Routing, Resend-Verifizierung, SSL).

## Entscheidung

**Domain zu Infomaniak transferieren** (via AuthCode von Hosttech).

## Evaluierte Optionen

| Kriterium | **Infomaniak** (Empfehlung) | Hostpoint | Hosttech (Status quo) | Cloudflare |
|---|---|---|---|---|
| **Sitz** | Genf, CH | Rapperswil, CH | Rapperswil, CH | USA |
| **.ch möglich?** | Ja | Ja | Ja | **Nein** |
| **Transfer-Kosten** | Gratis | Gratis | — | — |
| **Preis 1. Jahr** | ~CHF 5 (Aktion) | CHF 5 (Aktion) | CHF 10.70 | — |
| **Preis ab 2. Jahr** | ~CHF 10–12 | CHF 15 | CHF 10.70 | — |
| **DNS-Verwaltung** | Gratis inkl. | Gratis inkl. | Gratis inkl. | — |
| **DNSSEC** | Gratis (manuell aktivieren) | Gratis (automatisch) | Gratis | — |
| **E-Mail-Weiterleitung** | 1 Gratis-Mailbox inkl. | Nur mit Hosting-Paket | Nur mit Hosting-Paket | — |
| **Interface-Sprache** | DE / FR / IT / EN | DE / FR / IT / EN | DE / FR / IT / EN | EN |

Weitere geprüfte und ausgeschlossene Anbieter:
- **Gandi:** Renewal CHF 32/Jahr — viel zu teuer seit Übernahme 2023
- **Namecheap:** .ch-Transfer nicht unterstützt, ~CHF 24/Jahr, nur Englisch
- **Squarespace Domains:** .ch nicht unterstützt

## Begründung

1. **Günstigster Preis** — ~CHF 3–5/Jahr weniger als Hostpoint ab dem 2. Jahr
2. **Gratis E-Mail-Mailbox** — nützlich für `info@olivalle.ch` ohne separaten Dienst
3. **Schweizer Firma, DSG-konform** — Daten in der Schweiz
4. **Deutsches Interface** — wichtig für den Stakeholder
5. **Gratis Transfer** — kein finanzielles Risiko
6. **Cloudflare fällt weg** — unterstützt .ch-Domains nicht
7. **Hosttech-Account nicht zugänglich** — gehört dem bisherigen Administrator mit anderen Domains

## Offener Punkt

Den exakten Renewal-Preis bei Infomaniak vor dem Transfer im Shop verifizieren (`infomaniak.com/de/domains` → "olivalle.ch" eingeben). Drittquellen nennen CHF 10–12, aber Infomaniak rendert Preise dynamisch.

## Vorgehen

1. SH lässt AuthCode beim bisherigen Admin anfordern
2. Entwickler erstellt Infomaniak-Account
3. Domain mit AuthCode zu Infomaniak transferieren (dauert einige Tage)
4. DNS-Einträge bei Infomaniak setzen (fly.io, Resend)
5. Go-Live: DNS auf fly.io umstellen

## Konsequenzen

- Jährliche Kosten ~CHF 10–12 für Domain-Registrierung
- Volle DNS-Kontrolle beim Entwickler
- Kein Blocker mehr durch bisherigen Administrator
- Hosttech-Account wird für olivalle.ch nicht mehr benötigt
