# Heartbeat-Tuning Implementation Plan (Issue #116)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Setze `min_machines_running = 1` in `fly.toml`, damit der fly-Container 24/7 läuft, der Litestream-Heartbeat durchgängig pingt und Healthchecks.io keine false-positive Alerts mehr bei Auto-Stop-Phasen erzeugt.

**Architecture:** Pure Config- und Doku-Änderung. Kein App-Code betroffen, keine Unit-Tests nötig — Validierung erfolgt via `fly config validate`, Post-Deploy-Checks und 7-Tage-Beobachtung.

**Tech Stack:** fly.io (Deploy/Config), Markdown (ADR/Runbook/CLAUDE.md), Git/GitHub CLI.

**Spec:** [`docs/superpowers/specs/2026-04-22-issue-116-heartbeat-tuning-design.md`](../specs/2026-04-22-issue-116-heartbeat-tuning-design.md)

**Branch:** `feat/116-heartbeat-tuning` (bereits aktiv, Spec bereits committed)

---

## File Structure

**Modifizieren:**
- `fly.toml` (Zeile 23): `min_machines_running = 0 → 1`
- `docs/adr-backup-strategie.md` (neue Section am Ende): "Nachtrag 2026-04-22: Heartbeat-Strategie"
- `docs/runbook-restore.md` (Section "Heartbeat-Alert erhalten — was tun?", Zeile 131–141): Interpretation aktualisieren
- `CLAUDE.md` (Zeile 42): Hosting-Zeile mit aktualisierten Kosten

**Nicht modifizieren (bewusst):**
- `entrypoint.sh`, `litestream.yml`, `Dockerfile` — Backup-Pfad bleibt unverändert
- Healthchecks.io-Konfig (Period 10 Min, Grace 5 Min bleibt)
- `app/` — kein App-Code betroffen

**Post-Merge (separater Schritt nach 7 Tagen):**
- Memory `project_backup_setup.md` — Deploy-Datum ergänzen, Folge-Issue-Referenz entfernen
- Issue #116 schliessen

---

### Task 1: `fly.toml` ändern & validieren

**Files:**
- Modify: `fly.toml:23`

- [ ] **Step 1: Aktuellen Stand prüfen**

Run: `grep -n "min_machines_running" fly.toml`
Expected: `23:  min_machines_running = 0`

- [ ] **Step 2: Zeile ändern**

Edit `fly.toml`:

```diff
   auto_stop_machines = 'stop'
   auto_start_machines = true
-  min_machines_running = 0
+  min_machines_running = 1
```

- [ ] **Step 3: Lokale Syntax-Validierung**

Run: `fly config validate -a olivalle`
Expected: `Configuration is valid`

- [ ] **Step 4: Änderung sichten**

Run: `git diff fly.toml`
Expected: Genau eine Zeile geändert, nur `0 → 1` bei `min_machines_running`.

- [ ] **Step 5: Commit**

```bash
git add fly.toml
git commit -m "feat: Machine 24/7 laufen lassen (min_machines_running = 1) (#116)"
```

---

### Task 2: ADR-Nachtrag in `docs/adr-backup-strategie.md`

**Files:**
- Modify: `docs/adr-backup-strategie.md` (neue Section am Ende anhängen)

- [ ] **Step 1: Aktuelles Ende der Datei prüfen**

Run: `tail -10 docs/adr-backup-strategie.md`
Expected: Endet mit der "Key-Rotation"-Zeile im Abschnitt "Risiken & Folge-Issues".

- [ ] **Step 2: Nachtrag anhängen**

Append to `docs/adr-backup-strategie.md`:

```markdown

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
```

- [ ] **Step 3: Sichten**

Run: `tail -25 docs/adr-backup-strategie.md`
Expected: Neue Section korrekt angehängt, Markdown-Struktur intakt.

- [ ] **Step 4: Commit**

```bash
git add docs/adr-backup-strategie.md
git commit -m "docs: ADR-Nachtrag Heartbeat-Strategie (#116)"
```

---

### Task 3: Runbook-Abschnitt "Heartbeat-Alert erhalten" aktualisieren

**Files:**
- Modify: `docs/runbook-restore.md:131-141`

- [ ] **Step 1: Aktuellen Abschnitt sichten**

