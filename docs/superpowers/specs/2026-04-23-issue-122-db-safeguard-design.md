# Issue #122 — App-Safeguard gegen silent DB-Creation

**Status:** Design approved (2026-04-23)
**Issue:** [#122](https://github.com/konstantinniedermann/olivalle-webshop/issues/122)
**Relates to:** #110 (Backup-Setup), #115 (Restore-Test v1, fehlgeschlagen), #123 (Restore-Test v2)

## Kontext

Beim Restore-Test am 2026-04-23 (Issue #115) wurde ein latenter Bug entdeckt: Wenn `/data/olivalle.db` in Production fehlt, erstellt `sqlite3.connect()` per Default eine neue leere DB (`mode=rwc`). Dadurch:

1. Die laufende App macht weiter, aber jeder DB-Query wirft `no such table: …` → 500er für Kunden.
2. Beim nächsten Machine-Restart sieht `entrypoint.sh:11` (`[ ! -f "$DB_PATH" ]`) die leere DB als existierend an → **Auto-Restore aus Tigris wird übersprungen**.

Das ist genau das, was beim Test-Run passiert ist. Im echten Volume-Verlust-Szenario (Runbook-Szenario A) würde derselbe Bug den Recovery-Pfad blockieren.

## Root Cause

`sqlite3.connect(path)` hat per Default `mode=rwc` (read/write/**create**). Für Request-Handler in Production ist das `create` unerwünscht: fehlende DB = Störung, nicht Auto-Heal.

## Ziel

Request-Handler sollen bei fehlender DB mit `OperationalError` (→ HTTP 500) reagieren, statt silent eine leere DB zu erstellen. `init_db()` bleibt unverändert und nutzt weiter `create`, weil der Bootstrap-Pfad in `entrypoint.sh` darauf angewiesen ist (Erst-Deployment ohne Backup).

## Scope (YAGNI)

**In-Scope:**
- Differenzierung der Connection-Modes in `app/database.py`.
- Unit- und Integrations-Test für den Fehlerpfad.

**Out-of-Scope (bewusst, siehe Brainstorming 2026-04-23):**
- `init_db()` aus `app/main.py:18` entfernen — redundant mit `entrypoint.sh` Schritt 2, aber Uvicorn reloaded nicht von selbst, Risiko gering. Falls später auffällig: Folge-Issue.
- Eigener DB-Healthcheck / `/health`-Erweiterung — Issue #111 bei Bedarf separat.
- Schöne Fehlerseite statt generischem 500 — Szenario ist selten, primäre Recovery läuft über Machine-Restart.
- Logging-Wrapper — Uvicorn-Default-Traceback in `fly logs` reicht zur Diagnose.

## Architektur

**Einzige produktive Änderung:** `app/database.py` — aus einer Connect-Funktion werden zwei mit klarer Rollenteilung.

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


def init_db() -> None:
    conn = _connect_bootstrap()    # einzige Zeilenänderung
    try:
        ...
```

**Rationale für zwei Funktionen** (vs. Boolean-Parameter): explizite Intent-Klarheit, keine `if create:`-Verzweigung, Call-Sites bleiben unverändert. Passt zu den Architektur-Prinzipien in `CLAUDE.md` (Klare Schnittstellen, Separation of Concerns).

## Call-Sites

**Unverändert.** Alle 13 `get_db()`-Aufrufe in den 6 Routern bleiben wie sie sind und bekommen automatisch die `rw`-Connection:

- `app/routers/produkte.py:12`
- `app/routers/bestellungen.py:162, 292`
- `app/routers/admin.py:115, 158, 189, 232, 271, 314`
- `app/routers/rabattcodes.py:39, 64, 114, 150, 185`
- `app/routers/webhooks.py:24, 115`

Keine API-Änderung, keine Migration nötig.

## Datenfluss

**Normalfall (DB existiert):**
Request → Router → `get_db()` → SQLite öffnet im `rw`-Modus → Query → Response. Verhalten identisch mit heute.

**Fehlerfall (DB fehlt):**
Request → Router → `get_db()` → `sqlite3.OperationalError: unable to open database file` → Exception propagiert ungefangen → FastAPI-Default-Handler → **HTTP 500**. **Keine leere DB wird erstellt.** Beim nächsten Machine-Restart greift `entrypoint.sh` Schritt 1 (Auto-Restore aus Tigris) korrekt.

## Tests

**Neu:** `tests/test_database_missing_db.py`

1. **`test_get_db_wirft_operational_error_bei_fehlender_db`** — Unit
   - `settings.database_path` via `monkeypatch` auf Pfad in `tmp_path`, der *nicht* existiert.
   - `get_db()` aufrufen → `pytest.raises(sqlite3.OperationalError)`.
   - Assert: nach dem Aufruf existiert die DB-Datei *immer noch nicht* (der Kern des Bugs).

2. **`test_request_handler_antwortet_500_bei_fehlender_db`** — Integration
   - Eigener `TestClient` mit `database_path` auf nicht-existenten Pfad (ohne `init_db()`).
   - `GET /` (Produktliste, nutzt `get_db()`) → `response.status_code == 500`.
   - Assert: DB-Datei existiert nach dem Request weiterhin nicht.

**Bestehende Tests unverändert.** `conftest.py:73,147` ruft weiter `init_db()` auf, was jetzt intern `_connect_bootstrap()` (mode=rwc) nutzt — Fixture-Setup funktioniert wie gehabt. Request-Handler in Tests laufen mit `rw`, aber die DB existiert zu dem Zeitpunkt (von `init_db()` erstellt) — kein Problem.

**Kein eigener Test für `_connect_bootstrap()`**: Die Funktion ist 4 Zeilen, wird durch jede existierende Fixture implizit ausgeübt (jede Integration läuft über `init_db` → `_connect_bootstrap`). Dedizierter Test wäre redundant.

## Doku-Updates

- **Kein ADR.** Die Entscheidung ist lokal, 2 Funktionen, nicht architektonisch weitreichend genug für ein ADR. Docstrings im Code + dieses Spec-Dokument + Issue #122 reichen.
- **Runbook `docs/runbook-restore.md`:** Falls dort ein Abschnitt zu "leere DB nach Volume-Glitch" steht, kurz ergänzen dass die App dann 500er liefert und der Auto-Restore beim Restart sauber greift. Sonst kein Update nötig.
- **`user-stories-testplan.md`:** Prüfen (Memory-Regel), ob ein Eintrag zu DB-Fehlerverhalten existiert — vermutlich nein, da die User-Stories auf Business-Flows fokussiert sind. Falls nein: kein Eintrag nötig.

## Akzeptanzkriterien

- [ ] `get_db()` nutzt `file:...?mode=rw` URI-Connect.
- [ ] `_connect_bootstrap()` existiert mit `mode=rwc`, wird von `init_db()` aufgerufen.
- [ ] Unit-Test `test_get_db_wirft_operational_error_bei_fehlender_db` grün.
- [ ] Integration-Test `test_request_handler_antwortet_500_bei_fehlender_db` grün.
- [ ] Bestehende Tests unverändert grün (`make test`).
- [ ] `make lint-all` grün (Ruff).
- [ ] Docstrings erklären Warum (nicht nur Was) — mit Issue-Referenz.

## Risiken & Mitigation

| Risiko | Mitigation |
|---|---|
| URI-Form mit relativen Pfaden (Dev) oder Sonderzeichen bricht | `settings.database_path` ist immer ein einfacher Pfad ohne Sonderzeichen — `olivalle.db` (Dev, relativ) oder `/data/olivalle.db` (fly, absolut). Beide Formen sind per SQLite-URI-Spec (`file:{path}?mode=rw`) valide und werden vom Unit-Test mit `tmp_path` abgedeckt. |
| Tests hängen an einer globalen DB-Verbindung | Jede Fixture nutzt `tmp_path` — bestehende Isolation bleibt. |
| `init_db()` aus `main.py:18` könnte weiterhin bei Prozess-Neustart silent DB erstellen | Out-of-Scope (siehe oben). Falls sich das Verhalten in Produktion zeigt: Folge-Issue. |

## Nach-Merge

Issue #122 schliessen → `#123` (Restore-Test v2) wird entsperrt und kann geplant werden.
