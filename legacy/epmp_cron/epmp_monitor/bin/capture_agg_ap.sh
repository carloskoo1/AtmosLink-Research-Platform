#!/usr/bin/env bash
set -u
set -o pipefail

source /home/carlos/epmp_monitor/config/epmp.conf

PROJECT_DIR="/home/carlos/Proyectos/EstacionMeteorologica"
PYTHON="$PROJECT_DIR/venv/bin/python"
DATABASE="$PROJECT_DIR/SQLite/CU01/weather_local.db"

if [[ ! -r "$PASS_FILE" ]]; then
    echo "ERROR: no se puede leer $PASS_FILE" >&2
    exit 1
fi

PASSWORD="$(<"$PASS_FILE")"

mkdir -p "$DATA_DIR" "$LOG_DIR"

extract_value() {
    local text="$1"
    local key="$2"

    awk -v wanted="$key" '
        $1 == wanted {
            print $2
            exit
        }
    ' <<<"$text" |
    tr -d '\r' |
    xargs 2>/dev/null || true
}

numeric_rate() {
    local value="${1:-}"

    value="$(
      printf '%s' "$value" |
      tr -d '\r' |
      sed -E 's/[[:space:]]+//g; s/[Mm]$//'
    )"

    if [[ "$value" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
        printf '%s' "$value"
    fi
}

valid_integer() {
    [[ "${1:-}" =~ ^-?[0-9]+$ ]]
}

while true; do
    TS_LOCAL="$(date --iso-8601=seconds)"
    TODAY="$(date +%F)"

    CSV_FILE="$DATA_DIR/agg_ap_${TODAY}.csv"
    RAW_FILE="$LOG_DIR/raw_show_sta_${TODAY}.log"
    ERR_FILE="$LOG_DIR/agg_ap_${TODAY}.err.log"

    if [[ ! -f "$CSV_FILE" ]]; then
        echo \
"ts,role,ip,peer_ip,dl_mcs,ul_mcs,dl_snr_db,ul_snr_db,dl_rssi_dbm,ul_rssi_dbm,dl_rate_mbps,note" \
        >"$CSV_FILE"
    fi

    RAW="$(
      sshpass -p "$PASSWORD" \
      ssh \
      $SSH_OPTS \
      "${RADIO_USER}@${AP_IP}" \
      "show sta" \
      2>>"$ERR_FILE" || true
    )"

    {
        echo "===== $TS_LOCAL ====="
        echo "$RAW"
        echo
    } >>"$RAW_FILE"

    PEER_IP="$(extract_value "$RAW" connectedSTAIP)"
    DL_MCS="$(extract_value "$RAW" connectedSTADLMCS)"
    UL_MCS="$(extract_value "$RAW" connectedSTAULMCS)"
    DL_SNR="$(extract_value "$RAW" connectedSTADLSNR)"
    UL_SNR="$(extract_value "$RAW" connectedSTAULSNR)"
    DL_RSSI="$(extract_value "$RAW" connectedSTADLRSSI)"
    UL_RSSI="$(extract_value "$RAW" connectedSTAULRSSI)"
    DL_RATE_RAW="$(
      extract_value "$RAW" connectedSTADLRateMbps
    )"
    DL_RATE="$(numeric_rate "$DL_RATE_RAW")"

    NOTE="ok"
    ERROR_TEXT=""

    if [[ -z "$PEER_IP" ]]; then
        NOTE="SM_NOT_ASSOCIATED"
        ERROR_TEXT="El AP no devolvió una estación asociada"
    elif [[ "$PEER_IP" != "$SM_IP" ]]; then
        NOTE="UNEXPECTED_SM"
        ERROR_TEXT="SM esperado $SM_IP; detectado $PEER_IP"
    elif ! valid_integer "$DL_RSSI" ||
         ! valid_integer "$UL_RSSI" ||
         ! valid_integer "$DL_SNR" ||
         ! valid_integer "$UL_SNR"; then
        NOTE="INCOMPLETE_TELEMETRY"
        ERROR_TEXT="Faltan RSSI o SNR válidos"
    elif (( DL_SNR < 15 || UL_SNR < 15 )); then
        NOTE="LOW_SNR"
    elif (( DL_RSSI < -85 || UL_RSSI < -85 )); then
        NOTE="LOW_RSSI"
    fi

    printf \
      '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
      "$TS_LOCAL" \
      "AP" \
      "$AP_IP" \
      "$PEER_IP" \
      "$DL_MCS" \
      "$UL_MCS" \
      "$DL_SNR" \
      "$UL_SNR" \
      "$DL_RSSI" \
      "$UL_RSSI" \
      "$DL_RATE" \
      "$NOTE" \
      >>"$CSV_FILE"

    "$PYTHON" - \
      "$DATABASE" \
      "$AP_IP" \
      "$SM_IP" \
      "$PEER_IP" \
      "$DL_MCS" \
      "$UL_MCS" \
      "$DL_SNR" \
      "$UL_SNR" \
      "$DL_RSSI" \
      "$UL_RSSI" \
      "$DL_RATE" \
      "$NOTE" \
      "$ERROR_TEXT" <<'PY'
