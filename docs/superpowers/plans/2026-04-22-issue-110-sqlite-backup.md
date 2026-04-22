# SQLite-Backup-Strategie (Issue #110) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Kontinuierliche SQLite-Replikation via Litestream nach Tigris (Paris) einführen, mit Heartbeat-Monitoring, jährlichem Restore-Test-Runbook und automatischem Restore bei Volume-Verlust.

**Architecture:** Litestream läuft als Sidecar im bestehenden fly-Container (PID 1, `-exec uvicorn`). Replikation nach Tigris-Bucket in Region `cdg`. Healthchecks.io-Heartbeat alle 10 Min aus `entrypoint.sh`-Loop. ADR + Runbook ergänzen bestehende `docs/`-Struktur.

**Tech Stack:** Litestream 0.3.13, Tigris (fly storage), Healthchecks.io, Bash, pytest, shellcheck. Keine Python-Codeänderung (ausser einem Regressionstest).

**Spec:** [`docs/superpowers/specs/2026-04-22-issue-110-sqlite-backup-design.md`](../specs/2026-04-22-issue-110-sqlite-backup-design.md)

---

## File Structure

| Datei | Aktion | Verantwortung |
|---|---|---|
| `litestream.yml` | neu | Litestream-Replikationskonfig (eine DB, ein S3-Replica) |
| `entrypoint.sh` | neu | Auto-Restore + Heartbeat-Loop + `litestream replicate -exec uvicorn` |
| `Dockerfile` | modify | Litestream-Binary installieren, CMD → ENTRYPOINT |
| `.dockerignore` | check | Sicherstellen, dass `litestream.yml`/`entrypoint.sh` nicht ausgeschlossen werden |
| `tests/test_database_wal_mode.py` | neu | pytest: `get_db()` setzt `journal_mode=WAL` |
| `docs/adr-backup-strategie.md` | neu | Architekturentscheidung (Format wie `adr-email-provider.md`) |
| `docs/runbook-restore.md` | neu | Drei Restore-Szenarien (Volume-Verlust / Korruption / jährl. Test) |
| `docs/index.md` | modify | Link auf ADR und Runbook ergänzen |
| `README.md` | modify | Kurzer Backup-Abschnitt mit Link ins Runbook |
| `Makefile` | modify | `shellcheck`-Target und Einbindung in `lint-all` |
| `.github/workflows/lint.yml` | modify | shellcheck-Schritt ergänzen |

**Secrets (einmalig manuell via CLI, nicht im Repo):**
- `LITESTREAM_ACCESS_KEY_ID` (Tigris)
- `LITESTREAM_SECRET_ACCESS_KEY` (Tigris)
- `HEALTHCHECKS_URL` (Heartbeat-URL)

---

## Task 1: WAL-Modus-Regressionstest (pytest)

**Files:**
- Create: `tests/test_database_wal_mode.py`

- [ ] **Step 1: Failing Test schreiben**

```python
# tests/test_database_wal_mode.py
"""Regressionsschutz: get_db() muss WAL-Modus aktivieren.

Litestream repliziert über das SQLite-WAL. Fällt der WAL-Modus aus,
funktioniert das Backup stillschweigend nicht mehr.
"""

import sqlite3
from pathlib import Path


def test_get_db_aktiviert_wal_modus(monkeypatch, tmp_path):
    db_path = tmp_path / "olivalle-test.db"
    monkeypatch.setattr("app.config.settings.database_path", str(db_path))

    from app.database import get_db

    conn = get_db()
    try:
        row = conn.execute("PRAGMA journal_mode").fetchone()
        assert row[0].lower() == "wal", (
            f"journal_mode ist {row[0]}, erwartet 'wal' — "
            "ohne WAL funktioniert die Litestream-Replikation nicht"
        )
    finally:
        conn.close()
```

- [ ] **Step 2: Test ausführen und Fehler erwarten (falls Config nicht geladen)**

Run: `uv run pytest tests/test_database_wal_mode.py -v`
Expected: PASS — `get_db()` setzt WAL bereits in `app/database.py:12`. Dieser Test ist Regressionsschutz und soll sofort grün sein. Falls er rot ist: `app/database.py` wurde gebrochen und muss korrigiert werden, **bevor** der Rest des Plans weiterläuft.

