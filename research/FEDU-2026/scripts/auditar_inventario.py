#!/usr/bin/env python3
"""FEDU: auditoría preliminar estrictamente de solo lectura.

Este inventario NO confirma eventos de degradación: agrupa errores de adquisición
o prueba como candidatos que requieren corroboración independiente.
No ejecuta pruebas de red, no cambia configuración y no escribe en las bases.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timedelta
import json
from pathlib import Path
import sqlite3


def connect_readonly(db: Path) -> sqlite3.Connection:
    if not db.is_file():
        raise FileNotFoundError(db)
    conn = sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True, timeout=2)
    conn.execute("PRAGMA query_only=ON")
    return conn


def existing_tables(conn: sqlite3.Connection) -> set[str]:
    return {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}


def schema(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')}


def count_range(conn: sqlite3.Connection, table: str, timestamp: str) -> dict:
    n, first, last = conn.execute(
        f'SELECT COUNT(*), MIN("{timestamp}"), MAX("{timestamp}") FROM "{table}"'
    ).fetchone()
    return {"rows": n, "first": first, "last": last}


def by_value(conn: sqlite3.Connection, table: str, field: str) -> dict:
    return {str(value): count for value, count in conn.execute(
        f'SELECT "{field}", COUNT(*) FROM "{table}" GROUP BY "{field}"'
    ).fetchall()}


def candidates(conn: sqlite3.Connection, gap_minutes: int) -> list[dict]:
    """Agrupar pruebas fallidas próximas, sin interpretarlas como fallas RF."""
    records = conn.execute(
        "SELECT timestamp_start_local, direction "
        "FROM active_throughput_6g "
        "WHERE status='ERROR' ORDER BY timestamp_start_local"
    ).fetchall()
    output: list[dict] = []
    for raw_time, direction in records:
        try:
            when = datetime.fromisoformat(raw_time)
        except (ValueError, TypeError):
            continue
        if (not output or when - datetime.fromisoformat(output[-1]["last"])
                > timedelta(minutes=gap_minutes)):
            output.append({
                "first": when.isoformat(),
                "last": when.isoformat(),
                "failed_tests": 1,
                "directions": [direction] if direction else [],
            })
        else:
            last = output[-1]
            last["last"] = when.isoformat()
            last["failed_tests"] += 1
            if direction and direction not in last["directions"]:
                last["directions"].append(direction)
    return output


def review_campaign_events(path: Path) -> dict:
    count = Counter()
    last_commit = None
    valid_lines = 0
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            valid_lines += 1
            name = item.get("event", "UNSPECIFIED")
            count[str(name)] += 1
            if name == "SWITCH_COMMITTED":
                last_commit = item.get("timestamp_utc")
    return {"lines_valid": valid_lines, "event_counts": dict(count),
            "last_switch_commit_utc": last_commit}


def review_schedule(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8") as stream:
        schedule = list(csv.DictReader(stream))
    if not schedule:
        return {"rows": 0}
    return {
        "rows": len(schedule),
        "last_scheduled_end_local": schedule[-1].get("end_local"),
        "last_scheduled_scenario": schedule[-1].get("scenario_id"),
        "planned_configuration_transitions": max(0, len(schedule) - 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True,
                        help="Ruta SQLite existente, abierta con mode=ro")
    parser.add_argument("--campaign-events", type=Path)
    parser.add_argument("--campaign-schedule", type=Path)
    parser.add_argument("--candidate-gap-min", type=int, default=30)
    args = parser.parse_args()
    if args.candidate_gap_min < 1:
        parser.error("--candidate-gap-min debe ser positivo")

    result = {
        "audit_type": "INVENTARIO_PRELIMINAR_NO_CONFIRMATORIO",
        "predictive_validation_completed": False,
        "independent_degradation_events_confirmed": None,
        "candidate_gap_min": args.candidate_gap_min,
        "caution": [
            "ERROR en pruebas/colección no confirma degradación de RF",
            "candidatos no son eventos independientes ni etiquetas de ML",
            "transiciones programadas deben excluirse o estratificarse",
            "no usar tasa DL reportada por radio como throughput medido",
        ],
    }
    conn = connect_readonly(args.db)
    try:
        tables = existing_tables(conn)
        for name, ts in (
            ("active_throughput_6g", "timestamp_start_local"),
            ("radio_link_config_telemetry", "timestamp_local"),
            ("scientific_campaign_6g_integrated", "rf_timestamp_local"),
            ("master_observations_multistation", "bucket_minute"),
        ):
            if name not in tables or ts not in schema(conn, name):
                continue
            item = count_range(conn, name, ts)
            fields = schema(conn, name)
            if name == "active_throughput_6g":
                if "status" in fields:
                    item["by_status"] = by_value(conn, name, "status")
                    tentative = candidates(conn, args.candidate_gap_min)
                    item["unverified_error_clusters"] = len(tentative)
                    item["unverified_error_cluster_examples"] = tentative[:12]
                if "direction" in fields:
                    item["by_direction"] = by_value(conn, name, "direction")
            if name == "radio_link_config_telemetry" and "collection_status" in fields:
                item["by_collection_status"] = by_value(conn, name, "collection_status")
            if name == "master_observations_multistation" and "station_id" in fields:
                item["by_station"] = by_value(conn, name, "station_id")
            if name == "scientific_campaign_6g_integrated":
                for col in ("both_weather_stations_matched", "field_analysis_valid"):
                    if col in fields:
                        item["by_" + col] = by_value(conn, name, col)
            result[name] = item
    finally:
        conn.close()
    if args.campaign_events and args.campaign_events.is_file():
        result["campaign_events"] = review_campaign_events(args.campaign_events)
    if args.campaign_schedule and args.campaign_schedule.is_file():
        result["campaign_schedule"] = review_schedule(args.campaign_schedule)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
