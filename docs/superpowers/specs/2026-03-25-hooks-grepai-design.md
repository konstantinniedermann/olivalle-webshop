# Design Spec: Claude Code Hooks + grepai Auto-Start

**Datum:** 2026-03-25
**Issue:** #34 (Claude Code Hooks konfigurieren) + ALL-HOOKS
**Status:** Approved

---

## Kontext

Das Projekt nutzt:
- **FastAPI + Python** — Linting via Ruff (ruff check / ruff format)
- **grepai** — semantische Codesuche via MCP, benötigt laufenden `watch`-Daemon
- **Claude Code superpowers** — bereits aktiv via `enabledPlugins`, SessionStart-Hook läuft automatisch

Ist-Zustand:
- `settings.json` (global): keine Hooks konfiguriert
- `grepai watch` läuft aktuell als Foreground-Prozess, startet nach Reboot nicht automatisch
- `grepai mcp-serve` wird von Claude Code automatisch gestartet — kein Handlungsbedarf

---

## Ziele

1. Ruff automatisch nach jedem Python-Edit ausführen (blockierend, global)
2. grepai watch beim Login automatisch für alle CAS-Projekte starten
3. Neue Projekte brauchen keine Konfigurationsänderung — nur `grepai init` ausführen

---

## Nicht im Scope

- Superpowers SessionStart-Hook: bereits aktiv via Plugin-System, kein Handlungsbedarf
- Stop-Hook für Memory: auto-memory System ist instructions-basiert, funktioniert bereits
- grepai mcp-serve: wird von Claude Code selbst verwaltet
- Hookify-Plugin: Overkill für diesen Anwendungsfall

---

## Design

### 1. Ruff-Hook (`~/.claude/hooks/ruff-check.sh`)

Shell-Script das von Claude Code nach jedem `Edit`- oder `Write`-Tool-Call ausgeführt wird.

**Input-Mechanismus:** Claude Code übergibt Hook-Daten via **stdin als JSON** (nicht als Env-Variable). Der Dateipfad liegt unter `.tool_input.file_path`. Das Script liest stdin mit `python3` (garantiert verfügbar im Python-Projekt):

```bash
FILE_PATH=$(python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))")
```

**Verhalten:**
- Liest den Dateipfad aus dem stdin-JSON via python3
- Bricht ab wenn die Datei keine `.py`-Endung hat (Exit 0, kein Fehler)
- Wechselt ins Verzeichnis der Datei und führt `ruff check --fix` aus
- Bricht graceful ab wenn `ruff` nicht gefunden wird (Exit 0 — kein Fehler für Projekte ohne Ruff)
- Output geht an Claude Code (blockierend, `async: false`)

**Pfad zu uv:** `uv` liegt bei `~/.local/bin/uv` und ist nicht im konfigurierten Claude Code PATH (`/opt/homebrew/bin:...`). Das Script verwendet den expliziten Pfad: `~/.local/bin/uv run ruff check --fix "$FILE_PATH"`.

**Warum uv run:** Ruff ist als Dev-Dependency im Projekt via uv installiert — kein globales Ruff nötig.

### 2. PostToolUse-Hook in `~/.claude/settings.json`

```json
"hooks": {
  "PostToolUse": [
    {
      "matcher": "Edit|Write",
      "hooks": [
        {
          "type": "command",
          "command": "bash /Users/KN/.claude/hooks/ruff-check.sh",
          "async": false
        }
      ]
    }
  ]
}
```

**Hinweis Pfad:** `~` wird in JSON-Command-Feldern nicht expandiert — absoluter Pfad verwenden.

Scope: global (gilt für alle Projekte). Nur Python-Dateien werden effektiv geprüft (Script-interne Filterung).

### 3. grepai Watch-Script (`~/.claude/hooks/grepai-watch-start.sh`)

Iteriert über alle Unterordner in `~/Dropbox/Privat/CAS/projekte/`:
- Ordner mit `.grepai`-Verzeichnis werden erkannt (`.grepai` existiert in jedem via `grepai init` initialisierten Projektordner)
- Script wechselt per `cd "$dir"` ins Projektverzeichnis bevor `grepai watch --background` aufgerufen wird — jede Instanz überwacht nur ihr eigenes Verzeichnis
- Mehrere parallele Background-Watcher werden von grepai unterstützt (je Worktree-ID)
- Neue Projekte: `grepai init` ausführen → beim nächsten Login automatisch dabei

### 4. launchd-Plist (`~/Library/LaunchAgents/com.grepai.watch.plist`)

- `RunAtLoad: true` — startet beim Login
- Ruft `grepai-watch-start.sh` auf
- Da `grepai watch --background` sich selbst als Daemon verwaltet, startet launchd einmalig

---

## Dateien

| Pfad | Typ | Zweck |
|------|-----|-------|
| `~/.claude/hooks/ruff-check.sh` | Shell-Script | Ruff nach Python-Edit |
| `~/.claude/hooks/grepai-watch-start.sh` | Shell-Script | grepai watch für alle Projekte |
| `~/.claude/settings.json` | JSON (erweitern) | PostToolUse-Hook registrieren |
| `~/Library/LaunchAgents/com.grepai.watch.plist` | XML-Plist | Auto-Start beim Login |

---

## Erweiterbarkeit

- Neues Projekt in `~/Dropbox/Privat/CAS/projekte/`: `grepai init` ausführen → automatisch beim nächsten Login dabei
- Ruff-Hook gilt bereits global für alle `.py`-Dateien in allen Projekten
- Kein Änderungsbedarf an bestehenden Konfigurationsdateien

---

## Nicht behandelte Risiken

- `uv` wird via explizitem Pfad `~/.local/bin/uv` aufgerufen (nicht im Claude Code PATH)
- Wenn ein Projekt kein uv/Ruff hat: Script exitiert graceful (Exit 0) — kein Fehler für den User
- Reviewer-Note: `.grepai` existiert korrekt in den Projektordnern (verifiziert) — kein Problem