- [ ] **Step 3: Commit**

```bash
git add tests/test_database_wal_mode.py
git commit -m "test: WAL-Modus-Regressionsschutz fuer Litestream (#110)"
```

---

## Task 2: `litestream.yml` anlegen

**Files:**
- Create: `litestream.yml` (Repo-Root)

- [ ] **Step 1: Datei schreiben**

```yaml
# litestream.yml
# Repliziert /data/olivalle.db kontinuierlich nach Tigris (Paris / cdg).
# Secrets (LITESTREAM_*) werden via fly secrets set injiziert.
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
        retention: 720h              # 30 Tage
        retention-check-interval: 24h
        snapshot-interval: 24h
        sync-interval: 1s
```

- [ ] **Step 2: Verifizieren dass `.dockerignore` die Datei nicht ausschliesst**

Run: `grep -n litestream .dockerignore || echo "nicht ignoriert → ok"`
Expected: Ausgabe `nicht ignoriert → ok`. Falls Ausgabe eine Zeile mit Pattern zeigt → Eintrag entfernen, weil die Datei ins Image muss.

- [ ] **Step 3: Commit**

```bash
git add litestream.yml
git commit -m "feat: Litestream-Konfig fuer Tigris-Replikation (#110)"
```

---

## Task 3: `entrypoint.sh` anlegen + shellcheck lokal prüfen

**Files:**
- Create: `entrypoint.sh` (Repo-Root)

- [ ] **Step 1: Script schreiben**

```bash
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

Run:
```bash
chmod +x entrypoint.sh
```

- [ ] **Step 2: shellcheck lokal installieren (falls fehlend) und ausführen**

Run: `command -v shellcheck >/dev/null || brew install shellcheck`
Run: `shellcheck entrypoint.sh`
Expected: keine Warnungen (exit 0). Falls Warnungen: korrigieren, bevor weiter.

- [ ] **Step 3: Commit**

```bash
git add entrypoint.sh
git commit -m "feat: entrypoint.sh mit Litestream-Auto-Restore + Heartbeat (#110)"
```

---

## Task 4: Dockerfile anpassen

**Files:**
- Modify: `Dockerfile:22-31` (EXPOSE + CMD-Block ersetzen)

- [ ] **Step 1: Dockerfile editieren**

Ersetze den Block ab `EXPOSE 8000` (aktuell `Dockerfile:22-31`) durch:

```dockerfile
# Litestream-Binary installieren (pinned, analog zum SHA-Pinning-Grundsatz).
# Architektur via TARGETARCH damit fly sowohl amd64 als auch arm64 deployen kann.
ARG LITESTREAM_VERSION=0.3.13
ARG TARGETARCH=amd64
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && curl -fsSL "https://github.com/benbjohnson/litestream/releases/download/v${LITESTREAM_VERSION}/litestream-v${LITESTREAM_VERSION}-linux-${TARGETARCH}.tar.gz" \
      | tar -xzC /usr/local/bin \
 && apt-get purge -y curl \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

COPY litestream.yml /etc/litestream.yml
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

# Migrationen + uvicorn werden von entrypoint.sh orchestriert.
ENTRYPOINT ["/entrypoint.sh"]
```

Der alte `CMD`-Zeile wird komplett entfernt — Migration und uvicorn laufen nun aus `entrypoint.sh`.

- [ ] **Step 2: Image lokal bauen, um Syntaxfehler auszuschliessen**

Run: `docker build -t olivalle-litestream-check .`
Expected: Build erfolgreich. Wichtig: `curl` muss in Stage 2 installiert sein (python:3.13-slim hat es nicht), deshalb der apt-Block.

- [ ] **Step 3: Litestream im Image prüfen**

Run: `docker run --rm --entrypoint litestream olivalle-litestream-check version`
Expected: Ausgabe `v0.3.13`.

- [ ] **Step 4: Commit**

```bash
git add Dockerfile
git commit -m "feat: Dockerfile installiert Litestream und nutzt entrypoint.sh (#110)"
```

---

## Task 5: ADR schreiben

**Files:**
- Create: `docs/adr-backup-strategie.md`

- [ ] **Step 1: Datei schreiben** — Inhalt exakt wie folgt (Format orientiert sich an `docs/adr-email-provider.md`):

```markdown
# ADR: Backup-Strategie — Litestream + Tigris

