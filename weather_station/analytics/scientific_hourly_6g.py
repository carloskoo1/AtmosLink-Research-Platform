#!/usr/bin/env python3

import sqlite3
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd


DB = Path("SQLite/CU01/weather_local.db")
EXPORT_DIR = Path("Data/exports")

GENERAL_TABLE = "scientific_hourly_6g_general"
WIND_TABLE = "scientific_hourly_6g_wind"


def first_valid(series):
    x = series.dropna()
    return x.iloc[0] if not x.empty else np.nan


def mode_value(series):
    x = series.dropna()
    if x.empty:
        return np.nan
    m = x.mode()
    return m.iloc[0] if not m.empty else x.iloc[0]


def load_qc(con):
    needed = [
        "rf_timestamp_local",
        "field_analysis_valid",

        "operating_frequency_mhz",
        "channel_bandwidth_mhz",

        "dl_rssi_dbm",
        "ul_rssi_dbm",
        "dl_snr_db",
        "ul_snr_db",
        "dl_mcs",
        "ul_mcs",
        "reported_dl_link_rate_mbps",
        "reported_ul_link_rate_mbps",

        "cu01_local_temp_avg_c",
        "cu01_local_hum_avg_pct",
        "cu01_local_press_hpa",
        "cu01_local_dew_point_c",
        "cu01_local_vapor_pressure_hpa",
        "cu01_local_rain_1h_mm",
        "cu01_local_wind_speed_ms",
        "cu01_local_wind_gust_ms",

        "sj01_local_temp_avg_c",
        "sj01_local_hum_avg_pct",
        "sj01_local_press_hpa",
        "sj01_local_dew_point_c",
        "sj01_local_vapor_pressure_hpa",
        "sj01_local_rain_1h_mm",
        "sj01_local_wind_speed_ms",
        "sj01_local_wind_gust_ms",

        "cu01_era5_temp_c",
        "cu01_era5_dewpoint_c",
        "cu01_era5_rh_pct",
        "cu01_era5_precip_mm",
        "cu01_era5_press_hpa",
        "cu01_era5_wind_ms",

        "sj01_era5_temp_c",
        "sj01_era5_dewpoint_c",
        "sj01_era5_rh_pct",
        "sj01_era5_precip_mm",
        "sj01_era5_press_hpa",
        "sj01_era5_wind_ms",

        "cu01_nasa_temp_c",
        "cu01_nasa_dewpoint_c",
        "cu01_nasa_rh_pct",
        "cu01_nasa_precip_mm",
        "cu01_nasa_press_hpa",
        "cu01_nasa_wind10m_ms",

        "sj01_nasa_temp_c",
        "sj01_nasa_dewpoint_c",
        "sj01_nasa_rh_pct",
        "sj01_nasa_precip_mm",
        "sj01_nasa_press_hpa",
        "sj01_nasa_wind10m_ms",

        "qc_operational_exclusion",
        "qc_rf_collection_ok",
        "qc_rf_available",
        "qc_rf_values_valid",
        "qc_weather_match_valid",
        "qc_cu01_pressure_valid",
        "qc_sj01_pressure_valid",
        "qc_gust_common_method",
        "qc_analysis_valid",
        "qc_wind_analysis_valid",
        "qc_exclusion_reasons",
    ]

    sql = f"""
        SELECT {", ".join(needed)}
        FROM scientific_campaign_6g_analysis_qc
        ORDER BY rf_timestamp_local
    """

    df = pd.read_sql_query(sql, con)

    if df.empty:
        raise RuntimeError("scientific_campaign_6g_analysis_qc está vacío")

    df["rf_timestamp_utc"] = pd.to_datetime(
        df["rf_timestamp_local"],
        utc=True,
        errors="coerce"
    )

    df = df[df["rf_timestamp_utc"].notna()].copy()

    df["hour_utc"] = df["rf_timestamp_utc"].dt.floor("h")

    df["hour_local"] = (
        df["hour_utc"]
        .dt.tz_convert("America/Lima")
    )

    return df


