import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from weather_station.config.settings import load_config


CONFIG = load_config()

BASE_DIR = Path(__file__).resolve().parents[2]
DB_FILE = Path(CONFIG["database"]["sqlite"])

RUNTIME_DIR = BASE_DIR / "runtime"
ALERTS_FILE = RUNTIME_DIR / "alerts.json"
HEALTH_FILE = RUNTIME_DIR / "health_status.json"
TASK_REGISTRY_FILE = RUNTIME_DIR / "task_registry.json"

MAX_WEATHER_AGE_MINUTES = 5
MAX_MASTER_AGE_MINUTES = 5

RAIN_INTENSE_MM_H = 10.0

WIND_SPEED_WARNING_MS = 10.0
WIND_SPEED_CRITICAL_MS = 17.0
WIND_GUST_WARNING_MS = 15.0
WIND_GUST_CRITICAL_MS = 22.0

DISK_FREE_CRITICAL_PCT = 10.0
DISK_FREE_WARNING_PCT = 20.0
CPU_WARNING_PCT = 90.0
RAM_WARNING_PCT = 90.0


def now_utc():
    return datetime.now(timezone.utc)


def load_json(path):
    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def parse_dt(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def minutes_since(dt):
    if dt is None:
        return None

    if dt.tzinfo is None:
        dt = dt.astimezone()

    return (now_utc() - dt.astimezone(timezone.utc)).total_seconds() / 60.0


def table_exists(conn, table_name):
    query = """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name=?
    """
    return conn.execute(query, (table_name,)).fetchone() is not None


def get_latest_row(table_name, order_column="id"):
    if not DB_FILE.exists():
        return None

    conn = sqlite3.connect(DB_FILE, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.row_factory = sqlite3.Row

    if not table_exists(conn, table_name):
        conn.close()
        return None

    cur = conn.cursor()
    cur.execute(f"""
        SELECT *
        FROM {table_name}
        ORDER BY {order_column} DESC
        LIMIT 1
    """)

    row = cur.fetchone()
    conn.close()

    return dict(row) if row else None


def add_alert(alerts, alert_id, severity, title, message):
    alerts.append({
        "id": alert_id,
        "severity": severity,
        "title": title,
        "message": message,
    })


def check_weather(alerts):
    row = get_latest_row("weather_local")

    if not row:
        add_alert(
            alerts,
            "WEATHER_NO_DATA",
            "critical",
            "Sin datos meteorológicos",
            "No existen registros en weather_local."
        )
        return

    ts = parse_dt(row.get("timestamp_local"))
    age = minutes_since(ts)

    if age is None:
        add_alert(
            alerts,
            "WEATHER_INVALID_TIMESTAMP",
            "warning",
            "Timestamp meteorológico inválido",
            f"No se pudo interpretar timestamp_local: {row.get('timestamp_local')}"
        )
    elif age > MAX_WEATHER_AGE_MINUTES:
        add_alert(
            alerts,
            "WEATHER_STALE",
            "critical",
            "Estación meteorológica sin actualización",
            f"Último dato hace {age:.1f} minutos. Último timestamp: {row.get('timestamp_local')}"
        )

    if row.get("bme_ok") != 1:
        add_alert(
            alerts,
            "BME280_NOT_OK",
            "critical",
            "BME280 con falla",
            "El último registro indica bme_ok diferente de 1."
        )

    if row.get("rain_ok") != 1:
        add_alert(
            alerts,
            "RAIN_SENSOR_NOT_OK",
            "critical",
            "Pluviómetro con falla",
            "El último registro indica rain_ok diferente de 1."
        )

    try:
        rain_1h = float(row.get("rain_1h_mm"))
        if rain_1h >= RAIN_INTENSE_MM_H:
            add_alert(
                alerts,
                "INTENSE_RAIN",
                "warning",
                "Lluvia intensa detectada",
                f"Lluvia última hora: {rain_1h:.2f} mm."
            )
    except Exception:
        pass

    check_wind(alerts, row)


def check_wind(alerts, row):
    wind_ok = row.get("wind_ok")

    if wind_ok in [None, "", 0]:
        return

    if wind_ok != 1:
        add_alert(
            alerts,
            "WIND_SENSOR_NOT_OK",
            "warning",
            "Anemómetro con falla",
            "El último registro indica wind_ok diferente de 1."
        )
        return

    try:
        wind_speed = float(row.get("wind_speed_ms"))
        if wind_speed >= WIND_SPEED_CRITICAL_MS:
            add_alert(
                alerts,
                "WIND_SPEED_CRITICAL",
                "critical",
                "Viento crítico detectado",
                f"Velocidad del viento: {wind_speed:.2f} m/s."
            )
        elif wind_speed >= WIND_SPEED_WARNING_MS:
            add_alert(
                alerts,
                "WIND_SPEED_WARNING",
                "warning",
                "Viento elevado detectado",
                f"Velocidad del viento: {wind_speed:.2f} m/s."
            )
    except Exception:
        pass

    try:
        wind_gust = float(row.get("wind_gust_ms"))
        if wind_gust >= WIND_GUST_CRITICAL_MS:
            add_alert(
                alerts,
                "WIND_GUST_CRITICAL",
                "critical",
                "Ráfaga crítica detectada",
                f"Ráfaga máxima: {wind_gust:.2f} m/s."
            )
        elif wind_gust >= WIND_GUST_WARNING_MS:
            add_alert(
                alerts,
                "WIND_GUST_WARNING",
                "warning",
                "Ráfaga elevada detectada",
                f"Ráfaga máxima: {wind_gust:.2f} m/s."
            )
    except Exception:
        pass


def check_master(alerts):
    row = get_latest_row("master_observations", order_column="bucket_minute")

    if not row:
        add_alert(
            alerts,
            "MASTER_NO_DATA",
            "warning",
            "Master dataset sin datos",
            "No existen registros en master_observations."
        )
        return

    ts = parse_dt(row.get("master_timestamp_local"))
    age = minutes_since(ts)

    if age is not None and age > MAX_MASTER_AGE_MINUTES:
        add_alert(
            alerts,
            "MASTER_STALE",
            "warning",
            "Master dataset desactualizado",
            f"Última sincronización útil hace {age:.1f} minutos. Último registro: {row.get('master_timestamp_local')}"
        )


def check_health(alerts):
    health = load_json(HEALTH_FILE)
    checks = health.get("checks", {})

    sqlite_check = checks.get("sqlite", {})
    if sqlite_check and sqlite_check.get("status") != "ok":
        add_alert(
            alerts,
            "SQLITE_HEALTH_FAIL",
            "critical",
            "SQLite con falla",
            sqlite_check.get("message", "El chequeo SQLite no está en estado OK.")
        )

    internet_check = checks.get("internet", {})
    if internet_check and internet_check.get("status") != "ok":
        add_alert(
            alerts,
            "INTERNET_HEALTH_FAIL",
            "warning",
            "Conectividad a Internet con falla",
            internet_check.get("message", "El chequeo de Internet no está en estado OK.")
        )

    disk = checks.get("disk", {})
    try:
        free_pct = float(disk.get("free_percent"))
        if free_pct < DISK_FREE_CRITICAL_PCT:
            add_alert(
                alerts,
                "DISK_FREE_CRITICAL",
                "critical",
                "Espacio en disco crítico",
                f"Espacio libre: {free_pct:.2f}%."
            )
        elif free_pct < DISK_FREE_WARNING_PCT:
            add_alert(
                alerts,
                "DISK_FREE_WARNING",
                "warning",
                "Espacio en disco bajo",
                f"Espacio libre: {free_pct:.2f}%."
            )
    except Exception:
        pass

    cpu_memory = checks.get("cpu_memory", {})

    try:
        cpu = float(cpu_memory.get("cpu_percent"))
        if cpu >= CPU_WARNING_PCT:
            add_alert(
                alerts,
                "CPU_HIGH",
                "warning",
                "Uso alto de CPU",
                f"CPU: {cpu:.2f}%."
            )
    except Exception:
        pass

    try:
        ram = float(cpu_memory.get("ram_percent"))
        if ram >= RAM_WARNING_PCT:
            add_alert(
                alerts,
                "RAM_HIGH",
                "warning",
                "Uso alto de RAM",
                f"RAM: {ram:.2f}%."
            )
    except Exception:
        pass


def check_scheduler(alerts):
    registry = load_json(TASK_REGISTRY_FILE)
    tasks = registry.get("tasks", {})

    for task_name, task in tasks.items():
        enabled = task.get("enabled")
        status = task.get("status")
        failures = task.get("failures", 0)

        if enabled and status in ["failed", "error", "timeout"]:
            add_alert(
                alerts,
                f"TASK_{task_name}_FAILED",
                "warning",
                f"Tarea fallida: {task_name}",
                f"Estado: {status}. Fallos acumulados: {failures}."
            )


def check_radio(alerts):
    row = get_latest_row("radio_link_local")

    if not row:
        return

    note = row.get("note")
    if note and note not in ["ok", "LOW_SNR", "LOW_RSSI", "LOW_MCS", "LOW_RATE"]:
        add_alert(
            alerts,
            "RADIO_LINK_STATUS",
            "warning",
            "Estado anómalo del radioenlace",
            f"Nota del colector: {note}"
        )

    if note in ["LOW_SNR", "LOW_RSSI", "LOW_MCS", "LOW_RATE"]:
        add_alert(
            alerts,
            f"RADIO_{note}",
            "warning",
            f"Radioenlace: {note}",
            f"Último estado del radioenlace: {note}"
        )


def build_alerts():
    alerts = []

    check_weather(alerts)
    check_master(alerts)
    check_health(alerts)
    check_scheduler(alerts)
    check_radio(alerts)

    payload = {
        "updated_at": now_utc().isoformat(timespec="seconds"),
        "alert_count": len(alerts),
        "alerts": alerts,
    }

    return payload


def main():
    payload = build_alerts()
    save_json(ALERTS_FILE, payload)

    print("ALERTS generado correctamente")
    print(f"Alertas activas: {payload['alert_count']}")
    print(f"Archivo: {ALERTS_FILE}")


if __name__ == "__main__":
    main()
