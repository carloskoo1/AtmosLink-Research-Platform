import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from weather_station.config.station_manager import get_station_context


STATION_CONTEXT = get_station_context()
DB_FILE = Path(STATION_CONTEXT["database"])
EXPORT_FILE = Path("Data/exports/master_observations_enriched.csv")

DERIVED_COLUMNS = [
    "derived_saturation_vapor_pressure_hpa",
    "derived_actual_vapor_pressure_hpa",
    "derived_dew_point_c",
    "derived_vpd_hpa",
    "derived_heat_index_c",
    "derived_wind_chill_c",
    "derived_air_density_kg_m3",
]


def table_exists(conn, table_name: str) -> bool:
    query = """
    SELECT name FROM sqlite_master
    WHERE type='table' AND name=?
    """
    return conn.execute(query, (table_name,)).fetchone() is not None


def source_numeric(
    dataframe: pd.DataFrame,
    primary: str,
    fallback: str,
) -> pd.Series:
    """
    Preserva la semántica histórica de derive_weather_metrics:
    si existe la columna primaria, se usa esa columna; solo si
    no existe se utiliza el nombre local de respaldo.
    """
    if primary in dataframe.columns:
        values = dataframe[primary]
    elif fallback in dataframe.columns:
        values = dataframe[fallback]
    else:
        return pd.Series(
            np.nan,
            index=dataframe.index,
            dtype="float64",
        )

    return pd.to_numeric(
        values,
        errors="coerce",
    ).astype("float64")


def round_finite(
    values: pd.Series,
    digits: int,
) -> pd.Series:
    result = pd.to_numeric(
        values,
        errors="coerce",
    ).astype("float64")

    result = result.where(
        np.isfinite(result)
    )

    return result.round(digits)


