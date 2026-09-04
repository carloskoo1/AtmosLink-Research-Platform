from flask import Flask, render_template, jsonify
import sqlite3
from datetime import datetime
import json
from pathlib import Path
import os

from weather_station.config.station_manager import get_station_context
from weather_station.events.event_logger import log_event, list_events, event_statistics
from weather_station.dashboard.multistation_api import multistation_api


BASE_DIR = Path(__file__).resolve().parents[2]
STATION_CONTEXT = get_station_context()
DB_FILE = BASE_DIR / STATION_CONTEXT["database"]

RUNTIME_DIR = BASE_DIR / "runtime"
HEALTH_FILE = RUNTIME_DIR / "health_status.json"
TASK_REGISTRY_FILE = RUNTIME_DIR / "task_registry.json"
ALERTS_FILE = RUNTIME_DIR / "alerts.json"
QC_SUMMARY_FILE = RUNTIME_DIR / "qc_summary.json"
SCIENTIFIC_HEALTH_FILE = RUNTIME_DIR / "scientific_health_score.json"
SCIENTIFIC_RELIABILITY_FILE = RUNTIME_DIR / "scientific_reliability.json"
SCIENTIFIC_COMPARISON_FILE = RUNTIME_DIR / "scientific_comparison.json"
SCIENTIFIC_AGREEMENT_FILE = RUNTIME_DIR / "scientific_agreement_index.json"
ATMOSPHERIC_CORRIDOR_FILE = RUNTIME_DIR / "atmospheric_corridor.json"

app = Flask(__name__)
app.register_blueprint(multistation_api)


def load_json(path):
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def clean_timestamp(value):
    if value is None:
        return None
    value = str(value).replace("T", " ")
    if value.endswith("-05:00") or value.endswith("+00:00"):
        value = value[:-6]
    return value


def wind_direction_text(deg):
    if deg is None:
        return None
    try:
        deg = float(deg) % 360
    except Exception:
        return None

    labels = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
              "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = int((deg + 11.25) // 22.5) % 16
    return labels[idx]


def table_exists(conn, table_name):
    q = """
    SELECT name FROM sqlite_master
    WHERE type='table' AND name=?
    """
    return conn.execute(q, (table_name,)).fetchone() is not None


def get_columns(conn, table_name):
    if not table_exists(conn, table_name):
        return []
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table_name})").fetchall()]


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def select_expr(columns, column_name, alias=None):
    alias = alias or column_name
    if column_name in columns:
        return f"{column_name} AS {alias}"
    return f"NULL AS {alias}"




def parse_dashboard_datetime(value):
    if not value:
        return None
    try:
        value = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception:
        return None


def seconds_age_label(seconds):
    if seconds is None:
        return "--"
    try:
        seconds = int(seconds)
    except Exception:
        return "--"

    if seconds < 60:
        return f"hace {seconds} s"
    minutes = seconds / 60
    if minutes < 60:
        return f"hace {minutes:.1f} min"
    hours = minutes / 60
    return f"hace {hours:.1f} h"


def age_seconds_from_now(timestamp_value):
    dt = parse_dashboard_datetime(timestamp_value)
    if dt is None:
        return None

    now = datetime.now()
    return max(int((now - dt).total_seconds()), 0)


def wind_installation_requested():
    """
    Indica si el módulo RS485 de viento está habilitado en esta
    instalación. Un sensor deshabilitado no debe mostrarse como error.
    """
    return os.getenv(
        "ATMOSLINK_WIND_ENABLED",
        "0",
    ).strip().lower() in {"1", "true", "yes", "on"}


def scientific_wind_state(
    wind_ok,
    wind_speed,
    wind_direction,
    wind_gust,
    age_seconds,
):
    """
    Distingue entre sensor no instalado, operativo, sin datos y error.
    """
    requested = wind_installation_requested()

    has_measurement = any(
        value is not None
        for value in (
            wind_speed,
            wind_direction,
            wind_gust,
        )
    )

    # Una medición físicamente válida tiene prioridad sobre la
    # configuración histórica de instalación. Esto permite reconocer
    # automáticamente el anemómetro de cada estación.
    if wind_ok in (1, 1.0, True) and has_measurement:
        if age_seconds is not None and age_seconds > 300:
            return "STALE"
        return "OK"

    if not requested and not has_measurement:
        return "NOT_INSTALLED"

    if not has_measurement:
        return "NO_DATA"

    return "ERROR"


def scientific_rain_state(rain_ok, rain_1h):
    """
    Distingue una observación válida de cero lluvia de una falla
    del pluviómetro.
    """
    if rain_ok not in (1, 1.0, True):
        return "ERROR"

    try:
        value = float(rain_1h or 0)
    except (TypeError, ValueError):
        return "NO_DATA"

    if value > 0:
        return "RAIN_DETECTED"

    return "NO_RAIN"


