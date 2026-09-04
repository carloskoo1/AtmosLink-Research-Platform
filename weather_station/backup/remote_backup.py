import fcntl
import json
import shutil
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from weather_station.config.station_manager import get_station_context


BASE_DIR = Path(__file__).resolve().parents[2]
LOGS_DIR = BASE_DIR / "logs"
RUNTIME_DIR = BASE_DIR / "runtime"
BACKUP_LOCK = RUNTIME_DIR / "remote_backup.lock"
BACKUP_LOG = LOGS_DIR / "backup.log"

REMOTE_TARGETS = (
    {
        "key": "primary",
        "name": "atmoslink_drive",
        "root": "AtmosLink_Backups",
        "description": "Google Drive principal",
    },
    {
        "key": "unc",
        "name": "atmoslink_drive_unc",
        "root": "AtmosLink_Backups_UNC",
        "description": "Google Drive UNC",
    },
)

PLATFORM_NAME = "AtmosLink Research Platform"
PLATFORM_VERSION = "1.0-lts"
MAX_REMOTE_SECONDS = 600


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(message: str) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    line = f"{now_utc()} | {message}"
    print(line)

    with BACKUP_LOG.open("a", encoding="utf-8") as file:
        file.write(line + "\n")


def run_command(
    command: list[str],
    timeout: int,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def rclone_available() -> bool:
    return shutil.which("rclone") is not None


def configured_remotes() -> set[str]:
    result = run_command(
        ["rclone", "listremotes"],
        timeout=30,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "No se pudieron consultar los remotos de rclone: "
            f"{result.stderr.strip()}"
        )

    return {
        line.strip().removesuffix(":")
        for line in result.stdout.splitlines()
        if line.strip()
    }


def get_latest_local_backup(
    station_id: str,
) -> Optional[Path]:
    backup_dir = BASE_DIR / "Backups" / station_id

    if not backup_dir.exists():
        return None

    backups = sorted(
        backup_dir.glob(f"backup_{station_id}_*.zip"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    return backups[0] if backups else None


def create_local_backup() -> bool:
    command = [
        str(BASE_DIR / "venv" / "bin" / "python"),
        "-m",
        "weather_station.backup.local_backup",
    ]

    result = run_command(command, timeout=600)

    if result.returncode != 0:
        log("Error creando backup local consistente")

        if result.stdout.strip():
            log(result.stdout.strip())

        if result.stderr.strip():
            log(result.stderr.strip())

        return False

    log("Backup local consistente creado correctamente")
    return True


def build_remote_directory(
    target: dict[str, str],
    station_id: str,
    deployment_mode: str,
) -> str:
    return (
        f"{target['name']}:{target['root']}/"
        f"{station_id}/{deployment_mode}"
    )


def upload_backup(
    backup_path: Path,
    remote_directory: str,
    description: str,
) -> bool:
    remote_file = f"{remote_directory}/{backup_path.name}"

    command = [
        "rclone",
        "copyto",
        str(backup_path),
        remote_file,
        "--transfers",
        "1",
        "--checkers",
        "2",
        "--retries",
        "3",
        "--low-level-retries",
        "10",
        "--contimeout",
        "15s",
        "--timeout",
        "5m",
    ]

    result = run_command(
        command,
        timeout=MAX_REMOTE_SECONDS,
    )

    if result.returncode != 0:
        log(
            f"Error subiendo backup a {description}: "
            f"{remote_file}"
        )

        if result.stderr.strip():
            log(result.stderr.strip())

        return False

    log(
        f"Backup subido correctamente a {description}: "
        f"{remote_file}"
    )
    return True


def verify_remote_backup(
    backup_path: Path,
    remote_directory: str,
    description: str,
) -> bool:
    remote_file = f"{remote_directory}/{backup_path.name}"

    size_result = run_command(
        [
            "rclone",
            "size",
            remote_file,
            "--json",
        ],
        timeout=120,
    )

    if size_result.returncode != 0:
        log(
            f"No se pudo consultar el archivo en {description}: "
            f"{remote_file}"
        )

        if size_result.stderr.strip():
            log(size_result.stderr.strip())

        return False

    try:
        remote_info = json.loads(size_result.stdout)
        remote_count = int(remote_info.get("count", 0))
        remote_bytes = int(remote_info.get("bytes", -1))
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        log(
            f"Respuesta inválida de rclone size "
            f"en {description}: {error}"
        )
        return False

    local_bytes = backup_path.stat().st_size

    if remote_count != 1:
        log(
            f"Verificación fallida en {description}: "
            f"count remoto={remote_count}"
        )
        return False

    if remote_bytes != local_bytes:
        log(
            f"Verificación por tamaño fallida en {description}: "
            f"local={local_bytes}, remoto={remote_bytes}"
        )
        return False

    check_result = run_command(
        [
            "rclone",
            "check",
            str(backup_path.parent),
            remote_directory,
            "--include",
            backup_path.name,
            "--one-way",
            "--size-only",
        ],
        timeout=300,
    )

    if check_result.returncode != 0:
        log(f"rclone check encontró diferencias en {description}")

        if check_result.stdout.strip():
            log(check_result.stdout.strip())

        if check_result.stderr.strip():
            log(check_result.stderr.strip())

        return False

    log(
        f"Verificación correcta en {description}: "
        f"{backup_path.name} ({local_bytes} bytes)"
    )
    return True


def write_runtime_status(
    backup_path: Optional[Path],
    station_id: str,
    deployment_mode: str,
    destinations: dict[str, dict[str, Any]],
    error: Optional[str] = None,
) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    expected_keys = {
        str(target["key"])
        for target in REMOTE_TARGETS
    }

    uploaded = (
        set(destinations) == expected_keys
        and all(
            bool(result.get("uploaded"))
            for result in destinations.values()
        )
    )

    verified = (
        set(destinations) == expected_keys
        and all(
            bool(result.get("verified"))
            for result in destinations.values()
        )
    )

    primary_remote = destinations.get(
        "primary",
        {},
    ).get("remote")

    status = {
        "platform": PLATFORM_NAME,
        "platform_version": PLATFORM_VERSION,
        "updated_at": now_utc(),
        "hostname": socket.gethostname(),
        "station_id": station_id,
        "deployment_mode": deployment_mode,
        "last_backup_file": (
            str(backup_path)
            if backup_path
            else None
        ),
        "last_backup_name": (
            backup_path.name
            if backup_path
            else None
        ),
        "local_size_bytes": (
            backup_path.stat().st_size
            if backup_path and backup_path.exists()
            else None
        ),
        "uploaded": uploaded,
        "verified": verified,
        "remote": primary_remote,
        "destinations": destinations,
        "required_destinations": len(REMOTE_TARGETS),
        "verified_destinations": sum(
            1
            for result in destinations.values()
            if result.get("verified")
        ),
        "error": error,
    }

    output = RUNTIME_DIR / "backup_status.json"
    temporary = output.with_suffix(".json.tmp")

    temporary.write_text(
        json.dumps(
            status,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    temporary.replace(output)


def acquire_backup_lock():
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    lock_file = BACKUP_LOCK.open(
        "a+",
        encoding="utf-8",
    )

    try:
        fcntl.flock(
            lock_file.fileno(),
            fcntl.LOCK_EX | fcntl.LOCK_NB,
        )
    except BlockingIOError:
        lock_file.close()
        return None

    lock_file.seek(0)
    lock_file.truncate()
    lock_file.write(str(__import__("os").getpid()))
    lock_file.flush()

    return lock_file


def main() -> int:
    lock_file = acquire_backup_lock()

    if lock_file is None:
        log(
            "Backup remoto omitido: "
            "ya existe otra ejecución activa"
        )
        return 0

    station_id = "UNKNOWN"
    deployment_mode = "field"
    backup_path: Optional[Path] = None
    destinations: dict[str, dict[str, Any]] = {}

    try:
        ctx = get_station_context()
        station_id = str(ctx["station_id"])
        deployment_mode = str(
            ctx.get("deployment_mode", "field")
        ).lower()

        if not rclone_available():
            raise RuntimeError("rclone no está instalado")

        available_remotes = configured_remotes()

        log(
            "Generando un único backup local consistente "
            "para ambos destinos remotos"
        )

        if not create_local_backup():
            raise RuntimeError(
                "No se pudo crear el backup local consistente"
            )

        backup_path = get_latest_local_backup(station_id)

        if backup_path is None:
            raise RuntimeError(
                "No se encontró el backup local recién generado"
            )

        for target in REMOTE_TARGETS:
            key = str(target["key"])
            name = str(target["name"])
            description = str(target["description"])
            remote_directory = build_remote_directory(
                target=target,
                station_id=station_id,
                deployment_mode=deployment_mode,
            )

            result: dict[str, Any] = {
                "description": description,
                "remote_name": name,
                "remote": remote_directory,
                "uploaded": False,
                "verified": False,
                "error": None,
            }

            if name not in available_remotes:
                message = (
                    f"No existe el remoto rclone {name}:"
                )
                log(message)
                result["error"] = message
                destinations[key] = result
                continue

            uploaded = upload_backup(
                backup_path=backup_path,
                remote_directory=remote_directory,
                description=description,
            )

            result["uploaded"] = uploaded

            if uploaded:
                verified = verify_remote_backup(
                    backup_path=backup_path,
                    remote_directory=remote_directory,
                    description=description,
                )
                result["verified"] = verified

                if not verified:
                    result["error"] = (
                        "La copia remota no superó "
                        "la verificación"
                    )
            else:
                result["error"] = (
                    "La copia remota no pudo cargarse"
                )

            destinations[key] = result

        all_uploaded = (
            len(destinations) == len(REMOTE_TARGETS)
            and all(
                result["uploaded"]
                for result in destinations.values()
            )
        )

        all_verified = (
            len(destinations) == len(REMOTE_TARGETS)
            and all(
                result["verified"]
                for result in destinations.values()
            )
        )

        write_runtime_status(
            backup_path=backup_path,
            station_id=station_id,
            deployment_mode=deployment_mode,
            destinations=destinations,
        )

        if not all_uploaded or not all_verified:
            log(
                "Backup remoto dual finalizado con error "
                f"| uploaded={all_uploaded} "
                f"| verified={all_verified}"
            )
            return 1

        log(
            "Backup remoto dual finalizado correctamente "
            f"| station={station_id} "
            f"| file={backup_path.name} "
            f"| destinations={len(destinations)}"
        )
        return 0

    except Exception as error:
        log(f"Error general en backup remoto dual: {error}")

        write_runtime_status(
            backup_path=backup_path,
            station_id=station_id,
            deployment_mode=deployment_mode,
            destinations=destinations,
            error=str(error),
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
