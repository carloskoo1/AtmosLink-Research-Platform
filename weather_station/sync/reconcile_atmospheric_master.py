from __future__ import annotations

import argparse
import json
import math
import sqlite3
from pathlib import Path

import pandas as pd

from weather_station.sync.build_master_dataset import (
    calc_relative_humidity_pct,
)


DB_FILE = Path(
    "SQLite/CU01/weather_local.db"
)

STATE_FILE = Path(
    "runtime/atmospheric_reconciler_state.json"
)

SITE_TAG = "MID_LINK"


ERA5_MASTER_COLUMNS = [
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


NASA_MASTER_COLUMNS = [
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


def load_state():
    if not STATE_FILE.exists():
        return {}

    try:
        return json.loads(
            STATE_FILE.read_text(
                encoding="utf-8"
            )
        )
    except Exception as exc:
        raise RuntimeError(
            f"No se pudo leer {STATE_FILE}: {exc}"
        )


def save_state(state):
    STATE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp = STATE_FILE.with_suffix(
        ".json.tmp"
    )

    temp.write_text(
        json.dumps(
            state,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    temp.replace(STATE_FILE)


def clean_value(value):
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass

    return value


def numeric(value):
    value = clean_value(value)

    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None

    return number


def in_range(value, low, high):
    value = numeric(value)

    if value is None:
        return False

    return low <= value <= high


def nonnegative(value):
    value = numeric(value)

    if value is None:
        return False

    return value >= 0


def master_hour_bounds(timestamp_local):
    ts = pd.Timestamp(timestamp_local)

    start = ts.floor("h")
    end = start + pd.Timedelta(hours=1)

    return (
        start.isoformat().replace(
            "T",
            " ",
            1,
        ),
        end.isoformat().replace(
            "T",
            " ",
            1,
        ),
    )


def era5_target(row):
    temp = clean_value(row["temp_c"])
    dew = clean_value(row["dewpoint_c"])

    rh = None

    if temp is not None and dew is not None:
        try:
            rh_series = (
                calc_relative_humidity_pct(
                    pd.Series([temp]),
                    pd.Series([dew]),
                )
            )

            rh = clean_value(
                rh_series.iloc[0]
            )
        except Exception:
            rh = None

    return [
        clean_value(row["timestamp_utc"]),
        clean_value(row["timestamp_local"]),
        clean_value(row["site_tag"]),
        clean_value(row["lat"]),
        clean_value(row["lon"]),
        temp,
        dew,
        rh,
        clean_value(row["precip_mm"]),
        clean_value(row["press_hpa"]),
        clean_value(row["wind_ms"]),
    ]


def nasa_row_is_valid(row):
    return (
        in_range(
            row["temp_c"],
            -60,
            60,
        )
        and in_range(
            row["dewpoint_c"],
            -80,
            60,
        )
        and in_range(
            row["rh_pct"],
            0,
            100,
        )
        and nonnegative(
            row["precip_mm"]
        )
        and in_range(
            row["press_hpa"],
            300,
            1100,
        )
        and nonnegative(
            row["wind10m_ms"]
        )
    )


def nasa_target(row):
    if not nasa_row_is_valid(row):
        return [
            None
            for _ in NASA_MASTER_COLUMNS
        ]

    return [
        clean_value(row["timestamp_utc"]),
        clean_value(row["timestamp_local"]),
        clean_value(row["site_tag"]),
        clean_value(row["lat"]),
        clean_value(row["lon"]),
        clean_value(row["temp_c"]),
        clean_value(row["dewpoint_c"]),
        clean_value(row["rh_pct"]),
        clean_value(row["precip_mm"]),
        clean_value(row["press_kpa"]),
        clean_value(row["press_hpa"]),
        clean_value(row["wind10m_ms"]),
        clean_value(row["source"]),
        clean_value(row["downloaded_at_utc"]),
    ]


def mismatch_clause(columns):
    return " OR ".join(
        f'"{column}" IS NOT ?'
        for column in columns
    )


def update_set_clause(columns):
    return ", ".join(
        f'"{column}" = ?'
        for column in columns
    )


def count_master_rows(
    conn,
    start_text,
    end_text,
):
    return conn.execute("""
        SELECT COUNT(*)
        FROM master_observations
        WHERE master_timestamp_local >= ?
          AND master_timestamp_local < ?
    """, (
        start_text,
        end_text,
    )).fetchone()[0]


def count_mismatches(
    conn,
    columns,
    target,
    start_text,
    end_text,
):
    sql = f"""
        SELECT COUNT(*)
        FROM master_observations
        WHERE master_timestamp_local >= ?
          AND master_timestamp_local < ?
          AND (
              {mismatch_clause(columns)}
          )
    """

    return conn.execute(
        sql,
        [
            start_text,
            end_text,
            *target,
        ],
    ).fetchone()[0]


def apply_update(
    conn,
    columns,
    target,
    start_text,
    end_text,
):
    sql = f"""
        UPDATE master_observations
        SET
            {update_set_clause(columns)}
        WHERE master_timestamp_local >= ?
          AND master_timestamp_local < ?
          AND (
              {mismatch_clause(columns)}
          )
    """

    cur = conn.execute(
        sql,
        [
            *target,
            start_text,
            end_text,
            *target,
        ],
    )

    return cur.rowcount


def initial_era5_watermark(conn):
    return conn.execute("""
        SELECT MAX(era5_timestamp_local)
        FROM master_observations
        WHERE era5_timestamp_local IS NOT NULL
    """).fetchone()[0]


def initial_nasa_watermark(conn):
    # Para la primera ejecución usamos el máximo
    # downloaded_at que ya fue incorporado al master.
    return conn.execute("""
        SELECT MAX(nasa_downloaded_at_utc)
        FROM master_observations
        WHERE nasa_downloaded_at_utc IS NOT NULL
    """).fetchone()[0]


def get_era5_candidates(
    conn,
    watermark,
):
    if watermark is None:
        return conn.execute("""
            SELECT *
            FROM era5_land_hourly
            WHERE site_tag=?
            ORDER BY timestamp_local
        """, (SITE_TAG,)).fetchall()

    return conn.execute("""
        SELECT *
        FROM era5_land_hourly
        WHERE site_tag=?
          AND timestamp_local > ?
        ORDER BY timestamp_local
    """, (
        SITE_TAG,
        watermark,
    )).fetchall()


def get_nasa_candidates(
    conn,
    watermark,
):
    if watermark is None:
        return conn.execute("""
            SELECT *
            FROM nasa_power_hourly
            WHERE site_tag=?
            ORDER BY
                downloaded_at_utc,
                timestamp_local
        """, (SITE_TAG,)).fetchall()

    return conn.execute("""
        SELECT *
        FROM nasa_power_hourly
        WHERE site_tag=?
          AND downloaded_at_utc > ?
        ORDER BY
            downloaded_at_utc,
            timestamp_local
    """, (
        SITE_TAG,
        watermark,
    )).fetchall()


def reconcile_source(
    conn,
    rows,
    columns,
    target_function,
    apply_changes,
):
    candidate_hours = 0
    hours_with_master = 0
    hours_without_master = 0
    mismatch_rows = 0
    updated_rows = 0

    for row in rows:
        candidate_hours += 1

        start_text, end_text = (
            master_hour_bounds(
                row["timestamp_local"]
            )
        )

        master_rows = count_master_rows(
            conn,
            start_text,
            end_text,
        )

        if master_rows == 0:
            hours_without_master += 1
            continue

        hours_with_master += 1

        target = target_function(row)

        mismatches = count_mismatches(
            conn,
            columns,
            target,
            start_text,
            end_text,
        )

        mismatch_rows += mismatches

        if (
            apply_changes
            and mismatches > 0
        ):
            updated_rows += apply_update(
                conn,
                columns,
                target,
                start_text,
                end_text,
            )

    return {
        "candidate_hours": candidate_hours,
        "hours_with_master": hours_with_master,
        "hours_without_master": hours_without_master,
        "mismatch_rows": mismatch_rows,
        "updated_rows": updated_rows,
    }


def main():
    parser = argparse.ArgumentParser()

    group = (
        parser.add_mutually_exclusive_group(
            required=True
        )
    )

    group.add_argument(
        "--dry-run",
        action="store_true",
    )

    group.add_argument(
        "--apply",
        action="store_true",
    )

    args = parser.parse_args()

    mode = (
        "APPLY"
        if args.apply
        else "DRY-RUN"
    )

    print(
        "ATMOSLINK atmospheric reconciler"
    )
    print("mode =", mode)
    print("database =", DB_FILE)
    print("state =", STATE_FILE)
    print("site_tag =", SITE_TAG)

    state = load_state()

    conn = sqlite3.connect(
        DB_FILE,
        timeout=60,
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA busy_timeout=60000"
    )

    era5_watermark = state.get(
        "era5_timestamp_local"
    )

    if era5_watermark is None:
        era5_watermark = (
            initial_era5_watermark(conn)
        )

    nasa_watermark = state.get(
        "nasa_downloaded_at_utc"
    )

    if nasa_watermark is None:
        nasa_watermark = (
            initial_nasa_watermark(conn)
        )

    print()
    print("===== ERA5 =====")
    print(
        "ERA5 processed watermark =",
        era5_watermark,
    )

    era5_rows = get_era5_candidates(
        conn,
        era5_watermark,
    )

    era5_result = reconcile_source(
        conn,
        era5_rows,
        ERA5_MASTER_COLUMNS,
        era5_target,
        args.apply,
    )

    for key, value in era5_result.items():
        print(
            f"ERA5 {key} = {value}"
        )

    print()
    print("===== NASA POWER =====")
    print(
        "NASA processed watermark =",
        nasa_watermark,
    )

    nasa_rows = get_nasa_candidates(
        conn,
        nasa_watermark,
    )

    nasa_invalid = sum(
        1
        for row in nasa_rows
        if not nasa_row_is_valid(row)
    )

    nasa_result = reconcile_source(
        conn,
        nasa_rows,
        NASA_MASTER_COLUMNS,
        nasa_target,
        args.apply,
    )

    for key, value in nasa_result.items():
        print(
            f"NASA {key} = {value}"
        )

    print(
        "NASA invalid QA/QC hours =",
        nasa_invalid,
    )

    if args.apply:
        conn.commit()

        new_state = dict(state)

        if era5_rows:
            new_state[
                "era5_timestamp_local"
            ] = max(
                row["timestamp_local"]
                for row in era5_rows
            )
        elif (
            "era5_timestamp_local"
            not in new_state
        ):
            new_state[
                "era5_timestamp_local"
            ] = era5_watermark

        if nasa_rows:
            new_state[
                "nasa_downloaded_at_utc"
            ] = max(
                row["downloaded_at_utc"]
                for row in nasa_rows
                if row["downloaded_at_utc"]
                is not None
            )
        elif (
            "nasa_downloaded_at_utc"
            not in new_state
        ):
            new_state[
                "nasa_downloaded_at_utc"
            ] = nasa_watermark

        save_state(new_state)

        print()
        print("COMMIT realizado.")
        print("Estado actualizado:")
        print(
            json.dumps(
                new_state,
                indent=2,
                sort_keys=True,
            )
        )

    else:
        conn.rollback()

        print()
        print(
            "DRY-RUN: no se modifico SQLite."
        )
        print(
            "DRY-RUN: no se modifico estado."
        )

    print()
    print(
        "quick_check =",
        conn.execute(
            "PRAGMA quick_check"
        ).fetchone()[0],
    )

    print(
        "master rows =",
        conn.execute("""
            SELECT COUNT(*)
            FROM master_observations
        """).fetchone()[0],
    )

    print(
        "master latest =",
        conn.execute("""
            SELECT MAX(master_timestamp_local)
            FROM master_observations
        """).fetchone()[0],
    )

    conn.close()


if __name__ == "__main__":
    main()