Run: `sed -n '131,141p' docs/runbook-restore.md`
Expected: Zeigt aktuellen Text (mit "Machine könnte schlafen").

- [ ] **Step 2: Abschnitt ersetzen**

Edit `docs/runbook-restore.md`, ersetze:

```markdown
## Heartbeat-Alert erhalten — was tun?

Healthchecks.io mailt, wenn > 15 Min kein Ping kam.

1. `fly logs -a olivalle` — läuft die App überhaupt? (Machine könnte schlafen)
2. `fly ssh console -a olivalle` → `ls -la /data/olivalle.db-litestream`
   → Modifikationszeiten prüfen
3. `fly logs` nach `litestream:` filtern — Replikationsfehler sichtbar?
4. Häufigster Fall: Tigris-Credentials rotiert/abgelaufen → neue Keys
   erzeugen (`fly storage create` hat eine `regen`-Variante oder Bucket
   neu anlegen) und via `fly secrets set` injizieren.
```

durch:

```markdown
## Heartbeat-Alert erhalten — was tun?

Healthchecks.io mailt, wenn > 15 Min kein Ping kam. **Seit 2026-04-22
(Issue #116) läuft die Machine via `min_machines_running = 1` durchgängig
— ein Alert ist daher ernst zu nehmen, kein Toleranzband mehr durch
Machine-Stop.**

1. `fly status -a olivalle` — Machine muss `started` sein. Falls `stopped`
   oder `failed`: fly-Problem, `fly machine restart` versuchen, bei
   Wiederholung fly-Support.
2. `fly logs -a olivalle --no-tail` — letzte Replikations-Zeilen prüfen.
   Nach `litestream:` filtern — Replikationsfehler sichtbar?
3. `fly ssh console -a olivalle` → `ls -la /data/olivalle.db-litestream`
   → Modifikationszeiten prüfen (sollten < 1 Min alt sein).
4. Häufigster Fall: Tigris-Credentials rotiert/abgelaufen → neue Keys
   erzeugen (`fly storage create` hat eine `regen`-Variante oder Bucket
   neu anlegen) und via `fly secrets set` injizieren.
```

- [ ] **Step 3: Sichten**

Run: `sed -n '131,150p' docs/runbook-restore.md`
Expected: Neue Fassung mit Hinweis auf `min_machines_running = 1` und Schritt 1 als `fly status`-Check.

- [ ] **Step 4: Commit**

```bash
git add docs/runbook-restore.md
git commit -m "docs: Runbook-Heartbeat-Alert-Interpretation aktualisiert (#116)"
```

---

### Task 4: `CLAUDE.md` Hosting-Kostenzeile aktualisieren

**Files:**
- Modify: `CLAUDE.md:42`

- [ ] **Step 1: Aktuelle Zeile prüfen**

Run: `grep -n "Hosting" CLAUDE.md`
Expected: `42:| Hosting | fly.io (1 Docker-Container) | Günstig (~$5/Mt), kommerziell erlaubt |`

- [ ] **Step 2: Zeile ersetzen**

Edit `CLAUDE.md`:

```diff
-| Hosting | fly.io (1 Docker-Container) | Günstig (~$5/Mt), kommerziell erlaubt |
+| Hosting | fly.io (1 Docker-Container, 24/7) | Günstig (~$2/Mt), kommerziell erlaubt |
```

- [ ] **Step 3: Sichten**

