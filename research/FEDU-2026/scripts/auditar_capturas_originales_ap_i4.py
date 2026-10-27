#!/usr/bin/env python3
"""Auditar capturas AP 'show sta' I4 sin modificar datos.

Sin dependencias externas. Este script SOLO LEE archivos raw_show_sta_YYYY-MM-DD.log.
No imprime direcciones, MAC, contraseñas ni muestras originales.
La pertenencia al SM esperado se verifica con FEDU_EXPECTED_PEER (variable local).
Los códigos SSH no están disponibles en estos logs (el script de adquisición usa || true).
No interpretar la ausencia de tabla como desasociación RF verificada.

Uso:
 FEDU_EXPECTED_PEER=<IP_SM_LOCAL> python3 auditar_capturas_originales_ap_i4.py \
   --raw-dir /ruta/autorizada/epmp_monitor/logs
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re

WINDOWS = [
    ("C001", "2026-09-04T08:00:07", "2026-09-04T08:30:25"),
    ("C002", "2026-09-04T09:15:07", "2026-09-04T16:00:21"),
    ("C003", "2026-09-10T19:00:06", "2026-09-11T13:15:18"),
    ("C011", "2026-10-05T15:45:06", "2026-10-05T16:15:18"),
    ("C016", "2026-10-13T13:45:06", "2026-10-13T14:00:05"),
    ("C020", "2026-10-21T02:45:05", "2026-10-21T04:00:27"),
    ("C022", "2026-10-21T06:00:06", "2026-10-21T07:45:24"),
    ("C024", "2026-10-21T10:15:06", "2026-10-21T10:30:24"),
]

STAMP = re.compile(r"^===== (\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)")
PEER = re.compile(r"^\s*connectedSTAIP\s+(\S+)", re.MULTILINE)

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def classify(text: str, expected_peer: str) -> str:
    ips = PEER.findall(text)
    if "[cambiumAPConnectedSTATable]" in text:
        if expected_peer in ips:
            return "PEER_EXPECTED_IN_TABLE"
        return "TABLE_OTHER_OR_ZERO_PEER"
    if "Connected sessions:" in text:
        return "SSH_BANNER_NO_RADIO_TABLE"
    return "NO_USABLE_RESPONSE"

def parse_file(path: Path, expected_peer: str):
    timestamp = None
    lines = []

    def finish():
        if timestamp is not None:
            return (timestamp, classify("".join(lines), expected_peer))
        return None

    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            match = STAMP.match(line)
            if match:
                sample = finish()
                if sample is not None:
                    yield sample
                timestamp = match.group(1)
                lines = []
            else:
                lines.append(line)
    sample = finish()
    if sample is not None:
        yield sample

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw-dir", type=Path, required=True)
    args = p.parse_args()

    expected = os.getenv("FEDU_EXPECTED_PEER", "").strip()
    if not expected or expected == "0.0.0.0":
        p.error("Defina FEDU_EXPECTED_PEER localmente con el IP del SM")
    days = sorted({v[:10] for _, a, b in WINDOWS for v in (a, b)})
    observations = []
    file_info = []
    for day in days:
        path = args.raw_dir / f"raw_show_sta_{day}.log"
        if not path.is_file():
            file_info.append({"date": day, "status": "MISSING_FILE"})
            continue
        file_info.append({"date": day, "status": "AVAILABLE", "sha256": sha256_file(path)})
        observations.extend(parse_file(path, expected))

    cases = []
    for code, start, end in WINDOWS:
        rows = [(t, state) for t, state in observations if start <= t <= end]
        counts = Counter(state for _, state in rows)
        cases.append({
            "id": code, "start_local": start, "end_local": end,
            "n": len(rows), "counts": dict(sorted(counts.items())),
            "first": rows[0][0] if rows else None,
            "last": rows[-1][0] if rows else None,
            "ground_truth_rf_failure": "INDETERMINADO",
        })
    print(json.dumps({"timezone": "America/Lima", "source": "raw AP show sta",
                      "files": file_info, "cases": cases}, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
