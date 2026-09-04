import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from weather_station.config.settings import load_config
from weather_station.config.station_manager import get_station_context


CONFIG = load_config()
STATION_CONTEXT = get_station_context()
DB_FILE = STATION_CONTEXT["database"]


def table_exists(conn, table_name):
    q = """
    SELECT name FROM sqlite_master
    WHERE type='table' AND name=?
    """
    return conn.execute(q, (table_name,)).fetchone() is not None


def read_table(
    conn,
    table_name,
    timestamp_column=None,
    start_local=None,
    end_local=None,
    site_tag=None,
):
    """
    Lee una tabla completa o una ventana temporal.

    El filtrado SQL reduce I/O.
    Las funciones prepare_* mantienen la logica
    original de QA/QC y deduplicacion.
    """

    if not table_exists(conn, table_name):
        return pd.DataFrame()

    sql = f'SELECT * FROM "{table_name}"'
    where = []
    params = []

    if (
        timestamp_column is not None
        and start_local is not None
    ):
        where.append(
            f'"{timestamp_column}" >= ?'
        )
        params.append(start_local)

    if (
        timestamp_column is not None
        and end_local is not None
    ):
        where.append(
            f'"{timestamp_column}" < ?'
        )
        params.append(end_local)

    if site_tag is not None:
        where.append('"site_tag" = ?')
        params.append(site_tag)

    if where:
        sql += " WHERE " + " AND ".join(where)

    return pd.read_sql_query(
        sql,
        conn,
        params=params
    )


def saturation_vapor_pressure_hpa(temp_c):
    return 6.112 * np.exp((17.67 * temp_c) / (temp_c + 243.5))


def calc_relative_humidity_pct(temp_c, dewpoint_c):
    temp_c = pd.to_numeric(temp_c, errors="coerce")
    dewpoint_c = pd.to_numeric(dewpoint_c, errors="coerce")

    es_temp = saturation_vapor_pressure_hpa(temp_c)
    es_dew = saturation_vapor_pressure_hpa(dewpoint_c)

    rh = 100.0 * (es_dew / es_temp)
    rh = rh.clip(lower=0, upper=100)

    return rh.round(2)


