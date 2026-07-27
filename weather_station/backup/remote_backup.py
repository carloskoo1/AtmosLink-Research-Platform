import fcntl
import json
import shutil
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from weather_station.config.station_manager import get_station_context


BASE_DIR = Path(__file__).resolve().parents[2]
LOGS_DIR = BASE_DIR / "logs"
RUNTIME_DIR = BASE_DIR / "runtime"
BACKUP_LOCK = RUNTIME_DIR / "remote_backup.lock"
BACKUP_LOG = LOGS_DIR / "backup.log"

REMOTE_NAME = "atmoslink_drive"
REMOTE_ROOT = "AtmosLink_Backups"
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


def run_command(command: list[str], timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def rclone_available() -> bool:
    return shutil.which("rclone") is not None


def remote_exists() -> bool:
    result = run_command(
        ["rclone", "listremotes"],
        timeout=30,
    )

    if result.returncode != 0:
        log(f"Error ejecutando rclone listremotes: {result.stderr.strip()}")
        return False

    remotes = {line.strip() for line in result.stdout.splitlines()}
    return f"{REMOTE_NAME}:" in remotes


def get_latest_local_backup(station_id: str) -> Optional[Path]:
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
        log(result.stdout.strip())
        log(result.stderr.strip())
        return False

    log("Backup local consistente creado correctamente")
    return True


def upload_backup(
    backup_path: Path,
    station_id: str,
    deployment_mode: str,
) -> tuple[bool, str]:
    remote_directory = (
        f"{REMOTE_NAME}:{REMOTE_ROOT}/"
        f"{station_id}/{deployment_mode}"
    )

    command = [
        "rclone",
        "copyto",
        str(backup_path),
        f"{remote_directory}/{backup_path.name}",
        "--transfers",
        "1",
        "--checkers",
        "2",
        "--retries",
        "3",
        "--low-level-retries",
        "10",
    ]

    result = run_command(command, timeout=MAX_REMOTE_SECONDS)

    if result.returncode != 0:
        log("Error subiendo backup a Google Drive")
        log(result.stderr.strip())
        return False, remote_directory

    log(
        "Backup subido correctamente: "
        f"{remote_directory}/{backup_path.name}"
    )
    return True, remote_directory


def verify_remote_backup(
    backup_path: Path,
    remote_directory: str,
) -> bool:
    remote_file = f"{remote_directory}/{backup_path.name}"

    size_result = run_command(
        ["rclone", "size", remote_file, "--json"],
        timeout=120,
    )

    if size_result.returncode != 0:
        log(f"No se pudo consultar el archivo remoto: {remote_file}")
        log(size_result.stderr.strip())
        return False

    try:
        remote_info = json.loads(size_result.stdout)
        remote_count = int(remote_info.get("count", 0))
        remote_bytes = int(remote_info.get("bytes", -1))
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        log(f"Respuesta inválida de rclone size: {error}")
        return False

    local_bytes = backup_path.stat().st_size

    if remote_count != 1:
        log(f"Verificación fallida: count remoto={remote_count}")
        return False

    if remote_bytes != local_bytes:
        log(
            "Verificación fallida por tamaño: "
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
        log("rclone check encontró diferencias")
        log(check_result.stdout.strip())
        log(check_result.stderr.strip())
        return False

    log(
        "Verificación remota correcta: "
        f"{backup_path.name} ({local_bytes} bytes)"
    )
    return True


def write_runtime_status(
    backup_path: Optional[Path],
    station_id: str,
    deployment_mode: str,
    uploaded: bool,
    verified: bool,
    remote_directory: str,
    error: Optional[str] = None,
) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    status = {
        "platform": PLATFORM_NAME,
        "platform_version": PLATFORM_VERSION,
        "updated_at": now_utc(),
        "hostname": socket.gethostname(),
        "station_id": station_id,
        "deployment_mode": deployment_mode,
        "last_backup_file": str(backup_path) if backup_path else None,
        "last_backup_name": backup_path.name if backup_path else None,
        "local_size_bytes": (
            backup_path.stat().st_size
            if backup_path and backup_path.exists()
            else None
        ),
        "uploaded": uploaded,
        "verified": verified,
        "remote": remote_directory,
        "error": error,
    }

    output = RUNTIME_DIR / "backup_status.json"
    output.write_text(
        json.dumps(status, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )


def acquire_backup_lock():
    """Obtiene un bloqueo exclusivo para impedir backups simultáneos."""
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    lock_file = BACKUP_LOCK.open("a+", encoding="utf-8")

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

    ctx = get_station_context()

    station_id = str(ctx["station_id"])
    deployment_mode = str(
        ctx.get("deployment_mode", "field")
    ).lower()

    remote_directory = (
        f"{REMOTE_NAME}:{REMOTE_ROOT}/"
        f"{station_id}/{deployment_mode}"
    )

    backup_path: Optional[Path] = None

    try:
        if not rclone_available():
            raise RuntimeError("rclone no está instalado")

        if not remote_exists():
            raise RuntimeError(
                f"No existe el remoto rclone {REMOTE_NAME}:"
            )

        log(
            "Generando backup local consistente antes de la subida remota"
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

        uploaded, remote_directory = upload_backup(
            backup_path=backup_path,
            station_id=station_id,
            deployment_mode=deployment_mode,
        )

        verified = (
            verify_remote_backup(
                backup_path=backup_path,
                remote_directory=remote_directory,
            )
            if uploaded
            else False
        )

        write_runtime_status(
            backup_path=backup_path,
            station_id=station_id,
            deployment_mode=deployment_mode,
            uploaded=uploaded,
            verified=verified,
            remote_directory=remote_directory,
        )

        if not uploaded or not verified:
            log(
                "Backup remoto finalizado con error "
                f"| uploaded={uploaded} | verified={verified}"
            )
            return 1

        log(
            "Backup remoto finalizado correctamente "
            f"| station={station_id} "
            f"| file={backup_path.name}"
        )
        return 0

    except Exception as error:
        log(f"Error general en backup remoto: {error}")

        write_runtime_status(
            backup_path=backup_path,
            station_id=station_id,
            deployment_mode=deployment_mode,
            uploaded=False,
            verified=False,
            remote_directory=remote_directory,
            error=str(error),
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
