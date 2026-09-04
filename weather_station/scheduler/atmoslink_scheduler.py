#!/usr/bin/env python3
"""
AtmosLink Central Scheduler

Scheduler configurable mediante YAML con:
- registro persistente del estado de tareas;
- recuperación del último tiempo de ejecución tras reinicios;
- timeout global y timeout individual por tarea.
"""

import time
import json
import yaml
import logging
import subprocess
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_FILE = BASE_DIR / "config" / "scheduler.yaml"

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

RUNTIME_DIR = BASE_DIR / "runtime"
RUNTIME_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "atmoslink_scheduler.log"
REGISTRY_FILE = RUNTIME_DIR / "task_registry.json"


logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def load_config():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"No existe el archivo de configuración: {CONFIG_FILE}"
        )

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_registry():
    """
    Recupera el estado persistido de la ejecución anterior.

    Un registry inexistente, vacío o corrupto no impide iniciar
    AtmosLink: en ese caso se parte de un estado nuevo.
    """
    if not REGISTRY_FILE.exists():
        return {}

    try:
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        tasks = data.get("tasks", {})

        if isinstance(tasks, dict):
            return tasks

    except Exception as e:
        logging.warning(
            f"No se pudo recuperar task_registry.json: {e}"
        )

    return {}


def save_registry(tasks):
    registry = {
        "updated_at": now_iso(),
        "tasks": {}
    }

    for name, task in tasks.items():
        registry["tasks"][name] = {
            "enabled": task.get("enabled", False),
            "status": task.get("status", "unknown"),
            "interval_seconds": task.get("interval_seconds"),
            "timeout_seconds": task.get("timeout_seconds"),
            "last_run": task.get("last_run_iso"),
            "last_start": task.get("last_start"),
            "last_end": task.get("last_end"),
            "last_success": task.get("last_success"),
            "last_duration_seconds": task.get(
                "last_duration_seconds"
            ),
            "failures": task.get("failures", 0),
            "last_error": task.get("last_error")
        }

    tmp_file = REGISTRY_FILE.with_suffix(".json.tmp")

    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(
            registry,
            f,
            indent=4,
            ensure_ascii=False
        )
        f.flush()

    tmp_file.replace(REGISTRY_FILE)