def prepare_weather(df):
    if df.empty:
        return df

    df["timestamp_local_dt"] = pd.to_datetime(df["timestamp_local"], errors="coerce")
    df = df.dropna(subset=["timestamp_local_dt"])
    df["bucket_minute"] = df["timestamp_local_dt"].dt.floor("min")

    required = [
        "temp_avg_C",
        "temp_min_C",
        "temp_max_C",
        "hum_avg_pct",
        "hum_min_pct",
        "hum_max_pct",
        "pres_avg_hPa",
        "dew_point_C",
        "vapor_pressure_hPa",
        "rain_1min_mm",
        "rain_1h_mm",
        "rain_total_mm",
        "bme_ok",
        "rain_ok",
    ]

    for col in required:
        if col not in df.columns:
            print(f"Columna meteorológica faltante: {col}")
            return pd.DataFrame()

    before = len(df)

    df = df[
        (df["temp_avg_C"].between(-30, 60)) &
        (df["temp_min_C"].between(-30, 60)) &
        (df["temp_max_C"].between(-30, 60)) &
        (df["hum_avg_pct"].between(0, 100)) &
        (df["hum_min_pct"].between(0, 100)) &
        (df["hum_max_pct"].between(0, 100)) &
        (df["pres_avg_hPa"].between(500, 1100)) &
        (df["dew_point_C"].between(-40, 60)) &
        (df["vapor_pressure_hPa"].between(0, 100)) &
        (df["rain_1min_mm"] >= 0) &
        (df["rain_1h_mm"] >= 0) &
        (df["rain_total_mm"] >= 0) &
        (df["bme_ok"] == 1) &
        (df["rain_ok"] == 1)
    ].copy()

    removed = before - len(df)
    if removed > 0:
        print(f"Registros meteorológicos descartados por calidad: {removed}")

    cols = [
        "bucket_minute",
        "station_id",
        "station_name",
        "radio_role",
        "timestamp_utc",
        "timestamp_local",
        "temp_avg_C",
        "temp_min_C",
        "temp_max_C",
        "hum_avg_pct",
        "hum_min_pct",
        "hum_max_pct",
        "pres_avg_hPa",
        "dew_point_C",
        "vapor_pressure_hPa",
        "rain_1min_mm",
        "rain_1h_mm",
        "rain_total_mm",
        "pulses_delta",
        "pulses_total",
        "wind_speed_ms",
        "wind_direction_deg",
        "wind_gust_ms",
        "wind_ok",
        "bme_ok",
        "rain_ok",
    ]

    cols = [c for c in cols if c in df.columns]
    df = df[cols].copy()

    rename = {
        "timestamp_utc": "weather_timestamp_utc",
        "timestamp_local": "weather_timestamp_local",
        "station_id": "station_id",
        "station_name": "station_name",
        "radio_role": "radio_role",
        "temp_avg_C": "local_temp_avg_c",
        "temp_min_C": "local_temp_min_c",
        "temp_max_C": "local_temp_max_c",
        "hum_avg_pct": "local_hum_avg_pct",
        "hum_min_pct": "local_hum_min_pct",
        "hum_max_pct": "local_hum_max_pct",
        "pres_avg_hPa": "local_press_hpa",
        "dew_point_C": "local_dew_point_c",
        "vapor_pressure_hPa": "local_vapor_pressure_hpa",
        "rain_1min_mm": "local_rain_1min_mm",
        "rain_1h_mm": "local_rain_1h_mm",
        "rain_total_mm": "local_rain_total_mm",
        "pulses_delta": "local_pulses_delta",
        "pulses_total": "local_pulses_total",
        "wind_speed_ms": "local_wind_speed_ms",
        "wind_direction_deg": "local_wind_direction_deg",
        "wind_gust_ms": "local_wind_gust_ms",
        "wind_ok": "local_wind_ok",
        "bme_ok": "local_bme_ok",
        "rain_ok": "local_rain_ok",
    }

    df = df.rename(columns=rename)
    df = df.sort_values("bucket_minute")
    df = df.drop_duplicates(subset=["bucket_minute"], keep="last")

    return df


def prepare_radio(df):
    if df.empty:
        return df

    df["timestamp_local_dt"] = pd.to_datetime(df["timestamp_local"], errors="coerce")
    df = df.dropna(subset=["timestamp_local_dt"])
    df["bucket_minute"] = df["timestamp_local_dt"].dt.floor("min")

    if "error" in df.columns:
        df = df[(df["error"].isna()) | (df["error"] == "")].copy()

    if "note" in df.columns:
        accepted_notes = ["ok", "LOW_SNR", "LOW_RSSI", "LOW_MCS", "LOW_RATE"]
        df = df[df["note"].fillna("ok").isin(accepted_notes)].copy()

    cols = [
        "bucket_minute",
        "station_id",
        "station_name",
        "radio_role",
        "local_role",
        "timestamp_utc",
        "timestamp_local",
        "mcs_dl",
        "mcs_ul",
        "snr_dl",
        "snr_ul",
        "rssi_c0p",
        "rssi_c0e",
        "rssi_c1p",
        "rssi_c1e",
        "dl_rate",
        "ul_rate",
        "sta_dl_rssi",
        "sta_ul_rssi",
        "note",
        "error",
    ]

    cols = [c for c in cols if c in df.columns]
    df = df[cols].copy()

    rename = {
        "timestamp_utc": "radio_timestamp_utc",
        "timestamp_local": "radio_timestamp_local",
        "station_id": "radio_station_id",
        "station_name": "radio_station_name",
        "radio_role": "radio_role_from_radio",
        "local_role": "radio_local_role",
        "mcs_dl": "radio_mcs_dl",
        "mcs_ul": "radio_mcs_ul",
        "snr_dl": "radio_snr_dl",
        "snr_ul": "radio_snr_ul",
        "rssi_c0p": "radio_rssi_c0p",
        "rssi_c0e": "radio_rssi_c0e",
        "rssi_c1p": "radio_rssi_c1p",
        "rssi_c1e": "radio_rssi_c1e",
        "dl_rate": "radio_dl_rate",
        "ul_rate": "radio_ul_rate",
        "sta_dl_rssi": "radio_sta_dl_rssi",
        "sta_ul_rssi": "radio_sta_ul_rssi",
        "note": "radio_note",
        "error": "radio_error",
    }

    df = df.rename(columns=rename)
    df = df.sort_values("bucket_minute")
    df = df.drop_duplicates(subset=["bucket_minute"], keep="last")

    return df


