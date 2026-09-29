#!/usr/bin/env bash
set -u

# ====== CONFIG ======
LOG_DIR="/home/carlos/epmp_logs"
AP_IP="192.168.1.2"
SM_IP="192.168.1.3"
PASSFILE="${LOG_DIR}/.ap_pass"   # contraseña SSH del admin del AP (una sola línea)

CSV_FILE="${LOG_DIR}/epmp_agg_$(date +%F).csv"
REJECT_FILE="${LOG_DIR}/epmp_agg_reject_$(date +%F).csv"

SSH_USER="admin"
SSH_OPTS=(
  -o StrictHostKeyChecking=no
  -o UserKnownHostsFile=/dev/null
  -o ConnectTimeout=5
  -o ServerAliveInterval=5
  -o ServerAliveCountMax=1
)

# Timestamp limpio (sin duplicar TZ)
TS="$(date '+%Y-%m-%dT%H:%M:%S%z')"

# ====== INIT CSV HEADERS ======
if [ ! -f "$CSV_FILE" ]; then
  echo "ts,role,ip,peer_ip,dl_mcs,ul_mcs,dl_snr_db,ul_snr_db,dl_rssi_dbm,ul_rssi_dbm,dl_rate,note" > "$CSV_FILE"
fi
if [ ! -f "$REJECT_FILE" ]; then
  echo "ts,role,ip,reason,raw_line" > "$REJECT_FILE"
fi

# ====== HELPERS ======
append_csv () {
  # Asegura 12 campos siempre
  local line="$1"
  awk -F, -v L="$line" 'BEGIN{
    n=split(L,a,",");
    for(i=n+1;i<=12;i++) a[i]="";
    out=a[1];
    for(i=2;i<=12;i++) out=out","a[i];
    print out
  }' >> "$CSV_FILE"
}

reject () {
  local role="$1" ip="$2" reason="$3" raw="$4"
  # Limpia saltos de línea para que no rompa el CSV de rejects
  raw="${raw//$'\n'/ }"
  echo "${TS},${role},${ip},${reason},${raw}" >> "$REJECT_FILE"
}

run_ssh_show_sta () {
  # Devuelve stdout del "show sta" del AP.
  # Requiere sshpass si cron no puede interactuar.
  if command -v sshpass >/dev/null 2>&1; then
    if [ -r "$PASSFILE" ]; then
      sshpass -f "$PASSFILE" ssh "${SSH_OPTS[@]}" "${SSH_USER}@${AP_IP}" "show sta" 2>&1
      return $?
    else
      echo "PASSFILE_NOT_READABLE"
      return 90
    fi
  else
    echo "SSHPASS_NOT_INSTALLED"
    return 91
  fi
}

# ====== 1) FILA AP: sacar métricas agregadas desde AP (show sta) ======
OUT="$(run_ssh_show_sta)"
RC=$?

dl_mcs=""; ul_mcs=""; dl_snr=""; ul_snr=""; dl_rssi=""; ul_rssi=""; dl_rate=""; peer_ip="$SM_IP"; note=""

if [ $RC -ne 0 ]; then
  note="ssh_fail_rc_${RC}"
  reject "AP" "$AP_IP" "ssh_fail" "$OUT"
else
  # Detectar bloqueos/credenciales
  echo "$OUT" | grep -qi "Login is blocked" && { note="ssh_auth_or_blocked"; reject "AP" "$AP_IP" "auth_blocked" "$OUT"; }
  echo "$OUT" | grep -qi "Permission denied" && { note="ssh_auth_or_blocked"; reject "AP" "$AP_IP" "permission_denied" "$OUT"; }

  # Parsear campos (solo si existe contenido esperado)
  if [ -z "$note" ]; then
    # Si no hay ninguna línea connectedSTA, no hay datos (o salida rara)
    if ! echo "$OUT" | grep -q "connectedSTA"; then
      note="no_connectedSTA_lines"
      reject "AP" "$AP_IP" "no_connectedSTA_lines" "$OUT"
    else
      peer_ip="$(echo "$OUT" | awk '/connectedSTAIP[[:space:]]/{print $2; exit}')"
      dl_mcs="$(echo "$OUT" | awk '/connectedSTADLMCS[[:space:]]/{print $2; exit}')"
      ul_mcs="$(echo "$OUT" | awk '/connectedSTAULMCS[[:space:]]/{print $2; exit}')"
      dl_snr="$(echo "$OUT" | awk '/connectedSTADLSNR[[:space:]]/{print $2; exit}')"
      ul_snr="$(echo "$OUT" | awk '/connectedSTAULSNR[[:space:]]/{print $2; exit}')"
      dl_rssi="$(echo "$OUT" | awk '/connectedSTADLRSSI[[:space:]]/{print $2; exit}')"
      ul_rssi="$(echo "$OUT" | awk '/connectedSTAULRSSI[[:space:]]/{print $2; exit}')"
      dl_rate="$(echo "$OUT" | awk '/connectedSTADLRateMbps[[:space:]]/{print $2; exit}')"

      # Si faltan campos críticos, marcar nota
      if [ -z "$dl_snr" ] || [ -z "$ul_snr" ] || [ -z "$dl_mcs" ] || [ -z "$ul_mcs" ]; then
        note="ap_parse_incomplete"
        reject "AP" "$AP_IP" "ap_parse_incomplete" "$OUT"
      fi
      # Si peer_ip no salió, deja SM_IP
      [ -z "$peer_ip" ] && peer_ip="$SM_IP"
    fi
  fi
fi

append_csv "${TS},AP,${AP_IP},${peer_ip},${dl_mcs},${ul_mcs},${dl_snr},${ul_snr},${dl_rssi},${ul_rssi},${dl_rate},${note}"

# ====== 2) FILA SM: tu SM no expone esos campos por CLI (según tu evidencia). ======
append_csv "${TS},SM,${SM_IP},${AP_IP},,,,,,,,sm_cli_no_snr_fields"
