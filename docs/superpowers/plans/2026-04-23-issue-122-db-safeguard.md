# Issue #122 — App-Safeguard gegen silent DB-Creation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Request-Handler sollen bei fehlender DB-Datei `OperationalError` werfen (→ HTTP 500) statt silent eine leere DB zu erstellen. `init_db()` bleibt unverändert.

**Architecture:** In `app/database.py` werden zwei klar getrennte Connect-Funktionen eingeführt: `get_db()` (mode=rw, für alle Request-Handler) und `_connect_bootstrap()` (mode=rwc, nur für `init_db`). Call-Sites in den 6 Routern bleiben identisch — sie bekommen automatisch die neue Semantik durch `get_db()`.

**Tech Stack:** Python 3 (FastAPI), SQLite (stdlib `sqlite3`), pytest, pytest `tmp_path` / `monkeypatch`.

**Spec:** `docs/superpowers/specs/2026-04-23-issue-122-db-safeguard-design.md`

---

## File Structure

- **Modify:** `app/database.py` — `get_db()` auf URI-Form mit `mode=rw` umstellen, neue private Funktion `_connect_bootstrap()` mit `mode=rwc`, `init_db()` nutzt diese.
- **Create:** `tests/test_database_missing_db.py` — Unit + Integration für Missing-DB-Pfad.

Keine weiteren Files. Kein Touch an Routern, `entrypoint.sh`, `app/main.py`, oder existierenden Tests.

---

## Task 1: Unit-Test für `get_db()` bei fehlender DB (Red)

**Files:**
- Create: `tests/test_database_missing_db.py`

- [ ] **Step 1: Failing Unit-Test schreiben**

Datei `tests/test_database_missing_db.py` anlegen mit folgendem Inhalt:

```python
import sqlite3

import pytest

from app.database import get_db


def test_get_db_wirft_operational_error_bei_fehlender_db(tmp_path, monkeypatch):
    """Fehlt die DB-Datei, MUSS get_db() OperationalError werfen und DARF
    keine leere DB anlegen (sonst wird der entrypoint.sh-Auto-Restore durch
    die Existenz einer leeren Datei blockiert — Bug aus Issue #115 / #122).
    """
    db_path = tmp_path / "does_not_exist.db"
    monkeypatch.setattr("app.config.settings.database_path", str(db_path))

    assert not db_path.exists()

    with pytest.raises(sqlite3.OperationalError):
        get_db()

    # Kern des Bugs: nach dem Aufruf darf kein File entstanden sein.
    assert not db_path.exists()
```

- [ ] **Step 2: Test ausführen, Fail verifizieren**

Run: `uv run pytest tests/test_database_missing_db.py::test_get_db_wirft_operational_error_bei_fehlender_db -v`

Expected: **FAIL** — aktuell wird `get_db()` die DB mit `mode=rwc` erstellen, kein Error, und die Datei existiert danach.

- [ ] **Step 3: Commit (Red)**

```bash
git add tests/test_database_missing_db.py
git commit -m "test: failing test for get_db() bei fehlender DB (Issue #122)"
```

---

## Task 2: `get_db()` auf `mode=rw` umstellen (Green)

**Files:**
- Modify: `app/database.py:9-14`

- [ ] **Step 1: `get_db()` umstellen**

In `app/database.py` ersetze die bestehende Funktion (Zeilen 9–14):

```python
def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
```

durch:

```python
def get_db() -> sqlite3.Connection:
    """Connection für Request-Handler. mode=rw — keine Auto-Creation.

    Fehlt die DB-Datei, wirft sqlite3 OperationalError → FastAPI antwortet mit
    500. Das verhindert, dass ein Volume-Glitch silent eine leere DB hinterlässt
    und dadurch den entrypoint.sh-Auto-Restore blockiert (Issue #122).
    """
    conn = sqlite3.connect(
        f"file:{settings.database_path}?mode=rw", uri=True
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
```

