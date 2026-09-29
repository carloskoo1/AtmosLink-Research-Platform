#!/usr/bin/env python3

import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DB = Path(
    "/home/ckoo/Proyectos/EstacionMeteorologica/"
    "SQLite/SJ01/weather_local.db"
)

SERVICE = "weather-logger-sj01.service"
STATION_ID = "SJ01"

STALE_SECONDS = 300
COOLDOWN_SECONDS = 600

STATE_FILE = Path(
    "/run/atmoslink-weather-watchdog-sj01.last-restart"
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
            f"base inexistente: {DB}"
        )

    con = sqlite3.connect(
        f"file:{DB}?mode=ro",
        uri=True,
        timeout=10,
    )

    try:
        row = con.execute(
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
        con.close()

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


def cooldown_remaining():
    if not STATE_FILE.exists():
        return 0

    try:
        previous = float(
            STATE_FILE.read_text().strip()
        )
    except (OSError, ValueError):
        return 0

    elapsed = max(
        time.time() - previous,
        0,
    )

    return max(
        int(COOLDOWN_SECONDS - elapsed),
        0,
    )


def restart_logger(reason):
    remaining = cooldown_remaining()

    if remaining > 0:
        log(
            "RECUPERACIÓN EN ESPERA | "
            f"motivo={reason} | "
            f"cooldown={remaining}s"
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
            "ERROR | reinicio terminó "
            f"con código {result.returncode}"
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
        "ERROR | logger no quedó activo"
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
            "base SJ01 sin registros"
        )

    age_seconds = max(
        int(
            (
                datetime.now(
                    timestamp.tzinfo
                )
                - timestamp
            ).total_seconds()
        ),
        0,
    )

    if not active:
        return restart_logger(
            "weather-logger-sj01 inactivo"
        )

    if age_seconds > STALE_SECONDS:
        return restart_logger(
            "sin mediciones SJ01 durante "
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
