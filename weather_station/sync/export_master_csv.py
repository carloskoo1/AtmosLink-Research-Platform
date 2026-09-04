from __future__ import annotations

import csv
import os
import sqlite3
import time
from pathlib import Path


DB_FILE = Path(
    "SQLite/CU01/weather_local.db"
)

OUTPUT_FILE = Path(
    "Data/exports/master_observations.csv"
)


def main():
    started = time.monotonic()

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_file = OUTPUT_FILE.with_name(
        OUTPUT_FILE.name + ".tmp"
    )

    conn = sqlite3.connect(
        DB_FILE,
        timeout=60,
    )

    conn.execute(
        "PRAGMA busy_timeout=60000"
    )

    try:
        cursor = conn.execute("""
            SELECT *
            FROM master_observations
            ORDER BY master_timestamp_local
        """)

        columns = [
            item[0]
            for item in cursor.description
        ]

        rows_written = 0
        latest_timestamp = None

        timestamp_index = columns.index(
            "master_timestamp_local"
        )

        with temp_file.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as handle:

            writer = csv.writer(handle)

            writer.writerow(columns)

            while True:
                rows = cursor.fetchmany(2000)

                if not rows:
                    break

                writer.writerows(rows)

                rows_written += len(rows)

                latest_timestamp = (
                    rows[-1][timestamp_index]
                )

            handle.flush()
            os.fsync(handle.fileno())

        os.replace(
            temp_file,
            OUTPUT_FILE,
        )

        elapsed = (
            time.monotonic() - started
        )

        print(
            "ATMOSLINK master CSV export completed"
        )
        print(
            "database =",
            DB_FILE
        )
        print(
            "output =",
            OUTPUT_FILE
        )
        print(
            "rows =",
            rows_written
        )
        print(
            "latest =",
            latest_timestamp
        )
        print(
            "size_bytes =",
            OUTPUT_FILE.stat().st_size
        )
        print(
            "duration_seconds =",
            round(elapsed, 3)
        )

    finally:
        conn.close()

        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    main()
