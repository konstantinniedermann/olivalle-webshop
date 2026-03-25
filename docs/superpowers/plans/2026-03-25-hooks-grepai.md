# Claude Code Hooks + grepai Auto-Start — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ruff automatisch nach jedem Python-Edit ausführen und grepai watch beim Login für alle CAS-Projekte starten.

**Architecture:** Zwei Shell-Scripts in `~/.claude/hooks/` plus ein launchd-Plist. Der Ruff-Hook wird in `~/.claude/settings.json` als globaler PostToolUse-Hook registriert. Das grepai-Script iteriert über alle Projektordner mit `.grepai` — neue Projekte brauchen nur `grepai init`, keine Konfigurationsänderung.

**Tech Stack:** bash, python3 (stdin JSON-Parsing), uv (`/Users/KN/.local/bin/uv`), grepai (`/opt/homebrew/bin/grepai`), macOS launchd

---

## Dateien

| Datei | Aktion | Zweck |
|-------|--------|-------|
| `~/.claude/hooks/ruff-check.sh` | Erstellen | Ruff nach Python-Edit |
| `~/.claude/hooks/grepai-watch-start.sh` | Erstellen | grepai watch für alle CAS-Projekte |
| `~/.claude/settings.json` | Erweitern | PostToolUse-Hook registrieren |
| `~/Library/LaunchAgents/com.grepai.watch.plist` | Erstellen | grepai auto-start beim Login |

> **Hinweis:** Alle Dateien ausser `settings.json` liegen ausserhalb des Projekt-Repos. Kein Git-Commit nötig — Ausnahme: `settings.json` ist ggf. zu sensibel für den Repo.

---

## Task 1: Ruff-Hook Script erstellen

**Files:**
- Create: `/Users/KN/.claude/hooks/ruff-check.sh`

- [ ] **Schritt 1: Hooks-Verzeichnis sicherstellen**

```bash
mkdir -p /Users/KN/.claude/hooks
```

- [ ] **Schritt 2: Script erstellen**

Datei `/Users/KN/.claude/hooks/ruff-check.sh`:

```bash
#!/usr/bin/env bash
# PostToolUse-Hook: Ruff nach Python-Edit ausführen
# Input: JSON via stdin (Claude Code Hook-Mechanismus)

set -euo pipefail

# Dateipfad aus stdin-JSON lesen
FILE_PATH=$(python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('tool_input', {}).get('file_path', ''))
" 2>/dev/null || echo "")

# Nur Python-Dateien prüfen
[[ "$FILE_PATH" == *.py ]] || exit 0

# Graceful exit wenn Datei nicht existiert
[[ -f "$FILE_PATH" ]] || exit 0

# uv und ruff prüfen
UV="/Users/KN/.local/bin/uv"
[[ -x "$UV" ]] || exit 0

# In Projektverzeichnis wechseln
cd "$(dirname "$FILE_PATH")"

# Ruff ausführen
"$UV" run ruff check --fix "$FILE_PATH" 2>&1 || true
```

- [ ] **Schritt 3: Ausführbar machen**

```bash
chmod +x /Users/KN/.claude/hooks/ruff-check.sh
```

- [ ] **Schritt 4: Script manuell testen**

Temporäre Python-Datei mit Ruff-Fehler erstellen und Script direkt testen:

```bash
cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle

# Test-Input als JSON (wie Claude Code es schicken würde)
echo '{"tool_input": {"file_path": "/tmp/test_ruff.py"}}' > /tmp/test_hook_input.json

# Test-Datei mit absichtlichem Ruff-Fehler
echo 'x=1' > /tmp/test_ruff.py

bash /Users/KN/.claude/hooks/ruff-check.sh < /tmp/test_hook_input.json
```

Erwartetes Ergebnis: Ruff-Output (`Found 1 error. Fixed 1 error.`) oder kein Fehler

- [ ] **Schritt 5: Test mit Nicht-Python-Datei (soll nichts tun)**

```bash
echo '{"tool_input": {"file_path": "/tmp/test.txt"}}' | \
  bash /Users/KN/.claude/hooks/ruff-check.sh
echo "Exit code: $?"
```

Erwartetes Ergebnis: Exit 0, kein Output

---

## Task 2: PostToolUse-Hook in settings.json registrieren

**Files:**
- Modify: `/Users/KN/.claude/settings.json`

- [ ] **Schritt 1: Aktuellen Inhalt prüfen**

```bash
cat /Users/KN/.claude/settings.json
```

- [ ] **Schritt 2: `hooks`-Sektion ergänzen**

Die bestehende `settings.json` um einen `hooks`-Block erweitern. Ergebnis:

```json
{
  "env": {
    "PATH": "/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
  },
  "permissions": {
    "allow": [
      "Bash(gh label:*)",
      "Bash(git merge:*)"
    ]
  },
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
  },
  "enabledPlugins": {
    "context7@claude-plugins-official": true,
    "superpowers@claude-plugins-official": true,
    "project-management@talent-factory": true
  },
  "extraKnownMarketplaces": {
    "talent-factory": {
      "source": {
        "source": "git",
        "url": "https://github.com/talent-factory/claude-plugins.git"
      }
    }
  }
}
```