def prepare_era5(df, site_tag="MID_LINK"):
    if df.empty:
        return df

    if "site_tag" not in df.columns:
        print("ERA5 no tiene columna site_tag")
        return pd.DataFrame()

    df = df[df["site_tag"] == site_tag].copy()

    if df.empty:
        print(f"No hay datos ERA5 para site_tag={site_tag}")
        return df

    df["timestamp_local_dt"] = pd.to_datetime(df["timestamp_local"], errors="coerce")
    df = df.dropna(subset=["timestamp_local_dt"])
    df["bucket_hour"] = df["timestamp_local_dt"].dt.floor("h")

    required = [
        "temp_c",
        "dewpoint_c",
    ]

    for col in required:
        if col not in df.columns:
            print(f"Columna ERA5 faltante: {col}")
            return pd.DataFrame()

    df["era5_rh_pct_calc"] = calc_relative_humidity_pct(
        df["temp_c"],
        df["dewpoint_c"]
    )

    cols = [
        "bucket_hour",
        "timestamp_utc",
        "timestamp_local",
        "site_tag",
        "lat",
        "lon",
        "temp_c",
        "dewpoint_c",
        "era5_rh_pct_calc",
        "precip_mm",
        "press_hpa",
        "wind_ms",
    ]

    cols = [c for c in cols if c in df.columns]
    df = df[cols].copy()

    rename = {
        "timestamp_utc": "era5_timestamp_utc",
        "timestamp_local": "era5_timestamp_local",
        "site_tag": "era5_site_tag",
        "lat": "era5_lat",
        "lon": "era5_lon",
        "temp_c": "era5_temp_c",
        "dewpoint_c": "era5_dewpoint_c",
        "era5_rh_pct_calc": "era5_rh_pct",
        "precip_mm": "era5_precip_mm",
        "press_hpa": "era5_press_hpa",
        "wind_ms": "era5_wind_ms",
    }

    df = df.rename(columns=rename)
    df = df.sort_values("bucket_hour")
    df = df.drop_duplicates(subset=["bucket_hour"], keep="last")

    return df


