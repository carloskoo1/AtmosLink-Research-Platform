#!/usr/bin/env python3
from pathlib import Path
import json,sys
import pandas as pd

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scripts.validate_asde_v24_start_manifest import validate

if len(sys.argv)!=2:
    raise SystemExit("Usage: run_asde_v24_prospective.py <FROZEN_ACTIVE_manifest.json>")

manifest_path=Path(sys.argv[1])
errors,m=validate(manifest_path,require_active=True)
if errors:
    print(json.dumps({"status":"REFUSED","errors":errors},indent=2))
    raise SystemExit(2)

source=ROOT/m["prospective_source"]["path"]
if not source.exists():
    raise RuntimeError(f"Prospective source missing: {source}")

# Only after all integrity gates pass is the dedicated prospective source read.
df=pd.read_csv(source)
if "rf_timestamp_utc" not in df.columns:
    raise RuntimeError("Prospective source lacks rf_timestamp_utc")
t=pd.to_datetime(df["rf_timestamp_utc"],utc=True,errors="raise")
start=pd.Timestamp(m["calibration_start_utc"])
end=pd.Timestamp(m["calibration_end_utc"])
if len(df)==0:
    raise RuntimeError("Prospective source is empty")
if t.min()<start:
    raise RuntimeError("Prospective source contains pre-start rows")
if t.max()>=end:
    raise RuntimeError("Prospective source contains rows at/after frozen 60-day end")

# This pre-freeze runner intentionally stops at source isolation.
# Inferential execution will be added only after a second concordance audit.
print(json.dumps({
  "status":"SOURCE_ISOLATION_PASS",
  "rows":len(df),
  "min_timestamp_utc":t.min().isoformat(),
  "max_timestamp_utc":t.max().isoformat(),
  "message":"Prospective source passed isolation gates. Inferential execution is not yet enabled."
},indent=2))