def scientific_observation_state(age_seconds):
    """
    Clasificación visual de vigencia de la observación local.
    """
    if age_seconds is None:
        return "NO_DATA"

    if age_seconds <= 420:
        return "CURRENT"

    if age_seconds <= 900:
        return "DELAYED"

    return "STALE"


def sensor_state(ok_value, age_seconds=None, stale_after_seconds=120):
    try:
        ok = int(float(ok_value)) == 1
    except Exception:
        ok = False

    if not ok:
        return "ERROR"

    if age_seconds is not None and age_seconds > stale_after_seconds:
        return "STALE"

    return "OK"


def age_payload(reference_ts, source_ts):
    ref = parse_dashboard_datetime(reference_ts)
    src = parse_dashboard_datetime(source_ts)

    if not ref or not src:
        return {
            "age_hours": None,
            "age_days": None,
            "age_label": "--",
            "freshness": "unknown",
        }

    delta_hours = max((ref - src).total_seconds() / 3600.0, 0)
    delta_days = delta_hours / 24.0

    if delta_hours < 24:
        label = f"hace {delta_hours:.1f} h"
    else:
        label = f"hace {delta_days:.1f} días"

    if delta_days <= 2:
        freshness = "fresh"
    elif delta_days <= 7:
        freshness = "expected_delay"
    else:
        freshness = "stale"

    return {
        "age_hours": round(delta_hours, 2),
        "age_days": round(delta_days, 2),
        "age_label": label,
        "freshness": freshness,
    }