def parse_datetime(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def should_run(task):
    if not task.get("enabled", False):
        return False

    if task.get("last_run") is None:
        return True

    interval = task.get("interval_seconds", 60)

    elapsed = datetime.now() - task["last_run"]

    return elapsed.total_seconds() >= interval


def run_task(
    task_name,
    task,
    default_timeout_seconds,
    tasks
):
    command = task.get("command")

    if not command:
        task["status"] = "failed"
        task["last_error"] = "Task without command"
        save_registry(tasks)

        logging.error(
            f"Task without command: {task_name}"
        )
        return

    task_timeout_seconds = task.get(
        "timeout_seconds",
        default_timeout_seconds
    )

    try:
        task_timeout_seconds = int(
            task_timeout_seconds
        )
    except Exception:
        task_timeout_seconds = int(
            default_timeout_seconds
        )

    logging.info(
        f"Starting task: {task_name} "
        f"(timeout={task_timeout_seconds}s)"
    )

    start_time = datetime.now()

    task["status"] = "running"
    task["last_start"] = start_time.isoformat(
        timespec="seconds"
    )
    task["last_error"] = None

    save_registry(tasks)

    try:
        result = subprocess.run(
            command,
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=task_timeout_seconds
        )

        end_time = datetime.now()

        duration = (
            end_time - start_time
        ).total_seconds()

        task["last_duration_seconds"] = round(
            duration,
            3
        )

        if result.returncode == 0:
            task["status"] = "completed"

            task["last_success"] = (
                end_time.isoformat(
                    timespec="seconds"
                )
            )

            task["failures"] = 0
            task["last_error"] = None

            logging.info(
                f"Task completed: {task_name}"
            )

            if result.stdout.strip():
                logging.info(
                    f"{task_name} output: "
                    f"{result.stdout.strip()}"
                )

            if result.stderr.strip():
                logging.warning(
                    f"{task_name} stderr: "
                    f"{result.stderr.strip()}"
                )

        else:
            task["status"] = "failed"

            task["failures"] = (
                task.get("failures", 0) + 1
            )

            task["last_error"] = (
                result.stderr.strip()
                or result.stdout.strip()
                or f"Return code {result.returncode}"
            )

            logging.error(
                f"Task failed: {task_name}"
            )

            logging.error(
                f"{task_name} error: "
                f"{task['last_error']}"
            )

    except subprocess.TimeoutExpired:
        end_time = datetime.now()

        duration = (
            end_time - start_time
        ).total_seconds()

        task["status"] = "timeout"

        task["failures"] = (
            task.get("failures", 0) + 1
        )

        task["last_duration_seconds"] = round(
            duration,
            3
        )

        task["last_error"] = (
            f"Timeout after "
            f"{task_timeout_seconds} seconds"
        )

        logging.error(
            f"Task timeout: {task_name} "
            f"after {task_timeout_seconds}s"
        )

    except Exception as e:
        end_time = datetime.now()

        duration = (
            end_time - start_time
        ).total_seconds()

        task["status"] = "error"

        task["failures"] = (
            task.get("failures", 0) + 1
        )

        task["last_duration_seconds"] = round(
            duration,
            3
        )

        task["last_error"] = str(e)

        logging.exception(
            f"Unexpected error in task "
            f"{task_name}: {e}"
        )

    finally:
        end_time = datetime.now()

        task["last_run"] = end_time

        task["last_run_iso"] = (
            end_time.isoformat(
                timespec="seconds"
            )
        )

        task["last_end"] = (
            end_time.isoformat(
                timespec="seconds"
            )
        )

        save_registry(tasks)


def prepare_tasks(config):
    """
    Prepara las tareas conservando, cuando sea posible,
    el estado persistente de la ejecución anterior.

    Esto evita que un restart del servicio haga que todas
    las tareas se ejecuten inmediatamente de nuevo.
    """
    tasks = config.get("tasks", {})
    previous = load_registry()

    for name, task in tasks.items():

        old = previous.get(name, {})

        task["last_run_iso"] = old.get(
            "last_run"
        )

        task["last_run"] = parse_datetime(
            task["last_run_iso"]
        )

        task["last_start"] = old.get(
            "last_start"
        )

        task["last_end"] = old.get(
            "last_end"
        )

        task["last_success"] = old.get(
            "last_success"
        )

        task["last_duration_seconds"] = old.get(
            "last_duration_seconds"
        )

        task["failures"] = old.get(
            "failures",
            0
        )

        task["last_error"] = old.get(
            "last_error"
        )

        if not task.get("enabled", False):
            task["status"] = "disabled"

        elif task["last_run"] is None:
            task["status"] = "pending"

        else:
            task["status"] = old.get(
                "status",
                "pending"
            )

    return tasks


def main():
    config = load_config()

    scheduler_config = config.get(
        "scheduler",
        {}
    )

    loop_sleep_seconds = scheduler_config.get(
        "loop_sleep_seconds",
        5
    )

    task_timeout_seconds = scheduler_config.get(
        "task_timeout_seconds",
        300
    )

    tasks = prepare_tasks(config)

    save_registry(tasks)

    logging.info(
        "AtmosLink Central Scheduler started"
    )

    logging.info(
        f"Loaded config: {CONFIG_FILE}"
    )

    logging.info(
        f"Task registry: {REGISTRY_FILE}"
    )

    logging.info(
        f"Default task timeout: "
        f"{task_timeout_seconds}s"
    )

    while True:

        for task_name, task in tasks.items():

            if should_run(task):
                run_task(
                    task_name,
                    task,
                    task_timeout_seconds,
                    tasks
                )

        save_registry(tasks)

        time.sleep(loop_sleep_seconds)


if __name__ == "__main__":
    main()
