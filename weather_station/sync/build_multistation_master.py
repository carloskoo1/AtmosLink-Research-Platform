"""
AtmosLink Research Platform
Multi-Station Scientific Master Dataset Builder

Construye:

    master_observations_multistation

Fuentes:

    master_observations
        CU01 con meteorología local y telemetría RF ya consolidada.

    station_observations
        Estaciones remotas, actualmente SJ01.

    era5_land_hourly
        ERA5-Land horario para cada punto del corredor.

    nasa_power_hourly
        NASA POWER horario para cada punto del corredor.

Reglas científicas:

    CU01 -> AP_CUNACALES
    SJ01 -> SM_SAN_JOSE

    MID_LINK se reserva exclusivamente para el análisis espacial
    del corredor; no se asigna como fuente local de una estación.

La asociación atmosférica se realiza mediante:

    station_id
    + site_tag configurado
    + bucket_hour UTC

El constructor conserva la telemetría RF existente de CU01 y no
asigna telemetría RF de CU01 a las estaciones remotas.
"""

from __future__ import annotations

import math
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from weather_station.config.station_manager import get_station_context


PROJECT_ROOT = Path(__file__).resolve().parents[2]

STATION_CONTEXT = get_station_context()

DB_FILE = PROJECT_ROOT / Path(
    STATION_CONTEXT.get(
        "database",
        "SQLite/CU01/weather_local.db",
    )
)

OUTPUT_TABLE = "master_observations_multistation"

OUTPUT_CSV = (
    PROJECT_ROOT
    / "Data"
    / "exports"
    / "master_observations_multistation.csv"
)


# ==========================================================
# MAPEO CIENTÍFICO ESTACIÓN -> PUNTO ATMOSFÉRICO
# ==========================================================

SITE_MAPPING: dict[str, dict[str, str]] = {
    "CU01": {
        "era5": "AP_CUNACALES",
        "nasa": "AP_CUNACALES",
    },
    "SJ01": {
        "era5": "SM_SAN_JOSE",
        "nasa": "SM_SAN_JOSE",
    },
}


# ==========================================================
# CAMPOS
# ==========================================================

REMOTE_SOURCE_COLUMNS = [
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
    "wind_speed_ms",
    "wind_direction_deg",
    "wind_gust_ms",
    "bme_ok",
    "rain_ok",
    "wind_ok",
    "firmware_version",
    "firmware_build",
    "device_id",
]


REMOTE_WEATHER_RENAME = {
    "timestamp_utc": "weather_timestamp_utc",
    "timestamp_local": "weather_timestamp_local",
    "temp_avg_C": "local_temp_avg_c",
    "temp_min_C": "local_temp_min_c",
    "temp_max_C": "local_temp_max_c",
    "hum_avg_pct": "local_hum_avg_pct",
    "hum_min_pct": "local_hum_min_pct",
    "hum_max_pct": "local_hum_max_pct",
    "pres_avg_hPa": "local_press_hpa",
    "dew_point_C": "local_dew_point_c",
    "vapor_pressure_hPa": "local_vapor_pressure_hpa",
    "rain_1min_mm": "local_rain_1min_mm",
    "rain_1h_mm": "local_rain_1h_mm",
    "rain_total_mm": "local_rain_total_mm",
    "pulses_delta": "local_pulses_delta",
    "pulses_total": "local_pulses_total",
    "wind_speed_ms": "local_wind_speed_ms",
    "wind_direction_deg": "local_wind_direction_deg",
    "wind_gust_ms": "local_wind_gust_ms",
    "bme_ok": "local_bme_ok",
    "rain_ok": "local_rain_ok",
    "wind_ok": "local_wind_ok",
}


RADIO_COLUMNS = [
    "radio_station_id",
    "radio_station_name",
    "radio_role_from_radio",
    "radio_local_role",
    "radio_timestamp_utc",
    "radio_timestamp_local",
    "radio_mcs_dl",
    "radio_mcs_ul",
    "radio_snr_dl",
    "radio_snr_ul",
    "radio_rssi_c0p",
    "radio_rssi_c0e",
    "radio_rssi_c1p",
    "radio_rssi_c1e",
    "radio_dl_rate",
    "radio_ul_rate",
    "radio_sta_dl_rssi",
    "radio_sta_ul_rssi",
    "radio_note",
    "radio_error",
]


