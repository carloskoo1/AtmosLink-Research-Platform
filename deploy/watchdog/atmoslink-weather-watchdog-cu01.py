#!/usr/bin/env python3

import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DB = Path(
    "/home/carlos/Proyectos/EstacionMeteorologica/"
    "SQLite/CU01/weather_local.db"
)

SERVICE = "weather-logger.service"
STATION_ID = "CU01"

STALE_SECONDS = 300
COOLDOWN_SECONDS = 600

STATE_FILE = Path(
    "/run/atmoslink-weather-watchdog.last-restart"
)

LOCAL_ZONE = ZoneInfo("America/Lima")


def log(message):
    stamp = datetime.now(
        LOCAL_ZONE
    ).isoformat(timespec="seconds")

    print(
        f"{stamp} | {message}",
        flush=True,
    )


def service_active():
    result = subprocess.run(
        [
            "systemctl",
            "is-active",
            "--quiet",
            SERVICE,
        ],
        check=False,
    )

    return result.returncode == 0


def latest_timestamp():
    if not DB.exists():
        raise RuntimeError(
            f"base de datos inexistente: {DB}"
        )

    connection = sqlite3.connect(
        f"file:{DB}?mode=ro",
        uri=True,
        timeout=10,
    )

    try:
        row = connection.execute(
            """
            SELECT timestamp_local
            FROM weather_local
            WHERE station_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (STATION_ID,),
        ).fetchone()
    finally:
        connection.close()

    if not row or not row[0]:
        return None

    value = str(row[0]).strip()

    if value.endswith("Z"):
        value = value[:-1] + "+00:00"

    timestamp = datetime.fromisoformat(
        value
    )

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(
            tzinfo=LOCAL_ZONE
        )

    return timestamp


def seconds_since_last_restart():
    if not STATE_FILE.exists():
        return None

    try:
        previous = float(
            STATE_FILE.read_text().strip()
        )
    except (OSError, ValueError):
        return None

    return max(
        time.time() - previous,
        0,
    )


def restart_logger(reason):
    elapsed = seconds_since_last_restart()

    if (
        elapsed is not None
        and elapsed < COOLDOWN_SECONDS
    ):
        remaining = int(
            COOLDOWN_SECONDS - elapsed
        )

        log(
            "RECUPERACIÓN EN ESPERA | "
            f"motivo={reason} | "
            f"cooldown_restante={remaining}s"
        )
        return 0

    log(
        "RECUPERACIÓN AUTOMÁTICA | "
        f"motivo={reason} | "
        f"reiniciando={SERVICE}"
    )

    result = subprocess.run(
        [
            "systemctl",
            "restart",
            SERVICE,
        ],
        check=False,
    )

    if result.returncode != 0:
        log(
            "ERROR | systemctl restart "
            f"terminó con código "
            f"{result.returncode}"
        )
        return 1

    STATE_FILE.write_text(
        str(time.time())
    )

    time.sleep(5)

    if service_active():
        log(
            "RECUPERACIÓN EJECUTADA | "
            f"{SERVICE}=active"
        )
        return 0

    log(
        "ERROR | servicio no quedó activo "
        "después del reinicio"
    )
    return 1


def main():
    active = service_active()

    try:
        timestamp = latest_timestamp()
    except Exception as exc:
        log(
            "ERROR DE COMPROBACIÓN | "
            f"{type(exc).__name__}: {exc}"
        )
        return 1

    if timestamp is None:
        return restart_logger(
            "base sin registros de CU01"
        )

    now = datetime.now(
        timestamp.tzinfo
    )

    age_seconds = max(
        int(
            (
                now - timestamp
            ).total_seconds()
        ),
        0,
    )

    if not active:
        return restart_logger(
            "weather-logger inactivo"
        )

    if age_seconds > STALE_SECONDS:
        return restart_logger(
            "sin mediciones nuevas durante "
            f"{age_seconds}s; "
            f"último={timestamp.isoformat()}"
        )

    log(
        "OK | "
        f"servicio=active | "
        f"edad_medición={age_seconds}s | "
        f"último={timestamp.isoformat()}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