def basic_hourly(df, validity_column):
    """
    Genera una observación por hora.

    El dataframe completo se usa para conocer cobertura y exclusiones.
    Solo validity_column == 1 entra en los estadísticos científicos.
    """

    all_counts = (
        df.groupby("hour_utc")
        .size()
        .rename("rf_total_count")
    )

    excluded_counts = (
        df.groupby("hour_utc")["qc_operational_exclusion"]
        .sum()
        .rename("operational_excluded_count")
    )

    valid = df[df[validity_column] == 1].copy()

    if valid.empty:
        return pd.DataFrame()

    agg = valid.groupby("hour_utc").agg(

        rf_valid_count=("rf_timestamp_local", "count"),

        frequency_mhz=("operating_frequency_mhz", mode_value),
        bandwidth_mhz=("channel_bandwidth_mhz", mode_value),

        dl_rssi_mean_dbm=("dl_rssi_dbm", "mean"),
        dl_rssi_median_dbm=("dl_rssi_dbm", "median"),
        dl_rssi_std_db=("dl_rssi_dbm", "std"),
        dl_rssi_min_dbm=("dl_rssi_dbm", "min"),
        dl_rssi_max_dbm=("dl_rssi_dbm", "max"),

        ul_rssi_mean_dbm=("ul_rssi_dbm", "mean"),
        ul_rssi_median_dbm=("ul_rssi_dbm", "median"),
        ul_rssi_std_db=("ul_rssi_dbm", "std"),
        ul_rssi_min_dbm=("ul_rssi_dbm", "min"),
        ul_rssi_max_dbm=("ul_rssi_dbm", "max"),

        dl_snr_mean_db=("dl_snr_db", "mean"),
        dl_snr_median_db=("dl_snr_db", "median"),
        dl_snr_std_db=("dl_snr_db", "std"),
        dl_snr_min_db=("dl_snr_db", "min"),
        dl_snr_max_db=("dl_snr_db", "max"),

        ul_snr_mean_db=("ul_snr_db", "mean"),
        ul_snr_median_db=("ul_snr_db", "median"),
        ul_snr_std_db=("ul_snr_db", "std"),
        ul_snr_min_db=("ul_snr_db", "min"),
        ul_snr_max_db=("ul_snr_db", "max"),

        dl_mcs_median=("dl_mcs", "median"),
        ul_mcs_median=("ul_mcs", "median"),

        reported_dl_link_rate_median_mbps=(
            "reported_dl_link_rate_mbps", "median"
        ),
        reported_ul_link_rate_median_mbps=(
            "reported_ul_link_rate_mbps", "median"
        ),

        # CU01 local
        cu01_temp_mean_c=("cu01_local_temp_avg_c", "mean"),
        cu01_temp_median_c=("cu01_local_temp_avg_c", "median"),
        cu01_rh_mean_pct=("cu01_local_hum_avg_pct", "mean"),
        cu01_rh_median_pct=("cu01_local_hum_avg_pct", "median"),
        cu01_press_median_hpa=("cu01_local_press_hpa", "median"),
        cu01_dewpoint_median_c=("cu01_local_dew_point_c", "median"),
        cu01_vapor_pressure_median_hpa=(
            "cu01_local_vapor_pressure_hpa", "median"
        ),
        cu01_rain_1h_max_mm=("cu01_local_rain_1h_mm", "max"),
        cu01_wind_mean_ms=("cu01_local_wind_speed_ms", "mean"),
        cu01_gust_max_ms=("cu01_local_wind_gust_ms", "max"),

        # SJ01 local
        sj01_temp_mean_c=("sj01_local_temp_avg_c", "mean"),
        sj01_temp_median_c=("sj01_local_temp_avg_c", "median"),
        sj01_rh_mean_pct=("sj01_local_hum_avg_pct", "mean"),
        sj01_rh_median_pct=("sj01_local_hum_avg_pct", "median"),
        sj01_press_median_hpa=("sj01_local_press_hpa", "median"),
        sj01_dewpoint_median_c=("sj01_local_dew_point_c", "median"),
        sj01_vapor_pressure_median_hpa=(
            "sj01_local_vapor_pressure_hpa", "median"
        ),
        sj01_rain_1h_max_mm=("sj01_local_rain_1h_mm", "max"),
        sj01_wind_mean_ms=("sj01_local_wind_speed_ms", "mean"),
        sj01_gust_max_ms=("sj01_local_wind_gust_ms", "max"),

        # ERA5 CU01
        cu01_era5_temp_c=("cu01_era5_temp_c", first_valid),
        cu01_era5_dewpoint_c=("cu01_era5_dewpoint_c", first_valid),
        cu01_era5_rh_pct=("cu01_era5_rh_pct", first_valid),
        cu01_era5_precip_mm=("cu01_era5_precip_mm", first_valid),
        cu01_era5_press_hpa=("cu01_era5_press_hpa", first_valid),
        cu01_era5_wind_ms=("cu01_era5_wind_ms", first_valid),

        # ERA5 SJ01
        sj01_era5_temp_c=("sj01_era5_temp_c", first_valid),
        sj01_era5_dewpoint_c=("sj01_era5_dewpoint_c", first_valid),
        sj01_era5_rh_pct=("sj01_era5_rh_pct", first_valid),
        sj01_era5_precip_mm=("sj01_era5_precip_mm", first_valid),
        sj01_era5_press_hpa=("sj01_era5_press_hpa", first_valid),
        sj01_era5_wind_ms=("sj01_era5_wind_ms", first_valid),

        # NASA CU01
        cu01_nasa_temp_c=("cu01_nasa_temp_c", first_valid),
        cu01_nasa_dewpoint_c=("cu01_nasa_dewpoint_c", first_valid),
        cu01_nasa_rh_pct=("cu01_nasa_rh_pct", first_valid),
        cu01_nasa_precip_mm=("cu01_nasa_precip_mm", first_valid),
        cu01_nasa_press_hpa=("cu01_nasa_press_hpa", first_valid),
        cu01_nasa_wind10m_ms=("cu01_nasa_wind10m_ms", first_valid),

        # NASA SJ01
        sj01_nasa_temp_c=("sj01_nasa_temp_c", first_valid),
        sj01_nasa_dewpoint_c=("sj01_nasa_dewpoint_c", first_valid),
        sj01_nasa_rh_pct=("sj01_nasa_rh_pct", first_valid),
        sj01_nasa_precip_mm=("sj01_nasa_precip_mm", first_valid),
        sj01_nasa_press_hpa=("sj01_nasa_press_hpa", first_valid),
        sj01_nasa_wind10m_ms=("sj01_nasa_wind10m_ms", first_valid),

    )

    agg = agg.join(all_counts, how="left")
    agg = agg.join(excluded_counts, how="left")

    # Porcentaje de validez entre las filas RF realmente observadas
    agg["rf_validity_pct"] = (
        100.0 *
        agg["rf_valid_count"] /
        agg["rf_total_count"]
    )

    # Cobertura temporal esperada.
    # La telemetría RF nominal se colecta aproximadamente cada 5 minutos:
    # 12 observaciones esperadas por hora completa.
    agg["rf_expected_count"] = 12

    agg["rf_temporal_coverage_pct"] = (
        100.0 *
        agg["rf_total_count"] /
        agg["rf_expected_count"]
    ).clip(upper=100.0)

    # Compatibilidad con versiones previas:
    # rf_coverage_pct conserva temporalmente el significado antiguo.
    agg["rf_coverage_pct"] = agg["rf_validity_pct"]

    # ¿Hubo más de una configuración RF dentro de la misma hora?
    cfg_n = (
        valid[
            [
                "hour_utc",
                "operating_frequency_mhz",
                "channel_bandwidth_mhz",
            ]
        ]
        .drop_duplicates()
        .groupby("hour_utc")
        .size()
        .rename("configuration_count")
    )

    agg = agg.join(cfg_n, how="left")
    agg["configuration_mixed"] = (
        agg["configuration_count"] > 1
    ).astype(int)

    # Identificación provisional de escenario baseline.
    agg["scenario_id"] = np.where(
        (agg["frequency_mhz"] == 7000) &
        (agg["bandwidth_mhz"] == 20),
        "BASELINE_F7000_B20",
        "UNCLASSIFIED"
    )

    agg = agg.reset_index()

    agg["hour_local"] = (
        agg["hour_utc"]
        .dt.tz_convert("America/Lima")
        .astype(str)
    )

    agg["hour_utc"] = agg["hour_utc"].astype(str)

    agg["generated_at_utc"] = (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
    )

    return agg