**Status:** Entschieden (2026-04-22)
**Beteiligte:** Entwickler (KN)

## Kontext

Der Olivalle-Webshop läuft live auf fly.io. Die SQLite-DB
(`/data/olivalle.db`, WAL-Modus) liegt auf einem persistenten fly-Volume.
fly macht automatisch Volume-Snapshots, aber:
- nur 5 Tage Retention
- Snapshots einer WAL-SQLite können inkonsistent sein
- kein dokumentierter Restore-Prozess, nie getestet

Bei Volume-Verlust oder Korruption sind alle Bestellungen, Kundendaten
und Rabattcodes weg. Nicht akzeptabel für einen Live-Shop.

## Evaluierte Optionen

| Option | Methode | Ziel-Storage | RPO | Kosten |
|---|---|---|---|---|
| (a) Litestream + Tigris | Kontinuierliche WAL-Replikation | Tigris (fly, cdg) | Sekunden | 0 CHF (Free Tier) |
| (b) Täglicher sqlite3 .backup + Upload | Cron + Shell-Skript | Cloudflare R2 | 24h | 0 CHF |
| (c) GitHub Action via fly ssh | Scheduled extern | Cloudflare R2 | 24h | 0 CHF |
| (d) Nur fly-Snapshots (Status quo) | — | fly intern | Tage | 0 CHF |

## Entscheidung

**(a) Litestream mit Tigris-Bucket in Region `cdg` (Paris, EU).**

### Entscheidungsfindung

1. **RPO in Sekunden statt Tagen:** Jede Olivalle-Bestellung ist CHF 8–50.
   Tagesverlust = reale Umsatzeinbussen + Vertrauensschaden. Litestream
   repliziert praktisch verlustfrei.
2. **DSG-konform:** Tigris-Region `cdg` = Paris/EU. Konsistent mit dem
   Brevo-ADR (Frankreich).
3. **Gratis bei dieser Grösse:** DB ~10 MB, Tigris Free Tier 10 GB.
4. **Integriert in fly-Ökosystem:** Ein Account, ein Billing, ein CLI.
5. **Automatischer Restore beim Container-Start:** Im Katastrophenfall
   zieht `entrypoint.sh` den Backup automatisch — kein manueller Eingriff.

### Verworfene Alternativen

- **(b)/(c)** RPO zu hoch für Live-Shop mit echten Zahlungen
- **(d)** 5-Tage-Retention und WAL-Inkonsistenz sind genau die Risiken,
  die Issue #110 adressieren will

## Konsequenzen

- Neue Dateien: `Dockerfile` erweitert, `litestream.yml`, `entrypoint.sh`
- Neue fly-Secrets: `LITESTREAM_ACCESS_KEY_ID`, `LITESTREAM_SECRET_ACCESS_KEY`,
  `HEALTHCHECKS_URL` (manuell via `fly secrets set`, konsistent zur
  Projekt-Konvention)
- Neues Runbook: `docs/runbook-restore.md`
- Monitoring: Healthchecks.io-Heartbeat alle 10 Min
- Jährlicher manueller Restore-Test (Kalendereintrag)

### Risiken & Folge-Issues

- **Tigris-Ausfall bei gleichzeitigem fly-Ausfall**: Same-Provider-Risiko
  bewusst akzeptiert. Migration nach Cloudflare R2 wäre nur eine
  `litestream.yml`-Änderung, keine App-Änderung.
- **Key-Rotation**: Tigris-Keys haben kein Ablaufdatum. Bei Entwickler-
  Wechsel manuell rotieren und Runbook aktualisieren.