import sqlite3
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

(
    _,
    database,
    ap_ip,
    sm_ip,
    peer_ip,
    dl_mcs,
    ul_mcs,
    dl_snr,
    ul_snr,
    dl_rssi,
    ul_rssi,
    dl_rate,
    note,
    error_text,
) = sys.argv

def number(value, cast=float):
    value = str(value).strip()

    if not value:
        return None

    try:
        return cast(value)
    except (TypeError, ValueError):
        return None

now_utc = datetime.now(timezone.utc)
now_local = now_utc.astimezone(
    ZoneInfo("America/Lima")
)

values = {
    "timestamp_utc": now_utc.isoformat(
        timespec="seconds"
    ),
    "timestamp_local": now_local.isoformat(
        timespec="seconds"
    ),
    "source": "epmp_ssh_show_sta_v2",
    "ap_ip": ap_ip,
    "sm_ip": sm_ip,
    "mcs_dl": number(dl_mcs, int),
    "mcs_ul": number(ul_mcs, int),
    "snr_dl": number(dl_snr),
    "snr_ul": number(ul_snr),
    "rssi_c0p": None,
    "rssi_c0e": None,
    "rssi_c1p": None,
    "rssi_c1e": None,
    "dl_rate": number(dl_rate),
    "ul_rate": None,
    "sta_dl_rssi": number(dl_rssi),
    "sta_ul_rssi": number(ul_rssi),
    "note": note,
    "error": error_text,
}

stations = [
    {
        "station_id": "CU01",
        "station_name": "Cerro Cuñacales",
        "radio_role": "AP",
        "local_role": "AP",
    },
    {
        "station_id": "SJ01",
        "station_name": "Cerro San José",
        "radio_role": "SM",
        "local_role": "SM",
    },
]

columns = [
    "timestamp_utc",
    "timestamp_local",
    "source",
    "ap_ip",
    "sm_ip",
    "mcs_dl",
    "mcs_ul",
    "snr_dl",
    "snr_ul",
    "rssi_c0p",
    "rssi_c0e",
    "rssi_c1p",
    "rssi_c1e",
    "dl_rate",
    "ul_rate",
    "sta_dl_rssi",
    "sta_ul_rssi",
    "note",
    "error",
    "station_id",
    "station_name",
    "radio_role",
    "local_role",
]

sql = f"""
    INSERT INTO radio_link_local (
        {", ".join(columns)}
    )
    VALUES (
        {", ".join("?" for _ in columns)}
    )
"""

connection = sqlite3.connect(
    database,
    timeout=20,
)

try:
    connection.execute(
        "PRAGMA busy_timeout = 20000"
    )

    for station in stations:
        row = {
            **values,
            **station,
        }

        connection.execute(
            sql,
            [row[column] for column in columns],
        )

    connection.commit()

finally:
    connection.close()

print(
    "RF_GUARDADO",
    values["timestamp_local"],
    peer_ip or "SIN_SM",
    note,
)
PY

    sleep "$INTERVAL_SECONDS"
done
