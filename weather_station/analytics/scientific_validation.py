"""
AtmosLink Research Platform
Scientific Validation Engine V2

Construye un dataset horario científicamente consistente y calcula
métricas entre observaciones locales de CU01, ERA5-Land y NASA POWER.

Criterios metodológicos:
- Solo se emplea la campaña de campo válida de CU01.
- Inicio válido: 2026-07-22T13:35:29-05:00.
- Una sola fila por hora.
- Temperatura, humedad, presión y punto de rocío:
  promedio horario local.
- Precipitación local:
  suma de rain_1min_mm dentro de cada hora.
- ERA5 y NASA:
  un único valor por hora.
- Viento de CU01:
  excluido hasta confirmar sensor físico instalado.
- SJ01:
  excluida mientras permanezca en laboratorio.
"""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE = (
    PROJECT_ROOT
    / "SQLite"
    / "CU01"
    / "weather_local.db"
)

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "Data"
    / "validation"
)

MASTER_TABLE = "master_observations_multistation"
HOURLY_TABLE = "scientific_hourly_validation"

STATION_ID = "CU01"

CAMPAIGN_START_LOCAL = (
    "2026-07-22T13:35:29-05:00"
)

# Primer registro físicamente válido del anemómetro CU01.
# Los registros anteriores no participan en la validación de viento.
WIND_CAMPAIGN_START_LOCAL = (
    "2026-08-13T19:32:27-05:00"
)

# Elevaciones empleadas para homogeneizar la presión superficial.
# CU01 corresponde a la elevación física de la estación.
# ERA5-Land corresponde a la celda más próxima (-6.7, -78.5).
# NASA POWER corresponde a la elevación GEOS-IT informada por la API.
STATION_ELEVATION_M = 2733.00
ERA5_MODEL_ELEVATION_M = 3107.79
NASA_MODEL_ELEVATION_M = 2392.27
NASA_PRESSURE_BIAS_HPA = 8.248838159008756
NASA_PRESSURE_VALIDATION_START_UTC = (
    "2026-08-08T12:00:00+00:00"
)

GRAVITY_MS2 = 9.80665
DRY_AIR_GAS_CONSTANT = 287.05
STANDARD_LAPSE_RATE_K_M = 0.0065

# Gradiente vertical aproximado del punto de rocío.
# Se utiliza solamente para generar una variable ERA5
# normalizada a la elevación física de CU01.
DEWPOINT_LAPSE_RATE_K_M = 0.0020


VARIABLES = {
    "temperature": {
        "label": "Temperatura",
        "unit": "°C",
        "observed": "local_temp_avg_c",
        "era5": "era5_temp_c",
        "nasa": "nasa_temp_c",
        "enabled": True,
    },
    "humidity": {
        "label": "Humedad relativa",
        "unit": "%",
        "observed": "local_hum_avg_pct",
        "era5": "era5_rh_station_pct",
        "nasa": "nasa_rh_pct",
        "enabled": True,
        "era5_processing": (
            "normalizada a la elevación de CU01"
        ),
        "nasa_processing": "valor nativo",
    },
    "pressure": {
        "label": "Presión atmosférica normalizada",
        "unit": "hPa",
        "observed": "local_press_hpa",
        "era5": "era5_press_station_hpa",
        "nasa": "nasa_press_corrected_hpa",
        "enabled": True,
        "normalization_elevation_m": STATION_ELEVATION_M,
    },
    "dewpoint": {
        "label": "Punto de rocío",
        "unit": "°C",
        "observed": "local_dew_point_c",
        "era5": "era5_dewpoint_c",
        "nasa": "nasa_dewpoint_c",
        "enabled": True,
    },
    "precipitation": {
        "label": "Precipitación horaria",
        "unit": "mm",
        "observed": "local_precip_hour_mm",
        "era5": "era5_precip_mm",
        "nasa": "nasa_precip_mm",
        "enabled": True,
    },
    "wind": {
        "label": "Velocidad del viento",
        "unit": "m/s",
        "observed": "local_wind_speed_ms",
        "era5": "era5_wind_ms",
        "nasa": "nasa_wind10m_ms",
        "enabled": True,
        "campaign_start_local": (
            WIND_CAMPAIGN_START_LOCAL
        ),
    },
}


@dataclass
class Metrics:
    count: int
    bias: float | None
    mae: float | None
    rmse: float | None
    pearson_r: float | None
    r_squared: float | None
    nse: float | None
    willmott_d: float | None
    observed_mean: float | None
    modeled_mean: float | None
    error_std: float | None
    minimum_error: float | None
    maximum_error: float | None


