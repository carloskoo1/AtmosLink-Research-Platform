"""
AtmosLink Scientific Validation - SJ01 FIELD

Estacion:
    SJ01 - Cerro San Jose

Inicio FIELD:
    2026-08-31 16:00 America/Lima
    2026-08-31 21:00 UTC

Principios:
- Nunca mezcla datos LAB con FIELD.
- Utiliza master_observations_multistation.
- Solo compara observaciones temporalmente emparejadas.
- No aplica calibraciones obtenidas en CU01.
- No interpola datos ausentes.
- La madurez depende del numero de pares horarios.
"""

import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

DATABASE = (
    ROOT
    / "SQLite"
    / "CU01"
    / "weather_local.db"
)

TABLE = "master_observations_multistation"

OUTPUT_DIRECTORY = (
    ROOT
    / "Data"
    / "validation"
)

STATION_ID = "SJ01"
STATION_NAME = "Cerro San Jose"

STATION_ELEVATION_M = 3650.0

# Altura física del anemómetro SJ01 sobre el terreno.
WIND_SENSOR_HEIGHT_AGL_M = 10.0

FIELD_START_LOCAL = (
    "2026-08-31T16:00:00-05:00"
)

FIELD_START_UTC = (
    "2026-08-31T21:00:00+00:00"
)

ERA5_SITE_TAG = "SM_SAN_JOSE"
NASA_SITE_TAG = "SM_SAN_JOSE"

ENGINE_VERSION = "SJ01-1.0.0"


VARIABLES = {
    "temperature": {
        "label": "Temperatura",
        "unit": "°C",
        "observed": "local_temp_avg_c",
        "era5": "era5_temp_c",
        "nasa": "nasa_temp_c",
        "aggregation": "mean",
    },

    "humidity": {
        "label": "Humedad relativa",
        "unit": "%",
        "observed": "local_hum_avg_pct",

        # El valor inicial se habilita posteriormente
        # mediante era5_rh_station_pct, una vez aplicada
        # la armonizacion vertical especifica de SJ01.
        "era5": None,

        "nasa": "nasa_rh_pct",
        "aggregation": "mean",
    },

    "pressure": {
        "label": "Presion atmosferica",
        "unit": "hPa",
        "observed": "local_press_hpa",

        # Los valores iniciales se habilitan
        # posteriormente solo mediante columnas
        # verticalmente armonizadas para SJ01.
        "era5": None,
        "nasa": None,

        "aggregation": "mean",
    },

    "precipitation": {
        "label": "Precipitacion horaria",
        "unit": "mm",
        "observed": "local_rain_1min_mm",
        "era5": "era5_precip_mm",
        "nasa": "nasa_precip_mm",
        "aggregation": "sum",
    },

    "wind": {
        "label": "Velocidad del viento",
        "unit": "m/s",
        "observed": "local_wind_speed_ms",
        "era5": "era5_wind_ms",
        "nasa": "nasa_wind10m_ms",
        "aggregation": "mean",
    },
}


def finite_number(value):
    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None

    return number


def maturity_from_count(count):
    """
    Clasificacion operacional de madurez.

    No representa calidad del modelo.
    Representa solamente cantidad de pares horarios.
    """

    if count <= 0:
        return "NOT_AVAILABLE"

    if count < 24:
        return "PRELIMINARY"

    if count < 168:
        return "INTERMEDIATE"

    return "MATURE"


def safe_metrics(observed, modeled):
    pairs = pd.DataFrame(
        {
            "observed": pd.to_numeric(
                observed,
                errors="coerce",
            ),
            "modeled": pd.to_numeric(
                modeled,
                errors="coerce",
            ),
        }
    ).dropna()

    count = len(pairs)

    result = {
        "count": int(count),
        "maturity": maturity_from_count(
            count
        ),
    }

    if count == 0:
        return result

    error = (
        pairs["modeled"]
        - pairs["observed"]
    )

    result.update(
        {
            "observed_mean": round(
                float(
                    pairs[
                        "observed"
                    ].mean()
                ),
                6,
            ),
            "modeled_mean": round(
                float(
                    pairs[
                        "modeled"
                    ].mean()
                ),
                6,
            ),
            "bias": round(
                float(error.mean()),
                6,
            ),
            "mae": round(
                float(error.abs().mean()),
                6,
            ),
            "rmse": round(
                float(
                    (
                        error.pow(2).mean()
                    )
                    ** 0.5
                ),
                6,
            ),
        }
    )

    # Correlacion y estadisticos de ajuste no se
    # publican para muestras demasiado pequenas.
    if count >= 24:

        observed_std = (
            pairs["observed"].std()
        )

        modeled_std = (
            pairs["modeled"].std()
        )

        if (
            pd.notna(observed_std)
            and pd.notna(modeled_std)
            and observed_std > 0
            and modeled_std > 0
        ):
            correlation = (
                pairs[
                    "observed"
                ].corr(
                    pairs[
                        "modeled"
                    ]
                )
            )

            if pd.notna(correlation):
                result[
                    "pearson_r"
                ] = round(
                    float(correlation),
                    6,
                )

                result[
                    "r_squared"
                ] = round(
                    float(
                        correlation
                        * correlation
                    ),
                    6,
                )

    return result


