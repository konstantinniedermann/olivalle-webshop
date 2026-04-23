# Uptime- & TLS-Monitoring Implementation Plan (#111)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Externe Frühwarnung bei App-Downtime, DB-Korruption und TLS-Ablauf für `olivalle.ch`, wiederverwendet den Healthchecks.io-Account aus #118.

**Architecture:** 3 Healthchecks.io-Checks im bestehenden Account, gepingt von 2 neuen GitHub-Action-Workflows (HTTP alle 10 min, TLS 1×/Tag). `/health` wird um DB-Touch erweitert (konsistent mit #122). `fly.toml` bekommt einen `[[http_service.checks]]`-Block für fly-internen Self-Heal. Runbook `docs/runbook-incident.md` als Triage-Leitfaden.

**Tech Stack:** FastAPI, sqlite3 (raw, nicht SQLAlchemy), pytest, uv, GitHub Actions, curl, Python `ssl`-Modul, Healthchecks.io.

**Spec:** `docs/superpowers/specs/2026-04-23-issue-111-monitoring-design.md`

---

## File Structure

| Pfad | Aktion | Verantwortung |
|---|---|---|
| `app/main.py` | Modify (Zeilen 24–26) | `/health` macht `SELECT 1`, 503 bei Fehler |
| `tests/test_health.py` | Modify (komplett ersetzen) | 2 Tests: DB ok → 200; DB weg → 503 |
| `fly.toml` | Modify (anhängen nach `[http_service]`) | `[[http_service.checks]]`-Block für fly-internen Check |
| `scripts/check_tls.py` | Create | TLS-Cert-Alter prüfen, exit 0/1 abhängig von Threshold, Ping bei OK |
| `tests/test_check_tls.py` | Create | 3 Tests: > 30 Tage → ping; < 30 Tage → kein ping; Malformed Date → klarer Fehler |
| `.github/workflows/monitor-tls.yml` | Create | Cron täglich, ruft `scripts/check_tls.py` |
| `.github/workflows/monitor-uptime.yml` | Create | Cron 10-min, curl auf `/health` + Ping bei 200 |
| `docs/runbook-incident.md` | Create | Triage-Leitfaden für Downtime-/TLS-Alarme |
| `docs/index.md` | Modify | Link auf `runbook-incident.md` |
| `docs/arc42.md` | Modify | Erwähnung des Monitoring-Setups im Betriebs-Kapitel |

---

## PR-Struktur (Übersicht)

| PR | Umfang | Tasks |
|---|---|---|
| 1 | `/health` mit DB-Touch | Task 1 |
| 2 | `fly.toml` `[[checks]]` | Task 2 |
| — | **Manuelle Setup-Schritte** (Healthchecks.io + GitHub-Secrets) | Zwischen PR 2 und PR 3 |
| 3 | Monitoring-Workflows + TLS-Skript | Tasks 3, 4, 5 |
| 4 | Runbook + Doku-Updates | Task 6 |
| — | **Smoke-Test** (manuell nach PR 3) | Task 7 |

---

## Task 1: `/health` mit DB-Touch

**Files:**
- Modify: `app/main.py:24-26`
- Modify: `tests/test_health.py` (vorhandene Datei ersetzen)

Der bestehende Test (`test_health_gibt_nur_status_zurueck`) prüft nur den Happy-Path-Response. Wir erweitern um DB-Touch-Semantik und einen Failure-Test analog zu `tests/test_database_missing_db.py`.

- [ ] **Step 1: Fehlenden Failure-Test schreiben**

`tests/test_health.py` komplett ersetzen mit:

```python
from fastapi.testclient import TestClient


def test_health_gibt_200_und_status_ok_bei_erreichbarer_db(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_gibt_503_bei_fehlender_db(tmp_path, monkeypatch):
    """Wenn die DB-Datei weg ist, MUSS /health 503 antworten statt
    fälschlicherweise 'ok' zu melden. Konsistent mit Issue #122."""
    from app.main import app

    db_path = tmp_path / "does_not_exist.db"
    monkeypatch.setattr("app.config.settings.database_path", str(db_path))
    monkeypatch.setattr("app.config.settings.cookie_secure", False)

    test_client = TestClient(app, raise_server_exceptions=False)
    response = test_client.get("/health")

    assert response.status_code == 503
    assert not db_path.exists(), "DB darf nicht angelegt werden"
```

- [ ] **Step 2: Test laufen lassen — Failure-Test schlägt fehl**

Run: `uv run pytest tests/test_health.py -v`

Expected: `test_health_gibt_503_bei_fehlender_db` FAIL (aktuelles `/health` checkt DB nicht, liefert 200).

- [ ] **Step 3: `/health` in `app/main.py` ersetzen**

Aktuelle Zeilen 24–26:

```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

Ersetzen durch:

```python
@app.get("/health")
def health():
    import sqlite3

    from fastapi import HTTPException

    from app.database import get_db

    try:
        conn = get_db()
        try:
            conn.execute("SELECT 1")
        finally:
            conn.close()
    except sqlite3.Error:
        raise HTTPException(status_code=503, detail="db unavailable")
    return {"status": "ok"}
```

Hinweis: Die Imports stehen bewusst in der Funktion (lokal), weil die
Route so früh in `app/main.py` definiert ist, dass Modul-Top-Level-Imports
die bestehende Reihenfolge durcheinanderbringen würden. Falls beim Review
ein anderes Muster präferiert wird, können die Imports nach oben gezogen
werden.

- [ ] **Step 4: Tests laufen lassen — beide grün**

Run: `uv run pytest tests/test_health.py -v`

Expected: beide Tests PASS.

- [ ] **Step 5: Regression-Check — gesamte Suite**

Run: `uv run pytest -x`

Expected: alle Tests PASS. (Besonders wichtig: `tests/test_database_missing_db.py` muss weiter grün sein.)

- [ ] **Step 6: Linting**

Run: `make lint-all`

Expected: keine Fehler.

- [ ] **Step 7: Commit**

```bash
git add app/main.py tests/test_health.py
git commit -m "feat: /health macht DB-Touch, 503 bei Fehler (#111)

Ergänzt den Liveness-Endpoint um SELECT 1 gegen SQLite.
Bei OperationalError/DatabaseError wird HTTP 503 geworfen,
konsistent mit dem in #122 etablierten Standard."
```

- [ ] **Step 8: PR 1 öffnen, warten auf Review + Merge**

```bash
git push -u origin <branch-name>
gh pr create --title "feat: /health macht DB-Touch, 503 bei Fehler (#111)" --body "Erster Schritt für Issue #111. Siehe Spec \`docs/superpowers/specs/2026-04-23-issue-111-monitoring-design.md\`."
```

---

## Task 2: `fly.toml` `[[http_service.checks]]`

**Files:**
- Modify: `fly.toml` (anhängen nach dem `[http_service]`-Block)

Keine automatisierten Tests — `fly.toml` ist Infrastruktur-Config, Verifikation erfolgt nach Deploy via `fly checks list`.

- [ ] **Step 1: Block anhängen**

`fly.toml` nach dem bestehenden `[http_service]`-Block (Zeilen 17–22) folgendes einfügen:

```toml
[[http_service.checks]]
  interval = "30s"
  timeout = "5s"
  grace_period = "10s"
  method = "GET"
  path = "/health"
```

- [ ] **Step 2: Lint**

Run: `make lint-all`

Expected: keine Fehler.

- [ ] **Step 3: Commit**

```bash
git add fly.toml
git commit -m "ops: fly-internen Healthcheck auf /health konfigurieren (#111)

fly restartet die Machine automatisch bei 3 aufeinanderfolgenden
Fehlern. Ergänzt — nicht ersetzt — das externe Monitoring."
```

- [ ] **Step 4: PR 2 öffnen, Review + Merge abwarten**

```bash
git push -u origin <branch-name>
gh pr create --title "ops: fly-internen Healthcheck auf /health (#111)" --body "Teil 2 von Issue #111."
```

- [ ] **Step 5: Nach Deploy verifizieren**

Run: `fly checks list -a olivalle`

Expected: Eintrag für `/health` als `passing` sichtbar.

---

## Manuelle Setup-Schritte (zwischen PR 2 und PR 3)

**Diese Schritte führt der Entwickler manuell aus — kein Code, keine Tests.**

- [ ] **Step 1: Healthchecks.io — Check `olivalle-http-uptime` anlegen**

1. In Healthchecks.io einloggen (gleicher Account wie `olivalle-litestream-heartbeat`)
2. "Add Check" → Name: `olivalle-http-uptime`
3. Schedule: "Simple" / Period 10 min, Grace 20 min
4. Ping-URL kopieren (Format: `https://hc-ping.com/<uuid>`)
5. Integrations → E-Mail `konstantin.niedermann@gmail.com` zuweisen

- [ ] **Step 2: Healthchecks.io — Check `olivalle-tls-expiry` anlegen**

1. "Add Check" → Name: `olivalle-tls-expiry`
2. Schedule: "Simple" / Period 1 day, Grace 1 day
3. Ping-URL kopieren
4. Integrations → E-Mail `konstantin.niedermann@gmail.com` zuweisen

- [ ] **Step 3: GitHub Repo-Secrets eintragen**

Im Repo auf GitHub: Settings → Secrets and variables → Actions → New repository secret.

Folgende zwei Secrets anlegen:

| Name | Wert |
|---|---|
| `HC_PING_URL_HTTP` | Ping-URL aus Step 1 |
| `HC_PING_URL_TLS` | Ping-URL aus Step 2 |

---

## Task 3: `scripts/check_tls.py` + Tests

**Files:**
- Create: `scripts/check_tls.py`
- Create: `tests/test_check_tls.py`

Analog zu `scripts/check_backup.py` / `tests/test_check_backup.py` aus #118:
das Skript liest Konfiguration aus Env-Vars, pingt Healthchecks.io selbst
bei OK, exit 1 bei Problem (kein Ping → Healthchecks.io alarmiert).

- [ ] **Step 1: Tests schreiben (TDD, Tests zuerst)**

Create `tests/test_check_tls.py`:

```python
"""Tests für scripts/check_tls.py (Issue #111)."""

import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

# scripts/ auf sys.path, damit `import check_tls` funktioniert
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


def _fake_cert_with_notafter(days_from_now: int) -> dict:
    """Baut ein cert-Dict im Format zurück, wie ssock.getpeercert() es liefert."""
    not_after = datetime.now(timezone.utc) + timedelta(days=days_from_now)
    return {"notAfter": not_after.strftime("%b %d %H:%M:%S %Y GMT")}


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("HEALTHCHECKS_URL_TLS", "https://hc-ping.example/tls-uuid")


def test_cert_frisch_triggert_ping(env):
    import check_tls

    with patch("check_tls._get_cert", return_value=_fake_cert_with_notafter(60)):
        with patch("check_tls.urlopen") as mock_urlopen:
            exit_code = check_tls.main()

    assert exit_code == 0
    mock_urlopen.assert_called_once()
    url = mock_urlopen.call_args[0][0]
    assert url == "https://hc-ping.example/tls-uuid"


def test_cert_laeuft_bald_ab_kein_ping(env):
    import check_tls

    with patch("check_tls._get_cert", return_value=_fake_cert_with_notafter(10)):
        with patch("check_tls.urlopen") as mock_urlopen:
            exit_code = check_tls.main()

    assert exit_code == 1
    mock_urlopen.assert_not_called()


def test_cert_mit_malformed_date_wirft_klar(env):
    import check_tls

    with patch("check_tls._get_cert", return_value={"notAfter": "not-a-date"}):
        with pytest.raises(ValueError):
            check_tls.main()
```

- [ ] **Step 2: Tests laufen lassen — alle fehlen, weil Skript nicht existiert**

Run: `uv run pytest tests/test_check_tls.py -v`

Expected: 3× FAIL mit `ModuleNotFoundError: No module named 'check_tls'`.

- [ ] **Step 3: Skript schreiben**

Create `scripts/check_tls.py`:

```python
"""TLS-Cert-Monitoring für olivalle.ch (Issue #111).

Prüft die Restlaufzeit des TLS-Zertifikats und pingt Healthchecks.io
bei mindestens `THRESHOLD_DAYS` Tagen Restlaufzeit. Bei Unterschreitung
wird kein Ping abgesetzt — Healthchecks.io alarmiert dann nach Ablauf
der Grace-Period per E-Mail.
"""

import os
import socket
import ssl
import sys
from datetime import datetime, timezone
from urllib.request import urlopen

HOST = "olivalle.ch"
PORT = 443
THRESHOLD_DAYS = 30


def _get_cert(host: str, port: int) -> dict:
    """TLS-Handshake + Peer-Cert holen. Isoliert für Test-Mocking."""
    ctx = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=10) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ssock:
            return ssock.getpeercert()


def _days_until_expiry(cert: dict) -> int:
    not_after = datetime.strptime(
        cert["notAfter"], "%b %d %H:%M:%S %Y %Z"
    ).replace(tzinfo=timezone.utc)
    return (not_after - datetime.now(timezone.utc)).days


def main() -> int:
    cert = _get_cert(HOST, PORT)
    days_left = _days_until_expiry(cert)
    print(f"TLS cert for {HOST}: {days_left} days left (threshold: {THRESHOLD_DAYS})")

    if days_left < THRESHOLD_DAYS:
        return 1

    ping_url = os.environ["HEALTHCHECKS_URL_TLS"]
    with urlopen(ping_url, timeout=10) as resp:
        print(f"Healthchecks.io ping: {resp.status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Tests laufen lassen — grün**

Run: `uv run pytest tests/test_check_tls.py -v`

Expected: 3× PASS.

- [ ] **Step 5: Smoke-Test lokal (optional)**

```bash
HEALTHCHECKS_URL_TLS="https://httpbin.org/status/200" uv run python scripts/check_tls.py
```

Expected: Ausgabe `TLS cert for olivalle.ch: <N> days left (threshold: 30)` + `Healthchecks.io ping: 200`, exit 0.

Falls olivalle.ch gerade unter 30 Tagen läge: exit 1 ohne Ping (Alarm-Semantik testen).

- [ ] **Step 6: Linting**

Run: `make lint-all`

Expected: keine Fehler.

- [ ] **Step 7: Commit**

```bash
git add scripts/check_tls.py tests/test_check_tls.py
git commit -m "feat: scripts/check_tls.py für TLS-Ablauf-Monitoring (#111)

Pingt Healthchecks.io bei Restlaufzeit >= 30 Tagen; kein Ping
bei Unterschreitung → Healthchecks.io alarmiert nach Grace.
Analog zu scripts/check_backup.py aus #118."
```

---

## Task 4: Workflow `monitor-tls.yml`

**Files:**
- Create: `.github/workflows/monitor-tls.yml`

Muster aus `.github/workflows/backup-check.yml` übernehmen (SHA-Pinning,
uv-Setup, FORCE_JAVASCRIPT_ACTIONS_TO_NODE24).

- [ ] **Step 1: Workflow-Datei schreiben**

Create `.github/workflows/monitor-tls.yml`:

```yaml
name: TLS-Monitor

on:
  schedule:
    - cron: '23 5 * * *'
  workflow_dispatch:

env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true

permissions:
  contents: read

jobs:
  check:
    name: Prüft TLS-Cert-Restlaufzeit von olivalle.ch
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd  # v6.0.2

      - name: Install uv
        uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b  # v8.1.0
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: uv sync --extra dev

      - name: Check TLS cert freshness
        run: uv run python scripts/check_tls.py
        env:
          HEALTHCHECKS_URL_TLS: ${{ secrets.HC_PING_URL_TLS }}
```

- [ ] **Step 2: Lint — actionlint via lint.yml**

Run: `make lint-all` (enthält actionlint-Lauf)

Expected: keine Fehler.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/monitor-tls.yml
git commit -m "feat: GitHub Action für TLS-Cert-Monitoring (#111)

Täglicher Cron ruft scripts/check_tls.py, das bei >= 30 Tagen
Restlaufzeit an Healthchecks.io pingt."
```

---

## Task 5: Workflow `monitor-uptime.yml`

**Files:**
- Create: `.github/workflows/monitor-uptime.yml`

Hier bewusst **kein** Python-Skript — die Logik ist "HTTP 200?", das
beherrscht `curl --fail` nativ. Eine Python-Wrapper-Schicht wäre hier
Zeremonie ohne Gewinn (siehe Spec D5).

- [ ] **Step 1: Workflow-Datei schreiben**

Create `.github/workflows/monitor-uptime.yml`:

```yaml
name: Uptime-Monitor

on:
  schedule:
    - cron: '*/10 * * * *'
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: monitor-uptime
  cancel-in-progress: false

jobs:
  check:
    name: Prüft HTTP-Erreichbarkeit von olivalle.ch
    runs-on: ubuntu-latest
    timeout-minutes: 3
    steps:
      - name: Probe /health
        run: curl --fail --max-time 10 https://olivalle.ch/health

      - name: Ping Healthchecks.io
        if: success()
        run: curl --fail --max-time 10 "${HC_URL}"
        env:
          HC_URL: ${{ secrets.HC_PING_URL_HTTP }}
```

Hinweis: Secret via `env:` ausgereicht (nicht inline in `run:`), damit
Bash keine Shell-Expansion auf die URL macht (GitHub-Actions-Best-Practice).

- [ ] **Step 2: Lint**

Run: `make lint-all`

Expected: keine Fehler.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/monitor-uptime.yml
git commit -m "feat: GitHub Action für HTTP-Uptime-Monitoring (#111)

Cron alle 10 min: curl /health, bei 200 Ping an Healthchecks.io.
Time-to-Alarm: 10-30 min bei echtem Ausfall."
```

- [ ] **Step 4: PR 3 öffnen (enthält Tasks 3 + 4 + 5)**

```bash
git push -u origin <branch-name>
gh pr create --title "feat: HTTP- und TLS-Monitoring via GitHub Actions (#111)" --body "Teil 3 von #111. Setzt voraus: Healthchecks.io-Checks + GitHub-Secrets sind manuell angelegt (siehe Spec, Abschnitt 'Implementierungs-Reihenfolge')."
```

- [ ] **Step 5: Nach Merge — ersten Workflow-Lauf manuell triggern**

```bash
gh workflow run monitor-uptime.yml
gh workflow run monitor-tls.yml
```

Healthchecks.io-Dashboard öffnen — beide Checks sollten innerhalb
1–2 min einen Ping registrieren.

---

## Task 6: Runbook `docs/runbook-incident.md`

**Files:**
- Create: `docs/runbook-incident.md`
- Modify: `docs/index.md`
- Modify: `docs/arc42.md`

Orientierung an `docs/runbook-restore.md` — gleiches Layout, damit das
Betriebs-Handbuch konsistent bleibt.

- [ ] **Step 1: Runbook-Datei schreiben**

Create `docs/runbook-incident.md`:

````markdown
# Runbook: Incident-Triage für Olivalle

**Ziel-Leser:** Entwickler. Szenarien A–C erfordern fly-CLI-Zugang.

**Siehe auch:** [`runbook-restore.md`](runbook-restore.md), [`adr-backup-strategie.md`](adr-backup-strategie.md)

## Zugänge, die nötig sind

| Was | Wo | Wer hat Zugriff |
|---|---|---|
| fly-Account (olivalle-App) | https://fly.io | Entwickler |
| Healthchecks.io | https://healthchecks.io | Entwickler |
| Domain-Registrar (DNS) | siehe `adr-domain-registrar.md` | Entwickler |
| GitHub-Repo | https://github.com/konstantinniedermann/olivalle-webshop | Entwickler |

---

## Alarm kam rein — was jetzt?

1. **Browser-Test:** `https://olivalle.ch/health` aufrufen.
   - 200 `{"status": "ok"}` → False-Positive oder bereits selbst-resolved → Schritt 5.
   - 503 → Szenario A.
   - Timeout/Connection refused → Szenario B.
   - TLS-Fehler im Browser → Szenario C.
2. **fly-Status:** `fly status -a olivalle` und `fly logs -a olivalle`.
3. **Szenario auswählen** (unten).
4. **Nach Fix:** Browser-Test wiederholen, Healthchecks.io-Dashboard kontrollieren.
5. **False-Positive?** Kein Handlungsbedarf — Healthchecks.io selbst-resolved beim nächsten erfolgreichen Ping.

---

## Szenario A — 503 vom Health-Check (DB-Problem)

**Symptom:** `/health` antwortet 503, App-Prozess läuft aber.

**Ursache meist:** SQLite-DB fehlt oder ist korrupt (Volume-Detach,
Permission, File-System-Fehler).

```bash
fly logs -a olivalle              # Hinweise: OperationalError, "unable to open database file"?
fly ssh console -a olivalle       # In die Machine einloggen
ls -la /data/                     # Ist olivalle.db vorhanden und > 0 Byte?
```

Wenn DB fehlt oder offensichtlich defekt:
**→ [`runbook-restore.md`](runbook-restore.md), Szenario A oder B.**

---

## Szenario B — Timeout / Connection refused (Machine tot)

**Symptom:** Keine HTTP-Antwort, Browser zeigt Timeout oder "Connection refused".

```bash
fly status -a olivalle            # Running? Failed?
fly machine list -a olivalle
fly logs -a olivalle --since 1h
```

Häufige Ursachen + Reaktion:

| Beobachtung | Aktion |
|---|---|
| Machine "stopped" | `fly machine start <id>` |
| Machine "crashed" in Loop | `fly deploy` — Image-Problem, Neubau |
| `out of memory` im Log | RAM upsizen in `fly.toml` oder Memory-Leak-Debug |
| fly-Region-Ausfall | https://status.flyio.net prüfen, warten |

---

## Szenario C — TLS-Alarm (`olivalle-tls-expiry`)

**Symptom:** Alarm-Mail von Healthchecks.io mit Check-Name `olivalle-tls-expiry`.
Restlaufzeit des TLS-Zertifikats ist unter 30 Tage gefallen.

**Diagnose:**

```bash
echo | openssl s_client -connect olivalle.ch:443 -servername olivalle.ch 2>/dev/null | openssl x509 -noout -dates
fly certs list -a olivalle
fly certs check olivalle.ch -a olivalle
```

**Aktion:**

- fly renewed Let's Encrypt automatisch. Wenn das nicht passiert:
  - DNS-Records auf Registrar-Seite prüfen (A/AAAA → fly-IP; CAA-Record erlaubt Let's Encrypt?).
  - `fly certs check olivalle.ch` zeigt fehlschlagende Challenges.
- Notfalls: `fly certs remove olivalle.ch && fly certs add olivalle.ch` (Vorsicht: DNS muss passen, sonst bleibt die Seite vorübergehend ohne Cert).
- Bei Registrar-Problemen → `adr-domain-registrar.md` konsultieren.

---

## Szenario D — Healthchecks.io meldet Silence, aber Shop erreichbar

**Symptom:** Alarm für `olivalle-http-uptime` oder `olivalle-tls-expiry`, aber
Browser kann olivalle.ch normal aufrufen.

**Ursache meist:** GitHub-Actions-Runner-Queue verzögert, oder Workflow
deaktiviert/kaputt.

```bash
gh run list --workflow monitor-uptime.yml --limit 5
gh run list --workflow monitor-tls.yml --limit 5
```

- Wenn Runs ausfallen/fehlen: GitHub-Status https://www.githubstatus.com prüfen.
- Wenn Runs rot sind: Log öffnen, Ursache fixen.
- Healthchecks.io resolved automatisch beim nächsten erfolgreichen Ping — keine manuelle Aktion nötig ausser Ursachen-Fix.

---

## Verifikation der Monitoring-Kette (regelmässig, z.B. 1×/Quartal)

1. `fly checks list -a olivalle` → `/health`-Check passing.
2. GitHub Actions-Tab → grüne Runs für beide Monitor-Workflows.
3. Healthchecks.io-Dashboard → drei Checks (`litestream-heartbeat`, `http-uptime`, `tls-expiry`) zeigen "up".
4. Test-Alarm auslösen:
   - In Healthchecks.io einen Check manuell auf "pause" stellen.
   - Nach Grace-Period E-Mail-Eingang prüfen.
   - Check wieder "resume".

---

## Eskalation

| Wann | An wen |
|---|---|
| fly-Machine nicht wiederherstellbar | fly-Community-Support: https://community.fly.io |
| Domain-Problem | Registrar (siehe `adr-domain-registrar.md`) |
| DB korrupt + Backup ebenfalls defekt | SH informieren, letzter manueller Export? |
````

- [ ] **Step 2: `docs/index.md` erweitern**

Im Abschnitt "Runbooks" (oder analoger Stelle) folgenden Link einfügen:

```markdown
- [`runbook-incident.md`](runbook-incident.md) — Triage bei Downtime-/TLS-Alarmen
```

Falls der Abschnitt noch nicht existiert, analog zum bestehenden
`runbook-restore.md`-Link strukturieren. Vor dem Edit einmal den
aktuellen Inhalt von `docs/index.md` lesen und die bestehende Struktur
respektieren.

- [ ] **Step 3: `docs/arc42.md` erweitern**

Im Betriebs-Kapitel (vermutlich "Laufzeitsicht" oder "Betrieb") einen
kurzen Absatz zum Monitoring einfügen:

```markdown
### Monitoring & Alarmierung

- **fly-internes Self-Heal:** `[[http_service.checks]]` in `fly.toml` — Machine-Restart bei wiederholten Fehlern.
- **Externes HTTP-Monitoring:** GitHub Action `monitor-uptime.yml` alle 10 min, Alarm via Healthchecks.io bei fehlendem Ping (Time-to-Alarm: 10–30 min).
- **TLS-Ablauf:** GitHub Action `monitor-tls.yml` täglich, Alarm bei < 30 Tagen Restlaufzeit.
- **Backup-Monitoring:** siehe #118, `olivalle-litestream-heartbeat`.
- **Runbook:** `docs/runbook-incident.md`.
```

Vor dem Edit einmal `docs/arc42.md` inspizieren, passende Stelle suchen,
Format an Bestand anpassen.

- [ ] **Step 4: Links + Markdown-Lint prüfen**

Run: `make lint-all`

Expected: keine Fehler.

- [ ] **Step 5: Commit**

```bash
git add docs/runbook-incident.md docs/index.md docs/arc42.md
git commit -m "docs: Runbook für Incident-Triage (#111)

Triage-Leitfaden für die vier Szenarien A-D (DB-Problem,
Machine down, TLS, False-Positive). Verknüpft mit arc42
und index. Schliesst #111."
```

- [ ] **Step 6: PR 4 öffnen, Review + Merge**

```bash
git push -u origin <branch-name>
gh pr create --title "docs: Runbook für Incident-Triage (#111)" --body "Letzter Teil von #111. Closes #111."
```

---

## Task 7: End-to-End Smoke-Test (nach allen Merges)

**Kein Code-Task, nur manuelle Verifikation.**

- [ ] **Step 1: `fly checks list -a olivalle`** — `/health` passing.

- [ ] **Step 2: GitHub Actions-Tab** — beide Monitor-Workflows haben grüne Runs in den letzten 15 min.

- [ ] **Step 3: Healthchecks.io** — drei Checks "up", letzte Pings aktuell.

- [ ] **Step 4: Test-Pausierung**

In Healthchecks.io `olivalle-http-uptime` auf "pause" stellen (oder Grace kurzzeitig auf 1 min reduzieren), warten bis E-Mail kommt, Check wieder "resume".

Erwartung: E-Mail-Alarm bei `konstantin.niedermann@gmail.com`, korrekter Betreff, Link auf Dashboard.

- [ ] **Step 5: Memory aktualisieren**

In `/Users/KN/.claude/projects/-Users-KN-Dropbox-Privat-CAS-projekte-olivalle/memory/`:

Entweder neue Datei `project_monitoring_setup.md` anlegen, oder
bestehende `project_backup_setup.md` erweitern. Inhalt:

- 3 Healthchecks.io-Checks (Namen, Intervall, Grace)
- Secrets: `HC_PING_URL_HTTP`, `HC_PING_URL_TLS` (GitHub Repo-Secrets)
- Alarm-Empfänger: konstantin.niedermann@gmail.com
- Time-to-Alarm: ~30 min HTTP, ~1 Tag TLS
- Runbook-Pfad: `docs/runbook-incident.md`

Entsprechenden Eintrag in `MEMORY.md`-Index ergänzen.

- [ ] **Step 6: GitHub-Issue schliessen**

Wenn nicht bereits automatisch via "Closes #111" in PR 4:

```bash
gh issue close 111 --comment "Alle 4 PRs gemerged, Smoke-Test bestanden. Monitoring-Stack aktiv."
```

---

## Abhängigkeiten & Hinweise für den ausführenden Agenten

- **Reihenfolge strikt einhalten:** Task 3/4/5 setzen voraus, dass die Healthchecks.io-Ping-URLs als GitHub-Secrets existieren — sonst scheitern die Workflows.
- **SHA-Pinning:** Neue/geänderte `uses:`-Zeilen in Workflows immer SHA-gepinnt mit Versions-Kommentar (Muster aus `.github/workflows/backup-check.yml` übernehmen).
- **Secrets:** Niemals inline in Code — immer via `${{ secrets.NAME }}` oder `env:`-Mapping.
- **Tests:** `uv run pytest` ist der kanonische Weg (siehe `Makefile`). Vor Commits immer `make lint-all` + `uv run pytest -x`.
- **Commits:** Eine logische Änderung pro Commit, Präfix `feat:`/`fix:`/`docs:`/`ops:` gemäss Commit-Konvention.
- **PRs:** Je Task-Gruppe einen PR (siehe PR-Struktur-Tabelle oben).