ERA5_OUTPUT_COLUMNS = [
    "era5_timestamp_utc",
    "era5_timestamp_local",
    "era5_site_tag",
    "era5_lat",
    "era5_lon",
    "era5_temp_c",
    "era5_dewpoint_c",
    "era5_rh_pct",
    "era5_precip_mm",
    "era5_press_hpa",
    "era5_wind_ms",
]


NASA_OUTPUT_COLUMNS = [
    "nasa_timestamp_utc",
    "nasa_timestamp_local",
    "nasa_site_tag",
    "nasa_lat",
    "nasa_lon",
    "nasa_temp_c",
    "nasa_dewpoint_c",
    "nasa_rh_pct",
    "nasa_precip_mm",
    "nasa_press_kpa",
    "nasa_press_hpa",
    "nasa_wind10m_ms",
    "nasa_source",
    "nasa_downloaded_at_utc",
]


# ==========================================================
# UTILIDADES SQLITE
# ==========================================================

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


def read_table(
    conn: sqlite3.Connection,
    table_name: str,
) -> pd.DataFrame:
    if not table_exists(conn, table_name):
        print(
            f"AVISO: no existe la tabla {table_name}"
        )
        return pd.DataFrame()

    return pd.read_sql_query(
        f"SELECT * FROM {table_name}",
        conn,
    )


# ==========================================================
# UTILIDADES TEMPORALES
# ==========================================================

def normalize_datetime_series(
    values: pd.Series,
) -> pd.Series:
    return pd.to_datetime(
        values,
        errors="coerce",
        utc=True,
    )


