"""
AtmosLink Research Platform
Multi-station Dashboard API

Rutas:
    GET /api/stations
    GET /api/station/latest?station_id=SJ01
    GET /api/station/history?station_id=SJ01&limit=180

La API utiliza master_observations_multistation sin modificar las rutas
clásicas del dashboard productivo.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Blueprint, jsonify, request

from weather_station.config.station_manager import get_station_context


BASE_DIR = Path(__file__).resolve().parents[2]
STATION_CONTEXT = get_station_context()
DB_FILE = BASE_DIR / STATION_CONTEXT["database"]

MULTISTATION_TABLE = "master_observations_multistation"

multistation_api = Blueprint(
    "multistation_api",
    __name__,
)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(
        DB_FILE,
        timeout=30,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


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


def clean_timestamp(value: Any) -> str | None:
    if value is None:
        return None

    return str(value).replace("T", " ")


def parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None

    try:
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except (TypeError, ValueError):
        return None


def observation_age_seconds(value: Any) -> int | None:
    timestamp = parse_timestamp(value)

    if timestamp is None:
        return None

    now = datetime.now(
        timestamp.tzinfo
    ) if timestamp.tzinfo else datetime.now()

    return max(
        int((now - timestamp).total_seconds()),
        0,
    )


def observation_state(
    age_seconds: int | None,
) -> str:
    """
    Estado operacional canónico de AtmosLink.

    ONLINE  : observación dentro del ciclo normal.
    DELAYED : retraso operativo recuperable.
    STALE   : observación antigua.
    OFFLINE : interrupción confirmada.
    UNKNOWN : no existe timestamp evaluable.
    """
    if age_seconds is None:
        return "UNKNOWN"

    if age_seconds <= 420:
        return "ONLINE"

    if age_seconds <= 900:
        return "DELAYED"

    if age_seconds <= 1800:
        return "STALE"

    return "OFFLINE"


def wind_direction_text(
    degrees: Any,
) -> str | None:
    if degrees is None:
        return None

    try:
        value = float(degrees) % 360
    except (TypeError, ValueError):
        return None

    labels = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]

    index = int(
        (value + 11.25) // 22.5
    ) % 16

    return labels[index]


def normalize_station_id(
    station_id: str | None,
) -> str:
    value = (
        station_id
        or ""
    ).strip().upper()

    if not value:
        raise ValueError(
            "Debe indicar station_id."
        )

    if not all(
        character.isalnum()
        or character in {"-", "_"}
        for character in value
    ):
        raise ValueError(
            "station_id contiene caracteres no permitidos."
        )

    return value


def safe_limit(
    raw_value: str | None,
    default: int = 180,
    maximum: int = 5000,
) -> int:
    try:
        value = int(
            raw_value
            if raw_value is not None
            else default
        )
    except (TypeError, ValueError):
        value = default

    return max(
        1,
        min(value, maximum),
    )


def station_exists(
    conn: sqlite3.Connection,
    station_id: str,
) -> bool:
    row = conn.execute(
        f"""
        SELECT 1
        FROM {MULTISTATION_TABLE}
        WHERE station_id = ?
        LIMIT 1
        """,
        (station_id,),
    ).fetchone()

    return row is not None


def normalize_master_row(
    row: sqlite3.Row,
) -> dict[str, Any]:
    data = dict(row)

    timestamp_local = (
        data.get("weather_timestamp_local")
        or data.get("master_timestamp_local")
        or data.get("bucket_minute")
    )

    age_seconds = observation_age_seconds(
        timestamp_local
    )

    payload = {
        "station_id": data.get("station_id"),
        "station_name": data.get("station_name"),
        "radio_role": data.get("radio_role"),

        "bucket_minute": clean_timestamp(
            data.get("bucket_minute")
        ),
        "bucket_hour": clean_timestamp(
            data.get("bucket_hour")
        ),
        "timestamp_local": clean_timestamp(
            timestamp_local
        ),
        "weather_timestamp_local": clean_timestamp(
            data.get("weather_timestamp_local")
        ),
        "weather_timestamp_utc": clean_timestamp(
            data.get("weather_timestamp_utc")
        ),

        "temp_avg_C": data.get(
            "local_temp_avg_c"
        ),
        "temp_min_C": data.get(
            "local_temp_min_c"
        ),
        "temp_max_C": data.get(
            "local_temp_max_c"
        ),

        "hum_avg_pct": data.get(
            "local_hum_avg_pct"
        ),
        "hum_min_pct": data.get(
            "local_hum_min_pct"
        ),
        "hum_max_pct": data.get(
            "local_hum_max_pct"
        ),

        "pres_avg_hPa": data.get(
            "local_press_hpa"
        ),
        "dew_point_C": data.get(
            "local_dew_point_c"
        ),
        "vapor_pressure_hPa": data.get(
            "local_vapor_pressure_hpa"
        ),

        "rain_1min_mm": data.get(
            "local_rain_1min_mm"
        ),
        "rain_1h_mm": data.get(
            "local_rain_1h_mm"
        ),
        "rain_total_mm": data.get(
            "local_rain_total_mm"
        ),
        "pulses_delta": data.get(
            "local_pulses_delta"
        ),
        "pulses_total": data.get(
            "local_pulses_total"
        ),

        "wind_speed_ms": data.get(
            "local_wind_speed_ms"
        ),
        "wind_direction_deg": data.get(
            "local_wind_direction_deg"
        ),
        "wind_direction_text": wind_direction_text(
            data.get(
                "local_wind_direction_deg"
            )
        ),
        "wind_gust_ms": data.get(
            "local_wind_gust_ms"
        ),

        "bme_ok": data.get(
            "local_bme_ok"
        ),
        "rain_ok": data.get(
            "local_rain_ok"
        ),
        "wind_ok": data.get(
            "local_wind_ok"
        ),

        "firmware_version": data.get(
            "firmware_version"
        ),
        "firmware_build": data.get(
            "firmware_build"
        ),
        "device_id": data.get(
            "device_id"
        ),

        "radio": {
            "station_id": data.get(
                "radio_station_id"
            ),
            "timestamp_local": clean_timestamp(
                data.get(
                    "radio_timestamp_local"
                )
            ),
            "mcs_dl": data.get(
                "radio_mcs_dl"
            ),
            "mcs_ul": data.get(
                "radio_mcs_ul"
            ),
            "snr_dl": data.get(
                "radio_snr_dl"
            ),
            "snr_ul": data.get(
                "radio_snr_ul"
            ),
            "rssi_c0p": data.get(
                "radio_rssi_c0p"
            ),
            "rssi_c1p": data.get(
                "radio_rssi_c1p"
            ),
            "dl_rate": data.get(
                "radio_dl_rate"
            ),
            "ul_rate": data.get(
                "radio_ul_rate"
            ),
            "note": data.get(
                "radio_note"
            ),
            "error": data.get(
                "radio_error"
            ),
        },

        "era5": {
            "site_tag": data.get(
                "era5_site_tag"
            ),
            "timestamp_local": clean_timestamp(
                data.get(
                    "era5_timestamp_local"
                )
            ),
            "temp_c": data.get(
                "era5_temp_c"
            ),
            "rh_pct": data.get(
                "era5_rh_pct"
            ),
            "precip_mm": data.get(
                "era5_precip_mm"
            ),
            "press_hpa": data.get(
                "era5_press_hpa"
            ),
            "wind_ms": data.get(
                "era5_wind_ms"
            ),
        },

        "nasa_power": {
            "site_tag": data.get(
                "nasa_site_tag"
            ),
            "timestamp_local": clean_timestamp(
                data.get(
                    "nasa_timestamp_local"
                )
            ),
            "temp_c": data.get(
                "nasa_temp_c"
            ),
            "rh_pct": data.get(
                "nasa_rh_pct"
            ),
            "precip_mm": data.get(
                "nasa_precip_mm"
            ),
            "press_hpa": data.get(
                "nasa_press_hpa"
            ),
            "wind10m_ms": data.get(
                "nasa_wind10m_ms"
            ),
        },

        "source_kind": data.get(
            "source_kind"
        ),
        "source_station_id": data.get(
            "source_station_id"
        ),
        "source_local_id": data.get(
            "source_local_id"
        ),
        "source_db": data.get(
            "source_db"
        ),

        "observation_age_seconds": age_seconds,
        "observation_state": observation_state(
            age_seconds
        ),
    }

    return payload


@multistation_api.route(
    "/api/stations",
    methods=["GET"],
)
def api_stations():
    conn = get_connection()

    try:
        if not table_exists(
            conn,
            MULTISTATION_TABLE,
        ):
            return jsonify(
                {
                    "status": "error",
                    "error": (
                        "No existe "
                        f"{MULTISTATION_TABLE}."
                    ),
                    "stations": [],
                }
            ), 503

        rows = conn.execute(
            f"""
            SELECT
                station_id,
                MAX(station_name) AS station_name,
                MAX(radio_role) AS radio_role,
                COUNT(*) AS total_records,
                MIN(
                    COALESCE(
                        weather_timestamp_local,
                        bucket_minute
                    )
                ) AS first_timestamp,
                MAX(
                    COALESCE(
                        weather_timestamp_local,
                        bucket_minute
                    )
                ) AS last_timestamp
            FROM {MULTISTATION_TABLE}
            WHERE station_id IS NOT NULL
            GROUP BY station_id
            ORDER BY station_id
            """
        ).fetchall()

        stations = []

        for row in rows:
            data = dict(row)

            age_seconds = observation_age_seconds(
                data.get("last_timestamp")
            )

            data["first_timestamp"] = clean_timestamp(
                data.get("first_timestamp")
            )
            data["last_timestamp"] = clean_timestamp(
                data.get("last_timestamp")
            )
            data["age_seconds"] = age_seconds
            data["status"] = observation_state(
                age_seconds
            )

            stations.append(data)

        return jsonify(
            {
                "status": "ok",
                "count": len(stations),
                "stations": stations,
            }
        )

    finally:
        conn.close()


@multistation_api.route(
    "/api/station/latest",
    methods=["GET"],
)
def api_station_latest():
    try:
        station_id = normalize_station_id(
            request.args.get("station_id")
        )
    except ValueError as exc:
        return jsonify(
            {
                "status": "error",
                "error": str(exc),
            }
        ), 400

    conn = get_connection()

    try:
        if not table_exists(
            conn,
            MULTISTATION_TABLE,
        ):
            return jsonify(
                {
                    "status": "error",
                    "error": (
                        "No existe "
                        f"{MULTISTATION_TABLE}."
                    ),
                }
            ), 503

        if not station_exists(
            conn,
            station_id,
        ):
            return jsonify(
                {
                    "status": "error",
                    "error": (
                        "Estación no encontrada."
                    ),
                    "station_id": station_id,
                }
            ), 404

        row = conn.execute(
            f"""
            SELECT *
            FROM {MULTISTATION_TABLE}
            WHERE station_id = ?
              AND local_temp_avg_c IS NOT NULL
            ORDER BY bucket_minute DESC
            LIMIT 1
            """,
            (station_id,),
        ).fetchone()

        if row is None:
            return jsonify(
                {
                    "status": "error",
                    "error": (
                        "La estación no tiene "
                        "observaciones válidas."
                    ),
                    "station_id": station_id,
                }
            ), 404

        payload = normalize_master_row(
            row
        )

        # La tabla maestra puede contener una observación
        # meteorológica más reciente que su consolidación RF.
        # En ese caso, incorporar únicamente telemetría RF
        # real, reciente y asociada a la estación solicitada.
        radio_payload = payload.get("radio") or {}

        radio_metrics = (
            radio_payload.get("mcs_dl"),
            radio_payload.get("mcs_ul"),
            radio_payload.get("snr_dl"),
            radio_payload.get("snr_ul"),
            radio_payload.get("rssi_c0p"),
            radio_payload.get("rssi_c1p"),
            radio_payload.get("dl_rate"),
            radio_payload.get("ul_rate"),
        )

        if (
            not any(
                value is not None
                for value in radio_metrics
            )
            and table_exists(
                conn,
                "radio_link_local",
            )
        ):
            radio_row = conn.execute(
                """
                SELECT *
                FROM radio_link_local
                WHERE station_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (station_id,),
            ).fetchone()

            if radio_row is not None:
                radio_data = dict(radio_row)

                radio_age = observation_age_seconds(
                    radio_data.get(
                        "timestamp_local"
                    )
                )

                invalid_notes = {
                    "RADIO_UNAVAILABLE",
                    "SM_NOT_ASSOCIATED",
                    "NOT_AVAILABLE",
                    "NO_TELEMETRY",
                }

                radio_note = (
                    radio_data.get("note")
                    or ""
                ).strip().upper()

                if (
                    radio_age is not None
                    and radio_age <= 900
                    and radio_note
                    not in invalid_notes
                ):
                    downlink_rssi = (
                        radio_data.get(
                            "sta_dl_rssi"
                        )
                    )

                    if downlink_rssi is None:
                        downlink_rssi = (
                            radio_data.get(
                                "rssi_c0p"
                            )
                        )

                    uplink_rssi = (
                        radio_data.get(
                            "sta_ul_rssi"
                        )
                    )

                    if uplink_rssi is None:
                        uplink_rssi = (
                            radio_data.get(
                                "rssi_c1p"
                            )
                        )

                    payload["radio"] = {
                        "station_id": (
                            radio_data.get(
                                "station_id"
                            )
                        ),
                        "timestamp_local": (
                            clean_timestamp(
                                radio_data.get(
                                    "timestamp_local"
                                )
                            )
                        ),
                        "mcs_dl": radio_data.get(
                            "mcs_dl"
                        ),
                        "mcs_ul": radio_data.get(
                            "mcs_ul"
                        ),
                        "snr_dl": radio_data.get(
                            "snr_dl"
                        ),
                        "snr_ul": radio_data.get(
                            "snr_ul"
                        ),
                        "rssi_c0p": downlink_rssi,
                        "rssi_c1p": uplink_rssi,
                        "sta_dl_rssi": downlink_rssi,
                        "sta_ul_rssi": uplink_rssi,
                        "dl_rate": radio_data.get(
                            "dl_rate"
                        ),
                        "ul_rate": radio_data.get(
                            "ul_rate"
                        ),
                        "note": radio_data.get(
                            "note"
                        ),
                        "error": radio_data.get(
                            "error"
                        ),
                        "source": radio_data.get(
                            "source"
                        ),
                        "age_seconds": radio_age,
                    }

        payload["status"] = "ok"

        return jsonify(payload)

    finally:
        conn.close()


