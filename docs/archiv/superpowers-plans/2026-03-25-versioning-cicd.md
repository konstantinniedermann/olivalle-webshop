# Versionierung & CI/CD — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** GitHub Actions CI/CD-Pipeline einrichten (test → build → deploy auf fly.io) mit automatischer Patch-Versionierung und APP_VERSION im /health-Endpoint sowie im Footer.

**Architecture:** Drei Jobs in einem Workflow: `test` (pytest), `build` (Docker → GHCR, Version berechnen), `deploy` (flyctl + Git-Tag setzen). Version wird als Docker Build-Arg übergeben und via `APP_VERSION` ENV-Variable in der App verfügbar gemacht.

**Tech Stack:** GitHub Actions, Docker, GHCR (ghcr.io), fly.io (flyctl), FastAPI, Pydantic Settings, Jinja2

**Spec:** `docs/superpowers/specs/2026-03-25-versioning-cicd-design.md`

---

## File Map

| Datei | Änderung |
|-------|----------|
| `pyproject.toml` | `version = "0.1.0"` → `"0.1"` |
| `app/config.py` | Feld `app_version: str = "dev"` ergänzen |
| `app/main.py` | `/health` gibt `{"status": "ok", "version": settings.app_version}` zurück |
| `app/templating.py` | `templates.env.globals["app_version"]` nach Templates-Init setzen |
| `templates/base.html` | Versionsnummer im Footer ergänzen |
| `Dockerfile` | `ARG APP_VERSION=dev` + `ENV APP_VERSION=${APP_VERSION}` vor CMD |
| `.github/workflows/deploy.yml` | Neu — vollständiger CI/CD-Workflow |
| `tests/test_health.py` | Neu — Test für /health-Endpoint |

---

## Task 1: APP_VERSION im Code verankern

Betroffene Dateien:
- Modify: `pyproject.toml:3`
- Modify: `app/config.py`
- Modify: `app/main.py:12-14`
- Modify: `app/templating.py`
- Modify: `templates/base.html:33-42`
- Modify: `Dockerfile`
- Create: `tests/test_health.py`

- [ ] **Schritt 1: Test schreiben**

Neue Datei `tests/test_health.py`:

```python
import pytest
from fastapi.testclient import TestClient


def test_health_gibt_status_und_version_zurueck(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert isinstance(data["version"], str)
```

- [ ] **Schritt 2: Test laufen lassen — muss FEHLSCHLAGEN**

```bash
uv run pytest tests/test_health.py -v
```

Erwartet: FAIL — `AssertionError: assert 'version' in {'status': 'ok'}`

- [ ] **Schritt 3: `pyproject.toml` anpassen**

Zeile 3 von `version = "0.1.0"` auf `version = "0.1"` ändern.

```toml
version = "0.1"
```

Hintergrund: Der CI/CD-Workflow liest diesen Wert als MINOR-Version und hängt automatisch einen PATCH an (z.B. `v0.1.3`). Ein dreistelliges Format würde das Schema brechen.

- [ ] **Schritt 4: `app/config.py` — app_version Feld ergänzen**

Nach `database_path` einfügen:

```python
app_version: str = "dev"
```

Pydantic Settings liest dieses Feld automatisch aus der Umgebungsvariable `APP_VERSION`. Im lokalen Betrieb und in Tests bleibt der Wert `"dev"`, im Container-Deploy wird er durch den Build-Arg überschrieben.

Die Datei sieht danach so aus:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env"}

    secret_key: str = "change-me"
    base_url: str = "http://localhost:8000"

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    resend_api_key: str = ""

    qr_iban: str = ""
    qr_name: str = ""
    qr_address: str = ""
    qr_zip: str = ""
    qr_city: str = ""

    database_path: str = "olivalle.db"

    app_version: str = "dev"


settings = Settings()
```

- [ ] **Schritt 5: `app/main.py` — /health-Endpoint aktualisieren**

Import ergänzen (nach dem bestehenden `from fastapi import FastAPI`, d.h. als dritte Import-Zeile in der Datei):

```python
from app.config import settings
```

Den bestehenden `/health`-Endpoint (aktuell Zeilen 12–14) ersetzen:

```python
@app.get("/health")
def health():
    return {"status": "ok", "version": settings.app_version}
```

- [ ] **Schritt 6: `app/templating.py` — globalen Template-Kontext setzen**

Nach der `templates`-Initialisierung einfügen:

```python
from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.globals["app_version"] = settings.app_version
```

`env.globals` ist ein dict, das Jinja2 in jeden Template-Render-Kontext injiziert. Damit ist `{{ app_version }}` in allen Templates verfügbar, ohne dass Request-Handler es einzeln übergeben müssen.

- [ ] **Schritt 7: `templates/base.html` — Version im Footer**

Im `<footer>` nach dem letzten `<p>`-Tag (vor `</div>`) einfügen:

```html
<p class="mt-2 text-xs text-stone-600">{{ app_version }}</p>
```

Der Footer-Block sieht danach so aus:

```html
<footer class="border-t border-stone-700 py-6 text-center text-stone-400 text-sm">
    <div class="max-w-4xl mx-auto px-4">
        <p>&copy; Olivalle — Biologisches Olivenöl aus Andalusien</p>
        <p class="mt-1">
            <a href="/impressum" class="hover:text-accent">Impressum</a> ·
            <a href="/datenschutz" class="hover:text-accent">Datenschutz</a> ·
            <a href="/agb" class="hover:text-accent">AGB</a>
        </p>
        <p class="mt-2 text-xs text-stone-600">{{ app_version }}</p>
    </div>
