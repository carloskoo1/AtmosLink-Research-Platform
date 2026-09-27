#!/usr/bin/env python3
"""Exact pre-freeze v24 sham-schedule feasibility diagnostic.

Uses D_development weather/time only. No RF values, RF availability, RF events,
or D_validation are read. Feasibility is solved as a binary MILP.
"""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import pandas as pd
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix,vstack

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.synthetic_benchmark import robust_z
SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/reviewer_a_v24_sham_feasibility_exact.json"
EXPECTED="eed7df2621f6952b9ea2eaa7524f735a706b69494d3d272fd2dd828b52a97387"
DRIVERS={
 "cu01_local_temp_avg_c__rise":("cu01_local_temp_avg_c","rise",1.5308007671599377,23),
 "sj01_local_temp_avg_c__fall":("sj01_local_temp_avg_c","fall",1.2876641771825945,28),
 "sj01_local_hum_avg_pct__fall":("sj01_local_hum_avg_pct","fall",1.6365945597866016,28),
 "sj01_local_press_hpa__rise":("sj01_local_press_hpa","rise",0.8993210126363124,28),
}
WEATHER=sorted({x[0] for x in DRIVERS.values()})

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):h.update(block)
 return h.hexdigest()
if sha(SOURCE)!=EXPECTED:raise RuntimeError("D_development SHA mismatch")

df=pd.read_csv(SOURCE,usecols=["rf_timestamp_utc"]+WEATHER)
df["t"]=pd.to_datetime(df.rf_timestamp_utc,utc=True,errors="raise")
X=df.set_index("t")[WEATHER].resample("5min").median()
n=len(X)

def peaks(score,thr):
 out=[];last=None
 for t,v in score.dropna().items():
  if v<thr:continue
  if v<score.loc[t-pd.Timedelta("10min"):t+pd.Timedelta("10min")].max():continue
  if last is None or t-last>=pd.Timedelta("360min"):
   out.append(t);last=t
 return pd.DatetimeIndex(out)

events={};indices={}
for name,(col,way,thr,expected) in DRIVERS.items():
 z=robust_z(X[col].diff(3));score=z if way=="rise" else -z
 ev=peaks(score,thr)
 if len(ev)!=expected:raise RuntimeError((name,len(ev),expected))
 events[name]=ev
 indices[name]=np.asarray([X.index.get_loc(t) for t in ev],dtype=int)

weather_complete=X[WEATHER].notna().all(axis=1).to_numpy(bool)
local=X.index.tz_convert("America/Lima")
strata_1h=np.asarray(local.hour,dtype=int)
strata_2h=strata_1h//2
base=np.zeros(n,dtype=bool)
base[24:n-24]=weather_complete[24:n-24]  # fixed 120-min edge margin

all_events=np.unique(np.concatenate(list(indices.values())))

def exclusion_mask(events_to_exclude):
 m=base.copy()
 if events_to_exclude is None:return m
 bad=np.zeros(n,dtype=bool)
 for e in events_to_exclude:
  bad[max(0,e-24):min(n,e+25)]=True
 return m&~bad

def solve(mask,target,strata):
 cand=np.where(mask)[0];m=len(cand)
 for h,c in target.items():
  if int(np.sum(strata[cand]==h))<int(c):
   return {"feasible":False,"reason":"insufficient_stratum_candidates","selected":0}

 rows=[];lo=[];hi=[]
 H=lil_matrix((len(target),m),dtype=float)
 for r,(h,c) in enumerate(sorted(target.items())):
  H[r,np.where(strata[cand]==h)[0]]=1
  lo.append(float(c));hi.append(float(c))
 rows.append(H.tocsr())

 # Any 72-bin (=360-min) inclusive window may contain at most one anchor.
 W=lil_matrix((n-71,m),dtype=float)
 for r,s in enumerate(range(n-71)):
  j=np.where((cand>=s)&(cand<=s+71))[0]
  if len(j):W[r,j]=1
 rows.append(W.tocsr());lo.extend([-np.inf]*(n-71));hi.extend([1.0]*(n-71))

 A=vstack(rows).tocsr()
 res=milp(c=np.zeros(m),integrality=np.ones(m),
          bounds=Bounds(np.zeros(m),np.ones(m)),
          constraints=LinearConstraint(A,np.asarray(lo),np.asarray(hi)),
          options={"time_limit":30})
 selected=0 if res.x is None else int(np.sum(res.x>.5))
 return {"feasible":bool(res.success),"reason":str(res.message),"selected":selected}

result={
 "classification":"pre-freeze design-feasibility diagnostic; weather/time only",
 "source_sha256":EXPECTED,
 "grid_bins":n,
 "rf_columns_read":False,
 "d_validation_accessed":False,
 "constraints":{"edge_margin_min":120,"sham_refractory_min":360},
 "drivers":{}
}
for name,ev in events.items():
 h1=pd.Series(ev.tz_convert("America/Lima").hour).value_counts().sort_index().to_dict()
 h2=pd.Series(ev.tz_convert("America/Lima").hour//2).value_counts().sort_index().to_dict()
 designs={
  "all_driver_exclusion_1h":solve(exclusion_mask(all_events),h1,strata_1h),
  "same_driver_exclusion_1h":solve(exclusion_mask(indices[name]),h1,strata_1h),
  "no_weather_exclusion_1h":solve(exclusion_mask(None),h1,strata_1h),
  "all_driver_exclusion_2h":solve(exclusion_mask(all_events),h2,strata_2h),
  "same_driver_exclusion_2h":solve(exclusion_mask(indices[name]),h2,strata_2h),
  "no_weather_exclusion_2h":solve(exclusion_mask(None),h2,strata_2h),
 }
 result["drivers"][name]={
  "target_event_count":len(ev),
  "hour_histogram_1h":{str(int(k)):int(v) for k,v in h1.items()},
  "hour_histogram_2h":{str(int(k)):int(v) for k,v in h2.items()},
  "designs":designs
 }

OUT.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({
 name:{k:v["feasible"] for k,v in d["designs"].items()}
 for name,d in result["drivers"].items()
},indent=2))
