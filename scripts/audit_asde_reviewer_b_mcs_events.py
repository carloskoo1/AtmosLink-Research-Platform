#!/usr/bin/env python3
"""Read-only, post-audit decomposition of frozen development RF events."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import pandas as pd

ROOT = Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.synthetic_benchmark import (
    RF_FEATURES, robust_reference,
    rf_drop_threshold_from_array, detect_drop_indices_fixed_threshold,
)
SRC = ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
OUT = ROOT/"Results/scientific_discovery/DISCOVERY-001/reviewer_b_mcs_event_diagnostic.json"
EVENTS = ROOT/"Results/scientific_discovery/DISCOVERY-001/reviewer_b_mcs_event_rows.csv"
EXPECTED = "eed7df2621f6952b9ea2eaa7524f735a706b69494d3d272fd2dd828b52a97387"
if hashlib.sha256(SRC.read_bytes()).hexdigest() != EXPECTED:
    raise RuntimeError("Development snapshot hash changed")
df = pd.read_csv(SRC)
df["t"] = pd.to_datetime(df.rf_timestamp_utc,utc=True)
X = df.set_index("t")[RF_FEATURES].resample("5min").median()

def reference(frame):
    med = frame.median()
    mad = (frame-med).abs().median()
    iqr = (frame.quantile(.75)-frame.quantile(.25))/1.349
    std = frame.std(ddof=0)
    scale = (1.4826*mad).where(mad>0,iqr).where(lambda a:a>0,std).replace(0,1)
    return med,scale

def outcome(frame):
    med,scale = reference(frame)
    array = frame.to_numpy(float)
    threshold = rf_drop_threshold_from_array(
        array,med.to_numpy(float),scale.to_numpy(float),quantile=.075)
    idx = detect_drop_indices_fixed_threshold(
        array,med.to_numpy(float),scale.to_numpy(float),threshold,refractory_steps=6)
    return idx,threshold,scale

six,thr6,scale6 = outcome(X)
analog,thr4,scale4 = outcome(X[RF_FEATURES[:4]])
delta = X-X.shift(3)
normalized = delta.div(scale6)
rows = []
for i in six:
    mcs_jump = bool((delta.iloc[i][["dl_mcs","ul_mcs"]].abs()>=90).any())
    mcs_contrib = float(normalized.iloc[i][["dl_mcs","ul_mcs"]].sum()/6)
    analog_contrib = float(normalized.iloc[i][RF_FEATURES[:4]].sum()/6)
    rows.append(dict(timestamp_utc=X.index[i].isoformat(),bin_index=int(i),
        mcs_jump_90=mcs_jump,mcs_contribution=mcs_contrib,
        analog_contribution=analog_contrib,
        analog_event_exact=bool(i in analog),
        analog_event_within_15min=bool(any(abs(i-j)<=3 for j in analog)),
        dl_mcs_delta=float(delta.iloc[i]["dl_mcs"]),
        ul_mcs_delta=float(delta.iloc[i]["ul_mcs"])))
tab = pd.DataFrame(rows)
jump = tab[tab.mcs_jump_90]
payload = {
    "classification":"post-audit descriptive diagnostic; no causal or null calibration",
    "source_sha256":EXPECTED,"development_rows":len(df),"grid_bins":len(X),
    "all6_threshold":thr6,"analog4_threshold":thr4,
    "all6_events":len(six),"analog4_events":len(analog),
    "all6_analog_exact_overlap":int(tab.analog_event_exact.sum()),
    "all6_analog_within_15min":int(tab.analog_event_within_15min.sum()),
    "all6_events_with_mcs_90_jump":len(jump),
    "mcs_jump_events_analog_nonnegative":int((jump.analog_contribution>=0).sum()),
    "mcs_jump_events_mcs_dominant":int(
        (jump.mcs_contribution<jump.analog_contribution).sum()),
    "mcs_jump_events_no_analog_within_15min":int(
        (~jump.analog_event_within_15min).sum()),
    "all6_scale":scale6.to_dict(),"analog4_scale":scale4.to_dict(),
}
OUT.write_text(json.dumps(payload,indent=2)+"\n")
tab.to_csv(EVENTS,index=False)
print(json.dumps(payload,indent=2))
