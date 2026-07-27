"""
Column discovery for AtmosLink scientific source tables.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


COLUMN_ALIASES = {
    "timestamp_utc": (
        "weather_timestamp_utc",
        "timestamp_utc",
        "radio_timestamp_utc",
    ),
    "station_id": (
        "station_id",
        "local_station_id",
    ),
    "temperature_c": (
        "local_temp_avg_c",
        "local_temperature_c",
        "temperature_c",
        "temp_c",
    ),
    "relative_humidity_pct": (
        "local_hum_avg_pct",
        "local_humidity_pct",
        "relative_humidity_pct",
        "humidity_pct",
        "humidity",
    ),
    "pressure_hpa": (
        "local_press_hpa",
        "local_pressure_hpa",
        "pressure_hpa",
        "pressure",
    ),
    "rain_1min_mm": (
        "local_rain_1min_mm",
        "rain_1min_mm",
    ),
    "pulses_delta": (
        "local_pulses_delta",
        "pulses_delta",
    ),
    "rain_ok": (
        "local_rain_ok",
        "rain_ok",
    ),
    "observed_rssi_dbm": (
        "radio_sta_dl_rssi",
        "radio_sta_ul_rssi",
        "radio_rssi_c0p",
        "radio_rssi_c1p",
        "radio_rssi_c0e",
        "radio_rssi_c1e",
        "radio_rssi_dbm",
        "rssi_dbm",
        "rssi",
        "downlink_rssi_dbm",
        "uplink_rssi_dbm",
    ),
}


@dataclass(frozen=True)
class SourceMapping:
    timestamp_utc: str | None
    station_id: str | None
    temperature_c: str | None
    relative_humidity_pct: str | None
    pressure_hpa: str | None
    rain_1min_mm: str | None
    pulses_delta: str | None
    rain_ok: str | None
    observed_rssi_dbm: str | None


def table_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> set[str]:
    rows = connection.execute(
        f'PRAGMA table_info("{table_name}")'
    ).fetchall()

    return {str(row[1]) for row in rows}


def first_existing(
    existing_columns: set[str],
    aliases: tuple[str, ...],
) -> str | None:
    for alias in aliases:
        if alias in existing_columns:
            return alias

    return None


def discover_mapping(
    connection: sqlite3.Connection,
    table_name: str,
) -> SourceMapping:
    columns = table_columns(connection, table_name)

    resolved = {
        logical_name: first_existing(columns, aliases)
        for logical_name, aliases in COLUMN_ALIASES.items()
    }

    return SourceMapping(**resolved)
