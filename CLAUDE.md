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
| Backend/API | Python + FastAPI | Entwickler kennt Python/SQL |
| Frontend | Jinja2-Templates + Tailwind CSS | Kein zweites Framework, alles Python |
| Datenbank | SQLite | Eine Datei, kein separater Service, reicht für ~100 Bestellungen/Mt |
| Payments | Stripe | Twint (CH), Kreditkarte |
| QR-Rechnung | swiss-qr-bill (Open Source) | Kein Bexio, direkt im Code |
| Styling | Tailwind CSS | Utility-first, flexibel |
| Hosting | fly.io (1 Docker-Container) | Günstig (~$5/Mt), kommerziell erlaubt |

## Design
- **Font:** Amatic SC (Hausschrift der bestehenden Website)
- **Farben:** Weiss auf dunklem Hintergrund, Akzentfarbe Gelb `#f1d600`
- **Logo:** olivalle-logo2017_2.jpg (rundes Logo)

### Tailwind Card-UI Klassen (Issue #51)
| Element | Klassen |
|---|---|
| Card | `bg-stone-700 rounded-lg p-6 shadow-md` |
| Card Hover (Produktkarten) | `hover:shadow-lg hover:-translate-y-1 transition-all duration-200` |
| Responsive Grid | `grid gap-6 sm:grid-cols-2 lg:grid-cols-3` |
| Button Transition | `transition-colors` |

## Wichtigste Funktionen
1. Webshop mit Warenkorb
2. Direkte Zahlung via Stripe (Twint, Kreditkarte)
3. QR-Rechnung via swiss-qr-bill
4. Automatisierte Rechnungsstellung
5. Administrativen Aufwand für Einzelunternehmer minimieren

## Kundendaten
Pflichtfelder: Vorname, Nachname, Strasse, PLZ, Ort, E-Mail
Optionale Felder: Telefonnummer, Kommentar
Versandoptionen: Abholung vor Ort / Postversand (CHF 9.90, gratis ab CHF 100)

## Context-Scopes

Je nach Aufgabe nur den relevanten Scope laden — reduziert Token-Verbrauch und hält den Fokus:

| Scope | Pfade | Wann verwenden |
|---|---|---|
| App | `app/`, `templates/`, `static/`, `CLAUDE.md` | FastAPI, Jinja2, Stripe Webhook |
| Vollständig | alles | Architektur- und Querschnittsthemen |

## Architektur-Regeln
- Alles in FastAPI — kein separates Frontend-Framework
- UI-Texte auf Deutsch (CH)

## Entwicklungsphasen
Aufgaben werden via **GitHub Issues** verwaltet: https://github.com/konstantinniedermann/olivalle-webshop/issues
Labels: `phase-0` bis `phase-3`, `technisch`, `rechtlich`, `claude-code`
Milestones: Phase 0 bis Phase 3

### Phase 0 — Vorbereitung ✓
Dokumentation, rechtliche Grundlagen, technisches Setup, Claude Code Setup

### Phase 1 — Fundament
FastAPI + Jinja2 Setup, SQLite verbinden, Produkte anzeigen

### Phase 2 — Shop
Warenkorb, Checkout, Stripe (Kreditkarte + Twint), Bestellbestätigung per E-Mail

### Phase 3 — Konfiguration, Go-Live & Automatisierung
Accounts einrichten (Stripe, Resend), fly.io Secrets, Domain-Routing, Stripe Live-Modus,
QR-Rechnung, automatisierte Rechnungsstellung, Admin-Bereich, Go-Live Checkliste

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