def load_field_data():
    connection = sqlite3.connect(
        DATABASE
    )

    try:
        dataframe = pd.read_sql_query(
            f"""
            SELECT *
            FROM {TABLE}
            WHERE station_id = ?
              AND bucket_hour >= ?
            ORDER BY bucket_hour,
                     bucket_minute
            """,
            connection,
            params=(
                STATION_ID,
                FIELD_START_UTC,
            ),
        )

    finally:
        connection.close()

    return dataframe


# =========================================================
# ERA5-LAND VERTICAL HARMONIZATION - SJ01
# =========================================================
#
# Elevación física de la estación:
#     SJ01 Cerro San José = 3650.00 m
#
# Elevación de la celda ERA5-Land:
#     SM_SAN_JOSE = 3562.38 m
#
# La elevación ERA5-Land fue obtenida directamente
# del geopotencial del producto reanalysis-era5-land:
#
#     celda seleccionada ≈ (-6.8, -78.6)
#     geopotencial        = 34934.984 m²/s²
#     z / g               = 3562.38 m
#
# Diferencia vertical:
#
#     estación - ERA5 = +87.62 m
#
# Los valores ERA5 originales almacenados en SQLite
# NO son sustituidos. Las siguientes funciones generan
# exclusivamente variables derivadas para comparación.
# =========================================================

ERA5_MODEL_ELEVATION_M = 3562.38

# Elevacion de superficie GEOS-IT reportada por
# NASA POWER API geometry.coordinates[2]
# para SM_SAN_JOSE.
NASA_MODEL_ELEVATION_M = 2749.53

GRAVITY_MS2 = 9.80665
DRY_AIR_GAS_CONSTANT = 287.05

STANDARD_LAPSE_RATE_K_M = 0.0065

DEWPOINT_LAPSE_RATE_K_M = 0.0020


def normalize_era5_pressure_sj01(
    pressure_hpa,
    temperature_c,
):
    """
    Traslada la presión superficial ERA5-Land desde
    la elevación representativa de la celda
    SM_SAN_JOSE (3562.38 m) hasta la elevación
    física de SJ01 (3650.00 m).

    Se emplea una formulación hipsométrica.

    La presión ERA5 original permanece intacta.
    """

    try:
        pressure = float(
            pressure_hpa
        )

        temperature_k = (
            float(temperature_c)
            + 273.15
        )

    except (
        TypeError,
        ValueError,
    ):
        return float("nan")

    if not (
        math.isfinite(pressure)
        and math.isfinite(
            temperature_k
        )
    ):
        return float("nan")

    delta_elevation = (
        STATION_ELEVATION_M
        - ERA5_MODEL_ELEVATION_M
    )

    mean_temperature_k = (
        temperature_k
        - STANDARD_LAPSE_RATE_K_M
        * delta_elevation
        / 2.0
    )

    if mean_temperature_k <= 0:
        return float("nan")

    normalized_pressure = (
        pressure
        * math.exp(
            -GRAVITY_MS2
            * delta_elevation
            /
            (
                DRY_AIR_GAS_CONSTANT
                * mean_temperature_k
            )
        )
    )

    return normalized_pressure


