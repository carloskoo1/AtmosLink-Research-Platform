from __future__ import annotations

import json
import signal
import sqlite3
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from weather_station.config.settings import load_config


PROJECT_ROOT = Path(__file__).resolve().parents[2]

LINK_ID = "LINK_6G_4600C"
DEVICE_MODEL = "Cambium ePMP Force 4600C"
FREQUENCY_BAND = "6_GHZ"

AP_DEVICE_ID = "CU01_4600C_AP"
AP_STATION_ID = "CU01"
AP_IP = "192.168.1.8"

SM_DEVICE_ID = "SJ01_4600C_SM"
SM_STATION_ID = "SJ01"
SM_IP = "192.168.1.9"

SM_PASSFILE = Path(
    "/home/carlos/epmp_monitor/config/.radio_pass_4600_sm"
)

INTERVAL_SECONDS = 300
SSH_TIMEOUT_SECONDS = 15

TABLE_NAME = "radio_link_config_telemetry"

running = True


def stop_handler(signum: int, frame: Any) -> None:
    global running
    running = False


def now_times() -> tuple[str, str]:
    return (
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
        datetime.now().astimezone().isoformat(timespec="seconds"),
    )


def parse_key_value(text: str) -> dict[str, str]:
    values: dict[str, str] = {}

    for line in text.splitlines():
        parts = line.strip().split(None, 1)

        if len(parts) != 2:
            continue

        key, value = parts
        values[key.strip()] = value.strip()

    return values


def numeric(value: Any) -> float | None:
    if value is None:
        return None

    text = str(value).strip()

    if not text or text.upper() == "N/A":
        return None

    text = text.rstrip("Mm%")

    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def integer(value: Any) -> int | None:
    number = numeric(value)
    return int(number) if number is not None else None


def bandwidth_mhz(raw_value: Any) -> float | None:
    raw = integer(raw_value)

    # Correspondencias verificadas con la interfaz del Force 4600C.
    mapping = {
        1: 20.0,
        2: 40.0,
    }

    return mapping.get(raw)


def load_runtime_config() -> tuple[str, Path, Path]:
    config = load_config()

    ssh_user = str(config["radio_link"]["ssh_user"])
    ap_passfile = Path(str(config["radio_link"]["passfile"]))

    database_value = Path(str(config["database"]["sqlite"]))

    if database_value.is_absolute():
        database = database_value
    else:
        database = PROJECT_ROOT / database_value

    return ssh_user, ap_passfile, database


def run_ssh(
    ssh_user: str,
    passfile: Path,
    host: str,
    command_text: str,
) -> str:
    command = [
        "sshpass",
        "-f",
        str(passfile),
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-o",
        f"ConnectTimeout={SSH_TIMEOUT_SECONDS}",
        f"{ssh_user}@{host}",
        command_text,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=SSH_TIMEOUT_SECONDS + 5,
        check=False,
    )

    if result.returncode != 0:
        error = result.stderr.strip() or result.stdout.strip()

        raise RuntimeError(
            f"SSH {host} {command_text}: "
            f"código {result.returncode}: {error}"
        )

    return result.stdout


def table_columns(
    con: sqlite3.Connection,
) -> set[str]:
    return {
        row[1]
        for row in con.execute(
            f"PRAGMA table_info({TABLE_NAME})"
        )
    }


