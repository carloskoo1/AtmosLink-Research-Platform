#!/usr/bin/env python3
from pathlib import Path
import json, math
import pandas as pd

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
DIR=ROOT/"Results/scientific_discovery/DISCOVERY-001/v21_end_to_end_audit"

# Pandas treats the literal string "null" as NA by default. The audit uses
# "null" as a scientific trial label, so keep_default_na=False is mandatory.
trials=pd.read_csv(DIR/"end_to_end_trials.csv",keep_default_na=False)
summary=json.loads((DIR/"v21_summary.json").read_text())

null=trials[trials["mode"]=="null"].copy()
if len(null)!=1000:
    raise RuntimeError(f"Expected 1000 null trials, found {len(null)}")
fwer=(pd.to_numeric(null["n_selected"])>0).mean()
if not math.isclose(fwer,summary["library_wide_null_fwer"],abs_tol=1e-15):
    raise RuntimeError(f"FWER mismatch: reconstructed={fwer}, summary={summary['library_wide_null_fwer']}")

expected={
    (1.0,15):(0.8525,0.9450,0.0),
    (1.0,30):(0.7900,0.8950,0.0),
    (1.0,60):(0.2125,0.5950,0.0),
}
for (effect,lag),(truth_exp,top_exp,dist_exp) in expected.items():
    g=trials[(trials["mode"]=="injected")
             &(pd.to_numeric(trials["effect_sd"])==effect)
             &(pd.to_numeric(trials["lag_min"])==lag)]
    if len(g)!=400:
        raise RuntimeError(f"Expected 400 trials for {effect}/{lag}, found {len(g)}")
    truth=g["truth_selected"].map({"True":True,"False":False,True:True,False:False}).mean()
    top=g["unique_top1_correct"].map({"True":True,"False":False,True:True,False:False}).mean()
    dist=g["distractor_coselected"].map({"True":True,"False":False,True:True,False:False}).mean()
    got=(truth,top,dist)
    exp=(truth_exp,top_exp,dist_exp)
    if any(not math.isclose(a,b,abs_tol=1e-15) for a,b in zip(got,exp)):
        raise RuntimeError(f"Cell {effect}/{lag} mismatch: got={got}, expected={exp}")

print("V21_AUDIT_RECONSTRUCTION_PASS")
print(f"library_wide_null_fwer={fwer:.6f}")
for key,val in expected.items():
    print(f"effect={key[0]:.1f}, lag={key[1]} min, truth_selected={val[0]:.4f}, top1={val[1]:.4f}, distractor={val[2]:.4f}")