@multistation_api.route(
    "/api/station/history",
    methods=["GET"],
)
def api_station_history():
    try:
        station_id = normalize_station_id(
            request.args.get("station_id")
        )
    except ValueError as exc:
        return jsonify(
            {
                "status": "error",
                "error": str(exc),
            }
        ), 400

    limit = safe_limit(
        request.args.get("limit"),
        default=180,
        maximum=5000,
    )

    conn = get_connection()

    try:
        if not table_exists(
            conn,
            MULTISTATION_TABLE,
        ):
            return jsonify(
                {
                    "status": "error",
                    "error": (
                        "No existe "
                        f"{MULTISTATION_TABLE}."
                    ),
                    "records": [],
                }
            ), 503

        if not station_exists(
            conn,
            station_id,
        ):
            return jsonify(
                {
                    "status": "error",
                    "error": (
                        "Estación no encontrada."
                    ),
                    "station_id": station_id,
                    "records": [],
                }
            ), 404

        rows = conn.execute(
            f"""
            SELECT *
            FROM {MULTISTATION_TABLE}
            WHERE station_id = ?
              AND local_temp_avg_c IS NOT NULL
            ORDER BY bucket_minute DESC
            LIMIT ?
            """,
            (
                station_id,
                limit,
            ),
        ).fetchall()

        records = [
            normalize_master_row(row)
            for row in reversed(rows)
        ]

        return jsonify(
            {
                "status": "ok",
                "station_id": station_id,
                "count": len(records),
                "limit": limit,
                "records": records,
            }
        )

    finally:
        conn.close()


