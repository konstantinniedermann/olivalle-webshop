# Design: Externes Backup-Monitoring (Issue #118)

**Status:** Entwurf (2026-04-22)
**Issue:** [#118](https://github.com/konstantinniedermann/olivalle-webshop/issues/118)
**Relates to:** [#110](https://github.com/konstantinniedermann/olivalle-webshop/issues/110) (Litestream-Setup), [#116](https://github.com/konstantinniedermann/olivalle-webshop/issues/116) (min_machines_running=1)

## Kontext

Mit #110 ist Litestream + Tigris als Backup live, mit #116 läuft die
fly-Machine 24/7. Nach Inbetriebnahme zeigten sich zwei Probleme am
**sekundären Heartbeat-Loop** in `entrypoint.sh:22-32`:

1. **Pfad-Bug:** Der Loop prüft `/data/olivalle.db-litestream`, Litestream
   schreibt aber in `/data/.olivalle.db-litestream` (Dotfile). Seit #110
   kam dadurch kein einziger Ping bei Healthchecks.io an — fiel erst nach
   dem ersten vollen Loop-Durchlauf nach #116 auf.
2. **Falsche Mess-Semantik:** Der Loop prüft einen Zwischenschritt auf dem
   Server (lokale Litestream-Dateien), nicht das **Ergebnis in der Cloud**
   (Tigris-Replikat aktuell?). Selbst wenn der Pfad-Bug behoben wäre,
   würde bei ruhiger DB (lange Stille-Phasen ohne Writes) regelmässig ein
   false-positive Alarm drohen.

Zusätzlich hatte der #116-ADR-Nachtrag die Option "Externer Cron gegen
Tigris" noch verworfen mit dem Argument "mehr Komplexität, neue Secrets,
nicht lohnend für CHF 1.40/Mt Kostenersparnis". Durch die oben genannten
Bugs kehrt sich die Abwägung um: **nicht Kosten treiben den Wechsel,
sondern Korrektheit**.

## Ziel

Backup-Monitoring misst das **Ergebnis** (frisches Objekt im Cloud-Bucket?)
statt eines Server-internen Zwischenschritts. Betriebsmodell:

- **Scheduled GitHub Action** (1×/Tag) prüft via S3-API bei Tigris, ob
  das neueste Objekt im Bucket `olivalle-backup` < 24 h alt ist.
- Bei **OK** → Ping an Healthchecks.io.
- Bei **stale / leer / API-Fehler** → kein Ping; Healthchecks.io alarmiert
  per E-Mail nach Ablauf der Grace-Period (25 h).
- Der sekundäre Heartbeat-Loop in `entrypoint.sh` wird **ersatzlos
  entfernt** — die Litestream-Replikation selbst bleibt unverändert.

## Design-Entscheidungen

### D1: Prüffrequenz — täglich + Grace 25 h

**Entscheidung:** `cron: '17 5 * * *'` (05:17 UTC ≈ 07:17 CH-Sommerzeit),
Threshold in der Action 24 h, Healthchecks.io Grace 25 h (1 h Puffer).

**Verworfen:** stündlich (2 h Grace) — schnellerer Alarm, aber für einen
Einzelunternehmer-Shop mit manueller Reaktion überdimensioniert.

**Begründung Uhrzeit:** Frühmorgens heisst, ein möglicher Alarm erreicht
den Entwickler beim Aufstehen, nicht mitten in der Nacht. Minute `:17`
vermeidet GitHub-Peak zur vollen Stunde.

### D2: Credentials — Wiederverwendung der Litestream-Keys

**Entscheidung:** Die bestehenden Secrets `LITESTREAM_ACCESS_KEY_ID` und
`LITESTREAM_SECRET_ACCESS_KEY` werden einmalig aus den fly-Secrets
übernommen und als **GitHub Repo-Secrets** eingetragen. Die GitHub Action
nutzt sie read-only (sie macht nur `ListObjectsV2`).

**Verworfen:** Separate read-only-Keys via Tigris-Dashboard erzeugen.
Principle of Least Privilege wäre technisch sauberer, würde aber Handarbeit
im Tigris-Dashboard erfordern und ein weiteres Secret-Paar zu pflegen
hinzufügen. Für Single-Dev + Private-Repo ist der reale Angriffsvektor
nicht wesentlich grösser.

### D3: Implementierung — Python-Skript + pytest

**Entscheidung:** Threshold-Logik in `scripts/check_backup.py`, testbar
mit `pytest` + `moto`. Workflow ruft `uv run python scripts/check_backup.py`
auf.

**Verworfen:** Inline-Bash im Workflow — nicht isoliert testbar, und
Threshold-Logik ist genau die Stelle wo Off-by-one-Bugs entstehen (siehe
Pfad-Bug im bisherigen Heartbeat). Auch verworfen: Marketplace-Action —
zusätzliche Dependency, SHA-Pinning-Pflege, intransparent für diesen
simplen Use-Case.

### D4: Error-Handling — Silent Skip

**Entscheidung:** Bei Tigris-API-Fehler (Netzwerk, 5xx, Auth, leerer
Bucket) → Log-Ausgabe, **kein Ping**, Action exit 0. Healthchecks.io
alarmiert nach Ablauf der Grace-Period falls der Zustand anhält.

**Verworfen:** "Fail loud" (action exit 1, GitHub-E-Mail zusätzlich zu
Healthchecks.io) — bewusst gegen Dual-Channel entschieden, weil ein
kurzer Tigris-Hiccup sonst sofortige false-alarm-Mails triggert. Tradeoff:
Ein mehrstündiger Tigris-Ausfall kann bis zu ~2 Tage unbemerkt bleiben
(heutiger Run fällt, morgen ist Tigris wieder ok, übermorgen hätte
Grace-Period Alarm ausgelöst). Für Olivalle-Scale akzeptabel.

### D5: Cleanup-Strategie — Heartbeat raus, Check umkonfigurieren

**Entscheidung:**

- `entrypoint.sh:22-32` (Heartbeat-Loop) ersatzlos entfernen; Variablen
  `STATE_DIR` und `HEARTBEAT_URL` mitentfernen.
- `fly secrets unset HEALTHCHECKS_URL -a olivalle` nach erstem
  erfolgreichen Action-Run.
- **Bestehenden** Healthchecks.io-Check (`olivalle-litestream-heartbeat`)
  umkonfigurieren: Period `10 min` → `1 day`, Grace `5 min` → `25 h`,
  Check unpausen. Name + Ping-URL bleiben, Historie bleibt erhalten.

**Verworfen:** Neuen Check anlegen + alten archivieren — saubere Trennung,
aber Secret-Rotation und History-Verlust sind unnötiger Aufwand.

## Komponenten

### Neu: `scripts/check_backup.py`

```python
# Skizze, nicht finaler Code
import os, sys, boto3
from datetime import datetime, timezone, timedelta
import urllib.request

BUCKET = "olivalle-backup"
PREFIX = "olivalle/"
ENDPOINT = "https://fly.storage.tigris.dev"
THRESHOLD_HOURS = 24

def newest_object_age(s3) -> timedelta | None:
    """None falls Bucket leer. Exceptions propagiert der Caller."""
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)
    contents = resp.get("Contents", [])
    if not contents:
        return None
    newest = max(o["LastModified"] for o in contents)
    return datetime.now(timezone.utc) - newest

def main() -> int:
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=ENDPOINT,
            region_name="auto",
            aws_access_key_id=os.environ["LITESTREAM_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["LITESTREAM_SECRET_ACCESS_KEY"],
        )
        age = newest_object_age(s3)
    except Exception as e:
        print(f"[check_backup] tigris unreachable: {e}", file=sys.stderr)
        return 0  # silent skip

    if age is None:
        print("[check_backup] bucket empty — skipping ping")
        return 0
    if age > timedelta(hours=THRESHOLD_HOURS):
        print(f"[check_backup] stale: age={age} > {THRESHOLD_HOURS}h")
        return 0

    urllib.request.urlopen(os.environ["HEALTHCHECKS_URL"], timeout=10)
    print(f"[check_backup] ok, ping sent. age={age}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

**Note:** Keine `ContinuationToken`-Schleife nötig — Litestream hält den
Bucket bei Retention 30 Tage weit unter 1000 Objekten (S3-Default-Limit
von `list_objects_v2`). Falls das mal ansteigt, wäre der Fix eine
einzeilige Ergänzung; YAGNI für v1.

### Neu: `tests/test_check_backup.py`

4 Tests mit `moto.mock_aws` und `monkeypatch` für den HTTP-Ping:

| Test | Setup | Erwartet |
|---|---|---|
| `test_fresh_object_triggers_ping` | Bucket mit Objekt `now-1h` | Ping-Call erfolgt, exit 0 |
| `test_stale_object_skips_ping` | Objekt `now-30h` | Kein Ping, exit 0 |
| `test_empty_bucket_skips_ping` | Bucket leer | Kein Ping, exit 0 |
| `test_api_error_silent_skip` | `list_objects_v2` wirft `ClientError` | Kein Ping, exit 0 |

### Neu: `.github/workflows/backup-check.yml`

```yaml
name: Backup-Monitoring
on:
  schedule:
    - cron: '17 5 * * *'
  workflow_dispatch:
permissions:
  contents: read
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<SHA>  # v6.0.2
      - uses: astral-sh/setup-uv@<SHA>  # v8.1.0
        with:
          python-version: "3.13"
      - run: uv sync --extra dev
      - run: uv run python scripts/check_backup.py
        env:
          LITESTREAM_ACCESS_KEY_ID: ${{ secrets.LITESTREAM_ACCESS_KEY_ID }}
          LITESTREAM_SECRET_ACCESS_KEY: ${{ secrets.LITESTREAM_SECRET_ACCESS_KEY }}
          HEALTHCHECKS_URL: ${{ secrets.HEALTHCHECKS_URL }}
```

SHAs werden bei der Implementierung aus den bestehenden Workflows
(`deploy.yml`, `lint.yml`) übernommen — Memory-Regel
`feedback_github_actions_sha_pinning` greift.

### Änderung: `entrypoint.sh`

Zeilen 22-32 (Heartbeat-Loop inkl. Kommentarblock) entfernen. Die
Variablen `STATE_DIR` und `HEARTBEAT_URL` werden ebenfalls nicht mehr
gesetzt. `DB_PATH` bleibt, wird weiter von Litestream genutzt.

### Änderung: `pyproject.toml`

`boto3` und `moto` als Dev-Dependencies hinzufügen (Gruppe `dev`, nur
für CI/Test, nicht im prod-Container).

## Tests

**Unit-Tests:** Laufen im bestehenden `pytest`-Job von `deploy.yml`. Kein
echter Netzwerk-Call — `moto` mockt S3, `monkeypatch` mockt den HTTP-Ping.

**Smoke-Test (manuell nach Deploy):**

1. `gh workflow run backup-check.yml` → Run-Log prüfen, im
   Healthchecks.io-Log sollte innerhalb 30 s ein Ping sichtbar sein.
2. Temporär falsches Secret setzen + `workflow_dispatch` → erwartet:
   Log zeigt "tigris unreachable", Action exit 0, kein Ping.
3. Test-Secret wieder zurücksetzen.

## Rollout

Wichtig: Reihenfolge so wählen, dass **kein Überwachungs-Gap** entsteht —
der alte Heartbeat wird erst entfernt, wenn die neue Action verifiziert
pingt.

1. Feature-Branch `feat/118-external-backup-monitoring`, alles committen
   (Script, Tests, Workflow, entrypoint.sh-Änderung, pyproject.toml).
2. GitHub Repo-Secrets setzen: `LITESTREAM_ACCESS_KEY_ID`,
   `LITESTREAM_SECRET_ACCESS_KEY`, `HEALTHCHECKS_URL` (aus fly-Secrets
   übernommen via `fly ssh console -a olivalle -C 'printenv …'`).
3. Auf dem Branch: `gh workflow run backup-check.yml` → Run-Log prüfen,
   Ping im Healthchecks.io-Log erwarten.
4. Healthchecks.io-Dashboard: Check `olivalle-litestream-heartbeat` →
   Period `1 day`, Grace `25 h`, Check **unpausen**.
5. PR-Review + Merge → Deploy rollt neue `entrypoint.sh` ohne
   Heartbeat-Loop aus.
6. `fly secrets unset HEALTHCHECKS_URL -a olivalle` (Aufräumen).
7. **7 Tage Beobachtung** (Acceptance-Criterion aus #118).

## Dokumentations-Updates (im selben PR)

1. `docs/adr-backup-strategie.md` — zweiter Nachtrag ("Nachtrag
   2026-04-22b: Monitoring-Architektur-Umbau") erklärt die Kehrtwende
   gegenüber dem #116-Nachtrag (Korrektheit, nicht Kosten).
2. `docs/runbook-restore.md` — Abschnitt "Heartbeat-Alert erhalten"
   wird zu "Backup-Monitoring-Alarm erhalten": verweist auf GitHub
   Actions Tab als erste Diagnose-Stelle, nicht mehr auf `fly ssh`.
3. `README.md` — Abschnitt "Backups & Wiederherstellung" um eine Zeile
   ergänzen: "Tägliches Monitoring via scheduled GitHub Action prüft
   Tigris-Frische gegen Healthchecks.io."
4. `CLAUDE.md` (Projekt) — keine Änderung nötig (Monitoring-Umbau ist
   Implementierungsdetail, nicht Tech-Stack-Ebene).
5. Memory-Update `project_backup_setup.md` — nach Merge: "#118
   Monitoring-Umbau live".

## Akzeptanzkriterien (aus #118 übernommen)

- [ ] GitHub Action läuft nach Zeitplan und pingt bei gesundem Backup an
      Healthchecks.io.
- [ ] Manueller Test: Tigris unreachable oder Objekt veraltet → kein
      Ping → Alarm kommt innerhalb der Grace-Period.
- [ ] Heartbeat-Loop aus `entrypoint.sh` entfernt.
- [ ] Doku aktualisiert (ADR-Nachtrag, Runbook, README).
- [ ] 7 Tage Normalbetrieb ohne false-positives nach Deploy.
- [ ] Healthchecks.io-Check wieder aktiv.

## Risiken & offene Punkte

**Risiko 1 — Tigris-Ausfall bleibt bis zu 2 Tage unbemerkt (D4-Tradeoff):**
Bewusst akzeptiert. Bei einem dauerhaften Tigris-Ausfall deckt Grace-Period
den Fall ab; bei einem einzelnen Hickup ist die Verzögerung akzeptabel.

**Risiko 2 — GitHub Actions Schedule ist best-effort:** GitHub garantiert
cron-Schedules nicht auf die Minute; bei hoher Last können Runs 15–30 Min
später kommen. Der 1-Stunden-Puffer (Threshold 24 h vs Grace 25 h) fängt
das ab.

**Risiko 3 — `list_objects_v2` 1000-Objekte-Limit:** Bei Retention 30 Tage
und Litestream-Snapshot-Interval 24 h stehen real ~30–60 Objekte im
Bucket. Weit unter dem Limit; kein Pagination-Code nötig (YAGNI).

**Offen für spätere Issues:**
- Initialer Restore-Test (#115) — wird nicht Teil dieses PR.
- Separate Read-Only-Keys (D2, verworfen) — könnten bei späterem
  Security-Review nachgeholt werden.
- Externes Uptime-Monitoring für `olivalle.ch` (#111) — separates Thema.

## Referenzen

- Litestream S3-Config: [`litestream.yml`](../../../litestream.yml)
- ADR: [`docs/adr-backup-strategie.md`](../../adr-backup-strategie.md)
- Runbook: [`docs/runbook-restore.md`](../../runbook-restore.md)
- Vorgänger-Spec: [`docs/superpowers/specs/2026-04-22-issue-110-sqlite-backup-design.md`](2026-04-22-issue-110-sqlite-backup-design.md)
- Vorgänger-Spec: [`docs/superpowers/specs/2026-04-22-issue-116-heartbeat-tuning-design.md`](2026-04-22-issue-116-heartbeat-tuning-design.md)
