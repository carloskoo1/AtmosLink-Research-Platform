from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import pandas as pd


CAMPAIGN_ID = "CAMPAIGN_6G_20260831"
CAMPAIGN_START_LOCAL = pd.Timestamp("2026-08-31T16:00:00-05:00")
LINK_ID = "LINK_6G_4600C"
FREQUENCY_BAND = "6_GHZ"
OBS_TABLE = "scientific_campaign_observations"
LINK_TABLE = "scientific_campaign_6g_integrated"


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone() is not None


def read_table(connection: sqlite3.Connection, table_name: str) -> pd.DataFrame:
    if not table_exists(connection, table_name):
        raise RuntimeError(f"No existe la tabla obligatoria: {table_name}")
    return pd.read_sql_query(f'SELECT * FROM "{table_name}"', connection)


def parse_utc(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, errors="coerce", utc=True)


def add_campaign_classification(observations: pd.DataFrame) -> pd.DataFrame:
    result = observations.copy()
    station = result["station_id"].fillna("").astype(str).str.upper()
    timestamps = parse_utc(result["bucket_minute"])
    cutoff_utc = CAMPAIGN_START_LOCAL.tz_convert("UTC")

    result.insert(0, "campaign_id", CAMPAIGN_ID)
    result.insert(1, "campaign_start_local", CAMPAIGN_START_LOCAL.isoformat())
    result.insert(2, "deployment_phase", "UNCLASSIFIED")
    result.insert(3, "field_analysis_valid", 0)
    result.insert(4, "deployment_note", "Registro fuera de las reglas conocidas de campaña.")

    cu_baseline = (station == "CU01") & (timestamps < cutoff_utc)
    sj_laboratory = (station == "SJ01") & (timestamps < cutoff_utc)
    field_operation = station.isin(["CU01", "SJ01"]) & (timestamps >= cutoff_utc)

    result.loc[cu_baseline, "deployment_phase"] = "FIELD_BASELINE_CU01"
    result.loc[cu_baseline, "deployment_note"] = (
        "Medición real de Cuñacales anterior a la campaña integrada de 6 GHz."
    )
    result.loc[sj_laboratory, "deployment_phase"] = "LABORATORY_TEST"
    result.loc[sj_laboratory, "deployment_note"] = (
        "Prueba de laboratorio de SJ01; no representa Cerro San José."
    )
    result.loc[field_operation, "deployment_phase"] = "FIELD_OPERATION"
    result.loc[field_operation, "field_analysis_valid"] = 1
    result.loc[field_operation, "deployment_note"] = (
        "Medición de campo posterior al despliegue definitivo de SJ01."
    )

    result["campaign_timestamp_utc"] = timestamps.map(
        lambda value: value.isoformat() if pd.notna(value) else None
    )
    return result


def prepare_station_weather(
    observations: pd.DataFrame,
    station_id: str,
    prefix: str,
) -> pd.DataFrame:
    station = observations[
        observations["station_id"].fillna("").astype(str).str.upper() == station_id
    ].copy()
    station["match_time_utc"] = parse_utc(station["bucket_minute"])
    station = station.dropna(subset=["match_time_utc"])
    station = station.sort_values("match_time_utc").drop_duplicates(
        subset=["match_time_utc"], keep="last"
    )

    keep = [
        "match_time_utc",
        "bucket_minute",
        "weather_timestamp_utc",
        "weather_timestamp_local",
        "local_temp_avg_c",
        "local_temp_min_c",
        "local_temp_max_c",
        "local_hum_avg_pct",
        "local_hum_min_pct",
        "local_hum_max_pct",
        "local_press_hpa",
        "local_dew_point_c",
        "local_vapor_pressure_hpa",
        "local_rain_1min_mm",
        "local_rain_1h_mm",
        "local_rain_total_mm",
        "local_pulses_delta",
        "local_pulses_total",
        "local_wind_speed_ms",
        "local_wind_direction_deg",
        "local_wind_gust_ms",
        "local_wind_ok",
        "local_bme_ok",
        "local_rain_ok",
        "era5_timestamp_utc",
        "era5_timestamp_local",
        "era5_site_tag",
        "era5_temp_c",
        "era5_dewpoint_c",
        "era5_rh_pct",
        "era5_precip_mm",
        "era5_press_hpa",
        "era5_wind_ms",
        "nasa_timestamp_utc",
        "nasa_timestamp_local",
        "nasa_site_tag",
        "nasa_temp_c",
        "nasa_dewpoint_c",
        "nasa_rh_pct",
        "nasa_precip_mm",
        "nasa_press_hpa",
        "nasa_wind10m_ms",
    ]
    keep = [column for column in keep if column in station.columns]
    station = station[keep].copy()
    return station.rename(
        columns={column: f"{prefix}{column}" for column in station.columns if column != "match_time_utc"}
    )