def normalize_nasa_pressure_sj01(
    pressure_hpa,
    temperature_c,
):
    """
    Traslada NASA POWER PS desde la elevacion de
    superficie GEOS-IT reportada por la API para
    SM_SAN_JOSE (2749.53 m) hasta la elevacion
    fisica de SJ01 (3650.00 m).

    Se emplea la ecuacion hipsometrica.

    No se aplica ningun bias empirico heredado
    de CU01.

    El valor NASA POWER original permanece intacto.
    """

    try:
        pressure = float(
            pressure_hpa
        )

        temperature_k = (
            float(temperature_c)
            + 273.15
        )

    except (
        TypeError,
        ValueError,
    ):
        return float("nan")

    if not (
        math.isfinite(pressure)
        and math.isfinite(
            temperature_k
        )
    ):
        return float("nan")

    if pressure <= 0:
        return float("nan")

    delta_elevation = (
        STATION_ELEVATION_M
        - NASA_MODEL_ELEVATION_M
    )

    mean_temperature_k = (
        temperature_k
        - STANDARD_LAPSE_RATE_K_M
        * delta_elevation
        / 2.0
    )

    if mean_temperature_k <= 0:
        return float("nan")

    normalized_pressure = (
        pressure
        * math.exp(
            -GRAVITY_MS2
            * delta_elevation
            /
            (
                DRY_AIR_GAS_CONSTANT
                * mean_temperature_k
            )
        )
    )

    return normalized_pressure


def normalize_era5_humidity_sj01(
    temperature_c,
    dewpoint_c,
):
    """
    Calcula humedad relativa ERA5-Land para la
    elevación física de SJ01.

    Primero se ajustan temperatura y punto de rocío
    desde 3562.38 m hasta 3650.00 m.

    Temperatura:
        gradiente = 6.5 °C/km

    Punto de rocío:
        gradiente = 2.0 °C/km

    Posteriormente se calcula RH mediante la
    relación temperatura/punto de rocío.

    Las variables ERA5 originales permanecen
    almacenadas sin modificación.
    """

    try:
        temperature = float(
            temperature_c
        )

        dewpoint = float(
            dewpoint_c
        )

    except (
        TypeError,
        ValueError,
    ):
        return float("nan")

    if not (
        math.isfinite(temperature)
        and math.isfinite(dewpoint)
    ):
        return float("nan")

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

    denominator_td = (
        243.04
        + adjusted_dewpoint
    )

    denominator_t = (
        243.04
        + adjusted_temperature
    )

    if (
        denominator_td == 0
        or denominator_t == 0
    ):
        return float("nan")

    exponent = (
        17.625
        * adjusted_dewpoint
        / denominator_td
        -
        17.625
        * adjusted_temperature
        / denominator_t
    )

    humidity = (
        100.0
        * math.exp(exponent)
    )

    return min(
        max(
            humidity,
            0.0,
        ),
        100.0,
    )


# Habilitar exclusivamente las variables ERA5
# cuya armonización vertical ya tiene soporte
# metodológico específico para SJ01.
VARIABLES[
    "humidity"
][
    "era5"
] = "era5_rh_station_pct"

VARIABLES[
    "pressure"
][
    "era5"
] = "era5_press_station_hpa"


# NASA POWER PS se compara exclusivamente despues
# de armonizar verticalmente la presion desde la
# superficie GEOS-IT (2749.53 m) hasta SJ01
# (3650.00 m).
VARIABLES[
    "pressure"
][
    "nasa"
] = "nasa_press_station_hpa"