> **Wichtig:** Nur den `hooks`-Block in die bestehende `settings.json` einfügen — nicht die ganze Datei ersetzen. Bestehende `permissions.allow`- und `enabledPlugins`-Einträge beibehalten.

- [ ] **Schritt 3: JSON validieren**

```bash
python3 -c "import json; json.load(open('/Users/KN/.claude/settings.json')); print('JSON valid')"
```

Erwartetes Ergebnis: `JSON valid`

- [ ] **Schritt 4: Hook in Claude Code testen**

Eine bestehende Python-Datei minimal bearbeiten und speichern — Claude Code sollte den Ruff-Output im Terminal anzeigen:

```bash
# Beispiel: Datei berühren und in Claude Code via Edit-Tool speichern
# Ruff-Output erscheint danach im Hook-Feedback
```

---

## Task 3: grepai Watch-Script erstellen

**Files:**
- Create: `/Users/KN/.claude/hooks/grepai-watch-start.sh`

- [ ] **Schritt 1: Script erstellen**

Datei `/Users/KN/.claude/hooks/grepai-watch-start.sh`:

```bash
#!/usr/bin/env bash
# Startet grepai watch --background für alle CAS-Projekte mit .grepai-Index

PROJECTS_DIR="$HOME/Dropbox/Privat/CAS/projekte"
GREPAI="/opt/homebrew/bin/grepai"

[[ -x "$GREPAI" ]] || { echo "grepai nicht gefunden: $GREPAI"; exit 1; }
[[ -d "$PROJECTS_DIR" ]] || { echo "Projektordner nicht gefunden: $PROJECTS_DIR"; exit 1; }

for dir in "$PROJECTS_DIR"/*/; do
    [[ -d "${dir}.grepai" ]] || continue
    project_name=$(basename "$dir")
    echo "Starte grepai watch für: $project_name"
    (cd "$dir" && "$GREPAI" watch --background 2>/dev/null) || \
        echo "Warnung: grepai watch für $project_name fehlgeschlagen"
done

echo "grepai watch-start abgeschlossen."
```

- [ ] **Schritt 2: Ausführbar machen**

```bash
chmod +x /Users/KN/.claude/hooks/grepai-watch-start.sh
```

- [ ] **Schritt 3: Script testen**

```bash
bash /Users/KN/.claude/hooks/grepai-watch-start.sh
```

Erwartetes Ergebnis: Output für olivalle und Munica, kein Fehler

- [ ] **Schritt 4: grepai watch Status prüfen**

```bash
grepai watch --status
```

Erwartetes Ergebnis: `Status: running` (oder bereits laufend)

---

## Task 4: launchd-Plist erstellen und aktivieren

**Files:**
- Create: `/Users/KN/Library/LaunchAgents/com.grepai.watch.plist`

- [ ] **Schritt 1: Plist-Datei erstellen**

Datei `/Users/KN/Library/LaunchAgents/com.grepai.watch.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.grepai.watch</string>
    <key>RunAtLoad</key>
    <true/>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/KN/.claude/hooks/grepai-watch-start.sh</string>
    </array>
    <key>StandardOutPath</key>
    <string>/Users/KN/Library/Logs/grepai/launchd-watch.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/KN/Library/Logs/grepai/launchd-watch.log</string>
</dict>
</plist>
```

- [ ] **Schritt 2: Log-Verzeichnis sicherstellen**

```bash
mkdir -p /Users/KN/Library/Logs/grepai
```

- [ ] **Schritt 3: Plist laden (sofort aktivieren ohne Reboot)**

```bash
launchctl load /Users/KN/Library/LaunchAgents/com.grepai.watch.plist
```

- [ ] **Schritt 4: Aktivierung prüfen**

```bash
launchctl list | grep grepai
```

Erwartetes Ergebnis: Zeile mit `com.grepai.watch` und Exit-Code `0`

- [ ] **Schritt 5: Log prüfen**

```bash
cat /Users/KN/Library/Logs/grepai/launchd-watch.log
```

Erwartetes Ergebnis: Script-Output (`Starte grepai watch für: olivalle` etc.)

---

## Verifikation Gesamtsystem

- [ ] **Smoke Test: Ruff-Hook**

In Claude Code eine Python-Datei im olivalle-Projekt via Edit-Tool bearbeiten. Ruff-Output soll im Antwort-Kontext erscheinen.

- [ ] **Smoke Test: grepai**

```bash
grepai watch --status
pgrep -a grepai
```

Erwartetes Ergebnis: `grepai watch` läuft. `grepai mcp-serve` wird von Claude Code selbst gestartet (nicht Teil dieses Setups) — falls er läuft, ist das ein Bonus.

- [ ] **Neues Projekt testen (optional)**

```bash
mkdir /Users/KN/Dropbox/Privat/CAS/projekte/test-projekt
cd /Users/KN/Dropbox/Privat/CAS/projekte/test-projekt
grepai init
bash /Users/KN/.claude/hooks/grepai-watch-start.sh
# → sollte auch test-projekt watchen
rm -rf /Users/KN/Dropbox/Privat/CAS/projekte/test-projekt
```