def derive_weather_metrics_vectorized(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Equivalente vectorizado de derive_weather_metrics().

    Evita iterrows()/Series.to_dict() sobre todo el histórico,
    manteniendo las mismas fórmulas, reglas de validez y redondeo.
    """
    temp = source_numeric(
        dataframe,
        "temp_avg_C",
        "local_temp_avg_c",
    )
    hum = source_numeric(
        dataframe,
        "hum_avg_pct",
        "local_hum_avg_pct",
    )
    pres = source_numeric(
        dataframe,
        "pres_avg_hPa",
        "local_press_hpa",
    )
    wind = source_numeric(
        dataframe,
        "wind_speed_ms",
        "local_wind_speed_ms",
    )

    valid_temp = temp.notna()
    valid_hum = hum.notna()
    valid_pres = pres.notna()
    valid_wind = wind.notna()

    hum_valid = (
        valid_hum
        & hum.between(
            0,
            100,
            inclusive="both",
        )
    )

    hum_dew_valid = (
        valid_hum
        & (hum > 0)
        & (hum <= 100)
    )

    es = pd.Series(
        np.nan,
        index=dataframe.index,
        dtype="float64",
    )

    with np.errstate(
        divide="ignore",
        invalid="ignore",
        over="ignore",
    ):
        mask = valid_temp
        es.loc[mask] = (
            6.112
            * np.exp(
                (17.67 * temp.loc[mask])
                / (temp.loc[mask] + 243.5)
            )
        )

    ea = pd.Series(
        np.nan,
        index=dataframe.index,
        dtype="float64",
    )

    mask = valid_temp & hum_valid
    ea.loc[mask] = (
        es.loc[mask]
        * (hum.loc[mask] / 100.0)
    )

    dew_point = pd.Series(
        np.nan,
        index=dataframe.index,
        dtype="float64",
    )

    mask = valid_temp & hum_dew_valid

    with np.errstate(
        divide="ignore",
        invalid="ignore",
        over="ignore",
    ):
        alpha = (
            (17.27 * temp.loc[mask])
            / (237.7 + temp.loc[mask])
            + np.log(
                hum.loc[mask] / 100.0
            )
        )

        dew_point.loc[mask] = (
            (237.7 * alpha)
            / (17.27 - alpha)
        )

    vpd = es - ea
    vpd.loc[
        ~(valid_temp & hum_valid)
    ] = np.nan

    heat_index = pd.Series(
        np.nan,
        index=dataframe.index,
        dtype="float64",
    )

    mask = valid_temp & valid_hum

    cool = (
        mask
        & (temp < 26.7)
    )
    heat_index.loc[cool] = temp.loc[cool]

    hot = (
        mask
        & ~cool
    )

    temp_f = (
        temp.loc[hot] * 9.0 / 5.0
        + 32.0
    )
    rh = hum.loc[hot]

    hi_f = (
        -42.379
        + 2.04901523 * temp_f
        + 10.14333127 * rh
        - 0.22475541 * temp_f * rh
        - 0.00683783 * temp_f * temp_f
        - 0.05481717 * rh * rh
        + 0.00122874
        * temp_f
        * temp_f
        * rh
        + 0.00085282
        * temp_f
        * rh
        * rh
        - 0.00000199
        * temp_f
        * temp_f
        * rh
        * rh
    )

    heat_index.loc[hot] = (
        (hi_f - 32.0) * 5.0 / 9.0
    )

    wind_chill = pd.Series(
        np.nan,
        index=dataframe.index,
        dtype="float64",
    )

    mask = valid_temp & valid_wind
    wind_kmh = wind * 3.6

    simple = (
        mask
        & (
            (temp > 10)
            | (wind_kmh <= 4.8)
        )
    )

    wind_chill.loc[simple] = (
        temp.loc[simple]
    )

    chill = (
        mask
        & ~simple
    )

    with np.errstate(
        divide="ignore",
        invalid="ignore",
        over="ignore",
    ):
        wind_power = np.power(
            wind_kmh.loc[chill],
            0.16,
        )

        wind_chill.loc[chill] = (
            13.12
            + 0.6215 * temp.loc[chill]
            - 11.37 * wind_power
            + 0.3965
            * temp.loc[chill]
            * wind_power
        )

    air_density = pd.Series(
        np.nan,
        index=dataframe.index,
        dtype="float64",
    )

    mask = (
        valid_temp
        & valid_pres
        & hum_valid
    )

    temp_k = (
        temp.loc[mask] + 273.15
    )
    pressure_pa = (
        pres.loc[mask] * 100.0
    )
    vapor_pressure_pa = (
        ea.loc[mask] * 100.0
    )
    dry_air_pressure_pa = (
        pressure_pa
        - vapor_pressure_pa
    )

    with np.errstate(
        divide="ignore",
        invalid="ignore",
        over="ignore",
    ):
        air_density.loc[mask] = (
            dry_air_pressure_pa
            / (287.05 * temp_k)
            + vapor_pressure_pa
            / (461.495 * temp_k)
        )

    return pd.DataFrame(
        {
            DERIVED_COLUMNS[0]: round_finite(
                es,
                2,
            ),
            DERIVED_COLUMNS[1]: round_finite(
                ea,
                2,
            ),
            DERIVED_COLUMNS[2]: round_finite(
                dew_point,
                2,
            ),
            DERIVED_COLUMNS[3]: round_finite(
                vpd,
                2,
            ),
            DERIVED_COLUMNS[4]: round_finite(
                heat_index,
                2,
            ),
            DERIVED_COLUMNS[5]: round_finite(
                wind_chill,
                2,
            ),
            DERIVED_COLUMNS[6]: round_finite(
                air_density,
                4,
            ),
        },
        index=dataframe.index,
    )


def enrich_master_dataset():
    if not DB_FILE.exists():
        raise FileNotFoundError(
            f"No existe la base de datos: {DB_FILE}"
        )

    conn = sqlite3.connect(
        DB_FILE,
        timeout=60,
    )
    conn.execute(
        "PRAGMA busy_timeout=60000"
    )

    if not table_exists(
        conn,
        "master_observations",
    ):
        conn.close()
        raise RuntimeError(
            "No existe la tabla master_observations. "
            "Ejecuta primero build_master_dataset."
        )

    df = pd.read_sql_query(
        "SELECT * FROM master_observations",
        conn,
    )

    if df.empty:
        conn.close()
        print(
            "master_observations está vacío. "
            "No se generó dataset enriquecido."
        )
        return

    derived_df = (
        derive_weather_metrics_vectorized(
            df
        )
    )

    enriched = pd.concat(
        [
            df.reset_index(drop=True),
            derived_df.reset_index(
                drop=True
            ),
        ],
        axis=1,
    )

    enriched.to_sql(
        "master_observations_enriched",
        conn,
        if_exists="replace",
        index=False,
        chunksize=1000,
    )

    EXPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    enriched.to_csv(
        EXPORT_FILE,
        index=False,
    )

    conn.close()

    print(
        "MASTER DATASET ENRIQUECIDO "
        "generado correctamente"
    )
    print(
        f"Estación : "
        f"{STATION_CONTEXT['station_id']} | "
        f"{STATION_CONTEXT['station_name']}"
    )
    print(
        f"Filas    : {len(enriched)}"
    )
    print(
        "Tabla    : "
        "master_observations_enriched"
    )
    print(
        f"CSV      : {EXPORT_FILE}"
    )


if __name__ == "__main__":
    enrich_master_dataset()
