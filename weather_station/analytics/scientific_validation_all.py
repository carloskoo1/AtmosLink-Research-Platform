"""
AtmosLink Scientific Validation Orchestrator.

Ejecuta de forma independiente:
- CU01: motor científico histórico V2.
- SJ01: motor científico FIELD.

Un fallo en una estación no impide ejecutar la otra.
"""

import subprocess
import sys
from datetime import datetime, timezone


ENGINES = (
    (
        "CU01",
        "weather_station.analytics.scientific_validation",
    ),
    (
        "SJ01",
        "weather_station.analytics.scientific_validation_sj01",
    ),
)


def run_engine(station_id, module):
    print()
    print("=" * 80)
    print(
        f" ATMOSLINK VALIDATION {station_id}"
    )
    print("=" * 80)

    command = [
        sys.executable,
        "-u",
        "-m",
        module,
    ]

    try:
        result = subprocess.run(
            command,
            check=False,
        )

        if result.returncode == 0:
            print(
                f"[OK] {station_id} finalizó correctamente."
            )
            return True

        print(
            f"[ERROR] {station_id} terminó "
            f"con código {result.returncode}."
        )
        return False

    except Exception as exc:
        print(
            f"[ERROR] {station_id}: "
            f"{type(exc).__name__}: {exc}"
        )
        return False


def main():
    started = datetime.now(
        timezone.utc
    )

    print("=" * 80)
    print(
        " AtmosLink Scientific Validation Orchestrator"
    )
    print("=" * 80)
    print(
        "Inicio UTC:",
        started.isoformat(),
    )

    results = {}

    for station_id, module in ENGINES:
        results[station_id] = run_engine(
            station_id,
            module,
        )

    finished = datetime.now(
        timezone.utc
    )

    print()
    print("=" * 80)
    print(" RESUMEN")
    print("=" * 80)

    for station_id in results:
        print(
            f"{station_id}:",
            "OK"
            if results[station_id]
            else "ERROR",
        )

    print(
        "Fin UTC:",
        finished.isoformat(),
    )

    # El servicio falla solamente si fallaron
    # absolutamente todos los motores.
    #
    # Si uno funciona y otro falla, el journal
    # conservará el error pero la otra estación
    # seguirá siendo actualizada.
    if not any(results.values()):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
