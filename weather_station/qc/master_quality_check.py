import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from weather_station.config.station_manager import get_station_context


STATION_CONTEXT = get_station_context()
DB_FILE = Path(STATION_CONTEXT["database"])
EXPORT_FILE = Path("Data/exports/master_quality_report.csv")

QC_COLUMNS = [
    "station_id",
    "master_timestamp_local",
    "local_temp_avg_c",
    "local_hum_avg_pct",
    "local_press_hpa",
    "local_rain_total_mm",
    "derived_vpd_hpa",
    "derived_air_density_kg_m3",
]


def table_exists(
    conn,
    table_name: str,
) -> bool:
    query = """
    SELECT name FROM sqlite_master
    WHERE type='table' AND name=?
    """
    return (
        conn.execute(
            query,
            (table_name,),
        ).fetchone()
        is not None
    )


def table_columns(
    conn,
    table_name: str,
) -> set[str]:
    return {
        row[1]
        for row in conn.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()
    }


def add_issue_dict(
    issues,
    row,
    issue_type,
    severity,
    message,
):
    issues.append(
        {
            "station_id": row.get(
                "station_id"
            ),
            "timestamp": row.get(
                "master_timestamp_local"
            ),
            "issue_type": issue_type,
            "severity": severity,
            "message": message,
        }
    )