# ==========================================================
# ATMOSLINK SCIENTIFIC COMPARISON API
# ==========================================================

SCIENTIFIC_SITE_MAPPING = {
    "CU01": {
        "era5": "AP_CUNACALES",
        "nasa": "AP_CUNACALES",
    },
    "SJ01": {
        "era5": "SM_SAN_JOSE",
        "nasa": "SM_SAN_JOSE",
    },
}


def scientific_float(value):
    """
    Convierte un valor a float de forma segura.
    """
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def scientific_difference(
    model_value,
    observed_value,
):
    """
    Diferencia modelo - observado.
    """
    model = scientific_float(model_value)
    observed = scientific_float(observed_value)

    if model is None or observed is None:
        return None

    return round(
        model - observed,
        4,
    )


def scientific_absolute_error(
    model_value,
    observed_value,
):
    """
    Error absoluto |modelo - observado|.
    """
    difference = scientific_difference(
        model_value,
        observed_value,
    )

    if difference is None:
        return None

    return round(
        abs(difference),
        4,
    )


def scientific_age_seconds(
    newer_timestamp,
    older_timestamp,
):
    """
    Calcula la diferencia temporal absoluta entre dos fechas.
    """
    newer = parse_timestamp(newer_timestamp)
    older = parse_timestamp(older_timestamp)

    if newer is None or older is None:
        return None

    try:
        return int(
            abs(
                (
                    newer - older
                ).total_seconds()
            )
        )
    except TypeError:
        return None


