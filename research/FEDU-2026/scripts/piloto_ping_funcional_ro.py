#!/usr/bin/env python3
"""FEDU: piloto ACOTADO de disponibilidad ICMP local AP/SM (no permanente).

Hace 1 ICMP IPv4 por destino en cada ronda; sin configuraciones RF, switch
ni modificacion de los recolectores de AtmosLink. El resultado es evidencia
de conectividad de gestión local, NO prueba causal de propagación RF.

Requisitos: ping de iputils instalado y rutas locales verificadas.
No incluir destinos reales ni secretos en GitHub: pasar --ap y --sm en local.

Ejemplo local (privado):
 python3 piloto_ping_funcional_ro.py --ap IP_AP --sm IP_SM \
   --runs 3 --interval-sec 10 --output /ruta_privada/piloto.jsonl
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import time

RTT = re.compile(r"time[=<]([0-9.]+)\s*ms")


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def probe(host: str, label: str) -> dict:
    start = utcnow()
    t0 = time.monotonic()
    try:
        r = subprocess.run(
            ["ping", "-n", "-c", "1", "-W", "1", host],
            capture_output=True, text=True, timeout=3, check=False,
        )
        if r.returncode == 0:
            status = "ICMP_REPLY"
        elif r.returncode == 1:
            status = "ICMP_NO_REPLY"
        else:
            status = "PROBE_ERROR"
        match = RTT.search(r.stdout)
        rtt = float(match.group(1)) if match else None
    except (OSError, subprocess.TimeoutExpired):
        status, rtt = "PROBE_ERROR", None
    return {
        "endpoint": label, "start_utc": start, "available_at_utc": utcnow(),
        "status": status, "rtt_ms": rtt,
        "elapsed_ms": round((time.monotonic()-t0)*1000, 1),
    }


def interpret(ap: str, sm: str) -> str:
    if "PROBE_ERROR" in (ap, sm):
        return "INSTRUMENT_ERROR"
    if ap == "ICMP_REPLY" and sm == "ICMP_REPLY":
        return "BOTH_MANAGEMENT_ENDPOINTS_RESPOND"
    if ap == "ICMP_REPLY" and sm == "ICMP_NO_REPLY":
        return "SM_PATH_NO_REPLY_CHECK_RF_OR_MANAGEMENT"
    if ap == "ICMP_NO_REPLY" and sm == "ICMP_NO_REPLY":
        return "BOTH_PATHS_NO_REPLY_CHECK_LOCAL_NETWORK"
    return "ASYMMETRIC_OR_UNEXPECTED_PATH"


def append_jsonl_private(path: Path, item: dict) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ap", required=True, help="IP local AP; no se guarda")
    p.add_argument("--sm", required=True, help="IP local SM; no se guarda")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--interval-sec", type=float, default=10)
    args = p.parse_args()
    if not (1 <= args.runs <= 5) or args.interval_sec < 10:
        p.error("Piloto acotado: 1-5 rondas; intervalo al menos 10 segundos")
    for i in range(args.runs):
        began = utcnow()
        ap = probe(args.ap, "CU01_AP_6G")
        sm = probe(args.sm, "SJ01_SM_6G")
        record = {
            "round": i+1, "source": "FEDU_ICMP_PILOT_MANAGEMENT_LOCAL",
            "round_start_utc": began, "round_available_at_utc": utcnow(),
            "ap": ap, "sm": sm,
            "interpretation": interpret(ap["status"], sm["status"]),
            "eligibility_rf_event": "NOT_DIRECTLY_ESTABLISHED",
            "source_clock": "CONTROLLER_UTC",
        }
        append_jsonl_private(args.output, record)
        print(f"ronda {i+1}: AP={ap['status']} SM={sm['status']} "
              f"resultado={record['interpretation']}")
        if i < args.runs-1:
            time.sleep(args.interval_sec)


if __name__ == "__main__":
    main()
