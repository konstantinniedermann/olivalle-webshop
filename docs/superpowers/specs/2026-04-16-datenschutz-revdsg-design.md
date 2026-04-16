# Design: Datenschutzerklärung revDSG-konform ergänzen

**Issue:** #69
**Datum:** 2026-04-16
**Ansatz:** Inline-Ergänzungen (bestehende Struktur beibehalten)

## Kontext

Die Datenschutzerklärung (`templates/datenschutz.html`) enthält bereits die Grundstruktur, ist aber nicht vollständig nach dem revidierten Schweizer Datenschutzgesetz (revDSG, in Kraft seit 1. September 2023). Der Stakeholder hat zu 8 Punkten Stellung genommen.

## SH-Entscheidungen

| Punkt | Thema | Entscheidung |
|-------|-------|--------------|
| 1 | Verantwortlicher | Auf Impressum verlinken (nicht Adresse wiederholen) |
| 2 | Aufbewahrungsdauer | So lassen, nicht auf 10 Jahre verweisen |
| 3 | Stripe/USA-Hinweis | Ja |
| 4 | Stripe-Cookies | Ja |
| 5 | Server-Logs | Ja |
| 6 | Zweck präzisieren | Ja |
| 7 | Recht auf Datenherausgabe | Ja |
| 8 | Datum "Stand: ..." | Ja |

## Änderungen an `templates/datenschutz.html`

### 1. Neuer Abschnitt "Verantwortlich" (nach Einleitung)

> Angaben zur verantwortlichen Stelle finden Sie in unserem [Impressum](/impressum).

Eigener Abschnitt oben — das ist das erste, wonach Nutzer suchen, und entspricht dem revDSG-Standard.

### 2. Zweck: Rechtsgrundlage ergänzen

Zusätzlicher Satz am Ende des bestehenden "Zweck der Datenbearbeitung"-Abschnitts:

> Die Datenbearbeitung erfolgt zur Erfüllung des Kaufvertrags sowie zur Wahrung unserer berechtigten Interessen (z.B. Betrugsprävention, Fehleranalyse).

### 3. Drittanbieter: Bekanntgabe ins Ausland

Neuer Absatz nach dem bestehenden Text im "Drittanbieter"-Abschnitt:

> **Bekanntgabe ins Ausland:** Stripe verarbeitet Zahlungsdaten teilweise in den USA. Der Datenschutz wird durch Standardvertragsklauseln (Standard Contractual Clauses) sichergestellt.

### 4. Cookies: Stripe-Cookies

Ergänzung im bestehenden "Cookies"-Abschnitt:

> Stripe setzt zudem eigene Cookies zur Betrugserkennung (Fraud Detection). Diese Cookies sind technisch notwendig für die sichere Zahlungsabwicklung.

### 5. Neuer Abschnitt "Server-Logs" (nach Cookies)

> Beim Besuch unserer Website werden automatisch folgende Daten in Server-Logs gespeichert: IP-Adresse, Zeitpunkt des Zugriffs, aufgerufene Seite und verwendeter Browser. Diese Daten dienen der Sicherstellung des Betriebs und der Fehleranalyse. Sie werden nicht mit anderen Daten zusammengeführt.

### 6. Ihre Rechte: Datenherausgabe

Neuer Listenpunkt:

> **Datenherausgabe** — Ihre Daten in einem gängigen elektronischen Format (z.B. PDF) zu erhalten (Art. 28 DSG)

### 7. Stand-Datum

Nach dem "Änderungen"-Abschnitt, am Ende der Seite:

> Stand: 16. April 2026

## Was sich NICHT ändert

- **Punkt 2 (Aufbewahrungsdauer):** Aktueller Text sagt bereits "gesetzliche Aufbewahrungsfristen" ohne 10-Jahre-Verweis — kein Change nötig.
- **Kein Cookie-Banner:** Nur technisch notwendige Cookies, kein Opt-in nach Schweizer Recht nötig.
- **Keine DSGVO-Verweise:** Nur CH-Kunden, revDSG gilt.
- **Keine Backend-Änderungen:** Reine Template-Anpassung.
- **Styling:** Bestehende CSS-Klassen werden wiederverwendet.

## Betroffene Dateien

- `templates/datenschutz.html` — einzige Datei die geändert wird
