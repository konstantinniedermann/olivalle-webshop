# Design Spec: Versionierung & CI/CD

**Datum:** 2026-03-25
**Status:** Genehmigt
**Referenz:** Munica-Projekt (identischer Ansatz, adaptiert auf einen Service)

---

## Ziel

Automatisierte CI/CD-Pipeline auf GitHub Actions: Push auf `main` löst Tests, Docker-Build und Deployment auf fly.io aus. Semantische Versionierung mit manueller MINOR- und automatischer PATCH-Vergabe.

---

## Pipeline-Struktur

```
Push auf main
    │
    ├─► test         pytest mit uv — schlägt fehl → Pipeline stoppt
    ├─► build        Docker Build → GHCR, APP_VERSION berechnen
    └─► deploy       flyctl deploy --image → fly.io, Git-Tag setzen
```

**Trigger:** `push` auf Branch `main`
**Concurrency:** `group: deploy`, `cancel-in-progress: true`

---

## Versionierung

**Schema:** `v{MINOR}.{PATCH}` (z.B. `v0.1.3`)

- `MINOR` steht in `pyproject.toml` → `version = "0.1"` (manuell erhöhen bei neuer Phase)
- `PATCH` wird von CI berechnet: Anzahl vorhandener Git-Tags mit Präfix `v{MINOR}.*` + 1
- Nach erfolgreichem Deploy: CI setzt Git-Tag (z.B. `v0.1.3`) auf `main`

---

## Jobs

### `test`
- Runner: `ubuntu-latest`
- Python 3.13 via `actions/setup-python`
- Dependencies: `pip install -e .[dev]`
- Befehl: `pytest`

### `build`
- Needs: `test`
- Berechnet `APP_VERSION` (MINOR aus `pyproject.toml` + PATCH via Tag-Zählung)
- Docker-Image: `ghcr.io/konstantinniedermann/olivalle`
- Tags: `:sha` (short SHA) + `:latest`
- Push zu GHCR via `GITHUB_TOKEN` (kein zusätzliches Secret)
- Build-Arg: `APP_VERSION=${{ env.APP_VERSION }}`
- Output: `image_sha`, `app_version`

### `deploy`
- Needs: `build`
- `flyctl deploy --app olivalle --image ${{ needs.build.outputs.image_sha }}`
- Secret: `FLY_API_TOKEN`
- Git-Tag setzen nach erfolgreichem Deploy (via `github-actions[bot]`)

---

## APP_VERSION im Code

**Dockerfile** (Ergänzung):
```dockerfile
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}
```

**`app/config.py`** — neues Feld:
```python
app_version: str = "dev"
```
Gelesen aus `APP_VERSION` Umgebungsvariable.

**`/health`-Endpoint** (in `app/main.py`):
```json
{"version": "v0.1.3", "status": "ok"}
```

**Footer** (`templates/base.html`):
```html
<span class="text-xs text-gray-400">{{ app_version }}</span>
```
Version wird einmalig in `app/templating.py` in den globalen Template-Kontext gesetzt.

---

## Betroffene Dateien

| Datei | Änderung |
|-------|----------|
| `.github/workflows/deploy.yml` | Neu — vollständiger Workflow |
| `Dockerfile` | `ARG APP_VERSION=dev` + `ENV APP_VERSION=${APP_VERSION}` |
| `app/config.py` | Feld `app_version: str` ergänzen |
| `app/main.py` | `/health`-Endpoint + version im Template-Kontext |
| `templates/base.html` | Versionsnummer im Footer |

---

## Voraussetzungen (einmalig)

- GitHub Secret `FLY_API_TOKEN` im Repo anlegen (`fly tokens create deploy`)
- GHCR-Zugriff: automatisch via `GITHUB_TOKEN` (keine manuelle Konfiguration)

---

## Abgrenzung

- Kein separater Datenbank-Service (SQLite liegt im fly.io Volume — ein Container)
- Kein Benchmark-Job (nicht benötigt für Olivalle)
- Kein automatischer CHANGELOG
