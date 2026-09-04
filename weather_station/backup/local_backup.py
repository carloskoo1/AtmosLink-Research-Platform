import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
import shutil

from weather_station.config.station_manager import get_station_context


KEEP_LAST = 20


def backup_sqlite(db_path: Path, output_db: Path):
    output_db.parent.mkdir(parents=True, exist_ok=True)

    source = sqlite3.connect(db_path)
    target = sqlite3.connect(output_db)

    with target:
        source.backup(target)

    source.close()
    target.close()


def cleanup_old_backups(backup_dir: Path):
    backups = sorted(
        backup_dir.glob("*.zip"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    for old_file in backups[KEEP_LAST:]:
        old_file.unlink()


def main():
    ctx = get_station_context()

    station_id = ctx["station_id"]
    db_path = Path(ctx["database"])
    config_file = Path(ctx["config_file"])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_root = Path("Backups") / station_id
    work_dir = backup_root / f"backup_{station_id}_{timestamp}"
    zip_file = backup_root / f"backup_{station_id}_{timestamp}.zip"

    work_dir.mkdir(parents=True, exist_ok=True)

    print("======================================")
    print(" AtmosLink Local Backup")
    print("======================================")
    print(f"Station : {station_id} | {ctx['station_name']}")
    print(f"Role    : {ctx['radio_role']}")
    print(f"DB      : {db_path}")
    print(f"Output  : {zip_file}")

    if not db_path.exists():
        raise FileNotFoundError(f"No existe la base de datos: {db_path}")

    db_backup = work_dir / db_path.name
    backup_sqlite(db_path, db_backup)

    if config_file.exists():
        shutil.copy2(config_file, work_dir / config_file.name)

    export_dir = Path("Data") / "exports"
    export_names = (
        "master_observations.csv",
        "master_observations_multistation.csv",
        "scientific_campaign_observations.csv",
        "scientific_campaign_6g_integrated.csv",
        "active_throughput_6g.csv",
    )

    for export_name in export_names:
        export_file = export_dir / export_name
        if export_file.exists():
            shutil.copy2(export_file, work_dir / export_name)

    with zipfile.ZipFile(zip_file, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in work_dir.rglob("*"):
            zf.write(file, file.relative_to(work_dir))

    shutil.rmtree(work_dir)

    cleanup_old_backups(backup_root)

    print("--------------------------------------")
    print("Backup generado correctamente")
    print(f"Archivo : {zip_file}")
    print("Status  : OK")
    print("======================================")


if __name__ == "__main__":
    main()