```

- [ ] **Step 2: Commit**

```bash
git add docs/adr-backup-strategie.md
git commit -m "docs: ADR Backup-Strategie Litestream+Tigris (#110)"
```

---

## Task 6: Runbook schreiben

**Files:**
- Create: `docs/runbook-restore.md`

- [ ] **Step 1: Datei schreiben**

````markdown
# Runbook: Backup-Restore für Olivalle

**Ziel-Leser:** Entwickler oder Inhaber. Szenario A kann der Inhaber
eigenständig durchführen, falls fly-CLI-Zugang vorhanden.

**Siehe auch:** [`adr-backup-strategie.md`](adr-backup-strategie.md)

## Zugänge, die nötig sind

| Was | Wo | Wer hat Zugriff |
|---|---|---|
| fly-Account (olivalle-App) | https://fly.io | Entwickler |
| Tigris-Bucket `olivalle-backup` | `fly storage` | automatisch via fly-Secrets |
| Healthchecks.io-Check | https://healthchecks.io | Entwickler |
| Domain-Registrar (DNS) | siehe `adr-domain-registrar.md` | Entwickler |

fly-Support im Ernstfall: https://community.fly.io oder
https://fly.io/docs/about/support/.

---

## Szenario A — Komplettverlust des fly-Volumes

**Symptom:** fly meldet Volume-Ausfall, die Machine startet nicht oder startet
mit leerer DB.

```bash
fly logs -a olivalle                    # Ursache prüfen
fly deploy                              # entrypoint.sh triggert Auto-Restore
```

`entrypoint.sh` erkennt beim Start, dass `/data/olivalle.db` fehlt, und zieht
den letzten Stand aus Tigris. Erwartete Downtime ~5 Min, Datenverlust im
Sekundenbereich.

**Verifikation:**
1. Shop-Startseite aufrufen → 200
2. Im Admin-Bereich die letzten 5 Bestellungen gegen das Stripe-Dashboard
   abgleichen

---

## Szenario B — DB ist da, aber korrupt

**Symptom:** Admin-Bereich zeigt Unsinn, Fehler in `fly logs`, oder
`PRAGMA integrity_check` schlägt fehl.

```bash
fly ssh console -a olivalle
```

Im Container:

```sh
# Alte DB wegsichern (nicht löschen — forensische Reserve)
mv /data/olivalle.db /data/olivalle.db.broken

# Restore aus Tigris (optional Point-in-Time)
litestream restore -config /etc/litestream.yml /data/olivalle.db
# Point-in-Time-Variante:
# litestream restore -timestamp 2026-04-22T14:00:00Z \
#   -config /etc/litestream.yml /data/olivalle.db

exit
```

Danach:

```bash
fly machine restart -a olivalle
```

**Verifikation** wie Szenario A.

---

## Szenario C — Jährlicher Restore-Test

**Kalendereintrag:** "Olivalle Backup-Test" — 1x/Jahr (empfohlen im April,
zum Jahrestag der Einführung).

### Schritte

1. Tigris-Credentials lokal als ENV-Vars setzen (aus fly-Secrets):

   ```bash
   export LITESTREAM_ACCESS_KEY_ID="$(fly secrets list --app olivalle | grep LITESTREAM_ACCESS_KEY_ID)"  # Wert ist nicht sichtbar → temporär via 'fly ssh console' und echo holen ODER aus eigenem Passwort-Manager
   export LITESTREAM_SECRET_ACCESS_KEY="…"
   ```

   > **Hinweis:** `fly secrets list` zeigt Secrets nicht im Klartext. Praktikabler
   > Weg: `fly ssh console -a olivalle -C 'printenv LITESTREAM_ACCESS_KEY_ID'`
   > (einmalig für den Test, danach lokal wieder löschen).

2. Restore in ein tmp-File:

   ```bash
   litestream restore \
     -config litestream.yml \
     -o /tmp/olivalle-restore-test.db
   ```

3. Integritätscheck:

   ```bash
   sqlite3 /tmp/olivalle-restore-test.db "PRAGMA integrity_check;"
   ```

   Erwartet: `ok`.

4. Plausibilitätsabfrage:

   ```bash
   sqlite3 /tmp/olivalle-restore-test.db \
     "SELECT COUNT(*) AS bestellungen,
             MIN(erstellt_am) AS erste,
             MAX(erstellt_am) AS letzte
      FROM bestellungen;"
   ```

   Die Anzahl muss plausibel zum Shop-Umsatz der letzten Monate passen.

5. Ergebnis im Anhang unten festhalten und tmp-File löschen:

   ```bash
   rm /tmp/olivalle-restore-test.db
   ```

---

## Heartbeat-Alert erhalten — was tun?

Healthchecks.io mailt, wenn > 15 Min kein Ping kam.

1. `fly logs -a olivalle` — läuft die App überhaupt? (Machine könnte schlafen)
2. `fly ssh console -a olivalle` → `ls -la /data/olivalle.db-litestream`
   → Modifikationszeiten prüfen
3. `fly logs` nach `litestream:` filtern — Replikationsfehler sichtbar?
4. Häufigster Fall: Tigris-Credentials rotiert/abgelaufen → neue Keys
   erzeugen (`fly storage create` hat eine `regen`-Variante oder Bucket
   neu anlegen) und via `fly secrets set` injizieren.

---

## Anhang: Protokoll der Restore-Tests

| Datum | Ergebnis `integrity_check` | Bestellungen | Bemerkung |
|---|---|---|---|
| YYYY-MM-DD | ok / FAIL | N | — |
````

- [ ] **Step 2: Commit**

```bash
git add docs/runbook-restore.md
git commit -m "docs: Runbook fuer Backup-Restore (3 Szenarien + Heartbeat) (#110)"
```

---

## Task 7: `docs/index.md` und `README.md` ergänzen

**Files:**
- Modify: `docs/index.md` (Link in bestehende Struktur einhängen)
- Modify: `README.md` (Backup-Abschnitt)

- [ ] **Step 1: `docs/index.md` prüfen und ergänzen**

Run: `cat docs/index.md`
Lokalisiere die ADR-Liste. Füge einen Eintrag ein:

```markdown
- [ADR: Backup-Strategie (Litestream + Tigris)](adr-backup-strategie.md)
```

Lokalisiere die Runbook-/Betriebsliste (oder schaffe sie, falls noch nicht existent). Füge ein:

```markdown
- [Runbook: Backup-Restore](runbook-restore.md)
```

- [ ] **Step 2: `README.md` ergänzen**

Lokalisiere einen passenden Abschnitt (nach `Tech-Stack` oder vor `Schnellstart`). Füge ein:

```markdown
## Backups & Wiederherstellung