def find_col(columns, candidates):
    lower = {c.lower(): c for c in columns}

    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]

    return None


def integrate_active_throughput(con, hourly):
    """
    Intenta incorporar active_throughput_6g sin asumir su esquema.
    Si no reconoce las columnas mínimas, conserva el dataset horario
    y muestra el esquema detectado.
    """

    exists = con.execute("""
        SELECT COUNT(*)
        FROM sqlite_master
        WHERE type='table'
          AND name='active_throughput_6g'
    """).fetchone()[0]

    if not exists:
        print("active_throughput_6g: tabla no encontrada")
        return hourly

    columns = [
        r[1]
        for r in con.execute(
            "PRAGMA table_info(active_throughput_6g)"
        )
    ]

    print("\n===== ACTIVE THROUGHPUT: COLUMNAS =====")
    print(", ".join(columns))

    timestamp_col = find_col(columns, [
        "timestamp_start_local",
        "timestamp_start_utc",
        "timestamp_local",
        "test_timestamp_local",
        "started_at_local",
        "start_timestamp_local",
        "datetime_local",
        "timestamp",
    ])

    direction_col = find_col(columns, [
        "direction",
        "traffic_direction",
        "test_direction",
    ])

    throughput_col = find_col(columns, [
        "measured_throughput_mbps",
        "receiver_mbps",
        "sender_mbps",
        "goodput_mbps",
        "throughput_mbps",
        "measured_mbps",
        "bitrate_mbps",
        "mbps",
    ])

    rtt_col = find_col(columns, [
        "ping_rtt_avg_ms",
        "rtt_ms",
        "avg_rtt_ms",
        "mean_rtt_ms",
        "ping_rtt_ms",
    ])

    retrans_col = find_col(columns, [
        "retransmits",
        "retransmissions",
        "retrans",
        "tcp_retransmissions",
    ])

    if timestamp_col is None:
        print(
            "active_throughput_6g: no se reconoció columna temporal. "
            "No se fusionó throughput."
        )
        return hourly

    use = [timestamp_col]

    for c in [
        direction_col,
        throughput_col,
        rtt_col,
        retrans_col,
    ]:
        if c and c not in use:
            use.append(c)

    tp = pd.read_sql_query(
        f"""
        SELECT {", ".join(use)}
        FROM active_throughput_6g
        WHERE status = 'OK'
        """,
        con
    )

    tp["hour_utc"] = pd.to_datetime(
        tp[timestamp_col],
        utc=True,
        errors="coerce"
    ).dt.floor("h")

    tp = tp[tp["hour_utc"].notna()].copy()

    if tp.empty:
        print("active_throughput_6g: sin timestamps utilizables")
        return hourly

    h = hourly.copy()
    h["_hour_merge"] = pd.to_datetime(
        h["hour_utc"],
        utc=True,
        errors="coerce"
    )

    # Caso ideal: dirección + throughput.
    if direction_col and throughput_col:

        tp["_direction"] = (
            tp[direction_col]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        def classify_direction(v):
            if (
                "DL" in v or
                "DOWN" in v or
                "CU01_TO_SJ01" in v or
                "AP_TO_SM" in v
            ):
                return "DL"

            if (
                "UL" in v or
                "UP" in v or
                "SJ01_TO_CU01" in v or
                "SM_TO_AP" in v
            ):
                return "UL"

            return "OTHER"

        tp["_dir2"] = tp["_direction"].map(classify_direction)

        for d in ["DL", "UL"]:
            z = tp[tp["_dir2"] == d].copy()

            if z.empty:
                continue

            aggregation = {
                throughput_col: ["mean", "median", "std", "count"]
            }

            if rtt_col:
                aggregation[rtt_col] = ["mean", "median"]

            if retrans_col:
                aggregation[retrans_col] = ["sum", "mean"]

            g = z.groupby("hour_utc").agg(aggregation)

            g.columns = [
                "_".join(
                    [str(x) for x in col if str(x)]
                )
                for col in g.columns.to_flat_index()
            ]

            prefix = d.lower() + "_active_"

            g = g.rename(
                columns={
                    c: prefix + c
                    for c in g.columns
                }
            )

            h = h.merge(
                g,
                left_on="_hour_merge",
                right_index=True,
                how="left"
            )

        print(
            "active_throughput_6g: integración horaria realizada "
            f"timestamp={timestamp_col}, "
            f"direction={direction_col}, "
            f"throughput={throughput_col}"
        )

    else:
        # Guardamos por lo menos número de pruebas por hora.
        g = (
            tp.groupby("hour_utc")
            .size()
            .rename("active_throughput_test_count")
        )

        h = h.merge(
            g,
            left_on="_hour_merge",
            right_index=True,
            how="left"
        )

        print(
            "active_throughput_6g: integración parcial. "
            "No se reconoció dirección y/o throughput."
        )

    h = h.drop(columns=["_hour_merge"])

    return h


def publish(con, df, table_name, csv_path):
    if df.empty:
        raise RuntimeError(f"{table_name}: dataframe vacío")

    df.to_sql(
        table_name,
        con,
        if_exists="replace",
        index=False
    )

    df.to_csv(
        csv_path,
        index=False
    )


def main():
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(DB)

    try:
        print("==========================================")
        print(" AtmosLink Scientific Hourly 6 GHz Builder")
        print("==========================================")
        print("Database:", DB)

        qc = load_qc(con)

        print("Filas QC:", len(qc))
        print(
            "Rango:",
            qc["rf_timestamp_local"].min(),
            "->",
            qc["rf_timestamp_local"].max()
        )

        general = basic_hourly(
            qc,
            "qc_analysis_valid"
        )

        wind = basic_hourly(
            qc,
            "qc_wind_analysis_valid"
        )

        general = integrate_active_throughput(
            con,
            general
        )

        wind = integrate_active_throughput(
            con,
            wind
        )

        general_csv = (
            EXPORT_DIR /
            "scientific_hourly_6g_general.csv"
        )

        wind_csv = (
            EXPORT_DIR /
            "scientific_hourly_6g_wind.csv"
        )

        publish(
            con,
            general,
            GENERAL_TABLE,
            general_csv
        )

        publish(
            con,
            wind,
            WIND_TABLE,
            wind_csv
        )

        con.commit()

        print("\n===== RESULTADOS =====")
        print(
            GENERAL_TABLE,
            "filas =",
            len(general)
        )
        print(
            WIND_TABLE,
            "filas =",
            len(wind)
        )

        print(
            "general rango =",
            general["hour_local"].min(),
            "->",
            general["hour_local"].max()
        )

        print(
            "wind rango =",
            wind["hour_local"].min(),
            "->",
            wind["hour_local"].max()
        )

        print("\nCSV general:", general_csv)
        print("CSV viento :", wind_csv)

        print(
            "\nquick_check =",
            con.execute(
                "PRAGMA quick_check"
            ).fetchone()[0]
        )

        print("Status: OK")

    finally:
        con.close()


if __name__ == "__main__":
    main()
