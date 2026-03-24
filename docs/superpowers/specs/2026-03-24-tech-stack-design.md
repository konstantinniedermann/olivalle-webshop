# Tech-Stack Design — Olivalle Webshop

> Erstellt: 2026-03-24
> Status: Entwurf
> Kontext: Ersetzt den bisherigen Stack (Next.js + Supabase + Vercel/Railway) durch einen vereinfachten, Python-zentrischen Ansatz.

---

## 1. Ausgangslage

### Bisheriger Plan (arc42 / CLAUDE.md)
| Layer | Tool |
|---|---|
| Frontend | Next.js 15 (App Router) + shadcn/ui |
| Backend | FastAPI (Python) |
| Datenbank | Supabase (PostgreSQL) |
| Hosting | Vercel (Frontend) + Railway/Render (Backend) |
| Payments | Stripe (Twint, Kreditkarte, Abos) |
| QR-Rechnung | swiss-qr-bill |
| E-Mail | Resend |

### Warum Änderung?
- **SH-Meeting 2026-03-24:** Abos gestrichen, Hosting → fly.io, QR-Rechnung bleibt Pflicht
- **Entwickler-Kontext:** Python-Kenntnisse vorhanden, JavaScript/React neu und nicht nötig
- **Synergie mit Munica:** Gleiche Plattform (fly.io), gleicher Workflow, gleiche Tools → weniger Admin, mehr Expertise
- **Prinzipien:** Einfachheit, niedrige Kosten, minimale Wartung

---

## 2. Neuer Tech-Stack

