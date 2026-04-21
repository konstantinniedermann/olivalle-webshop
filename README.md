# Olivalle Webshop

Webshop für biologisches Olivenöl aus Andalusien — ersetzt den bisherigen manuellen Bestellprozess durch Bezahlung via Twint oder Kreditkarte, QR-Rechnung, automatische Bestellbestätigung per E-Mail und Rabattcodes.

**Tech-Stack:** FastAPI + Jinja2 + Tailwind CSS + SQLite + fly.io

**Status:** Live auf [olivalle.ch](https://olivalle.ch) seit 2026-04-08 (v1.0)

**Dokumentation:** [docs/index.md](docs/index.md) — Übersicht aller Doks (arc42, ADRs, Bestellprozess, Rechtliches)

---

## Projektfortschritt

<table>
<tr>
<th>Phase</th>
<th>Inhalt</th>
<th>Fortschritt</th>
<th>Status</th>
</tr>
<tr>
<td><strong><a href="https://github.com/konstantinniedermann/olivalle-webshop/milestone/1">Phase 0</a></strong> — Vorbereitung</td>
<td>Dokumentation, Rechtliches, Setup</td>
<td>20 / 20</td>
<td><img src="https://img.shields.io/badge/Erledigt-brightgreen?style=flat-square" /></td>
</tr>
<tr>
<td><strong><a href="https://github.com/konstantinniedermann/olivalle-webshop/milestone/2">Phase 1</a></strong> — Fundament</td>
<td>FastAPI, SQLite, Produktseite</td>
<td>7 / 7</td>
<td><img src="https://img.shields.io/badge/Erledigt-brightgreen?style=flat-square" /></td>
</tr>
<tr>
<td><strong><a href="https://github.com/konstantinniedermann/olivalle-webshop/milestone/3">Phase 2</a></strong> — Shop</td>
<td>Warenkorb, Checkout, Stripe, E-Mail</td>
<td>6 / 6</td>
<td><img src="https://img.shields.io/badge/Erledigt-brightgreen?style=flat-square" /></td>
</tr>
<tr>
<td><strong><a href="https://github.com/konstantinniedermann/olivalle-webshop/milestone/4">Phase 3</a></strong> — Konfiguration, Go-Live & Automatisierung</td>
<td>Accounts, Secrets, Domain, Stripe Live, QR-Rechnung, Admin, Go-Live</td>
<td>18 / 18</td>
<td><img src="https://img.shields.io/badge/Erledigt-brightgreen?style=flat-square" /></td>
</tr>
</table>

---

## Frontend-CSS (Tailwind Build-Step)

Tailwind CSS wird zur Build-Zeit lokal kompiliert — es wird **kein CDN** mehr eingebunden. Das fertige Stylesheet liegt unter `static/css/app.css`.

**Einmalig einrichten** (muss vor dem ersten `make dev` laufen, sonst fehlt `static/css/app.css`):
```bash
npm install
make css-build
```

**Während der Entwicklung** (parallel zum FastAPI-Server laufen lassen, beobachtet Template-Änderungen):
```bash
make css-watch
```

**Docker-Deployment:** Der Multi-Stage-Build im `Dockerfile` enthält eine Node-Stage, die Tailwind automatisch baut. Lokales `npm install` ist für Deployment nicht nötig — nur für die lokale Entwicklung.

---

## Entwicklung

Vor jedem Push empfohlen:

```bash
make lint-all   # Ruff-Check + Format-Check (identisch zum CI-Gate)
make test       # Tests via pytest
```

Eine Übersicht aller verfügbaren Kommandos liefert `make help`.
