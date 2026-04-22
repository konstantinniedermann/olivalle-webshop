# Externes Backup-Monitoring — Implementation Plan (Issue #118)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Backup-Monitoring vom Server (`entrypoint.sh`) in eine scheduled GitHub Action migrieren, die via S3-API bei Tigris die Frische des Backups prüft und Healthchecks.io pingt.

**Architecture:** Scheduled GitHub Action (1×/Tag) ruft Python-Skript auf, das mit boto3 das neueste Objekt im Tigris-Bucket `olivalle-backup` prüft. Ist es < 24 h alt, wird Healthchecks.io gepingt; sonst silent skip. Grace 25 h auf Healthchecks.io-Seite alarmiert per E-Mail. Der Heartbeat-Loop in `entrypoint.sh` wird ersatzlos entfernt.

**Tech Stack:** Python 3.13, boto3, moto (S3-Mock), pytest, GitHub Actions, Tigris S3-API, Healthchecks.io

**Spec:** [`docs/superpowers/specs/2026-04-22-issue-118-backup-monitoring-design.md`](../specs/2026-04-22-issue-118-backup-monitoring-design.md)

---

## File Structure

**Neu:**
- `scripts/check_backup.py` — Threshold-Check + Ping-Logik (importierbar + CLI-Entry-Point)
- `tests/test_check_backup.py` — 4 Unit-Tests mit moto + monkeypatch
- `.github/workflows/backup-check.yml` — Daily Cron + workflow_dispatch

**Modifiziert:**
- `pyproject.toml` — `boto3`, `moto` zu Dev-Dependencies
- `entrypoint.sh` — Zeilen 22-32 (Heartbeat-Loop) entfernen
- `docs/adr-backup-strategie.md` — zweiter Nachtrag (Monitoring-Umbau)
- `docs/runbook-restore.md` — Abschnitt "Heartbeat-Alert" → "Backup-Monitoring-Alarm"
- `README.md` — Zeile im Backup-Abschnitt ergänzen

**Operational (nicht im Code, via Checkliste in Task 11):**
- GitHub Repo-Secrets setzen (3 Secrets)
- Healthchecks.io Period/Grace umkonfigurieren + unpausen
- `fly secrets unset HEALTHCHECKS_URL`

---

## Task 1: Feature-Branch + Dev-Dependencies

**Files:**
- Modify: `pyproject.toml` (`[project.optional-dependencies].dev`)

- [ ] **Step 1: Feature-Branch anlegen**

```bash
git checkout -b feat/118-external-backup-monitoring
```

- [ ] **Step 2: Dev-Dependencies ergänzen**

In `pyproject.toml` innerhalb `[project.optional-dependencies].dev` die Liste so anpassen:

```toml
dev = [
    "pytest>=8",
    "httpx>=0.28",
    "ruff>=0.9",
    "boto3>=1.34",
    "moto[s3]>=5.0",
]
```

- [ ] **Step 3: Dependencies installieren**

```bash
uv sync --extra dev
```