def parse_dashboard_datetime(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception:
        return None


def build_age_label(reference_ts, source_ts):
    ref = parse_dashboard_datetime(reference_ts)
    src = parse_dashboard_datetime(source_ts)

    if ref is None or src is None:
        return "--"

    hours = max((ref - src).total_seconds() / 3600.0, 0)
    days = hours / 24.0

    if hours < 24:
        return f"hace {hours:.1f} h"

    return f"hace {days:.1f} días"

def get_latest():
    if not DB_FILE.exists():
        return {}

    conn = get_connection()

    if not table_exists(conn, "master_observations"):
        conn.close()
        return {}

    latest_local = conn.execute("""
        SELECT *
        FROM master_observations
        WHERE local_temp_avg_c IS NOT NULL
        ORDER BY bucket_minute DESC
        LIMIT 1
    """).fetchone()

    latest_nasa = conn.execute("""
        SELECT *
        FROM master_observations
        WHERE nasa_timestamp_local IS NOT NULL
        ORDER BY bucket_minute DESC
        LIMIT 1
    """).fetchone()

    latest_era5 = conn.execute("""
        SELECT *
        FROM master_observations
        WHERE era5_timestamp_local IS NOT NULL
        ORDER BY bucket_minute DESC
        LIMIT 1
    """).fetchone()

    latest_radio = conn.execute("""
        SELECT *
        FROM master_observations
        WHERE radio_timestamp_local IS NOT NULL
        ORDER BY bucket_minute DESC
        LIMIT 1
    """).fetchone()

    gust_row = None
    if table_exists(conn, "master_observations"):
        gust_row = conn.execute("""
            SELECT MAX(local_wind_speed_ms) AS gust
            FROM master_observations
            WHERE local_wind_speed_ms IS NOT NULL
              AND datetime(weather_timestamp_local) >= datetime(
                  (SELECT MAX(weather_timestamp_local) FROM master_observations),
                  '-60 seconds'
              )
        """).fetchone()

    conn.close()

    if latest_local is None:
        return {}

    local = dict(latest_local)
    d = dict(local)

    d["timestamp_local"] = clean_timestamp(local.get("master_timestamp_local"))
    d["weather_timestamp_local_clean"] = clean_timestamp(local.get("weather_timestamp_local"))
    d["observation_age_seconds"] = age_seconds_from_now(local.get("weather_timestamp_local") or local.get("master_timestamp_local"))
    d["observation_age_label"] = seconds_age_label(d["observation_age_seconds"])

    d["temp_avg_C"] = local.get("local_temp_avg_c")
    d["hum_avg_pct"] = local.get("local_hum_avg_pct")
    d["pres_avg_hPa"] = local.get("local_press_hpa")
    d["dew_point_C"] = local.get("local_dew_point_c")
    d["vapor_pressure_hPa"] = local.get("local_vapor_pressure_hpa")
    d["rain_1min_mm"] = local.get("local_rain_1min_mm")
    d["rain_1h_mm"] = local.get("local_rain_1h_mm")
    d["rain_total_mm"] = local.get("local_rain_total_mm")
    d["bme_ok"] = local.get("local_bme_ok")
    d["rain_ok"] = local.get("local_rain_ok")

    d["wind_speed_ms"] = local.get("local_wind_speed_ms")
    d["wind_direction_deg"] = local.get("local_wind_direction_deg")
    d["wind_direction_text"] = wind_direction_text(local.get("local_wind_direction_deg"))
    d["wind_gust_ms"] = local.get("local_wind_gust_ms")
    if d["wind_gust_ms"] is None and gust_row is not None:
        d["wind_gust_ms"] = gust_row["gust"]
    d["wind_ok"] = local.get("local_wind_ok")
    d["wind_requested"] = wind_installation_requested()
    d["wind_state"] = scientific_wind_state(
        d["wind_ok"],
        d["wind_speed_ms"],
        d["wind_direction_deg"],
        d["wind_gust_ms"],
        d["observation_age_seconds"],
    )

    d["rain_state"] = scientific_rain_state(
        local.get("local_rain_ok"),
        d.get("rain_1h_mm"),
    )

    d["observation_state"] = scientific_observation_state(
        d["observation_age_seconds"]
    )

    d["scientific_quality"] = {
        "bme280": sensor_state(local.get("local_bme_ok"), d["observation_age_seconds"], 120),
        "rain_gauge": sensor_state(local.get("local_rain_ok"), d["observation_age_seconds"], 120),
        "anemometer": d["wind_state"],
        "era5": "OK" if latest_era5 is not None else "ERROR",
        "nasa_power": "OK" if latest_nasa is not None else "ERROR",
        "radio_link": (
            "OK"
            if latest_radio is not None
            and any(
                dict(latest_radio).get(field) is not None
                for field in (
                    "radio_mcs_dl",
                    "radio_mcs_ul",
                    "radio_snr_dl",
                    "radio_snr_ul",
                    "radio_sta_dl_rssi",
                    "radio_sta_ul_rssi",
                    "radio_dl_rate",
                    "radio_ul_rate",
                )
            )
            else (
                "NO_TELEMETRY"
                if latest_radio is not None
                else "PENDING"
            )
        ),
    }

    if latest_nasa is not None:
        nasa = dict(latest_nasa)
        d["nasa_timestamp_local"] = clean_timestamp(nasa.get("nasa_timestamp_local"))
        d["nasa_temp_c"] = nasa.get("nasa_temp_c")
        d["nasa_dewpoint_c"] = nasa.get("nasa_dewpoint_c")
        d["nasa_rh_pct"] = nasa.get("nasa_rh_pct")
        d["nasa_precip_mm"] = nasa.get("nasa_precip_mm")
        d["nasa_press_hpa"] = nasa.get("nasa_press_hpa")
        d["nasa_wind10m_ms"] = nasa.get("nasa_wind10m_ms")

    if latest_era5 is not None:
        era5 = dict(latest_era5)
        d["era5_timestamp_local"] = clean_timestamp(era5.get("era5_timestamp_local"))
        d["era5_temp_c"] = era5.get("era5_temp_c")
        d["era5_dewpoint_c"] = era5.get("era5_dewpoint_c")
        d["era5_rh_pct"] = era5.get("era5_rh_pct")
        d["era5_precip_mm"] = era5.get("era5_precip_mm")
        d["era5_press_hpa"] = era5.get("era5_press_hpa")
        d["era5_wind_ms"] = era5.get("era5_wind_ms")

    if latest_radio is not None:
        radio = dict(latest_radio)
        d["radio_timestamp_local"] = clean_timestamp(radio.get("radio_timestamp_local"))
        d["radio_mcs_dl"] = radio.get("radio_mcs_dl")
        d["radio_mcs_ul"] = radio.get("radio_mcs_ul")
        d["radio_snr_dl"] = radio.get("radio_snr_dl")
        d["radio_snr_ul"] = radio.get("radio_snr_ul")
        d["radio_sta_dl_rssi"] = radio.get("radio_sta_dl_rssi")
        d["radio_sta_ul_rssi"] = radio.get("radio_sta_ul_rssi")
        d["radio_dl_rate"] = radio.get("radio_dl_rate")
        d["radio_ul_rate"] = radio.get("radio_ul_rate")
        d["radio_note"] = radio.get("radio_note")

    d["era5_age_label"] = build_age_label(d.get("timestamp_local"), d.get("era5_timestamp_local"))
    d["nasa_age_label"] = build_age_label(d.get("timestamp_local"), d.get("nasa_timestamp_local"))

    d["era5_age_label"] = build_age_label(d.get("timestamp_local"), d.get("era5_timestamp_local"))
    d["nasa_age_label"] = build_age_label(d.get("timestamp_local"), d.get("nasa_timestamp_local"))

    return d


def get_history(limit=180):
    """
    Historial científico estrictamente emparejado.

    Solo devuelve registros donde existen simultáneamente:
    - estación local
    - ERA5-Land
    - NASA POWER

    Esto evita comparar curvas de fechas diferentes y permite que los gráficos
    Local vs ERA5 vs NASA sean temporalmente válidos.
    """
    if not DB_FILE.exists():
        return []

    conn = get_connection()

    if not table_exists(conn, "master_observations"):
        conn.close()
        return []

    query = """
        SELECT
            bucket_minute,
            master_timestamp_local,
            master_timestamp_hour,

            weather_timestamp_local,
            era5_timestamp_local,
            nasa_timestamp_local,
            radio_timestamp_local,

            local_temp_avg_c,
            local_hum_avg_pct,
            local_press_hpa,
            local_dew_point_c,
            local_vapor_pressure_hpa,
            local_rain_1min_mm,
            local_rain_1h_mm,
            local_rain_total_mm,
            local_wind_speed_ms,
            local_wind_direction_deg,
            local_wind_gust_ms,
            local_wind_ok,

            era5_temp_c,
            era5_dewpoint_c,
            era5_rh_pct,
            era5_precip_mm,
            era5_press_hpa,
            era5_wind_ms,

            nasa_temp_c,
            nasa_dewpoint_c,
            nasa_rh_pct,
            nasa_precip_mm,
            nasa_press_hpa,
            nasa_wind10m_ms,

            radio_snr_dl,
            radio_snr_ul,
            radio_sta_dl_rssi,
            radio_sta_ul_rssi,
            radio_mcs_dl,
            radio_mcs_ul,
            radio_dl_rate,
            radio_ul_rate,
            radio_note
        FROM master_observations
        WHERE local_temp_avg_c IS NOT NULL
          AND local_hum_avg_pct IS NOT NULL
          AND local_press_hpa IS NOT NULL

          AND era5_temp_c IS NOT NULL
          AND era5_rh_pct IS NOT NULL
          AND era5_press_hpa IS NOT NULL

          AND nasa_temp_c IS NOT NULL
          AND nasa_rh_pct IS NOT NULL
          AND nasa_press_hpa IS NOT NULL
        ORDER BY bucket_minute DESC
        LIMIT ?
    """

    rows = conn.execute(query, (limit,)).fetchall()
    conn.close()

    data = []

    for row in rows:
        d = dict(row)

        for key in [
            "bucket_minute",
            "master_timestamp_local",
            "master_timestamp_hour",
            "weather_timestamp_local",
            "era5_timestamp_local",
            "nasa_timestamp_local",
            "radio_timestamp_local",
        ]:
            if key in d:
                d[key] = clean_timestamp(d.get(key))

        d["history_mode"] = "strict_matched_local_era5_nasa"
        data.append(d)

    data.reverse()
    return data


def get_master_summary():
    if not DB_FILE.exists():
        return {}

    conn = get_connection()

    if not table_exists(conn, "master_observations"):
        conn.close()
        return {}

    row = conn.execute("""
        SELECT
            COUNT(*) AS total_records,
            MIN(master_timestamp_local) AS first_record,
            MAX(master_timestamp_local) AS last_record,
            COUNT(era5_timestamp_local) AS era5_matched_records,
            COUNT(nasa_timestamp_local) AS nasa_matched_records,
            COUNT(radio_timestamp_local) AS radio_matched_records
        FROM master_observations
    """).fetchone()

    conn.close()

    if not row:
        return {}

    d = dict(row)
    d["first_record"] = clean_timestamp(d.get("first_record"))
    d["last_record"] = clean_timestamp(d.get("last_record"))

    return d


def latest_rows_by_site(conn, table_name, site_column="site_tag"):
    if not table_exists(conn, table_name):
        return {}

    rows = conn.execute(f"""
        SELECT t.*
        FROM {table_name} t
        INNER JOIN (
            SELECT {site_column}, MAX(timestamp_local) AS max_timestamp
            FROM {table_name}
            WHERE temp_c IS NOT NULL
               OR rh_pct IS NOT NULL
               OR press_hpa IS NOT NULL
               OR precip_mm IS NOT NULL
               OR wind10m_ms IS NOT NULL
               OR wind_ms IS NOT NULL
            GROUP BY {site_column}
        ) latest
        ON t.{site_column} = latest.{site_column}
        AND t.timestamp_local = latest.max_timestamp
        ORDER BY t.{site_column}
    """).fetchall()

    data = {}

    for row in rows:
        d = dict(row)
        d["timestamp_local"] = clean_timestamp(d.get("timestamp_local"))
        data[d.get(site_column)] = d

    return data


def get_api_v2_overview():
    conn = get_connection()

    payload = {
        "station": STATION_CONTEXT,
        "database": str(DB_FILE),
        "local": {},
        "nasa": {},
        "era5": {},
        "radio": {},
        "scientific": {
            "health": load_json(SCIENTIFIC_HEALTH_FILE),
            "reliability": load_json(SCIENTIFIC_RELIABILITY_FILE),
            "comparison": load_json(SCIENTIFIC_COMPARISON_FILE),
            "agreement": load_json(SCIENTIFIC_AGREEMENT_FILE),
            "qc": load_json(QC_SUMMARY_FILE),
        },
        "system": {
            "health": load_json(HEALTH_FILE),
            "registry": load_json(TASK_REGISTRY_FILE),
            "alerts": load_json(ALERTS_FILE),
            "master_summary": get_master_summary(),
        },
    }

    if table_exists(conn, "station_observations"):
        rows = conn.execute("""
            SELECT so.*
            FROM station_observations so
            INNER JOIN (
                SELECT source_station_id, MAX(timestamp_local) AS max_timestamp
                FROM station_observations
                GROUP BY source_station_id
            ) latest
            ON so.source_station_id = latest.source_station_id
            AND so.timestamp_local = latest.max_timestamp
            ORDER BY so.source_station_id
        """).fetchall()

        for row in rows:
            d = dict(row)
            d["timestamp_local"] = clean_timestamp(d.get("timestamp_local"))
            payload["local"][d.get("source_station_id")] = d

    payload["nasa"] = latest_rows_by_site(conn, "nasa_power_hourly", "site_tag")
    payload["era5"] = latest_rows_by_site(conn, "era5_land_hourly", "site_tag")

    if table_exists(conn, "radio_link_local"):
        row = conn.execute("""
            SELECT *
            FROM radio_link_local
            ORDER BY id DESC
            LIMIT 1
        """).fetchone()

        if row:
            d = dict(row)
            if "timestamp_local" in d:
                d["timestamp_local"] = clean_timestamp(d.get("timestamp_local"))
            payload["radio"]["latest"] = d

    conn.close()
    return payload


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ui-v2")
def ui_v2_dashboard():
    """
    Interfaz AtmosLink UI v2.

    Esta ruta se mantiene en paralelo al dashboard operativo
    principal y consume exclusivamente las API existentes.
    """
    return render_template("v2/dashboard.html")




@app.route("/ui-v2-pro")
def ui_v2_professional():
    return render_template("v2/professional.html")


@app.route("/api/v2/overview")
def api_v2_overview():
    return jsonify(get_api_v2_overview())


@app.route("/api/latest")
def api_latest():
    return jsonify(get_latest())


@app.route("/api/history")
def api_history():
    return jsonify(get_history())



def get_stations_latest():
    conn = get_connection()
    try:
        if table_exists(conn, "master_observations"):
            row = conn.execute("""
                SELECT *
                FROM master_observations
                WHERE local_temp_avg_c IS NOT NULL
                ORDER BY bucket_minute DESC
                LIMIT 1
            """).fetchone()

            if row is not None:
                r = dict(row)
                station_id = STATION_CONTEXT.get("station_id", "CU01")

                return [{
                    "source_station_id": station_id,
                    "station_id": station_id,
                    "station_name": STATION_CONTEXT.get("station_name", "Cerro Cuñacales"),
                    "radio_role": STATION_CONTEXT.get("radio_role", "AP"),
                    "timestamp_local": clean_timestamp(r.get("weather_timestamp_local") or r.get("master_timestamp_local")),
                    "temp_avg_C": r.get("local_temp_avg_c"),
                    "hum_avg_pct": r.get("local_hum_avg_pct"),
                    "pres_avg_hPa": r.get("local_press_hpa"),
                    "rain_total_mm": r.get("local_rain_total_mm"),
                    "bme_ok": r.get("local_bme_ok"),
                    "rain_ok": r.get("local_rain_ok"),
                    "wind_speed_ms": r.get("local_wind_speed_ms"),
                    "wind_direction_deg": r.get("local_wind_direction_deg"),
                    "wind_direction_text": wind_direction_text(r.get("local_wind_direction_deg")),
                    "wind_gust_ms": r.get("local_wind_gust_ms"),
                    "wind_ok": r.get("local_wind_ok"),
                }]

        if not table_exists(conn, "station_observations"):
            return []

        rows = conn.execute("""
            SELECT so.*
            FROM station_observations so
            INNER JOIN (
                SELECT source_station_id, MAX(timestamp_local) AS max_timestamp
                FROM station_observations
                GROUP BY source_station_id
            ) latest
            ON so.source_station_id = latest.source_station_id
            AND so.timestamp_local = latest.max_timestamp
            ORDER BY so.source_station_id
        """).fetchall()

        out = []
        for row in rows:
            d = dict(row)
            d["timestamp_local"] = clean_timestamp(d.get("timestamp_local"))
            d["wind_direction_text"] = wind_direction_text(d.get("wind_direction_deg"))
            out.append(d)

        return out
    finally:
        conn.close()

@app.route("/api/stations/latest")
def api_stations_latest():
    return jsonify(get_stations_latest())



def wind_sector_16(deg):
    if deg is None:
        return None
    try:
        deg = float(deg) % 360
    except Exception:
        return None

    labels = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
              "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = int((deg + 11.25) // 22.5) % 16
    return idx, labels[idx]


def get_windrose(
    period="24h",
    station_id="CU01",
    selected_date=None,
):
    """
    Calcula una rosa de vientos local de 16 sectores.

    La fuente central station_observations permite consultar
    CU01 y SJ01 sin acceder directamente al equipo remoto.
    """
    conn = get_connection()

    labels = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW",
    ]

    try:
        if not table_exists(
            conn,
            "station_observations",
        ):
            return {
                "status": "not_available",
                "station_id": station_id,
                "period": period,
                "reason": (
                    "No existe la tabla central "
                    "station_observations."
                ),
                "samples": 0,
                "sectors": [],
            }

        where = """
            station_id = ?
            AND wind_speed_ms IS NOT NULL
            AND wind_direction_deg IS NOT NULL
            AND wind_ok = 1
        """

        parameters = [station_id]

        if selected_date:
            where += """
                AND substr(timestamp_local, 1, 10) = ?
            """
            parameters.append(selected_date)

        elif period == "24h":
            where += """
                AND datetime(timestamp_local)
                    >= datetime(
                        'now',
                        'localtime',
                        '-24 hours'
                    )
            """
        elif period == "7d":
            where += """
                AND datetime(timestamp_local)
                    >= datetime(
                        'now',
                        'localtime',
                        '-7 days'
                    )
            """
        elif period == "30d":
            where += """
                AND datetime(timestamp_local)
                    >= datetime(
                        'now',
                        'localtime',
                        '-30 days'
                    )
            """

        rows = conn.execute(
            f"""
            SELECT
                timestamp_local,
                wind_speed_ms,
                wind_direction_deg,
                wind_gust_ms
            FROM station_observations
            WHERE {where}
            ORDER BY timestamp_local ASC
            """,
            parameters,
        ).fetchall()

        sectors = {
            label: {
                "sector": label,
                "count": 0,
                "frequency_pct": 0.0,
                "speed_sum_ms": 0.0,
                "speed_avg_ms": None,
                "speed_max_ms": None,
            }
            for label in labels
        }

        total = 0
        calm_samples = 0
        speed_sum = 0.0
        speed_max = None
        gust_max = None
        first_timestamp = None
        last_timestamp = None

        for row in rows:
            try:
                speed = float(row["wind_speed_ms"])
                direction = (
                    float(row["wind_direction_deg"])
                    % 360.0
                )
            except (TypeError, ValueError):
                continue

            sector = wind_sector_16(direction)

            if sector is None:
                continue

            gust = row["wind_gust_ms"]

            if gust is not None:
                try:
                    gust = float(gust)

                    if (
                        gust_max is None
                        or gust > gust_max
                    ):
                        gust_max = gust
                except (TypeError, ValueError):
                    pass

            total += 1
            speed_sum += speed

            if speed_max is None or speed > speed_max:
                speed_max = speed

            timestamp = row["timestamp_local"]

            if speed < 0.5:
                calm_samples += 1

                if first_timestamp is None:
                    first_timestamp = timestamp

                last_timestamp = timestamp
                continue

            _, label = sector
            item = sectors[label]

            item["count"] += 1
            item["speed_sum_ms"] += speed

            if (
                item["speed_max_ms"] is None
                or speed > item["speed_max_ms"]
            ):
                item["speed_max_ms"] = speed

            if first_timestamp is None:
                first_timestamp = timestamp

            last_timestamp = timestamp

        directional_total = total - calm_samples
        dominant_sector = None
        dominant_count = 0

        for label in labels:
            item = sectors[label]

            if item["count"] > 0:
                item["frequency_pct"] = round(
                    item["count"] * 100.0
                    / directional_total,
                    2,
                )
                item["speed_avg_ms"] = round(
                    item["speed_sum_ms"]
                    / item["count"],
                    2,
                )
                item["speed_max_ms"] = round(
                    item["speed_max_ms"],
                    2,
                )

            item.pop("speed_sum_ms", None)

            if item["count"] > dominant_count:
                dominant_sector = label
                dominant_count = item["count"]

        hourly_summary = []
        speed_max_timestamp = None
        gust_max_timestamp = None

        if selected_date:
            hourly = {
                hour: {
                    "hour": f"{hour:02d}:00",
                    "samples": 0,
                    "speed_sum_ms": 0.0,
                    "speed_max_ms": None,
                    "gust_max_ms": None,
                    "calm_samples": 0,
                }
                for hour in range(24)
            }

            daily_speed_max = None
            daily_gust_max = None

            for row in rows:
                try:
                    speed = float(
                        row["wind_speed_ms"]
                    )
                    timestamp = str(
                        row["timestamp_local"]
                    )
                    hour = int(timestamp[11:13])
                except (
                    TypeError,
                    ValueError,
                    IndexError,
                ):
                    continue

                item = hourly[hour]
                item["samples"] += 1
                item["speed_sum_ms"] += speed

                if (
                    item["speed_max_ms"] is None
                    or speed > item["speed_max_ms"]
                ):
                    item["speed_max_ms"] = speed

                if speed < 0.5:
                    item["calm_samples"] += 1

                if (
                    daily_speed_max is None
                    or speed > daily_speed_max
                ):
                    daily_speed_max = speed
                    speed_max_timestamp = timestamp

                gust = row["wind_gust_ms"]

                if gust is not None:
                    try:
                        gust = float(gust)

                        if (
                            item["gust_max_ms"] is None
                            or gust
                            > item["gust_max_ms"]
                        ):
                            item["gust_max_ms"] = gust

                        if (
                            daily_gust_max is None
                            or gust > daily_gust_max
                        ):
                            daily_gust_max = gust
                            gust_max_timestamp = timestamp

                    except (
                        TypeError,
                        ValueError,
                    ):
                        pass

            for hour in range(24):
                item = hourly[hour]
                samples = item["samples"]

                hourly_summary.append({
                    "hour": item["hour"],
                    "samples": samples,
                    "coverage_pct": round(
                        samples * 100.0 / 60,
                        2,
                    ),
                    "speed_avg_ms": (
                        round(
                            item["speed_sum_ms"]
                            / samples,
                            2,
                        )
                        if samples
                        else None
                    ),
                    "speed_max_ms": (
                        round(
                            item["speed_max_ms"],
                            2,
                        )
                        if item["speed_max_ms"]
                        is not None
                        else None
                    ),
                    "gust_max_ms": (
                        round(
                            item["gust_max_ms"],
                            2,
                        )
                        if item["gust_max_ms"]
                        is not None
                        else None
                    ),
                    "calm_frequency_pct": (
                        round(
                            item["calm_samples"]
                            * 100.0
                            / samples,
                            2,
                        )
                        if samples
                        else None
                    ),
                })

        return {
            "status": "ok",
            "station_id": station_id,
            "period": period,
            "selected_date": selected_date,
            "speed_max_timestamp": speed_max_timestamp,
            "gust_max_timestamp": gust_max_timestamp,
            "hourly_summary": hourly_summary,
            "samples": total,
            "coverage_pct": (
                round(total * 100.0 / 1440, 2)
                if selected_date
                else None
            ),
            "directional_samples": directional_total,
            "calm_samples": calm_samples,
            "calm_frequency_pct": (
                round(
                    calm_samples * 100.0 / total,
                    2,
                )
                if total
                else None
            ),
            "dominant_sector": dominant_sector,
            "dominant_frequency_pct": (
                round(
                    dominant_count * 100.0
                    / directional_total,
                    2,
                )
                if directional_total
                else None
            ),
            "speed_avg_ms": (
                round(speed_sum / total, 2)
                if total
                else None
            ),
            "speed_max_ms": (
                round(speed_max, 2)
                if speed_max is not None
                else None
            ),
            "gust_max_ms": (
                round(gust_max, 2)
                if gust_max is not None
                else None
            ),
            "first_timestamp": first_timestamp,
            "last_timestamp": last_timestamp,
            "sectors": [
                sectors[label]
                for label in labels
            ],
        }

    finally:
        conn.close()