def build_integrated_link(
    observations: pd.DataFrame,
    telemetry: pd.DataFrame,
) -> pd.DataFrame:
    link = telemetry[
        (telemetry["link_id"] == LINK_ID)
        & (telemetry["frequency_band"] == FREQUENCY_BAND)
    ].copy()
    link["rf_timestamp_utc_parsed"] = parse_utc(link["timestamp_utc"])
    cutoff_utc = CAMPAIGN_START_LOCAL.tz_convert("UTC")
    link = link[
        link["rf_timestamp_utc_parsed"].notna()
        & (link["rf_timestamp_utc_parsed"] >= cutoff_utc)
    ].sort_values("rf_timestamp_utc_parsed")

    if link.empty:
        raise RuntimeError("No hay telemetría detallada válida de LINK_6G_4600C.")

    link = link.rename(
        columns={
            "timestamp_utc": "rf_timestamp_utc",
            "timestamp_local": "rf_timestamp_local",
            "dl_rate_mbps": "reported_dl_link_rate_mbps",
            "ul_rate_mbps": "reported_ul_link_rate_mbps",
        }
    )

    cu01 = prepare_station_weather(observations, "CU01", "cu01_")
    sj01 = prepare_station_weather(observations, "SJ01", "sj01_")

    result = pd.merge_asof(
        link,
        cu01,
        left_on="rf_timestamp_utc_parsed",
        right_on="match_time_utc",
        direction="nearest",
        tolerance=pd.Timedelta(minutes=2),
    ).drop(columns=["match_time_utc"], errors="ignore")
    result = pd.merge_asof(
        result.sort_values("rf_timestamp_utc_parsed"),
        sj01,
        left_on="rf_timestamp_utc_parsed",
        right_on="match_time_utc",
        direction="nearest",
        tolerance=pd.Timedelta(minutes=2),
    ).drop(columns=["match_time_utc"], errors="ignore")

    result.insert(0, "campaign_id", CAMPAIGN_ID)
    result.insert(1, "deployment_phase", "FIELD_OPERATION")
    result.insert(2, "field_analysis_valid", 1)
    result.insert(3, "rate_metric_type", "CAMBIUM_REPORTED_LINK_RATE_NOT_ACTIVE_THROUGHPUT")
    result.insert(4, "active_throughput_measured", 0)
    result.insert(
        5,
        "ul_link_rate_available",
        result["reported_ul_link_rate_mbps"].notna().astype(int),
    )
    result["cu01_weather_match_delta_seconds"] = (
        result["rf_timestamp_utc_parsed"]
        - parse_utc(result.get("cu01_bucket_minute"))
    ).abs().dt.total_seconds()
    result["sj01_weather_match_delta_seconds"] = (
        result["rf_timestamp_utc_parsed"]
        - parse_utc(result.get("sj01_bucket_minute"))
    ).abs().dt.total_seconds()
    result["cu01_weather_matched"] = result.get("cu01_bucket_minute").notna().astype(int)
    result["sj01_weather_matched"] = result.get("sj01_bucket_minute").notna().astype(int)
    result["both_weather_stations_matched"] = (
        (result["cu01_weather_matched"] == 1)
        & (result["sj01_weather_matched"] == 1)
    ).astype(int)
    result["rf_timestamp_utc_parsed"] = result["rf_timestamp_utc_parsed"].map(
        lambda value: value.isoformat() if pd.notna(value) else None
    )
    return result


def atomic_publish_table(
    connection: sqlite3.Connection,
    table_name: str,
    dataframe: pd.DataFrame,
) -> None:
    temporary = f"{table_name}_new"
    previous = f"{table_name}_old"
    dataframe.to_sql(temporary, connection, if_exists="replace", index=False, chunksize=1000)
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute(f'DROP TABLE IF EXISTS "{previous}"')
        if table_exists(connection, table_name):
            connection.execute(f'ALTER TABLE "{table_name}" RENAME TO "{previous}"')
        connection.execute(f'ALTER TABLE "{temporary}" RENAME TO "{table_name}"')
        connection.execute(f'DROP TABLE IF EXISTS "{previous}"')
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def serializable(dataframe: pd.DataFrame) -> pd.DataFrame:
    result = dataframe.copy()
    for column in result.columns:
        if pd.api.types.is_datetime64_any_dtype(result[column]):
            result[column] = result[column].map(
                lambda value: value.isoformat() if pd.notna(value) else None
            )
    return result.where(pd.notna(result), None)


def write_atomic_csv(dataframe: pd.DataFrame, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    dataframe.to_csv(temporary, index=False)
    temporary.replace(destination)


def build(database: Path, output_dir: Path) -> dict[str, object]:
    connection = sqlite3.connect(database, timeout=60)
    connection.execute("PRAGMA busy_timeout=60000")
    try:
        observations = read_table(connection, "master_observations_multistation")
        telemetry = read_table(connection, "radio_link_config_telemetry")
        classified = serializable(add_campaign_classification(observations))
        integrated = serializable(build_integrated_link(observations, telemetry))
        atomic_publish_table(connection, OBS_TABLE, classified)
        atomic_publish_table(connection, LINK_TABLE, integrated)
    finally:
        connection.close()

    observations_csv = output_dir / "scientific_campaign_observations.csv"
    integrated_csv = output_dir / "scientific_campaign_6g_integrated.csv"
    write_atomic_csv(classified, observations_csv)
    write_atomic_csv(integrated, integrated_csv)

    summary = {
        "campaign_id": CAMPAIGN_ID,
        "campaign_start_local": CAMPAIGN_START_LOCAL.isoformat(),
        "classified_rows": len(classified),
        "integrated_6g_rows": len(integrated),
        "field_rows": int((classified["field_analysis_valid"] == 1).sum()),
        "laboratory_sj01_rows": int(
            (
                (classified["station_id"] == "SJ01")
                & (classified["deployment_phase"] == "LABORATORY_TEST")
            ).sum()
        ),
        "both_weather_matched": int(integrated["both_weather_stations_matched"].sum()),
        "ul_link_rate_available": int(integrated["ul_link_rate_available"].sum()),
        "active_throughput_measured": False,
        "outputs": [str(observations_csv), str(integrated_csv)],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    build(args.database, args.output_dir)


if __name__ == "__main__":
    main()
