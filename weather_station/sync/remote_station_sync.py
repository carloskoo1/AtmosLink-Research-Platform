"""
AtmosLink Research Platform
Remote Station Synchronizer

Sincroniza incrementalmente observaciones meteorológicas desde estaciones
remotas hacia la tabla central station_observations.

Arquitectura:

    Raspberry remota
    SQLite/.../weather_local.db
              |
              | SSH sobre Tailscale
              v
    Controlador AtmosLink
    SQLite/CU01/weather_local.db
    tabla station_observations

Características:
- Sincronización incremental por source_local_id.
- Prevención de duplicados.
- Reanudación después de cortes de red.
- Lectura remota de SQLite en modo solo lectura.
- Soporte para múltiples estaciones declaradas en YAML.
- Registro del estado y errores de cada sincronización.
- Compatible con firmware_version, firmware_build y device_id.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_FILE = (
    PROJECT_ROOT
    / "Config"
    / "remote_stations.yaml"
)


WEATHER_FIELDS = [
    "id",
    "timestamp_utc",
    "timestamp_local",
    "station_id",
    "station_name",
    "radio_role",
    "t_s",
    "temp_avg_C",
    "temp_min_C",
    "temp_max_C",
    "hum_avg_pct",
    "hum_min_pct",
    "hum_max_pct",
    "pres_avg_hPa",
    "dew_point_C",
    "vapor_pressure_hPa",
    "rain_1min_mm",
    "rain_1h_mm",
    "rain_total_mm",
    "pulses_delta",
    "pulses_total",
    "bme_ok",
    "rain_ok",
    "wind_speed_ms",
    "wind_direction_deg",
    "wind_gust_ms",
    "wind_ok",
    "firmware_version",
    "firmware_build",
    "device_id",
]


STATION_OBSERVATION_COLUMNS = [
    "source_station_id",
    "source_local_id",
    "source_db",
    "timestamp_utc",
    "timestamp_local",
    "station_id",
    "station_name",
    "radio_role",
    "t_s",
    "temp_avg_C",
    "temp_min_C",
    "temp_max_C",
    "hum_avg_pct",
    "hum_min_pct",
    "hum_max_pct",
    "pres_avg_hPa",
    "dew_point_C",
    "vapor_pressure_hPa",
    "rain_1min_mm",
    "rain_1h_mm",
    "rain_total_mm",
    "pulses_delta",
    "pulses_total",
    "bme_ok",
    "rain_ok",
    "wind_speed_ms",
    "wind_direction_deg",
    "wind_gust_ms",
    "wind_ok",
    "firmware_version",
    "firmware_build",
    "device_id",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_configuration() -> dict[str, Any]:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"No existe el archivo de configuración: "
            f"{CONFIG_FILE}"
        )

    with CONFIG_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        config = yaml.safe_load(file) or {}

    if "remote_sync" not in config:
        raise RuntimeError(
            "Falta la sección remote_sync en "
            "Config/remote_stations.yaml"
        )

    if "stations" not in config:
        raise RuntimeError(
            "Falta la sección stations en "
            "Config/remote_stations.yaml"
        )

    return config


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value)

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def table_exists(
    conn: sqlite3.Connection,
    table_name: str,
) -> bool:
    row = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,),
    ).fetchone()

    return row is not None


def get_table_columns(
    conn: sqlite3.Connection,
    table_name: str,
) -> set[str]:
    rows = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return {
        row[1]
        for row in rows
    }


def ensure_central_schema(
    conn: sqlite3.Connection,
) -> None:
    """
    Crea o actualiza las tablas utilizadas por la sincronización.
    """

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS station_observations (
            central_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_station_id TEXT NOT NULL,
            source_local_id INTEGER NOT NULL,
            source_db TEXT,
            timestamp_utc TEXT,
            timestamp_local TEXT,
            station_id TEXT,
            station_name TEXT,
            radio_role TEXT,
            t_s INTEGER,
            temp_avg_C REAL,
            temp_min_C REAL,
            temp_max_C REAL,
            hum_avg_pct REAL,
            hum_min_pct REAL,
            hum_max_pct REAL,
            pres_avg_hPa REAL,
            dew_point_C REAL,
            vapor_pressure_hPa REAL,
            rain_1min_mm REAL,
            rain_1h_mm REAL,
            rain_total_mm REAL,
            pulses_delta INTEGER,
            pulses_total INTEGER,
            bme_ok INTEGER,
            rain_ok INTEGER,
            wind_speed_ms REAL,
            wind_direction_deg REAL,
            wind_gust_ms REAL,
            wind_ok INTEGER,
            firmware_version TEXT,
            firmware_build TEXT,
            device_id TEXT,
            UNIQUE(
                source_station_id,
                source_local_id
            )
        )
        """
    )

    required_columns = {
        "firmware_version": "TEXT",
        "firmware_build": "TEXT",
        "device_id": "TEXT",
    }

    existing_columns = get_table_columns(
        conn,
        "station_observations",
    )

    for column_name, column_type in required_columns.items():
        if column_name in existing_columns:
            continue

        conn.execute(
            f"""
            ALTER TABLE station_observations
            ADD COLUMN {column_name} {column_type}
            """
        )

        print(
            f"Columna agregada a station_observations: "
            f"{column_name}"
        )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS remote_sync_state (
            station_id TEXT PRIMARY KEY,
            remote_host TEXT NOT NULL,
            remote_database TEXT NOT NULL,

            last_source_local_id INTEGER NOT NULL DEFAULT 0,
            last_remote_timestamp TEXT,

            last_sync_started_utc TEXT,
            last_sync_completed_utc TEXT,

            last_status TEXT,
            last_error TEXT,

            rows_received INTEGER NOT NULL DEFAULT 0,
            rows_inserted INTEGER NOT NULL DEFAULT 0,
            rows_ignored INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_station_observations_source_timestamp
        ON station_observations (
            source_station_id,
            timestamp_local
        )
        """
    )

    conn.commit()


def get_last_synced_id(
    conn: sqlite3.Connection,
    station_id: str,
) -> int:
    """
    Obtiene el mayor id remoto confirmado para la estación.

    Se consulta tanto remote_sync_state como station_observations,
    para recuperarse incluso si el estado quedó desactualizado.
    """

    state_row = conn.execute(
        """
        SELECT last_source_local_id
        FROM remote_sync_state
        WHERE station_id = ?
        """,
        (station_id,),
    ).fetchone()

    state_id = (
        int(state_row[0])
        if state_row and state_row[0] is not None
        else 0
    )

    observation_row = conn.execute(
        """
        SELECT COALESCE(
            MAX(source_local_id),
            0
        )
        FROM station_observations
        WHERE source_station_id = ?
        """,
        (station_id,),
    ).fetchone()

    observation_id = (
        int(observation_row[0])
        if observation_row
        else 0
    )

    return max(
        state_id,
        observation_id,
    )


def update_sync_state(
    conn: sqlite3.Connection,
    *,
    station_id: str,
    remote_host: str,
    remote_database: str,
    last_source_local_id: int,
    last_remote_timestamp: str | None,
    started_utc: str,
    completed_utc: str | None,
    status: str,
    error: str | None,
    rows_received: int,
    rows_inserted: int,
    rows_ignored: int,
) -> None:
    conn.execute(
        """
        INSERT INTO remote_sync_state (
            station_id,
            remote_host,
            remote_database,
            last_source_local_id,
            last_remote_timestamp,
            last_sync_started_utc,
            last_sync_completed_utc,
            last_status,
            last_error,
            rows_received,
            rows_inserted,
            rows_ignored
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(station_id)
        DO UPDATE SET
            remote_host = excluded.remote_host,
            remote_database = excluded.remote_database,
            last_source_local_id =
                excluded.last_source_local_id,
            last_remote_timestamp =
                excluded.last_remote_timestamp,
            last_sync_started_utc =
                excluded.last_sync_started_utc,
            last_sync_completed_utc =
                excluded.last_sync_completed_utc,
            last_status =
                excluded.last_status,
            last_error =
                excluded.last_error,
            rows_received =
                excluded.rows_received,
            rows_inserted =
                excluded.rows_inserted,
            rows_ignored =
                excluded.rows_ignored
        """,
        (
            station_id,
            remote_host,
            remote_database,
            last_source_local_id,
            last_remote_timestamp,
            started_utc,
            completed_utc,
            status,
            error,
            rows_received,
            rows_inserted,
            rows_ignored,
        ),
    )

    conn.commit()


def build_remote_reader_script(
    *,
    remote_database: str,
    last_id: int,
    batch_size: int,
) -> str:
    """
    Devuelve un programa Python para ejecutarse en la Raspberry
    remota.

    La salida es un único documento JSON.
    """

    requested_fields_json = json.dumps(
        WEATHER_FIELDS
    )

    return f"""
import json
import sqlite3
import sys

database_path = {remote_database!r}
last_id = {int(last_id)}
batch_size = {int(batch_size)}
requested_fields = {requested_fields_json}

try:
    connection = sqlite3.connect(
        "file:" + database_path + "?mode=ro",
        uri=True,
        timeout=10,
    )

    connection.row_factory = sqlite3.Row

    table = connection.execute(
        '''
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'weather_local'
        '''
    ).fetchone()

    if table is None:
        raise RuntimeError(
            "No existe weather_local en la base remota"
        )

    available_columns = {{
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(weather_local)"
        ).fetchall()
    }}

    select_expressions = []

    for field in requested_fields:
        if field in available_columns:
            select_expressions.append(field)
        else:
            select_expressions.append(
                "NULL AS " + field
            )

    query = (
        "SELECT "
        + ", ".join(select_expressions)
        + " FROM weather_local "
        + "WHERE id > ? "
        + "ORDER BY id ASC "
        + "LIMIT ?"
    )

    rows = connection.execute(
        query,
        (last_id, batch_size),
    ).fetchall()

    payload = [
        dict(row)
        for row in rows
    ]

    connection.close()

    print(
        json.dumps(
            {{
                "status": "ok",
                "rows": payload,
            }},
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )

except Exception as exc:
    print(
        json.dumps(
            {{
                "status": "error",
                "error": str(exc),
            }},
            ensure_ascii=False,
        )
    )

    sys.exit(2)
"""


def fetch_remote_rows(
    *,
    station_config: dict[str, Any],
    last_id: int,
    batch_size: int,
    ssh_config: dict[str, Any],
) -> list[dict[str, Any]]:
    host = str(
        station_config["host"]
    )

    user = str(
        station_config["user"]
    )

    port = int(
        station_config.get(
            "port",
            22,
        )
    )

    remote_database = str(
        station_config["remote_database"]
    )

    connect_timeout = int(
        ssh_config.get(
            "connect_timeout_seconds",
            15,
        )
    )

    command_timeout = int(
        ssh_config.get(
            "command_timeout_seconds",
            45,
        )
    )

    remote_script = build_remote_reader_script(
        remote_database=remote_database,
        last_id=last_id,
        batch_size=batch_size,
    )

    ssh_command = [
        "ssh",
        "-p",
        str(port),
        "-o",
        "BatchMode=yes",
        "-o",
        f"ConnectTimeout={connect_timeout}",
        "-o",
        "ServerAliveInterval=10",
        "-o",
        "ServerAliveCountMax=2",
        f"{user}@{host}",
        "python3",
        "-",
    ]

    process = subprocess.run(
        ssh_command,
        input=remote_script,
        capture_output=True,
        text=True,
        timeout=command_timeout,
        check=False,
    )

    stdout = process.stdout.strip()
    stderr = process.stderr.strip()

    if process.returncode != 0:
        message = (
            stderr
            or stdout
            or (
                "SSH terminó con código "
                f"{process.returncode}"
            )
        )

        raise RuntimeError(message)

    if not stdout:
        raise RuntimeError(
            "La estación remota no devolvió JSON"
        )

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Respuesta remota no válida: "
            f"{stdout[:300]!r}"
        ) from exc

    if payload.get("status") != "ok":
        raise RuntimeError(
            str(
                payload.get(
                    "error",
                    "Error remoto desconocido",
                )
            )
        )

    rows = payload.get(
        "rows",
        [],
    )

    if not isinstance(rows, list):
        raise RuntimeError(
            "La respuesta remota no contiene "
            "una lista de filas"
        )

    return rows


def normalize_row(
    *,
    row: dict[str, Any],
    station_key: str,
    station_config: dict[str, Any],
) -> dict[str, Any]:
    remote_id = row.get("id")

    if remote_id is None:
        raise RuntimeError(
            "Fila remota sin campo id"
        )

    station_id = (
        row.get("station_id")
        or station_config.get("station_id")
        or station_key
    )

    station_name = (
        row.get("station_name")
        or station_config.get("station_name")
        or station_id
    )

    radio_role = (
        row.get("radio_role")
        or station_config.get("radio_role")
    )

    source_db = (
        f"ssh://"
        f"{station_config['user']}"
        f"@{station_config['host']}"
        f"{station_config['remote_database']}"
    )

    return {
        "source_station_id": station_id,
        "source_local_id": int(remote_id),
        "source_db": source_db,

        "timestamp_utc": row.get(
            "timestamp_utc"
        ),
        "timestamp_local": row.get(
            "timestamp_local"
        ),

        "station_id": station_id,
        "station_name": station_name,
        "radio_role": radio_role,

        "t_s": row.get("t_s"),

        "temp_avg_C": row.get(
            "temp_avg_C"
        ),
        "temp_min_C": row.get(
            "temp_min_C"
        ),
        "temp_max_C": row.get(
            "temp_max_C"
        ),

        "hum_avg_pct": row.get(
            "hum_avg_pct"
        ),
        "hum_min_pct": row.get(
            "hum_min_pct"
        ),
        "hum_max_pct": row.get(
            "hum_max_pct"
        ),

        "pres_avg_hPa": row.get(
            "pres_avg_hPa"
        ),
        "dew_point_C": row.get(
            "dew_point_C"
        ),
        "vapor_pressure_hPa": row.get(
            "vapor_pressure_hPa"
        ),

        "rain_1min_mm": row.get(
            "rain_1min_mm"
        ),
        "rain_1h_mm": row.get(
            "rain_1h_mm"
        ),
        "rain_total_mm": row.get(
            "rain_total_mm"
        ),

        "pulses_delta": row.get(
            "pulses_delta"
        ),
        "pulses_total": row.get(
            "pulses_total"
        ),

        "bme_ok": row.get("bme_ok"),
        "rain_ok": row.get("rain_ok"),

        "wind_speed_ms": row.get(
            "wind_speed_ms"
        ),
        "wind_direction_deg": row.get(
            "wind_direction_deg"
        ),
        "wind_gust_ms": row.get(
            "wind_gust_ms"
        ),
        "wind_ok": row.get("wind_ok"),

        "firmware_version": row.get(
            "firmware_version"
        ),
        "firmware_build": row.get(
            "firmware_build"
        ),
        "device_id": row.get(
            "device_id"
        ),
    }


def insert_rows(
    conn: sqlite3.Connection,
    rows: list[dict[str, Any]],
) -> tuple[int, int]:
    if not rows:
        return 0, 0

    placeholders = ",".join(
        ["?"] * len(
            STATION_OBSERVATION_COLUMNS
        )
    )

    columns = ",".join(
        STATION_OBSERVATION_COLUMNS
    )

    sql = f"""
        INSERT OR IGNORE INTO station_observations (
            {columns}
        )
        VALUES (
            {placeholders}
        )
    """

    inserted = 0
    ignored = 0

    for row in rows:
        values = [
            row.get(column)
            for column
            in STATION_OBSERVATION_COLUMNS
        ]

        before = conn.total_changes

        conn.execute(
            sql,
            values,
        )

        after = conn.total_changes

        if after > before:
            inserted += 1
        else:
            ignored += 1

    conn.commit()

    return inserted, ignored


def check_remote_service(
    station_config: dict[str, Any],
    ssh_config: dict[str, Any],
) -> str | None:
    service_name = station_config.get(
        "expected_service"
    )

    if not service_name:
        return None

    host = str(
        station_config["host"]
    )

    user = str(
        station_config["user"]
    )

    port = int(
        station_config.get(
            "port",
            22,
        )
    )

    connect_timeout = int(
        ssh_config.get(
            "connect_timeout_seconds",
            15,
        )
    )

    command = [
        "ssh",
        "-p",
        str(port),
        "-o",
        "BatchMode=yes",
        "-o",
        f"ConnectTimeout={connect_timeout}",
        f"{user}@{host}",
        "systemctl",
        "is-active",
        str(service_name),
    ]

    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=connect_timeout + 10,
        check=False,
    )

    return process.stdout.strip() or None


def synchronize_station(
    *,
    conn: sqlite3.Connection,
    station_key: str,
    station_config: dict[str, Any],
    ssh_config: dict[str, Any],
    sync_config: dict[str, Any],
) -> dict[str, Any]:
    station_id = str(
        station_config.get(
            "station_id",
            station_key,
        )
    )

    remote_host = str(
        station_config["host"]
    )

    remote_database = str(
        station_config["remote_database"]
    )

    batch_size = int(
        sync_config.get(
            "batch_size",
            500,
        )
    )

    max_batches = int(
        sync_config.get(
            "max_batches_per_run",
            20,
        )
    )

    started_utc = utc_now_iso()

    last_id = get_last_synced_id(
        conn,
        station_id,
    )

    total_received = 0
    total_inserted = 0
    total_ignored = 0

    last_timestamp = None

    print("--------------------------------------")
    print(f"Estación remota : {station_id}")
    print(f"Host             : {remote_host}")
    print(f"Base remota      : {remote_database}")
    print(f"Último id local  : {last_id}")

    try:
        service_status = check_remote_service(
            station_config,
            ssh_config,
        )

        if service_status:
            print(
                f"Servicio remoto  : "
                f"{service_status}"
            )

        for batch_number in range(
            1,
            max_batches + 1,
        ):
            remote_rows = fetch_remote_rows(
                station_config=station_config,
                last_id=last_id,
                batch_size=batch_size,
                ssh_config=ssh_config,
            )

            received = len(remote_rows)

            if received == 0:
                break

            normalized_rows = [
                normalize_row(
                    row=row,
                    station_key=station_key,
                    station_config=station_config,
                )
                for row in remote_rows
            ]

            inserted, ignored = insert_rows(
                conn,
                normalized_rows,
            )

            total_received += received
            total_inserted += inserted
            total_ignored += ignored

            last_remote_row = remote_rows[-1]

            last_id = int(
                last_remote_row["id"]
            )

            last_timestamp = (
                last_remote_row.get(
                    "timestamp_local"
                )
            )

            print(
                f"Lote {batch_number}: "
                f"recibidos={received}, "
                f"insertados={inserted}, "
                f"ignorados={ignored}, "
                f"último_id={last_id}"
            )

            update_sync_state(
                conn,
                station_id=station_id,
                remote_host=remote_host,
                remote_database=remote_database,
                last_source_local_id=last_id,
                last_remote_timestamp=last_timestamp,
                started_utc=started_utc,
                completed_utc=None,
                status="RUNNING",
                error=None,
                rows_received=total_received,
                rows_inserted=total_inserted,
                rows_ignored=total_ignored,
            )

            if received < batch_size:
                break

        completed_utc = utc_now_iso()

        update_sync_state(
            conn,
            station_id=station_id,
            remote_host=remote_host,
            remote_database=remote_database,
            last_source_local_id=last_id,
            last_remote_timestamp=last_timestamp,
            started_utc=started_utc,
            completed_utc=completed_utc,
            status="OK",
            error=None,
            rows_received=total_received,
            rows_inserted=total_inserted,
            rows_ignored=total_ignored,
        )

        print(
            f"Sincronización OK: "
            f"recibidos={total_received}, "
            f"insertados={total_inserted}, "
            f"ignorados={total_ignored}"
        )

        return {
            "station_id": station_id,
            "status": "OK",
            "received": total_received,
            "inserted": total_inserted,
            "ignored": total_ignored,
            "last_id": last_id,
        }

    except Exception as exc:
        completed_utc = utc_now_iso()
        error_message = str(exc)

        update_sync_state(
            conn,
            station_id=station_id,
            remote_host=remote_host,
            remote_database=remote_database,
            last_source_local_id=last_id,
            last_remote_timestamp=last_timestamp,
            started_utc=started_utc,
            completed_utc=completed_utc,
            status="ERROR",
            error=error_message,
            rows_received=total_received,
            rows_inserted=total_inserted,
            rows_ignored=total_ignored,
        )

        print(
            f"ERROR {station_id}: "
            f"{error_message}"
        )

        return {
            "station_id": station_id,
            "status": "ERROR",
            "error": error_message,
            "received": total_received,
            "inserted": total_inserted,
            "ignored": total_ignored,
            "last_id": last_id,
        }


def main() -> int:
    config = load_configuration()

    remote_sync_config = config[
        "remote_sync"
    ]

    if not bool(
        remote_sync_config.get(
            "enabled",
            True,
        )
    ):
        print(
            "La sincronización remota está "
            "deshabilitada."
        )
        return 0

    central_database = resolve_project_path(
        str(
            remote_sync_config[
                "central_database"
            ]
        )
    )

    central_database.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ssh_config = remote_sync_config.get(
        "ssh",
        {},
    )

    synchronization_config = (
        remote_sync_config.get(
            "synchronization",
            {},
        )
    )

    stations = config.get(
        "stations",
        {},
    )

    print("======================================")
    print(" AtmosLink Remote Station Synchronizer")
    print("======================================")
    print(f"Configuración : {CONFIG_FILE}")
    print(f"Base central : {central_database}")

    connection = sqlite3.connect(
        central_database,
        timeout=30,
    )

    try:
        connection.execute(
            "PRAGMA journal_mode=WAL"
        )
        connection.execute(
            "PRAGMA busy_timeout=30000"
        )

        ensure_central_schema(
            connection
        )

        results = []

        for station_key, station_config in stations.items():
            if not bool(
                station_config.get(
                    "enabled",
                    True,
                )
            ):
                print(
                    f"Estación deshabilitada: "
                    f"{station_key}"
                )
                continue

            result = synchronize_station(
                conn=connection,
                station_key=station_key,
                station_config=station_config,
                ssh_config=ssh_config,
                sync_config=synchronization_config,
            )

            results.append(result)

    finally:
        connection.close()

    errors = [
        result
        for result in results
        if result.get("status") != "OK"
    ]

    print("======================================")
    print(" Resumen de sincronización")
    print("======================================")

    for result in results:
        print(
            f"{result.get('station_id')} | "
            f"{result.get('status')} | "
            f"recibidos={result.get('received', 0)} | "
            f"insertados={result.get('inserted', 0)} | "
            f"ignorados={result.get('ignored', 0)} | "
            f"último_id={result.get('last_id', 0)}"
        )

    if errors:
        print("Status global: ERROR")
        return 1

    print("Status global: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