Run: `grep -n "Hosting" CLAUDE.md`
Expected: Neue Zeile mit `24/7` und `~$2/Mt`.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: Hosting-Kostenzeile aktualisiert (#116)"
```

---

### Task 5: Push & PR erstellen

**Files:** keine — Git-/GitHub-Operationen

- [ ] **Step 1: Commits sichten**

Run: `git log main..HEAD --oneline`
Expected: 5 Commits auf `feat/116-heartbeat-tuning`:
1. `docs: Design-Spec fuer Heartbeat-Tuning (#116)` (bereits gemacht)
2. `feat: Machine 24/7 laufen lassen (min_machines_running = 1) (#116)`
3. `docs: ADR-Nachtrag Heartbeat-Strategie (#116)`
4. `docs: Runbook-Heartbeat-Alert-Interpretation aktualisiert (#116)`
5. `docs: Hosting-Kostenzeile aktualisiert (#116)`

- [ ] **Step 2: Push mit Upstream**

Run: `git push -u origin feat/116-heartbeat-tuning`
Expected: Push erfolgreich, neuer Remote-Branch sichtbar.

- [ ] **Step 3: PR erstellen**

```bash
gh pr create --title "ops: Heartbeat-Tuning via min_machines_running=1 (#116)" --body "$(cat <<'EOF'
## Summary

- Setzt `min_machines_running = 1` in `fly.toml` — Machine läuft 24/7, Heartbeat-Loop pingt durchgängig an Healthchecks.io.
- Behebt false-positive Alerts durch fly-Auto-Stop in ruhigen Phasen.
- Kosten-Delta: ~CHF 1.40/Mt (Entscheidung dokumentiert in ADR-Nachtrag).

## Änderungen

- `fly.toml` — 1 Zeile
- `docs/adr-backup-strategie.md` — Nachtrag 2026-04-22 (Entscheidung + verworfene Alternativen + Kosten)
- `docs/runbook-restore.md` — "Heartbeat-Alert erhalten — was tun?" aktualisiert (Alerts sind ab jetzt ernst)
- `CLAUDE.md` — Hosting-Kostenzeile von `~$5/Mt` auf `~$2/Mt` angepasst

## Test plan

- [ ] CI grün
- [ ] Nach Merge: `fly deploy` → `fly status -a olivalle` zeigt 1 Machine `started`, bleibt stabil
- [ ] `fly logs -a olivalle --no-tail | grep litestream` zeigt regelmässige Heartbeat-Pings
- [ ] Healthchecks.io-Dashboard: letzter Ping < 10 Min alt, Status grün
- [ ] 7-Tage-Beobachtung ohne false-positive Alerts → dann Issue #116 schliessen

Closes-after-verification: #116

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 4: PR-URL festhalten**

Expected: `gh pr create` gibt die PR-URL aus. In die Session-Ausgabe für den nächsten Schritt übernehmen.

---

### Task 6: Review & Merge

**Files:** keine — GitHub-Aktion

- [ ] **Step 1: CI abwarten**

Run: `gh pr checks`
Expected: Alle Checks grün (lint.yml).

- [ ] **Step 2: Self-Review im PR**

Auf GitHub die Diff-Ansicht öffnen und durchgehen:
- fly.toml: einzelne Zeilenänderung, keine Nebenwirkungen.
- ADR-Nachtrag: Markdown rendert sauber.
- Runbook: Fluss der Anleitung bleibt sinnvoll.
- CLAUDE.md: Zeile konsistent mit Tabellen-Format.

- [ ] **Step 3: Code-Review via Skill**

Skill: `superpowers:requesting-code-review` — lässt einen Review-Subagenten die Änderung gegen Spec + CLAUDE.md-Standards prüfen (Doku-Konsistenz, Commit-Konvention, OWASP-Prüfung entfällt mangels App-Code).

- [ ] **Step 4: Merge**

Nach User-Freigabe:

```bash
gh pr merge --squash --delete-branch
```

Expected: PR gemerged, lokaler Branch automatisch bereinigt.

- [ ] **Step 5: `main` aktualisieren**

```bash
git checkout main
git pull
```

---

### Task 7: Deploy & Post-Deploy-Verifikation

**Files:** keine — Ops-Aktion

- [ ] **Step 1: Deploy**

Run: `fly deploy -a olivalle`
Expected: Build + Deploy erfolgreich, neue Machine gestartet, alte beendet.

- [ ] **Step 2: Machine-Status prüfen**

Run: `fly status -a olivalle`
Expected: Genau 1 Machine im State `started`, Health-Checks grün.

- [ ] **Step 3: Heartbeat-Loop läuft**

Run: `fly logs -a olivalle --no-tail | grep -i 'heartbeat\|litestream' | tail -20`
Expected: Mindestens ein `litestream:`- oder Heartbeat-Log-Eintrag innerhalb der letzten 10 Min.

- [ ] **Step 4: Healthchecks.io-Dashboard prüfen**

Öffne https://healthchecks.io → Check "olivalle-litestream-heartbeat"
Expected: Status grün, letzter Ping < 10 Min alt.

- [ ] **Step 5: 1 Stunde später nochmal**

Nach ~60 Min:

Run: `fly status -a olivalle`
Expected: Machine weiterhin `started` (wurde nicht zwischendurch gestoppt).

- [ ] **Step 6: Kosten-Blick**

fly Dashboard → Billing → aktueller Verbrauch
Expected: Hochrechnung liegt im erwarteten Korridor (~$2/Mt).

---

### Task 8: 7-Tage-Beobachtung

**Files:** keine — manuelle Überwachung, kein Code-Change in dieser Zeit

- [ ] **Step 1: Erinnerung setzen**

Kalender-/Reminder-Eintrag für 2026-04-29 (genau 7 Tage nach Deploy): *"Issue #116 schliessen — Heartbeat-Tuning verifizieren"*

- [ ] **Step 2: Tägliches Mini-Check (2 Min)**

Einmal pro Tag im Posteingang prüfen:
- Kam ein Healthchecks.io-Alert-Mail? → **NEIN erwartet**
- Falls ja: sofort `fly status` + `fly logs` prüfen, Ursache analysieren, Issue **nicht** schliessen.

Ohne Auffälligkeit: weiter nichts tun.

---

### Task 9: Memory-Update & Issue schliessen (nach 7 Tagen)

**Files:**
- Modify: `/Users/KN/.claude/projects/-Users-KN-Dropbox-Privat-CAS-projekte-olivalle/memory/project_backup_setup.md`

- [ ] **Step 1: Memory-Datei öffnen**

Lese Inhalt, identifiziere die Zeile: *"Heartbeat-Alerts können in ruhigen Phasen falsch sein (Machine bei fly Auto-Stop = kein Heartbeat) → siehe Folge-Issue #116"*

- [ ] **Step 2: Memory aktualisieren**

Ersetze diese Zeile durch:

```markdown
- Seit 2026-04-22 läuft die fly-Machine via `min_machines_running = 1` durchgängig (Issue #116, PR <PR-Nr>). Heartbeat-Alerts sind ab jetzt ernst zu nehmen — keine Toleranz mehr durch Machine-Stop. Verifikation: 7 Tage ohne false-positives bestanden am 2026-04-29.
```

Falls das Feld `description` im Frontmatter veraltet ist (erwähnt `#116 offen`), entsprechend aktualisieren.

- [ ] **Step 3: Issue schliessen**

```bash
gh issue close 116 --comment "Verifiziert: 7 Tage Normalbetrieb ab 2026-04-22 ohne false-positive Alerts. Machine via min_machines_running=1 durchgängig, Heartbeat-Loop pingt kontinuierlich. Doku in ADR-Nachtrag + Runbook + CLAUDE.md aktualisiert."
```

- [ ] **Step 4: Abschluss-Hygiene (siehe CLAUDE.md "Beim Pausieren")**

- GitHub Issues: andere offene Issues prüfen — wird durch #116-Schluss etwas unblocked?
- README / Docs: konsistent?
- Nächste sinnvolle Session vorschlagen.

---

## Self-Review

**Spec coverage:**
- Spec-Abschnitt "Zweck" → abgedeckt durch Task 1 (fly.toml-Änderung).
- Spec "Änderungen im Detail" 1–5 → Tasks 1, 2, 3, 4 + Task 9 (Memory).
- Spec "Verifikation & Akzeptanzkriterien" → Task 7 (Post-Deploy) + Task 8 (7 Tage) + Task 9 (Schluss).
- Spec "Rollback" → implizit in Task 1 (reversibel via gleichem Mechanismus); optional explizit im PR-Body.
- Spec "Deliverables" → Task 5 (PR), Task 6 (Merge), Task 9 (Memory, Issue-Schluss).
- Spec "Risiken" → mitigationen in den jeweiligen Tasks (fly config validate, `fly status`-Check, Beobachtung).

**Placeholder scan:** keine TBD/TODO-Einträge, alle Commands konkret.

**Type consistency:** Keine Types involviert — nur Textdateien und CLI-Kommandos. Commit-Messages konsistent mit `feat:`/`docs:`-Präfixen aus Projekt-Convention.

**Known deviations from default template:**
- Keine Unit-Tests, keine TDD-Zyklen — bewusste Spec-Entscheidung ("pure Config-Änderung"). Validierung via `fly config validate` + Post-Deploy-Checks + 7-Tage-Beobachtung.
- Tasks 8 und 9 sind zeitlich entkoppelt (7 Tage später) und werden bewusst in separater Session gemacht.