@app.route("/api/windrose")
def api_windrose():
    from flask import request

    period = (
        request.args.get(
            "period",
            "24h",
        )
        .strip()
        .lower()
    )

    if period not in {
        "24h",
        "7d",
        "30d",
        "all",
        "date",
    }:
        period = "24h"

    station_id = (
        request.args.get(
            "station_id",
            "CU01",
        )
        .strip()
        .upper()
    )

    if station_id not in {
        "CU01",
        "SJ01",
    }:
        return jsonify(
            {
                "status": "error",
                "error": "Estación no válida.",
                "available_stations": [
                    "CU01",
                    "SJ01",
                ],
            }
        ), 400

    selected_date = (
        request.args.get("date", "").strip()
        or None
    )

    if selected_date:
        import datetime as dt

        try:
            dt.datetime.strptime(
                selected_date,
                "%Y-%m-%d",
            )
        except ValueError:
            return jsonify({
                "status": "error",
                "error": (
                    "Fecha no válida. "
                    "Utilice YYYY-MM-DD."
                ),
            }), 400

    return jsonify(
        get_windrose(
            period=period,
            station_id=station_id,
            selected_date=selected_date,
        )
    )


@app.route("/api/master/summary")
def api_master_summary():
    return jsonify(get_master_summary())


@app.route("/api/core/status")
def api_core_status():
    return jsonify({
        "station": STATION_CONTEXT,
        "database": str(DB_FILE),
        "health": load_json(HEALTH_FILE),
        "registry": load_json(TASK_REGISTRY_FILE),
        "alerts": load_json(ALERTS_FILE),
        "qc_summary": load_json(QC_SUMMARY_FILE),
        "scientific_health": load_json(SCIENTIFIC_HEALTH_FILE),
        "scientific_reliability": load_json(SCIENTIFIC_RELIABILITY_FILE),
        "scientific_comparison": load_json(SCIENTIFIC_COMPARISON_FILE),
        "scientific_agreement": load_json(SCIENTIFIC_AGREEMENT_FILE),
        "atmospheric_corridor": load_json(ATMOSPHERIC_CORRIDOR_FILE),
        "master_summary": get_master_summary(),
    })