def scientific_age_label(seconds):
    if seconds is None:
        return None

    if seconds < 60:
        return f"{seconds} s"

    if seconds < 3600:
        return (
            f"{seconds / 60:.1f} min"
        )

    if seconds < 86400:
        return (
            f"{seconds / 3600:.1f} h"
        )

    return (
        f"{seconds / 86400:.1f} días"
    )


def scientific_local_payload(row):
    if row is None:
        return None

    data = dict(row)

    return {
        "station_id": data.get(
            "station_id"
        ),
        "station_name": data.get(
            "station_name"
        ),
        "timestamp_local": clean_timestamp(
            data.get(
                "weather_timestamp_local"
            )
            or data.get(
                "master_timestamp_local"
            )
            or data.get(
                "bucket_minute"
            )
        ),
        "bucket_hour": clean_timestamp(
            data.get(
                "bucket_hour"
            )
        ),
        "temperature_c": data.get(
            "local_temp_avg_c"
        ),
        "humidity_pct": data.get(
            "local_hum_avg_pct"
        ),
        "pressure_hpa": data.get(
            "local_press_hpa"
        ),
        "dewpoint_c": data.get(
            "local_dew_point_c"
        ),
        "precipitation_mm": data.get(
            "local_rain_1h_mm"
        ),
        "wind_ms": data.get(
            "local_wind_speed_ms"
        ),
        "wind_direction_deg": data.get(
            "local_wind_direction_deg"
        ),
        "bme_ok": data.get(
            "local_bme_ok"
        ),
        "rain_ok": data.get(
            "local_rain_ok"
        ),
        "wind_ok": data.get(
            "local_wind_ok"
        ),
    }


def scientific_era5_payload(row):
    if row is None:
        return None

    data = dict(row)

    return {
        "site_tag": data.get(
            "site_tag"
        ),
        "timestamp_local": clean_timestamp(
            data.get(
                "timestamp_local"
            )
        ),
        "latitude": data.get(
            "lat"
        ),
        "longitude": data.get(
            "lon"
        ),
        "temperature_c": data.get(
            "temp_c"
        ),
        "dewpoint_c": data.get(
            "dewpoint_c"
        ),
        "humidity_pct": data.get(
            "rh_pct"
        ),
        "precipitation_mm": data.get(
            "precip_mm"
        ),
        "pressure_hpa": data.get(
            "press_hpa"
        ),
        "wind_ms": data.get(
            "wind_ms"
        ),
    }


def scientific_nasa_payload(row):
    if row is None:
        return None

    data = dict(row)

    return {
        "site_tag": data.get(
            "site_tag"
        ),
        "timestamp_local": clean_timestamp(
            data.get(
                "timestamp_local"
            )
        ),
        "latitude": data.get(
            "lat"
        ),
        "longitude": data.get(
            "lon"
        ),
        "temperature_c": data.get(
            "temp_c"
        ),
        "dewpoint_c": data.get(
            "dewpoint_c"
        ),
        "humidity_pct": data.get(
            "rh_pct"
        ),
        "precipitation_mm": data.get(
            "precip_mm"
        ),
        "pressure_hpa": data.get(
            "press_hpa"
        ),
        "pressure_kpa": data.get(
            "press_kpa"
        ),
        "wind_ms": data.get(
            "wind10m_ms"
        ),
        "source": data.get(
            "source"
        ),
        "downloaded_at_utc": clean_timestamp(
            data.get(
                "downloaded_at_utc"
            )
        ),
    }


