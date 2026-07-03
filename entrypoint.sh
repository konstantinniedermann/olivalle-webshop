#!/bin/sh
# entrypoint.sh
# Startet Litestream (PID 1) + uvicorn. Restored bei leerem Volume automatisch.
# Backup-Monitoring läuft extern via GitHub Action (siehe
# .github/workflows/backup-check.yml, Issue #118).
set -eu

DB_PATH="${DATABASE_PATH:-/data/olivalle.db}"

# 1) Fail-Fast: Produktionskonfiguration pruefen (bricht bei fehlenden
#    Pflicht-Secrets ab, statt mit unsicheren Defaults zu starten).
#    Bewusst VOR dem Restore: bei Fehlkonfiguration soll der Container
#    sofort abbrechen, ohne den Backup-Pfad anzufassen.
python -m app.config

# 2) Auto-Restore bei leerem Volume
if [ ! -f "$DB_PATH" ]; then
  echo "[entrypoint] Keine DB gefunden — versuche Restore aus Tigris…"
  # -if-replica-exists deckt das Erstdeployment ab: existiert keine Replica,
  # endet Litestream mit Exit 0 und init_db() legt unten eine frische DB an.
  # Bei ECHTEN Fehlern (Tigris nicht erreichbar, Credentials falsch) liefert
  # Litestream dagegen Exit != 0 — dann bricht set -e den Start ab (Fail-Fast).
  # Kein ||-Fallback: der wuerde jeden Fehler maskieren, eine leere DB anlegen
  # und via litestream replicate eine neue Backup-Generation der leeren DB
  # starten — das echte Backup ginge nach Ablauf der Retention verloren (#165).
  litestream restore -if-replica-exists -config /etc/litestream.yml "$DB_PATH"
fi

# 3) Migrationen (idempotent, auf Volume)
python -c 'from app.database import init_db; init_db()'

# 4) Litestream als PID 1, uvicorn als ueberwachter Subprocess
exec litestream replicate -config /etc/litestream.yml -exec \
  "uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=*"