</footer>
```

- [ ] **Schritt 8: `Dockerfile` — Build-Arg und ENV ergänzen**

Direkt vor der letzten `CMD`-Zeile einfügen:

```dockerfile
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}
```

Das `ARG` macht den Wert beim `docker build --build-arg APP_VERSION=v0.1.3` zugänglich. Das `ENV` schreibt ihn in die Container-Laufzeitumgebung, wo Pydantic Settings ihn als `APP_VERSION` liest.

- [ ] **Schritt 9: Test laufen lassen — muss BESTEHEN**

```bash
uv run pytest tests/test_health.py -v
```

Erwartet: PASS

- [ ] **Schritt 10: Alle Tests laufen lassen**

```bash
uv run pytest -v
```

Erwartet: alle Tests PASS

- [ ] **Schritt 11: Linting**

```bash
uv run ruff check . && uv run ruff format --check .
```

Erwartet: keine Fehler

- [ ] **Schritt 12: Commit**

```bash
git add pyproject.toml app/config.py app/main.py app/templating.py templates/base.html Dockerfile tests/test_health.py
git commit -m "feat: APP_VERSION in config, /health-Endpoint und Footer"
```

---

## Task 2: GitHub Actions Workflow erstellen

Betroffene Dateien:
- Create: `.github/workflows/deploy.yml`

- [ ] **Schritt 1: Verzeichnis anlegen**

```bash
mkdir -p .github/workflows
```

- [ ] **Schritt 2: `deploy.yml` erstellen**

```yaml
name: Deploy olivalle

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true

concurrency:
  group: deploy
  cancel-in-progress: true

permissions:
  contents: read
  packages: write

jobs:
  test:
    name: Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: uv sync --extra dev

      - name: Run tests
        run: uv run pytest

  build:
    name: Docker Build & Push
    needs: test
    runs-on: ubuntu-latest
    outputs:
      image_sha: ${{ steps.image_ref.outputs.ref }}
      app_version: ${{ env.APP_VERSION }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Compute APP_VERSION
        run: |
          MINOR=$(python -c "
          import tomllib
          with open('pyproject.toml', 'rb') as f:
              d = tomllib.load(f)
          print(d['project']['version'])
          ")
          git fetch --tags
          PATCH=$(git tag --list "v${MINOR}.*" | wc -l | tr -d ' ')
          PATCH=$((PATCH + 1))
          APP_VERSION="v${MINOR}.${PATCH}"
          echo "APP_VERSION=${APP_VERSION}" >> $GITHUB_ENV
          echo "Computed version: ${APP_VERSION}"

      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/konstantinniedermann/olivalle
          tags: |
            type=sha,prefix=
            type=raw,value=latest

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          platforms: linux/amd64
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            APP_VERSION=${{ env.APP_VERSION }}

      - name: Set image ref output
        id: image_ref
        run: |
          SHA=$(git rev-parse --short HEAD)
          echo "ref=ghcr.io/konstantinniedermann/olivalle:${SHA}" >> $GITHUB_OUTPUT

  deploy:
    name: Deploy to fly.io
    needs: build
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - uses: superfly/flyctl-actions/setup-flyctl@master

      - name: Deploy
        run: flyctl deploy --app olivalle --image ${{ needs.build.outputs.image_sha }}
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}

      - name: Git-Tag setzen
        run: |
          APP_VERSION="${{ needs.build.outputs.app_version }}"
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git tag "$APP_VERSION"
          git push origin "$APP_VERSION"
```

- [ ] **Schritt 3: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "feat: GitHub Actions CI/CD-Workflow (test → build → deploy)"
```

---

## Task 3: FLY_API_TOKEN Secret einrichten (manuell)

Dieser Schritt kann nicht automatisiert werden — er erfordert einmalige manuelle Aktion.

- [ ] **Schritt 1: fly.io Token erstellen**

```bash
fly tokens create deploy -x 999999h
```

Den ausgegebenen Token kopieren.

- [ ] **Schritt 2: GitHub Secret anlegen**

Im Browser:
1. https://github.com/konstantinniedermann/olivalle-webshop/settings/secrets/actions öffnen
2. "New repository secret" klicken
3. Name: `FLY_API_TOKEN`
4. Value: Token aus Schritt 1 einfügen
5. "Add secret" bestätigen

- [ ] **Schritt 3: Pipeline testen**

Einen leeren Commit auf `main` pushen:

```bash
git commit --allow-empty -m "ci: Pipeline-Test"
git push
```

Unter https://github.com/konstantinniedermann/olivalle-webshop/actions den Workflow beobachten.

Erwartet: alle drei Jobs (Tests, Build, Deploy) grün. Nach dem Deploy ist ein Git-Tag `v0.1.1` im Repository sichtbar.