def scientific_comparison_payload(
    local,
    model,
):
    if local is None or model is None:
        return {
            "available": False,
            "temperature": None,
            "humidity": None,
            "pressure": None,
            "dewpoint": None,
            "precipitation": None,
            "wind": None,
        }

    return {
        "available": True,

        "temperature": {
            "observed": local.get(
                "temperature_c"
            ),
            "model": model.get(
                "temperature_c"
            ),
            "bias_model_minus_observed": (
                scientific_difference(
                    model.get(
                        "temperature_c"
                    ),
                    local.get(
                        "temperature_c"
                    ),
                )
            ),
            "absolute_error": (
                scientific_absolute_error(
                    model.get(
                        "temperature_c"
                    ),
                    local.get(
                        "temperature_c"
                    ),
                )
            ),
            "unit": "°C",
        },

        "humidity": {
            "observed": local.get(
                "humidity_pct"
            ),
            "model": model.get(
                "humidity_pct"
            ),
            "bias_model_minus_observed": (
                scientific_difference(
                    model.get(
                        "humidity_pct"
                    ),
                    local.get(
                        "humidity_pct"
                    ),
                )
            ),
            "absolute_error": (
                scientific_absolute_error(
                    model.get(
                        "humidity_pct"
                    ),
                    local.get(
                        "humidity_pct"
                    ),
                )
            ),
            "unit": "%",
        },

        "pressure": {
            "observed": local.get(
                "pressure_hpa"
            ),
            "model": model.get(
                "pressure_hpa"
            ),
            "bias_model_minus_observed": (
                scientific_difference(
                    model.get(
                        "pressure_hpa"
                    ),
                    local.get(
                        "pressure_hpa"
                    ),
                )
            ),
            "absolute_error": (
                scientific_absolute_error(
                    model.get(
                        "pressure_hpa"
                    ),
                    local.get(
                        "pressure_hpa"
                    ),
                )
            ),
            "unit": "hPa",
        },

        "dewpoint": {
            "observed": local.get(
                "dewpoint_c"
            ),
            "model": model.get(
                "dewpoint_c"
            ),
            "bias_model_minus_observed": (
                scientific_difference(
                    model.get(
                        "dewpoint_c"
                    ),
                    local.get(
                        "dewpoint_c"
                    ),
                )
            ),
            "absolute_error": (
                scientific_absolute_error(
                    model.get(
                        "dewpoint_c"
                    ),
                    local.get(
                        "dewpoint_c"
                    ),
                )
            ),
            "unit": "°C",
        },

        "precipitation": {
            "observed": local.get(
                "precipitation_mm"
            ),
            "model": model.get(
                "precipitation_mm"
            ),
            "bias_model_minus_observed": (
                scientific_difference(
                    model.get(
                        "precipitation_mm"
                    ),
                    local.get(
                        "precipitation_mm"
                    ),
                )
            ),
            "absolute_error": (
                scientific_absolute_error(
                    model.get(
                        "precipitation_mm"
                    ),
                    local.get(
                        "precipitation_mm"
                    ),
                )
            ),
            "unit": "mm",
        },

        "wind": {
            "observed": local.get(
                "wind_ms"
            ),
            "model": model.get(
                "wind_ms"
            ),
            "bias_model_minus_observed": (
                scientific_difference(
                    model.get(
                        "wind_ms"
                    ),
                    local.get(
                        "wind_ms"
                    ),
                )
            ),
            "absolute_error": (
                scientific_absolute_error(
                    model.get(
                        "wind_ms"
                    ),
                    local.get(
                        "wind_ms"
                    ),
                )
            ),
            "unit": "m/s",
        },
    }


