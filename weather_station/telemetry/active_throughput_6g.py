from __future__ import annotations

import argparse
import csv
import fcntl
import json
import re
import sqlite3
import subprocess
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


CAMPAIGN_ID = "CAMPAIGN_6G_20260831"
FORMAL_CAMPAIGN_ID = "ANDEAN_6GHZ_3X2_2026"
FORMAL_START_LOCAL = "2026-09-15T00:00:00-05:00"
LINK_ID = "LINK_6G_4600C"
TABLE = "active_throughput_6g"
CLIENT_IP = "192.168.1.50"
SERVER_IP = "192.168.1.4"
CLIENT_INTERFACE = "enp1s0"
SERVER_INTERFACE = "eth0"
PORT = 5201
DURATION_SECONDS = 8
OMIT_SECONDS = 1
PARALLEL_STREAMS = 1


def now_pair() -> tuple[str, str]:
    return (
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
        datetime.now().astimezone().isoformat(timespec="seconds"),
    )


def run(command: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def interface_counters(interface: str) -> tuple[int, int]:
    root = Path("/sys/class/net") / interface / "statistics"
    return (
        int((root / "rx_bytes").read_text().strip()),
        int((root / "tx_bytes").read_text().strip()),
    )


def ping_metrics() -> dict[str, Any]:
    result = run(
        ["ping", "-I", CLIENT_INTERFACE, "-c", "5", "-W", "2", SERVER_IP],
        timeout=20,
    )
    text = result.stdout + "\n" + result.stderr
    loss_match = re.search(r"([0-9.]+)% packet loss", text)
    rtt_match = re.search(
        r"(?:rtt|round-trip) min/avg/max/(?:mdev|stddev) = "
        r"([0-9.]+)/([0-9.]+)/([0-9.]+)/([0-9.]+)",
        text,
    )
    return {
        "ping_status": "OK" if result.returncode == 0 else "ERROR",
        "ping_loss_pct": float(loss_match.group(1)) if loss_match else None,
        "ping_rtt_min_ms": float(rtt_match.group(1)) if rtt_match else None,
        "ping_rtt_avg_ms": float(rtt_match.group(2)) if rtt_match else None,
        "ping_rtt_max_ms": float(rtt_match.group(3)) if rtt_match else None,
        "ping_rtt_mdev_ms": float(rtt_match.group(4)) if rtt_match else None,
        "ping_raw": text[-4000:],
    }


def get_nested(data: dict[str, Any], *path: str) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def bps_to_mbps(value: Any) -> float | None:
    try:
        return float(value) / 1_000_000.0
    except (TypeError, ValueError):
        return None


def run_iperf(
    direction: str,
    duration_seconds: int,
    omit_seconds: int,
    parallel_streams: int,
) -> tuple[dict[str, Any] | None, str]:
    command = [
        "iperf3",
        "--client", SERVER_IP,
        "--bind", CLIENT_IP,
        "--port", str(PORT),
        "--time", str(duration_seconds),
        "--omit", str(omit_seconds),
        "--parallel", str(parallel_streams),
        "--json",
    ]
    if direction == "UL":
        command.append("--reverse")

    errors: list[str] = []
    for attempt in range(1, 4):
        result = run(command, timeout=duration_seconds + omit_seconds + 30)
        raw = result.stdout.strip()
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError as exc:
            payload = None
            errors.append(f"intento {attempt}: JSON inválido: {exc}; {result.stderr.strip()}")

        if result.returncode == 0 and isinstance(payload, dict) and not payload.get("error"):
            return payload, ""

        detail = ""
        if isinstance(payload, dict):
            detail = str(payload.get("error", ""))
        detail = detail or result.stderr.strip() or raw[-1000:]
        errors.append(f"intento {attempt}: {detail}")
        if attempt < 3:
            time.sleep(3)

    return None, " | ".join(errors)[-4000:]


def init_database(connection: sqlite3.Connection) -> None:
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id TEXT NOT NULL,
            campaign_id TEXT NOT NULL,
            link_id TEXT NOT NULL,
            direction TEXT NOT NULL,
            timestamp_start_utc TEXT NOT NULL,
            timestamp_start_local TEXT NOT NULL,
            timestamp_end_utc TEXT NOT NULL,
            timestamp_end_local TEXT NOT NULL,
            status TEXT NOT NULL,
            error TEXT,
            protocol TEXT NOT NULL,
            client_ip TEXT NOT NULL,
            server_ip TEXT NOT NULL,
            client_interface TEXT NOT NULL,
            server_interface TEXT NOT NULL,
            route_verified INTEGER NOT NULL,
            duration_seconds INTEGER NOT NULL,
            omit_seconds INTEGER NOT NULL,
            parallel_streams INTEGER NOT NULL,
            sender_mbps REAL,
            receiver_mbps REAL,
            measured_throughput_mbps REAL,
            retransmits INTEGER,
            bytes_sent INTEGER,
            bytes_received INTEGER,
            local_interface_rx_delta_bytes INTEGER,
            local_interface_tx_delta_bytes INTEGER,
            ping_status TEXT,
            ping_loss_pct REAL,
            ping_rtt_min_ms REAL,
            ping_rtt_avg_ms REAL,
            ping_rtt_max_ms REAL,
            ping_rtt_mdev_ms REAL,
            rf_telemetry_id INTEGER,
            rf_timestamp_local TEXT,
            rf_time_delta_seconds REAL,
            operating_frequency_mhz REAL,
            channel_bandwidth_mhz REAL,
            tdd_ratio_raw INTEGER,
            tdd_dl_pct REAL,
            tdd_ul_pct REAL,
            tdd_frame_us INTEGER,
            tdd_frame_ms REAL,
            ap_tx_power_dbm REAL,
            sm_tx_power_dbm REAL,
            dl_rssi_dbm REAL,
            ul_rssi_dbm REAL,
            dl_snr_db REAL,
            ul_snr_db REAL,
            dl_mcs REAL,
            ul_mcs REAL,
            reported_dl_link_rate_mbps REAL,
            reported_ul_link_rate_mbps REAL,
            tx_quality_pct REAL,
            tx_capacity_pct REAL,
            sm_tx_quality_pct REAL,
            sm_tx_capacity_pct REAL,
            cu01_weather_timestamp_local TEXT,
            cu01_weather_time_delta_seconds REAL,
            cu01_temp_c REAL,
            cu01_hum_pct REAL,
            cu01_press_hpa REAL,
            cu01_rain_1min_mm REAL,
            cu01_wind_speed_ms REAL,
            cu01_wind_direction_deg REAL,
            sj01_weather_timestamp_local TEXT,
            sj01_weather_time_delta_seconds REAL,
            sj01_temp_c REAL,
            sj01_hum_pct REAL,
            sj01_press_hpa REAL,
            sj01_rain_1min_mm REAL,
            sj01_wind_speed_ms REAL,
            sj01_wind_direction_deg REAL,
            iperf_json TEXT,
            ping_raw TEXT
        )
        """
    )
    existing = {
        row[1]
        for row in connection.execute(f"PRAGMA table_info({TABLE})")
    }
    migrations = {
        "tdd_ratio_raw": "INTEGER",
        "tdd_dl_pct": "REAL",
        "tdd_ul_pct": "REAL",
        "tdd_frame_us": "INTEGER",
        "tdd_frame_ms": "REAL",
        "cu01_weather_time_delta_seconds": "REAL",
        "sj01_weather_time_delta_seconds": "REAL",
    }
    for column, column_type in migrations.items():
        if column not in existing:
            connection.execute(
                f"ALTER TABLE {TABLE} ADD COLUMN {column} {column_type}"
            )
    connection.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{TABLE}_time ON {TABLE}(timestamp_start_utc)"
    )
    connection.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{TABLE}_direction ON {TABLE}(direction, timestamp_start_utc)"
    )
    connection.commit()


def nearest_rf(connection: sqlite3.Connection, timestamp_utc: str) -> dict[str, Any]:
    connection.row_factory = sqlite3.Row
    row = connection.execute(
        """
        SELECT *, ABS(strftime('%s', timestamp_utc) - strftime('%s', ?)) AS delta_s
        FROM radio_link_config_telemetry
        WHERE link_id = ? AND frequency_band = '6_GHZ'
        ORDER BY delta_s ASC
        LIMIT 1
        """,
        (timestamp_utc, LINK_ID),
    ).fetchone()
    if row is None or float(row["delta_s"] or 999999) > 600:
        return {}
    return dict(row)


def nearest_weather(
    connection: sqlite3.Connection,
    station_id: str,
    timestamp_utc: str,
) -> dict[str, Any]:
    connection.row_factory = sqlite3.Row
    if station_id == "CU01":
        query = """
            SELECT
                timestamp_local AS weather_timestamp_local,
                temp_avg_C AS local_temp_avg_c,
                hum_avg_pct AS local_hum_avg_pct,
                pres_avg_hPa AS local_press_hpa,
                rain_1min_mm AS local_rain_1min_mm,
                wind_speed_ms AS local_wind_speed_ms,
                wind_direction_deg AS local_wind_direction_deg,
                ABS(strftime('%s', timestamp_utc) - strftime('%s', ?)) AS delta_s
            FROM weather_local
            WHERE station_id = 'CU01' OR station_id IS NULL
            ORDER BY delta_s ASC
            LIMIT 1
        """
        parameters = (timestamp_utc,)
    else:
        query = """
            SELECT
                timestamp_local AS weather_timestamp_local,
                temp_avg_C AS local_temp_avg_c,
                hum_avg_pct AS local_hum_avg_pct,
                pres_avg_hPa AS local_press_hpa,
                rain_1min_mm AS local_rain_1min_mm,
                wind_speed_ms AS local_wind_speed_ms,
                wind_direction_deg AS local_wind_direction_deg,
                ABS(strftime('%s', timestamp_utc) - strftime('%s', ?)) AS delta_s
            FROM station_observations
            WHERE source_station_id = ? OR station_id = ?
            ORDER BY delta_s ASC
            LIMIT 1
        """
        parameters = (timestamp_utc, station_id, station_id)

    row = connection.execute(query, parameters).fetchone()
    if row is None or float(row["delta_s"] or 999999) > 600:
        return {}
    return dict(row)


def build_record(
    test_id: str,
    campaign_id: str,
    duration_seconds: int,
    omit_seconds: int,
    parallel_streams: int,
    direction: str,
    start_utc: str,
    start_local: str,
    end_utc: str,
    end_local: str,
    payload: dict[str, Any] | None,
    error: str,
    counters_before: tuple[int, int],
    counters_after: tuple[int, int],
    ping: dict[str, Any],
    rf: dict[str, Any],
    cu01: dict[str, Any],
    sj01: dict[str, Any],
) -> dict[str, Any]:
    sent = get_nested(payload or {}, "end", "sum_sent") or {}
    received = get_nested(payload or {}, "end", "sum_received") or {}
    receiver_mbps = bps_to_mbps(received.get("bits_per_second"))
    return {
        "test_id": test_id,
        "campaign_id": campaign_id,
        "link_id": LINK_ID,
        "direction": direction,
        "timestamp_start_utc": start_utc,
        "timestamp_start_local": start_local,
        "timestamp_end_utc": end_utc,
        "timestamp_end_local": end_local,
        "status": "OK" if payload is not None and not error else "ERROR",
        "error": error,
        "protocol": "TCP",
        "client_ip": CLIENT_IP,
        "server_ip": SERVER_IP,
        "client_interface": CLIENT_INTERFACE,
        "server_interface": SERVER_INTERFACE,
        "route_verified": 1,
        "duration_seconds": duration_seconds,
        "omit_seconds": omit_seconds,
        "parallel_streams": parallel_streams,
        "sender_mbps": bps_to_mbps(sent.get("bits_per_second")),
        "receiver_mbps": receiver_mbps,
        "measured_throughput_mbps": receiver_mbps,
        "retransmits": sent.get("retransmits"),
        "bytes_sent": sent.get("bytes"),
        "bytes_received": received.get("bytes"),
        "local_interface_rx_delta_bytes": max(0, counters_after[0] - counters_before[0]),
        "local_interface_tx_delta_bytes": max(0, counters_after[1] - counters_before[1]),
        **{key: ping.get(key) for key in (
            "ping_status", "ping_loss_pct", "ping_rtt_min_ms", "ping_rtt_avg_ms",
            "ping_rtt_max_ms", "ping_rtt_mdev_ms",
        )},
        "rf_telemetry_id": rf.get("id"),
        "rf_timestamp_local": rf.get("timestamp_local"),
        "rf_time_delta_seconds": rf.get("delta_s"),
        "operating_frequency_mhz": rf.get("operating_frequency_mhz"),
        "channel_bandwidth_mhz": rf.get("channel_bandwidth_mhz"),
        "tdd_ratio_raw": rf.get("tdd_ratio_raw"),
        "tdd_dl_pct": rf.get("tdd_dl_pct"),
        "tdd_ul_pct": rf.get("tdd_ul_pct"),
        "tdd_frame_us": rf.get("tdd_frame_us"),
        "tdd_frame_ms": rf.get("tdd_frame_ms"),
        "ap_tx_power_dbm": rf.get("ap_tx_power_dbm"),
        "sm_tx_power_dbm": rf.get("sm_tx_power_dbm"),
        "dl_rssi_dbm": rf.get("dl_rssi_dbm"),
        "ul_rssi_dbm": rf.get("ul_rssi_dbm"),
        "dl_snr_db": rf.get("dl_snr_db"),
        "ul_snr_db": rf.get("ul_snr_db"),
        "dl_mcs": rf.get("dl_mcs"),
        "ul_mcs": rf.get("ul_mcs"),
        "reported_dl_link_rate_mbps": rf.get("dl_rate_mbps"),
        "reported_ul_link_rate_mbps": rf.get("ul_rate_mbps"),
        "tx_quality_pct": rf.get("tx_quality_pct"),
        "tx_capacity_pct": rf.get("tx_capacity_pct"),
        "sm_tx_quality_pct": rf.get("sm_tx_quality_pct"),
        "sm_tx_capacity_pct": rf.get("sm_tx_capacity_pct"),
        "cu01_weather_timestamp_local": cu01.get("weather_timestamp_local"),
        "cu01_weather_time_delta_seconds": cu01.get("delta_s"),
        "cu01_temp_c": cu01.get("local_temp_avg_c"),
        "cu01_hum_pct": cu01.get("local_hum_avg_pct"),
        "cu01_press_hpa": cu01.get("local_press_hpa"),
        "cu01_rain_1min_mm": cu01.get("local_rain_1min_mm"),
        "cu01_wind_speed_ms": cu01.get("local_wind_speed_ms"),
        "cu01_wind_direction_deg": cu01.get("local_wind_direction_deg"),
        "sj01_weather_timestamp_local": sj01.get("weather_timestamp_local"),
        "sj01_weather_time_delta_seconds": sj01.get("delta_s"),
        "sj01_temp_c": sj01.get("local_temp_avg_c"),
        "sj01_hum_pct": sj01.get("local_hum_avg_pct"),
        "sj01_press_hpa": sj01.get("local_press_hpa"),
        "sj01_rain_1min_mm": sj01.get("local_rain_1min_mm"),
        "sj01_wind_speed_ms": sj01.get("local_wind_speed_ms"),
        "sj01_wind_direction_deg": sj01.get("local_wind_direction_deg"),
        "iperf_json": json.dumps(payload, ensure_ascii=False, sort_keys=True) if payload else "",
        "ping_raw": ping.get("ping_raw", ""),
    }


def insert_record(connection: sqlite3.Connection, record: dict[str, Any]) -> None:
    columns = list(record)
    connection.execute(
        f'INSERT INTO {TABLE} ({", ".join(columns)}) VALUES ({", ".join("?" for _ in columns)})',
        [record[column] for column in columns],
    )
    connection.commit()


def export_csv(connection: sqlite3.Connection, destination: Path) -> None:
    connection.row_factory = sqlite3.Row
    rows = connection.execute(f"SELECT * FROM {TABLE} ORDER BY id").fetchall()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        if rows:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(dict(row) for row in rows)
    temporary.replace(destination)


def collect(
    database: Path,
    output_csv: Path,
    directions: list[str],
    campaign_id: str,
    duration_seconds: int,
    omit_seconds: int,
    parallel_streams: int,
) -> None:
    lock_path = Path("runtime/active_throughput_6g.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as lock_handle:
        try:
            fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Otra prueba de throughput está en ejecución.")

        connection = sqlite3.connect(database, timeout=60)
        connection.execute("PRAGMA busy_timeout=60000")
        init_database(connection)
        test_id = str(uuid.uuid4())
        ping = ping_metrics()

        for index, direction in enumerate(directions):
            if index:
                time.sleep(5)
            start_utc, start_local = now_pair()
            before = interface_counters(CLIENT_INTERFACE)
            payload, error = run_iperf(
                direction,
                duration_seconds,
                omit_seconds,
                parallel_streams,
            )
            after = interface_counters(CLIENT_INTERFACE)
            end_utc, end_local = now_pair()
            rf = nearest_rf(connection, start_utc)
            cu01 = nearest_weather(connection, "CU01", start_utc)
            sj01 = nearest_weather(connection, "SJ01", start_utc)
            record = build_record(
                test_id,
                campaign_id,
                duration_seconds,
                omit_seconds,
                parallel_streams,
                direction, start_utc, start_local, end_utc, end_local,
                payload, error, before, after, ping, rf, cu01, sj01,
            )
            insert_record(connection, record)
            print(
                f"{direction} | {record['status']} | "
                f"throughput={record['measured_throughput_mbps']} Mbps | "
                f"retransmits={record['retransmits']} | "
                f"RTT={record['ping_rtt_avg_ms']} ms",
                flush=True,
            )

        export_csv(connection, output_csv)
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--direction", choices=["BOTH", "DL", "UL"], default="BOTH")
    parser.add_argument("--campaign-id", default=CAMPAIGN_ID)
    parser.add_argument("--duration", type=int, default=DURATION_SECONDS)
    parser.add_argument("--omit", type=int, default=OMIT_SECONDS)
    parser.add_argument("--parallel", type=int, default=PARALLEL_STREAMS)
    args = parser.parse_args()

    # Safety guard: the legacy 15-minute pilot timer invokes this module without
    # --campaign-id. From the formal 3x2 start onward it must not generate extra
    # network load or contaminate the experiment. The formal runner explicitly
    # passes ANDEAN_6GHZ_3X2_2026 and is therefore unaffected.
    now_local = datetime.now(timezone(timedelta(hours=-5))).isoformat()
    if args.campaign_id == CAMPAIGN_ID and now_local >= FORMAL_START_LOCAL:
        print(
            f"Legacy pilot throughput skipped after formal start {FORMAL_START_LOCAL}; "
            f"formal campaign is {FORMAL_CAMPAIGN_ID}.",
            flush=True,
        )
        return

    directions = ["DL", "UL"] if args.direction == "BOTH" else [args.direction]

    collect(
        args.database,
        args.output_csv,
        directions,
        args.campaign_id,
        args.duration,
        args.omit,
        args.parallel,
    )


if __name__ == "__main__":
    main()
