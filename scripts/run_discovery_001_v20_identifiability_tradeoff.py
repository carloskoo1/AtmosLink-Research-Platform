#!/usr/bin/env python3
from pathlib import Path
import itertools,json,sys
import numpy as np
import pandas as pd

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.synthetic_benchmark import robust_z,peak_events

SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/v20_identifiability_tradeoff"
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
names=list(scores)

def overlap(a,b,tol_min=60):
    if not a or not b: return 0.0
    tol=pd.Timedelta(minutes=tol_min)
    ma=sum(any(abs(x-y)<=tol for y in b) for x in a)
    mb=sum(any(abs(y-x)<=tol for x in a) for y in b)
    return min(1.0,max(ma,mb)/min(len(a),len(b)))

def maximum_independent_set(valid_names,events,threshold=.35):
    n=len(valid_names)
    bad=set()
    for i,a in enumerate(valid_names):
        for j in range(i+1,n):
            b=valid_names[j]
            if overlap(events[a],events[b],60)>threshold:
                bad.add((i,j))
    best=[]
    # Exact brute force: <=12 candidates => at most 4096 subsets.
    for mask in range(1<<n):
        if mask.bit_count()<=len(best):
            continue
        idx=[i for i in range(n) if mask&(1<<i)]
        ok=True
        for ii,i in enumerate(idx):
            for j in idx[ii+1:]:
                if (min(i,j),max(i,j)) in bad:
                    ok=False; break
            if not ok: break
        if ok:
            best=idx
    return [valid_names[i] for i in best]

rows=[]
designs=[]
for q in [.85,.90,.925,.95,.975]:
    for refractory in [180,240,300,360]:
        events={}
        for name,score in scores.items():
            events[name]=peak_events(score,quantile=q,refractory_min=refractory)[0]
        valid=[n for n in names if len(events[n])>=12]
        mis=maximum_independent_set(valid,events,.35)
        counts=[len(events[n]) for n in mis]
        design={
            "quantile":q,"refractory_min":refractory,
            "valid_driver_count":len(valid),
            "max_identifiable_driver_count":len(mis),
            "min_events_selected":min(counts) if counts else 0,
            "median_events_selected":float(np.median(counts)) if counts else 0,
            "selected_drivers":";".join(mis)
        }
        designs.append(design)
        for n in names:
            rows.append({"quantile":q,"refractory_min":refractory,
                         "driver":n,"events":len(events[n]),
                         "in_max_identifiable_set":n in mis})

d=pd.DataFrame(designs)
# Ranking is descriptive only: maximize separable drivers, then minimum event support.
d=d.sort_values(["max_identifiable_driver_count","min_events_selected","median_events_selected"],
                ascending=[False,False,False])
d.to_csv(OUT/"design_tradeoff.csv",index=False)
pd.DataFrame(rows).to_csv(OUT/"driver_counts_by_design.csv",index=False)

payload={
    "experiment_id":"DISCOVERY-001",
    "version":"20.0-identifiability-power-tradeoff",
    "validation_accessed":False,
    "status":"EXPLORATORY_DESIGN",
    "minimum_events_per_driver":12,
    "proximity_window_min":60,
    "max_allowed_pair_overlap":0.35,
    "designs":d.to_dict(orient="records"),
    "interpretation":"Increasing event sparsity can improve temporal attribution but reduces event support. The design must be frozen based on an explicit identifiability/power criterion before an audit-grade end-to-end benchmark."
}
(OUT/"v20_summary.json").write_text(json.dumps(payload,indent=2,default=str)+"\n")
print(d.head(20).to_string(index=False))
