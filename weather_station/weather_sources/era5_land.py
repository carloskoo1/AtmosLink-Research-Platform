import argparse
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone

import cdsapi
import pandas as pd
import xarray as xr

from weather_station.config.station_manager import get_station_context


STATION_CONTEXT = get_station_context()
DB_FILE = STATION_CONTEXT["database"]
ERA_CACHE_DIR = "Data/external/era5_cache"

LIMA_TZ = timezone(timedelta(hours=-5))

SITES = {
    "AP_CUNACALES": {"lat": -6.69240, "lon": -78.51418},
    "SM_SAN_JOSE": {"lat": -6.76387, "lon": -78.60154},
    "MID_LINK": {
        "lat": (-6.69240 + -6.76387) / 2.0,
        "lon": (-78.51418 + -78.60154) / 2.0,
    },
}

VARIABLES = [
    "2m_temperature",
    "2m_dewpoint_temperature",
    "total_precipitation",
    "surface_pressure",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
]


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS era5_land_hourly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_utc TEXT NOT NULL,
            timestamp_local TEXT NOT NULL,
            site_tag TEXT NOT NULL,
            lat REAL,
            lon REAL,
            temp_c REAL,
            dewpoint_c REAL,
            precip_mm REAL,
            press_hpa REAL,
            wind_ms REAL,
            UNIQUE(timestamp_utc, site_tag)
        )
    """)

    conn.commit()
    conn.close()


def cache_path(date_lima, site_tag):
    Path(ERA_CACHE_DIR).mkdir(parents=True, exist_ok=True)
    return f"{ERA_CACHE_DIR}/era5land_{site_tag}_{date_lima}.nc"


def download_day(date_lima, site_tag, lat, lon):
    path = cache_path(date_lima, site_tag)

    if Path(path).exists() and Path(path).stat().st_size > 0:
        return path

    start_lima = datetime.combine(date_lima, datetime.min.time(), tzinfo=LIMA_TZ)
    end_lima = start_lima + timedelta(days=1)

    start_utc = start_lima.astimezone(timezone.utc)
    end_utc = end_lima.astimezone(timezone.utc) - timedelta(hours=1)

    utc_days = sorted({
        start_utc.strftime("%d"),
        end_utc.strftime("%d"),
    })

    request = {
        "variable": VARIABLES,
        "year": start_utc.strftime("%Y"),
        "month": start_utc.strftime("%m"),
        "day": utc_days,
        "time": [f"{h:02d}:00" for h in range(24)],
        "area": [
            lat + 0.10,
            lon - 0.10,
            lat - 0.10,
            lon + 0.10,
        ],
        "data_format": "netcdf",
        "download_format": "unarchived",
    }

    print(f"Descargando ERA5-Land {site_tag} {date_lima}...")
    cdsapi.Client().retrieve("reanalysis-era5-land", request, path)

    return path


def detect_time_coord(ds):
    if "valid_time" in ds.coords:
        return "valid_time"
    if "time" in ds.coords:
        return "time"

    for coord in ds.coords:
        if "time" in coord.lower():
            return coord

    raise RuntimeError(f"No se encontró eje temporal. Coordenadas: {list(ds.coords)}")


def pick_col(df, *names):
    for name in names:
        if name in df.columns:
            return df[name]

    raise KeyError(f"No se encontró ninguna columna de {names}. Columnas: {list(df.columns)}")


def extract_day(date_lima, site_tag, lat, lon):
    start_lima = datetime.combine(date_lima, datetime.min.time(), tzinfo=LIMA_TZ)
    end_lima = start_lima + timedelta(days=1)

    start_utc = start_lima.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = end_lima.astimezone(timezone.utc).replace(tzinfo=None)

    nc_path = download_day(date_lima, site_tag, lat, lon)

    ds = xr.open_dataset(nc_path)
    time_name = detect_time_coord(ds)

    lat_name = "latitude" if "latitude" in ds.coords else "lat"
    lon_name = "longitude" if "longitude" in ds.coords else "lon"

    lon_sel = lon
    if float(ds[lon_name].max()) > 180 and lon_sel < 0:
        lon_sel = 360 + lon_sel

    point = ds.sel(
        {
            lat_name: lat,
            lon_name: lon_sel,
        },
        method="nearest",
    )

    # Se conserva inicialmente toda la ventana UTC descargada.
    # Esto permite utilizar la hora anterior al inicio del día
    # local para desacumular correctamente la precipitación.
    df = point.to_dataframe().reset_index()

    if time_name in df.columns and time_name != "time":
        df = df.rename(columns={time_name: "time"})

    if df.empty:
        return pd.DataFrame()

    df["timestamp_utc"] = pd.to_datetime(df["time"], utc=True)
    df["timestamp_local"] = df["timestamp_utc"].dt.tz_convert("America/Lima")

    df["temp_c"] = pick_col(df, "2m_temperature", "t2m") - 273.15
    df["dewpoint_c"] = pick_col(df, "2m_dewpoint_temperature", "d2m") - 273.15
    # ERA5-Land entrega total_precipitation como acumulación
    # dentro del ciclo. Primero se convierte de metros a milímetros
    # y después se obtiene la cantidad correspondiente a cada hora.
    precip_accumulated_mm = (
        pd.to_numeric(
            pick_col(
                df,
                "total_precipitation",
                "tp",
            ),
            errors="coerce",
        )
        * 1000.0
    )

    precip_difference_mm = (
        precip_accumulated_mm.diff()
    )

    # Una diferencia negativa identifica el reinicio del ciclo.
    # En esa hora, el propio valor acumulado representa la primera
    # cantidad del nuevo ciclo.
    df["precip_mm"] = (
        precip_difference_mm.where(
            precip_difference_mm >= 0,
            precip_accumulated_mm,
        )
        .fillna(precip_accumulated_mm)
        .clip(lower=0)
    )
    df["press_hpa"] = pick_col(df, "surface_pressure", "sp") / 100.0

    u = pick_col(df, "10m_u_component_of_wind", "u10")
    v = pick_col(df, "10m_v_component_of_wind", "v10")
    df["wind_ms"] = (u * u + v * v) ** 0.5

    # La desacumulación se realiza antes de recortar el día
    # local para no perder la observación de la hora precedente.
    start_filter = pd.Timestamp(
        start_utc,
        tz="UTC",
    )
    end_filter = pd.Timestamp(
        end_utc,
        tz="UTC",
    )

    df = df[
        (df["timestamp_utc"] >= start_filter)
        & (df["timestamp_utc"] < end_filter)
    ].copy()

    return df[[
        "timestamp_utc",
        "timestamp_local",
        "temp_c",
        "dewpoint_c",
        "precip_mm",
        "press_hpa",
        "wind_ms",
    ]]


def save_to_sqlite(df, site_tag, lat, lon):
    if df.empty:
        print(f"Sin datos ERA5 para {site_tag}")
        return

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    for _, r in df.iterrows():
        cur.execute("""
            INSERT OR IGNORE INTO era5_land_hourly (
                timestamp_utc,
                timestamp_local,
                site_tag,
                lat,
                lon,
                temp_c,
                dewpoint_c,
                precip_mm,
                press_hpa,
                wind_ms
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r["timestamp_utc"].isoformat(),
            r["timestamp_local"].isoformat(),
            site_tag,
            lat,
            lon,
            float(r["temp_c"]),
            float(r["dewpoint_c"]),
            float(r["precip_mm"]),
            float(r["press_hpa"]),
            float(r["wind_ms"]),
        ))

    conn.commit()
    conn.close()

    print(f"Guardado ERA5: {site_tag}, filas={len(df)}")


def run_for_day(date_str):
    init_db()
    date_lima = datetime.strptime(date_str, "%Y-%m-%d").date()

    for site_tag, cfg in SITES.items():
        df = extract_day(date_lima, site_tag, cfg["lat"], cfg["lon"])
        save_to_sqlite(df, site_tag, cfg["lat"], cfg["lon"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Descarga e inserta ERA5-Land horario en SQLite.")
    parser.add_argument("--day", required=True, help="Día Lima YYYY-MM-DD")
    args = parser.parse_args()

    run_for_day(args.day)
