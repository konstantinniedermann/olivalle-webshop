# Design: Externes Uptime-Monitoring + fly-Healthchecks (Issue #111)

**Status:** Entwurf (2026-04-23)
**Issue:** [#111](https://github.com/konstantinniedermann/olivalle-webshop/issues/111)
**Relates to:** [#110](https://github.com/konstantinniedermann/olivalle-webshop/issues/110) (Litestream-Setup), [#116](https://github.com/konstantinniedermann/olivalle-webshop/issues/116) (`min_machines_running=1`), [#118](https://github.com/konstantinniedermann/olivalle-webshop/issues/118) (Backup-Monitoring), [#122](https://github.com/konstantinniedermann/olivalle-webshop/issues/122) (Request-Handler werfen 500 bei fehlender DB)
**Blocks:** #120

## Kontext

Der Shop läuft live auf fly.io (`olivalle.ch`) mit `min_machines_running = 1`
seit #116 — Kaltstart-Risiko entfällt. Aktueller Stand:

- `/health`-Endpoint existiert (`app/main.py:24`) und gibt `{"status": "ok"}`
  zurück, macht aber **keinen DB-Check**.
- `fly.toml` hat **keine** `[[checks]]`-Sektion — fly kennt den Endpoint nicht.
- Es existiert **keine externe Uptime-Überwachung**. Ein Ausfall von
  olivalle.ch würde erst auffallen, wenn ein Kunde sich meldet.
- Der Healthchecks.io-Account aus #118 (Check `olivalle-litestream-heartbeat`)
  läuft stabil, E-Mail-Alarm geht an `konstantin.niedermann@gmail.com`.

Seit #122 werfen Request-Handler klar 500 bei DB-Fehlern. Das schliesst
ein Loch, lässt aber `/health` unberührt: wenn die DB kaputt ist und die
App sonst läuft, meldet `/health` weiterhin "ok" — ein externer Check
würde den Fehlerzustand nicht sehen.

## Ziel

Frühwarnung bei App-Ausfall, DB-Korruption (bei laufender App) und
TLS-Ablauf. Zielwerte:

- **Time-to-Alarm HTTP-Ausfall:** 10–30 min
- **Time-to-Alarm TLS-Ablauf:** ≥ 30 Tage vor Expiry
- **Kein neuer Dienst, kein neuer Account** — Wiederverwendung des
  bestehenden Healthchecks.io-Accounts aus #118.

Explizit **nicht** in Scope dieses Specs:

- Stripe-Webhook-Heartbeat ("N Minuten kein Webhook trotz Bestellung") —
  als separates Issue nach #111 einzustellen.
- SH als zweiter Alarm-Empfänger — kann jederzeit nachträglich im
  Healthchecks.io-Dashboard konfiguriert werden, keine Code-Änderung.
- Synthetic Transactions (fake Bestellung) — Overkill für
  ~100 Bestellungen/Monat.
- Kunden-Status-Page.

## Architektur

```
                                              ┌───────────────────┐
                         ┌─────────────────►  │  fly.io           │
                         │  (HTTP GET        │   └── Machine      │
                         │   alle 10 min,    │       (1x, 24/7)   │
                         │   curl /health)   │       │            │
                         │                   │       ├─ FastAPI   │
┌─────────────────────┐  │                   │       │  /health   │
│ GitHub Action       │  │                   │       │  + DB-Touch│
│ monitor-uptime.yml  │──┤                   │       ├─ fly check │
│ cron: */10 * * * *  │  │                   │       │  (interner │
└─────────┬───────────┘  │                   │       │   restart  │
          │              │                   │       │   loop)    │
          │              └──────────────────►│       └─ SQLite DB │
          │ bei 200 OK                      olivalle.ch           │
          │
          ▼
┌─────────────────────┐     Alarm bei       ┌───────────────────┐
│ Healthchecks.io     │     fehlendem Ping  │ konstantin.niedermann
│ olivalle-http-uptime│─────────────────────▶  @gmail.com       │
│ (period 10m,        │     E-Mail          │                   │
│  grace 20m)         │                     └───────────────────┘
└─────────────────────┘

┌─────────────────────┐   TLS-Cert-Check
│ GitHub Action       │   1x/Tag via
│ monitor-tls.yml     │   ssl.get_server_certificate()
│ cron: 23 5 * * *    │   → Ping wenn Restlaufzeit ≥ 30 Tage
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐     Alarm bei       ┌───────────────────┐
│ Healthchecks.io     │     fehlendem Ping  │ konstantin.niedermann
│ olivalle-tls-expiry │─────────────────────▶  @gmail.com       │
│ (period 1d,         │     E-Mail          └───────────────────┘
│  grace 1d)          │
└─────────────────────┘

                    bereits produktiv aus #118:
                    olivalle-litestream-heartbeat (Backup, daily)
```

Drei Checks im selben Healthchecks.io-Account, gleiches Alarm-Ziel.

## Design-Entscheidungen

### D1: Monitoring-Stack — Healthchecks.io + GitHub Actions

**Entscheidung:** Wiederverwendung des Setups aus #118 (GitHub Action
pingt bei Success, Healthchecks.io alarmiert bei fehlendem Ping).

**Verworfen:** Spezialisierte Uptime-Services (UptimeRobot, Better Stack).
Purpose-built mit 1–3 min Polling und nativem TLS-Monitoring, aber neuer
Account, neues Dashboard, neuer Alarm-Kanal. Für einen Einzelunternehmer-Shop
mit manueller Reaktionszeit ist 10-Min-Polling völlig ausreichend.

**Begründung:** Die Blaupause aus #118 ist getestet und funktioniert.
Konsistenz > Feature-Maximierung. TLS-Monitoring in ~25 Zeilen Python
ist trivial und testbar.

### D2: `/health` mit DB-Touch (Variante B)

**Entscheidung:** `/health` wird erweitert um `SELECT 1` gegen die DB.
Bei DB-Fehler wird `HTTPException(503)` geworfen.

**Verworfen:**

- *Flach belassen (A):* würde DB-Korruption bei laufender App verpassen.
  Seit #122 werfen Request-Handler 500 bei DB-Fehlern; `/health` ist die
  letzte verbleibende Route ohne DB-Semantik.
- *Deep-Check mit Stripe+SMTP (C):* externe Dependencies im
  Liveness-Signal erzeugen Kaskaden-Alarme (Stripe-Ausfall ≠ Olivalle-Downtime).
  Anti-Pattern.

**Begründung:** Konsistent mit dem in #122 etablierten Grundsatz "bei
DB-Fehler klar 503/500 statt leise mogeln". Minimal mehr Last (`/health`
wird nur alle paar Minuten extern gecheckt, plus fly-intern alle 30 s).