@multistation_api.route(
    "/api/station/scientific",
    methods=["GET"],
)
def api_station_scientific():
    try:
        station_id = normalize_station_id(
            request.args.get(
                "station_id"
            )
        )

    except ValueError as exc:
        return jsonify(
            {
                "status": "error",
                "error": str(exc),
            }
        ), 400

    mapping = SCIENTIFIC_SITE_MAPPING.get(
        station_id
    )

    if mapping is None:
        return jsonify(
            {
                "status": "error",
                "error": (
                    "No existe mapeo científico "
                    "para la estación."
                ),
                "station_id": station_id,
            }
        ), 404

    conn = get_connection()

    try:
        if not table_exists(
            conn,
            MULTISTATION_TABLE,
        ):
            return jsonify(
                {
                    "status": "error",
                    "error": (
                        "No existe "
                        f"{MULTISTATION_TABLE}."
                    ),
                }
            ), 503

        local_latest_row = conn.execute(
            f"""
            SELECT *
            FROM {MULTISTATION_TABLE}
            WHERE station_id = ?
              AND local_temp_avg_c IS NOT NULL
            ORDER BY bucket_minute DESC
            LIMIT 1
            """,
            (station_id,),
        ).fetchone()

        if local_latest_row is None:
            return jsonify(
                {
                    "status": "error",
                    "error": (
                        "La estación no tiene "
                        "observaciones locales."
                    ),
                    "station_id": station_id,
                }
            ), 404

        era5_latest_row = conn.execute(
            """
            SELECT
                *,
                (
                    100.0
                    * EXP(
                        (
                            17.625
                            * dewpoint_c
                        )
                        /
                        (
                            243.04
                            + dewpoint_c
                        )
                    )
                    /
                    EXP(
                        (
                            17.625
                            * temp_c
                        )
                        /
                        (
                            243.04
                            + temp_c
                        )
                    )
                ) AS rh_pct
            FROM era5_land_hourly
            WHERE site_tag = ?
            ORDER BY timestamp_local DESC
            LIMIT 1
            """,
            (
                mapping["era5"],
            ),
        ).fetchone()

        nasa_latest_row = conn.execute(
            """
            SELECT *
            FROM nasa_power_hourly
            WHERE site_tag = ?
            ORDER BY timestamp_local DESC
            LIMIT 1
            """,
            (
                mapping["nasa"],
            ),
        ).fetchone()

        strict_row = conn.execute(
            f"""
            SELECT *
            FROM {MULTISTATION_TABLE}
            WHERE station_id = ?
              AND local_temp_avg_c IS NOT NULL
              AND era5_timestamp_local IS NOT NULL
              AND nasa_timestamp_local IS NOT NULL
            ORDER BY bucket_hour DESC,
                     bucket_minute DESC
            LIMIT 1
            """,
            (station_id,),
        ).fetchone()

        local_latest = scientific_local_payload(
            local_latest_row
        )

        era5_latest = scientific_era5_payload(
            era5_latest_row
        )

        nasa_latest = scientific_nasa_payload(
            nasa_latest_row
        )

        local_timestamp = (
            local_latest.get(
                "timestamp_local"
            )
            if local_latest
            else None
        )

        era5_timestamp = (
            era5_latest.get(
                "timestamp_local"
            )
            if era5_latest
            else None
        )

        nasa_timestamp = (
            nasa_latest.get(
                "timestamp_local"
            )
            if nasa_latest
            else None
        )

        era5_age_seconds = scientific_age_seconds(
            local_timestamp,
            era5_timestamp,
        )

        nasa_age_seconds = scientific_age_seconds(
            local_timestamp,
            nasa_timestamp,
        )

        strict_payload = None

        if strict_row is not None:
            strict_data = dict(
                strict_row
            )

            strict_local = {
                "timestamp_local": clean_timestamp(
                    strict_data.get(
                        "weather_timestamp_local"
                    )
                ),
                "bucket_hour": clean_timestamp(
                    strict_data.get(
                        "bucket_hour"
                    )
                ),
                "temperature_c": strict_data.get(
                    "local_temp_avg_c"
                ),
                "humidity_pct": strict_data.get(
                    "local_hum_avg_pct"
                ),
                "pressure_hpa": strict_data.get(
                    "local_press_hpa"
                ),
                "dewpoint_c": strict_data.get(
                    "local_dew_point_c"
                ),
                "precipitation_mm": strict_data.get(
                    "local_rain_1h_mm"
                ),
                "wind_ms": strict_data.get(
                    "local_wind_speed_ms"
                ),
            }

            strict_era5 = {
                "site_tag": strict_data.get(
                    "era5_site_tag"
                ),
                "timestamp_local": clean_timestamp(
                    strict_data.get(
                        "era5_timestamp_local"
                    )
                ),
                "temperature_c": strict_data.get(
                    "era5_temp_c"
                ),
                "humidity_pct": strict_data.get(
                    "era5_rh_pct"
                ),
                "pressure_hpa": strict_data.get(
                    "era5_press_hpa"
                ),
                "dewpoint_c": strict_data.get(
                    "era5_dewpoint_c"
                ),
                "precipitation_mm": strict_data.get(
                    "era5_precip_mm"
                ),
                "wind_ms": strict_data.get(
                    "era5_wind_ms"
                ),
            }

            strict_nasa = {
                "site_tag": strict_data.get(
                    "nasa_site_tag"
                ),
                "timestamp_local": clean_timestamp(
                    strict_data.get(
                        "nasa_timestamp_local"
                    )
                ),
                "temperature_c": strict_data.get(
                    "nasa_temp_c"
                ),
                "humidity_pct": strict_data.get(
                    "nasa_rh_pct"
                ),
                "pressure_hpa": strict_data.get(
                    "nasa_press_hpa"
                ),
                "dewpoint_c": strict_data.get(
                    "nasa_dewpoint_c"
                ),
                "precipitation_mm": strict_data.get(
                    "nasa_precip_mm"
                ),
                "wind_ms": strict_data.get(
                    "nasa_wind10m_ms"
                ),
            }

            strict_payload = {
                "available": True,
                "bucket_hour": clean_timestamp(
                    strict_data.get(
                        "bucket_hour"
                    )
                ),
                "local": strict_local,
                "era5": strict_era5,
                "nasa_power": strict_nasa,
                "era5_comparison": (
                    scientific_comparison_payload(
                        strict_local,
                        strict_era5,
                    )
                ),
                "nasa_comparison": (
                    scientific_comparison_payload(
                        strict_local,
                        strict_nasa,
                    )
                ),
            }

        else:
            strict_payload = {
                "available": False,
                "reason": (
                    "No existe todavía una hora "
                    "con observación local, ERA5 "
                    "y NASA POWER simultáneos."
                ),
            }

        comparison_mode = (
            "STRICT_MATCHED"
            if strict_payload.get(
                "available"
            )
            else "LATEST_AVAILABLE"
        )

        return jsonify(
            {
                "status": "ok",
                "station_id": station_id,
                "site_mapping": mapping,

                "comparison_mode": (
                    comparison_mode
                ),

                "latest_available": {
                    "local": local_latest,
                    "era5": era5_latest,
                    "nasa_power": nasa_latest,

                    "era5_age_seconds": (
                        era5_age_seconds
                    ),
                    "era5_age_label": (
                        scientific_age_label(
                            era5_age_seconds
                        )
                    ),

                    "nasa_age_seconds": (
                        nasa_age_seconds
                    ),
                    "nasa_age_label": (
                        scientific_age_label(
                            nasa_age_seconds
                        )
                    ),

                    "scientifically_comparable": (
                        False
                    ),

                    "warning": (
                        "Los registros latest no deben "
                        "utilizarse para calcular error "
                        "cuando pertenecen a horas "
                        "diferentes."
                    ),
                },

                "strict_matched": (
                    strict_payload
                ),
            }
        )

    finally:
        conn.close()


# ==========================================================
# ATMOSLINK SCIENTIFIC VALIDATION V2 API
# ==========================================================

import json
from pathlib import Path