Die SQLite-DB wird kontinuierlich via [Litestream](https://litestream.io)
nach einem Tigris-Bucket (Region Paris) repliziert. Im Katastrophenfall
(Volume-Verlust) restored der Container automatisch beim Start.

- Architekturentscheidung: [`docs/adr-backup-strategie.md`](docs/adr-backup-strategie.md)
- Restore-Anleitung: [`docs/runbook-restore.md`](docs/runbook-restore.md)
```

- [ ] **Step 3: Commit**

```bash
git add docs/index.md README.md
git commit -m "docs: Backup-Strategie in README und Doku-Index verlinken (#110)"
```

---

## Task 8: shellcheck in Makefile und CI integrieren

**Files:**
- Modify: `Makefile` (neuer Target + `lint-all` erweitern)
- Modify: `.github/workflows/lint.yml` (shellcheck-Step ergänzen)

- [ ] **Step 1: Makefile anpassen**

Bearbeite `Makefile`. In der `.PHONY:`-Zeile `shellcheck` ergänzen:

```makefile
.PHONY: help dev test lint lint-all format migrate docs css-build css-watch shellcheck
```

Am Ende neuen Target ergänzen:

```makefile
shellcheck: ## Shell-Skripte statisch prüfen
	shellcheck entrypoint.sh
```

`lint-all`-Target um shellcheck erweitern:

```makefile
lint-all: ## Ruff-Check + Format-Check + shellcheck (gleich wie CI)
	uv run ruff check app tests
	uv run ruff format --check app tests
	shellcheck entrypoint.sh
```

- [ ] **Step 2: Lokal prüfen**

Run: `make lint-all`
Expected: keine Fehler. Falls `shellcheck` fehlt: `brew install shellcheck`.

- [ ] **Step 3: CI-Workflow anpassen**

Bearbeite `.github/workflows/lint.yml`. Nach dem Ruff-Format-Step ergänzen:

```yaml
      - name: ShellCheck
        uses: ludeeus/action-shellcheck@00cae500b08a931fb5698e11e79bfbd38e612a38  # v2.0.0
        with:
          scandir: '.'
          additional_files: 'entrypoint.sh'
```

> SHA-Pinning ist Projektstandard (Memory `feedback_github_actions_sha_pinning.md`).
> Der SHA oben ist `ludeeus/action-shellcheck@v2.0.0`. **Vor Commit verifizieren**
> mit: `gh api repos/ludeeus/action-shellcheck/git/refs/tags/v2.0.0 --jq .object.sha`
> (falls ein neuerer v2-Tag existiert, dessen SHA verwenden).

- [ ] **Step 4: Commit**

```bash
git add Makefile .github/workflows/lint.yml
git commit -m "ci: shellcheck fuer entrypoint.sh in make lint-all + CI (#110)"
```

---

## Task 9: Tigris-Bucket + fly-Secrets setzen (manuelle Vorarbeit vor Deploy)

> **Diese Task produziert keinen Repo-Commit** — sie dokumentiert die manuellen Schritte, die **einmalig** vor dem Merge-Deploy ausgeführt werden. Resultat dieser Task: drei gesetzte fly-Secrets und ein aktiver Healthchecks.io-Check.

- [ ] **Step 1: Tigris-Bucket anlegen**

Run:
```bash
fly storage create olivalle-backup --org personal
```

Expected: Ausgabe mit `BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`. Den Bucket-Namen im Kopf behalten (soll `olivalle-backup` sein; falls fly einen Suffix vergibt → `litestream.yml` entsprechend anpassen und Commit vor Deploy).

- [ ] **Step 2: Region prüfen**

Run: `fly storage list`
Expected: Bucket in Region `cdg` (Paris). Falls andere Region → Bucket löschen und neu anlegen mit `--region cdg`.

- [ ] **Step 3: Healthchecks.io-Check anlegen**

1. Auf https://healthchecks.io anmelden (Free Tier, 20 Checks)
2. Neuen Check "olivalle-litestream-heartbeat" anlegen
3. Period: 10 Minuten, Grace: 5 Minuten (= Alarm nach 15 Min ohne Ping)
4. Benachrichtigung auf `konstantin.niedermann@gmail.com` konfigurieren
5. Ping-URL kopieren (Format: `https://hc-ping.com/<uuid>`)

- [ ] **Step 4: fly-Secrets setzen (LITESTREAM_*-Namespace)**

> `fly storage create` setzt die Werte standardmässig als `AWS_ACCESS_KEY_ID` und
> `AWS_SECRET_ACCESS_KEY` auf der App. Wir spiegeln sie bewusst unter
> `LITESTREAM_*`, damit der Zweck im Namen sichtbar ist und keine Kollision mit
> zukünftigen AWS-SDK-Usages entsteht.

Run:
```bash
# 1) Werte (aus Schritt 1 Output) unter LITESTREAM_* setzen
fly secrets set \
  LITESTREAM_ACCESS_KEY_ID='<aus Schritt 1>' \
  LITESTREAM_SECRET_ACCESS_KEY='<aus Schritt 1>' \
  HEALTHCHECKS_URL='<aus Schritt 3>' \
  --app olivalle

# 2) Die redundanten AWS_*-Secrets entfernen (nicht nötig, da litestream.yml
#    explizit LITESTREAM_* referenziert)
fly secrets unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY --app olivalle
```

Expected: `Secrets are staged for the first deployment`.

- [ ] **Step 5: Secrets verifizieren**

Run: `fly secrets list --app olivalle`
Expected: `LITESTREAM_ACCESS_KEY_ID`, `LITESTREAM_SECRET_ACCESS_KEY`, `HEALTHCHECKS_URL`, `BUCKET_NAME` sichtbar. Kein `AWS_*` mehr (falls doch: Unset nochmal ausführen).

- [ ] **Step 6: Bucket-Namen in `litestream.yml` gegenprüfen**

`fly storage create` kann den Bucket-Namen mit einem Org-Prefix versehen. Prüfen:

Run: `fly secrets list --app olivalle | grep BUCKET_NAME`
Wenn der echte Bucket-Name **nicht** `olivalle-backup` ist: `litestream.yml` anpassen:

```yaml
bucket: <tatsächlicher Bucket-Name aus fly secrets>
```

und einen zusätzlichen Commit auf dem Feature-Branch machen, bevor Task 10 ausgeführt wird:

```bash
git add litestream.yml
git commit -m "fix: Bucket-Namen an tatsaechlichen Tigris-Namen anpassen (#110)"
```

---

## Task 10: Deploy + Abnahme-Checkliste

> **Erst ausführen, nachdem Tasks 1–9 gemerged oder in einem gemeinsamen PR gebündelt sind und Task 9 (manuell) erledigt ist.**

- [ ] **Step 1: CI lokal spiegeln**

Run: `make lint-all && uv run pytest -q`
Expected: alles grün.

- [ ] **Step 2: Deployen**

Run: `fly deploy --app olivalle`
Expected: Build erfolgreich, Machine startet, `fly logs` zeigt nacheinander:
1. `[entrypoint] Keine DB gefunden — versuche Restore aus Tigris…` (beim allerersten Deploy existiert kein Backup → "Kein Backup vorhanden — frische DB.") **ODER** bei jedem weiteren Deploy: DB existiert, Schritt wird übersprungen.
2. Migration-Log aus `init_db()`
3. `litestream: initialized db: /data/olivalle.db`
4. `litestream: snapshot written` (innerhalb 2 Min)
5. uvicorn Startup-Log

- [ ] **Step 3: Tigris-Bucket-Inhalt prüfen**

Run: `fly storage dashboard --app olivalle` (öffnet Browser) oder via AWS-CLI:

```bash
AWS_ACCESS_KEY_ID=<tigris-key> \
AWS_SECRET_ACCESS_KEY=<tigris-secret> \
aws s3 ls s3://olivalle-backup/olivalle/ \
  --endpoint-url https://fly.storage.tigris.dev
```

Expected: Es erscheinen Pfade wie `generations/.../snapshots/` und `generations/.../wal/`.

- [ ] **Step 4: Healthchecks.io-Status prüfen**

Auf https://healthchecks.io → Check "olivalle-litestream-heartbeat" muss innerhalb 15 Min nach Deploy auf grün (`up`) gehen.

- [ ] **Step 5: Katastrophenfall simulieren (einmaliger Restore-Test)**

```bash
fly ssh console -a olivalle
# Im Container:
mv /data/olivalle.db /data/olivalle.db.sim-backup
exit
fly machine restart -a olivalle
```

Nach ~30 Sek `fly logs`: muss `[entrypoint] Keine DB gefunden — versuche Restore aus Tigris…` und danach erfolgreichen Start zeigen. Shop-Startseite aufrufen, letzte 5 Bestellungen im Admin-Bereich prüfen → müssen vollständig sein.

Aufräumen:
```bash
fly ssh console -a olivalle
rm /data/olivalle.db.sim-backup
exit
```

- [ ] **Step 6: Ergebnis in Runbook eintragen**

Tabelle am Ende von `docs/runbook-restore.md` um eine Zeile erweitern:

```markdown
| 2026-04-22 | ok | <Anzahl aus Plausibilitätsabfrage> | Initialer Restore-Test |
```

```bash
git add docs/runbook-restore.md
git commit -m "docs: initialen Restore-Test im Runbook dokumentieren (#110)"
git push
```

- [ ] **Step 7: Kalendereintrag erstellen**

Google Calendar (oder äquivalent): "Olivalle Backup-Restore-Test" — 2027-04-22, ganztägig, jährlich wiederkehrend. Link ins Runbook in die Beschreibung.

- [ ] **Step 8: Issue #110 schliessen**

```bash
gh issue close 110 --comment "Umgesetzt. ADR: docs/adr-backup-strategie.md, Runbook: docs/runbook-restore.md. Restore-Test erfolgreich durchgeführt 2026-04-22."
```

- [ ] **Step 9: Folge-Issues prüfen**

Nach den Projekt-Regeln (Memory `feedback_pause_cleanup.md`): prüfen ob #111 (Uptime-Monitoring) jetzt einfacher wird, weil Healthchecks.io-Account bereits existiert. Falls ja: Hinweis im Issue #111 hinterlegen.

---

## Zusammenfassung der zu committenden Dateien

| Datei | Commits |
|---|---|
| `tests/test_database_wal_mode.py` | Task 1 |
| `litestream.yml` | Task 2 |
| `entrypoint.sh` | Task 3 |
| `Dockerfile` | Task 4 |
| `docs/adr-backup-strategie.md` | Task 5 |
| `docs/runbook-restore.md` | Task 6, Task 10/Step 6 |
| `docs/index.md`, `README.md` | Task 7 |
| `Makefile`, `.github/workflows/lint.yml` | Task 8 |

Tasks 9 und 10 sind operativ, keine Repo-Änderungen ausser der Restore-Test-Zeile im Runbook.
