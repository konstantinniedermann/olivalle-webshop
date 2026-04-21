# Olivalle Webshop

Webshop für biologisches Olivenöl aus Andalusien — live auf **[olivalle.ch](https://olivalle.ch)** seit April 2026.

Ersetzt den bisherigen manuellen Bestellprozess (Tally-Formular) durch einen vollständigen Shop mit Kartenzahlung/TWINT, automatischer Bestellbestätigung per E-Mail und QR-Rechnung für Rechnungskäufer.

---

## Tech-Stack

| Bereich | Technologie |
|---|---|
| Backend | Python 3.13 + FastAPI |
| Frontend | Jinja2 Templates + Tailwind CSS (lokaler Build) |
| Datenbank | SQLite (persistentes fly.io Volume) |
| Zahlungen | Stripe (Twint, Kreditkarte) |
| QR-Rechnung | [`qrbill`](https://github.com/claudep/swiss-qr-bill) (Open Source) |
| E-Mail | Brevo (Free Tier) |
| Hosting | [fly.io](https://fly.io) — 1 Docker-Container, Region `cdg` |
| Tests | pytest (Unit + Integration + E2E) |
| CI | GitHub Actions — Ruff-Lint-Gate, SHA-gepinnte Actions, Dependabot |

Entscheidungsgrundlagen siehe [`docs/arc42.md`](docs/arc42.md) und die ADRs unter [`docs/`](docs/).

---

## Projekt-Kontext

Erstes eigenes Webprojekt im Rahmen des **CAS AI-Supported Software Engineering (AISE)** an der FFHS. Gebaut für einen Freund als Einzelunternehmer-Shop. Der gesamte Entwicklungsprozess lief unter Einsatz von **Claude Code** und einem formalen Agentic-Workflow (Brainstorming → Writing Plans → TDD → Code Review → Merge) über das [`superpowers`](https://github.com/obra/superpowers)-Plugin.

Dokumentations-Philosophie: **arc42** für Architektur, **ADRs** für Entscheidungen mit Tragweite, **Mermaid** für Diagramme direkt im Markdown.

---

## Schnellstart (lokale Entwicklung)

**Voraussetzungen:** Python 3.13 (via [`uv`](https://github.com/astral-sh/uv)) und Node.js (für Tailwind-Build).

```bash
# 1. Python-Umgebung anlegen (uv liest pyproject.toml + uv.lock)
uv sync --extra dev

# 2. Tailwind einmalig bauen (ohne das fehlt static/css/app.css)
npm install
make css-build

# 3. Dev-Server starten (FastAPI mit Auto-Reload)
make dev
```

Shop läuft dann auf [http://localhost:8000](http://localhost:8000).

Während der Entwicklung läuft parallel:
```bash
make css-watch   # rebuildet Tailwind bei Template-Änderungen
```

### Wichtigste Make-Targets
```bash
make help        # zeigt alle verfügbaren Kommandos
make test        # pytest (Unit + Integration)
make lint-all    # Ruff Check + Format-Check (identisch zum CI-Gate)
make migrate     # SQLite-Schema initialisieren
make docs        # MkDocs-Preview der Dokumentation
```

### Konfiguration
Eine Vorlage liegt in `.env.example`. Produktive Secrets werden nicht im Repo geführt — auf fly.io über `fly secrets set` konfiguriert.

---

## Projektstruktur

```
app/              FastAPI-Anwendung (Routen, Services, Modelle)
templates/        Jinja2-Templates (Shop, Checkout, Admin, E-Mails)
static/           CSS (Tailwind-Output), Bilder, JS
tests/            pytest — Unit, Integration, E2E
migrations/       SQLite-Schema-Migrationen
docs/             arc42-Architektur, ADRs, Bestellprozess, Rechtliches
```

Detail-Scopes für fokussierte Arbeit: siehe `CLAUDE.md`.

---

## Dokumentation

Einstiegspunkt: [**docs/index.md**](docs/index.md)

| Dokument | Inhalt |
|---|---|
| [arc42.md](docs/arc42.md) | Vollständige Architekturdokumentation |
| [systemarchitektur.md](docs/systemarchitektur.md) | Komponenten-Zusammenspiel (Frontend, DB, Stripe, E-Mail) |
| [datenbankschema.md](docs/datenbankschema.md) | SQLite-Tabellen und Beziehungen |
| [bestellprozess.md](docs/bestellprozess.md) | Ablauf vom Warenkorb bis zur Bestätigung |
| [adr-email-provider.md](docs/adr-email-provider.md) | ADR: Brevo gewählt |
| [adr-domain-registrar.md](docs/adr-domain-registrar.md) | ADR: Infomaniak gewählt |
| [security.md](docs/security.md) | Sicherheits-Referenz |
| [legal/](docs/legal/) | Datenschutzerklärung, Impressum, AGB |

---

## Deployment

Produktionsdeployment läuft über GitHub Actions nach `fly.io`:

```bash
fly deploy                    # manueller Deploy vom lokalen Rechner
fly logs                      # Live-Logs der Produktions-App
fly ssh console               # Shell in den Container
```

Konfiguration: [`fly.toml`](fly.toml). Persistente Daten (SQLite-DB) liegen auf dem Volume `olivalle_data` unter `/data`.

---

## Lizenz / Nutzung

Dieses Repository ist öffentlich zu Lern- und Demonstrationszwecken des CAS-Projekts. Der Code ist der konkrete Webshop eines Einzelunternehmers — keine OSS-Lizenz, alle Rechte vorbehalten. Pull Requests werden nicht angenommen; Issues für Fragen zum Projekt-Kontext sind willkommen.