def prepare_nasa_power(df, site_tag="MID_LINK"):
    if df.empty:
        return df

    if "site_tag" not in df.columns:
        print("NASA POWER no tiene columna site_tag")
        return pd.DataFrame()

    df = df[df["site_tag"] == site_tag].copy()

    if df.empty:
        print(f"No hay datos NASA POWER para site_tag={site_tag}")
        return df

    df["timestamp_local_dt"] = pd.to_datetime(df["timestamp_local"], errors="coerce")
    df = df.dropna(subset=["timestamp_local_dt"])
    df["bucket_hour"] = df["timestamp_local_dt"].dt.floor("h")

    required = [
        "temp_c",
        "dewpoint_c",
        "rh_pct",
        "precip_mm",
        "press_hpa",
        "wind10m_ms",
    ]

    for col in required:
        if col not in df.columns:
            print(f"Columna NASA POWER faltante: {col}")
            return pd.DataFrame()

    before = len(df)

    df = df[
        (df["temp_c"].between(-60, 60)) &
        (df["dewpoint_c"].between(-80, 60)) &
        (df["rh_pct"].between(0, 100)) &
        (df["precip_mm"] >= 0) &
        (df["press_hpa"].between(300, 1100)) &
        (df["wind10m_ms"] >= 0)
    ].copy()

    removed = before - len(df)
    if removed > 0:
        print(f"Registros NASA POWER descartados por calidad: {removed}")

    cols = [
        "bucket_hour",
        "timestamp_utc",
        "timestamp_local",
        "site_tag",
        "lat",
        "lon",
        "temp_c",
        "dewpoint_c",
        "rh_pct",
        "precip_mm",
        "press_kpa",
        "press_hpa",
        "wind10m_ms",
        "source",
        "downloaded_at_utc",
    ]

    cols = [c for c in cols if c in df.columns]
    df = df[cols].copy()

    rename = {
        "timestamp_utc": "nasa_timestamp_utc",
        "timestamp_local": "nasa_timestamp_local",
        "site_tag": "nasa_site_tag",
        "lat": "nasa_lat",
        "lon": "nasa_lon",
        "temp_c": "nasa_temp_c",
        "dewpoint_c": "nasa_dewpoint_c",
        "rh_pct": "nasa_rh_pct",
        "precip_mm": "nasa_precip_mm",
        "press_kpa": "nasa_press_kpa",
        "press_hpa": "nasa_press_hpa",
        "wind10m_ms": "nasa_wind10m_ms",
        "source": "nasa_source",
        "downloaded_at_utc": "nasa_downloaded_at_utc",
    }

    df = df.rename(columns=rename)
    df = df.sort_values("bucket_hour")
    df = df.drop_duplicates(subset=["bucket_hour"], keep="last")

    return df