- [ ] **Step 2: Test ausführen, Pass verifizieren**

Run: `uv run pytest tests/test_database_missing_db.py::test_get_db_wirft_operational_error_bei_fehlender_db -v`

Expected: **PASS** — `get_db()` wirft `OperationalError`, keine DB-Datei entsteht.

- [ ] **Step 3: Verifizieren, dass init_db noch bricht**

Run: `uv run pytest tests/test_database_wal_mode.py -v`

Expected: **FAIL** oder mindestens **Warnung** — `init_db()` ruft noch `get_db()` auf, das jetzt `mode=rw` ist, kann also auf leerem Pfad keine DB erstellen. (Falls dieser Test auf einer leeren tmp-DB läuft, bricht er.)

Falls der Test nicht bricht, andere bestehende Tests mit leerer DB prüfen:

Run: `uv run pytest tests/test_produkt_repo.py -v --tb=short 2>&1 | head -40`

Expected: mindestens einer der Integration-Tests schlägt fehl mit `OperationalError: unable to open database file`, weil `init_db()` via `get_db()` läuft.

- [ ] **Step 4: NICHT committen**

Warten bis Task 3 fertig ist — Commit erfolgt dort mit den zwei Änderungen zusammen.

---

## Task 3: `_connect_bootstrap()` einführen, `init_db()` anpassen

**Files:**
- Modify: `app/database.py` (neue Funktion + eine Zeile in `init_db`)

- [ ] **Step 1: `_connect_bootstrap()` hinzufügen**

In `app/database.py` direkt nach der `get_db()`-Funktion einfügen (vor `_add_column_if_not_exists`):

```python
def _connect_bootstrap() -> sqlite3.Connection:
    """Connection für init_db — mode=rwc, erstellt DB falls nicht vorhanden.

    Wird nur beim Bootstrap aufgerufen (entrypoint.sh Schritt 2 → init_db;
    zusätzlich läuft init_db auch beim FastAPI-Import in app.main — idempotent).
    """
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
```

- [ ] **Step 2: `init_db()` auf `_connect_bootstrap()` umstellen**

In `app/database.py` in der `init_db()`-Funktion die erste Zeile ändern:

Von:
```python
def init_db() -> None:
    conn = get_db()
```

Zu:
```python
def init_db() -> None:
    conn = _connect_bootstrap()
```

- [ ] **Step 3: Unit-Test nochmal grün?**

Run: `uv run pytest tests/test_database_missing_db.py::test_get_db_wirft_operational_error_bei_fehlender_db -v`

Expected: **PASS** (Task-2-Test bleibt grün).

- [ ] **Step 4: Volle Test-Suite laufen lassen**

Run: `make test` (oder `uv run pytest -x`)

Expected: **ALL PASS** — alle bestehenden Tests wieder grün, weil `init_db()` die DB jetzt wieder erstellen darf.

Falls ein Test hängt oder bricht: diagnostizieren bevor weitergemacht wird. Häufigste Ursache: eine Fixture, die ohne `init_db()` eine Route aufruft.

- [ ] **Step 5: Commit (Green)**

```bash
git add app/database.py
git commit -m "feat: mode=rw für Request-Handler, mode=rwc nur noch für init_db (Issue #122)"
```

---

## Task 4: Integration-Test — Request-Handler antwortet 500

**Files:**
- Modify: `tests/test_database_missing_db.py`

- [ ] **Step 1: Integration-Test hinzufügen**

In `tests/test_database_missing_db.py` ans Ende anfügen:

```python
from fastapi.testclient import TestClient


def test_request_handler_antwortet_500_bei_fehlender_db(tmp_path, monkeypatch):
    """GET / nutzt get_db() → muss bei fehlender DB 500 antworten und darf
    keine leere DB anlegen."""
    db_path = tmp_path / "does_not_exist.db"
    monkeypatch.setattr("app.config.settings.database_path", str(db_path))
    monkeypatch.setattr("app.config.settings.cookie_secure", False)

    # Bewusst ohne init_db() — wir testen den Fehlerpfad.
    assert not db_path.exists()

    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/")

    assert response.status_code == 500
    assert not db_path.exists()
```

**Hinweis:** `raise_server_exceptions=False` ist nötig, damit der TestClient die Exception nicht nach pytest propagiert, sondern die 500-Antwort des FastAPI-Default-Handlers zurückgibt (dieses Verhalten soll der Test ja genau verifizieren).

**Zweiter Hinweis:** `app.main` wird importiert, was `init_db()` *beim Import* aufruft (`app/main.py:18`). Zum Zeitpunkt dieses Imports ist `settings.database_path` aber bereits durch `monkeypatch` auf den nicht-existenten Pfad gesetzt — `init_db()` wird die DB also anlegen (mode=rwc). Das sabotiert den Test.

**Lösung:** `from app.main import app` MUSS *vor* dem `monkeypatch.setattr` auf `database_path` stehen, damit `init_db()` auf der Default-DB läuft, nicht auf unserer Test-DB. Danach setzen wir den Pfad um, und erst dann kommt der Request. Korrigierter Code:

```python
from fastapi.testclient import TestClient


def test_request_handler_antwortet_500_bei_fehlender_db(tmp_path, monkeypatch):
    """GET / nutzt get_db() → muss bei fehlender DB 500 antworten und darf
    keine leere DB anlegen."""
    from app.main import app  # Import zuerst — init_db läuft auf Default-DB

    db_path = tmp_path / "does_not_exist.db"
    monkeypatch.setattr("app.config.settings.database_path", str(db_path))
    monkeypatch.setattr("app.config.settings.cookie_secure", False)

    assert not db_path.exists()

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/")

    assert response.status_code == 500
    assert not db_path.exists()
```

- [ ] **Step 2: Test ausführen**

Run: `uv run pytest tests/test_database_missing_db.py::test_request_handler_antwortet_500_bei_fehlender_db -v`

Expected: **PASS** — `GET /` gibt 500 zurück, der Test-DB-Pfad bleibt leer.

Falls der Test mit einem anderen Fehler bricht (z.B. 200 OK weil doch eine DB existiert): prüfen ob `init_db()` aus einer früheren Test-Runzeit eine DB unter dem Default-Pfad `olivalle.db` liegen lässt (nicht unser Problem — relevant ist nur `db_path` unter `tmp_path`).

- [ ] **Step 3: Gesamte Suite nochmal**

Run: `make test`

Expected: **ALL PASS**.

- [ ] **Step 4: Commit (Integration)**

```bash
git add tests/test_database_missing_db.py
git commit -m "test: integration test for 500 response bei fehlender DB (Issue #122)"
```

---

## Task 5: Lint & Final Check

**Files:** — (keine Änderung, nur Verifikation)

- [ ] **Step 1: Ruff laufen lassen**

Run: `make lint-all`

Expected: **exit 0** — keine Ruff-Fehler, keine Format-Abweichungen.

Falls Ruff Issues meldet: direkt fixen (`uv run ruff format` / `uv run ruff check --fix`) und in den vorherigen Commit amenden — **NICHT**, sondern als neuer Commit:

```bash
git add -p
git commit -m "style: ruff-format"
```

- [ ] **Step 2: Volle Suite nochmal**

Run: `make test`

Expected: **ALL PASS** (inkl. der 2 neuen Tests).

- [ ] **Step 3: Manuelle Smoke-Check mit Default-DB (optional, nur wenn Zweifel)**

Run: `ls -la olivalle.db 2>/dev/null`

Falls vorhanden und es stört: `rm olivalle.db` (nur lokale Dev-DB — die Produktions-DB liegt auf fly).

---