def safe_round(
    value: float | None,
    digits: int = 6,
) -> float | None:
    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None

    return round(number, digits)


def calculate_metrics(
    observed: Iterable[float],
    modeled: Iterable[float],
) -> Metrics:
    frame = pd.DataFrame(
        {
            "observed": pd.to_numeric(
                pd.Series(observed),
                errors="coerce",
            ),
            "modeled": pd.to_numeric(
                pd.Series(modeled),
                errors="coerce",
            ),
        }
    ).dropna()

    count = len(frame)

    if count == 0:
        return Metrics(
            count=0,
            bias=None,
            mae=None,
            rmse=None,
            pearson_r=None,
            r_squared=None,
            nse=None,
            willmott_d=None,
            observed_mean=None,
            modeled_mean=None,
            error_std=None,
            minimum_error=None,
            maximum_error=None,
        )

    observed_series = frame["observed"]
    modeled_series = frame["modeled"]

    error = (
        modeled_series
        - observed_series
    )

    bias = error.mean()
    mae = error.abs().mean()
    rmse = math.sqrt(
        (error ** 2).mean()
    )

    pearson_r = None
    r_squared = None

    if (
        count >= 2
        and observed_series.nunique() > 1
        and modeled_series.nunique() > 1
    ):
        pearson_r = observed_series.corr(
            modeled_series
        )

        if pd.notna(pearson_r):
            r_squared = pearson_r ** 2
        else:
            pearson_r = None

    observed_mean = (
        observed_series.mean()
    )

    modeled_mean = (
        modeled_series.mean()
    )

    nse = None

    nse_denominator = (
        (
            observed_series
            - observed_mean
        ) ** 2
    ).sum()

    if nse_denominator != 0:
        nse = 1 - (
            (
                (
                    modeled_series
                    - observed_series
                ) ** 2
            ).sum()
            / nse_denominator
        )

    willmott_d = None

    willmott_denominator = (
        (
            (
                modeled_series
                - observed_mean
            ).abs()
            +
            (
                observed_series
                - observed_mean
            ).abs()
        ) ** 2
    ).sum()

    if willmott_denominator != 0:
        willmott_d = 1 - (
            (
                (
                    modeled_series
                    - observed_series
                ) ** 2
            ).sum()
            / willmott_denominator
        )

    return Metrics(
        count=count,
        bias=safe_round(bias),
        mae=safe_round(mae),
        rmse=safe_round(rmse),
        pearson_r=safe_round(
            pearson_r
        ),
        r_squared=safe_round(
            r_squared
        ),
        nse=safe_round(nse),
        willmott_d=safe_round(
            willmott_d
        ),
        observed_mean=safe_round(
            observed_mean
        ),
        modeled_mean=safe_round(
            modeled_mean
        ),
        error_std=safe_round(
            error.std(ddof=1)
            if count > 1
            else 0.0
        ),
        minimum_error=safe_round(
            error.min()
        ),
        maximum_error=safe_round(
            error.max()
        ),
    )


def load_campaign_rows(
    connection: sqlite3.Connection,
) -> pd.DataFrame:
    query = f"""
        SELECT
            bucket_hour,
            weather_timestamp_local,

            local_temp_avg_c,
            local_hum_avg_pct,
            local_press_hpa,
            local_dew_point_c,
            local_rain_1min_mm,
            local_wind_speed_ms,
            local_wind_ok,

            era5_timestamp_local,
            era5_site_tag,
            era5_temp_c,
            era5_rh_pct,
            era5_press_hpa,
            era5_dewpoint_c,
            era5_precip_mm,
            era5_wind_ms,

            nasa_timestamp_local,
            nasa_site_tag,
            nasa_temp_c,
            nasa_rh_pct,
            nasa_press_hpa,
            nasa_dewpoint_c,
            nasa_precip_mm,
            nasa_wind10m_ms

        FROM {MASTER_TABLE}

        WHERE station_id = ?
          AND weather_timestamp_local >= ?
          AND local_bme_ok = 1
        ORDER BY bucket_hour,
                 weather_timestamp_local
    """

    frame = pd.read_sql_query(
        query,
        connection,
        params=(
            STATION_ID,
            CAMPAIGN_START_LOCAL,
        ),
    )

    if frame.empty:
        raise RuntimeError(
            "No existen registros válidos "
            "para la campaña seleccionada."
        )

    return frame