### D3: Poll-Intervall HTTP — 10 min, Grace 20 min

**Entscheidung:** `cron: '*/10 * * * *'`, Healthchecks.io period 10 min,
grace 20 min. Time-to-Alarm bei echtem Ausfall: 10–30 min (abhängig davon,
wann der Ausfall im Poll-Zyklus liegt).

**Verworfen:**

- *5 min:* GitHub-Actions-Cron ist bei Intervallen ≤ 5 min dokumentiert
  unzuverlässig (Runner-Delay, GHA-Peak zur vollen Stunde). Würde zu
  False-Positives führen.
- *15 min:* zu konservativ — ein verpasster Run + Grace ergäbe Time-to-Alarm
  von bis zu 45 min.

**Begründung:** 20 min Grace = ein verpasster Run Puffer. Für einen Shop
mit ~100 Bestellungen/Monat und manueller Reaktionszeit sind 30 min
Obergrenze absolut akzeptabel.

### D4: TLS-Check — täglich 05:23 UTC, Threshold 30 Tage

**Entscheidung:** `cron: '23 5 * * *'` (~07:23 CH-Sommerzeit, vor dem
Arbeitstag). Python-Skript `scripts/check_tls.py` öffnet TLS-Socket zu
`olivalle.ch:443`, liest `notAfter`, exit 0 bei ≥ 30 Tagen Restlaufzeit,
sonst exit 1. Ping nur bei exit 0.

