#!/usr/bin/env bash
set -euo pipefail

# =========================
# snr_agg_ap_sm.sh
# Registra SNR agregado DL/UL (y MCS/RSSI/Rate) desde:
#   - AP: "show sta" (vista AP del SM)
#   - SM: intenta "show ap", "show dashboard", "show wireless" (vista SM del AP)
# Escribe 2 filas por timestamp: role=AP y role=SM
# =========================

AP_IP="${AP_IP:-192.168.1.2}"
SM_IP="${SM_IP:-192.168.1.3}"
USER="${USER:-admin}"

LOG_DIR="${LOG_DIR:-/home/carlos/epmp_logs}"
CSV_FILE="${LOG_DIR}/epmp_snr_agg_$(date +%F).csv"
REJECT_FILE="${LOG_DIR}/epmp_snr_agg_reject_$(date +%F).csv"

PASS_FILE="${PASS_FILE:-${LOG_DIR}/.ap_pass}"   # si usas password (sshpass)
SSH_TIMEOUT="${SSH_TIMEOUT:-5}"

SSH_OPTS=(
  -o StrictHostKeyChecking=no
  -o UserKnownHostsFile=/dev/null
  -o ConnectTimeout="${SSH_TIMEOUT}"
  -o ServerAliveInterval=5
  -o ServerAliveCountMax=1
)

ts_now() { date --iso-8601=seconds; }

init_files() {
  mkdir -p "$LOG_DIR"
  if [[ ! -s "$CSV_FILE" ]]; then
    echo "ts,role,ip,sta_peer_ip,dl_mcs,ul_mcs,dl_snr_db,ul_snr_db,dl_rssi_dbm,ul_rssi_dbm,dl_rate,note" >> "$CSV_FILE"
  fi
  if [[ ! -s "$REJECT_FILE" ]]; then
    echo "ts,role,ip,reason,raw" >> "$REJECT_FILE"
  fi
}

ssh_run() {
  local ip="$1"; shift
  local cmd="$*"
  if command -v sshpass >/dev/null 2>&1 && [[ -f "$PASS_FILE" ]]; then
    sshpass -f "$PASS_FILE" ssh "${SSH_OPTS[@]}" "${USER}@${ip}" "$cmd"
  else
    ssh "${SSH_OPTS[@]}" "${USER}@${ip}" "$cmd"
  fi
}

# -------------------------
# Parse AP side (show sta)
# -------------------------
parse_ap_show_sta() {
  awk '
    BEGIN{
      peer=""; dlmcs=""; ulmcs=""; dlsnr=""; ulsnr="";
      dlrssi=""; ulrssi=""; dlrate="";
      in_block=0
    }
    /^\s*\[[0-9]+\]\s*$/ { in_block=1; next }
    in_block==0 { next }
    {
      if ($1=="connectedSTAIP") peer=$2
      else if ($1=="connectedSTADLMCS") dlmcs=$2
      else if ($1=="connectedSTAULMCS") ulmcs=$2
      else if ($1=="connectedSTADLSNR") dlsnr=$2
      else if ($1=="connectedSTAULSNR") ulsnr=$2
      else if ($1=="connectedSTADLRSSI") dlrssi=$2
      else if ($1=="connectedSTAULRSSI") ulrssi=$2
      else if ($1=="connectedSTADLRateMbps") dlrate=$2
    }
    END{
      # imprime: peer, dlmcs, ulmcs, dlsnr, ulsnr, dlrssi, ulrssi, dlrate
      if (peer!="") printf "%s,%s,%s,%s,%s,%s,%s,%s\n", peer, dlmcs, ulmcs, dlsnr, ulsnr, dlrssi, ulrssi, dlrate
    }
  '
}

