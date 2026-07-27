"""
Inspección estructural de bases SQLite de AtmosLink.

El módulo identifica:

- tablas disponibles;
- columnas y tipos declarados;
- cantidad de registros;
- columnas temporales candidatas;
- rango temporal;
- columnas candidatas para estación local, ERA5, NASA POWER y Cambium;
- porcentaje aproximado de valores nulos.

No modifica la base de datos.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
import sqlite3
from typing import Any


TIMESTAMP_PATTERNS = (
    "timestamp",
    "datetime",
    "date_time",
    "fecha_hora",
    "fecha",
    "time",
    "created_at",
    "recorded_at",
    "measured_at",
)

SOURCE_PATTERNS: dict[str, tuple[str, ...]] = {
    "local": (
        "local",
        "sensor",
        "bme280",
        "station",
        "estacion",
        "temperature",
        "temperatura",
        "humidity",
        "humedad",
        "pressure",
        "presion",
        "rain",
        "lluvia",
    ),
    "era5": (
        "era5",
        "era5_land",
        "ecmwf",
    ),
    "nasa": (
        "nasa",
        "power",
        "nasa_power",
    ),
    "cambium": (
        "cambium",
        "rssi",
        "snr",
        "mcs",
        "throughput",
        "modulation",
        "radio",
        "link",
    ),
}


@dataclass(frozen=True, slots=True)
class ColumnProfile:
    name: str
    declared_type: str
    not_null: bool
    primary_key: bool
    null_count: int | None
    null_percentage: float | None
    detected_roles: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TableProfile:
    name: str
    row_count: int
    columns: tuple[ColumnProfile, ...]
    timestamp_column: str | None
    timestamp_min: str | None
    timestamp_max: str | None
    detected_sources: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DatabaseProfile:
    database_path: str
    database_size_bytes: int
    sqlite_version: str
    table_count: int
    tables: tuple[TableProfile, ...]


def _quote_identifier(identifier: str) -> str:
    """Protege identificadores SQLite mediante comillas dobles."""
    return '"' + identifier.replace('"', '""') + '"'


def _normalized_name(value: str) -> str:
    value = value.casefold()
    return re.sub(r"[^a-z0-9áéíóúüñ]+", "_", value).strip("_")


def _detect_roles(column_name: str) -> tuple[str, ...]:
    normalized = _normalized_name(column_name)
    roles: list[str] = []

    if any(pattern in normalized for pattern in TIMESTAMP_PATTERNS):
        roles.append("timestamp")

    for source, patterns in SOURCE_PATTERNS.items():
        if any(pattern in normalized for pattern in patterns):
            roles.append(source)

    return tuple(dict.fromkeys(roles))


def _select_timestamp_column(
    column_names: list[str],
) -> str | None:
    normalized_columns = {
        column: _normalized_name(column)
        for column in column_names
    }

    for pattern in TIMESTAMP_PATTERNS:
        for original, normalized in normalized_columns.items():
            if normalized == pattern:
                return original

    for pattern in TIMESTAMP_PATTERNS:
        for original, normalized in normalized_columns.items():
            if pattern in normalized:
                return original

    return None


def _safe_scalar(
    connection: sqlite3.Connection,
    query: str,
) -> Any:
    try:
        row = connection.execute(query).fetchone()
    except sqlite3.Error:
        return None

    if row is None:
        return None

    return row[0]


def inspect_sqlite_database(
    database_path: str | Path,
) -> DatabaseProfile:
    """
    Inspecciona una base SQLite sin modificarla.

    Parameters
    ----------
    database_path:
        Ruta de la base SQLite.

    Returns
    -------
    DatabaseProfile
        Perfil estructural y temporal de la base.
    """

    path = Path(database_path)

    if not path.exists():
        raise FileNotFoundError(
            f"No existe la base SQLite: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"La ruta no corresponde a un archivo: {path}"
        )

    uri = f"file:{path.resolve()}?mode=ro"

    with sqlite3.connect(uri, uri=True) as connection:
        sqlite_version = str(
            connection.execute(
                "SELECT sqlite_version()"
            ).fetchone()[0]
        )

        table_rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        table_profiles: list[TableProfile] = []

        for (table_name,) in table_rows:
            quoted_table = _quote_identifier(table_name)

            pragma_rows = connection.execute(
                f"PRAGMA table_info({quoted_table})"
            ).fetchall()

            row_count_value = _safe_scalar(
                connection,
                f"SELECT COUNT(*) FROM {quoted_table}",
            )
            row_count = int(row_count_value or 0)

            column_names = [
                str(row[1])
                for row in pragma_rows
            ]

            timestamp_column = _select_timestamp_column(
                column_names
            )

            timestamp_min: str | None = None
            timestamp_max: str | None = None

            if timestamp_column:
                quoted_timestamp = _quote_identifier(
                    timestamp_column
                )

                temporal_row = connection.execute(
                    f"""
                    SELECT
                        MIN({quoted_timestamp}),
                        MAX({quoted_timestamp})
                    FROM {quoted_table}
                    WHERE {quoted_timestamp} IS NOT NULL
                    """
                ).fetchone()

                if temporal_row:
                    if temporal_row[0] is not None:
                        timestamp_min = str(temporal_row[0])
                    if temporal_row[1] is not None:
                        timestamp_max = str(temporal_row[1])

            columns: list[ColumnProfile] = []
            table_sources: list[str] = []

            for pragma_row in pragma_rows:
                column_name = str(pragma_row[1])
                declared_type = str(pragma_row[2] or "")
                not_null = bool(pragma_row[3])
                primary_key = bool(pragma_row[5])

                quoted_column = _quote_identifier(
                    column_name
                )

                null_count_value = _safe_scalar(
                    connection,
                    f"""
                    SELECT COUNT(*)
                    FROM {quoted_table}
                    WHERE {quoted_column} IS NULL
                    """,
                )

                null_count = (
                    int(null_count_value)
                    if null_count_value is not None
                    else None
                )

                if (
                    null_count is not None
                    and row_count > 0
                ):
                    null_percentage = (
                        null_count / row_count
                    ) * 100.0
                elif row_count == 0:
                    null_percentage = 0.0
                else:
                    null_percentage = None

                roles = _detect_roles(column_name)

                for role in roles:
                    if role != "timestamp":
                        table_sources.append(role)

                columns.append(
                    ColumnProfile(
                        name=column_name,
                        declared_type=declared_type,
                        not_null=not_null,
                        primary_key=primary_key,
                        null_count=null_count,
                        null_percentage=null_percentage,
                        detected_roles=roles,
                    )
                )

            normalized_table_name = _normalized_name(
                table_name
            )

            for source, patterns in SOURCE_PATTERNS.items():
                if any(
                    pattern in normalized_table_name
                    for pattern in patterns
                ):
                    table_sources.append(source)

            table_profiles.append(
                TableProfile(
                    name=str(table_name),
                    row_count=row_count,
                    columns=tuple(columns),
                    timestamp_column=timestamp_column,
                    timestamp_min=timestamp_min,
                    timestamp_max=timestamp_max,
                    detected_sources=tuple(
                        dict.fromkeys(table_sources)
                    ),
                )
            )

    return DatabaseProfile(
        database_path=str(path),
        database_size_bytes=path.stat().st_size,
        sqlite_version=sqlite_version,
        table_count=len(table_profiles),
        tables=tuple(table_profiles),
    )


def profile_to_dict(
    profile: DatabaseProfile,
) -> dict[str, Any]:
    """Convierte el perfil completo en un diccionario serializable."""
    return asdict(profile)