**Verworfen:**

- *Bei < 30 Tagen pingen (inverse Logik):* Healthchecks.io alarmiert auf
  *fehlenden* Ping, nicht auf aktiven Ping. Die "Ping-bei-OK"-Semantik ist
  konsistent mit #118 und der Healthchecks.io-Mentalität.
- *Shell-Einzeiler mit `openssl s_client`:* nicht testbar ohne Live-Netzwerk,
  Datum-Parsing im Shell ist fehleranfällig (`date -d` ist GNU-only).

**Begründung:** fly.io renewed Let's Encrypt automatisch alle ~60 Tage;
das Restrisiko ist DNS- oder Domain-Probleme, die das Renewal blockieren.
30 Tage Vorwarnzeit reichen für Untersuchung + manuelles Eingreifen.

**Uhrzeit 05:23 UTC:** versetzt zum Backup-Check (05:17) — sollte GHA-Peak
bei `:00`/`:15`/`:30` vermeiden und beide Alarm-Möglichkeiten am gleichen
Morgen erreichen.

### D5: HTTP-Workflow ohne Python-Skript

**Entscheidung:** Der HTTP-Uptime-Workflow enthält nur `curl --fail` +
`curl ping`. Keine separate Python-Logik.

**Verworfen:** Python-Skript wie in #118 (`scripts/check_backup.py`).

**Begründung:** In #118 enthielt das Skript echte Threshold-Mathematik
(Objektalter in S3, Zeitstempel-Vergleich) — testbar mit `moto`,
sinnvoll zu isolieren. Hier ist die Logik "HTTP 200?" — das kann `curl
--fail` nativ, ein Python-Wrapper wäre Zeremonie ohne Gewinn. Beim
TLS-Check ist Python dagegen gerechtfertigt: Datum-Parsing + Vergleich
sind die klassischen Off-by-One-Stellen.

### D6: Rollout in 4 separaten PRs

**Entscheidung:** Die Änderungen gehen in 4 kleinen PRs statt einem
grossen (siehe Implementierungs-Reihenfolge). Dazwischen manuelle
Setup-Schritte in Healthchecks.io und GitHub-Secrets.

**Verworfen:** Single-PR mit allem.

**Begründung:**

- `/health`-DB-Touch kann isoliert deployed und beobachtet werden. Falls
  der DB-Touch unerwartete Nebenwirkungen hat (Volume-Load, Lock-Timing),
  merkt man es vor der Monitoring-Einführung.
- Konsistent mit Projekt-Muster: #110 und #118 wurden auch in mehreren
  Schritten gemerged.
- Jeder PR bleibt isoliert reviewbar und rückrollbar.

## Komponenten

### K1: `/health` mit DB-Touch (`app/main.py`)