Expected: `uv.lock` aktualisiert, neue Pakete installiert.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat(deps): boto3 + moto als dev-deps für Backup-Monitoring (#118)"
```

---

## Task 2: Test + Implementation — Happy Path (Fresh Object → Ping)

**Files:**
- Create: `tests/test_check_backup.py`
- Create: `scripts/check_backup.py`

- [ ] **Step 1: Failing Test schreiben**

Datei `tests/test_check_backup.py` anlegen:

```python
"""Tests für scripts/check_backup.py (Issue #118)."""
import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import boto3
import pytest
from moto import mock_aws

BUCKET = "olivalle-backup"
PREFIX = "olivalle/"
ENDPOINT = "https://fly.storage.tigris.dev"

# scripts/ muss auf sys.path, damit `import check_backup` funktioniert
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


@pytest.fixture
def env(monkeypatch):
    """Setzt die 3 Env-Vars, die das Skript erwartet."""
    monkeypatch.setenv("LITESTREAM_ACCESS_KEY_ID", "test-key")
    monkeypatch.setenv("LITESTREAM_SECRET_ACCESS_KEY", "test-secret")
    monkeypatch.setenv("HEALTHCHECKS_URL", "https://hc-ping.example/abc")


def _put_object(s3, key: str, age_hours: float) -> None:
    """Legt ein Objekt mit künstlichem LastModified ab. Moto setzt
    LastModified auf now(); wir stellen das per freeze_time nicht um,
    sondern nutzen per-test-Zeit-Kontext via Body + LastModified-Check."""
    s3.put_object(Bucket=BUCKET, Key=key, Body=b"x")
    # Hinweis: moto setzt LastModified automatisch auf now(UTC).
    # Für age-Tests: wir setzen das THRESHOLD_HOURS dynamisch oder
    # patchen datetime.now() im Modul.


@mock_aws
def test_fresh_object_triggers_ping(env):
    """Frisches Objekt (jünger als Threshold) → Ping wird gesendet."""
    s3 = boto3.client("s3", endpoint_url=ENDPOINT, region_name="auto")
    s3.create_bucket(Bucket=BUCKET)
    s3.put_object(Bucket=BUCKET, Key=f"{PREFIX}snapshot-latest", Body=b"data")

    import check_backup

    with patch("urllib.request.urlopen") as mock_urlopen:
        rc = check_backup.main()

    assert rc == 0
    mock_urlopen.assert_called_once()
    args, _ = mock_urlopen.call_args
    assert args[0] == "https://hc-ping.example/abc"
```

- [ ] **Step 2: Test laufen lassen — erwartet FAIL**

```bash
uv run pytest tests/test_check_backup.py::test_fresh_object_triggers_ping -v
```

Expected: `ModuleNotFoundError: No module named 'check_backup'` (weil Skript noch nicht existiert).

- [ ] **Step 3: Minimales Skript implementieren**

Datei `scripts/check_backup.py` anlegen:

```python
"""Prüft, ob Tigris-Backup frisch ist, und pingt Healthchecks.io.

Issue #118. Entwurfsdokument:
docs/superpowers/specs/2026-04-22-issue-118-backup-monitoring-design.md
"""

from __future__ import annotations

import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

import boto3

BUCKET = "olivalle-backup"
PREFIX = "olivalle/"
ENDPOINT = "https://fly.storage.tigris.dev"
THRESHOLD_HOURS = 24


def _newest_object_age(s3) -> timedelta | None:
    """Alter des neuesten Objekts im Bucket. None falls Bucket leer."""
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)
    contents = resp.get("Contents", [])
    if not contents:
        return None
    newest = max(o["LastModified"] for o in contents)
    return datetime.now(timezone.utc) - newest


