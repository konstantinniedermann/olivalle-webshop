# Heartbeat-Tuning via `min_machines_running = 1` (Issue #116) — Design

**Issue:** [#116](https://github.com/konstantinniedermann/olivalle-webshop/issues/116) — `ops: Heartbeat vs. fly Auto-Stop — false-positive Alerts beim schlafenden Container vermeiden`

**Related:** [`adr-backup-strategie.md`](../../adr-backup-strategie.md), [`runbook-restore.md`](../../runbook-restore.md), [Issue #110](https://github.com/konstantinniedermann/olivalle-webshop/issues/110) (Backup-Setup), [Issue #115](https://github.com/konstantinniedermann/olivalle-webshop/issues/115) (Restore-Test)

## Zweck

Heartbeat-Alerts von Healthchecks.io sollen nur **echte** Probleme (Litestream-Replikation tatsächlich gestört) melden, nicht normales fly-Auto-Stop-Verhalten. Heute stirbt der Heartbeat-Loop zusammen mit dem Container, sobald fly die Machine nach ~5 Min Idle stoppt — false-positive Alerts drohen bei ruhigen Phasen.

## Scope

**In Scope**
- Einzeilige Konfig-Änderung in `fly.toml`: `min_machines_running = 0 → 1`
- ADR-Ergänzung in `docs/adr-backup-strategie.md` (Entscheidung, verworfene Alternativen, Kostenbegründung)
- Runbook-Update in `docs/runbook-restore.md` (Heartbeat-Alert-Interpretation)
- Kostenaktualisierung in `CLAUDE.md` (Hosting-Zeile)
- Memory-Update `project_backup_setup.md` nach Deploy
- Verifikation: 7 Tage Beobachtung ohne false-positives, dann Issue-Schluss

**Out of Scope**
- Änderungen an `entrypoint.sh`, `litestream.yml`, Healthchecks.io-Grace-Period oder dem Heartbeat-Loop selbst — der bestehende Pfad bleibt unverändert.
- Admin-UI-Erweiterung "Snapshot-Alter anzeigen" — eigenes Follow-up-Issue wert, falls gewünscht.
- Externer Tigris-Check via GitHub Action (Option C) — nur relevant falls 24/7-Kosten später inakzeptabel werden.
- SH-Freigabe-Prozess — Entscheidung: Umsetzung ohne Rückfrage (Delta ~CHF 1.40/Mt unterhalb Erheblichkeitsschwelle).

## Entscheidung & Alternativen

**Gewählt: Option A — `min_machines_running = 1`**

fly lässt mindestens 1 Machine durchgängig laufen. Auto-Stop bleibt formal aktiv, greift aber nicht, weil fly die Minimum-Menge schützt. Heartbeat-Loop läuft dadurch 24/7, Healthchecks.io-Konfig (Period 10 Min, Grace 5 Min) bleibt unverändert — enger Fehlerzeitraum ist ab jetzt Feature, kein Bug.

**Verworfene Alternativen:**

| Option | Verworfen weil |
|---|---|
| **B** — Healthchecks.io Grace-Period erhöhen (4h–24h) | Bei realistischen "Tagen ohne Besucher" (Olivalle ist Nischen-Shop) reicht auch 24h nicht. |
| **C** — Externer Cron (GitHub Action) prüft Tigris-Snapshot-Alter | Mehr Komplexität, neue Secrets, neuer Failure-Mode — für den erwartbaren CHF-1.40/Mt-Gewinn nicht lohnend. |
| **D** — Passive Überwachung, nur Admin-Dashboard | Kein Push-Alert bei echtem Ausfall — inakzeptabel für eine Umsatz-tragende DB. |

## Kostenbetrachtung

| Position | Jetzt (Auto-Stop) | Nach Umsetzung (24/7) |
|---|---|---|
| Compute `shared-cpu-1x` 256 MB | ~$0.05–0.15/Mt *(20–50 h Runtime geschätzt)* | $1.94/Mt |
| Rootfs-Storage (stopped) | ~$0.07/Mt | — |
| Volume 1 GB | $0.15/Mt | $0.15/Mt |
| **Total** | **≈ $0.30–0.40/Mt** | **≈ $2.09/Mt** |
| In CHF (~0.83 USD/CHF) | **~CHF 0.25–0.35/Mt** | **~CHF 1.75/Mt** |

**Delta: ~$1.70/Mt = CHF ~1.40/Mt = CHF ~17/Jahr.**

Einordnung: Die CLAUDE.md-Schätzung "~$5/Mt" war konservativ; reale Kosten liegen weit darunter. Delta entspricht dem Wert von ~1/6 einer 250ml-Flasche (CHF 8) pro Monat und ist bei ~100 Bestellungen/Mt ≈ CHF 2'400 Umsatz nicht erheblich.

**Nebeneffekte der 24/7-Machine:**
- Kein Kaltstart-Delay (~3–10 s) für echte Kunden beim ersten Besuch nach Idle → UX-Gewinn.
- Heartbeat-Alerts werden ab sofort ernst zu nehmen sein (kein Toleranzband durch Machine-Stop).

## Änderungen im Detail

### 1. `fly.toml`

```diff
 [http_service]
   internal_port = 8000
   force_https = true
   auto_stop_machines = 'stop'
   auto_start_machines = true
-  min_machines_running = 0
+  min_machines_running = 1
```

### 2. `docs/adr-backup-strategie.md`

Neuer Abschnitt **"Nachtrag 2026-04-22: Heartbeat-Strategie & `min_machines_running`"**:
- Kontext (Verweis auf Issue #116)
- Entscheidung (Option A gewählt)
- Alternativen (B, C, D) mit Ablehnungsgrund
- Kostenbegründung (~CHF 1.40/Mt Delta)
- Konsequenzen (Heartbeat-Alert ist ab jetzt ernst)

### 3. `docs/runbook-restore.md`

Abschnitt **"Heartbeat-Alert erhalten — was tun?"** erweitern:
- Hinweis: Machine läuft 24/7 seit 2026-04-22, daher **keine Toleranz** für Machine-Stop als Erklärung.
- Jeder Heartbeat-Alert = vermuteter echter Replikationsausfall → Litestream-Status prüfen.

### 4. `CLAUDE.md` (Projekt)

Zeile "Hosting" im Tech-Stack-Block:
```diff
-| Hosting | fly.io (1 Docker-Container) | Günstig (~$5/Mt), kommerziell erlaubt |
+| Hosting | fly.io (1 Docker-Container, 24/7) | Günstig (~$2/Mt), kommerziell erlaubt |
```

### 5. Memory-Update (nach Deploy)

`/Users/KN/.claude/projects/-Users-KN-Dropbox-Privat-CAS-projekte-olivalle/memory/project_backup_setup.md`:
- Zeile ergänzen: "Seit 2026-04-22 läuft Machine 24/7 (`min_machines_running = 1`), Heartbeat dadurch durchgängig aktiv; siehe Issue #116."
- Folge-Issue-Zeile für #116 aus der "How to apply"-Liste entfernen.

## Verifikation & Akzeptanzkriterien

| Kriterium (aus Issue #116) | Wie geprüft |
|---|---|
| Option entschieden + im ADR dokumentiert | Code-Review vor Merge |
| Konfig umgesetzt (`fly.toml` / Healthchecks.io / Skript) | Diff in PR + `fly config show` nach Deploy |
| Runbook-Abschnitt "Heartbeat-Alert erhalten — was tun?" aktualisiert | Code-Review |
| Eine Woche im Normalbetrieb ohne false-positive Alerts verifiziert | Manuelle Beobachtung 7 Tage nach Deploy → erst dann Issue schliessen |

## Post-Deploy-Checks (manuell, direkt nach Merge)

- `fly status -a olivalle` → genau 1 Machine im Status `started`, bleibt dort.
- `fly logs -a olivalle --no-tail | tail -50` → Heartbeat-Loop-Logs mit regelmässigen `litestream_ok=1`-Zeilen sichtbar.
- [Healthchecks.io-Dashboard](https://healthchecks.io) → letzter Ping < 10 Min alt, Status grün.
- Nach ~1 h nochmals prüfen: Machine immer noch `started` (nicht zwischendurch gestoppt).

## Rollback

Falls unerwartetes Verhalten (Kosten-Spike, Instabilität):

```diff
 [http_service]
   internal_port = 8000
   force_https = true
   auto_stop_machines = 'stop'
   auto_start_machines = true
-  min_machines_running = 1
+  min_machines_running = 0
```

`fly deploy` — gleich alter Zustand. Null Datenrisiko (keine DB-Migration, keine Schema-Änderung).

## Deliverables

- PR gegen `main` mit:
  - `fly.toml` (1 Zeile geändert)
  - `docs/adr-backup-strategie.md` (Nachtrag-Abschnitt)
  - `docs/runbook-restore.md` (Alert-Interpretation)
  - `CLAUDE.md` (Kostenzeile)
  - Diese Spec (bereits committed)
  - Implementierungsplan (wird via `writing-plans` erstellt)
- Gemergt, Issue #116 nach 7 Tagen Beobachtung `Closes #116`
- Memory-Datei `project_backup_setup.md` aktualisiert

## Risiken

| Risiko | Mitigation |
|---|---|
| fly-Deploy bricht (Config-Fehler) | Triviale 1-Zeilen-Änderung, syntaktisch validierbar via `fly config validate` vor `fly deploy` |
| Echte Kosten weichen stark nach oben ab | Nach Deploy wöchentlich `fly dashboard` prüfen; Rollback jederzeit möglich |
| Heartbeat fällt während der 7-Tage-Beobachtung trotzdem falsch-positiv | Deutet auf anderes Problem hin (Litestream-Crash, Container-Restart) → dann eskalieren, nicht Issue schliessen |
| False-negative: echtes Backup-Problem während der Beobachtung übersehen | Unwahrscheinlich, aber Admin-Smoke-Check (ein Blick in `fly logs | grep litestream`) einmal pro Tag während der Woche |

## Test-Strategie

Keine Unit-Tests (pure Config-Änderung, kein App-Code). Validierung erfolgt via:
1. `fly config validate fly.toml` vor dem Deploy
2. Post-Deploy-Checks (siehe oben)
3. 7-Tage-Beobachtungsfenster

## Offene Folge-Themen (nicht in diesem Issue)

- **Admin-UI: Snapshot-Alter anzeigen** — Vorschlag, als eigenes Issue zu tracken, falls gewünscht. Wäre unabhängig von #116 eine sinnvolle zweite Monitoring-Schicht.
- **Jährlicher nicht-destruktiver Restore-Test** — bereits eingeplant für 2027-04-22 via Runbook Szenario C (siehe Memory `project_backup_setup.md`).