def build_master():
    Path(DB_FILE).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_FILE, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")

    # ---------------------------------------------------------
    # MASTER INCREMENTAL OPERATIVO
    #
    # Cada ciclo reconstruye las ultimas 2 horas.
    # Esto permite absorber observaciones tardias y reinicios
    # sin reprocesar todo el historico.
    #
    # ERA5/NASA se consultan para exactamente las horas que
    # corresponden a esta ventana. El backfill atmosferico
    # historico se gestiona por separado.
    # ---------------------------------------------------------

    now_local = pd.Timestamp.now(
        tz="America/Lima"
    )

    window_start = (
        now_local.floor("min")
        - pd.Timedelta(hours=2)
    )

    # +1 hora garantiza cubrir correctamente bucket_hour
    # en el extremo superior de la ventana.
    window_end = (
        now_local.floor("min")
        + pd.Timedelta(hours=1)
    )

    start_iso = window_start.isoformat()
    end_iso = window_end.isoformat()

    print(
        "MASTER incremental:"
        f" {start_iso} -> {end_iso}"
    )

    weather = read_table(
        conn,
        "weather_local",
        timestamp_column="timestamp_local",
        start_local=start_iso,
        end_local=end_iso,
    )

    radio = read_table(
        conn,
        "radio_link_local",
        timestamp_column="timestamp_local",
        start_local=start_iso,
        end_local=end_iso,
    )

    # Para fuentes horarias usamos el inicio de la hora.
    atmos_start = (
        window_start.floor("h")
    ).isoformat()

    atmos_end = (
        window_end.ceil("h")
    ).isoformat()

    era5 = read_table(
        conn,
        "era5_land_hourly",
        timestamp_column="timestamp_local",
        start_local=atmos_start,
        end_local=atmos_end,
        site_tag="MID_LINK",
    )

    nasa = read_table(
        conn,
        "nasa_power_hourly",
        timestamp_column="timestamp_local",
        start_local=atmos_start,
        end_local=atmos_end,
        site_tag="MID_LINK",
    )

    weather = prepare_weather(weather)
    radio = prepare_radio(radio)
    era5 = prepare_era5(
        era5,
        site_tag="MID_LINK"
    )
    nasa = prepare_nasa_power(
        nasa,
        site_tag="MID_LINK"
    )

    if weather.empty:
        print("No hay datos meteorológicos locales válidos. No se genera master.")
        conn.close()
        return

    master = weather.copy()

    expected_radio_cols = [
        "radio_station_id",
        "radio_station_name",
        "radio_role_from_radio",
        "radio_local_role",
        "radio_timestamp_utc",
        "radio_timestamp_local",
        "radio_mcs_dl",
        "radio_mcs_ul",
        "radio_snr_dl",
        "radio_snr_ul",
        "radio_rssi_c0p",
        "radio_rssi_c0e",
        "radio_rssi_c1p",
        "radio_rssi_c1e",
        "radio_dl_rate",
        "radio_ul_rate",
        "radio_sta_dl_rssi",
        "radio_sta_ul_rssi",
        "radio_note",
        "radio_error",
    ]

    expected_era5_cols = [
        "era5_timestamp_utc",
        "era5_timestamp_local",
        "era5_site_tag",
        "era5_lat",
        "era5_lon",
        "era5_temp_c",
        "era5_dewpoint_c",
        "era5_rh_pct",
        "era5_precip_mm",
        "era5_press_hpa",
        "era5_wind_ms",
    ]

    expected_nasa_cols = [
        "nasa_timestamp_utc",
        "nasa_timestamp_local",
        "nasa_site_tag",
        "nasa_lat",
        "nasa_lon",
        "nasa_temp_c",
        "nasa_dewpoint_c",
        "nasa_rh_pct",
        "nasa_precip_mm",
        "nasa_press_kpa",
        "nasa_press_hpa",
        "nasa_wind10m_ms",
        "nasa_source",
        "nasa_downloaded_at_utc",
    ]

    if not radio.empty:
        master = master.merge(radio, on="bucket_minute", how="left")

    for col in expected_radio_cols:
        if col not in master.columns:
            master[col] = None

    master["bucket_hour"] = master["bucket_minute"].dt.floor("h")

    if not era5.empty:
        master = master.merge(era5, on="bucket_hour", how="left")

    for col in expected_era5_cols:
        if col not in master.columns:
            master[col] = None

    if not nasa.empty:
        master = master.merge(nasa, on="bucket_hour", how="left")

    for col in expected_nasa_cols:
        if col not in master.columns:
            master[col] = None

    if "station_id" not in master.columns:
        master["station_id"] = STATION_CONTEXT["station_id"]

    if "station_name" not in master.columns:
        master["station_name"] = STATION_CONTEXT["station_name"]

    if "radio_role" not in master.columns:
        master["radio_role"] = CONFIG.get("station", {}).get(
            "role",
            CONFIG.get("radio_link", {}).get("local_role", "UNKNOWN")
        )

    master["station_id"] = master["station_id"].fillna(STATION_CONTEXT["station_id"])
    master["station_name"] = master["station_name"].fillna(STATION_CONTEXT["station_name"])
    master["radio_role"] = master["radio_role"].fillna(
        STATION_CONTEXT["radio_role"]
    )

    master["master_timestamp_local"] = master["bucket_minute"].astype(str)
    master["master_timestamp_hour"] = master["bucket_hour"].astype(str)

    master = master.sort_values("bucket_minute")

    # ---------------------------------------------------------
    # Persistencia segura de master_observations
    #
    # La version anterior utilizaba:
    #
    #     if_exists="replace"
    #
    # Eso ejecutaba DROP TABLE + CREATE TABLE en cada ciclo,
    # eliminaba indices y aumentaba el riesgo de
    # "database is locked".
    #
    # Desde esta version la tabla es permanente y se actualiza
    # mediante UPSERT usando master_timestamp_local como clave.
    # ---------------------------------------------------------

    table_name = "master_observations"
    unique_index = (
        "ux_master_observations_timestamp_local"
    )

    table_exists = conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type='table'
          AND name=?
        """,
        (table_name,)
    ).fetchone() is not None

    if not table_exists:
        # Caso de recuperacion / instalacion nueva.
        # Solo se usa append para que pandas cree el esquema.
        master.head(0).to_sql(
            table_name,
            conn,
            if_exists="append",
            index=False
        )

    # Verificacion defensiva antes de crear UNIQUE.
    duplicate_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT master_timestamp_local
            FROM master_observations
            WHERE master_timestamp_local IS NOT NULL
            GROUP BY master_timestamp_local
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    if duplicate_count:
        raise RuntimeError(
            "master_observations contiene timestamps "
            "duplicados; UPSERT abortado"
        )

    null_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM master_observations
        WHERE master_timestamp_local IS NULL
        """
    ).fetchone()[0]

    if null_count:
        raise RuntimeError(
            "master_observations contiene "
            "master_timestamp_local NULL; UPSERT abortado"
        )

    conn.execute(
        f"""
        CREATE UNIQUE INDEX IF NOT EXISTS
        {unique_index}
        ON {table_name}(master_timestamp_local)
        """
    )

    # Comprobar que el dataframe que vamos a persistir
    # tampoco contiene claves invalidas.
    if master["master_timestamp_local"].isna().any():
        raise RuntimeError(
            "El nuevo master contiene timestamps NULL"
        )

    if master["master_timestamp_local"].duplicated().any():
        raise RuntimeError(
            "El nuevo master contiene timestamps duplicados"
        )

    columns = list(master.columns)

    quoted_columns = ", ".join(
        f'"{col}"'
        for col in columns
    )

    placeholders = ", ".join(
        "?"
        for _ in columns
    )

    update_columns = [
        col
        for col in columns
        if col != "master_timestamp_local"
    ]

    update_clause = ", ".join(
        f'"{col}"=excluded."{col}"'
        for col in update_columns
    )

    upsert_sql = f"""
        INSERT INTO {table_name}
        ({quoted_columns})
        VALUES ({placeholders})
        ON CONFLICT(master_timestamp_local)
        DO UPDATE SET
        {update_clause}
    """

    # ---------------------------------------------------------
    # Adaptacion de tipos pandas / numpy a tipos SQLite.
    #
    # sqlite3 no acepta directamente pd.Timestamp,
    # pd.Timedelta ni escalares numpy.
    # ---------------------------------------------------------

    def sqlite_value(value):

        if value is None:
            return None

        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass

        if isinstance(value, pd.Timestamp):
            return str(value)

        if isinstance(value, pd.Timedelta):
            return str(value)

        # Escalares numpy suelen implementar item().
        # Esto los convierte a int/float/bool nativos.
        if hasattr(value, "item"):
            try:
                return value.item()
            except (ValueError, TypeError):
                pass

        return value

    rows = [
        tuple(
            sqlite_value(value)
            for value in row
        )
        for row in master.itertuples(
            index=False,
            name=None
        )
    ]

    before_count = conn.execute(
        f"SELECT COUNT(*) FROM {table_name}"
    ).fetchone()[0]

    conn.executemany(
        upsert_sql,
        rows
    )

    conn.commit()

    after_count = conn.execute(
        f"SELECT COUNT(*) FROM {table_name}"
    ).fetchone()[0]

    print(
        "Persistencia master: UPSERT"
    )
    print(
        f"Filas antes: {before_count}"
    )
    print(
        f"Filas despues: {after_count}"
    )
    print(
        f"Filas procesadas por UPSERT: {len(rows)}"
    )

    # El CSV historico ya no se reescribe cada minuto.
    #
    # master_observations SQLite es ahora la fuente operativa.
    # La exportacion completa del CSV se realizara como tarea
    # separada para backup/reportes.
    out_csv = Path("Data/exports/master_observations.csv")

    print("MASTER DATASET incremental generado correctamente")
    print(f"Filas procesadas en ventana: {len(master)}")
    print("Tabla SQLite: master_observations")
    print(
        "CSV historico: no regenerado "
        "en ciclo incremental"
    )

    conn.close()


if __name__ == "__main__":
    build_master()