def first_valid(
    series: pd.Series,
):
    valid = series.dropna()

    if valid.empty:
        return None

    return valid.iloc[0]


def normalize_pressure_to_station(
    pressure_hpa,
    temperature_c,
    source_elevation_m,
):
    """
    Traslada la presión superficial del modelo a la elevación de CU01
    mediante la ecuación hipsométrica y un gradiente térmico estándar.

    La presión original se conserva; esta función genera una variable
    derivada exclusivamente para la comparación científica.
    """
    try:
        pressure = float(pressure_hpa)
        temperature_k = float(temperature_c) + 273.15
        source_elevation = float(source_elevation_m)
    except (TypeError, ValueError):
        return None

    if not all(
        math.isfinite(value)
        for value in (
            pressure,
            temperature_k,
            source_elevation,
        )
    ):
        return None

    delta_elevation = (
        STATION_ELEVATION_M
        - source_elevation
    )

    mean_temperature_k = (
        temperature_k
        - STANDARD_LAPSE_RATE_K_M
        * delta_elevation
        / 2.0
    )

    if mean_temperature_k <= 0:
        return None

    return pressure * math.exp(
        -GRAVITY_MS2
        * delta_elevation
        / (
            DRY_AIR_GAS_CONSTANT
            * mean_temperature_k
        )
    )


def normalize_era5_humidity_to_station(
    temperature_c,
    dewpoint_c,
):
    """
    Calcula humedad relativa ERA5 ajustando primero
    temperatura y punto de rocío desde la elevación
    de la celda hasta la elevación física de CU01.

    Los valores ERA5 originales permanecen intactos.
    """
    try:
        temperature = float(temperature_c)
        dewpoint = float(dewpoint_c)
    except (TypeError, ValueError):
        return None

    if not all(
        math.isfinite(value)
        for value in (
            temperature,
            dewpoint,
        )
    ):
        return None

    delta_elevation = (
        STATION_ELEVATION_M
        - ERA5_MODEL_ELEVATION_M
    )

    adjusted_temperature = (
        temperature
        - STANDARD_LAPSE_RATE_K_M
        * delta_elevation
    )

    adjusted_dewpoint = (
        dewpoint
        - DEWPOINT_LAPSE_RATE_K_M
        * delta_elevation
    )

    exponent = (
        17.625
        * adjusted_dewpoint
        / (243.04 + adjusted_dewpoint)
        - 17.625
        * adjusted_temperature
        / (243.04 + adjusted_temperature)
    )

    humidity = 100.0 * math.exp(exponent)

    return min(max(humidity, 0.0), 100.0)


