import json
import sqlite3
import math
from datetime import datetime
from pathlib import Path

from weather_station.config.station_manager import get_station_context


STATION_CONTEXT = get_station_context()
DB_FILE = Path(STATION_CONTEXT["database"])
OUTPUT_FILE = Path("runtime/atmospheric_corridor.json")

SITE_ORDER = ["AP_CUNACALES", "MID_LINK", "SM_SAN_JOSE"]

VARIABLES = [
    {"key": "temp_c", "label": "Temperatura", "unit": "°C"},
    {"key": "rh_pct", "label": "Humedad relativa", "unit": "%"},
    {"key": "press_hpa", "label": "Presión", "unit": "hPa"},
    {"key": "precip_mm", "label": "Precipitación", "unit": "mm"},
    {"key": "wind_ms", "label": "Viento", "unit": "m/s"},
]

SOURCE_TABLES = {
    "ERA5": {
        "table": "era5_land_hourly",
        "columns": {
            "temp_c": "temp_c",
            "rh_pct": "rh_pct_calc",
            "press_hpa": "press_hpa",
            "precip_mm": "precip_mm",
            "wind_ms": "wind_ms",
        },
    },
    "NASA": {
        "table": "nasa_power_hourly",
        "columns": {
            "temp_c": "temp_c",
            "rh_pct": "rh_pct",
            "press_hpa": "press_hpa",
            "precip_mm": "precip_mm",
            "wind_ms": "wind10m_ms",
        },
    },
}



def calc_relative_humidity_pct(temp_c, dewpoint_c):
    if temp_c is None or dewpoint_c is None:
        return None

    try:
        temp_c = float(temp_c)
        dewpoint_c = float(dewpoint_c)

        es = 6.112 * math.exp((17.67 * temp_c) / (temp_c + 243.5))
        e = 6.112 * math.exp((17.67 * dewpoint_c) / (dewpoint_c + 243.5))

        rh = 100.0 * e / es
        return max(0.0, min(100.0, rh))
    except Exception:
        return None

def table_exists(conn, table_name):
    return conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone() is not None


def get_columns(conn, table_name):
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table_name})").fetchall()]


def latest_valid_by_site(conn, table_name, source_columns):
    if not table_exists(conn, table_name):
        return {}

    available_columns = get_columns(conn, table_name)
    valid_cols = [c for c in source_columns.values() if c in available_columns]

    if not valid_cols:
        return {}

    valid_condition = " OR ".join([f"{c} IS NOT NULL" for c in valid_cols])

    query = f"""
        SELECT t.*
        FROM {table_name} t
        INNER JOIN (
            SELECT site_tag, MAX(timestamp_local) AS max_timestamp
            FROM {table_name}
            WHERE {valid_condition}
            GROUP BY site_tag
        ) latest
        ON t.site_tag = latest.site_tag
        AND t.timestamp_local = latest.max_timestamp
        ORDER BY t.site_tag
    """

    rows = conn.execute(query).fetchall()
    return {dict(r)["site_tag"]: dict(r) for r in rows}


def safe_value(row, column):
    if not row:
        return None

    if column == "rh_pct_calc":
        return calc_relative_humidity_pct(row.get("temp_c"), row.get("dewpoint_c"))

    value = row.get(column)

    if value is None:
        return None

    try:
        return round(float(value), 3)
    except Exception:
        return None


def build_source_corridor(source_name, cfg, rows_by_site):
    points = {}

    for site in SITE_ORDER:
        row = rows_by_site.get(site)

        point = {
            "site_tag": site,
            "timestamp_local": row.get("timestamp_local") if row else None,
        }

        for var in VARIABLES:
            column = cfg["columns"].get(var["key"])
            point[var["key"]] = safe_value(row, column)

        points[site] = point

    gradients = []

    for var in VARIABLES:
        key = var["key"]

        ap = points["AP_CUNACALES"].get(key)
        mid = points["MID_LINK"].get(key)
        sm = points["SM_SAN_JOSE"].get(key)

        gradients.append({
            "variable": key,
            "label": var["label"],
            "unit": var["unit"],
            "ap_value": ap,
            "mid_value": mid,
            "sm_value": sm,
            "gradient_ap_to_mid": round(mid - ap, 3) if ap is not None and mid is not None else None,
            "gradient_mid_to_sm": round(sm - mid, 3) if mid is not None and sm is not None else None,
            "gradient_ap_to_sm": round(sm - ap, 3) if ap is not None and sm is not None else None,
        })

    valid_points = sum(
        1 for site in SITE_ORDER
        if any(points[site].get(v["key"]) is not None for v in VARIABLES)
    )

    return {
        "source": source_name,
        "valid_points": valid_points,
        "points": points,
        "gradients": gradients,
    }


def build_atmospheric_corridor():
    payload = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "station_id": STATION_CONTEXT["station_id"],
        "station_name": STATION_CONTEXT["station_name"],
        "database": str(DB_FILE),
        "status": "unknown",
        "sources": {},
        "message": "",
    }

    if not DB_FILE.exists():
        payload["status"] = "critical"
        payload["message"] = "Base de datos no encontrada."
        return payload

    conn = sqlite3.connect(DB_FILE, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.row_factory = sqlite3.Row

    valid_sources = 0

    for source_name, cfg in SOURCE_TABLES.items():
        table_name = cfg["table"]

        if not table_exists(conn, table_name):
            payload["sources"][source_name] = {
                "source": source_name,
                "valid_points": 0,
                "points": {},
                "gradients": [],
            }
            continue

        rows_by_site = latest_valid_by_site(conn, table_name, cfg["columns"])
        source_payload = build_source_corridor(source_name, cfg, rows_by_site)

        payload["sources"][source_name] = source_payload

        if source_payload["valid_points"] > 0:
            valid_sources += 1

    conn.close()

    if valid_sources == 0:
        payload["status"] = "warning"
        payload["message"] = "No existen datos suficientes para construir el corredor atmosférico."
    elif valid_sources < len(SOURCE_TABLES):
        payload["status"] = "warning"
        payload["message"] = "Corredor atmosférico generado parcialmente."
    else:
        payload["status"] = "ok"
        payload["message"] = "Corredor atmosférico AP–MID–SM generado correctamente."

    return payload


def main():
    payload = build_atmospheric_corridor()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)

    print("ATMOSPHERIC CORRIDOR generado correctamente")
    print(f"Estado  : {payload['status']}")
    print(f"Mensaje : {payload['message']}")
    print(f"Archivo : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