VALIDATION_REPORTS = {
    "CU01": (
        Path(__file__).resolve().parents[2]
        / "Data"
        / "validation"
        / "validation_CU01_v2.json"
    ),
    "SJ01": (
        Path(__file__).resolve().parents[2]
        / "Data"
        / "validation"
        / "validation_SJ01_v2.json"
    ),
}


@multistation_api.route(
    "/api/scientific/validation",
    methods=["GET"],
)
def api_scientific_validation():
    try:
        station_id = normalize_station_id(
            request.args.get("station_id")
        )
    except ValueError as exc:
        return jsonify(
            {
                "status": "error",
                "error": str(exc),
            }
        ), 400

    report_path = VALIDATION_REPORTS.get(
        station_id
    )

    if report_path is None:
        return jsonify(
            {
                "status": "error",
                "station_id": station_id,
                "error": (
                    "No existe un reporte de validación "
                    "configurado para esta estación."
                ),
            }
        ), 404

    if not report_path.exists():
        return jsonify(
            {
                "status": "error",
                "station_id": station_id,
                "error": (
                    "El reporte de validación todavía "
                    "no ha sido generado."
                ),
                "report_path": str(report_path),
            }
        ), 503

    try:
        payload = json.loads(
            report_path.read_text(
                encoding="utf-8"
            )
        )
    except Exception as exc:
        return jsonify(
            {
                "status": "error",
                "station_id": station_id,
                "error": (
                    "No fue posible leer el reporte "
                    f"de validación: {exc}"
                ),
            }
        ), 500

    payload["report_path"] = str(
        report_path
    )

    return jsonify(payload)


# ==========================================================
# ATMOSLINK SCIENTIFIC HOURLY DATASET API
# ==========================================================

import math
import pandas as pd


SCIENTIFIC_HOURLY_REPORTS = {
    "CU01": (
        Path(__file__).resolve().parents[2]
        / "Data"
        / "validation"
        / "scientific_hourly_CU01.csv"
    ),
}


SCIENTIFIC_VARIABLE_MAPPING = {
    "temperature": {
        "label": "Temperatura",
        "unit": "°C",
        "observed": "local_temp_avg_c",
        "era5": "era5_temp_c",
        "nasa": "nasa_temp_c",
    },
    "humidity": {
        "label": "Humedad relativa",
        "unit": "%",
        "observed": "local_hum_avg_pct",
        "era5": "era5_rh_pct",
        "nasa": "nasa_rh_pct",
    },
    "pressure": {
        "label": "Presión atmosférica normalizada",
        "unit": "hPa",
        "observed": "local_press_hpa",
        "era5": "era5_press_hpa",
        "nasa": "nasa_press_hpa",
    },
    "dewpoint": {
        "label": "Punto de rocío",
        "unit": "°C",
        "observed": "local_dew_point_c",
        "era5": "era5_dewpoint_c",
        "nasa": "nasa_dewpoint_c",
    },
    "precipitation": {
        "label": "Precipitación horaria",
        "unit": "mm",
        "observed": "local_rain_total_mm",
        "era5": "era5_precip_mm",
        "nasa": "nasa_precip_mm",
    },
    "wind": {
        "label": "Velocidad del viento",
        "unit": "m/s",
        "observed": "local_wind_speed_ms",
        "era5": "era5_wind_ms",
        "nasa": "nasa_wind10m_ms",
    },
}


def scientific_json_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None

    return round(number, 6)


