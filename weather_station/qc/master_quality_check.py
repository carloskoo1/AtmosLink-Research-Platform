import sqlite3
from pathlib import Path

import pandas as pd

from weather_station.config.station_manager import get_station_context


STATION_CONTEXT = get_station_context()
DB_FILE = Path(STATION_CONTEXT["database"])
EXPORT_FILE = Path("Data/exports/master_quality_report.csv")


def table_exists(conn, table_name: str) -> bool:
    query = """
    SELECT name FROM sqlite_master
    WHERE type='table' AND name=?
    """
    return conn.execute(query, (table_name,)).fetchone() is not None


def add_issue(issues, row, issue_type, severity, message):
    issues.append({
        "station_id": row.get("station_id"),
        "timestamp": row.get("master_timestamp_local"),
        "issue_type": issue_type,
        "severity": severity,
        "message": message,
    })


def run_quality_check():
    if not DB_FILE.exists():
        raise FileNotFoundError(f"No existe la base de datos: {DB_FILE}")

    conn = sqlite3.connect(DB_FILE, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")

    table = "master_observations_enriched"
    if not table_exists(conn, table):
        conn.close()
        raise RuntimeError("No existe master_observations_enriched. Ejecuta primero enrich_master_dataset.")

    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)

    issues = []

    if df.empty:
        conn.close()
        print("Dataset enriquecido vacío. No se generó control de calidad.")
        return

    df["dt"] = pd.to_datetime(df["master_timestamp_local"], errors="coerce")
    df = df.sort_values("dt")

    for _, row in df.iterrows():
        if pd.isna(row.get("dt")):
            add_issue(issues, row, "INVALID_TIMESTAMP", "critical", "Timestamp no interpretable.")

        temp = row.get("local_temp_avg_c")
        hum = row.get("local_hum_avg_pct")
        pres = row.get("local_press_hpa")

        if pd.isna(temp) or pd.isna(hum) or pd.isna(pres):
            add_issue(issues, row, "MISSING_CORE_METEO", "critical", "Faltan temperatura, humedad o presión.")

        if pd.notna(temp) and (temp < -30 or temp > 60):
            add_issue(issues, row, "TEMP_OUT_OF_RANGE", "critical", f"Temperatura fuera de rango: {temp}")

        if pd.notna(hum) and (hum < 0 or hum > 100):
            add_issue(issues, row, "HUM_OUT_OF_RANGE", "critical", f"Humedad fuera de rango: {hum}")

        if pd.notna(pres) and (pres < 500 or pres > 1100):
            add_issue(issues, row, "PRESS_OUT_OF_RANGE", "critical", f"Presión fuera de rango: {pres}")

        vpd = row.get("derived_vpd_hpa")
        if pd.notna(vpd) and vpd < 0:
            add_issue(issues, row, "NEGATIVE_VPD", "warning", f"VPD negativo: {vpd}")

        air_density = row.get("derived_air_density_kg_m3")
        if pd.notna(air_density) and (air_density < 0.7 or air_density > 1.4):
            add_issue(issues, row, "AIR_DENSITY_SUSPICIOUS", "warning", f"Densidad del aire sospechosa: {air_density}")

    numeric_checks = [
        ("local_temp_avg_c", 8.0, "TEMP_JUMP"),
        ("local_hum_avg_pct", 20.0, "HUM_JUMP"),
        ("local_press_hpa", 5.0, "PRESS_JUMP"),
        ("local_rain_total_mm", 20.0, "RAIN_TOTAL_JUMP"),
    ]

    for col, threshold, issue_type in numeric_checks:
        if col not in df.columns:
            continue

        diffs = pd.to_numeric(df[col], errors="coerce").diff().abs()

        for idx in diffs[diffs > threshold].index:
            row = df.loc[idx]
            add_issue(
                issues,
                row,
                issue_type,
                "warning",
                f"Salto brusco en {col}: Δ={diffs.loc[idx]:.2f}"
            )

    report = pd.DataFrame(issues)

    if report.empty:
        report = pd.DataFrame([{
            "station_id": STATION_CONTEXT["station_id"],
            "timestamp": None,
            "issue_type": "NO_ISSUES",
            "severity": "ok",
            "message": "No se detectaron problemas de calidad."
        }])

    report.to_sql(
        "master_quality_report",
        conn,
        if_exists="replace",
        index=False,
    )

    EXPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(EXPORT_FILE, index=False)

    conn.close()

    print("REPORTE DE CALIDAD generado correctamente")
    print(f"Estación : {STATION_CONTEXT['station_id']} | {STATION_CONTEXT['station_name']}")
    print(f"Issues   : {len(report)}")
    print("Tabla    : master_quality_report")
    print(f"CSV      : {EXPORT_FILE}")


if __name__ == "__main__":
    run_quality_check()
