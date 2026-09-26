#!/usr/bin/env python3
"""Frozen post-v23 analog RF stress; never reads the validation block."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import numpy as np
import pandas as pd

ROOT = Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0, str(ROOT))
from scientific_discovery.synthetic_benchmark import (
    robust_z, rf_drop_threshold_from_array,
    detect_drop_indices_fixed_threshold, directional_test_indices,
)
SRC = ROOT / "Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
PROTOCOL = ROOT / "docs/ASDE_REVIEWER_B_ANALOG_STRESS_PROTOCOL.md"
OUT = ROOT / "Results/scientific_discovery/DISCOVERY-001/v25_reviewer_b_analog_stress"
EXPECTED = "eed7df2621f6952b9ea2eaa7524f735a706b69494d3d272fd2dd828b52a97387"
DRIVERS = {
    "cu01_local_temp_avg_c__rise": (1.5308007671599377, 23),
    "sj01_local_temp_avg_c__fall": (1.2876641771825945, 28),
    "sj01_local_hum_avg_pct__fall": (1.6365945597866016, 28),
    "sj01_local_press_hpa__rise": (0.8993210126363124, 28),
}
VIEWS = {
    "BOTH": ["dl_rssi_dbm", "ul_rssi_dbm", "dl_snr_db", "ul_snr_db"],
    "DL": ["dl_rssi_dbm", "dl_snr_db"],
    "UL": ["ul_rssi_dbm", "ul_snr_db"],
}
MORPHS = {"BOTH": VIEWS["BOTH"], "DL": VIEWS["DL"], "UL": VIEWS["UL"]}
LAGS = [15, 30, 60]
HORIZONS = [30, 60, 120]
ALPHA = .05 / (len(DRIVERS) * len(HORIZONS))
N_TRIALS = 100
N_NULL = 1000

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def events(score, threshold):
    output, last = [], None
    for t, value in score.dropna().items():
        if value < threshold:
            continue
        if value < score.loc[t-pd.Timedelta("10min"):t+pd.Timedelta("10min")].max():
            continue
        if last is None or t-last >= pd.Timedelta(minutes=360):
            output.append(t)
            last = t
    return output

def reference(frame):
    med = frame.median()
    mad = (frame-med).abs().median()
    iqr = (frame.quantile(.75)-frame.quantile(.25))/1.349
    std = frame.std(ddof=0)
    scale = (1.4826*mad).where(mad>0, iqr).where(lambda x:x>0, std).replace(0, 1.)
    return med.to_numpy(float), scale.to_numpy(float)

if subprocess.check_output(["git","status","--porcelain"],cwd=ROOT,text=True).strip():
    raise RuntimeError("Freeze violation: Git tree must be clean")
commit = subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
if digest(SRC) != EXPECTED:
    raise RuntimeError("Development source hash changed")
if OUT.exists():
    raise RuntimeError("Refusing to overwrite existing audit")
df = pd.read_csv(SRC)
df["t"] = pd.to_datetime(df.rf_timestamp_utc,utc=True)
weather = sorted({name.rsplit("__",1)[0] for name in DRIVERS})
X = df.set_index("t")[weather+VIEWS["BOTH"]].resample("5min").median()
idx = {}
for name,(threshold,expected) in DRIVERS.items():
    col,direction = name.rsplit("__",1)
    score = robust_z(X[col].diff(3))
    times = events(score if direction=="rise" else -score, threshold)
    if len(times) != expected:
        raise RuntimeError(f"Unexpected driver count: {name}: {len(times)}")
    idx[name] = np.asarray([X.index.get_loc(t) for t in times],int)
bounds_time = [
    ("2026-09-01T18:30:52Z","2026-09-04T08:02:17Z"),
    ("2026-09-04T08:12:19Z","2026-09-07T05:14:26Z"),
    ("2026-09-07T05:19:27Z","2026-09-09T18:41:57Z"),
    ("2026-09-09T18:46:58Z","2026-09-13T03:29:49Z"),
]
bounds = [(int(X.index.searchsorted(pd.Timestamp(a))),
           int(X.index.searchsorted(pd.Timestamp(b),side="right")-1))
          for a,b in bounds_time]
refs = {}
baseline = {}
for view,features in VIEWS.items():
    base = X[features].to_numpy(float)
    med,scale = reference(X[features])
    threshold = rf_drop_threshold_from_array(base,med,scale,quantile=.075)
    refs[view] = (med,scale,threshold)
    baseline[view] = detect_drop_indices_fixed_threshold(base,med,scale,threshold)

def selected(candidate, rf):
    names = []
    for name, driver in candidate.items():
        passed = False
        for horizon in HORIZONS:
            hs = horizon//5
            stat = directional_test_indices(driver,rf,hs)
            if stat["p_value"] >= ALPHA or stat["discordant"] < 8:
                continue
            positive = 0
            for a,b in bounds:
                de = driver[(driver>=a)&(driver<=b)]
                re = rf[(rf>=a-hs)&(rf<=b+hs)]
                fold = directional_test_indices(de,re,hs)
                positive += fold["post_only"] > fold["pre_only"]
            passed |= positive >= 3
        if passed:
            names.append(name)
    return names

def perturb(truth,lag,seed,morph):
    base = X[VIEWS["BOTH"]].to_numpy(float).copy()
    positions = [VIEWS["BOTH"].index(c) for c in MORPHS[morph]]
    rng = np.random.default_rng(530000+seed)
    activated = 0
    for e in idx[truth]:
        if rng.random() > .70:
            continue
        start = e+lag//5
        if start >= len(base):
            continue
        base[start:min(start+3,len(base)),positions] -= 2.0
        activated += 1
    return base,activated

rows = []
for truth in idx:
    for lag in LAGS:
        for seed in range(N_TRIALS):
            for morph in MORPHS:
                arr,n_activated = perturb(truth,lag,seed,morph)
                for view,features in VIEWS.items():
                    positions = [VIEWS["BOTH"].index(c) for c in features]
                    med,scale,threshold = refs[view]
                    rf = detect_drop_indices_fixed_threshold(
                        arr[:,positions],med,scale,threshold)
                    names = selected(idx,rf)
                    rows.append(dict(mode="injected",truth=truth,lag_min=lag,
                        seed=seed,morphology=morph,view=view,activated=n_activated,
                        rf_events=len(rf),truth_selected=truth in names,
                        exclusive_truth=(truth in names and len(names)==1),
                        distractor=any(n!=truth for n in names),
                        selected=";".join(names)))
rng = np.random.default_rng(2026092609)
for seed in range(N_NULL):
    shift = int(rng.integers(72,len(X)-72))
    shifted = {name:np.sort((driver+shift)%len(X)) for name,driver in idx.items()}
    for view,rf in baseline.items():
        names = selected(shifted,rf)
        rows.append(dict(mode="null",truth="",lag_min=np.nan,seed=seed,
            morphology="",view=view,activated=0,rf_events=len(rf),
            truth_selected=False,exclusive_truth=False,distractor=bool(names),
            selected=";".join(names)))
trials = pd.DataFrame(rows)
metrics = []
for (morph,view,lag),g in trials[trials["mode"]=="injected"].groupby(
        ["morphology","view","lag_min"]):
    metrics.append(dict(morphology=morph,view=view,lag_min=int(lag),
        trials=len(g),truth_selection=float(g.truth_selected.mean()),
        exclusive_truth=float(g.exclusive_truth.mean()),
        distractor=float(g.distractor.mean()),
        mean_rf_events=float(g.rf_events.mean())))
summary = {
    "status":"post-audit RF morphology diagnostic; conditional on one development background",
    "commit":commit,"source_sha256":digest(SRC),"protocol_sha256":digest(PROTOCOL),
    "n_development_rows":len(df),"n_grid_bins":len(X),"n_injected":int(sum(trials["mode"]=="injected")),
    "n_null":int(sum(trials["mode"]=="null")),
    "reference":{v:dict(features=VIEWS[v],median=m.tolist(),scale=s.tolist(),
                          drop_threshold=t,baseline_rf_events=len(baseline[v]))
                 for v,(m,s,t) in refs.items()},
    "null_selection":{v:float((g.selected!="").mean()) for v,g in
                       trials[trials["mode"]=="null"].groupby("view")},
    "limitations":["fixed field background","post-v21 design","surrogate null uncalibrated",
                   "unverified natural propagation and operational mechanisms"],
}
OUT.mkdir(parents=True,exist_ok=False)
trials.to_csv(OUT/"trials.csv",index=False)
pd.DataFrame(metrics).to_csv(OUT/"metrics.csv",index=False)
(OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(dict(out=str(OUT),null=summary["null_selection"],
                      reference=summary["reference"],
                      metrics_2db=metrics),indent=2))
