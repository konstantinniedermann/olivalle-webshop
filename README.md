# Olivalle Webshop

Webshop für biologisches Olivenöl aus Andalusien — live auf **[olivalle.ch](https://olivalle.ch)** seit April 2026.

Ersetzt den bisherigen manuellen Bestellprozess (Tally-Formular) durch einen vollständigen Shop mit Kartenzahlung/TWINT, automatischer Bestellbestätigung per E-Mail und QR-Rechnung für Rechnungskäufer.

> 📖 **Vollständige Projektdokumentation → [olivalle-Doku auf GitHub Pages](https://konstantinniedermann.github.io/olivalle-webshop/)**
>
> Roter Faden Problem → Lösung → Architektur (arc42) → Validierung → Betrieb. Architektur, ADRs, Diagramme und Betriebs-Runbooks leben dort — dieses README bleibt bewusst schlank.

---

## Tech-Stack (Kurzform)

Python 3.13 + FastAPI · Jinja2 + Tailwind CSS · SQLite · Stripe (Twint/Kreditkarte) · Brevo (E-Mail) · gehostet auf [fly.io](https://fly.io).

**Betrieb:** GitHub Actions (CI/CD) · pytest · Litestream → Tigris-Backup · `/health` + Healthchecks.io-Monitoring.

Begründungen, Alternativen und die vollständige Tabelle (inkl. Betriebs-Stack): [`docs/adr-tech-stack.md`](docs/adr-tech-stack.md).

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

## Projekt-Kontext

Erstes eigenes Webprojekt im Rahmen des **CAS AI-Supported Software Engineering (AISE)** an der FFHS, gebaut für einen Freund als Einzelunternehmer-Shop. Der gesamte Entwicklungsprozess lief unter Einsatz von **Claude Code** und einem formalen Agentic-Workflow (Brainstorming → Plan → TDD → Code Review → Merge) über das [`superpowers`](https://github.com/obra/superpowers)-Plugin.

Projektstand, Architektur (inkl. Projektstruktur/Bausteinsicht), Deployment und Backup-Strategie sind vollständig in der [Doku-Site](https://konstantinniedermann.github.io/olivalle-webshop/) dokumentiert — Einstieg: [`docs/projekt-status.md`](docs/projekt-status.md), [`docs/arc42.md`](docs/arc42.md), [`docs/ci-cd-und-versionierung.md`](docs/ci-cd-und-versionierung.md) und [`docs/adr-backup-strategie.md`](docs/adr-backup-strategie.md).

---

## Nutzung & Rechte

Dies ist der **produktive Code eines realen Live-Shops** ([olivalle.ch](https://olivalle.ch)) — kein Template zum Forken und keine Demo-App.

- **Code**: Entstanden im Rahmen des CAS AISE zu Lern- und Demonstrationszwecken. Keine OSS-Lizenz, alle Rechte vorbehalten. Studium zu Lernzwecken ist willkommen; Wiederverwendung bitte vorher anfragen.
- **Inhalte** (Logo, Produktbilder, Produkttexte, Marke Olivalle, Domains): Eigentum des Inhabers. Nicht Teil der Code-Nutzung — dürfen ohne Zustimmung nicht kopiert, abgebildet oder anderweitig verwendet werden.
- **Pull Requests**: Werden nicht angenommen. Für Fragen zum Projekt-Kontext Issues nutzen.

---

## Sicherheit

Eine Sicherheitslücke gefunden? Bitte **nicht** als öffentliches Issue melden, sondern über [GitHubs „Private vulnerability reporting"](https://github.com/konstantinniedermann/olivalle-webshop/security/advisories/new) — Details in [`SECURITY.md`](.github/SECURITY.md).