## Task 6: Docs-Review (leichtgewichtig)

**Files:**
- Möglicherweise Modify: `docs/runbook-restore.md`
- Möglicherweise Modify: `docs/user-stories-testplan.md`

- [ ] **Step 1: Runbook prüfen**

Run: `grep -n "leere DB\|empty DB\|silent" docs/runbook-restore.md || echo "no match"`

- Falls **no match**: kein Update nötig.
- Falls match: prüfen ob der Abschnitt jetzt verständlicher formuliert werden sollte ("App liefert 500er, Auto-Restore beim Restart greift"). Wenn ja: 1–2 Sätze anpassen.

- [ ] **Step 2: user-stories-testplan.md prüfen (Memory-Regel)**

Run: `grep -n -i "datenbank\|database" docs/user-stories-testplan.md || echo "no match"`

- Falls **no match**: kein Update nötig (User-Stories fokussieren auf Business-Flows).
- Falls match: prüfen ob ein Eintrag zu DB-Fehlerverhalten existiert, ggf. ergänzen.

- [ ] **Step 3: Falls Docs-Änderungen nötig waren, committen**

```bash
git add docs/
git commit -m "docs: Hinweis auf 500-Verhalten bei fehlender DB (Issue #122)"
```

Falls nichts zu ändern war: diesen Step überspringen.

---

## Task 7: PR erstellen

- [ ] **Step 1: Feature-Branch + Push**

Wenn wir in einem Worktree auf `main` arbeiten, jetzt einen Feature-Branch abziehen. Falls bereits auf Feature-Branch: nur pushen.

```bash
git status  # prüfen welcher Branch
# Falls main: neuen Branch
git checkout -b fix/issue-122-db-safeguard
git push -u origin fix/issue-122-db-safeguard
```

- [ ] **Step 2: PR öffnen**

```bash
gh pr create --title "fix: Request-Handler werfen 500 bei fehlender DB (#122)" --body "$(cat <<'EOF'
## Summary
- `get_db()` nutzt jetzt `file:{path}?mode=rw` — keine Auto-Creation einer leeren DB bei Volume-Glitch.
- Neue private `_connect_bootstrap()` (`mode=rwc`) wird von `init_db()` genutzt (Erst-Deployment bleibt funktional).
- Behebt den latenten Bug aus Restore-Test #115 (fehlgeschlagen 2026-04-23): leere DB blockierte den `entrypoint.sh`-Auto-Restore-Pfad.

Closes #122. Entsperrt #123 (Restore-Test v2).

## Test plan
- [ ] `make test` grün (inkl. 2 neuer Tests in `test_database_missing_db.py`)
- [ ] `make lint-all` grün
- [ ] Manuell: Container lokal starten mit leerer `/data/olivalle.db`, Request → 500 erwartet, DB-Datei entsteht nicht

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Review-Subagent (superpowers:requesting-code-review) anstossen**

Nach PR-Erstellung den Code-Review-Agent aufrufen (nicht inline hier, sondern als separaten Schritt vom Orchestrator).

---

## Self-Review (gefixt inline)

**Spec coverage:** Alle Akzeptanzkriterien aus dem Spec sind in Tasks 1–5 adressiert. Doku-Pfad ist Task 6.

**Placeholder-Scan:** Keine TBD/TODO/"implement later". Task 6 hat bedingte Doku-Updates mit klarem Output-Check — nicht placeholder, sondern "prüfen und ggf. anpassen". Akzeptabel.

**Type consistency:** Namen konsistent (`_connect_bootstrap`, nicht `connect_bootstrap` oder `_bootstrap_db`). `settings.database_path` durchgängig.

**Edge-Case aus Task 4:** Der Hinweis auf die Reihenfolge `from app.main import app` vs. `monkeypatch.setattr` ist essentiell — ohne das würde der Test das falsche Verhalten testen. Wurde explizit dokumentiert.
