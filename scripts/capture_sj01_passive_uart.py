#!/usr/bin/env python3
"""Passive SJ01 UART tap capture for FF64 causal isolation.

Use ONLY with a second RX-only USB-UART adapter or logic-level serial tap.
The script refuses the known production weather and wind ttyUSB devices.
It does not modify databases, services, firmware, or station configuration.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time

import serial

FORBIDDEN_REALPATHS = {"/dev/ttyUSB0", "/dev/ttyUSB1"}
FORBIDDEN_BY_ID_SUBSTRINGS = (
    "Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001",
    "1a86_USB_Serial-if00-port0",
)

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

def classify(raw: bytes) -> dict:
    ff = 0
    while ff < len(raw) and raw[ff] == 0xFF:
        ff += 1

    clean = raw.rstrip(b"\r\n")
    decoded = None
    decode_ok = True
    try:
        decoded = clean.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        decode_ok = False

    tail_ascii = raw[ff:].rstrip(b"\r\n").decode("utf-8", errors="replace")
    fields = decoded.split(",") if decoded is not None else []
    t_s = None
    if decoded is not None and fields:
        try:
            t_s = int(fields[0])
        except ValueError:
            pass

    if ff == 64:
        kind = "FF64"
    elif decode_ok and len(fields) == 17:
        kind = "VALID17"
    else:
        kind = "OTHER"

    return {
        "kind": kind,
        "raw_len": len(raw),
        "leading_ff": ff,
        "ends_crlf": raw.endswith(b"\r\n"),
        "ends_lf": raw.endswith(b"\n"),
        "decode_ok": decode_ok,
        "field_count": len(fields) if decoded is not None else None,
        "t_s": t_s,
        "text": decoded,
        "tail_ascii": tail_ascii,
        "raw_hex": raw.hex(),
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", required=True,
                    help="Second passive RX-only serial device, preferably /dev/serial/by-id/...")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--duration-minutes", type=float, default=20.0)
    ap.add_argument("--output", default=None)
    args = ap.parse_args()

    port = Path(args.port)
    try:
        real = str(port.resolve(strict=True))
    except FileNotFoundError:
        raise SystemExit(f"Port does not exist: {args.port}")

    if real in FORBIDDEN_REALPATHS or any(x in args.port for x in FORBIDDEN_BY_ID_SUBSTRINGS):
        raise SystemExit(
            f"REFUSED: {args.port} resolves to known production device {real}. "
            "Use a second RX-only adapter/tap."
        )

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(args.output) if args.output else (
        Path("Results") / "sj01_ff64_passive_capture" / f"passive_uart_{stamp}.jsonl"
    )
    out.parent.mkdir(parents=True, exist_ok=True)

    deadline = time.monotonic() + args.duration_minutes * 60.0
    counts = {"VALID17": 0, "FF64": 0, "OTHER": 0}

    with serial.Serial(
        port=args.port,
        baudrate=args.baud,
        timeout=2.0,
        write_timeout=2.0,
        rtscts=False,
        dsrdtr=False,
        xonxoff=False,
        exclusive=True,
    ) as ser, out.open("w", encoding="utf-8") as fh:
        try:
            ser.setDTR(False)
            ser.setRTS(False)
        except Exception:
            pass

        print(f"Passive capture: {args.port} -> {real} @ {args.baud}")
        print(f"Output: {out}")
        print(f"Duration: {args.duration_minutes:.1f} min")

        while time.monotonic() < deadline:
            raw = ser.read_until(b"\n")
            if not raw:
                continue
            rec = {"timestamp_utc": utc_now(), **classify(raw)}
            counts[rec["kind"]] += 1
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            print(
                rec["timestamp_utc"],
                rec["kind"],
                f"len={rec['raw_len']}",
                f"ff={rec['leading_ff']}",
                f"fields={rec['field_count']}",
            )

    print("SUMMARY", json.dumps(counts, sort_keys=True))
    print(out)

if __name__ == "__main__":
    main()
