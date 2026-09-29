#!/usr/bin/env bash
set -euo pipefail

if ! pgrep -af "bash $HOME/epmp_logs/poll_epmp.sh" >/dev/null 2>&1; then
  nohup env INTERVAL=60 RSSI_EVERY=5 RETRIES=3 COOLDOWN=6 \
    "$HOME/epmp_logs/poll_epmp.sh" >> "$HOME/epmp_logs/poll_debug.log" 2>&1 &
fi