def init_database(database: Path) -> None:
    database.parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(database, timeout=30)
    con.execute("PRAGMA busy_timeout=30000")

    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            timestamp_utc TEXT NOT NULL,
            timestamp_local TEXT NOT NULL,

            link_id TEXT NOT NULL,
            device_model TEXT NOT NULL,
            frequency_band TEXT NOT NULL,

            ap_device_id TEXT NOT NULL,
            ap_station_id TEXT NOT NULL,
            ap_ip TEXT NOT NULL,

            sm_device_id TEXT NOT NULL,
            sm_station_id TEXT NOT NULL,
            sm_ip TEXT NOT NULL,

            source_device_id TEXT NOT NULL,
            source_access TEXT NOT NULL,

            operating_frequency_mhz REAL,
            channel_bandwidth_raw INTEGER,
            channel_bandwidth_mhz REAL,

            tdd_ratio_raw INTEGER,
            tdd_dl_pct REAL,
            tdd_ul_pct REAL,
            tdd_frame_us INTEGER,
            tdd_frame_ms REAL,

            ap_tx_power_dbm REAL,
            configured_min_tx_power_dbm REAL,
            effective_antenna_gain_dbi REAL,

            dl_rssi_dbm REAL,
            ul_rssi_dbm REAL,
            dl_snr_db REAL,
            ul_snr_db REAL,

            dl_mcs REAL,
            ul_mcs REAL,
            dl_rate_mbps REAL,
            ul_rate_mbps REAL,

            tx_quality_pct REAL,
            tx_capacity_pct REAL,

            sm_direct_access_ok INTEGER NOT NULL DEFAULT 0,
            collection_status TEXT NOT NULL,

            dashboard_raw_json TEXT,
            station_raw_json TEXT,

            note TEXT,
            error TEXT,

            sm_operating_frequency_mhz REAL,
            sm_channel_bandwidth_raw INTEGER,
            sm_channel_bandwidth_mhz REAL,
            sm_tx_power_dbm REAL,
            sm_effective_antenna_gain_dbi REAL,
            sm_dl_rssi_dbm REAL,
            sm_dl_snr_db REAL,
            sm_tx_quality_pct REAL,
            sm_tx_capacity_pct REAL,
            sm_dashboard_raw_json TEXT
        )
        """
    )

    existing = table_columns(con)

    migrations = {
        "tdd_ratio_raw": "INTEGER",
        "tdd_dl_pct": "REAL",
        "tdd_ul_pct": "REAL",
        "tdd_frame_us": "INTEGER",
        "tdd_frame_ms": "REAL",
        "sm_operating_frequency_mhz": "REAL",
        "sm_channel_bandwidth_raw": "INTEGER",
        "sm_channel_bandwidth_mhz": "REAL",
        "sm_tx_power_dbm": "REAL",
        "sm_effective_antenna_gain_dbi": "REAL",
        "sm_dl_rssi_dbm": "REAL",
        "sm_dl_snr_db": "REAL",
        "sm_tx_quality_pct": "REAL",
        "sm_tx_capacity_pct": "REAL",
        "sm_dashboard_raw_json": "TEXT",
    }

    for column, column_type in migrations.items():
        if column not in existing:
            con.execute(
                f"""
                ALTER TABLE {TABLE_NAME}
                ADD COLUMN {column} {column_type}
                """
            )

    con.execute(
        f"""
        CREATE INDEX IF NOT EXISTS
            idx_{TABLE_NAME}_time
        ON {TABLE_NAME} (
            timestamp_utc
        )
        """
    )

    con.execute(
        f"""
        CREATE INDEX IF NOT EXISTS
            idx_{TABLE_NAME}_link
        ON {TABLE_NAME} (
            link_id,
            timestamp_utc
        )
        """
    )

    con.commit()
    con.close()


def insert_record(
    database: Path,
    record: dict[str, Any],
) -> None:
    columns = list(record.keys())
    column_sql = ", ".join(columns)
    placeholders = ", ".join(
        f":{column}"
        for column in columns
    )

    con = sqlite3.connect(database, timeout=30)
    con.execute("PRAGMA busy_timeout=30000")

    con.execute(
        f"""
        INSERT INTO {TABLE_NAME} (
            {column_sql}
        )
        VALUES (
            {placeholders}
        )
        """,
        record,
    )

    con.commit()
    con.close()


def save_success(
    database: Path,
    ap_dashboard: dict[str, str],
    ap_station: dict[str, str],
    sm_dashboard: dict[str, str],
    ap_config: dict[str, str],
) -> None:
    timestamp_utc, timestamp_local = now_times()

    ap_bandwidth_raw = integer(
        ap_dashboard.get(
            "cambiumSTAConnectedRFBandwidth"
        )
    )

    sm_bandwidth_raw = integer(
        sm_dashboard.get(
            "cambiumSTAConnectedRFBandwidth"
        )
    )

    tdd_ratio_raw = integer(
        ap_config.get("wirelessInterfaceTDDRatio")
    )
    tdd_frame_us = integer(
        ap_config.get("wirelessInterfaceTDDFrameSize")
    )

    # Mapeo documentado para la codificación TDD del equipo.
    tdd_ratio_map = {
        1: (75.0, 25.0),
        2: (50.0, 50.0),
        3: (30.0, 70.0),
    }
    tdd_dl_pct, tdd_ul_pct = tdd_ratio_map.get(
        tdd_ratio_raw,
        (None, None),
    )

    record = {
        "timestamp_utc": timestamp_utc,
        "timestamp_local": timestamp_local,

        "link_id": LINK_ID,
        "device_model": DEVICE_MODEL,
        "frequency_band": FREQUENCY_BAND,

        "ap_device_id": AP_DEVICE_ID,
        "ap_station_id": AP_STATION_ID,
        "ap_ip": AP_IP,

        "sm_device_id": SM_DEVICE_ID,
        "sm_station_id": SM_STATION_ID,
        "sm_ip": SM_IP,

        "source_device_id": (
            f"{AP_DEVICE_ID}+{SM_DEVICE_ID}"
        ),
        "source_access": "SSH_AP_AND_SM",

        "operating_frequency_mhz": numeric(
            ap_dashboard.get(
                "cambiumSTAConnectedRFFrequency"
            )
        ),
        "channel_bandwidth_raw": ap_bandwidth_raw,
        "channel_bandwidth_mhz": bandwidth_mhz(
            ap_bandwidth_raw
        ),

        "tdd_ratio_raw": tdd_ratio_raw,
        "tdd_dl_pct": tdd_dl_pct,
        "tdd_ul_pct": tdd_ul_pct,
        "tdd_frame_us": tdd_frame_us,
        "tdd_frame_ms": (
            tdd_frame_us / 1000.0
            if tdd_frame_us is not None
            else None
        ),

        "ap_tx_power_dbm": numeric(
            ap_dashboard.get(
                "cambiumSTAConductedTXPower"
            )
        ),
        "configured_min_tx_power_dbm": numeric(
            ap_dashboard.get(
                "cambiumEPTPMinTXPower"
            )
        ),
        "effective_antenna_gain_dbi": numeric(
            ap_dashboard.get(
                "cambiumEffectiveAntennaGain"
            )
        ),

        "dl_rssi_dbm": numeric(
            ap_station.get("connectedSTADLRSSI")
        ),
        "ul_rssi_dbm": numeric(
            ap_station.get("connectedSTAULRSSI")
        ),
        "dl_snr_db": numeric(
            ap_station.get("connectedSTADLSNR")
        ),
        "ul_snr_db": numeric(
            ap_station.get("connectedSTAULSNR")
        ),

        "dl_mcs": numeric(
            ap_station.get("connectedSTADLMCS")
        ),
        "ul_mcs": numeric(
            ap_station.get("connectedSTAULMCS")
        ),
        "dl_rate_mbps": numeric(
            ap_station.get("connectedSTADLRateMbps")
        ),
        "ul_rate_mbps": numeric(
            ap_station.get("connectedSTAULRateMbps")
        ),

        "tx_quality_pct": numeric(
            ap_station.get("connectedSTATXQuality")
        ),
        "tx_capacity_pct": numeric(
            ap_station.get("connectedSTATXCapacity")
        ),

        "sm_direct_access_ok": 1,
        "collection_status": "LINK_OPERATIONAL_DUAL",

        "dashboard_raw_json": json.dumps(
            ap_dashboard,
            ensure_ascii=False,
            sort_keys=True,
        ),
        "station_raw_json": json.dumps(
            ap_station,
            ensure_ascii=False,
            sort_keys=True,
        ),

        "note": (
            "Telemetría y configuración obtenidas "
            "directamente desde AP y SM."
        ),
        "error": "",

        "sm_operating_frequency_mhz": numeric(
            sm_dashboard.get(
                "cambiumSTAConnectedRFFrequency"
            )
        ),
        "sm_channel_bandwidth_raw": sm_bandwidth_raw,
        "sm_channel_bandwidth_mhz": bandwidth_mhz(
            sm_bandwidth_raw
        ),
        "sm_tx_power_dbm": numeric(
            sm_dashboard.get(
                "cambiumSTAConductedTXPower"
            )
        ),
        "sm_effective_antenna_gain_dbi": numeric(
            sm_dashboard.get(
                "cambiumEffectiveAntennaGain"
            )
        ),
        "sm_dl_rssi_dbm": numeric(
            sm_dashboard.get("cambiumSTADLRSSI")
        ),
        "sm_dl_snr_db": numeric(
            sm_dashboard.get("cambiumSTADLSNR")
        ),
        "sm_tx_quality_pct": numeric(
            sm_dashboard.get("staTxQuality")
        ),
        "sm_tx_capacity_pct": numeric(
            sm_dashboard.get("staTxCapacity")
        ),
        "sm_dashboard_raw_json": json.dumps(
            sm_dashboard,
            ensure_ascii=False,
            sort_keys=True,
        ),
    }

    insert_record(database, record)

    print(
        f"{timestamp_local} | {LINK_ID} | "
        f"LINK_OPERATIONAL_DUAL | "
        f"AP_TX={record['ap_tx_power_dbm']} dBm | "
        f"SM_TX={record['sm_tx_power_dbm']} dBm | "
        f"DL_RSSI={record['dl_rssi_dbm']} dBm | "
        f"UL_RSSI={record['ul_rssi_dbm']} dBm | "
        f"DL_SNR={record['dl_snr_db']} dB | "
        f"UL_SNR={record['ul_snr_db']} dB | "
        f"AP_QUALITY={record['tx_quality_pct']} % | "
        f"SM_QUALITY={record['sm_tx_quality_pct']} %",
        flush=True,
    )


def save_failure(
    database: Path,
    error: str,
) -> None:
    timestamp_utc, timestamp_local = now_times()

    record = {
        "timestamp_utc": timestamp_utc,
        "timestamp_local": timestamp_local,

        "link_id": LINK_ID,
        "device_model": DEVICE_MODEL,
        "frequency_band": FREQUENCY_BAND,

        "ap_device_id": AP_DEVICE_ID,
        "ap_station_id": AP_STATION_ID,
        "ap_ip": AP_IP,

        "sm_device_id": SM_DEVICE_ID,
        "sm_station_id": SM_STATION_ID,
        "sm_ip": SM_IP,

        "source_device_id": AP_DEVICE_ID,
        "source_access": "SSH_DUAL_ATTEMPT",

        "sm_direct_access_ok": 0,
        "collection_status": "COLLECTION_ERROR",

        "note": (
            "Falló la consulta conjunta del AP o SM."
        ),
        "error": error[:1000],
    }

    insert_record(database, record)

    print(
        f"{timestamp_local} | {LINK_ID} | "
        f"COLLECTION_ERROR | {error}",
        flush=True,
    )


def collect_once(
    ssh_user: str,
    ap_passfile: Path,
    database: Path,
) -> None:
    ap_dashboard_text = run_ssh(
        ssh_user,
        ap_passfile,
        AP_IP,
        "show dashboard",
    )

    ap_station_text = run_ssh(
        ssh_user,
        ap_passfile,
        AP_IP,
        "show sta",
    )

    ap_config_text = run_ssh(
        ssh_user,
        ap_passfile,
        AP_IP,
        "show config",
    )

    sm_dashboard_text = run_ssh(
        "admin",
        SM_PASSFILE,
        SM_IP,
        "show dashboard",
    )

    ap_dashboard = parse_key_value(
        ap_dashboard_text
    )
    ap_station = parse_key_value(
        ap_station_text
    )
    ap_config = parse_key_value(
        ap_config_text
    )
    sm_dashboard = parse_key_value(
        sm_dashboard_text
    )

    required = (
        ap_dashboard.get(
            "cambiumSTAConnectedRFFrequency"
        ),
        ap_dashboard.get(
            "cambiumSTAConductedTXPower"
        ),
        ap_station.get(
            "connectedSTADLRSSI"
        ),
        ap_station.get(
            "connectedSTADLSNR"
        ),
        sm_dashboard.get(
            "cambiumSTAConnectedRFFrequency"
        ),
        sm_dashboard.get(
            "cambiumSTAConductedTXPower"
        ),
    )

    if not all(value is not None for value in required):
        raise RuntimeError(
            "La consulta respondió, pero faltan "
            "variables obligatorias."
        )

    save_success(
        database=database,
        ap_dashboard=ap_dashboard,
        ap_station=ap_station,
        sm_dashboard=sm_dashboard,
        ap_config=ap_config,
    )


def main() -> None:
    signal.signal(signal.SIGTERM, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)

    ssh_user, ap_passfile, database = (
        load_runtime_config()
    )

    if not ap_passfile.is_file():
        raise RuntimeError(
            f"No existe el passfile del AP: "
            f"{ap_passfile}"
        )

    if not SM_PASSFILE.is_file():
        raise RuntimeError(
            f"No existe el passfile del SM: "
            f"{SM_PASSFILE}"
        )

    init_database(database)

    print(
        "AtmosLink Dual Force 4600C Collector",
        flush=True,
    )
    print(f"Link: {LINK_ID}", flush=True)
    print(f"AP: {AP_IP}", flush=True)
    print(f"SM: {SM_IP}", flush=True)
    print(f"Database: {database}", flush=True)
    print(
        f"Interval: {INTERVAL_SECONDS} s",
        flush=True,
    )

    while running:
        try:
            collect_once(
                ssh_user=ssh_user,
                ap_passfile=ap_passfile,
                database=database,
            )

        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            print(error, flush=True)

            try:
                save_failure(database, error)
            except Exception as database_exc:
                print(
                    f"Error guardando fallo: "
                    f"{database_exc}",
                    flush=True,
                )

        for _ in range(INTERVAL_SECONDS):
            if not running:
                break

            time.sleep(1)


if __name__ == "__main__":
    main()
