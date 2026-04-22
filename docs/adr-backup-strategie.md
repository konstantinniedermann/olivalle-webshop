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
| (a) Litestream + Tigris | Kontinuierliche WAL-Replikation | Tigris (fly, EU-Multi-Region) | Sekunden | 0 CHF (Free Tier) |
| (b) Täglicher sqlite3 .backup + Upload | Cron + Shell-Skript | Cloudflare R2 | 24h | 0 CHF |
| (c) GitHub Action via fly ssh | Scheduled extern | Cloudflare R2 | 24h | 0 CHF |
| (d) Nur fly-Snapshots (Status quo) | — | fly intern | Tage | 0 CHF |

## Entscheidung

**(a) Litestream mit Tigris-Bucket, Location `eur` (Multi-Region: Amsterdam + Frankfurt).**

### Entscheidungsfindung

1. **RPO in Sekunden statt Tagen:** Jede Olivalle-Bestellung ist CHF 8–50.
   Tagesverlust = reale Umsatzeinbussen + Vertrauensschaden. Litestream
   repliziert praktisch verlustfrei.
2. **DSG-konform:** Tigris-Location `eur` hält die Daten ausschliesslich in
   der EU (Amsterdam + Frankfurt, zwei Kopien). Konsistent mit dem
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

---

## Nachtrag 2026-04-22: Heartbeat-Strategie & `min_machines_running`

**Kontext:** Issue [#116](https://github.com/konstantinniedermann/olivalle-webshop/issues/116). Nach Inbetriebnahme (#110) zeigte sich, dass der Heartbeat-Loop in `entrypoint.sh` mit dem Container stirbt, wenn fly die Machine nach ~5 Min Idle via `auto_stop_machines = 'stop'` anhält. Dadurch drohten false-positive Alerts bei ruhigen Phasen — speziell nachts und an Tagen ohne Besucher.

**Entscheidung:** `min_machines_running = 1` in `fly.toml`. fly lässt mindestens 1 Machine durchgängig laufen; Auto-Stop bleibt formal aktiv, greift aber nicht. Heartbeat-Loop pingt dadurch 24/7, Healthchecks.io-Konfig (Period 10 Min, Grace 5 Min) bleibt unverändert.

**Verworfene Alternativen:**
- **Grace-Period hochsetzen** (z.B. auf 4–24 h): deckt realistische "Tage ohne Besucher" nicht ab.
- **Externer Cron (GitHub Action) prüft Tigris-Snapshot-Alter**: mehr Komplexität, neue Secrets, neuer Failure-Mode — für den erwartbaren Kostengewinn (~CHF 1.40/Mt) nicht lohnend.
- **Passive Überwachung, nur Admin-Dashboard**: kein Push-Alert bei echtem Ausfall — inakzeptabel.

**Kosten:** Geschätzt ~CHF 0.30/Mt vorher → ~CHF 1.75/Mt nachher, Delta ~CHF 1.40/Mt (~CHF 17/Jahr). Siehe Spec `docs/superpowers/specs/2026-04-22-issue-116-heartbeat-tuning-design.md` für Detailrechnung.

**Konsequenzen:**
- Ein Heartbeat-Alert ist ab 2026-04-22 **ernst zu nehmen** (keine Toleranz mehr durch Machine-Stop). Runbook-Abschnitt "Heartbeat-Alert erhalten" entsprechend aktualisiert.
- Nebeneffekt: Kein Kaltstart-Delay (~3–10 s) für echte Kunden beim ersten Besuch nach Idle.
- Verifikationsfenster: 7 Tage Beobachtung nach Deploy; Issue #116 schliesst erst dann.
