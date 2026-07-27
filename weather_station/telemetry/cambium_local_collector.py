import subprocess
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from weather_station.config.settings import load_config
from weather_station.config.station_manager import get_station_context

CONFIG = load_config()
STATION_CONTEXT = get_station_context()

STATION_ID = STATION_CONTEXT["station_id"]
STATION_NAME = STATION_CONTEXT["station_name"]
RADIO_ROLE = STATION_CONTEXT["radio_role"]
LOCAL_ROLE = STATION_CONTEXT["local_role"]

AP_IP = STATION_CONTEXT["ap_ip"]
SM_IP = STATION_CONTEXT["sm_ip"]
SSH_USER = CONFIG["radio_link"]["ssh_user"]
PASSFILE = CONFIG["radio_link"]["passfile"]
DB_FILE = CONFIG["database"]["sqlite"]

INTERVAL_SECONDS = CONFIG.get("radio_link", {}).get("interval_seconds", 60)
SSH_TIMEOUT = CONFIG.get("radio_link", {}).get("ssh_timeout_seconds", 15)


def now_times():
    return (
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
        datetime.now().astimezone().isoformat(timespec="seconds"),
    )


def to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def init_db():
    Path(DB_FILE).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS radio_link_local (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_utc TEXT NOT NULL,
            timestamp_local TEXT NOT NULL,
            station_id TEXT,
            station_name TEXT,
            radio_role TEXT,
            local_role TEXT,
            source TEXT,
            ap_ip TEXT,
            sm_ip TEXT,

            mcs_dl REAL,
            mcs_ul REAL,
            snr_dl REAL,
            snr_ul REAL,

            rssi_c0p REAL,
            rssi_c0e REAL,
            rssi_c1p REAL,
            rssi_c1e REAL,

            dl_rate REAL,
            ul_rate REAL,

            sta_dl_rssi REAL,
            sta_ul_rssi REAL,

            note TEXT,
            error TEXT
        )
    """)

    # Migración ligera para bases existentes
    existing_cols = [r[1] for r in cur.execute("PRAGMA table_info(radio_link_local)").fetchall()]
    for col, col_type in [
        ("station_id", "TEXT"),
        ("station_name", "TEXT"),
        ("radio_role", "TEXT"),
        ("local_role", "TEXT"),
    ]:
        if col not in existing_cols:
            cur.execute(f"ALTER TABLE radio_link_local ADD COLUMN {col} {col_type}")

    conn.commit()
    conn.close()


def save_status(note, error=""):
    timestamp_utc, timestamp_local = now_times()

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO radio_link_local (
            timestamp_utc,
            timestamp_local,
            station_id,
            station_name,
            radio_role,
            local_role,
            source,
            ap_ip,
            sm_ip,
            note,
            error
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp_utc,
        timestamp_local,
        STATION_ID,
        STATION_NAME,
        RADIO_ROLE,
        LOCAL_ROLE,
        "local_ssh",
        AP_IP,
        SM_IP,
        note,
        error[:300] if error else "",
    ))

    conn.commit()
    conn.close()

    print(f"RADIO STATUS: {timestamp_local} note={note} error={error}")


def run_ssh(cmd):
    command = [
        "sshpass", "-f", PASSFILE,
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", f"ConnectTimeout={SSH_TIMEOUT}",
        f"{SSH_USER}@{AP_IP}",
        cmd,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=SSH_TIMEOUT + 5
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return result.stdout


def value_after_key(text, key):
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[0] == key:
            return parts[1]
    return None


def value_after_colon(text, key):
    for line in text.splitlines():
        if key in line and ":" in line:
            return line.split(":", 1)[1].strip()
    return None


def classify_note(row):
    """
    Clasifica el estado operativo del radioenlace.

    SM_NOT_ASSOCIATED:
        El AP responde por SSH, pero no existen métricas de una estación
        suscriptora asociada.

    LINK_OPERATIONAL:
        Existen métricas RF válidas y no se detectan umbrales críticos.
    """

    link_fields = (
        "mcs_dl",
        "mcs_ul",
        "snr_dl",
        "snr_ul",
        "sta_dl_rssi",
        "sta_ul_rssi",
        "dl_rate",
        "ul_rate",
    )

    parsed_values = {
        key: to_float(row.get(key))
        for key in link_fields
    }

    if all(value is None for value in parsed_values.values()):
        return "SM_NOT_ASSOCIATED"

    snr_dl = parsed_values["snr_dl"]
    rssi_dl = parsed_values["sta_dl_rssi"]
    mcs_dl = parsed_values["mcs_dl"]
    dl_rate = parsed_values["dl_rate"]

    if snr_dl is not None and snr_dl < 15:
        return "LOW_SNR"

    if rssi_dl is not None and rssi_dl < -75:
        return "LOW_RSSI"

    if mcs_dl is not None and mcs_dl < 3:
        return "LOW_MCS"

    if dl_rate is not None and dl_rate < 20:
        return "LOW_RATE"

    return "LINK_OPERATIONAL"


def collect_once():
    show_sta = run_ssh("show sta")
    show_rssi = run_ssh("show rssi")

    row = {
        "mcs_dl": value_after_key(show_sta, "connectedSTADLMCS"),
        "mcs_ul": value_after_key(show_sta, "connectedSTAULMCS"),
        "snr_dl": value_after_key(show_sta, "connectedSTADLSNR"),
        "snr_ul": value_after_key(show_sta, "connectedSTAULSNR"),

        "dl_rate": value_after_key(show_sta, "connectedSTADLRateMbps"),
        "ul_rate": value_after_key(show_sta, "connectedSTAULRateMbps"),

        "sta_dl_rssi": value_after_key(show_sta, "connectedSTADLRSSI"),
        "sta_ul_rssi": value_after_key(show_sta, "connectedSTAULRSSI"),

        "rssi_c0p": value_after_colon(show_rssi, "chain 0 RSSI primary"),
        "rssi_c0e": value_after_colon(show_rssi, "chain 0 RSSI extension"),
        "rssi_c1p": value_after_colon(show_rssi, "chain 1 RSSI primary"),
        "rssi_c1e": value_after_colon(show_rssi, "chain 1 RSSI extension"),
    }

    note = classify_note(row)

    timestamp_utc, timestamp_local = now_times()

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO radio_link_local (
            timestamp_utc,
            timestamp_local,
            station_id,
            station_name,
            radio_role,
            local_role,
            source,
            ap_ip,
            sm_ip,

            mcs_dl,
            mcs_ul,
            snr_dl,
            snr_ul,

            rssi_c0p,
            rssi_c0e,
            rssi_c1p,
            rssi_c1e,

            dl_rate,
            ul_rate,

            sta_dl_rssi,
            sta_ul_rssi,

            note,
            error
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp_utc,
        timestamp_local,
        STATION_ID,
        STATION_NAME,
        RADIO_ROLE,
        LOCAL_ROLE,
        "local_ssh",
        AP_IP,
        SM_IP,

        to_float(row["mcs_dl"]),
        to_float(row["mcs_ul"]),
        to_float(row["snr_dl"]),
        to_float(row["snr_ul"]),

        to_float(row["rssi_c0p"]),
        to_float(row["rssi_c0e"]),
        to_float(row["rssi_c1p"]),
        to_float(row["rssi_c1e"]),

        to_float(row["dl_rate"]),
        to_float(row["ul_rate"]),

        to_float(row["sta_dl_rssi"]),
        to_float(row["sta_ul_rssi"]),

        note,
        "",
    ))

    conn.commit()
    conn.close()

    print(f"GUARDADO RADIO: {timestamp_local} note={note} row={row}")


def run_daemon():
    init_db()

    print("AtmosLink RadioLink Collector iniciado")
    print(f"Config: {CONFIG.get('_config_file', 'unknown')}")
    print(f"Station: {STATION_ID} | {STATION_NAME}")
    print(f"Role: {RADIO_ROLE} | Local role: {LOCAL_ROLE}")
    print(f"AP: {AP_IP}")
    print(f"SM: {SM_IP}")
    print(f"Intervalo: {INTERVAL_SECONDS} s")

    while True:
        try:
            collect_once()

        except KeyboardInterrupt:
            print("RadioLink Collector detenido por usuario")
            break

        except Exception as e:
            err = str(e)
            print(f"RADIO ERROR: {err}")
            try:
                save_status("RADIO_UNAVAILABLE", err)
            except Exception as db_err:
                print(f"ERROR GUARDANDO ESTADO RADIO: {db_err}")

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    run_daemon()