def build_hourly_dataset(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    numeric_columns = [
        "local_temp_avg_c",
        "local_hum_avg_pct",
        "local_press_hpa",
        "local_dew_point_c",
        "local_rain_1min_mm",
        "local_wind_speed_ms",
        "local_wind_ok",

        "era5_temp_c",
        "era5_rh_pct",
        "era5_press_hpa",
        "era5_dewpoint_c",
        "era5_precip_mm",
        "era5_wind_ms",

        "nasa_temp_c",
        "nasa_rh_pct",
        "nasa_press_hpa",
        "nasa_dewpoint_c",
        "nasa_precip_mm",
        "nasa_wind10m_ms",
    ]

    for column in numeric_columns:
        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

    wind_start_utc = pd.Timestamp(
        WIND_CAMPAIGN_START_LOCAL
    ).tz_convert("UTC")

    frame["_weather_timestamp_utc"] = (
        pd.to_datetime(
            frame["weather_timestamp_local"],
            errors="coerce",
            utc=True,
        )
    )

    hourly_rows: list[dict] = []

    grouped = frame.groupby(
        "bucket_hour",
        dropna=True,
        sort=True,
    )

    for bucket_hour, group in grouped:
        valid_wind = group.loc[
            (
                group["_weather_timestamp_utc"]
                >= wind_start_utc
            )
            & (
                group["local_wind_ok"] == 1
            )
            & (
                group[
                    "local_wind_speed_ms"
                ].notna()
            )
        ]

        local_count = int(
            group[
                "local_temp_avg_c"
            ].notna().sum()
        )

        local_pressure_valid = (
            group["local_press_hpa"].where(
                group["local_press_hpa"].between(
                    720.0,
                    755.0,
                    inclusive="both",
                )
            )
        )

        local_pressure_records = int(
            local_pressure_valid.notna().sum()
        )

        local_pressure_hourly = (
            local_pressure_valid.mean()
            if local_pressure_records >= 30
            else float("nan")
        )

        # NASA POWER: una hora solo tiene correspondencia NASA
        # cuando existe al menos una variable meteorológica válida.
        # Los metadatos timestamp/site_tag no deben, por sí solos,
        # convertir un placeholder en una observación NASA.
        nasa_measure_cols = [
            "nasa_temp_c",
            "nasa_rh_pct",
            "nasa_press_hpa",
            "nasa_dewpoint_c",
            "nasa_precip_mm",
            "nasa_wind10m_ms",
        ]

        nasa_valid_mask = (
            group[nasa_measure_cols]
            .notna()
            .any(axis=1)
        )

        nasa_group = group.loc[nasa_valid_mask]

        row = {
            "station_id": STATION_ID,
            "bucket_hour": bucket_hour,

            "local_records": local_count,
            "local_pressure_records": (
                local_pressure_records
            ),
            "local_pressure_qc": (
                "VALID"
                if local_pressure_records >= 30
                else "PRESSURE_QC_FAIL"
            ),

            "local_temp_avg_c": (
                group[
                    "local_temp_avg_c"
                ].mean()
            ),

            "local_hum_avg_pct": (
                group[
                    "local_hum_avg_pct"
                ].mean()
            ),

            "local_press_hpa": (
                local_pressure_hourly
            ),

            "local_dew_point_c": (
                group[
                    "local_dew_point_c"
                ].mean()
            ),

            "local_precip_hour_mm": (
                group[
                    "local_rain_1min_mm"
                ].fillna(0).sum()
            ),

            "local_wind_speed_ms": (
                valid_wind[
                    "local_wind_speed_ms"
                ].mean()
                if not valid_wind.empty
                else None
            ),

            "era5_timestamp_local": (
                first_valid(
                    group[
                        "era5_timestamp_local"
                    ]
                )
            ),

            "era5_site_tag": (
                first_valid(
                    group[
                        "era5_site_tag"
                    ]
                )
            ),

            "era5_temp_c": (
                first_valid(
                    group[
                        "era5_temp_c"
                    ]
                )
            ),

            "era5_rh_pct": (
                first_valid(
                    group[
                        "era5_rh_pct"
                    ]
                )
            ),

            "era5_press_hpa": (
                first_valid(
                    group[
                        "era5_press_hpa"
                    ]
                )
            ),

            "era5_dewpoint_c": (
                first_valid(
                    group[
                        "era5_dewpoint_c"
                    ]
                )
            ),

            "era5_precip_mm": (
                first_valid(
                    group[
                        "era5_precip_mm"
                    ]
                )
            ),

            "era5_wind_ms": (
                first_valid(
                    group[
                        "era5_wind_ms"
                    ]
                )
            ),

            "nasa_timestamp_local": (
                first_valid(
                    nasa_group[
                        "nasa_timestamp_local"
                    ]
                )
            ),

            "nasa_site_tag": (
                first_valid(
                    nasa_group[
                        "nasa_site_tag"
                    ]
                )
            ),

            "nasa_temp_c": (
                first_valid(
                    nasa_group[
                        "nasa_temp_c"
                    ]
                )
            ),

            "nasa_rh_pct": (
                first_valid(
                    nasa_group[
                        "nasa_rh_pct"
                    ]
                )
            ),

            "nasa_press_hpa": (
                first_valid(
                    nasa_group[
                        "nasa_press_hpa"
                    ]
                )
            ),

            "nasa_dewpoint_c": (
                first_valid(
                    nasa_group[
                        "nasa_dewpoint_c"
                    ]
                )
            ),

            "nasa_precip_mm": (
                first_valid(
                    nasa_group[
                        "nasa_precip_mm"
                    ]
                )
            ),

            "nasa_wind10m_ms": (
                first_valid(
                    nasa_group[
                        "nasa_wind10m_ms"
                    ]
                )
            ),
        }

        row["era5_rh_station_pct"] = (
            normalize_era5_humidity_to_station(
                row.get("era5_temp_c"),
                row.get("era5_dewpoint_c"),
            )
        )

        row["era5_press_station_hpa"] = (
            normalize_pressure_to_station(
                row.get("era5_press_hpa"),
                row.get("era5_temp_c"),
                ERA5_MODEL_ELEVATION_M,
            )
        )

        row["nasa_press_station_hpa"] = (
            normalize_pressure_to_station(
                row.get("nasa_press_hpa"),
                row.get("nasa_temp_c"),
                NASA_MODEL_ELEVATION_M,
            )
        )

        nasa_pressure_normalized = (
            row.get("nasa_press_station_hpa")
        )

        row["nasa_press_corrected_hpa"] = (
            nasa_pressure_normalized
            - NASA_PRESSURE_BIAS_HPA
            if nasa_pressure_normalized is not None
            else None
        )

        hourly_rows.append(row)

    hourly = pd.DataFrame(
        hourly_rows
    )

    if hourly.empty:
        raise RuntimeError(
            "No fue posible construir "
            "el dataset horario."
        )

    hourly = hourly.sort_values(
        "bucket_hour"
    ).reset_index(drop=True)

    return hourly


def save_hourly_dataset(
    connection: sqlite3.Connection,
    hourly: pd.DataFrame,
) -> Path:
    hourly.to_sql(
        HOURLY_TABLE,
        connection,
        if_exists="replace",
        index=False,
    )

    connection.execute(
        f"""
        CREATE INDEX IF NOT EXISTS
        idx_{HOURLY_TABLE}_station_hour

        ON {HOURLY_TABLE}
        (
            station_id,
            bucket_hour
        )
        """
    )

    connection.commit()

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = (
        OUTPUT_DIRECTORY
        / "scientific_hourly_CU01.csv"
    )

    hourly.to_csv(
        csv_path,
        index=False,
        encoding="utf-8",
    )

    return csv_path


def build_validation_report(
    hourly: pd.DataFrame,
) -> dict:
    report = {
        "status": "ok",
        "engine_version": "2.3.0",
        "station_id": STATION_ID,
        "validation_scope": (
            "FIELD_VALIDATION"
        ),
        "campaign_start_local": (
            CAMPAIGN_START_LOCAL
        ),
        "campaign_end_hour": (
            hourly[
                "bucket_hour"
            ].max()
        ),
        "hourly_rows": len(hourly),
        "methodology": {
            "temporal_resolution": "hourly",
            "local_temperature": "mean",
            "local_humidity": "mean",
            "local_pressure": "mean",
            "local_dewpoint": "mean",
            "local_precipitation": (
                "sum(local_rain_1min_mm)"
            ),
            "model_values": (
                "one record per bucket_hour"
            ),
            "humidity_era5_normalization": {
                "status": "altitude_normalized",
                "station_elevation_m": (
                    STATION_ELEVATION_M
                ),
                "model_elevation_m": (
                    ERA5_MODEL_ELEVATION_M
                ),
                "temperature_lapse_rate_k_m": (
                    STANDARD_LAPSE_RATE_K_M
                ),
                "dewpoint_lapse_rate_k_m": (
                    DEWPOINT_LAPSE_RATE_K_M
                ),
                "raw_column": "era5_rh_pct",
                "derived_column": (
                    "era5_rh_station_pct"
                ),
            },
            "pressure_nasa_bias_correction": {
                "status": "temporally_validated",
                "method": "constant_bias_subtraction",
                "bias_hpa": NASA_PRESSURE_BIAS_HPA,
                "calibration_pairs": 354,
                "calibration_start_utc": (
                    "2026-07-22T18:00:00+00:00"
                ),
                "calibration_end_utc": (
                    "2026-08-08T11:00:00+00:00"
                ),
                "validation_start_utc": (
                    NASA_PRESSURE_VALIDATION_START_UTC
                ),
                "raw_column": "nasa_press_hpa",
                "altitude_normalized_column": (
                    "nasa_press_station_hpa"
                ),
                "derived_column": (
                    "nasa_press_corrected_hpa"
                ),
            },
            "wind_CU01": {
                "status": "included",
                "aggregation": "mean",
                "campaign_start_local": (
                    WIND_CAMPAIGN_START_LOCAL
                ),
                "validity_criteria": (
                    "local_wind_ok = 1 and "
                    "local_wind_speed_ms is not null"
                ),
            },
        },
        "variables": {},
    }

    for variable_key, config in (
        VARIABLES.items()
    ):
        variable_report = {
            "label": config["label"],
            "unit": config["unit"],
            "enabled": config["enabled"],
            "models": {},
        }

        if not config["enabled"]:
            variable_report[
                "exclusion_reason"
            ] = config.get(
                "exclusion_reason"
            )

            report["variables"][
                variable_key
            ] = variable_report

            continue

        for model_name in (
            "era5",
            "nasa",
        ):
            observed_column = (
                config["observed"]
            )

            model_column = (
                config[model_name]
            )

            valid = hourly[
                [
                    "bucket_hour",
                    observed_column,
                    model_column,
                ]
            ].dropna()

            if (
                variable_key == "pressure"
                and model_name == "nasa"
            ):
                valid = valid[
                    valid["bucket_hour"]
                    >= NASA_PRESSURE_VALIDATION_START_UTC
                ]

            metrics = calculate_metrics(
                valid[observed_column],
                valid[model_column],
            )

            variable_report[
                "models"
            ][model_name] = {
                "observed_column": (
                    observed_column
                ),
                "modeled_column": (
                    model_column
                ),
                "first_hour": (
                    valid[
                        "bucket_hour"
                    ].min()
                    if not valid.empty
                    else None
                ),
                "last_hour": (
                    valid[
                        "bucket_hour"
                    ].max()
                    if not valid.empty
                    else None
                ),
                "metrics": asdict(
                    metrics
                ),
            }

        report["variables"][
            variable_key
        ] = variable_report

    return report


def export_report(
    report: dict,
) -> tuple[Path, Path]:
    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = (
        OUTPUT_DIRECTORY
        / "validation_CU01_v2.json"
    )

    csv_path = (
        OUTPUT_DIRECTORY
        / "validation_CU01_v2.csv"
    )

    json_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    rows = []

    for variable_key, variable in (
        report["variables"].items()
    ):
        if not variable["enabled"]:
            rows.append(
                {
                    "station_id": STATION_ID,
                    "variable": variable_key,
                    "variable_label": (
                        variable["label"]
                    ),
                    "unit": variable["unit"],
                    "model": None,
                    "enabled": False,
                    "exclusion_reason": (
                        variable.get(
                            "exclusion_reason"
                        )
                    ),
                }
            )

            continue

        for model_name, model in (
            variable["models"].items()
        ):
            row = {
                "station_id": STATION_ID,
                "variable": variable_key,
                "variable_label": (
                    variable["label"]
                ),
                "unit": variable["unit"],
                "model": model_name.upper(),
                "enabled": True,
                "first_hour": (
                    model["first_hour"]
                ),
                "last_hour": (
                    model["last_hour"]
                ),
            }

            row.update(
                model["metrics"]
            )

            rows.append(row)

    pd.DataFrame(rows).to_csv(
        csv_path,
        index=False,
        encoding="utf-8",
    )

    return json_path, csv_path


def print_summary(
    report: dict,
) -> None:
    print("=" * 88)
    print(
        " AtmosLink Scientific Validation Engine V2"
    )
    print("=" * 88)

    print(
        f"Estación        : {report['station_id']}"
    )

    print(
        f"Inicio campaña  : "
        f"{report['campaign_start_local']}"
    )

    print(
        f"Fin analizado   : "
        f"{report['campaign_end_hour']}"
    )

    print(
        f"Filas horarias  : "
        f"{report['hourly_rows']}"
    )

    print("-" * 88)

    for variable in (
        report["variables"].values()
    ):
        print(
            f"{variable['label']} "
            f"({variable['unit']})"
        )

        if not variable["enabled"]:
            print(
                "  EXCLUIDA | "
                + variable.get(
                    "exclusion_reason",
                    "Sin motivo registrado.",
                )
            )

            print("-" * 88)
            continue

        for model_name, model in (
            variable["models"].items()
        ):
            metrics = model["metrics"]

            print(
                f"  {model_name.upper():5s} | "
                f"N={metrics['count']:4d} | "
                f"BIAS={metrics['bias']} | "
                f"MAE={metrics['mae']} | "
                f"RMSE={metrics['rmse']} | "
                f"r={metrics['pearson_r']} | "
                f"R²={metrics['r_squared']} | "
                f"NSE={metrics['nse']} | "
                f"d={metrics['willmott_d']}"
            )

        print("-" * 88)


def main() -> None:
    if not DATABASE.exists():
        raise FileNotFoundError(
            f"No existe la base: {DATABASE}"
        )

    with sqlite3.connect(
        DATABASE
    ) as connection:
        campaign = load_campaign_rows(
            connection
        )

        hourly = build_hourly_dataset(
            campaign
        )

        hourly_csv = save_hourly_dataset(
            connection,
            hourly,
        )

    report = build_validation_report(
        hourly
    )

    json_path, csv_path = export_report(
        report
    )

    print_summary(report)

    print(
        f"Dataset horario : {hourly_csv}"
    )

    print(
        f"Reporte JSON    : {json_path}"
    )

    print(
        f"Reporte CSV     : {csv_path}"
    )

    print("Status: OK")


if __name__ == "__main__":
    main()