def main() -> int:
    s3 = boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        region_name="auto",
        aws_access_key_id=os.environ["LITESTREAM_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["LITESTREAM_SECRET_ACCESS_KEY"],
    )
    age = _newest_object_age(s3)
    if age is None or age > timedelta(hours=THRESHOLD_HOURS):
        print(f"[check_backup] stale or empty: age={age}")
        return 0
    urllib.request.urlopen(os.environ["HEALTHCHECKS_URL"], timeout=10)
    print(f"[check_backup] ok, ping sent. age={age}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Test laufen lassen — erwartet PASS**

```bash
uv run pytest tests/test_check_backup.py::test_fresh_object_triggers_ping -v
```

Expected: `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add scripts/check_backup.py tests/test_check_backup.py
git commit -m "feat(scripts): check_backup Happy Path — frisches Objekt triggert Ping (#118)"
```

---

## Task 3: Test — Stale Object → Silent Skip

**Files:**
- Modify: `tests/test_check_backup.py` (neuer Test)

**Hinweis (Stand nach Task 2):** Tests verwenden `MagicMock` auf `boto3.client` statt moto — moto kann Calls mit custom `endpoint_url` nicht sauber mocken. Hilfsfunktion `_make_s3_with_object(age)` aus Task 2 wird hier genutzt.

- [ ] **Step 1: Failing Test schreiben**

An `tests/test_check_backup.py` anhängen (nach `test_fresh_object_triggers_ping`):

```python
def test_stale_object_skips_ping(env):
    """Objekt > 24h alt → kein Ping."""
    import check_backup

    fake_s3 = _make_s3_with_object(timedelta(hours=30))
    with (
        patch.object(check_backup.boto3, "client", return_value=fake_s3),
        patch("urllib.request.urlopen") as mock_urlopen,
    ):
        rc = check_backup.main()

    assert rc == 0
    mock_urlopen.assert_not_called()
```

- [ ] **Step 2: Test laufen lassen — erwartet PASS**

```bash
uv run pytest tests/test_check_backup.py::test_stale_object_skips_ping -v
```

Expected: `PASSED` (die Logik `age > THRESHOLD_HOURS` ist bereits aus Task 2 da).

- [ ] **Step 3: Alle Tests laufen lassen — nichts kaputt gemacht**

```bash
uv run pytest tests/test_check_backup.py -v
```

Expected: 2 PASSED.

- [ ] **Step 4: Commit**

```bash
git add tests/test_check_backup.py
git commit -m "test: stale object skippt Ping (#118)"
```

---

## Task 4: Test — Empty Bucket → Silent Skip

**Files:**
- Modify: `tests/test_check_backup.py`

- [ ] **Step 1: Failing Test schreiben**

An `tests/test_check_backup.py` anhängen:

```python
def test_empty_bucket_skips_ping(env):
    """Leerer Bucket → kein Ping, exit 0."""
    import check_backup

    fake_s3 = _make_s3_with_object(None)
    with (
        patch.object(check_backup.boto3, "client", return_value=fake_s3),
        patch("urllib.request.urlopen") as mock_urlopen,
    ):
        rc = check_backup.main()

    assert rc == 0
    mock_urlopen.assert_not_called()
```

- [ ] **Step 2: Test laufen lassen — erwartet PASS**

```bash
uv run pytest tests/test_check_backup.py::test_empty_bucket_skips_ping -v
```

Expected: `PASSED` (die Logik `age is None` ist bereits aus Task 2 da).

- [ ] **Step 3: Commit**

```bash
git add tests/test_check_backup.py
git commit -m "test: empty bucket skippt Ping (#118)"
```

---

## Task 5: Test + Implementation — API-Fehler → Silent Skip

**Files:**
- Modify: `tests/test_check_backup.py`
- Modify: `scripts/check_backup.py` (Try/Except für API-Call hinzufügen)

- [ ] **Step 1: Failing Test schreiben**

An `tests/test_check_backup.py` anhängen:

```python
def test_api_error_silent_skip(env, monkeypatch, capsys):
    """boto3.client wirft Exception → kein Ping, exit 0, Log enthält 'tigris unreachable'."""
    import check_backup

    def boom(*args, **kwargs):
        raise RuntimeError("simulated tigris outage")

    with (
        patch.object(check_backup.boto3, "client", side_effect=boom),
        patch("urllib.request.urlopen") as mock_urlopen,
    ):
        rc = check_backup.main()

    assert rc == 0
    mock_urlopen.assert_not_called()
    captured = capsys.readouterr()
    assert "tigris unreachable" in captured.err
```

- [ ] **Step 2: Test laufen lassen — erwartet FAIL**

```bash
uv run pytest tests/test_check_backup.py::test_api_error_silent_skip -v
```

Expected: `FAIL — RuntimeError: simulated tigris outage` (keine Exception-Handhabung im Skript).

- [ ] **Step 3: Try/Except in `scripts/check_backup.py` einbauen**

In `scripts/check_backup.py` die `main()`-Funktion ersetzen durch:

```python
def main() -> int:
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=ENDPOINT,
            region_name="auto",
            aws_access_key_id=os.environ["LITESTREAM_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["LITESTREAM_SECRET_ACCESS_KEY"],
        )
        age = _newest_object_age(s3)
    except Exception as e:
        print(f"[check_backup] tigris unreachable: {e}", file=sys.stderr)
        return 0
    if age is None or age > timedelta(hours=THRESHOLD_HOURS):
        print(f"[check_backup] stale or empty: age={age}")
        return 0
    urllib.request.urlopen(os.environ["HEALTHCHECKS_URL"], timeout=10)
    print(f"[check_backup] ok, ping sent. age={age}")
    return 0
```

- [ ] **Step 4: Test laufen lassen — erwartet PASS**

```bash
uv run pytest tests/test_check_backup.py::test_api_error_silent_skip -v
```

Expected: `PASSED`.

- [ ] **Step 5: Alle Tests zusammen**

```bash
uv run pytest tests/test_check_backup.py -v
```

Expected: 4 PASSED.

- [ ] **Step 6: Commit**

```bash
git add scripts/check_backup.py tests/test_check_backup.py
git commit -m "feat(scripts): API-Fehler silent-skippen (#118)"
```

---

## Task 6: GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/backup-check.yml`

- [ ] **Step 1: Workflow-Datei erstellen**

Datei `.github/workflows/backup-check.yml`:

```yaml
name: Backup-Monitoring

on:
  schedule:
    - cron: '17 5 * * *'
  workflow_dispatch:

env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true

permissions:
  contents: read

jobs:
  check:
    name: Prüft Tigris-Backup-Frische
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd  # v6.0.2

      - name: Install uv
        uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b  # v8.1.0
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: uv sync --extra dev

      - name: Check backup freshness
        run: uv run python scripts/check_backup.py
        env:
          LITESTREAM_ACCESS_KEY_ID: ${{ secrets.LITESTREAM_ACCESS_KEY_ID }}
          LITESTREAM_SECRET_ACCESS_KEY: ${{ secrets.LITESTREAM_SECRET_ACCESS_KEY }}
          HEALTHCHECKS_URL: ${{ secrets.HEALTHCHECKS_URL }}
```

**SHA-Hinweis:** Die beiden `uses:`-Zeilen sind 1:1 aus `.github/workflows/deploy.yml` übernommen (identische Action-Versionen → SHA-Pinning konsistent mit Memory-Regel `feedback_github_actions_sha_pinning`).

- [ ] **Step 2: YAML-Syntax prüfen (lokal, mit yamllint falls installiert, sonst Sichtprüfung)**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/backup-check.yml'))" && echo "YAML OK"
```

Expected: `YAML OK`.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/backup-check.yml
git commit -m "feat(ci): Scheduled GitHub Action für Backup-Monitoring (#118)"
```

---

## Task 7: Heartbeat-Loop aus entrypoint.sh entfernen

**Files:**
- Modify: `entrypoint.sh`

Vor-Zustand (`entrypoint.sh`):

```sh
#!/bin/sh
# entrypoint.sh
# Startet Litestream (PID 1) + uvicorn. Restored bei leerem Volume automatisch
# und pingt Healthchecks.io periodisch, solange Litestream repliziert.
set -eu

DB_PATH="${DATABASE_PATH:-/data/olivalle.db}"
STATE_DIR="${DB_PATH}-litestream"
HEARTBEAT_URL="${HEALTHCHECKS_URL:-}"

# 1) Auto-Restore bei leerem Volume
if [ ! -f "$DB_PATH" ]; then
  echo "[entrypoint] Keine DB gefunden — versuche Restore aus Tigris…"
  litestream restore -if-replica-exists -config /etc/litestream.yml "$DB_PATH" || {
    echo "[entrypoint] Kein Backup vorhanden (erstes Deployment) — frische DB."
  }
fi

# 2) Migrationen (idempotent, auf Volume)
python -c 'from app.database import init_db; init_db()'

# 3) Heartbeat-Loop im Hintergrund
if [ -n "$HEARTBEAT_URL" ]; then
  (
    while true; do
      sleep 600
      if find "$STATE_DIR" -type f -mmin -15 2>/dev/null | grep -q .; then
        curl -fsS -m 10 --retry 3 -o /dev/null "$HEARTBEAT_URL" || true
      fi
    done
  ) &
fi

# 4) Litestream als PID 1, uvicorn als ueberwachter Subprocess
exec litestream replicate -config /etc/litestream.yml -exec \
  "uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=*"
```

- [ ] **Step 1: Heartbeat-Loop + unnötige Variablen entfernen**

`entrypoint.sh` komplett ersetzen durch:

```sh
#!/bin/sh
# entrypoint.sh
# Startet Litestream (PID 1) + uvicorn. Restored bei leerem Volume automatisch.
# Backup-Monitoring läuft extern via GitHub Action (siehe
# .github/workflows/backup-check.yml, Issue #118).
set -eu

DB_PATH="${DATABASE_PATH:-/data/olivalle.db}"

# 1) Auto-Restore bei leerem Volume
if [ ! -f "$DB_PATH" ]; then
  echo "[entrypoint] Keine DB gefunden — versuche Restore aus Tigris…"
  litestream restore -if-replica-exists -config /etc/litestream.yml "$DB_PATH" || {
    echo "[entrypoint] Kein Backup vorhanden (erstes Deployment) — frische DB."
  }
fi

# 2) Migrationen (idempotent, auf Volume)
python -c 'from app.database import init_db; init_db()'

# 3) Litestream als PID 1, uvicorn als ueberwachter Subprocess
exec litestream replicate -config /etc/litestream.yml -exec \
  "uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=*"
```

- [ ] **Step 2: Syntax-Check**

```bash
sh -n entrypoint.sh && echo "sh-syntax OK"
```

Expected: `sh-syntax OK`.

- [ ] **Step 3: Diff visuell prüfen**

```bash
git diff entrypoint.sh
```

Expected: Zeilen 9 (`STATE_DIR`), 10 (`HEARTBEAT_URL`), und der gesamte Heartbeat-Block (ehemals 22-32) sind weg. Kommentar oben angepasst, Nummerierung 1-3 statt 1-4.

- [ ] **Step 4: Commit**

```bash
git add entrypoint.sh
git commit -m "refactor(entrypoint): Heartbeat-Loop ersatzlos entfernt (#118)"
```

---

## Task 8: ADR-Nachtrag

**Files:**
- Modify: `docs/adr-backup-strategie.md`

- [ ] **Step 1: Zweiten Nachtrag am Dateiende anhängen**

An `docs/adr-backup-strategie.md` anfügen (nach dem #116-Nachtrag):

```markdown

---

## Nachtrag 2026-04-22b: Monitoring-Architektur-Umbau (Issue #118)

**Kontext:** Nach Inbetriebnahme von #110 und #116 zeigten sich zwei Probleme am sekundären Heartbeat-Loop in `entrypoint.sh`:

1. **Pfad-Bug:** Loop prüfte `/data/olivalle.db-litestream`, Litestream schreibt aber in `/data/.olivalle.db-litestream` (Dotfile) — kein einziger Ping seit #110 kam an.
2. **Falsche Mess-Semantik:** Loop prüfte einen Zwischenschritt auf dem Server (lokale Litestream-Dateien), nicht das Ergebnis in der Cloud (Tigris-Replikat aktuell?).

**Entscheidung:** Backup-Monitoring migriert in eine **scheduled GitHub Action** (`.github/workflows/backup-check.yml`, 1×/Tag), die via S3-API bei Tigris prüft, ob das neueste Objekt < 24 h alt ist. Bei OK → Ping an Healthchecks.io, sonst silent skip. Grace 25 h alarmiert per E-Mail.

Damit wird das im #116-Nachtrag verworfene Argument ("Komplexität nicht lohnend für CHF 1.40/Mt Kostenersparnis") überholt — **nicht Kosten treiben den Wechsel, sondern Korrektheit**.

**Konsequenzen:**
- Heartbeat-Loop aus `entrypoint.sh` entfernt; Variablen `STATE_DIR` und `HEARTBEAT_URL` weg.
- `HEALTHCHECKS_URL` wandert von fly-Secret nach GitHub Repo-Secret.
- Healthchecks.io-Check `olivalle-litestream-heartbeat` umkonfiguriert: Period `10 min` → `1 day`, Grace `5 min` → `25 h`. Name + Ping-URL bleiben, Historie erhalten.
- Credentials: bestehende `LITESTREAM_*`-Keys werden wiederverwendet (read-only im S3-ListObjectsV2-Kontext).

**Tradeoff:** Bei Tigris-API-Ausfall `silent skip` statt `fail loud` — verhindert false-alarm-Mails bei kurzen Hickups, verzögert aber den Alarm bei mehrtägigem Tigris-Ausfall auf ~48 h. Für Olivalle-Scale akzeptabel.

**Details:** [`docs/superpowers/specs/2026-04-22-issue-118-backup-monitoring-design.md`](superpowers/specs/2026-04-22-issue-118-backup-monitoring-design.md)
```

- [ ] **Step 2: Markdown-Link-Rendering prüfen (Sichtprüfung im Editor oder Preview)**

Expected: Der Link zum Spec-File sollte klickbar sein (relativer Pfad stimmt).

- [ ] **Step 3: Commit**

```bash
git add docs/adr-backup-strategie.md
git commit -m "docs(adr): Nachtrag 2026-04-22b — Monitoring-Umbau (#118)"
```

---

## Task 9: Runbook aktualisieren

**Files:**
- Modify: `docs/runbook-restore.md` (Abschnitt "Heartbeat-Alert erhalten — was tun?")

- [ ] **Step 1: Bestehenden Abschnitt ersetzen**

In `docs/runbook-restore.md` den **gesamten Block** `## Heartbeat-Alert erhalten — was tun?` inklusive Inhalt **und** der folgenden `---`-Trennlinie (aktuell ~Zeilen 131-153) ersetzen durch das untenstehende Markdown (das neue Section plus `---`-Trennlinie). Der Abschnitt `## Anhang: Protokoll der Restore-Tests` bleibt unangetastet.

```markdown
## Backup-Monitoring-Alarm erhalten — was tun?

Healthchecks.io mailt, wenn > 25 h kein Ping kam. **Seit 2026-04-22
(Issue #118) wird der Ping von einer scheduled GitHub Action gesendet,
nicht mehr vom Server.** Ein Alarm heisst: seit > 25 h wurde in Tigris
kein frisches Backup-Objekt gefunden *oder* die Action konnte Tigris
nicht erreichen.

1. **GitHub Actions Tab** → Workflow `Backup-Monitoring` → letzten Run-Log
   prüfen:
   - `[check_backup] ok, ping sent …` → dann ist's ein Healthchecks.io-
     seitiges Problem, nicht die Action. Ping-Historie im Healthchecks.io-
     Dashboard prüfen.
   - `[check_backup] tigris unreachable: …` → Netzwerk/Auth/Tigris-Outage.
     GitHub Repo-Secrets mit fly-Secrets abgleichen (siehe unten).
   - `[check_backup] stale or empty: age=…` → **echtes Problem**:
     Litestream repliziert nicht mehr.
2. `fly logs -a olivalle --no-tail | grep litestream` → Replikationsfehler
   sichtbar?
3. `fly ssh console -a olivalle` → `ls -la /data/.olivalle.db-litestream`
   → letzte WAL-Segment-Zeit prüfen.
4. Häufigster Fall: Tigris-Credentials rotiert/abgelaufen → neu erzeugen
   (`fly storage` oder Tigris-Dashboard), via `fly secrets set` **und**
   GitHub Repo-Secrets aktualisieren.
5. Healthchecks.io-Check testweise via `gh workflow run backup-check.yml`
   triggern → Ping-Ankunft verifizieren.

---
```

- [ ] **Step 2: Diff visuell prüfen**

```bash
git diff docs/runbook-restore.md
```

Expected: Alter Abschnitt "Heartbeat-Alert erhalten" komplett ersetzt; Anhang (Protokoll-Tabelle) unberührt.

- [ ] **Step 3: Commit**

```bash
git add docs/runbook-restore.md
git commit -m "docs(runbook): Backup-Monitoring-Alarm statt Heartbeat-Alert (#118)"
```

---

## Task 10: README-Zeile ergänzen

**Files:**
- Modify: `README.md` (Abschnitt "Backups & Wiederherstellung", Zeilen 27-35)

- [ ] **Step 1: Monitoring-Zeile einfügen**

In `README.md` den Abschnitt anpassen. Aktuell:

```markdown
## Backups & Wiederherstellung

Die SQLite-DB wird kontinuierlich via [Litestream](https://litestream.io)
in einen Tigris-Bucket (EU-Multi-Region: Amsterdam + Frankfurt) repliziert.
Im Katastrophenfall (Volume-Verlust) restored der Container automatisch
beim Start.

- Architekturentscheidung: [`docs/adr-backup-strategie.md`](docs/adr-backup-strategie.md)
- Restore-Anleitung: [`docs/runbook-restore.md`](docs/runbook-restore.md)
```

Ersetzen durch:

```markdown
## Backups & Wiederherstellung

Die SQLite-DB wird kontinuierlich via [Litestream](https://litestream.io)
in einen Tigris-Bucket (EU-Multi-Region: Amsterdam + Frankfurt) repliziert.
Im Katastrophenfall (Volume-Verlust) restored der Container automatisch
beim Start. Eine tägliche GitHub Action prüft die Backup-Frische gegen
Healthchecks.io (Alarm bei Stillstand > 25 h).

- Architekturentscheidung: [`docs/adr-backup-strategie.md`](docs/adr-backup-strategie.md)
- Restore-Anleitung: [`docs/runbook-restore.md`](docs/runbook-restore.md)
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs(readme): Backup-Monitoring-Zeile ergänzt (#118)"
```

---

## Task 11: Operational Checklist (nicht-code, manuell nach PR-Merge)

**Files:** keine Code-Änderung; diese Checkliste als Kommentar im PR-Body verwenden.

- [ ] **Step 1: GitHub Repo-Secrets setzen**

```bash
# Werte aus fly holen (einmalig)
fly ssh console -a olivalle -C 'printenv LITESTREAM_ACCESS_KEY_ID'
fly ssh console -a olivalle -C 'printenv LITESTREAM_SECRET_ACCESS_KEY'
fly ssh console -a olivalle -C 'printenv HEALTHCHECKS_URL'
```

Dann in GitHub: Repo → Settings → Secrets and variables → Actions → New repository secret. Drei Secrets anlegen:
- `LITESTREAM_ACCESS_KEY_ID`
- `LITESTREAM_SECRET_ACCESS_KEY`
- `HEALTHCHECKS_URL`

- [ ] **Step 2: Action testweise triggern (Branch noch nicht gemergt)**

```bash
gh workflow run backup-check.yml --ref feat/118-external-backup-monitoring
gh run list --workflow=backup-check.yml --limit 1
```

Expected: Action-Run endet mit exit 0, Log zeigt `[check_backup] ok, ping sent. age=…`.

- [ ] **Step 3: Healthchecks.io-UI: Ping-Ankunft verifizieren**

Im Healthchecks.io-Dashboard den Check `olivalle-litestream-heartbeat` öffnen. Unter "Events" sollte ein Ping von ~jetzt sichtbar sein (auch wenn Check pausiert ist, wird der Ping geloggt).

- [ ] **Step 4: Healthchecks.io-Check umkonfigurieren + unpausen**

- Period: `10 min` → `1 day`
- Grace: `5 min` → `25 h`
- Save → **Unpause**

- [ ] **Step 5: PR mergen**

Über GitHub-UI oder `gh pr merge`. Deploy rollt automatisch.

- [ ] **Step 6: Fly-Secret entfernen (erst nach erfolgreichem Deploy)**

```bash
fly secrets unset HEALTHCHECKS_URL -a olivalle
```

- [ ] **Step 7: 7 Tage Beobachtungsfenster starten**

Kalendereintrag für 2026-04-29 setzen: "Issue #118 schliessen wenn 7 Tage keine false-positives". Bis dahin täglich einen Blick auf GitHub Actions Tab und Healthchecks.io-Log werfen.

---

## Task 12: Lint + Full-Test-Run vor PR

**Files:** keine

- [ ] **Step 1: Ruff auf neuen Code**

```bash
uv run ruff check scripts/ tests/test_check_backup.py
uv run ruff format --check scripts/ tests/test_check_backup.py
```

Expected: `All checks passed!` und `would reformat 0 files` (oder 0 Findings).

- [ ] **Step 2: Pytest Full Run**

```bash
uv run pytest
```

Expected: alle Tests PASS, inklusive der 4 neuen in `test_check_backup.py`.

- [ ] **Step 3: Make-Lint-All (falls vorhanden)**

```bash
make lint-all
```

Expected: keine neuen Findings.

- [ ] **Step 4: PR eröffnen**

```bash
gh pr create --title "feat: Externes Backup-Monitoring via GitHub Action (#118)" --body "$(cat <<'EOF'
## Summary

- Neue scheduled GitHub Action `backup-check.yml` prüft täglich via S3-API bei Tigris, ob das neueste Objekt im Bucket `olivalle-backup` < 24 h alt ist. Bei OK → Ping an Healthchecks.io, sonst silent skip.
- Heartbeat-Loop aus `entrypoint.sh` ersatzlos entfernt — hatte Pfad-Bug (`.olivalle.db-litestream` vs `olivalle.db-litestream`) und mass am falschen Ende (Server-Zwischenschritt statt Cloud-Ergebnis).
- Doku: ADR-Nachtrag 2026-04-22b, Runbook-Abschnitt "Backup-Monitoring-Alarm erhalten", README-Zeile ergänzt.

Spec: `docs/superpowers/specs/2026-04-22-issue-118-backup-monitoring-design.md`

## Test plan

- [ ] `uv run pytest tests/test_check_backup.py -v` → 4 PASSED
- [ ] `make lint-all` → keine neuen Findings
- [ ] GitHub Repo-Secrets gesetzt (LITESTREAM_*, HEALTHCHECKS_URL)
- [ ] `gh workflow run backup-check.yml --ref feat/118-external-backup-monitoring` → ok, ping sent
- [ ] Healthchecks.io-Check Period/Grace umkonfiguriert + unpausen
- [ ] Merge + Deploy → fly-Logs ohne Heartbeat-Block
- [ ] `fly secrets unset HEALTHCHECKS_URL -a olivalle`
- [ ] 7 Tage Beobachtung ohne false-positives

Closes #118
EOF
)"
```

---

## Self-Review (durchgeführt)

**Spec-Coverage:**
- ✅ D1 (täglich + Grace 25h) — Task 6 (cron) + Task 11 Step 4 (Grace-Config)
- ✅ D2 (Credential-Reuse) — Task 11 Step 1
- ✅ D3 (Python + pytest + moto) — Tasks 1-5
- ✅ D4 (silent skip) — Task 5 (Try/Except)
- ✅ D5 (Cleanup) — Task 7 (entrypoint), Task 11 Step 4 (HC.io), Task 11 Step 6 (fly-secret)
- ✅ Komponenten `check_backup.py` + Tests — Tasks 2-5
- ✅ Workflow-YAML — Task 6
- ✅ Doku-Updates — Tasks 8, 9, 10
- ✅ Acceptance-Criteria — im PR-Body + 7-Tage-Fenster Task 11 Step 7

**Placeholder-Scan:**
- Keine TBDs, TODOs, "implement later" in Tasks.
- Jeder Code-Step enthält vollständigen Code oder exakte Edit-Anweisung.
- SHAs in Workflow sind konkret aus `deploy.yml` übernommen, nicht als `<SHA>`.

**Type/Name-Konsistenz:**
- `_newest_object_age` (Task 2) → gleiche Signatur in Task 5 (Refactor berührt sie nicht).
- Env-Vars `LITESTREAM_ACCESS_KEY_ID`, `LITESTREAM_SECRET_ACCESS_KEY`, `HEALTHCHECKS_URL` identisch in Skript, Workflow, Test-Fixture.
- `THRESHOLD_HOURS = 24` konsistent.
- Bucket `olivalle-backup`, Prefix `olivalle/`, Endpoint `https://fly.storage.tigris.dev` identisch in Skript und Tests.
