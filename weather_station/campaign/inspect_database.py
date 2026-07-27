"""
CLI para inspeccionar bases SQLite de AtmosLink.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from weather_station.campaign.inspection import (
    inspect_sqlite_database,
    profile_to_dict,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspecciona tablas, columnas, fuentes y rangos "
            "temporales de una base SQLite de AtmosLink."
        )
    )

    parser.add_argument(
        "--database",
        default="SQLite/CU01/weather_local.db",
        help="Ruta de la base SQLite.",
    )

    parser.add_argument(
        "--output",
        default="reports/scientific_engine/"
        "CU01_database_profile.json",
        help="Archivo JSON de salida.",
    )

    return parser.parse_args()


def _print_summary(profile: dict[str, Any]) -> None:
    print()
    print("==================================================")
    print("RESUMEN DE LA BASE")
    print("==================================================")
    print(f"Base: {profile['database_path']}")
    print(
        "Tamaño: "
        f"{profile['database_size_bytes']} bytes"
    )
    print(
        "Versión SQLite: "
        f"{profile['sqlite_version']}"
    )
    print(
        "Cantidad de tablas: "
        f"{profile['table_count']}"
    )

    for table in profile["tables"]:
        print()
        print(f"TABLA: {table['name']}")
        print(f"  Filas: {table['row_count']}")
        print(
            "  Fuentes detectadas: "
            + (
                ", ".join(table["detected_sources"])
                if table["detected_sources"]
                else "no determinadas"
            )
        )
        print(
            "  Columna temporal: "
            f"{table['timestamp_column']}"
        )
        print(
            "  Inicio: "
            f"{table['timestamp_min']}"
        )
        print(
            "  Fin: "
            f"{table['timestamp_max']}"
        )
        print("  Columnas:")

        for column in table["columns"]:
            roles = (
                ", ".join(column["detected_roles"])
                if column["detected_roles"]
                else "-"
            )

            null_percentage = (
                f"{column['null_percentage']:.2f}%"
                if column["null_percentage"] is not None
                else "N/D"
            )

            print(
                f"    - {column['name']} "
                f"[{column['declared_type'] or 'SIN TIPO'}] "
                f"roles={roles} "
                f"nulos={null_percentage}"
            )


def main() -> None:
    args = parse_args()

    profile = inspect_sqlite_database(
        args.database
    )
    profile_dict = profile_to_dict(profile)

    output_path = Path(args.output)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            profile_dict,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    _print_summary(profile_dict)

    print()
    print(
        "Perfil JSON generado en: "
        f"{output_path}"
    )


if __name__ == "__main__":
    main()