Das Projekt nutzt raw `sqlite3` (s. `app/database.py:9` `get_db()`). Der
Endpoint öffnet analog eine Connection via `get_db()` und macht `SELECT 1`.
Bei jedem Fehler (OperationalError bei fehlender DB, siehe #122) wird 503
zurückgegeben.

```python
import sqlite3
from fastapi import HTTPException
from app.database import get_db

@app.get("/health")
def health():
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

`sqlite3.Error` ist die Basis-Exception, fängt `OperationalError` (DB
weg/locked) und `DatabaseError` (korrupt). Kein breites `except Exception`
— wir wollen nicht, dass z.B. ImportError als "DB kaputt" rausgeht.

### K2: `fly.toml` — `[[http_service.checks]]`

```toml
[[http_service.checks]]
  interval = "30s"
  timeout = "5s"
  grace_period = "10s"
  method = "GET"
  path = "/health"
```

fly restartet die Machine automatisch bei wiederholten Fehlern (internes
Self-Heal). Ersetzt nicht die externe Überwachung, ergänzt sie.

### K3: `.github/workflows/monitor-uptime.yml`

```yaml
name: Uptime-Monitor
on:
  schedule:
    - cron: '*/10 * * * *'
  workflow_dispatch:
permissions: {}
concurrency:
  group: monitor-uptime
  cancel-in-progress: false
jobs:
  check:
    runs-on: ubuntu-latest
    timeout-minutes: 3
    steps:
      - name: Probe /health
        run: |
          curl --fail --max-time 10 https://olivalle.ch/health
      - name: Ping Healthchecks.io
        if: success()
        run: curl --max-time 10 "${{ secrets.HC_PING_URL_HTTP }}"
```

Alle `uses:`-Zeilen (falls später hinzugefügt) werden SHA-gepinnt nach
dem Muster aus #105.

### K4: `.github/workflows/monitor-tls.yml` + `scripts/check_tls.py`

`scripts/check_tls.py` (~25 Zeilen):

```python
import socket
import ssl
import sys
from datetime import datetime, timezone

HOST = "olivalle.ch"
PORT = 443
THRESHOLD_DAYS = 30


def days_until_expiry(host: str, port: int) -> int:
    ctx = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=10) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert()
    not_after = datetime.strptime(
        cert["notAfter"], "%b %d %H:%M:%S %Y %Z"
    ).replace(tzinfo=timezone.utc)
    return (not_after - datetime.now(timezone.utc)).days


def main() -> int:
    days_left = days_until_expiry(HOST, PORT)
    print(f"TLS cert for {HOST}: {days_left} days left")
    return 0 if days_left >= THRESHOLD_DAYS else 1


if __name__ == "__main__":
    sys.exit(main())