@multistation_api.route(
    "/api/scientific/hourly",
    methods=["GET"],
)
def api_scientific_hourly():
    """
    Devuelve series horarias independientes por estación.

    CU01 utiliza su dataset científico consolidado.
    SJ01 se construye dinámicamente desde global_master,
    exclusivamente desde el inicio de operación en campo.
    """
    try:
        station_id = normalize_station_id(
            request.args.get(
                "station_id",
                "CU01",
            )
        )
    except ValueError as exc:
        return jsonify(
            {
                "status": "error",
                "error": str(exc),
            }
        ), 400

    variable_key = (
        request.args.get(
            "variable",
            "temperature",
        )
        .strip()
        .lower()
    )

    variable = (
        SCIENTIFIC_VARIABLE_MAPPING.get(
            variable_key
        )
    )

    if variable is None:
        return jsonify(
            {
                "status": "error",
                "error": (
                    "Variable científica no válida."
                ),
                "available_variables": list(
                    SCIENTIFIC_VARIABLE_MAPPING
                ),
            }
        ), 400

    if station_id == "SJ01":
        conn = get_connection()

        try:
            dataframe = pd.read_sql_query(
                f"""
                SELECT *
                FROM {MULTISTATION_TABLE}
                WHERE station_id = ?
                  AND local_temp_avg_c
                      IS NOT NULL
                ORDER BY bucket_hour,
                         bucket_minute
                """,
                conn,
                params=("SJ01",),
            )
        finally:
            conn.close()

        if dataframe.empty:
            dataframe = pd.DataFrame(
                columns=[
                    "bucket_hour",
                    variable["observed"],
                    variable["era5"],
                    variable["nasa"],
                ]
            )

        else:
            if (
                "bucket_hour"
                not in dataframe.columns
            ):
                return jsonify(
                    {
                        "status": "error",
                        "station_id": "SJ01",
                        "error": (
                            "La tabla multistación "
                            "no contiene bucket_hour."
                        ),
                    }
                ), 500

            dataframe["_hour_utc"] = (
                pd.to_datetime(
                    dataframe["bucket_hour"],
                    errors="coerce",
                    utc=True,
                )
            )

            field_start_utc = pd.Timestamp(
                "2026-08-31T21:00:00Z"
            )

            dataframe = dataframe[
                dataframe["_hour_utc"].notna()
                & (
                    dataframe["_hour_utc"]
                    >= field_start_utc
                )
            ].copy()

            if not dataframe.empty:
                dataframe["bucket_hour"] = (
                    dataframe["_hour_utc"]
                    .dt.strftime(
                        "%Y-%m-%dT%H:00:00Z"
                    )
                )

                expected_columns = {
                    variable["observed"],
                    variable["era5"],
                    variable["nasa"],
                }

                for column in expected_columns:
                    if (
                        column
                        not in dataframe.columns
                    ):
                        dataframe[column] = None

                observed_column = (
                    variable["observed"]
                )

                model_columns = [
                    variable["era5"],
                    variable["nasa"],
                ]

                aggregation = {
                    observed_column: "mean",
                    model_columns[0]: "last",
                    model_columns[1]: "last",
                }

                if (
                    variable_key
                    == "precipitation"
                ):
                    # Precipitación horaria local derivada de los
                    # incrementos positivos sucesivos del contador
                    # acumulado local_rain_total_mm.
                    #
                    # local_rain_1h_mm no se usa porque representa
                    # una ventana móvil retrospectiva.
                    #
                    # Un salto negativo del acumulado se interpreta
                    # como reset del contador y no como precipitación.
                    dataframe = (
                        dataframe
                        .sort_values(
                            [
                                "_hour_utc",
                                "bucket_minute",
                            ]
                        )
                        .reset_index(drop=True)
                    )

                    dataframe[
                        "_rain_delta_mm"
                    ] = (
                        pd.to_numeric(
                            dataframe[
                                observed_column
                            ],
                            errors="coerce",
                        )
                        .diff()
                    )

                    dataframe.loc[
                        dataframe[
                            "_rain_delta_mm"
                        ] < 0,
                        "_rain_delta_mm",
                    ] = 0.0

                    dataframe[
                        "_rain_delta_mm"
                    ] = (
                        dataframe[
                            "_rain_delta_mm"
                        ]
                        .fillna(0.0)
                    )

                    grouped = (
                        dataframe
                        .groupby(
                            "bucket_hour",
                            as_index=False,
                        )
                        .agg(
                            {
                                "_rain_delta_mm":
                                    "sum",
                                model_columns[0]:
                                    "last",
                                model_columns[1]:
                                    "last",
                            }
                        )
                    )

                    grouped[
                        observed_column
                    ] = grouped[
                        "_rain_delta_mm"
                    ]

                    dataframe = (
                        grouped[
                            [
                                "bucket_hour",
                                observed_column,
                                model_columns[0],
                                model_columns[1],
                            ]
                        ]
                        .sort_values(
                            "bucket_hour"
                        )
                        .reset_index(drop=True)
                    )

                else:
                    dataframe = (
                        dataframe
                        .groupby(
                            "bucket_hour",
                            as_index=False,
                        )
                        .agg(aggregation)
                        .sort_values(
                            "bucket_hour"
                        )
                        .reset_index(drop=True)
                    )

    else:
        path = (
            SCIENTIFIC_HOURLY_REPORTS.get(
                station_id
            )
        )

        if (
            path is None
            or not path.exists()
        ):
            return jsonify(
                {
                    "status": "not_available",
                    "station_id": station_id,
                    "reason": (
                        "No existe el dataset "
                        "horario de validación."
                    ),
                }
            ), 404

        dataframe = pd.read_csv(path)

    required = [
        "bucket_hour",
        variable["observed"],
        variable["era5"],
        variable["nasa"],
    ]

    missing = [
        column
        for column in required
        if column
        not in dataframe.columns
    ]

    if missing:
        return jsonify(
            {
                "status": "error",
                "station_id": station_id,
                "error": (
                    "El dataset no contiene todas "
                    "las columnas requeridas."
                ),
                "missing_columns": missing,
            }
        ), 500

    records = []

    for row in dataframe[
        required
    ].itertuples(
        index=False,
        name=None,
    ):
        timestamp, observed, era5, nasa = row

        observed_value = (
            scientific_json_number(
                observed
            )
        )

        era5_value = (
            scientific_json_number(
                era5
            )
        )

        nasa_value = (
            scientific_json_number(
                nasa
            )
        )

        if (
            observed_value is None
            and era5_value is None
            and nasa_value is None
        ):
            continue

        records.append(
            {
                "timestamp": timestamp,
                "observed": observed_value,
                "era5": era5_value,
                "nasa": nasa_value,
            }
        )

    matched_era5 = sum(
        1
        for record in records
        if (
            record["observed"] is not None
            and record["era5"] is not None
        )
    )

    matched_nasa = sum(
        1
        for record in records
        if (
            record["observed"] is not None
            and record["nasa"] is not None
        )
    )

    return jsonify(
        {
            "status": "ok",
            "station_id": station_id,
            "validation_scope": (
                "INITIAL_FIELD_OPERATION"
                if station_id == "SJ01"
                else "FIELD_VALIDATION"
            ),
            "field_start_local": (
                "2026-08-31 16:00:00-05:00"
                if station_id == "SJ01"
                else None
            ),
            "variable": variable_key,
            "label": variable["label"],
            "unit": variable["unit"],
            "rows": len(records),
            "matched_era5": matched_era5,
            "matched_nasa": matched_nasa,
            "records": records,
        }
    )

