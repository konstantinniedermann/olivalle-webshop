# Ruff-Backlog Cleanup + Drift-Schutz — Design

- **Issue:** #103
- **Datum:** 2026-04-21
- **Typ:** Hygiene (kein Feature, keine funktionale Änderung)

## Problem

`uv run ruff check app tests` meldet **45 Lint-Violations** (43× E501, 2× E402), `uv run ruff format --check app tests` meldet **13 Format-Drift-Files**. Alle pre-existing, kein Runtime-Effekt. Die Ursache: es gibt keine CI-Stufe, die Ruff bei PRs erzwingt — nur `deploy.yml` läuft automatisiert.

Ohne Gate wird sich derselbe Drift nach dem Cleanup wieder ansammeln.

## Ziel

1. `ruff check app tests` und `ruff format --check app tests` beide clean.
2. GitHub-Actions-Workflow, der ab sofort jeden Drift blockiert, bevor er auf `main` kommt.
3. Keine funktionalen Änderungen — alle 207 Tests bleiben unverändert grün.

## Nicht-Ziele

- Weitere Ruff-Regeln aktivieren (z.B. `D`-Serie für Docstrings).
- Pre-commit-Hooks (CI-Gate reicht).
- Type-Checking (mypy/pyright) einführen.
- `.git-blame-ignore-revs` pflegen (YAGNI bei dieser Grösse).

## Scope

Angefasste Bereiche:

| Bereich | Dateien | Art der Änderung |
|---|---|---|
| `app/` | 7 Format-Drifts + 3 E501 | `ruff format` + manuelle Zeilenumbrüche |
| `tests/` | 6 Format-Drifts + 40 E501 + 2 E402 | `ruff format` + manuelle Zeilenumbrüche + Import-Reorg |
| `.github/workflows/` | 1 neue Datei | `lint.yml` |
| `Makefile` | 1 Target | `lint-all` ergänzen |

## Lösungsansatz

Big-Bang-Cleanup in einem Pull Request mit drei semantisch getrennten Commits.

### Commit 1 — `chore: ruff format über app/ und tests/`

Ausführen: `uv run ruff format app tests`.

Ergebnis: 13 Dateien umformatiert, ausschliesslich Layout-Änderungen (dict-Literale, Funktionsaufrufe inline vs. mehrzeilig). Kein menschliches Urteil, semantik-preserving.

### Commit 2 — `fix: Ruff-Lint-Violations (E501, E402) beheben`

Manuelle Fixes für die 45 Violations:

**43× E501 (Zeile zu lang, >88 Zeichen)**
- `app/routers/webhooks.py:142` — `details=json.dumps(...)` in Log-Aufruf brechen.
- `app/services/stripe_service.py:48` — `success_url`-f-string auf zwei Zeilen.
- `app/services/rabattcode_service.py:57` — Fehlermeldungs-f-string brechen.
- 40× in `tests/` — mehrzeilige SQL-INSERTs und Docstrings umbrechen. Strategie:
  - Mehrzeilige SQL-Strings via String-Literal-Concatenation (`"INSERT INTO ... " "VALUES ..."`), wobei jede Zeile ≤88 Zeichen bleibt.
  - Docstrings auf eine Zeile verkürzen oder triple-quoted mehrzeilig.
  - Assertion-Strings bei Bedarf in Variablen extrahieren.

**2× E402 (Import nicht am Dateianfang) in `tests/test_rabattcode_service.py`**

Beide Imports (`from app.repositories.rabattcode_repo import ...` und `from app.services.rabattcode_service import ...`) an den Datei-Kopf verschieben. Die vorhandenen Sektionsmarker `# --- Repository Tests ---` / `# --- Service Tests ---` bleiben als visuelle Trenner stehen.

### Commit 3 — `feat: CI-Workflow für Ruff-Gate auf PRs`

Neue Datei `.github/workflows/lint.yml`:

```yaml
name: Lint

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  ruff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          python-version: "3.13"
      - name: Install dev dependencies
        run: uv sync --extra dev
      - name: Ruff Check
        run: uv run ruff check app tests
      - name: Ruff Format Check
        run: uv run ruff format --check app tests
```

Zusätzlich in `Makefile` ein neues Target hinzufügen:

```make
lint-all: ## Ruff-Check + Format-Check (gleich wie CI)
	uv run ruff check app tests
	uv run ruff format --check app tests
```

Und in der `.PHONY`-Zeile `lint-all` ergänzen.

## Design-Entscheidungen (mit Begründung)

| Entscheidung | Warum |
|---|---|
| Big-Bang statt inkrementell | Projekt ist erst 6 Monate alt, ~60 Dateien → einmaliger Blame-Schmerz günstiger als dauerhafte Sonderregeln. |
| `ruff format` zuerst in eigenem Commit | Reine Layout-Commits sind für Reviewer leicht überspringbar. |
| E402 via Imports-nach-oben-ziehen (nicht `# noqa`) | Standard-Python-Idiom, weniger Sonderregeln. Kapitel-Struktur bleibt durch `# ---`-Kommentare erhalten. |
| CI-Trigger `pull_request` + `push` auf `main` | Safety-Net, falls direkt auf `main` committet wird. |
| CI-Scope `app tests` | Konsistent mit Akzeptanzkriterium des Issues. |
| Kein Cache im CI-Job | Job läuft in <30s, Cache-Config lohnt nicht. |
| `make lint-all` | Lokale Reproduktion des CI-Gates vor Push. |

## Verifikation

| Schritt | Erwartetes Ergebnis |
|---|---|
| `uv run ruff format --check app tests` | exit 0 |
| `uv run ruff check app tests` | "All checks passed!" |
| `uv run pytest` | alle 207 Tests grün |
| `make lint-all` | exit 0 |
| Neuer PR auf GitHub | `Lint`-Check-Job erscheint und läuft grün |

## Rollback-Plan

Falls ein Test nach dem `ruff format` rot wird (unerwartet — ruff format ist semantik-preserving):

1. `git reset --hard` auf den Stand vor Commit 1.
2. Pro Datei einzeln `ruff format <file>` laufen lassen + Tests prüfen.
3. Problematische Datei via `per-file-ignores` ausschliessen und im Issue dokumentieren.

## Offene Fragen

Keine.
