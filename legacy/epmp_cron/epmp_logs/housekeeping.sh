#!/usr/bin/env bash
set -euo pipefail

BASE="$HOME/epmp_logs"

# 1) Comprimir CSV y ssh_err de días anteriores (no el de hoy)
find "$BASE" -maxdepth 1 -type f -name 'epmp_local_*.csv' ! -name "epmp_local_$(date +%F).csv" -size +0c -exec gzip -f {} \; || true
find "$BASE" -maxdepth 1 -type f -name 'ssh_err_*.log'   ! -name "ssh_err_$(date +%F).log"   -size +0c -exec gzip -f {} \; || true

# 2) Retención: borrar comprimidos de más de 95 días
find "$BASE" -maxdepth 1 -type f \( -name 'epmp_local_*.csv.gz' -o -name 'ssh_err_*.log.gz' \) -mtime +95 -delete || true

# 3) Limitar tamaño de poll_debug.log (dejar últimos 5 MB)
DBG="$BASE/poll_debug.log"
if [[ -f "$DBG" ]]; then
  size=$(stat -c %s "$DBG" || echo 0)
  if (( size > 5*1024*1024 )); then
    tail -c $((5*1024*1024)) "$DBG" > "$DBG.tmp" && mv "$DBG.tmp" "$DBG"
  fi
fi