def run_quality_check():
    if not DB_FILE.exists():
        raise FileNotFoundError(
            f"No existe la base de datos: "
            f"{DB_FILE}"
        )

    conn = sqlite3.connect(
        DB_FILE,
        timeout=60,
    )
    conn.execute(
        "PRAGMA busy_timeout=60000"
    )

    table = (
        "master_observations_enriched"
    )

    if not table_exists(
        conn,
        table,
    ):
        conn.close()
        raise RuntimeError(
            "No existe "
            "master_observations_enriched. "
            "Ejecuta primero "
            "enrich_master_dataset."
        )

    available = table_columns(
        conn,
        table,
    )

    mandatory = {
        "station_id",
        "master_timestamp_local",
    }

    missing_mandatory = (
        mandatory - available
    )

    if missing_mandatory:
        conn.close()
        raise RuntimeError(
            "Faltan columnas obligatorias "
            "en master_observations_enriched: "
            + ", ".join(
                sorted(
                    missing_mandatory
                )
            )
        )

    select_expressions = []

    for column in QC_COLUMNS:
        if column in available:
            select_expressions.append(
                f'"{column}"'
            )
        else:
            select_expressions.append(
                f'NULL AS "{column}"'
            )

    df = pd.read_sql_query(
        "SELECT "
        + ", ".join(
            select_expressions
        )
        + f" FROM {table}",
        conn,
    )

    issues = []

    if df.empty:
        conn.close()
        print(
            "Dataset enriquecido vacío. "
            "No se generó control de calidad."
        )
        return

    df["dt"] = pd.to_datetime(
        df["master_timestamp_local"],
        errors="coerce",
    )

    df = df.sort_values("dt")

    temp = pd.to_numeric(
        df["local_temp_avg_c"],
        errors="coerce",
    )
    hum = pd.to_numeric(
        df["local_hum_avg_pct"],
        errors="coerce",
    )
    pres = pd.to_numeric(
        df["local_press_hpa"],
        errors="coerce",
    )
    vpd = pd.to_numeric(
        df["derived_vpd_hpa"],
        errors="coerce",
    )
    air_density = pd.to_numeric(
        df[
            "derived_air_density_kg_m3"
        ],
        errors="coerce",
    )

    row_rules = [
        (
            df["dt"].isna(),
            "INVALID_TIMESTAMP",
            "critical",
            lambda row: (
                "Timestamp no interpretable."
            ),
        ),
        (
            (
                temp.isna()
                | hum.isna()
                | pres.isna()
            ),
            "MISSING_CORE_METEO",
            "critical",
            lambda row: (
                "Faltan temperatura, "
                "humedad o presión."
            ),
        ),
        (
            (
                temp.notna()
                & (
                    (temp < -30)
                    | (temp > 60)
                )
            ),
            "TEMP_OUT_OF_RANGE",
            "critical",
            lambda row: (
                "Temperatura fuera de rango: "
                f"{row['local_temp_avg_c']}"
            ),
        ),
        (
            (
                hum.notna()
                & (
                    (hum < 0)
                    | (hum > 100)
                )
            ),
            "HUM_OUT_OF_RANGE",
            "critical",
            lambda row: (
                "Humedad fuera de rango: "
                f"{row['local_hum_avg_pct']}"
            ),
        ),
        (
            (
                pres.notna()
                & (
                    (pres < 500)
                    | (pres > 1100)
                )
            ),
            "PRESS_OUT_OF_RANGE",
            "critical",
            lambda row: (
                "Presión fuera de rango: "
                f"{row['local_press_hpa']}"
            ),
        ),
        (
            (
                vpd.notna()
                & (vpd < 0)
            ),
            "NEGATIVE_VPD",
            "warning",
            lambda row: (
                "VPD negativo: "
                f"{row['derived_vpd_hpa']}"
            ),
        ),
        (
            (
                air_density.notna()
                & (
                    (air_density < 0.7)
                    | (air_density > 1.4)
                )
            ),
            "AIR_DENSITY_SUSPICIOUS",
            "warning",
            lambda row: (
                "Densidad del aire "
                "sospechosa: "
                f"{row['derived_air_density_kg_m3']}"
            ),
        ),
    ]

    row_events = []

    for priority, (
        mask,
        issue_type,
        severity,
        message_factory,
    ) in enumerate(row_rules):
        positions = np.flatnonzero(
            mask.to_numpy()
        )

        for position in positions:
            row = df.iloc[
                int(position)
            ]

            row_events.append(
                (
                    int(position),
                    priority,
                    row,
                    issue_type,
                    severity,
                    message_factory(row),
                )
            )

    row_events.sort(
        key=lambda item: (
            item[0],
            item[1],
        )
    )

    for (
        _,
        _,
        row,
        issue_type,
        severity,
        message,
    ) in row_events:
        add_issue_dict(
            issues,
            row,
            issue_type,
            severity,
            message,
        )

    numeric_checks = [
        (
            "local_temp_avg_c",
            8.0,
            "TEMP_JUMP",
        ),
        (
            "local_hum_avg_pct",
            20.0,
            "HUM_JUMP",
        ),
        (
            "local_press_hpa",
            5.0,
            "PRESS_JUMP",
        ),
        (
            "local_rain_total_mm",
            20.0,
            "RAIN_TOTAL_JUMP",
        ),
    ]

    for (
        column,
        threshold,
        issue_type,
    ) in numeric_checks:
        values = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        diffs = values.diff().abs()

        positions = np.flatnonzero(
            (
                diffs > threshold
            ).to_numpy()
        )

        for position in positions:
            position = int(position)
            row = df.iloc[position]

            add_issue_dict(
                issues,
                row,
                issue_type,
                "warning",
                (
                    "Salto brusco en "
                    f"{column}: "
                    f"Δ={diffs.iloc[position]:.2f}"
                ),
            )

    report = pd.DataFrame(
        issues
    )

    if report.empty:
        report = pd.DataFrame(
            [
                {
                    "station_id": (
                        STATION_CONTEXT[
                            "station_id"
                        ]
                    ),
                    "timestamp": None,
                    "issue_type": (
                        "NO_ISSUES"
                    ),
                    "severity": "ok",
                    "message": (
                        "No se detectaron "
                        "problemas de calidad."
                    ),
                }
            ]
        )

    report.to_sql(
        "master_quality_report",
        conn,
        if_exists="replace",
        index=False,
    )

    EXPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report.to_csv(
        EXPORT_FILE,
        index=False,
    )

    conn.close()

    print(
        "REPORTE DE CALIDAD "
        "generado correctamente"
    )
    print(
        f"Estación : "
        f"{STATION_CONTEXT['station_id']} | "
        f"{STATION_CONTEXT['station_name']}"
    )
    print(
        f"Issues   : {len(report)}"
    )
    print(
        "Tabla    : "
        "master_quality_report"
    )
    print(
        f"CSV      : {EXPORT_FILE}"
    )


if __name__ == "__main__":
    run_quality_check()