def build_hourly(dataframe):
    if dataframe.empty:
        return pd.DataFrame()

    df = dataframe.copy()

    # -----------------------------------------------------
    # Variables ERA5-Land armonizadas verticalmente
    # para la elevación física de SJ01.
    #
    # Los valores originales:
    #   era5_press_hpa
    #   era5_temp_c
    #   era5_dewpoint_c
    #
    # permanecen intactos.
    # -----------------------------------------------------

    if (
        "era5_press_hpa" in df.columns
        and "era5_temp_c" in df.columns
    ):
        df[
            "era5_press_station_hpa"
        ] = df.apply(
            lambda row:
                normalize_era5_pressure_sj01(
                    row[
                        "era5_press_hpa"
                    ],
                    row[
                        "era5_temp_c"
                    ],
                ),
            axis=1,
        )
    else:
        df[
            "era5_press_station_hpa"
        ] = float("nan")

    if (
        "era5_temp_c" in df.columns
        and "era5_dewpoint_c" in df.columns
    ):
        df[
            "era5_rh_station_pct"
        ] = df.apply(
            lambda row:
                normalize_era5_humidity_sj01(
                    row[
                        "era5_temp_c"
                    ],
                    row[
                        "era5_dewpoint_c"
                    ],
                ),
            axis=1,
        )
    else:
        df[
            "era5_rh_station_pct"
        ] = float("nan")

    # -----------------------------------------------------
    # NASA POWER PS armonizada verticalmente.
    #
    # nasa_press_hpa:
    #     valor RAW NASA POWER / GEOS-IT
    #
    # nasa_press_station_hpa:
    #     valor derivado a la elevacion fisica de SJ01.
    #
    # El valor RAW permanece intacto.
    # -----------------------------------------------------

    if (
        "nasa_press_hpa" in df.columns
        and "nasa_temp_c" in df.columns
    ):
        df[
            "nasa_press_station_hpa"
        ] = df.apply(
            lambda row:
                normalize_nasa_pressure_sj01(
                    row[
                        "nasa_press_hpa"
                    ],
                    row[
                        "nasa_temp_c"
                    ],
                ),
            axis=1,
        )
    else:
        df[
            "nasa_press_station_hpa"
        ] = float("nan")


    df["_hour"] = pd.to_datetime(
        df["bucket_hour"],
        errors="coerce",
        utc=True,
    )

    df = df[
        df["_hour"].notna()
    ].copy()

    df = df[
        df["_hour"]
        >= pd.Timestamp(
            FIELD_START_UTC
        )
    ].copy()

    if df.empty:
        return pd.DataFrame()

    df["bucket_hour"] = (
        df["_hour"]
        .dt.strftime(
            "%Y-%m-%dT%H:00:00Z"
        )
    )

    output = pd.DataFrame(
        {
            "bucket_hour":
                sorted(
                    df[
                        "bucket_hour"
                    ].unique()
                )
        }
    )

    for key, config in VARIABLES.items():

        observed_column = (
            config["observed"]
        )

        if observed_column in df.columns:

            if (
                config[
                    "aggregation"
                ]
                == "sum"
            ):
                observed = (
                    df.groupby(
                        "bucket_hour"
                    )[
                        observed_column
                    ]
                    .sum(
                        min_count=1
                    )
                )
            else:
                observed = (
                    df.groupby(
                        "bucket_hour"
                    )[
                        observed_column
                    ]
                    .mean()
                )

            output = output.merge(
                observed.rename(
                    f"{key}_observed"
                ),
                on="bucket_hour",
                how="left",
            )

        else:
            output[
                f"{key}_observed"
            ] = None

        for model in (
            "era5",
            "nasa",
        ):

            model_column = config.get(
                model
            )

            target_column = (
                f"{key}_{model}"
            )

            if (
                model_column
                and model_column
                in df.columns
            ):
                modeled = (
                    df.groupby(
                        "bucket_hour"
                    )[
                        model_column
                    ]
                    .last()
                )

                output = output.merge(
                    modeled.rename(
                        target_column
                    ),
                    on="bucket_hour",
                    how="left",
                )

            else:
                output[
                    target_column
                ] = None

    return output


