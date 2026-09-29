#!/usr/bin/env bash
set -euo pipefail
SECRETS_FILE="${EPMP_TELEGRAM_SECRETS_FILE:-/home/carlos/.config/atmoslink/epmp_telegram.env}"
if [[ ! -r "$SECRETS_FILE" ]]; then
  echo "ERROR: no se puede leer $SECRETS_FILE" >&2
  exit 1
fi
set -a
source "$SECRETS_FILE"
set +a
exec /home/carlos/epmp_monitor/venv/bin/python /home/carlos/epmp_monitor/bin/alertas_automaticas.py "$@"
