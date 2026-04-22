# Design: SQLite-Backup-Strategie (Issue #110)

**Datum:** 2026-04-22
**Status:** Entwurf — Brainstorming abgeschlossen
**Issue:** [#110](https://github.com/konstantinniedermann/olivalle-webshop/issues/110)

## Kontext

Der Olivalle-Webshop läuft live auf fly.io. Die SQLite-DB (`/data/olivalle.db`, WAL-Modus) liegt auf einem persistenten fly-Volume (`olivalle_data`). Aktuell existiert **kein dokumentierter Backup-Prozess**. fly.io macht automatisch Volume-Snapshots, aber nur mit 5 Tagen Retention und diese können bei WAL-aktiven SQLite-Dateien inkonsistent sein. Bei Volume-Verlust oder DB-Korruption sind alle Bestellungen, Kundendaten und Rabattcodes weg — nicht akzeptabel für einen Live-Shop mit echten Zahlungen.

## Ziel

Ein Backup-System, das
- kontinuierlich repliziert (RPO in Sekunden),
- DSG-konform in der EU liegt,
- kostenlos bleibt (Projektvolumen ist winzig),
- im Katastrophenfall automatisch wiederherstellt,
- regelmässig überprüft wird (jährlicher manueller Restore-Test + automatischer Heartbeat-Alert).

## Entscheidungen

| Aspekt | Entscheidung |
|---|---|
| Backup-Methode | **Litestream** (kontinuierliche WAL-Replikation) |
| Ziel-Storage | **Tigris** (fly-integriert, S3-kompatibel) |
| Region | **`cdg`** (Paris, EU — DSG-konform, gleiche Region wie App) |
| Retention | **30 Tage** (WAL + tägl. Snapshot) |
| Heartbeat-Monitoring | **Healthchecks.io** (alle 10 Min) |
| Restore-Test | **Jährlich manuell**, dokumentiert im Runbook |
| Auto-Restore | **Ja** — entrypoint.sh restored bei leerem Volume automatisch |

## Architektur

```
┌──────────────────────────────────────────────┐
│   fly.io Machine (region cdg)                │
│                                              │
│   entrypoint.sh                              │
│    ├─ litestream replicate (sidecar)         │
│    │    └─ liest WAL aus olivalle.db         │
│    └─ exec uvicorn app.main:app              │
│                                              │
│   /data/olivalle.db ──────WAL──────┐         │
└────────────────────────────────────┼─────────┘
                                     │
                    ┌────────────────┴────────┐
                    ▼                         ▼
          ┌──────────────────┐     ┌──────────────────┐
          │ Tigris (cdg)     │     │ Healthchecks.io  │
          │ s3://olivalle-   │     │ Heartbeat /10min │
          │     backup/…     │     └──────────────────┘
          └──────────────────┘
```

**Komponenten:**
1. **Litestream als Sidecar im gleichen Container** — PID 1, überwacht uvicorn als Child-Process
2. **entrypoint.sh** — orchestriert Auto-Restore, startet Heartbeat-Loop, startet Litestream+uvicorn
3. **Tigris-Bucket** in Region `cdg`, Credentials als fly-Secrets
4. **Healthchecks.io-Heartbeat** — alle 10 Min, alarmiert per E-Mail bei Ausfall

## Dateien im Repo

| Datei | Status | Zweck |
|---|---|---|
| `Dockerfile` | erweitern | Litestream-Binary installieren, entrypoint.sh als CMD |
| `entrypoint.sh` | neu | Auto-Restore + Heartbeat-Loop + Litestream+uvicorn-Start |
| `litestream.yml` | neu | Replikationskonfig (Retention 30d, Snapshot 24h, Sync 1s) |
| `docs/adr-backup-strategie.md` | neu | Architekturentscheidung dokumentiert |
| `docs/runbook-restore.md` | neu | Drei Restore-Szenarien dokumentiert |
| `tests/test_database_wal_mode.py` | neu | pytest: WAL-Modus-Regressionsschutz |
| `README.md` | erweitern | Kurzer Hinweis auf Backup + Link ins Runbook |
| `fly.toml` | unverändert | (Secrets werden via `fly secrets set` injiziert) |

## Konfigurationen

### `litestream.yml`

```yaml
dbs:
  - path: /data/olivalle.db
    replicas:
      - type: s3
        bucket: olivalle-backup
        path: olivalle
        region: auto
        endpoint: https://fly.storage.tigris.dev
        access-key-id: ${LITESTREAM_ACCESS_KEY_ID}
        secret-access-key: ${LITESTREAM_SECRET_ACCESS_KEY}
        retention: 720h
        retention-check-interval: 24h
        snapshot-interval: 24h
        sync-interval: 1s
```

### `Dockerfile` (Ergänzung)

```dockerfile
ARG LITESTREAM_VERSION=0.3.13
RUN curl -L https://github.com/benbjohnson/litestream/releases/download/v${LITESTREAM_VERSION}/litestream-v${LITESTREAM_VERSION}-linux-amd64.tar.gz \
    | tar -xzC /usr/local/bin

COPY litestream.yml /etc/litestream.yml
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

Version `0.3.13` wird explizit gepinnt (gleiches Prinzip wie beim GitHub-Actions-SHA-Pinning).

### `entrypoint.sh`

```bash
#!/bin/sh
set -e

# 1. Auto-Restore bei leerem Volume (Katastrophenfall)
if [ ! -f /data/olivalle.db ]; then
  echo "[entrypoint] Keine DB gefunden — versuche Restore aus Tigris…"
  litestream restore -if-replica-exists -config /etc/litestream.yml /data/olivalle.db
fi

# 2. Heartbeat-Loop im Hintergrund
#    (pingt Healthchecks.io nur wenn Litestream in letzten 15 Min geschrieben hat)
(
  while true; do
    sleep 600
    if find /data/olivalle.db-litestream -type f -mmin -15 2>/dev/null | grep -q .; then
      curl -fsS -m 10 --retry 3 -o /dev/null "$HEALTHCHECKS_URL" || true
    fi
  done
) &

# 3. Litestream als PID 1, uvicorn als überwachter Subprocess
exec litestream replicate -config /etc/litestream.yml -exec "uvicorn app.main:app --host 0.0.0.0 --port 8000"
```

### Neue fly-Secrets

Einmalig manuell gesetzt (konsistent mit Memory `project_fly_secrets_approach.md`):

```bash
fly storage create olivalle-backup --org personal
# gibt BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

fly secrets set \
  LITESTREAM_ACCESS_KEY_ID=... \
  LITESTREAM_SECRET_ACCESS_KEY=... \
  HEALTHCHECKS_URL=https://hc-ping.com/<uuid>
```

## Runbook-Szenarien

Inhalt von `docs/runbook-restore.md`:

**Szenario A — Komplettverlust des fly-Volumes**
1. `fly logs -a olivalle` — Fehler prüfen
2. `fly deploy` — entrypoint.sh triggert Auto-Restore
3. Shop-Smoke-Test + Stripe-Abgleich der letzten Bestellungen

Downtime ~5 Min, Datenverlust im Sekundenbereich.

**Szenario B — Korrupte DB**
1. `fly ssh console -a olivalle`
2. `mv /data/olivalle.db /data/olivalle.db.broken`
3. `litestream restore -config /etc/litestream.yml /data/olivalle.db` (optional `-timestamp`)
4. `fly machine restart` — Smoke-Test

**Szenario C — Jährlicher Restore-Test (geplant)**
1. Lokal: `litestream restore -o /tmp/olivalle-restore-test.db -config litestream.yml`
2. `sqlite3 /tmp/olivalle-restore-test.db "PRAGMA integrity_check;"` → `ok`
3. `SELECT COUNT(*) FROM bestellungen` Plausibilitätscheck
4. Datum und Ergebnis im Runbook-Anhang festhalten

Runbook enthält ausserdem: Zugangsliste (fly, Tigris, Healthchecks.io), fly-Support-Kontakt, Links zur Litestream-Doku.

## Testing & Abnahme

**Ebene 1 — Automatisierte Tests (pytest + shellcheck, CI)**

| Test | Prüft |
|---|---|
| `tests/test_database_wal_mode.py` | `PRAGMA journal_mode` liefert `wal` (Regressionsschutz) |
| `shellcheck entrypoint.sh` | Statische Syntaxprüfung, eingehängt in `make lint-all` |

**Ebene 2 — Manuelle Abnahme-Checkliste (im PR)**

- **Pre-Deploy:** Tigris-Bucket angelegt, Secrets gesetzt, Healthchecks.io-Check aktiv
- **Post-Deploy:** fly-logs zeigen `litestream: initialized db` und `snapshot written`, Tigris-Bucket enthält Snapshot, Healthchecks-Status `up`
- **Restore-Test (einmalig):** Lokaler Restore + `integrity_check` + Plausibilitätsabfrage
- **Katastrophenfall-Simulation:** `mv olivalle.db olivalle.db.bak`, Machine-Restart, Auto-Restore verifizieren

## Risiken & bewusste Kompromisse

- **Same-Provider-Risiko**: Backup bei fly (Tigris). Akzeptiert, weil Migration auf Cloudflare R2 später nur Litestream-Konfig-Änderung wäre, keine App-Änderung.
- **Tigris-Keys beim Entwickler**: Für Restore braucht der Inhaber fly-CLI-Zugang oder Entwicklerhilfe. Akzeptiert für Einzelunternehmer-Projekt; weniger Credential-Standorte = weniger Angriffsfläche.
- **Kein Staging-Restore-Workflow**: Jährlicher Test erfolgt lokal. Overhead einer Staging-Pipeline nicht gerechtfertigt für dieses Projektvolumen.

## Issue-Abschlusskriterien

- [ ] ADR, Runbook und Code-Änderungen gemerged (ein PR)
- [ ] Alle Pre- und Post-Deploy-Checks abgehakt
- [ ] Initialer Restore-Test dokumentiert
- [ ] Kalendereintrag für jährlichen Restore-Test erstellt
- [ ] Issue #110 geschlossen mit Link auf ADR
