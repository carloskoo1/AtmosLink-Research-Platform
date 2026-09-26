#!/usr/bin/env python3
from pathlib import Path
import hashlib
import pandas as pd

ROOT = Path("/home/carlos/Proyectos/EstacionMeteorologica")
SOURCE = ROOT / "Data/exports/scientific_campaign_6g_integrated.csv"
OUT = ROOT / "Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"

CORE = [
    "dl_rssi_dbm","ul_rssi_dbm","dl_snr_db","ul_snr_db","dl_mcs","ul_mcs",
    "cu01_local_temp_avg_c","cu01_local_hum_avg_pct","cu01_local_press_hpa",
    "sj01_local_temp_avg_c","sj01_local_hum_avg_pct","sj01_local_press_hpa",
    "sj01_local_wind_speed_ms"
]
USE = ["rf_timestamp_utc","field_analysis_valid","operating_frequency_mhz",
       "channel_bandwidth_mhz"] + CORE

rows = []
need = 2860
for chunk in pd.read_csv(SOURCE, usecols=USE, chunksize=500):
    chunk["t"] = pd.to_datetime(chunk["rf_timestamp_utc"], utc=True, errors="coerce")
    chunk = chunk[
        (chunk["field_analysis_valid"] == 1)
        & (chunk["operating_frequency_mhz"] == 7000)
        & (chunk["channel_bandwidth_mhz"] == 20)
    ].dropna(subset=CORE).sort_values("t")
    if len(chunk):
        rows.append(chunk)
    if sum(len(x) for x in rows) >= need:
        break

df = pd.concat(rows, ignore_index=True).sort_values("t").iloc[:need].copy()
if len(df) != need:
    raise RuntimeError(f"Expected {need} prevalidation rows, got {len(df)}")
if str(df.iloc[2144]["rf_timestamp_utc"])[:19] != "2026-09-09T18:41:57":
    raise RuntimeError("Discovery boundary no longer matches frozen manifest")
if str(df.iloc[-1]["rf_timestamp_utc"])[:19] != "2026-09-13T03:29:49":
    raise RuntimeError("Characterization boundary no longer matches frozen manifest")
df.drop(columns=["t"]).to_csv(OUT, index=False)
h = hashlib.sha256(OUT.read_bytes()).hexdigest()
print("rows", len(df))
print("snapshot", OUT)
print("sha256", h)
