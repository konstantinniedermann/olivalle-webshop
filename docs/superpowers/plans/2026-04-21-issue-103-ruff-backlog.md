# Ruff-Backlog Cleanup + Drift-Schutz Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Alle 45 Ruff-Lint-Violations und 13 Format-Drifts in einem Big-Bang-PR beheben und einen CI-Workflow einziehen, der künftigen Drift auf PRs blockiert.

**Architecture:** Ein Feature-Branch, 5 semantisch getrennte Commits (1× `ruff format`, 3× manuelle Lint-Fixes gruppiert nach Bereich, 1× CI-Workflow + Makefile-Target). Ein einziger PR gegen `main`. Keine funktionalen Änderungen — die 207 bestehenden Tests bleiben unverändert grün und sind der einzige Regressions-Test.

**Tech Stack:** Ruff 0.9+ (linter + formatter), Python 3.13, uv (package manager), GitHub Actions, Make.

**Spec:** `docs/superpowers/specs/2026-04-21-ruff-backlog-design.md`
**Issue:** [#103](https://github.com/konstantinniedermann/olivalle-webshop/issues/103)

**Anmerkung zur Commit-Anzahl:** Die Spec skizzierte 3 Commits. Der Plan feingranuliert auf 5 Commits für atomare Rollbacks pro Bereich. Die drei mittleren `fix:`-Commits können vor Merge optional zu einem einzigen gesquasht werden.

---

## File Structure

Welche Dateien angefasst werden und wofür:

| Datei | Zweck | Tasks |
|---|---|---|
| `app/routers/webhooks.py` | 1× E501-Fix (Z.142) | Task 3 |
| `app/services/stripe_service.py` | 1× E501-Fix (Z.48) | Task 3 |
| `app/services/rabattcode_service.py` | 1× E501-Fix (Z.57) | Task 3 |
| `tests/test_rabattcode_service.py` | Imports nach oben + E501-Fixes | Task 4 |
| `tests/test_api_admin.py` + 8 weitere Test-Files | E501-Fixes | Task 5 |
| `.github/workflows/lint.yml` | Neue CI-Datei | Task 6 |
| `Makefile` | Neues Target `lint-all` | Task 6 |
| 13 Files in `app/` + `tests/` | Layout durch `ruff format` | Task 2 |

---

## Task 1: Feature-Branch anlegen

**Files:** keine

- [ ] **Step 1: Vom aktuellen main-Stand branchen**

```bash
git status
```
Expected: `working tree clean, your branch is up to date with 'origin/main'`

- [ ] **Step 2: Branch erstellen**

```bash
git checkout -b ruff-backlog-103
```
Expected: `Switched to a new branch 'ruff-backlog-103'`

- [ ] **Step 3: Baseline-Verifikation — Tests grün vor Start**

```bash
uv run pytest -q
```
Expected: `207 passed`

- [ ] **Step 4: Baseline dokumentieren — Ruff zeigt 45 + 13**

```bash
uv run ruff check app tests 2>&1 | tail -2
uv run ruff format --check app tests 2>&1 | tail -2
```
Expected:
- `Found 45 errors.`
- `13 files would be reformatted, 49 files already formatted`

---

## Task 2: Commit 1 — `ruff format` über `app/` und `tests/`

**Files:** 13 Dateien werden automatisch umformatiert:
- Modify: `app/repositories/rabattcode_repo.py`
- Modify: `app/routers/admin.py`
- Modify: `app/routers/rabattcodes.py`
- Modify: `app/routers/webhooks.py`
- Modify: `app/services/bestell_service.py`
- Modify: `app/services/email_service.py`
- Modify: `app/services/stripe_service.py`
- Modify: `tests/test_api_admin.py`
- Modify: `tests/test_api_rabattcodes.py`
- Modify: `tests/test_api_webhooks.py`
- Modify: `tests/test_csrf.py`
- Modify: `tests/test_email_service.py`
- Modify: `tests/test_rabattcode_service.py`

- [ ] **Step 1: Format-Check — zeigt welche Files drift haben**

```bash
uv run ruff format --check app tests
```
Expected: `13 files would be reformatted, 49 files already formatted`

- [ ] **Step 2: Auto-Format anwenden**

```bash
uv run ruff format app tests
```
Expected: `13 files reformatted, 49 files left unchanged`

- [ ] **Step 3: Format-Check nach Anwendung — muss clean sein**

```bash
uv run ruff format --check app tests
```
Expected: `62 files already formatted` (exit 0)

- [ ] **Step 4: Regressions-Test — alle Tests müssen grün bleiben**

```bash
uv run pytest -q
```
Expected: `207 passed`

- [ ] **Step 5: Diff inspizieren — nur Layout-Änderungen?**

```bash
git diff --stat
```
Expected: Nur dict-/Funktionsaufruf-Layout-Änderungen in den 13 Files, keine Semantik.

- [ ] **Step 6: Commit 1**

```bash
git add app/ tests/
git commit -m "chore: ruff format über app/ und tests/

Reine Layout-Angleichung der 13 Format-Drift-Files. Kein Semantik-Effekt,
alle 207 Tests bleiben grün.

Teil von #103."
```

---

## Task 3: Commit 2a — E501-Fixes in `app/` (3 Stellen)

**Files:**
- Modify: `app/routers/webhooks.py:142`
- Modify: `app/services/stripe_service.py:48`
- Modify: `app/services/rabattcode_service.py:57`

- [ ] **Step 1: Lint-Check auf `app/` — zeigt 3 E501**

```bash
uv run ruff check app --output-format=concise
```
Expected (3 Zeilen):
```
app/routers/webhooks.py:142:89: E501 Line too long (...)
app/services/rabattcode_service.py:57:89: E501 Line too long (...)
app/services/stripe_service.py:48:89: E501 Line too long (...)
```

Hinweis: Nach `ruff format` aus Task 2 können sich die Zeilennummern leicht verschoben haben. Arbeite mit den Zeilennummern, die `ruff check` jetzt meldet, nicht mit denen aus diesem Plan.

- [ ] **Step 2: Fix `app/routers/webhooks.py` — Log-Detail-JSON**

Aktuell (eine Zeile > 88 Zeichen):
```python
details=json.dumps({"von": "neu", "nach": "storniert", "grund": grund}),
```

Nachher (mehrzeilig):
```python
details=json.dumps(
    {"von": "neu", "nach": "storniert", "grund": grund}
),
```

Editiere die Datei entsprechend.

- [ ] **Step 3: Fix `app/services/stripe_service.py` — success_url f-string**

Aktuell:
```python
"success_url": f"{settings.base_url}/bestaetigung?session_id={{CHECKOUT_SESSION_ID}}",
```

Nachher:
```python
"success_url": (
    f"{settings.base_url}/bestaetigung"
    "?session_id={CHECKOUT_SESSION_ID}"
),
```

Hinweis: `{{CHECKOUT_SESSION_ID}}` ist im f-string doppelt geklammert, um ein literales `{CHECKOUT_SESSION_ID}` auszugeben. Im nicht-f-string-Teil reicht einfach geklammert.

- [ ] **Step 4: Fix `app/services/rabattcode_service.py` — Fehlermeldungs-f-string**

Aktuell:
```python
"fehler": f"Mindestbestellwert CHF {rc['mindestbestellwert_chf']:.2f} nicht erreicht.",
```

Nachher:
```python
"fehler": (
    f"Mindestbestellwert CHF {rc['mindestbestellwert_chf']:.2f} "
    "nicht erreicht."
),
```

- [ ] **Step 5: Lint-Check auf `app/` — muss clean sein**

```bash
uv run ruff check app
```
Expected: `All checks passed!`

- [ ] **Step 6: Regressions-Test**

```bash
uv run pytest -q
```
Expected: `207 passed`

- [ ] **Step 7: Stage aber NICHT committen (Commit folgt nach Task 5)**

```bash
git add app/routers/webhooks.py app/services/stripe_service.py app/services/rabattcode_service.py
git status
```
Expected: Drei Files unter "Changes to be committed".

---

## Task 4: Commit 2b — E402 + E501 in `tests/test_rabattcode_service.py`

**Files:**
- Modify: `tests/test_rabattcode_service.py` (Imports-Reorg + E501-Fixes in SQL-Strings)

Dieses File bekommt eine eigene Task weil es zwei verschiedene Fehlerarten kombiniert und die Import-Reorganisation strukturell wirkt.

- [ ] **Step 1: Ist-Stand — Fehler in dieser Datei auflisten**

```bash
uv run ruff check tests/test_rabattcode_service.py --output-format=concise
```
Expected: 9× E501 + 2× E402 (genaue Zeilennummern können nach Task 2 leicht verschoben sein).

- [ ] **Step 2: Imports an den Datei-Kopf verschieben**

Das File beginnt mit einem leeren Kopf, dann Kapitel `# --- Migration Tests ---`, später `# --- Repository Tests ---` mit einem Import dazwischen, später `# --- Service Tests ---` mit einem weiteren Import.

Nimm die zwei `from app.repositories.rabattcode_repo import (...)` und `from app.services.rabattcode_service import berechne_rabatt, pruefe_rabattcode` Zeilen und verschiebe sie an den Datei-Anfang (nach eventuellen stdlib-Imports oder Fixture-Imports, die dort schon stehen).

Die `# --- Repository Tests ---` und `# --- Service Tests ---` Kommentare bleiben als Sektions-Marker stehen, aber ohne Imports direkt darunter.

Die Import-Reihenfolge am File-Anfang soll sein:
1. ggf. existierende stdlib-/third-party-Imports
2. `from app.repositories.rabattcode_repo import (einloesung_speichern, ist_bereits_eingeloest, rabattcode_anlegen, rabattcode_laden, rabattcode_laden_by_code)`
3. `from app.services.rabattcode_service import berechne_rabatt, pruefe_rabattcode`

- [ ] **Step 3: E402-Verifikation**

```bash
uv run ruff check tests/test_rabattcode_service.py --select E402
```
Expected: `All checks passed!`

- [ ] **Step 4: E501-Fixes in SQL-INSERT-Statements**

Pattern: Die meisten E501 in diesem File sind SQL-INSERTs, bei denen zwar schon String-Concatenation verwendet wird, aber die einzelne Zeile noch zu lang ist.

Beispiel (Z.29 im Original, verschiebt sich nach Task 2 ggf.):

Aktuell:
```python
db.execute(
    "INSERT INTO bestellungen (kunde_id, zahlungsart, versandart, versandkosten_chf, total_chf) "
    "VALUES (1, 'stripe', 'versand', 9.90, 25.90)"
)
```

Nachher (Spaltenliste auf zwei Zeilen):
```python
db.execute(
    "INSERT INTO bestellungen "
    "(kunde_id, zahlungsart, versandart, versandkosten_chf, total_chf) "
    "VALUES (1, 'stripe', 'versand', 9.90, 25.90)"
)
```

Weitere E501-Stellen in diesem File betreffen:
- SELECT-Queries: gleiche Strategie (Zeile brechen, ggf. den WHERE-Teil in eigene String-Literal-Zeile).
- SQL-INSERT mit noch längeren Spaltenlisten: Spaltenliste über mehrere Zeilen verteilen.

Arbeite jede E501-Stelle so ab, dass jede resultierende Zeile ≤88 Zeichen ist. Nutze `ruff check tests/test_rabattcode_service.py` nach jedem Edit zum Gegencheck.

- [ ] **Step 5: Lint-Check auf diese Datei — muss clean sein**

```bash
uv run ruff check tests/test_rabattcode_service.py
```
Expected: `All checks passed!`

- [ ] **Step 6: Regressions-Test — nur diese Datei**

```bash
uv run pytest tests/test_rabattcode_service.py -q
```
Expected: Alle Tests aus diesem File grün.

- [ ] **Step 7: Stage**

```bash
git add tests/test_rabattcode_service.py
git status
```

---

## Task 5: Commit 2c — E501-Fixes in den restlichen 8 Test-Files + Commit 2

**Files:**
- Modify: `tests/test_abholung_bar.py` (1× E501)
- Modify: `tests/test_api_admin.py` (5× E501)
- Modify: `tests/test_api_rabattcodes.py` (3× E501)
- Modify: `tests/test_api_seiten.py` (2× E501)
- Modify: `tests/test_api_webhooks.py` (1× E501)
- Modify: `tests/test_e2e_bestellzyklus.py` (9× E501)
- Modify: `tests/test_email_service.py` (11× E501)

(Summen siehe Concise-Output aus Task 1.)

- [ ] **Step 1: Liste aller Lint-Fehler in Tests ausdrucken als Checkliste**

```bash
uv run ruff check tests --output-format=concise
```

Arbeite die Liste von oben nach unten ab.

- [ ] **Step 2: Fix-Pattern für SQL-Strings (E501 häufigster Fall)**

Muster 1 — INSERT mit langer Spaltenliste:
```python
"INSERT INTO tabelle (spalte1, spalte2, spalte3, spalte4) "
```
→ Brechen an einem Komma:
```python
"INSERT INTO tabelle "
"(spalte1, spalte2, spalte3, spalte4) "
```

Muster 2 — SELECT mit langem WHERE:
```python
row = db.execute("SELECT * FROM tabelle WHERE email = 'test@example.com'").fetchone()
```
→ Als mehrzeilig:
```python
row = db.execute(
    "SELECT * FROM tabelle WHERE email = 'test@example.com'"
).fetchone()
```

Muster 3 — Langer Docstring oder Kommentar:
```python
"""Sehr langer Docstring auf einer Zeile, der über 88 Zeichen hinausgeht und..."""
```
→ Mehrzeiliger Docstring:
```python
"""Sehr langer Docstring auf einer Zeile,
der über 88 Zeichen hinausgeht und..."""
```

Muster 4 — HTML-Assertion-String:
```python
assert "<a href='/admin/bestellung/123' class='btn'>Details</a>" in resp.text
```
→ In Variable extrahieren oder String-Concatenation nutzen:
```python
erwartet = "<a href='/admin/bestellung/123' class='btn'>Details</a>"
assert erwartet in resp.text
```

Wähle pro Stelle das Muster, das die natürliche Lesbarkeit am wenigsten stört.

- [ ] **Step 3: File für File abarbeiten — `tests/test_abholung_bar.py`**

```bash
uv run ruff check tests/test_abholung_bar.py --output-format=concise
```

Fix anwenden, dann:
```bash
uv run ruff check tests/test_abholung_bar.py
```
Expected: `All checks passed!`

- [ ] **Step 4: File für File — `tests/test_api_admin.py`**

Gleiche Prozedur: `ruff check` → fix → `ruff check`.

- [ ] **Step 5: File für File — `tests/test_api_rabattcodes.py`**

- [ ] **Step 6: File für File — `tests/test_api_seiten.py`**

- [ ] **Step 7: File für File — `tests/test_api_webhooks.py`**

- [ ] **Step 8: File für File — `tests/test_e2e_bestellzyklus.py`**

Grösstes File (9 Stellen). Empfehlung: `ruff check tests/test_e2e_bestellzyklus.py --output-format=concise` ausgeben lassen, dann jede Stelle einzeln editieren und am Ende verifizieren.

- [ ] **Step 9: File für File — `tests/test_email_service.py`**

Grösstes File nach `test_e2e_bestellzyklus.py` (11 Stellen). Die meisten davon sind SQL-INSERTs mit gleichem Schema — Muster 1 oben anwenden.

- [ ] **Step 10: Gesamt-Lint-Check**

```bash
uv run ruff check app tests
```
Expected: `All checks passed!`

- [ ] **Step 11: Gesamt-Format-Check (sicherstellen dass Edits nichts gebrochen haben)**

```bash
uv run ruff format --check app tests
```
Expected: exit 0.

Falls nicht: `uv run ruff format app tests` erneut laufen lassen und dann `ruff check` nochmal gegenprüfen (Format kann manchmal Zeilen anders umbrechen als vom Entwickler erwartet).

- [ ] **Step 12: Regressions-Test**

```bash
uv run pytest -q
```
Expected: `207 passed`

- [ ] **Step 13: Commit 2 (alle Lint-Fixes zusammen)**

```bash
git add app/ tests/
git commit -m "fix: Ruff-Lint-Violations (E501, E402) beheben

- 3× E501 in app/ (webhooks, stripe_service, rabattcode_service)
- 40× E501 in tests/ (mehrzeilige SQL-INSERTs und Docstrings)
- 2× E402 in tests/test_rabattcode_service.py (Imports an Datei-Kopf)

Keine funktionalen Änderungen. Alle 207 Tests grün.

Teil von #103."
```

Hinweis: Tasks 3 und 4 hatten bereits `git add` gemacht. Dieser `git add app/ tests/` ist idempotent und staged nun auch die in Task 5 bearbeiteten Test-Files.

---

## Task 6: Commit 3 — CI-Workflow + Makefile-Target

**Files:**
- Create: `.github/workflows/lint.yml`
- Modify: `Makefile` (neues Target `lint-all`, `.PHONY` erweitern)

- [ ] **Step 1: CI-Workflow anlegen**

Erstelle die Datei `.github/workflows/lint.yml` mit folgendem Inhalt:

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

- [ ] **Step 2: YAML-Validierung (offline, via Python)**

```bash
uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/lint.yml'))"
```
Expected: exit 0, keine Ausgabe.

- [ ] **Step 3: Makefile-Target `lint-all` hinzufügen**

Aktueller Makefile-Kopf:
```make
.PHONY: help dev test lint format migrate docs css-build css-watch
```

Ändere zu:
```make
.PHONY: help dev test lint lint-all format migrate docs css-build css-watch
```

Füge nach dem bestehenden `format`-Target folgendes neues Target ein:

```make
lint-all: ## Ruff-Check + Format-Check (gleich wie CI)
	uv run ruff check app tests
	uv run ruff format --check app tests
```

Wichtig: Der Einrückungsbefehl unter dem Target muss ein **TAB** sein, kein Spaces (Make-Konvention).

- [ ] **Step 4: `make help` testen — `lint-all` erscheint in der Liste**

```bash
make help
```
Expected: Zeile `lint-all       Ruff-Check + Format-Check (gleich wie CI)` erscheint.

- [ ] **Step 5: `make lint-all` ausführen — muss grün sein**

```bash
make lint-all
```
Expected:
- `All checks passed!`
- exit 0 (keine Format-Diffs)

- [ ] **Step 6: Commit 3**

```bash
git add .github/workflows/lint.yml Makefile
git commit -m "feat: CI-Workflow für Ruff-Gate auf PRs

- Neue .github/workflows/lint.yml: ruff check + format --check bei jedem PR
- Neues Makefile-Target 'lint-all' für lokale Reproduktion des CI-Gates

Schliesst #103."
```

---

## Task 7: End-to-End Verifikation + PR

**Files:** keine

- [ ] **Step 1: Finale Verifikationskette**

```bash
uv run ruff check app tests && \
uv run ruff format --check app tests && \
uv run pytest -q
```
Expected:
- `All checks passed!`
- `62 files already formatted`
- `207 passed`

- [ ] **Step 2: Commit-Historie prüfen**

```bash
git log --oneline main..HEAD
```
Expected: 3 Commits (oder 5 falls Tasks 3–5 einzeln committet wurden — das ist ok, aber dann in Step 4 squashen oder so lassen, wie die User-Präferenz ist).

- [ ] **Step 3: Push**

```bash
git push -u origin ruff-backlog-103
```
Expected: `Branch 'ruff-backlog-103' set up to track 'origin/ruff-backlog-103'`

- [ ] **Step 4: PR erstellen**

```bash
gh pr create --title "Ruff-Backlog Cleanup + CI-Drift-Schutz (#103)" --body "$(cat <<'BODY'
## Summary

Behebt Issue #103 (Ruff-Backlog). Big-Bang-Cleanup aller 45 Lint-Violations (43× E501, 2× E402) und 13 Format-Drift-Files plus neuer CI-Workflow, der künftigen Drift auf PRs blockiert.

## Commits

- `chore: ruff format über app/ und tests/` — Reine Layout-Angleichung, 13 Files
- `fix: Ruff-Lint-Violations (E501, E402) beheben` — 45 manuelle Fixes
- `feat: CI-Workflow für Ruff-Gate auf PRs` — GitHub Action + `make lint-all`

## Verifikation

- [x] `uv run ruff check app tests` → All checks passed!
- [x] `uv run ruff format --check app tests` → clean
- [x] `uv run pytest` → 207 passed
- [x] `make lint-all` → exit 0

## Non-Goals

Bewusst ausserhalb Scope: Weitere Ruff-Regeln (z.B. Docstring-Regeln), Pre-Commit-Hooks, Type-Checking (mypy). Kann später als separate Issues.

Spec: \`docs/superpowers/specs/2026-04-21-ruff-backlog-design.md\`
Closes #103.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
BODY
)"
```
Expected: PR-URL wird ausgegeben.

- [ ] **Step 5: CI-Run beobachten — der neue Lint-Workflow muss grün werden**

```bash
gh pr checks
```
Expected: `Lint / ruff` erscheint und läuft grün.

Falls rot: Log lesen via `gh run view <run-id> --log-failed`, Ursache beheben, erneut pushen.

- [ ] **Step 6: Code-Review anstossen (superpowers:requesting-code-review)**

Der Review-Sub-Agent prüft Spec-Konsistenz, Dokumentation und OWASP. Bei reinen Lint-Changes wenig zu beanstanden, aber Protokoll ist Pflicht laut CLAUDE.md.

- [ ] **Step 7: Nach Merge: Issue-Status, README, Memories**

Nach Merge in `main`:

```bash
gh issue close 103 --comment "Behoben via PR (siehe verlinkter PR). CI-Gate aktiv auf allen künftigen PRs."
git checkout main && git pull
git branch -d ruff-backlog-103
```

Post-Merge-Hygiene (gemäss `feedback_pause_cleanup.md`):
- GitHub Issues: #103 geschlossen, prüfen ob das andere Issues unblockt (sollte nicht, da "Blocks: nichts")
- README: kein Update nötig (rein technische Hygiene)
- Dokumentation: `docs/index.md` zeigt Spec bereits via Spec-Directory-Konvention
- Memory: ggf. ein `project_ci_gates.md` anlegen mit Hinweis „Ruff-Check ist CI-Gate seit 2026-04-21"

---

## Summary der Commit-Struktur

```
chore: ruff format über app/ und tests/          (Task 2, 13 Files)
fix:   Ruff-Lint-Violations (E501, E402) beheben (Tasks 3+4+5, 10 Files)
feat:  CI-Workflow für Ruff-Gate auf PRs         (Task 6, 2 Files)
```

3 Commits im finalen PR — falls Tasks 3/4/5 einzeln committet wurden, vor Merge optional via `git rebase -i main` zu einem Commit squashen (nur falls User das explizit wünscht; ansonsten mehr Commits lassen ist auch ok).
