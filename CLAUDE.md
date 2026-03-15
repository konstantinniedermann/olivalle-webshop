# Olivalle Webshop

## Über das Projekt
Webshop für "Olivalle" – Verkauf von biologischem Olivenöl (Import aus Andalusien, Spanien).
Einzelunternehmer in der Schweiz. Hobby-Projekt mit geplantem Produktivbetrieb.

Bestehende Website: https://www.olivalle.ch (im Umbau, SSL abgelaufen)
Aktuelles Bestellformular: https://tally.so/r/w7Y9xZ (manuell verarbeitet, wird ersetzt)

## Entwickler-Kontext
- Anfänger mit wenig Projekterfahrung
- Kenntnisse in Python und SQL
- Erstes eigenes Webprojekt
- Bitte jeden Schritt erklären und vor grossen Änderungen nachfragen
- Schrittweise vorgehen, nicht alles auf einmal

## Produkte & Preise
| Produkt | Preis |
|---|---|
| 250ml Flasche | CHF 8 |
| 750ml Flasche | CHF 18 |
| 3l Kanister | CHF 50 |

## Tech-Stack
| Layer | Tool | Begründung |
|---|---|---|
| Frontend | Next.js 15 (App Router) | SEO, Full-Stack in einem Repo |
| Backend/API | Python + FastAPI | Entwickler kennt Python/SQL |
| Datenbank | Supabase (PostgreSQL) | Managed Postgres, günstig, skalierbar |
| Payments | Stripe | Twint (CH), Kreditkarte, Abos |
| QR-Rechnung | swiss-qr-bill (Open Source) | Kein Bexio, direkt im Code |
| Styling | Tailwind CSS + shadcn/ui | Schnell, konsistent |
| Hosting | Vercel (Frontend) + Railway/Render (Backend) | Günstig für kleine Projekte |

## Design
- **Font:** Amatic SC (Hausschrift der bestehenden Website)
- **Farben:** Weiss auf dunklem Hintergrund, Akzentfarbe Gelb `#f1d600`
- **Logo:** olivalle-logo2017_2.jpg (rundes Logo)

## Wichtigste Funktionen
1. Webshop mit Warenkorb
2. Direkte Zahlung via Stripe (Twint, Kreditkarte)
3. QR-Rechnung via swiss-qr-bill
4. Wiederkehrende Lieferungen / Abonnements via Stripe Billing
5. Automatisierte Rechnungsstellung
6. Administrativen Aufwand für Einzelunternehmer minimieren

## Kundendaten (aus bestehendem Tally-Formular)
Pflichtfelder:
- Vorname, Nachname
- Strasse, PLZ, Ort
- E-Mail

Optionale Felder:
- Telefonnummer
- Kommentar

Versandoptionen:
- Abholung vor Ort
- Postversand (Kosten noch zu definieren)

## Entwicklungsphasen

### Phase 1 — Fundament (aktuell)
- [ ] Next.js 15 Projektstruktur aufsetzen
- [ ] FastAPI Backend aufsetzen
- [ ] Supabase Datenbank verbinden
- [ ] Produkte in Datenbank erfassen
- [ ] Produktseite anzeigen

### Phase 2 — Shop
- [ ] Warenkorb implementieren
- [ ] Checkout-Flow
- [ ] Stripe Integration (Kreditkarte zuerst)
- [ ] Twint via Stripe hinzufügen
- [ ] Bestellbestätigung per E-Mail

### Phase 3 — Automatisierung
- [ ] Stripe Billing für Abonnements
- [ ] QR-Rechnung via swiss-qr-bill generieren
- [ ] Automatisierte Rechnungsstellung
- [ ] Admin-Bereich für Bestellübersicht

## Projektstruktur (geplant)
```
olivalle/
├── frontend/          # Next.js 15
│   ├── app/
│   ├── components/
│   └── ...
├── backend/           # Python FastAPI
│   ├── main.py
│   ├── models/
│   ├── routes/
│   └── ...
├── CLAUDE.md          # Diese Datei
├── README.md
└── CAS_Projektidee_Olivalle.pdf
```

## Wichtige Hinweise
- SSL-Zertifikat auf olivalle.ch ist abgelaufen → vor Launch erneuern
- Schweizer Rechtslage beachten: MWST, Datenschutz (DSG)
- Stripe unterstützt Twint nativ in der Schweiz
- QR-Rechnung direkt mit swiss-qr-bill generieren (kein Bexio)

## Dokumentation
- Architekturdokumentation nach **arc42**-Template: `docs/arc42.md`
- Diagramme werden mit **Mermaid** erstellt (in Markdown-Dateien eingebettet)
- Kein `\n` in Mermaid-Node-Labels verwenden (wird in VS Code nicht gerendert)
- Übersicht aller Dokumente: `docs/index.md`

## Git & GitHub
- Repository: https://github.com/konstantinniedermann/olivalle-webshop
- Branch-Strategie: main (produktiv), develop (entwicklung)
- Commit-Konvention: `feat:`, `fix:`, `docs:`, `refactor:`