```

Workflow strukturell analog K3, ruft `uv run python scripts/check_tls.py` auf.

### K5: `docs/runbook-incident.md`

Struktur analog `docs/runbook-restore.md`:

1. **Zugänge nötig** (Tabelle: fly, Healthchecks.io, DNS-Registrar, SH-Kontakt)
2. **Alarm kam rein — was jetzt?** (Triage: Browser-Test → `fly logs -a olivalle` → `fly status -a olivalle`)
3. **Szenario A: 503 vom Health-Check** (DB-Problem — verlinkt auf `runbook-restore.md`)
4. **Szenario B: Timeout / Connection refused** (Machine tot — `fly machine list`, `fly deploy`)
5. **Szenario C: TLS-Alarm** (Domain/DNS prüfen, fly-Cert-Status, ggf. Cert manuell forcieren)
6. **Szenario D: False-Positive** (GitHub Action hing — Healthchecks.io selbst-resolved bei nächstem Ping)

Verweise in `docs/index.md` und `docs/arc42.md` eintragen.

## Tests

| Test | Datei | Was wird geprüft |
|---|---|---|
| `test_health_ok` | `tests/test_health.py` | `/health` gibt 200 + `{"status": "ok"}` bei erreichbarer DB |
| `test_health_db_failure` | `tests/test_health.py` | `/health` gibt 503 wenn DB-Connect wirft (via monkeypatch) |
| `test_check_tls_ok` | `tests/test_check_tls.py` | Skript exit 0 bei `notAfter` > 30 Tage in Zukunft (gemocktes Cert) |
| `test_check_tls_expired_soon` | `tests/test_check_tls.py` | Skript exit 1 bei `notAfter` < 30 Tage |
| `test_check_tls_malformed_date` | `tests/test_check_tls.py` | Skript wirft klaren Fehler statt silent exit 0 |

**Manuelle Verifikation** (im Runbook dokumentiert):

1. `fly checks list -a olivalle` → `/health`-Check als passing
2. GitHub Actions-Tab → grüne Runs alle 10 min
3. Healthchecks.io-Dashboard → letzter Ping < 15 min her
4. Test-Pausierung: Check manuell auf "pause" setzen, E-Mail nach Grace-Period prüfen, wieder "resume"
5. (Einmalig, optional) Downtime-Drill: `fly machine stop <id>` → Alarm innerhalb 30 min → `fly machine start <id>`

## Implementierungs-Reihenfolge

1. **PR 1:** `/health` mit DB-Touch + `tests/test_health.py`
2. **PR 2:** `fly.toml` `[[checks]]`-Sektion
3. **Manuell, einmalig:**
   - Healthchecks.io: Check `olivalle-http-uptime` (period 10m, grace 20m) anlegen, Ping-URL kopieren
   - Healthchecks.io: Check `olivalle-tls-expiry` (period 1d, grace 1d) anlegen, Ping-URL kopieren
   - GitHub Repo-Secrets: `HC_PING_URL_HTTP` und `HC_PING_URL_TLS` eintragen
4. **PR 3:** `monitor-uptime.yml` + `monitor-tls.yml` + `scripts/check_tls.py` + `tests/test_check_tls.py`
5. **PR 4:** `docs/runbook-incident.md` + Verweise in `docs/index.md`, `docs/arc42.md`
6. **Smoke-Test manuell:** Healthchecks.io-Check pausieren, E-Mail-Eingang bestätigen

## Konfiguration

| Was | Wo | Wer setzt | Quelle |
|---|---|---|---|
| `HC_PING_URL_HTTP` | GitHub Repo-Secrets | Entwickler manuell | Healthchecks.io-Dashboard |
| `HC_PING_URL_TLS` | GitHub Repo-Secrets | Entwickler manuell | Healthchecks.io-Dashboard |
| fly-Check-Params | `fly.toml` | im Repo | — |
| Cron-Zeiten, Thresholds | Workflow-Files, `scripts/check_tls.py` | im Repo | — |

Keine neuen fly-Secrets (konsistent mit Memory-Regel "Secrets einmalig
manuell via `fly secrets set`, nicht Pipeline").

## Memory-Updates nach Abschluss

Nach Merge aller 4 PRs: entweder neue Memory `project_monitoring_setup.md`
anlegen oder `project_backup_setup.md` erweitern. Inhalt:

- Healthchecks.io-Checks (jetzt 3 Stück): `olivalle-litestream-heartbeat`,
  `olivalle-http-uptime`, `olivalle-tls-expiry`
- Alarm-Empfänger: `konstantin.niedermann@gmail.com`
- Time-to-Alarm: ~30 min HTTP, ~1 Tag TLS
- Runbook-Pfad: `docs/runbook-incident.md`
- Secrets: `HC_PING_URL_HTTP`, `HC_PING_URL_TLS` (GitHub Repo-Secrets)

## Risiken & Mitigationen

| Risiko | Wahrscheinlichkeit | Mitigation |
|---|---|---|
| GitHub-Actions-Cron verzögert → False-Positive | mittel | 20 min Grace-Period als Puffer |
| Healthchecks.io-Ausfall → kein Alarm | niedrig | Drittdienst; akzeptiert. Status-Page-RSS im Notfall manuell prüfbar |
| DB-Touch in `/health` verursacht Locks bei hoher Last | sehr niedrig | `SELECT 1` ist read-only, hoher Load bei ~100 Bestellungen/Mt nicht erwartet |
| TLS-Cert-Parsing-Format ändert sich (OpenSSL-Upgrade) | niedrig | Test `test_check_tls_malformed_date` fängt Parse-Fehler |
| Cron-Peaks verzögern beide Workflows gleichzeitig | niedrig | HTTP und TLS haben unterschiedliche Minuten (`*/10` vs. `:23`) |

## Abhängigkeiten zu offenen Issues

- `Blocks: #120` — bleibt unverändert, nach Merge zu klären
- `Relates to: #110, #116, #118` — alle closed, Stack konsistent
- `Relates to: #122` — closed, der 503-Standard für DB-Fehler wird hier
  aufgegriffen
