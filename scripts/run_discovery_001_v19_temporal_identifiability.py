#!/usr/bin/env python3
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.synthetic_benchmark import robust_z,peak_events

SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
LIB=ROOT/"Results/scientific_discovery/DISCOVERY-001/v17_candidate_library/v17_summary.json"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/v19_temporal_identifiability"
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

selected=json.load(open(LIB))["selected_drivers"]
events={}
for name in selected:
    events[name]=peak_events(scores[name],quantile=.85,refractory_min=180)[0]

def proximity_overlap(a,b,tol_min):
    if not a or not b:
        return 0.0
    tol=pd.Timedelta(minutes=tol_min)
    ma=sum(any(abs(x-y)<=tol for y in b) for x in a)
    mb=sum(any(abs(y-x)<=tol for x in a) for y in b)
    return min(1.0,max(ma,mb)/min(len(a),len(b)))

long=[]
for tol in [10,30,60,120]:
    mat=pd.DataFrame(index=selected,columns=selected,dtype=float)
    for a in selected:
        for b in selected:
            v=proximity_overlap(events[a],events[b],tol)
            mat.loc[a,b]=v
            if a<b:
                long.append({"tolerance_min":tol,"driver_a":a,"driver_b":b,"overlap":v})
    mat.to_csv(OUT/f"overlap_{tol}min.csv")

longdf=pd.DataFrame(long)
longdf.to_csv(OUT/"temporal_overlap_long.csv",index=False)

# Connected components under a conservative 60-min overlap graph.
tol=60
threshold=0.35
edges=longdf[(longdf.tolerance_min==tol)&(longdf.overlap>threshold)]
parent={x:x for x in selected}
def find(x):
    while parent[x]!=x:
        parent[x]=parent[parent[x]]
        x=parent[x]
    return x
def union(a,b):
    ra,rb=find(a),find(b)
    if ra!=rb:
        parent[rb]=ra
for _,r in edges.iterrows():
    union(r.driver_a,r.driver_b)
groups={}
for x in selected:
    groups.setdefault(find(x),[]).append(x)
components=list(groups.values())

payload={
    "experiment_id":"DISCOVERY-001",
    "version":"19.0-temporal-identifiability-audit",
    "validation_accessed":False,
    "status":"EXPLORATORY_IDENTIFIABILITY",
    "driver_count":len(selected),
    "proximity_tolerances_min":[10,30,60,120],
    "equivalence_graph":{
        "tolerance_min":tol,
        "overlap_threshold":threshold,
        "components":components,
        "nontrivial_components":[g for g in components if len(g)>1]
    },
    "interpretation":"Drivers linked by substantial temporal proximity are observationally difficult to attribute uniquely under event-window analysis. Such candidates should be treated as an equivalence class until additional independent variation or intervention resolves them."
}
(OUT/"v19_summary.json").write_text(json.dumps(payload,indent=2,default=str)+"\n")
print(json.dumps(payload,indent=2,default=str))
print("\nHighest 60-min overlaps:")
print(edges.sort_values("overlap",ascending=False).head(20).to_string(index=False))