# -------------------------------------------------
# Parse genérico SM (busca patrones DL/UL SNR/MCS)
# Intenta extraer de "show ap" primero.
# -------------------------------------------------
parse_sm_generic() {
  awk '
    BEGIN{
      peer=""; dlmcs=""; ulmcs=""; dlsnr=""; ulsnr="";
      dlrssi=""; ulrssi=""; dlrate="";
    }
    {
      line=$0

      # IP del peer (AP) si aparece en forma simple
      if (peer=="" && line ~ /(AP|ap).*IP|IPAddress|ip/i) {
        # heurística: toma último token que parezca IP
        for(i=1;i<=NF;i++) if ($i ~ /^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$/) peer=$i
      }

      # patrones típicos; ajusta si tu "show ap" muestra nombres distintos
      if (dlmcs=="" && line ~ /DLMCS|DL MCS|dl.*mcs/i) dlmcs=$NF
      if (ulmcs=="" && line ~ /ULMCS|UL MCS|ul.*mcs/i) ulmcs=$NF

      if (dlsnr=="" && line ~ /DLSNR|DL SNR|dl.*snr/i) dlsnr=$NF
      if (ulsnr=="" && line ~ /ULSNR|UL SNR|ul.*snr/i) ulsnr=$NF

      if (dlrssi=="" && line ~ /DLRSSI|DL RSSI|dl.*rssi/i) dlrssi=$NF
      if (ulrssi=="" && line ~ /ULRSSI|UL RSSI|ul.*rssi/i) ulrssi=$NF

      if (dlrate=="" && line ~ /DLRate|DL Rate|dl.*rate/i) dlrate=$NF
    }
    END{
      # peer puede quedar vacío; no es crítico
      printf "%s,%s,%s,%s,%s,%s,%s,%s\n", peer, dlmcs, ulmcs, dlsnr, ulsnr, dlrssi, ulrssi, dlrate
    }
  '
}

clean_num_or_blank() {
  # deja solo enteros con signo, si no, vacío
  local v="${1:-}"
  if [[ "$v" =~ ^-?[0-9]+$ ]]; then
    echo "$v"
  else
    echo ""
  fi
}

main() {
  init_files
  local ts raw parsed peer dlmcs ulmcs dlsnr ulsnr dlrssi ulrssi dlrate

  ts="$(ts_now)"

  # ---------- AP row ----------
  if raw="$(ssh_run "$AP_IP" "show sta" 2>&1)"; then
    parsed="$(echo "$raw" | parse_ap_show_sta || true)"
    if [[ -n "$parsed" ]]; then
      IFS=, read -r peer dlmcs ulmcs dlsnr ulsnr dlrssi ulrssi dlrate <<<"$parsed"
      dlsnr="$(clean_num_or_blank "$dlsnr")"
      ulsnr="$(clean_num_or_blank "$ulsnr")"
      dlrssi="$(clean_num_or_blank "$dlrssi")"
      ulrssi="$(clean_num_or_blank "$ulrssi")"
      echo "${ts},AP,${AP_IP},${peer},${dlmcs},${ulmcs},${dlsnr},${ulsnr},${dlrssi},${ulrssi},${dlrate}," >> "$CSV_FILE"
    else
      echo "${ts},AP,${AP_IP},parse_fail,$(echo "$raw" | tr '\n' ' ' | sed 's/,/;/g')" >> "$REJECT_FILE"
    fi
  else
    echo "${ts},AP,${AP_IP},ssh_fail,$(echo "$raw" | tr '\n' ' ' | sed 's/,/;/g')" >> "$REJECT_FILE"
  fi

  # ---------- SM row ----------
  # Intentamos en orden (lo más común): show ap -> show dashboard -> show wireless
  raw=""
  if raw="$(ssh_run "$SM_IP" "show ap" 2>&1)"; then
    :
  elif raw2="$(ssh_run "$SM_IP" "show dashboard" 2>&1)"; then
    raw="$raw2"
  elif raw3="$(ssh_run "$SM_IP" "show wireless" 2>&1)"; then
    raw="$raw3"
  else
    echo "${ts},SM,${SM_IP},ssh_fail,$(echo "$raw" | tr '\n' ' ' | sed 's/,/;/g')" >> "$REJECT_FILE"
    exit 0
  fi

  parsed="$(echo "$raw" | parse_sm_generic || true)"
  IFS=, read -r peer dlmcs ulmcs dlsnr ulsnr dlrssi ulrssi dlrate <<<"$parsed"

  dlsnr="$(clean_num_or_blank "$dlsnr")"
  ulsnr="$(clean_num_or_blank "$ulsnr")"
  dlrssi="$(clean_num_or_blank "$dlrssi")"
  ulrssi="$(clean_num_or_blank "$ulrssi")"

  # Nota si no encontró SNR (para que no te engañe el CSV)
  note=""
  if [[ -z "$dlsnr" && -z "$ulsnr" ]]; then
    note="no_snr_found_in_sm_cli"
  fi

  echo "${ts},SM,${SM_IP},${peer},${dlmcs},${ulmcs},${dlsnr},${ulsnr},${dlrssi},${ulrssi},${dlrate},${note}" >> "$CSV_FILE"
}

main "$@"
