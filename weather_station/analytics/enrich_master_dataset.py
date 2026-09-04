import sqlite3
from pathlib import Path

import pandas as pd

from weather_station.config.station_manager import get_station_context
from weather_station.analytics.derived_weather import derive_weather_metrics


STATION_CONTEXT = get_station_context()
DB_FILE = Path(STATION_CONTEXT["database"])
EXPORT_FILE = Path("Data/exports/master_observations_enriched.csv")


def table_exists(conn, table_name: str) -> bool:
    query = """
    SELECT name FROM sqlite_master
    WHERE type='table' AND name=?
    """
    return conn.execute(query, (table_name,)).fetchone() is not None


def enrich_master_dataset():
    if not DB_FILE.exists():
        raise FileNotFoundError(f"No existe la base de datos: {DB_FILE}")

    conn = sqlite3.connect(DB_FILE, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")

    if not table_exists(conn, "master_observations"):
        conn.close()
        raise RuntimeError("No existe la tabla master_observations. Ejecuta primero build_master_dataset.")

    df = pd.read_sql_query("SELECT * FROM master_observations", conn)

    if df.empty:
        conn.close()
        print("master_observations está vacío. No se generó dataset enriquecido.")
        return

    derived_rows = []

    for _, row in df.iterrows():
        derived_rows.append(derive_weather_metrics(row.to_dict()))

    derived_df = pd.DataFrame(derived_rows)
    enriched = pd.concat([df.reset_index(drop=True), derived_df.reset_index(drop=True)], axis=1)

    enriched.to_sql(
        "master_observations_enriched",
        conn,
        if_exists="replace",
        index=False,
    )

    EXPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(EXPORT_FILE, index=False)

    conn.close()

    print("MASTER DATASET ENRIQUECIDO generado correctamente")
    print(f"Estación : {STATION_CONTEXT['station_id']} | {STATION_CONTEXT['station_name']}")
    print(f"Filas    : {len(enriched)}")
    print("Tabla    : master_observations_enriched")
    print(f"CSV      : {EXPORT_FILE}")


if __name__ == "__main__":
    enrich_master_dataset()
