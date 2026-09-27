#!/usr/bin/env python3
"""Pre-freeze feasibility of joint day-profile sham randomization.

Uses D_development weather/time only. No RF columns and no D_validation.
"""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import pandas as pd

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.synthetic_benchmark import robust_z

SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/reviewer_a_v24_day_profile_feasibility.json"
EXPECTED="eed7df2621f6952b9ea2eaa7524f735a706b69494d3d272fd2dd828b52a97387"
DRIVERS={
 "cu01_local_temp_avg_c__rise":("cu01_local_temp_avg_c","rise",1.5308007671599377,23),
 "sj01_local_temp_avg_c__fall":("sj01_local_temp_avg_c","fall",1.2876641771825945,28),
 "sj01_local_hum_avg_pct__fall":("sj01_local_hum_avg_pct","fall",1.6365945597866016,28),
 "sj01_local_press_hpa__rise":("sj01_local_press_hpa","rise",0.8993210126363124,28),
}
WEATHER=sorted({x[0] for x in DRIVERS.values()})
RNG_SEED=2026092614
PROPOSALS=20000

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):h.update(block)
 return h.hexdigest()
if sha(SOURCE)!=EXPECTED:raise RuntimeError("D_development SHA mismatch")

df=pd.read_csv(SOURCE,usecols=["rf_timestamp_utc"]+WEATHER)
df["t"]=pd.to_datetime(df.rf_timestamp_utc,utc=True,errors="raise")
X=df.set_index("t")[WEATHER].resample("5min").median()

def peaks(score,thr):
 out=[];last=None
 for t,v in score.dropna().items():
  if v<thr:continue
  if v<score.loc[t-pd.Timedelta("10min"):t+pd.Timedelta("10min")].max():continue
  if last is None or t-last>=pd.Timedelta("360min"):
   out.append(t);last=t
 return pd.DatetimeIndex(out)

events={}
for name,(col,way,thr,expected) in DRIVERS.items():
 z=robust_z(X[col].diff(3));score=z if way=="rise" else -z
 ev=peaks(score,thr)
 if len(ev)!=expected:raise RuntimeError((name,len(ev),expected))
 events[name]=ev.tz_convert("America/Lima")

local=X.index.tz_convert("America/Lima")
day_frame=pd.DataFrame(index=local)
day_frame["complete"]=X[WEATHER].notna().all(axis=1).to_numpy()
day_frame["date"]=local.date
stats=day_frame.groupby("date").agg(bins=("complete","size"),good=("complete","sum"))
full_days=[d for d,row in stats.iterrows() if row["bins"]==288 and row["good"]/288>=.95]

profiles={d:{name:[] for name in events} for d in full_days}
for name,ev in events.items():
 for t in ev:
  if t.date() in profiles:
   profiles[t.date()][name].append(int(t.hour*60+t.minute))

rng=np.random.default_rng(RNG_SEED)
valid=0
examples=[]
for _ in range(PROPOSALS):
 perm=np.asarray(full_days,dtype=object).copy()
 rng.shuffle(perm)
 # Joint derangement: every daily weather-event profile moves to a different day.
 if any(perm[i]==full_days[i] for i in range(len(full_days))):
  continue
 moved={name:[] for name in events}
 ok=True
 for src,dst in zip(full_days,perm):
  for name in events:
   for minute in profiles[src][name]:
    t=(pd.Timestamp(dst)+pd.Timedelta(minutes=minute)).tz_localize("America/Lima")
    moved[name].append(t)
 for name,arr in moved.items():
  arr=sorted(arr)
  if len(arr)>1:
   gaps=np.diff(pd.DatetimeIndex(arr).asi8)/1e9/60
   if np.any(gaps<360):
    ok=False;break
 if not ok:continue
 valid+=1
 if len(examples)<3:
  examples.append([[str(a),str(b)] for a,b in zip(full_days,perm)])

result={
 "classification":"pre-freeze joint day-profile sham feasibility; weather/time only",
 "source_sha256":EXPECTED,
 "rf_columns_read":False,
 "d_validation_accessed":False,
 "rng_seed":RNG_SEED,
 "proposals":PROPOSALS,
 "full_local_days":[str(d) for d in full_days],
 "full_day_count":len(full_days),
 "events_in_full_days":{
  name:int(sum(len(profiles[d][name]) for d in full_days)) for name in events
 },
 "valid_joint_derangements":valid,
 "acceptance_fraction":valid/PROPOSALS,
 "constraints":{
  "joint_profile_permutation":True,
  "no_fixed_day_profiles":True,
  "minimum_same_driver_gap_min":360,
  "preserves_exact_local_event_times":True,
  "preserves_within_day_cross_driver_structure":True
 },
 "example_valid_permutations":examples,
 "interpretation":"Constructive feasibility only; not RF calibration or a natural-weather null."
}
OUT.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({
 "full_day_count":len(full_days),
 "events_in_full_days":result["events_in_full_days"],
 "valid_joint_derangements":valid,
 "proposals":PROPOSALS,
 "acceptance_fraction":valid/PROPOSALS
},indent=2))
