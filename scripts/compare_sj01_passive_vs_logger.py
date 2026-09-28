#!/usr/bin/env python3
"""Compare passive ESP32-TX capture against the production SJ01 logger journal."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess

import pandas as pd

TS_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[.,]\d+)?[+-]\d{2}:\d{2})"
)

def load_passive(path: Path) -> pd.DataFrame:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        ts = pd.to_datetime(rec["timestamp_utc"], utc=True)
        rows.append({
            "minute": ts.floor("min"),
            "passive_kind": rec.get("kind", "OTHER"),
            "passive_t_s": rec.get("t_s"),
            "passive_raw_len": rec.get("raw_len"),
            "passive_leading_ff": rec.get("leading_ff"),
        })
    if not rows:
        raise SystemExit("Passive capture has no records.")
    df = pd.DataFrame(rows)
    return collapse_one_per_minute(df, "passive_kind", "PASSIVE_MULTI")

def load_logger(since_utc: pd.Timestamp, until_utc: pd.Timestamp) -> pd.DataFrame:
    since = since_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    until = until_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    p = subprocess.run(
        [
            "journalctl", "-u", "weather-logger-sj01.service",
            "--since", since, "--until", until,
            "--no-pager", "-o", "short-iso",
        ],
        capture_output=True, text=True, check=True,
    )
    rows = []
    for line in p.stdout.splitlines():
        mt = TS_RE.match(line)
        if not mt:
            continue
        ts = pd.to_datetime(mt.group(1).replace(",", "."), utc=True)
        kind = None
        t_s = None
        if "RX_VALIDO:" in line:
            kind = "VALID17"
            payload = line.split("RX_VALIDO:", 1)[1].strip()
            try:
                t_s = int(payload.split(",", 1)[0])
            except Exception:
                pass
        elif "fragmento no UTF-8 descartado" in line and "leading_ff=64" in line:
            kind = "FF64"
        if kind:
            rows.append({"minute": ts.floor("min"), "logger_kind": kind, "logger_t_s": t_s})
    if not rows:
        raise SystemExit("No production logger events found for passive capture interval.")
    df = pd.DataFrame(rows)
    return collapse_one_per_minute(df, "logger_kind", "LOGGER_MULTI")

def collapse_one_per_minute(df: pd.DataFrame, kind_col: str, multi_label: str) -> pd.DataFrame:
    other_cols = [c for c in df.columns if c not in {"minute", kind_col}]
    out = []
    for minute, g in df.groupby("minute"):
        kinds = sorted(set(g[kind_col].dropna()))
        row = {"minute": minute}
        row[kind_col] = kinds[0] if len(kinds) == 1 and len(g) == 1 else multi_label
        for col in other_cols:
            vals = g[col].dropna()
            row[col] = vals.iloc[0] if len(vals) else None
        out.append(row)
    return pd.DataFrame(out).sort_values("minute")

def causal_label(row) -> str:
    p = row.get("passive_kind")
    l = row.get("logger_kind")
    if p == "FF64" and l == "FF64":
        return "FF64_AT_ESP32_TX_AND_LOGGER"
    if p == "VALID17" and l == "FF64":
        return "ESP32_TX_CLEAN_LOGGER_FF64"
    if p == "VALID17" and l == "VALID17":
        return "BOTH_VALID"
    if p == "FF64" and l == "VALID17":
        return "DISCORDANT_PASSIVE_FF64_LOGGER_VALID"
    if pd.isna(p):
        return "NO_PASSIVE_EVENT"
    if pd.isna(l):
        return "NO_LOGGER_EVENT"
    return "OTHER_OR_MULTI"

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("capture", help="JSONL produced by capture_sj01_passive_uart.py")
    ap.add_argument("--output", default=None)
    args = ap.parse_args()

    capture = Path(args.capture)
    passive = load_passive(capture)
    start = passive["minute"].min() - pd.Timedelta(minutes=2)
    end = passive["minute"].max() + pd.Timedelta(minutes=2)
    logger = load_logger(start, end)

    merged = passive.merge(logger, on="minute", how="outer").sort_values("minute")
    merged["causal_class"] = merged.apply(causal_label, axis=1)

    out = Path(args.output) if args.output else capture.with_name(
        capture.stem + "_vs_logger.csv"
    )
    merged.to_csv(out, index=False)

    counts = Counter(merged["causal_class"])
    print("===== CAUSAL COMPARISON =====")
    for key, value in sorted(counts.items()):
        print(f"{key}: {value}")

    decisive_tx = counts["FF64_AT_ESP32_TX_AND_LOGGER"]
    decisive_downstream = counts["ESP32_TX_CLEAN_LOGGER_FF64"]
    print()
    if decisive_tx > 0 and decisive_downstream == 0:
        print("INTERPRETATION: FF64 is directly observed at the ESP32 TX tap.")
        print("Fault boundary moves upstream toward ESP32/firmware/UART.")
    elif decisive_downstream > 0 and decisive_tx == 0:
        print("INTERPRETATION: ESP32 TX is valid when production logger records FF64.")
        print("Fault boundary moves downstream toward CP2102/USB/host reception.")
    elif decisive_tx > 0 and decisive_downstream > 0:
        print("INTERPRETATION: mixed evidence; do not assign a single root cause yet.")
    else:
        print("INTERPRETATION: no decisive FF64 coincidence captured; extend duration.")

    print("Output:", out)

if __name__ == "__main__":
    main()