def ensure_time_buckets(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    result = dataframe.copy()

    timestamp_source = None

    for candidate in (
        "bucket_minute",
        "weather_timestamp_local",
        "timestamp_local",
        "master_timestamp_local",
    ):
        if candidate in result.columns:
            timestamp_source = candidate
            break

    if timestamp_source is None:
        raise RuntimeError(
            "No existe una columna temporal utilizable."
        )

    timestamps = normalize_datetime_series(
        result[timestamp_source]
    )

    valid = timestamps.notna()

    result = result.loc[valid].copy()
    timestamps = timestamps.loc[valid]

    result["bucket_minute"] = (
        timestamps.dt.floor("min")
    )

    result["bucket_hour"] = (
        timestamps.dt.floor("h")
    )

    return result


# ==========================================================
# HUMEDAD RELATIVA ERA5
# ==========================================================

def calculate_relative_humidity(
    temperature_c: Any,
    dewpoint_c: Any,
) -> float | None:
    """
    Calcula humedad relativa mediante la aproximación de Magnus.
    """

    try:
        temperature = float(temperature_c)
        dewpoint = float(dewpoint_c)
    except (TypeError, ValueError):
        return None

    if (
        not math.isfinite(temperature)
        or not math.isfinite(dewpoint)
    ):
        return None

    try:
        numerator = math.exp(
            (17.625 * dewpoint)
            / (243.04 + dewpoint)
        )

        denominator = math.exp(
            (17.625 * temperature)
            / (243.04 + temperature)
        )

        rh = 100.0 * numerator / denominator

        return round(
            max(0.0, min(100.0, rh)),
            3,
        )

    except (
        OverflowError,
        ZeroDivisionError,
    ):
        return None


# ==========================================================
# PREPARAR CU01
# ==========================================================

def prepare_existing_master(
    master_df: pd.DataFrame,
) -> pd.DataFrame:
    if master_df.empty:
        return master_df

    result = master_df.copy()

    if "station_id" not in result.columns:
        result["station_id"] = "CU01"

    result["station_id"] = (
        result["station_id"]
        .fillna("CU01")
        .astype(str)
        .str.upper()
    )

    result = ensure_time_buckets(result)

    result["source_kind"] = (
        "EXISTING_MASTER"
    )

    result["source_station_id"] = (
        result["station_id"]
    )

    if "source_local_id" not in result.columns:
        result["source_local_id"] = None

    if "source_db" not in result.columns:
        result["source_db"] = str(DB_FILE)

    for column in (
        "firmware_version",
        "firmware_build",
        "device_id",
    ):
        if column not in result.columns:
            result[column] = None

    return result


# ==========================================================
# PREPARAR ESTACIONES REMOTAS
# ==========================================================

def prepare_remote_weather(
    station_df: pd.DataFrame,
) -> pd.DataFrame:
    if station_df.empty:
        return station_df

    available_columns = [
        column
        for column in REMOTE_SOURCE_COLUMNS
        if column in station_df.columns
    ]

    result = station_df[
        available_columns
    ].copy()

    if "source_station_id" in result.columns:
        selector = (
            result["source_station_id"]
            .fillna("")
            .astype(str)
            .str.upper()
        )
    elif "station_id" in result.columns:
        selector = (
            result["station_id"]
            .fillna("")
            .astype(str)
            .str.upper()
        )
    else:
        raise RuntimeError(
            "station_observations no contiene station_id."
        )

    # CU01 ya se toma de master_observations.
    result = result[
        selector != "CU01"
    ].copy()

    if result.empty:
        return result

    result = result.rename(
        columns=REMOTE_WEATHER_RENAME
    )

    if "station_id" not in result.columns:
        result["station_id"] = (
            result["source_station_id"]
        )

    result["station_id"] = (
        result["station_id"]
        .fillna(result["source_station_id"])
        .astype(str)
        .str.upper()
    )

    if "station_name" not in result.columns:
        result["station_name"] = (
            result["station_id"]
        )

    if "radio_role" not in result.columns:
        result["radio_role"] = None

    result = ensure_time_buckets(result)

    result["master_timestamp_local"] = (
        result["weather_timestamp_local"]
    )

    result["master_timestamp_hour"] = (
        result["bucket_hour"]
    )

    result["source_kind"] = (
        "REMOTE_STATION_WEATHER"
    )

    # Una estación remota no hereda radio de CU01.
    for column in RADIO_COLUMNS:
        if column not in result.columns:
            result[column] = None

    result = result.sort_values(
        [
            "station_id",
            "bucket_minute",
            "source_local_id",
        ]
    )

    result = result.drop_duplicates(
        subset=[
            "station_id",
            "bucket_minute",
        ],
        keep="last",
    )

    return result


# ==========================================================
# PREPARAR ERA5
# ==========================================================

def prepare_era5(
    era5_df: pd.DataFrame,
) -> pd.DataFrame:
    if era5_df.empty:
        return era5_df

    result = era5_df.copy()

    result["site_tag"] = (
        result["site_tag"]
        .fillna("")
        .astype(str)
        .str.upper()
    )

    result["source_hour"] = (
        normalize_datetime_series(
            result["timestamp_local"]
        ).dt.floor("h")
    )

    result = result[
        result["source_hour"].notna()
    ].copy()

    result["rh_pct"] = result.apply(
        lambda row: calculate_relative_humidity(
            row.get("temp_c"),
            row.get("dewpoint_c"),
        ),
        axis=1,
    )

    result = result.sort_values(
        [
            "site_tag",
            "source_hour",
            "id",
        ]
    )

    result = result.drop_duplicates(
        subset=[
            "site_tag",
            "source_hour",
        ],
        keep="last",
    )

    result = result.rename(
        columns={
            "timestamp_utc": "era5_timestamp_utc",
            "timestamp_local": "era5_timestamp_local",
            "site_tag": "era5_site_tag",
            "lat": "era5_lat",
            "lon": "era5_lon",
            "temp_c": "era5_temp_c",
            "dewpoint_c": "era5_dewpoint_c",
            "rh_pct": "era5_rh_pct",
            "precip_mm": "era5_precip_mm",
            "press_hpa": "era5_press_hpa",
            "wind_ms": "era5_wind_ms",
        }
    )

    return result[
        [
            "source_hour",
            *ERA5_OUTPUT_COLUMNS,
        ]
    ]


# ==========================================================
# PREPARAR NASA POWER
# ==========================================================

def prepare_nasa(
    nasa_df: pd.DataFrame,
) -> pd.DataFrame:
    if nasa_df.empty:
        return nasa_df

    result = nasa_df.copy()

    result["site_tag"] = (
        result["site_tag"]
        .fillna("")
        .astype(str)
        .str.upper()
    )

    result["source_hour"] = (
        normalize_datetime_series(
            result["timestamp_local"]
        ).dt.floor("h")
    )

    result = result[
        result["source_hour"].notna()
    ].copy()

    result = result.sort_values(
        [
            "site_tag",
            "source_hour",
            "id",
        ]
    )

    result = result.drop_duplicates(
        subset=[
            "site_tag",
            "source_hour",
        ],
        keep="last",
    )

    result = result.rename(
        columns={
            "timestamp_utc": "nasa_timestamp_utc",
            "timestamp_local": "nasa_timestamp_local",
            "site_tag": "nasa_site_tag",
            "lat": "nasa_lat",
            "lon": "nasa_lon",
            "temp_c": "nasa_temp_c",
            "dewpoint_c": "nasa_dewpoint_c",
            "rh_pct": "nasa_rh_pct",
            "precip_mm": "nasa_precip_mm",
            "press_kpa": "nasa_press_kpa",
            "press_hpa": "nasa_press_hpa",
            "wind10m_ms": "nasa_wind10m_ms",
            "source": "nasa_source",
            "downloaded_at_utc": (
                "nasa_downloaded_at_utc"
            ),
        }
    )

    return result[
        [
            "source_hour",
            *NASA_OUTPUT_COLUMNS,
        ]
    ]


# ==========================================================
# ASOCIACIÓN POR ESTACIÓN
# ==========================================================

def drop_atmospheric_columns(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    removable = [
        column
        for column in (
            ERA5_OUTPUT_COLUMNS
            + NASA_OUTPUT_COLUMNS
        )
        if column in dataframe.columns
    ]

    return dataframe.drop(
        columns=removable,
        errors="ignore",
    )


def attach_atmospheric_sources(
    observations: pd.DataFrame,
    era5_prepared: pd.DataFrame,
    nasa_prepared: pd.DataFrame,
) -> pd.DataFrame:
    if observations.empty:
        return observations

    base = drop_atmospheric_columns(
        observations
    )

    station_outputs: list[pd.DataFrame] = []

    for station_id, station_rows in base.groupby(
        "station_id",
        dropna=False,
    ):
        normalized_station_id = str(
            station_id
        ).upper()

        mapping = SITE_MAPPING.get(
            normalized_station_id
        )

        station_part = station_rows.copy()

        if mapping is None:
            print(
                "AVISO: estación sin SITE_MAPPING: "
                f"{normalized_station_id}"
            )

            for column in (
                ERA5_OUTPUT_COLUMNS
                + NASA_OUTPUT_COLUMNS
            ):
                station_part[column] = None

            station_outputs.append(
                station_part
            )
            continue

        era5_site = mapping.get("era5")
        nasa_site = mapping.get("nasa")

        # ---------------- ERA5 ----------------

        if (
            not era5_prepared.empty
            and era5_site
        ):
            era5_site_rows = era5_prepared[
                era5_prepared["era5_site_tag"]
                == era5_site
            ].copy()

            if era5_site_rows.empty:
                print(
                    "AVISO: ERA5 sin datos para "
                    f"{normalized_station_id} "
                    f"({era5_site})"
                )

            station_part = station_part.merge(
                era5_site_rows,
                how="left",
                left_on="bucket_hour",
                right_on="source_hour",
            )

            station_part = station_part.drop(
                columns=["source_hour"],
                errors="ignore",
            )

        else:
            for column in ERA5_OUTPUT_COLUMNS:
                station_part[column] = None

        # ---------------- NASA ----------------

        if (
            not nasa_prepared.empty
            and nasa_site
        ):
            nasa_site_rows = nasa_prepared[
                nasa_prepared["nasa_site_tag"]
                == nasa_site
            ].copy()

            if nasa_site_rows.empty:
                print(
                    "AVISO: NASA sin datos para "
                    f"{normalized_station_id} "
                    f"({nasa_site})"
                )

            station_part = station_part.merge(
                nasa_site_rows,
                how="left",
                left_on="bucket_hour",
                right_on="source_hour",
            )

            station_part = station_part.drop(
                columns=["source_hour"],
                errors="ignore",
            )

        else:
            for column in NASA_OUTPUT_COLUMNS:
                station_part[column] = None

        station_outputs.append(
            station_part
        )

    if not station_outputs:
        return base

    return pd.concat(
        station_outputs,
        ignore_index=True,
        sort=False,
    )


# ==========================================================
# ALINEACIÓN DE ESQUEMAS
# ==========================================================

def align_columns(
    first: pd.DataFrame,
    second: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    ordered_columns = list(first.columns)

    for column in second.columns:
        if column not in ordered_columns:
            ordered_columns.append(column)

    for column in ordered_columns:
        if column not in first.columns:
            first[column] = None

        if column not in second.columns:
            second[column] = None

    return (
        first[ordered_columns],
        second[ordered_columns],
    )


# ==========================================================
# SERIALIZACIÓN SQLITE
# ==========================================================

def serialize_datetime_columns(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    result = dataframe.copy()

    for column in result.columns:
        series = result[column]

        if pd.api.types.is_datetime64_any_dtype(
            series
        ):
            result[column] = series.map(
                lambda value: (
                    value.isoformat()
                    if pd.notna(value)
                    else None
                )
            )
            continue

        if series.dtype != "object":
            continue

        contains_timestamp = series.map(
            lambda value: isinstance(
                value,
                pd.Timestamp,
            )
        ).any()

        if contains_timestamp:
            result[column] = series.map(
                lambda value: (
                    value.isoformat()
                    if isinstance(
                        value,
                        pd.Timestamp,
                    )
                    else value
                )
            )

    result = result.where(
        pd.notna(result),
        None,
    )

    return result


# ==========================================================
# VALIDACIÓN
# ==========================================================

def validate_output(
    output: pd.DataFrame,
) -> None:
    required = [
        "station_id",
        "bucket_minute",
        "bucket_hour",
        "local_temp_avg_c",
        "local_hum_avg_pct",
        "local_press_hpa",
    ]

    missing = [
        column
        for column in required
        if column not in output.columns
    ]

    if missing:
        raise RuntimeError(
            "Columnas obligatorias ausentes: "
            + ", ".join(missing)
        )

    duplicated = output.duplicated(
        subset=[
            "station_id",
            "bucket_minute",
        ]
    )

    if duplicated.any():
        duplicate_count = int(
            duplicated.sum()
        )

        raise RuntimeError(
            "Existen duplicados "
            "station_id + bucket_minute: "
            f"{duplicate_count}"
        )


def print_source_summary(
    output: pd.DataFrame,
) -> None:
    print(
        "Asociación atmosférica por estación:"
    )

    for station_id, group in output.groupby(
        "station_id"
    ):
        total = len(group)

        era5_count = (
            group["era5_timestamp_local"]
            .notna()
            .sum()
            if "era5_timestamp_local"
            in group.columns
            else 0
        )

        nasa_count = (
            group["nasa_timestamp_local"]
            .notna()
            .sum()
            if "nasa_timestamp_local"
            in group.columns
            else 0
        )

        era5_tags = sorted(
            {
                str(value)
                for value in group.get(
                    "era5_site_tag",
                    pd.Series(dtype=object),
                ).dropna()
            }
        )

        nasa_tags = sorted(
            {
                str(value)
                for value in group.get(
                    "nasa_site_tag",
                    pd.Series(dtype=object),
                ).dropna()
            }
        )

        print(
            f"  {station_id} | "
            f"total={total} | "
            f"ERA5={era5_count} "
            f"{era5_tags} | "
            f"NASA={nasa_count} "
            f"{nasa_tags}"
        )


# ==========================================================
# CONSTRUCTOR PRINCIPAL
# ==========================================================

def build_multistation_master() -> int:
    if not DB_FILE.exists():
        raise FileNotFoundError(
            f"No existe la base central: {DB_FILE}"
        )

    print(
        "======================================"
    )
    print(
        " AtmosLink Multi-station Master Builder"
    )
    print(
        "======================================"
    )
    print(
        f"Base central : {DB_FILE}"
    )

    connection = sqlite3.connect(
        DB_FILE,
        timeout=60,
    )

    connection.execute(
        "PRAGMA busy_timeout=60000"
    )

    connection.execute(
        "PRAGMA journal_mode=WAL"
    )

    try:
        existing_master = read_table(
            connection,
            "master_observations",
        )

        station_observations = read_table(
            connection,
            "station_observations",
        )

        era5_raw = read_table(
            connection,
            "era5_land_hourly",
        )

        nasa_raw = read_table(
            connection,
            "nasa_power_hourly",
        )

        if existing_master.empty:
            raise RuntimeError(
                "master_observations está vacía."
            )

        local_master = prepare_existing_master(
            existing_master
        )

        remote_master = prepare_remote_weather(
            station_observations
        )

        era5_prepared = prepare_era5(
            era5_raw
        )

        nasa_prepared = prepare_nasa(
            nasa_raw
        )

        local_master = attach_atmospheric_sources(
            local_master,
            era5_prepared,
            nasa_prepared,
        )

        if remote_master.empty:
            output = local_master.copy()

        else:
            remote_master = (
                attach_atmospheric_sources(
                    remote_master,
                    era5_prepared,
                    nasa_prepared,
                )
            )

            (
                local_master,
                remote_master,
            ) = align_columns(
                local_master,
                remote_master,
            )

            output = pd.concat(
                [
                    local_master,
                    remote_master,
                ],
                ignore_index=True,
                sort=False,
            )

        output = output.sort_values(
            [
                "station_id",
                "bucket_minute",
            ]
        )

        output = output.drop_duplicates(
            subset=[
                "station_id",
                "bucket_minute",
            ],
            keep="last",
        )

        validate_output(output)

        print_source_summary(output)

        output_sql = serialize_datetime_columns(
            output
        )

        # Publicación atómica del master multiestación.
        #
        # El DataFrame se escribe primero en una tabla temporal.
        # La tabla activa se sustituye después mediante una
        # transacción corta, evitando que las APIs observen una
        # tabla inexistente o parcialmente cargada.
        temporary_table = (
            f"{OUTPUT_TABLE}_new"
        )

        previous_table = (
            f"{OUTPUT_TABLE}_old"
        )

        output_sql.to_sql(
            temporary_table,
            connection,
            if_exists="replace",
            index=False,
            chunksize=1000,
        )

        try:
            connection.execute(
                "BEGIN IMMEDIATE"
            )

            connection.execute(
                f'DROP TABLE IF EXISTS '
                f'"{previous_table}"'
            )

            if table_exists(
                connection,
                OUTPUT_TABLE,
            ):
                connection.execute(
                    f'ALTER TABLE '
                    f'"{OUTPUT_TABLE}" '
                    f'RENAME TO '
                    f'"{previous_table}"'
                )

            connection.execute(
                f'ALTER TABLE '
                f'"{temporary_table}" '
                f'RENAME TO '
                f'"{OUTPUT_TABLE}"'
            )

            connection.execute(
                f'DROP TABLE IF EXISTS '
                f'"{previous_table}"'
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

    finally:
        connection.close()

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_sql.to_csv(
        OUTPUT_CSV,
        index=False,
    )

    print(
        "--------------------------------------"
    )
    print(
        "MASTER MULTIESTACIÓN generado"
    )
    print(
        f"Tabla  : {OUTPUT_TABLE}"
    )
    print(
        f"CSV    : {OUTPUT_CSV}"
    )
    print(
        f"Filas  : {len(output_sql)}"
    )

    summary = (
        output.groupby("station_id")
        .agg(
            registros=(
                "station_id",
                "size",
            ),
            primer_registro=(
                "bucket_minute",
                "min",
            ),
            ultimo_registro=(
                "bucket_minute",
                "max",
            ),
        )
        .reset_index()
    )

    print(
        "Resumen por estación:"
    )

    for row in summary.itertuples(
        index=False
    ):
        print(
            f"  {row.station_id} | "
            f"registros={row.registros} | "
            f"primero={row.primer_registro} | "
            f"último={row.ultimo_registro}"
        )

    print("Status: OK")
    print(
        "======================================"
    )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(
            build_multistation_master()
        )

    except Exception as exc:
        print(
            f"ERROR: {type(exc).__name__}: {exc}"
        )
        raise