| Layer | Tool | Begründung |
|---|---|---|
| **Backend/API** | FastAPI (Python) | Entwickler kennt Python, bewährt, schnell |
| **Frontend** | Jinja2-Templates + Tailwind CSS | Kein zweites Framework, alles Python, HTML-Templates reichen für 3 Produkte |
| **Interaktivität** | Vanilla JavaScript | Warenkorb (~50–100 Zeilen JS, localStorage), kein Framework nötig |
| **Datenbank** | SQLite | Eine Datei, kein separater Service, reicht für ~100 Bestellungen/Mt |
| **Hosting** | fly.io (1 Docker-Container) | Bereits vorhanden (Munica), günstig (~$5/Mt), kommerziell erlaubt |
| **Payments** | Stripe (Twint + Kreditkarte) | Twint nativ in CH, Stripe Checkout als Redirect |
| **QR-Rechnung** | swiss-qr-bill | Python-Bibliothek, passt zum Stack |
| **E-Mail** | Resend (Free Tier) | 3'000 Mails/Mt gratis, Absender: bestellung@olivalle.ch |
| **Styling** | Tailwind CSS | Utility-first, flexibel genug für eigenes Design (Amatic SC, dunkler Hintergrund, Gelb #f1d600) |
| **Testing** | pytest + Ruff | Wie Munica |

---

## 3. Was rausfällt

| Gestrichen | Grund |
|---|---|
| Next.js / React / TypeScript | Unnötige Komplexität, Entwickler kennt Python |
| Node.js | Nicht mehr nötig ohne Next.js |
| Supabase | SQLite reicht, ein externer Service weniger |
| shadcn/ui | React-basiert, fällt mit Next.js weg |
| Vercel | Kein Next.js mehr, fly.io übernimmt alles |
| Railway / Render | fly.io übernimmt alles |
| Stripe Billing (Abos) | SH-Entscheid: Abos gestrichen |

---

## 4. Architektur

### Übersicht

```mermaid
graph TD
    subgraph flyio["fly.io (1 Docker-Container)"]
        API["FastAPI"]
        Templates["Jinja2-Templates + Tailwind CSS"]
        DB["SQLite"]
        QR["swiss-qr-bill"]
    end

    Browser["Browser"] -->|HTTP| API
    API --> Templates
    API --> DB
    API -->|Checkout Session| Stripe
    Stripe -->|Webhook| API
    API -->|Bestellbestätigung| Resend["Resend (E-Mail)"]
    API -->|PDF generieren| QR

    Resend -->|bestellung@olivalle.ch| Kunde["Kunde (E-Mail)"]
```

### Request-Flow
1. Kunde öffnet `olivalle.ch` → FastAPI liefert Jinja2-Template mit Produkten
2. Kunde legt Produkte in Warenkorb → Vanilla JS + localStorage
3. Kunde klickt "Bestellen" → POST an FastAPI mit Warenkorb-Daten
4. FastAPI validiert Warenkorb serverseitig (Produkt-IDs, Preise aus DB, Mengen) und erstellt Stripe Checkout Session → Redirect zu Stripe
5. Kunde zahlt (Twint/Kreditkarte) → Stripe Webhook an FastAPI
6. FastAPI speichert Bestellung in SQLite, generiert QR-Rechnung (PDF), sendet Bestätigung via Resend

### Alternative: QR-Rechnung statt Stripe
1. Kunde wählt "Auf Rechnung zahlen"
2. FastAPI generiert QR-Rechnung (PDF) via swiss-qr-bill
3. PDF wird per E-Mail an Kunden gesendet
4. Bestellung erhält Status "offen" in SQLite
5. Zahlungseingang manuell vom Betreiber bestätigt

---

## 5. Datenbank (SQLite)

### Warum SQLite?
- Eine Datei, kein separater Service, kein Connection-Pool
- Für ~100 Bestellungen/Mt massiv überdimensioniert
- Backup = Datei kopieren
- Auf fly.io: persistentes Volume mounten

### Tabellen (Entwurf)
- `produkte` — id, name, preis_chf, beschreibung, bild_pfad
- `kunden` — id, vorname, nachname, email, strasse, plz, ort, telefon
- `bestellungen` — id, kunde_id, status, zahlungsart (stripe/rechnung), versandart, versandkosten, total_chf, stripe_session_id (nullable), kommentar, erstellt_am
- `bestellpositionen` — id, bestellung_id, produkt_id, menge, einzelpreis_chf

### SQLite auf fly.io
- Persistentes Volume für die `.db`-Datei
- Wichtig: fly.io Machines können pausieren → Volume bleibt erhalten
- **Backup (Pflicht):** Litestream für kontinuierliche Replikation der SQLite-DB auf Object Storage (z.B. S3-kompatibel). fly.io Volumes sind lokal an eine Machine gebunden — bei Hardware-Ausfall droht Datenverlust. Für einen produktiven Shop mit Bestelldaten ist das nicht akzeptabel.

---

## 6. Hosting (fly.io)

### Setup
- 1 Machine (shared-cpu-1x, 256 MB RAM)
- 1 persistentes Volume (1 GB, für SQLite + generierte PDFs)
- Docker-Image: Python 3.13-slim
- Kosten: ~$5/Mt

### Domain
- `olivalle.ch` → DNS-Transfer via AuthCode (SH fordert bei Hostech an wenn Prototyp steht)
- SSL: automatisch via fly.io
- DNS-Einträge für Resend (SPF/DKIM) bei Domain-Transfer einrichten

### Synergie mit Munica
- Gleicher fly.io Account
- Gleicher Deployment-Workflow (`fly deploy`)
- Gleiche Docker-Basis (Python 3.13-slim)

---

## 7. E-Mail (Resend)

- **Absender:** `bestellung@olivalle.ch` (verifizierte Domain)
- **Reply-To:** `olivalle.olten@outlook.com` (bestehende E-Mail des SH)
- **Free Tier:** 3'000 Mails/Mt, max. 100/Tag → reicht für ~100 Bestellungen/Mt
- **DNS:** SPF + DKIM Einträge für olivalle.ch nötig (beim Domain-Transfer einrichten)
- **Kosten:** $0/Mt

---

## 8. Payments (Stripe)

- **Stripe Checkout (hosted)** — Redirect zu Stripe, kein eigenes Zahlungsformular
- **Twint** — nativ unterstützt in Stripe Schweiz
- **Kreditkarte** — automatisch in Stripe Checkout enthalten
- **Abos** — gestrichen (SH-Entscheid)
- **Webhook** — Stripe → FastAPI Endpoint für Zahlungsbestätigung

---

## 9. Versand

- Versandkosten: CHF 9.90 pauschal
- Ab CHF 100: gratis Versand
- Abholung vor Ort möglich (Details per E-Mail, Adresse NICHT auf Website)

---

## 10. Kostenübersicht

| Dienst | Kosten/Mt |
|---|---|
| fly.io (1 Machine + Volume) | ~$5 |
| Resend (Free Tier) | $0 |
| Stripe (Transaktionsgebühren) | 1.5% + CHF 0.30 pro Zahlung (CH-Karten), 2.9% (internationale Karten) |
| Domain olivalle.ch | Bereits vorhanden |
| **Total fix** | **~CHF 5/Mt** |

---

## 11. Offene Punkte

- [ ] Produktbilder: statisch im Repo oder auf Volume?
- [ ] Admin-Bereich: wie verwaltet der SH Bestellungen? (Phase 3)
- [ ] Design-Mockups: Layout der Produktseite, Warenkorb, Checkout

---

## 12. Sicherheit

- **CSRF-Schutz:** FastAPI liefert CSRF-Tokens in Jinja2-Formularen. Alle POST-Endpoints (Bestellung, Kontakt) validieren das Token. Nötig weil Jinja2-Templates klassische Formular-Submits verwenden.
- **Warenkorb-Validierung:** Client-seitige Warenkorb-Daten (localStorage) werden beim Bestellen serverseitig gegen die Datenbank validiert (Produkt-IDs, Preise, Mengen). Keine Vertrauens­würdigkeit für Client-Daten.
- **Stripe Webhook:** Signatur-Verifizierung mit Stripe Webhook Secret.
- **Secrets:** IBAN, E-Mail-Adressen, API-Keys ausschliesslich in `.env` / fly.io Secrets, nie im Code.

---

## 13. Testing

- **Tool:** pytest + Ruff (Vitest entfällt mit TypeScript)
- **Test-Fokus:** Bestelllogik, Stripe Webhook-Verarbeitung, API-Endpunkte, Preisberechnung (Versandkosten-Logik)
- **CSRF:** Tests prüfen dass POST-Endpoints ohne gültiges Token abgelehnt werden

---

## 14. Dokumenten-Update (nach Genehmigung)

Folgende Dokumente müssen an den neuen Stack angepasst werden:

| Dokument | Änderungen |
|---|---|
| `CLAUDE.md` (Projekt) | Tech-Stack-Tabelle, Test-Strategie (Vitest entfernen), Context-Scopes, Phasen-Beschreibung, Abos entfernen, Versandkosten eintragen |
| `docs/arc42.md` | Abschnitte 3–5, 7, 9: Next.js/Supabase/Vercel → Jinja2/SQLite/fly.io; FA-009 (Abos) streichen |
| `docs/systemarchitektur.md` | Neues Mermaid-Diagramm gemäss Abschnitt 4 dieser Spec |
| `docs/datenbankschema.md` | An SQLite-Schema anpassen |