@app.route("/api/events")
def api_events():
    from flask import request

    limit = request.args.get("limit", 100)
    category = request.args.get("category")
    severity = request.args.get("severity")
    station = request.args.get("station")
    date_from = request.args.get("from")
    date_to = request.args.get("to")

    try:
        events = list_events(
            limit=limit,
            category=category,
            severity=severity,
            station=station,
            date_from=date_from,
            date_to=date_to,
        )
    except Exception as exc:
        return jsonify({
            "status": "error",
            "error": str(exc),
            "events": [],
        }), 500

    return jsonify({
        "status": "ok",
        "count": len(events),
        "filters": {
            "limit": limit,
            "category": category,
            "severity": severity,
            "station": station,
            "from": date_from,
            "to": date_to,
        },
        "statistics": event_statistics(),
        "events": events,
    })


@app.route("/api/health")
def api_health():
    """
    Health-check ligero para systemd, Gunicorn y monitoreo remoto.

    Comprueba:
    - disponibilidad de SQLite;
    - acceso de lectura a la base de datos;
    - vigencia de la última observación;
    - identidad de la estación y versión de la plataforma.
    """
    checked_at = datetime.now()
    database_status = "error"
    database_error = None
    latest_data = {}
    latest_error = None

    try:
        conn = get_connection()

        try:
            conn.execute("SELECT 1").fetchone()
            database_status = "ok"
        finally:
            conn.close()

    except Exception as exc:
        database_error = str(exc)

    try:
        latest_endpoint = None

        for rule in app.url_map.iter_rules():
            if str(rule) == "/api/latest":
                latest_endpoint = rule.endpoint
                break

        if latest_endpoint:
            response = app.view_functions[latest_endpoint]()

            if hasattr(response, "get_json"):
                latest_data = response.get_json(silent=True) or {}
            elif isinstance(response, dict):
                latest_data = response

    except Exception as exc:
        latest_error = str(exc)

    observation_age_seconds = latest_data.get(
        "observation_age_seconds"
    )

    try:
        observation_age_seconds = (
            float(observation_age_seconds)
            if observation_age_seconds is not None
            else None
        )
    except (TypeError, ValueError):
        observation_age_seconds = None

    latest_observation = (
        latest_data.get("weather_timestamp_local_clean")
        or latest_data.get("timestamp_local")
        or latest_data.get("weather_timestamp_local")
    )

    # AtmosLink V5.1.1 operational state model.
    #
    # 0-420 s: normal acquisition and synchronization cadence.
    # 421-900 s: operational delay beyond the expected cycle.
    # >900 s: confirmed stale observation.
    if database_status != "ok":
        overall_status = "unhealthy"
        operational_state = "CRITICAL"
        http_status = 503

    elif observation_age_seconds is None:
        overall_status = "degraded"
        operational_state = "UNKNOWN"
        http_status = 200

    elif observation_age_seconds <= 420:
        overall_status = "healthy"
        operational_state = "ONLINE"
        http_status = 200

    elif observation_age_seconds <= 900:
        overall_status = "observing"
        operational_state = "DELAYED"
        http_status = 200

    elif observation_age_seconds <= 1800:
        overall_status = "degraded"
        operational_state = "STALE"
        http_status = 200

    else:
        overall_status = "critical"
        operational_state = "CRITICAL"
        http_status = 200

    payload = {
        "status": overall_status,
        "operational_state": operational_state,
        "state_thresholds_seconds": {
            "fresh_max": 420,
            "waiting_max": 600,
            "stale_max": 1800,
        },
        "service": "atmoslink-dashboard",
        "platform": "AtmosLink Research Platform",
        "version": "5.1.1",
        "station_id": STATION_CONTEXT.get("station_id"),
        "station_name": STATION_CONTEXT.get("station_name"),
        "database": {
            "status": database_status,
            "path": str(DB_FILE),
            "error": database_error,
        },
        "latest_observation": latest_observation,
        "observation_age_seconds": observation_age_seconds,
        "latest_error": latest_error,
        "checked_at_local": checked_at.isoformat(
            timespec="seconds"
        ),
    }

    return jsonify(payload), http_status




def register_dashboard_startup_event():
    try:
        log_event(
            category="SYSTEM",
            severity="SUCCESS",
            station=STATION_CONTEXT.get("station_id"),
            title="AtmosLink dashboard started",
            description=(
                "Gunicorn loaded the AtmosLink dashboard application."
            ),
            author="system",
            tags=["dashboard", "gunicorn", "startup"],
            metadata={
                "platform_version": "5.2.1",
                "database": str(DB_FILE),
            },
            dedupe_key="dashboard-startup",
            dedupe_seconds=60,
        )
    except Exception:
        app.logger.exception(
            "Unable to register dashboard startup event."
        )


if os.environ.get("ATMOSLINK_STATION"):
    register_dashboard_startup_event()



@app.route("/ui-v3")
def ui_v3():
    """
    AtmosLink Multi-Site Scientific Control Center.
    Interfaz paralela a las vistas legacy y UI v2.
    """
    return render_template("v3/index.html")



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