def build_report(hourly):
    report = {
        "status": "ok",
        "engine_version": ENGINE_VERSION,
        "station_id": STATION_ID,
        "station_name": STATION_NAME,

        "environment": "FIELD",

        "validation_scope":
            "INITIAL_FIELD_OPERATION",

        "field_start_local":
            FIELD_START_LOCAL,

        "field_start_utc":
            FIELD_START_UTC,

        "station_elevation_m":
            STATION_ELEVATION_M,

        "era5_site_tag":
            ERA5_SITE_TAG,

        "nasa_site_tag":
            NASA_SITE_TAG,

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "hourly_rows":
            int(len(hourly)),

        "methodology": {
            "temporal_resolution":
                "hourly",

            "pairing":
                "exact bucket_hour UTC",

            "laboratory_data":
                "excluded before field_start_utc",

            "missing_values":
                "not interpolated",

            "model_calibration":
                "none inherited from CU01",

            "statistical_maturity": {
                "0":
                    "NOT_AVAILABLE",

                "1-23":
                    "PRELIMINARY",

                "24-167":
                    "INTERMEDIATE",

                "168+":
                    "MATURE",
            },

            "warning": (
                "PRELIMINARY, INTERMEDIATE and "
                "MATURE describe sample availability, "
                "not model accuracy."
            ),
        },

        "variables": {},
    }

    # Metadatos científicos de armonización vertical
    # ERA5-Land específicos de Cerro San José.
    report[
        "methodology"
    ][
        "era5_vertical_harmonization"
    ] = {
        "status":
            "enabled",

        "site_tag":
            ERA5_SITE_TAG,

        "station_elevation_m":
            STATION_ELEVATION_M,

        "era5_model_elevation_m":
            ERA5_MODEL_ELEVATION_M,

        "elevation_difference_m":
            round(
                STATION_ELEVATION_M
                - ERA5_MODEL_ELEVATION_M,
                2,
            ),

        "era5_grid_cell":
            {
                "latitude":
                    -6.8,

                "longitude":
                    -78.6,
            },

        "geopotential_m2_s2":
            34934.984,

        "elevation_source":
            (
                "ERA5-Land geopotential "
                "downloaded from Copernicus CDS"
            ),

        "pressure": {
            "status":
                "altitude_normalized",

            "raw_column":
                "era5_press_hpa",

            "derived_column":
                "era5_press_station_hpa",

            "method":
                "hypsometric_equation",
        },

        "humidity": {
            "status":
                "altitude_normalized",

            "temperature_column":
                "era5_temp_c",

            "dewpoint_column":
                "era5_dewpoint_c",

            "derived_column":
                "era5_rh_station_pct",

            "temperature_lapse_rate_k_m":
                STANDARD_LAPSE_RATE_K_M,

            "dewpoint_lapse_rate_k_m":
                DEWPOINT_LAPSE_RATE_K_M,
        },

        "raw_era5_values":
            "preserved",
    }


    # -----------------------------------------------------
    # Metadatos cientificos NASA POWER / GEOS-IT.
    #
    # La elevacion de 2749.53 m procede del tercer
    # elemento de geometry.coordinates devuelto por
    # NASA POWER para SM_SAN_JOSE.
    #
    # La armonizacion es fisica; no se hereda el
    # bias empirico de presion calculado para CU01.
    # -----------------------------------------------------

    report[
        "methodology"
    ][
        "nasa_vertical_harmonization"
    ] = {
        "status":
            "enabled",

        "site_tag":
            NASA_SITE_TAG,

        "station_elevation_m":
            STATION_ELEVATION_M,

        "nasa_model_elevation_m":
            NASA_MODEL_ELEVATION_M,

        "elevation_difference_m":
            round(
                STATION_ELEVATION_M
                - NASA_MODEL_ELEVATION_M,
                2,
            ),

        "nasa_product":
            "NASA POWER Hourly",

        "model_source":
            "GEOSIT",

        "api_geometry_coordinates": {
            "longitude":
                -78.602,

            "latitude":
                -6.764,

            "elevation_m":
                NASA_MODEL_ELEVATION_M,
        },

        "elevation_source":
            (
                "NASA POWER API "
                "geometry.coordinates[2]"
            ),

        "pressure": {
            "status":
                "altitude_normalized",

            "raw_column":
                "nasa_press_hpa",

            "temperature_column":
                "nasa_temp_c",

            "derived_column":
                "nasa_press_station_hpa",

            "method":
                "hypsometric_equation",

            "empirical_bias_correction":
                "none",
        },

        "raw_nasa_values":
            "preserved",

        "cu01_bias_inherited":
            False,

        "note": (
            "NASA POWER PS is normalized from "
            "the GEOS-IT surface elevation "
            "reported by the API for "
            "SM_SAN_JOSE to the physical SJ01 "
            "elevation. No CU01 empirical "
            "pressure bias is inherited."
        ),
    }


    # -----------------------------------------------------
    # Metadatos de comparabilidad vertical del viento.
    #
    # El anemómetro SJ01 está instalado a 10 m AGL.
    # ERA5-Land utiliza componentes u10/v10 a 10 m AGL.
    # NASA POWER utilizado por AtmosLink corresponde a
    # viento de referencia a 10 m.
    #
    # No se aplica transformación vertical a la velocidad
    # del viento por coincidencia de altura nominal.
    # -----------------------------------------------------

    report[
        "methodology"
    ][
        "wind_height_harmonization"
    ] = {
        "status":
            "HEIGHT_MATCHED",

        "local_sensor_height_agl_m":
            WIND_SENSOR_HEIGHT_AGL_M,

        "era5_reference_height_agl_m":
            10.0,

        "nasa_reference_height_agl_m":
            10.0,

        "era5_height_difference_m":
            (
                WIND_SENSOR_HEIGHT_AGL_M
                - 10.0
            ),

        "nasa_height_difference_m":
            (
                WIND_SENSOR_HEIGHT_AGL_M
                - 10.0
            ),

        "vertical_adjustment":
            "not_required",

        "local_sensor":
            "anemometer",

        "era5_variable":
            "10 m wind from u10/v10",

        "nasa_variable":
            "wind speed at 10 m",

        "height_reference":
            "AGL",

        "note": (
            "The SJ01 anemometer is installed "
            "at the same nominal 10 m AGL "
            "reference height used by the "
            "ERA5-Land and NASA POWER wind "
            "products used by AtmosLink."
        ),
    }


    if not hourly.empty:
        report[
            "campaign_end_hour"
        ] = str(
            hourly[
                "bucket_hour"
            ].max()
        )
    else:
        report[
            "campaign_end_hour"
        ] = None

    for key, config in VARIABLES.items():

        variable_report = {
            "label":
                config["label"],

            "unit":
                config["unit"],

            "observed_column":
                f"{key}_observed",

            "models": {},
        }

        for model in (
            "era5",
            "nasa",
        ):

            observed_column = (
                f"{key}_observed"
            )

            model_column = (
                f"{key}_{model}"
            )

            if (
                hourly.empty
                or observed_column
                not in hourly.columns
                or model_column
                not in hourly.columns
            ):
                metrics = {
                    "count": 0,
                    "maturity":
                        "NOT_AVAILABLE",
                }

            else:
                metrics = safe_metrics(
                    hourly[
                        observed_column
                    ],
                    hourly[
                        model_column
                    ],
                )

            model_report = {
                "source_column":
                    config.get(model),

                "metrics":
                    metrics,
            }

            if config.get(model) is None:

                model_report[
                    "comparison_status"
                ] = "DEFERRED"

                if key == "humidity" and model == "era5":
                    model_report[
                        "reason"
                    ] = (
                        "ERA5 relative humidity "
                        "requires SJ01-specific "
                        "vertical normalization."
                    )

                elif key == "pressure":
                    model_report[
                        "reason"
                    ] = (
                        "Pressure comparison is "
                        "deferred until model "
                        "elevation/reference "
                        "semantics are validated "
                        "for SJ01."
                    )

            else:
                model_report[
                    "comparison_status"
                ] = (
                    "AVAILABLE"
                    if metrics[
                        "count"
                    ] > 0
                    else "WAITING_FOR_PAIRS"
                )

            variable_report[
                "models"
            ][model] = model_report

        report[
            "variables"
        ][key] = variable_report

    return report


