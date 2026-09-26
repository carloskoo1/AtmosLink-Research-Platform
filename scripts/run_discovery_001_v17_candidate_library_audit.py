#!/usr/bin/env python3
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.synthetic_benchmark import robust_z,peak_events

SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/v17_candidate_library"
OUT.mkdir(parents=True,exist_ok=True)

VARS=[
    "cu01_local_temp_avg_c","cu01_local_hum_avg_pct",
    "sj01_local_temp_avg_c","sj01_local_hum_avg_pct",
    "sj01_local_press_hpa","sj01_local_wind_speed_ms"
]
df=pd.read_csv(SOURCE)
df["t"]=pd.to_datetime(df["rf_timestamp_utc"],utc=True,errors="raise")
X=df.set_index("t")[VARS].resample("5min").median()

scores={}
for col in VARS:
    z=robust_z(X[col].diff(3))
    scores[f"{col}__rise"]=z
    scores[f"{col}__fall"]=-z
scores["sj01_warming_drying"]=(robust_z(X["sj01_local_temp_avg_c"].diff(3))-robust_z(X["sj01_local_hum_avg_pct"].diff(3)))/np.sqrt(2)
scores["sj01_cooling_humidifying"]=-scores["sj01_warming_drying"]

events={}
rows=[]
for name,score in scores.items():
    ev,thr=peak_events(score,quantile=.85,refractory_min=180)
    events[name]=ev
    rows.append({"driver":name,"events":len(ev),"threshold":thr})

def overlap(a,b,tol_min=10):
    if not a or not b:
        return 0.0
    tol=pd.Timedelta(minutes=tol_min)
    ma=sum(any(abs(x-y)<=tol for y in b) for x in a)
    mb=sum(any(abs(y-x)<=tol for x in a) for y in b)
    # symmetric overlap coefficient normalized by smaller event set
    return min(1.0,max(ma,mb)/min(len(a),len(b)))

names=list(events)
mat=pd.DataFrame(index=names,columns=names,dtype=float)
for a in names:
    for b in names:
        mat.loc[a,b]=overlap(events[a],events[b])
mat.to_csv(OUT/"driver_event_overlap.csv")
pd.DataFrame(rows).to_csv(OUT/"driver_event_counts.csv",index=False)

# Greedy identifiable library: retain drivers with <=0.35 event overlap to all selected drivers.
ordered=sorted(names,key=lambda n:(-len(events[n]),n))
selected=[]
for name in ordered:
    if len(events[name])<20:
        continue
    if all(mat.loc[name,s]<=0.35 for s in selected):
        selected.append(name)

payload={
    "experiment_id":"DISCOVERY-001",
    "version":"17.0-candidate-library-audit",
    "validation_accessed":False,
    "status":"EXPLORATORY_LIBRARY_DESIGN",
    "candidate_driver_count":len(names),
    "identifiable_driver_count":len(selected),
    "overlap_tolerance_minutes":10,
    "max_pair_overlap_for_identifiable_library":0.35,
    "selected_drivers":selected,
    "event_counts":rows
}
(OUT/"v17_summary.json").write_text(json.dumps(payload,indent=2,default=str)+"\n")
print(json.dumps(payload,indent=2,default=str))
