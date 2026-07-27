"""
AtmosLink Scientific Propagation Pipeline V6.0.

The pipeline reads historical AtmosLink observations and writes derived
physical propagation results to an independent SQLite database.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from weather_station.propagation.atmospheric_inputs import (
    water_vapour_density_g_m3,
)
from weather_station.propagation.iturpy_adapter import (
    gaseous_attenuation_terrestrial,
    rain_specific_attenuation,
)
from weather_station.propagation.physics import (
    LinkBudget,
    free_space_path_loss_db,
    predicted_rssi_dbm,
    residual_db,
)
from weather_station.propagation.pipeline_schema import (
    initialize_database,
)
from weather_station.propagation.rain_inputs import (
    RainIntervalInput,
    RainProcessorConfiguration,
    process_rain_interval,
)
from weather_station.propagation.source_mapping import (
    SourceMapping,
    discover_mapping,
)


PIPELINE_VERSION = "6.0.0"


@dataclass(frozen=True)
class PipelineLinkConfiguration:
    link_id: str
    ap_station_id: str
    sm_station_id: str

    frequency_ghz: float
    path_distance_km: float

    tx_power_dbm: float
    ap_antenna_gain_dbi: float
    sm_antenna_gain_dbi: float

    ap_feeder_loss_db: float = 0.0
    sm_feeder_loss_db: float = 0.0

    polarization: str = "H"
    elevation_angle_deg: float = 0.0

    rain_interval_seconds: float = 60.0
    bucket_depth_mm: float = 0.279


@dataclass(frozen=True)
class PipelineStatistics:
    rows_read: int
    rows_calculated: int
    rows_written: int
    rows_skipped: int
    dry_run: bool


def utc_now_text() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_float(value: Any) -> float | None:
    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None

    return number


def safe_text(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def value_from_row(
    row: sqlite3.Row,
    column_name: str | None,
) -> Any:
    if column_name is None:
        return None

    return row[column_name]


def polarization_tilt_deg(polarization: str) -> float:
    normalized = polarization.strip().upper()

    if normalized == "H":
        return 0.0

    if normalized == "V":
        return 90.0

    if normalized in {"SLANT45", "45", "CIRCULAR"}:
        return 45.0

    raise ValueError(
        "polarization must be H, V, SLANT45, 45 or CIRCULAR"
    )


def register_link(
    connection: sqlite3.Connection,
    config: PipelineLinkConfiguration,
) -> None:
    connection.execute(
        """
        INSERT INTO propagation_link_registry (
            link_id,
            ap_station_id,
            sm_station_id,
            frequency_ghz,
            path_distance_km,
            tx_power_dbm,
            ap_antenna_gain_dbi,
            sm_antenna_gain_dbi,
            ap_feeder_loss_db,
            sm_feeder_loss_db,
            polarization,
            elevation_angle_deg,
            status,
            updated_at_utc
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
        ON CONFLICT(link_id) DO UPDATE SET
            ap_station_id = excluded.ap_station_id,
            sm_station_id = excluded.sm_station_id,
            frequency_ghz = excluded.frequency_ghz,
            path_distance_km = excluded.path_distance_km,
            tx_power_dbm = excluded.tx_power_dbm,
            ap_antenna_gain_dbi = excluded.ap_antenna_gain_dbi,
            sm_antenna_gain_dbi = excluded.sm_antenna_gain_dbi,
            ap_feeder_loss_db = excluded.ap_feeder_loss_db,
            sm_feeder_loss_db = excluded.sm_feeder_loss_db,
            polarization = excluded.polarization,
            elevation_angle_deg = excluded.elevation_angle_deg,
            updated_at_utc = excluded.updated_at_utc
        """,
        (
            config.link_id,
            config.ap_station_id,
            config.sm_station_id,
            config.frequency_ghz,
            config.path_distance_km,
            config.tx_power_dbm,
            config.ap_antenna_gain_dbi,
            config.sm_antenna_gain_dbi,
            config.ap_feeder_loss_db,
            config.sm_feeder_loss_db,
            config.polarization,
            config.elevation_angle_deg,
            utc_now_text(),
        ),
    )


def build_select_query(
    table_name: str,
    mapping: SourceMapping,
    limit: int | None,
) -> str:
    if mapping.timestamp_utc is None:
        raise RuntimeError(
            f"No UTC timestamp column was found in {table_name}"
        )

    query = (
        f'SELECT rowid AS _source_rowid, * '
        f'FROM "{table_name}" '
        f'WHERE "{mapping.timestamp_utc}" IS NOT NULL '
        f'ORDER BY "{mapping.timestamp_utc}"'
    )

    if limit is not None:
        query += f" LIMIT {int(limit)}"

    return query


def calculate_row(
    row: sqlite3.Row,
    mapping: SourceMapping,
    config: PipelineLinkConfiguration,
) -> dict[str, Any]:
    quality_flags: list[str] = []

    timestamp_utc = safe_text(
        value_from_row(row, mapping.timestamp_utc)
    )
    station_id = safe_text(
        value_from_row(row, mapping.station_id)
    )

    temperature_c = safe_float(
        value_from_row(row, mapping.temperature_c)
    )
    humidity_pct = safe_float(
        value_from_row(
            row,
            mapping.relative_humidity_pct,
        )
    )
    pressure_hpa = safe_float(
        value_from_row(row, mapping.pressure_hpa)
    )
    precipitation_mm = safe_float(
        value_from_row(row, mapping.rain_1min_mm)
    )
    observed_rssi_dbm = safe_float(
        value_from_row(row, mapping.observed_rssi_dbm)
    )

    if timestamp_utc is None:
        quality_flags.append("MISSING_TIMESTAMP")

    if temperature_c is None:
        quality_flags.append("MISSING_TEMPERATURE")

    if humidity_pct is None:
        quality_flags.append("MISSING_HUMIDITY")

    if pressure_hpa is None:
        quality_flags.append("MISSING_PRESSURE")

    if observed_rssi_dbm is None:
        quality_flags.append("MISSING_OBSERVED_RSSI")

    water_vapour_density = None
    gas_attenuation_db = None

    if (
        temperature_c is not None
        and humidity_pct is not None
        and pressure_hpa is not None
    ):
        try:
            water_vapour_density = water_vapour_density_g_m3(
                temperature_c=temperature_c,
                relative_humidity_pct=humidity_pct,
            )

            gas_result = gaseous_attenuation_terrestrial(
                path_distance_km=config.path_distance_km,
                frequency_ghz=config.frequency_ghz,
                elevation_angle_deg=config.elevation_angle_deg,
                water_vapour_density_g_m3=water_vapour_density,
                pressure_hpa=pressure_hpa,
                temperature_k=temperature_c + 273.15,
                mode="exact",
            )

            gas_attenuation_db = gas_result.attenuation_db
        except (TypeError, ValueError) as exc:
            quality_flags.append(
                f"GAS_INPUT_ERROR:{type(exc).__name__}"
            )

    rain_rate_mm_h = None
    rain_quality_flag = None
    rain_quality_valid = False
    rain_specific_db_km = None
    rain_uniform_path_db = None

    if precipitation_mm is None:
        quality_flags.append("MISSING_RAIN")
    else:
        artificial_end = datetime(
            2000,
            1,
            1,
            tzinfo=timezone.utc,
        )
        artificial_start = artificial_end.replace(
            second=0,
        )

        from datetime import timedelta

        artificial_start = (
            artificial_end
            - timedelta(
                seconds=config.rain_interval_seconds,
            )
        )

        rain_input_result = process_rain_interval(
            interval=RainIntervalInput(
                timestamp_start=artificial_start,
                timestamp_end=artificial_end,
                precipitation_mm=precipitation_mm,
                pulse_count=value_from_row(
                    row,
                    mapping.pulses_delta,
                ),
                source_field=(
                    mapping.rain_1min_mm
                    or "rain_1min_mm"
                ),
            ),
            configuration=RainProcessorConfiguration(
                minimum_interval_seconds=1.0,
                maximum_interval_seconds=3600.0,
                maximum_rain_rate_mm_h=500.0,
                bucket_depth_mm=config.bucket_depth_mm,
            ),
        )

        rain_rate_mm_h = rain_input_result.rain_rate_mm_h
        rain_quality_flag = (
            rain_input_result.quality_flag.value
        )
        rain_quality_valid = (
            rain_input_result.quality_valid
        )

        if rain_rate_mm_h is not None:
            rain_result = rain_specific_attenuation(
                rain_rate_mm_h=rain_rate_mm_h,
                frequency_ghz=config.frequency_ghz,
                elevation_angle_deg=config.elevation_angle_deg,
                polarization_tilt_deg=polarization_tilt_deg(
                    config.polarization
                ),
            )

            rain_specific_db_km = (
                rain_result.specific_attenuation_db_km
            )

            rain_uniform_path_db = (
                rain_specific_db_km
                * config.path_distance_km
            )

    link_budget = LinkBudget(
        frequency_ghz=config.frequency_ghz,
        path_distance_km=config.path_distance_km,
        tx_power_dbm=config.tx_power_dbm,
        ap_antenna_gain_dbi=config.ap_antenna_gain_dbi,
        sm_antenna_gain_dbi=config.sm_antenna_gain_dbi,
        ap_feeder_loss_db=config.ap_feeder_loss_db,
        sm_feeder_loss_db=config.sm_feeder_loss_db,
    )

    fspl_db = free_space_path_loss_db(
        config.frequency_ghz,
        config.path_distance_km,
    )

    clear_sky_additional = gas_attenuation_db or 0.0

    predicted_clear = predicted_rssi_dbm(
        link_budget,
        additional_attenuation_db=clear_sky_additional,
    )

    uniform_rain_additional = (
        clear_sky_additional
        + (rain_uniform_path_db or 0.0)
    )

    predicted_uniform_rain = predicted_rssi_dbm(
        link_budget,
        additional_attenuation_db=uniform_rain_additional,
    )

    residual_clear = None
    residual_uniform = None

    if observed_rssi_dbm is not None:
        residual_clear = residual_db(
            observed_rssi_dbm,
            predicted_clear,
        )
        residual_uniform = residual_db(
            observed_rssi_dbm,
            predicted_uniform_rain,
        )

    physics_valid = (
        timestamp_utc is not None
        and gas_attenuation_db is not None
        and rain_quality_valid
    )

    quality_valid = (
        physics_valid
        and observed_rssi_dbm is not None
    )

    if physics_valid and observed_rssi_dbm is None:
        quality_flags.append("PHYSICS_VALID_NO_RSSI")

    return {
        "source_row_id": str(row["_source_rowid"]),
        "source_timestamp_utc": timestamp_utc,
        "station_id": station_id,
        "temperature_c": temperature_c,
        "relative_humidity_pct": humidity_pct,
        "pressure_hpa": pressure_hpa,
        "water_vapour_density_g_m3": water_vapour_density,
        "precipitation_mm": precipitation_mm,
        "rain_interval_seconds": config.rain_interval_seconds,
        "rain_rate_mm_h": rain_rate_mm_h,
        "rain_quality_flag": rain_quality_flag,
        "rain_quality_valid": int(rain_quality_valid),
        "rain_specific_attenuation_db_km": rain_specific_db_km,
        "rain_uniform_path_attenuation_db": rain_uniform_path_db,
        "gaseous_attenuation_db": gas_attenuation_db,
        "free_space_path_loss_db": fspl_db,
        "tx_power_dbm": config.tx_power_dbm,
        "ap_antenna_gain_dbi": config.ap_antenna_gain_dbi,
        "sm_antenna_gain_dbi": config.sm_antenna_gain_dbi,
        "total_feeder_loss_db": (
            config.ap_feeder_loss_db
            + config.sm_feeder_loss_db
        ),
        "predicted_rssi_clear_sky_dbm": predicted_clear,
        "predicted_rssi_uniform_rain_dbm": (
            predicted_uniform_rain
        ),
        "observed_rssi_dbm": observed_rssi_dbm,
        "residual_clear_sky_db": residual_clear,
        "residual_uniform_rain_db": residual_uniform,
        "quality_valid": int(quality_valid),
        "quality_flags": ";".join(quality_flags),
    }


def write_result(
    connection: sqlite3.Connection,
    source_database: str,
    source_table: str,
    config: PipelineLinkConfiguration,
    result: dict[str, Any],
) -> None:
    connection.execute(
        """
        INSERT INTO propagation_observations (
            source_database,
            source_table,
            source_row_id,
            source_timestamp_utc,
            link_id,
            station_id,
            frequency_ghz,
            path_distance_km,
            temperature_c,
            relative_humidity_pct,
            pressure_hpa,
            water_vapour_density_g_m3,
            precipitation_mm,
            rain_interval_seconds,
            rain_rate_mm_h,
            rain_quality_flag,
            rain_quality_valid,
            rain_specific_attenuation_db_km,
            rain_uniform_path_attenuation_db,
            gaseous_attenuation_db,
            free_space_path_loss_db,
            tx_power_dbm,
            ap_antenna_gain_dbi,
            sm_antenna_gain_dbi,
            total_feeder_loss_db,
            predicted_rssi_clear_sky_dbm,
            predicted_rssi_uniform_rain_dbm,
            observed_rssi_dbm,
            residual_clear_sky_db,
            residual_uniform_rain_db,
            itu_rain_recommendation,
            itu_gas_recommendation,
            pipeline_version,
            quality_valid,
            quality_flags
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?
        )
        ON CONFLICT(
            source_database,
            source_table,
            source_timestamp_utc,
            link_id
        )
        DO UPDATE SET
            source_row_id = excluded.source_row_id,
            station_id = excluded.station_id,
            temperature_c = excluded.temperature_c,
            relative_humidity_pct =
                excluded.relative_humidity_pct,
            pressure_hpa = excluded.pressure_hpa,
            water_vapour_density_g_m3 =
                excluded.water_vapour_density_g_m3,
            precipitation_mm = excluded.precipitation_mm,
            rain_interval_seconds =
                excluded.rain_interval_seconds,
            rain_rate_mm_h = excluded.rain_rate_mm_h,
            rain_quality_flag = excluded.rain_quality_flag,
            rain_quality_valid = excluded.rain_quality_valid,
            rain_specific_attenuation_db_km =
                excluded.rain_specific_attenuation_db_km,
            rain_uniform_path_attenuation_db =
                excluded.rain_uniform_path_attenuation_db,
            gaseous_attenuation_db =
                excluded.gaseous_attenuation_db,
            free_space_path_loss_db =
                excluded.free_space_path_loss_db,
            predicted_rssi_clear_sky_dbm =
                excluded.predicted_rssi_clear_sky_dbm,
            predicted_rssi_uniform_rain_dbm =
                excluded.predicted_rssi_uniform_rain_dbm,
            observed_rssi_dbm = excluded.observed_rssi_dbm,
            residual_clear_sky_db =
                excluded.residual_clear_sky_db,
            residual_uniform_rain_db =
                excluded.residual_uniform_rain_db,
            pipeline_version = excluded.pipeline_version,
            quality_valid = excluded.quality_valid,
            quality_flags = excluded.quality_flags,
            calculated_at_utc = CURRENT_TIMESTAMP
        """,
        (
            source_database,
            source_table,
            result["source_row_id"],
            result["source_timestamp_utc"],
            config.link_id,
            result["station_id"],
            config.frequency_ghz,
            config.path_distance_km,
            result["temperature_c"],
            result["relative_humidity_pct"],
            result["pressure_hpa"],
            result["water_vapour_density_g_m3"],
            result["precipitation_mm"],
            result["rain_interval_seconds"],
            result["rain_rate_mm_h"],
            result["rain_quality_flag"],
            result["rain_quality_valid"],
            result["rain_specific_attenuation_db_km"],
            result["rain_uniform_path_attenuation_db"],
            result["gaseous_attenuation_db"],
            result["free_space_path_loss_db"],
            result["tx_power_dbm"],
            result["ap_antenna_gain_dbi"],
            result["sm_antenna_gain_dbi"],
            result["total_feeder_loss_db"],
            result["predicted_rssi_clear_sky_dbm"],
            result["predicted_rssi_uniform_rain_dbm"],
            result["observed_rssi_dbm"],
            result["residual_clear_sky_db"],
            result["residual_uniform_rain_db"],
            "ITU-R P.838-3",
            "ITU-R P.676-12",
            PIPELINE_VERSION,
            result["quality_valid"],
            result["quality_flags"],
        ),
    )


def run_pipeline(
    source_database: Path,
    output_database: Path,
    source_table: str,
    config: PipelineLinkConfiguration,
    limit: int | None,
    dry_run: bool,
) -> PipelineStatistics:
    initialize_database(output_database)

    rows_read = 0
    rows_calculated = 0
    rows_written = 0
    rows_skipped = 0

    with sqlite3.connect(source_database) as source:
        source.row_factory = sqlite3.Row

        mapping = discover_mapping(
            source,
            source_table,
        )

        print("Column mapping:")
        print(json.dumps(asdict(mapping), indent=2))

        query = build_select_query(
            source_table,
            mapping,
            limit,
        )

        rows = source.execute(query)

        with sqlite3.connect(output_database) as output:
            register_link(output, config)

            for row in rows:
                rows_read += 1

                try:
                    result = calculate_row(
                        row,
                        mapping,
                        config,
                    )
                    rows_calculated += 1
                except Exception as exc:
                    rows_skipped += 1
                    print(
                        f"SKIP rowid={row['_source_rowid']}: "
                        f"{type(exc).__name__}: {exc}"
                    )
                    continue

                if rows_read <= 3:
                    print()
                    print(
                        json.dumps(
                            result,
                            indent=2,
                            default=str,
                        )
                    )

                if not dry_run:
                    write_result(
                        output,
                        str(source_database),
                        source_table,
                        config,
                        result,
                    )
                    rows_written += 1

            if not dry_run:
                output.commit()

    return PipelineStatistics(
        rows_read=rows_read,
        rows_calculated=rows_calculated,
        rows_written=rows_written,
        rows_skipped=rows_skipped,
        dry_run=dry_run,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--source-db",
        default="SQLite/CU01/weather_local.db",
    )
    parser.add_argument(
        "--output-db",
        default="SQLite/propagation_physics.db",
    )
    parser.add_argument(
        "--source-table",
        default="master_observations",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write results. Default mode is dry-run.",
    )

    parser.add_argument("--link-id", default="CU01_SJ01_58")
    parser.add_argument("--frequency-ghz", type=float, default=5.8)
    parser.add_argument("--distance-km", type=float, default=12.0)

    parser.add_argument("--tx-power-dbm", type=float, required=True)
    parser.add_argument("--ap-gain-dbi", type=float, required=True)
    parser.add_argument("--sm-gain-dbi", type=float, required=True)

    parser.add_argument(
        "--ap-feeder-loss-db",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--sm-feeder-loss-db",
        type=float,
        default=0.0,
    )

    parser.add_argument("--polarization", default="H")
    parser.add_argument(
        "--elevation-angle-deg",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--rain-interval-seconds",
        type=float,
        default=60.0,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    config = PipelineLinkConfiguration(
        link_id=args.link_id,
        ap_station_id="CU01",
        sm_station_id="SJ01",
        frequency_ghz=args.frequency_ghz,
        path_distance_km=args.distance_km,
        tx_power_dbm=args.tx_power_dbm,
        ap_antenna_gain_dbi=args.ap_gain_dbi,
        sm_antenna_gain_dbi=args.sm_gain_dbi,
        ap_feeder_loss_db=args.ap_feeder_loss_db,
        sm_feeder_loss_db=args.sm_feeder_loss_db,
        polarization=args.polarization,
        elevation_angle_deg=args.elevation_angle_deg,
        rain_interval_seconds=args.rain_interval_seconds,
    )

    statistics = run_pipeline(
        source_database=Path(args.source_db),
        output_database=Path(args.output_db),
        source_table=args.source_table,
        config=config,
        limit=args.limit,
        dry_run=not args.write,
    )

    print()
    print("Pipeline statistics:")
    print(json.dumps(asdict(statistics), indent=2))


if __name__ == "__main__":
    main()
