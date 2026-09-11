from __future__ import annotations

import random
import sqlite3
import subprocess
import time
from datetime import datetime
from pathlib import Path

PYTHON = "/home/carlos/Proyectos/EstacionMeteorologica/venv/bin/python"
MODULE = "weather_station.telemetry.active_throughput_6g"

DB = "SQLite/CU01/weather_local.db"
CSV = "Data/exports/active_throughput_6g.csv"

BLOCKS = 10
PAUSE_BETWEEN_RUNS = 45

CONFIGS = [
    {"duration": 8, "omit": 1, "parallel": 1},
    {"duration": 15, "omit": 2, "parallel": 1},
    {"duration": 30, "omit": 2, "parallel": 1},
]


def max_id() -> int:
    con = sqlite3.connect(DB)
    value = con.execute(
        "SELECT COALESCE(MAX(id), 0) FROM active_throughput_6g"
    ).fetchone()[0]
    con.close()
    return int(value)


start_id = max_id()

print("======================================")
print(" AtmosLink PILOT iperf duration test")
print("======================================")
print("Inicio:", datetime.now().astimezone().isoformat())
print("ID inicial:", start_id)
print("Bloques:", BLOCKS)
print()

rng = random.Random(20260911)

for block in range(1, BLOCKS + 1):
    order = CONFIGS.copy()
    rng.shuffle(order)

    print(f"\n===== BLOQUE {block}/{BLOCKS} =====")
    print("Orden:", [c["duration"] for c in order])

    for cfg in order:
        duration = cfg["duration"]
        omit = cfg["omit"]
        parallel = cfg["parallel"]

        print(
            f"\n--- duration={duration}s "
            f"omit={omit}s parallel={parallel} ---",
            flush=True,
        )

        cmd = [
            PYTHON,
            "-m",
            MODULE,
            "--database",
            DB,
            "--output-csv",
            CSV,
            "--direction",
            "BOTH",
            "--duration",
            str(duration),
            "--omit",
            str(omit),
            "--parallel",
            str(parallel),
        ]

        result = subprocess.run(cmd)

        if result.returncode != 0:
            print(
                f"ADVERTENCIA: prueba terminó con código "
                f"{result.returncode}"
            )

        time.sleep(PAUSE_BETWEEN_RUNS)

end_id = max_id()

print("\n======================================")
print(" PILOTO TERMINADO")
print("======================================")
print("ID inicial exclusivo:", start_id)
print("ID final:", end_id)
print("Filas generadas:", end_id - start_id)
print("Fin:", datetime.now().astimezone().isoformat())
