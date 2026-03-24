# Olivalle Webshop — Claude Code Kontext

> Gemeinsame Arbeitsregeln (Workflow, Code-Qualität, Dokumentation) sind in `../CLAUDE.md` definiert.

> Für alle Aktionen → `make help` (zeigt alle verfügbaren Befehle)

## Über das Projekt
Webshop für "Olivalle" — Verkauf von biologischem Olivenöl (Import aus Andalusien, Spanien).
Wird für einen Freund (Auftraggeber/Inhaber) gebaut. Einzelunternehmer in der Schweiz.
Ersetzt den bisherigen manuellen Bestellprozess via Tally-Formular.

Private Infos (URLs, Zugangsdaten): siehe `NOTES.local.md` (nicht im Repo)

## Produkte & Preise
| Produkt | Preis |
|---|---|
| 250ml Flasche | CHF 8 |
| 750ml Flasche | CHF 18 |
| 3l Kanister | CHF 50 |

## Test-Strategie
| Tool | Sprache | Zweck |
|---|---|---|
| **pytest** | Python | Unit + Integration Tests |
| **Vitest** | TypeScript | Unit Tests Frontend |

E2E-Tests (z.B. Playwright) erst ab Phase 3 evaluieren.
Mindestens testen: Bestelllogik, Stripe Webhook, API-Endpunkte.

## E-Mail-Dienst: Resend
| Plan | Preis | Limit |
|---|---|---|
| Free | $0/Mt | 3'000 Mails/Mt, max. 100/Tag |
| Pro | $20/Mt | 50'000 Mails/Mt |

Für den Stakeholder: Bei ca. 100 Bestellungen/Mt bleibt man im Free Tier.
Erst ab ~3'000 Bestellungen/Mt (sehr unwahrscheinlich) wäre ein Upgrade nötig.

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

## Kundendaten
Pflichtfelder: Vorname, Nachname, Strasse, PLZ, Ort, E-Mail
Optionale Felder: Telefonnummer, Kommentar
Versandoptionen: Abholung vor Ort / Postversand (Kosten noch zu definieren)

## Context-Scopes

Je nach Aufgabe nur den relevanten Scope laden — reduziert Token-Verbrauch und hält den Fokus:

| Scope | Pfade | Wann verwenden |
|---|---|---|
| Frontend | `frontend/`, `CLAUDE.md` | UI, Next.js, Tailwind, shadcn |
| Backend | `backend/`, `CLAUDE.md` | FastAPI, Supabase, Stripe Webhook |
| Vollständig | alles | Architektur- und Querschnittsthemen |

## Architektur-Regeln
- Business-Logik gehört in FastAPI, nicht in Next.js Server Actions
- UI-Texte auf Deutsch (CH)

## Entwicklungsphasen
Aufgaben werden via **GitHub Issues** verwaltet: https://github.com/konstantinniedermann/olivalle-webshop/issues
Labels: `phase-0` bis `phase-3`, `technisch`, `rechtlich`, `claude-code`
Milestones: Phase 0 bis Phase 3

### Phase 0 — Vorbereitung (aktiv, 35%)
Dokumentation, rechtliche Grundlagen, technisches Setup, Claude Code Setup
Offene Punkte: E-Mail-Dienst, Linter, Test-Strategie, Rechtliches, MCP-Server, Hooks, Slash Commands

### Phase 1 — Fundament
Next.js + FastAPI Setup, Supabase verbinden, Produkte anzeigen

### Phase 2 — Shop
Warenkorb, Checkout, Stripe (Kreditkarte + Twint), Bestellbestätigung per E-Mail

### Phase 3 — Automatisierung
Stripe Billing (Abos), QR-Rechnung, automatisierte Rechnungsstellung, Admin-Bereich

## Dokumentation
- Architekturdokumentation: `docs/arc42.md`
- Übersicht aller Dokumente: `docs/index.md`

## Git & GitHub
- Repository: https://github.com/konstantinniedermann/olivalle-webshop
- Branch-Strategie: `main` (produktiv), `develop` (Entwicklung)

## Wichtige Hinweise
- SSL-Zertifikat auf olivalle.ch ist abgelaufen → vor Launch erneuern
- Schweizer Rechtslage: MWST, Datenschutz (DSG)
- Stripe unterstützt Twint nativ in der Schweiz