def save_outputs(hourly, report):
    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    hourly_path = (
        OUTPUT_DIRECTORY
        / "scientific_hourly_SJ01.csv"
    )

    report_path = (
        OUTPUT_DIRECTORY
        / "validation_SJ01_v2.json"
    )

    hourly.to_csv(
        hourly_path,
        index=False,
        encoding="utf-8",
    )

    report_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return hourly_path, report_path


def print_summary(report):
    print("=" * 80)
    print(
        " AtmosLink Scientific Validation - SJ01 FIELD"
    )
    print("=" * 80)

    print(
        "Estacion          :",
        report["station_id"],
    )

    print(
        "Ambiente          :",
        report["environment"],
    )

    print(
        "Inicio FIELD      :",
        report["field_start_local"],
    )

    print(
        "Filas horarias    :",
        report["hourly_rows"],
    )

    print(
        "Fin analizado     :",
        report["campaign_end_hour"],
    )

    print("-" * 80)

    for variable in (
        report["variables"].values()
    ):

        print(
            variable["label"],
            f"({variable['unit']})"
        )

        for model_name, model in (
            variable[
                "models"
            ].items()
        ):

            metrics = model[
                "metrics"
            ]

            print(
                f"  {model_name.upper():5s}"
                f" | N={metrics['count']}"
                f" | {metrics['maturity']}"
                f" | "
                f"{model['comparison_status']}"
            )

        print("-" * 80)


def main():
    if not DATABASE.exists():
        print(
            "[ERROR] No existe:",
            DATABASE,
        )
        return

    try:
        field = load_field_data()

        print(
            "Filas FIELD cargadas:",
            len(field),
        )

        hourly = build_hourly(
            field
        )

        report = build_report(
            hourly
        )

        hourly_path, report_path = (
            save_outputs(
                hourly,
                report,
            )
        )

        print_summary(
            report
        )

        print(
            "Dataset horario :",
            hourly_path,
        )

        print(
            "Reporte JSON    :",
            report_path,
        )

        print(
            "Status: OK"
        )

    except Exception as exc:
        print(
            "[ERROR]",
            type(exc).__name__,
            str(exc),
        )


if __name__ == "__main__":
    main()
