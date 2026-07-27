"""
AtmosLink Research Platform
Scientific Propagation Pipeline database schema.

This module creates an independent database. It does not alter the
historical AtmosLink weather or master databases.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_VERSION = "1.0.0"


DDL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS propagation_schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS propagation_link_registry (
    link_id TEXT PRIMARY KEY,

    ap_station_id TEXT NOT NULL,
    sm_station_id TEXT NOT NULL,

    frequency_ghz REAL NOT NULL,
    path_distance_km REAL NOT NULL,

    tx_power_dbm REAL,
    ap_antenna_gain_dbi REAL,
    sm_antenna_gain_dbi REAL,
    ap_feeder_loss_db REAL NOT NULL DEFAULT 0.0,
    sm_feeder_loss_db REAL NOT NULL DEFAULT 0.0,

    polarization TEXT NOT NULL DEFAULT 'H',
    elevation_angle_deg REAL NOT NULL DEFAULT 0.0,

    itu_rain_recommendation TEXT NOT NULL DEFAULT 'ITU-R P.838-3',
    itu_gas_recommendation TEXT NOT NULL DEFAULT 'ITU-R P.676-12',

    valid_from_utc TEXT,
    valid_to_utc TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE',

    created_at_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS propagation_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    source_database TEXT NOT NULL,
    source_table TEXT NOT NULL,
    source_row_id TEXT,
    source_timestamp_utc TEXT NOT NULL,

    link_id TEXT NOT NULL,
    station_id TEXT,

    frequency_ghz REAL NOT NULL,
    path_distance_km REAL NOT NULL,

    temperature_c REAL,
    relative_humidity_pct REAL,
    pressure_hpa REAL,
    water_vapour_density_g_m3 REAL,

    precipitation_mm REAL,
    rain_interval_seconds REAL,
    rain_rate_mm_h REAL,
    rain_quality_flag TEXT,
    rain_quality_valid INTEGER,

    rain_specific_attenuation_db_km REAL,
    rain_uniform_path_attenuation_db REAL,

    gaseous_attenuation_db REAL,
    free_space_path_loss_db REAL,

    tx_power_dbm REAL,
    ap_antenna_gain_dbi REAL,
    sm_antenna_gain_dbi REAL,
    total_feeder_loss_db REAL,

    predicted_rssi_clear_sky_dbm REAL,
    predicted_rssi_uniform_rain_dbm REAL,
    observed_rssi_dbm REAL,

    residual_clear_sky_db REAL,
    residual_uniform_rain_db REAL,

    itu_rain_recommendation TEXT,
    itu_gas_recommendation TEXT,
    pipeline_version TEXT NOT NULL,

    quality_valid INTEGER NOT NULL,
    quality_flags TEXT,

    calculated_at_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (link_id)
        REFERENCES propagation_link_registry(link_id),

    UNIQUE (
        source_database,
        source_table,
        source_timestamp_utc,
        link_id
    )
);

CREATE INDEX IF NOT EXISTS idx_propagation_observations_time
ON propagation_observations(source_timestamp_utc);

CREATE INDEX IF NOT EXISTS idx_propagation_observations_link_time
ON propagation_observations(link_id, source_timestamp_utc);

CREATE INDEX IF NOT EXISTS idx_propagation_observations_quality
ON propagation_observations(quality_valid);

CREATE INDEX IF NOT EXISTS idx_propagation_observations_residual
ON propagation_observations(residual_clear_sky_db);
"""


def initialize_database(database_path: str | Path) -> Path:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as connection:
        connection.executescript(DDL)

        connection.execute(
            """
            INSERT INTO propagation_schema_metadata(key, value)
            VALUES ('schema_version', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (SCHEMA_VERSION,),
        )

        connection.commit()

    return path
