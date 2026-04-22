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
