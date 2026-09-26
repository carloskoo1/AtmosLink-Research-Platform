#!/usr/bin/env python3
"""Post-audit equal-offset RF observation sensitivity, D_development only."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import pandas as pd
from scipy.stats import binom
ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.synthetic_benchmark import (
 RF_FEATURES,robust_z,robust_reference,rf_drop_threshold_from_array,
 detect_drop_indices_fixed_threshold,inject_array)
SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
PROTOCOL=ROOT/"docs/ASDE_REVIEWER_A_PAIRED_OBSERVATION_PROTOCOL.md"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/reviewer_a_paired_observation.json"
EXPECTED="eed7df2621f6952b9ea2eaa7524f735a706b69494d3d272fd2dd828b52a97387"
DRIVERS={"cu01_local_temp_avg_c__rise":(1.5308007671599377,23),
"sj01_local_temp_avg_c__fall":(1.2876641771825945,28),
"sj01_local_hum_avg_pct__fall":(1.6365945597866016,28),
"sj01_local_press_hpa__rise":(0.8993210126363124,28)}
BOUNDS=[("2026-09-01T18:30:52Z","2026-09-04T08:02:17Z"),
("2026-09-04T08:12:19Z","2026-09-07T05:14:26Z"),
("2026-09-07T05:19:27Z","2026-09-09T18:41:57Z"),
("2026-09-09T18:46:58Z","2026-09-13T03:29:49Z")]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE)==EXPECTED
df=pd.read_csv(SOURCE)
df["t"]=pd.to_datetime(df.rf_timestamp_utc,utc=True)
weather=sorted({name.rsplit("__",1)[0] for name in DRIVERS})
X=df.set_index("t")[weather+RF_FEATURES].resample("5min").median()
n=len(X);assert n==3276
driver={}
for name,(threshold,expected) in DRIVERS.items():
 col,way=name.rsplit("__",1);z=robust_z(X[col].diff(3))
 score=z if way=="rise" else -z
 events=[];last=None
 for t,v in score.dropna().items():
  if v<threshold or v<score.loc[t-pd.Timedelta("10min"):t+pd.Timedelta("10min")].max():continue
  if last is None or t-last>=pd.Timedelta("360min"):events.append(t);last=t
 assert len(events)==expected,(name,len(events))
 driver[name]=np.asarray([X.index.get_loc(t) for t in events],dtype=int)
med,scale=robust_reference(X)
base=X[RF_FEATURES].to_numpy(float)
med,scale=med.to_numpy(float),scale.to_numpy(float)
threshold=rf_drop_threshold_from_array(base,med,scale,quantile=.075)
assert abs(threshold-(-.5620817932460992))<1e-12
rf_base=detect_drop_indices_fixed_threshold(base,med,scale,threshold)
q=((base-med)/scale).mean(axis=1)
observable=np.zeros(n,dtype=bool)
observable[3:]=np.isfinite(q[3:])&np.isfinite(q[:-3])
folds=[(int(X.index.searchsorted(pd.Timestamp(a))),
        int(X.index.searchsorted(pd.Timestamp(b),side="right")-1)) for a,b in BOUNDS]
def classify(events,h,rf,paired):
 events=np.asarray(events,dtype=int)
 if paired:
  offsets=np.arange(1,h+1)
  left=events[:,None]-offsets[None,:]
  right=events[:,None]+offsets[None,:]
  inside=(left>=0)&(right<n)
  left=np.clip(left,0,n-1);right=np.clip(right,0,n-1)
  both=inside&observable[left]&observable[right]
  retain=both.sum(axis=1)>=h//2
  rfmask=np.zeros(n,dtype=bool);rfmask[rf]=True
  pre=(both&rfmask[left]).any(axis=1)[retain]
  post=(both&rfmask[right]).any(axis=1)[retain]
  raw_pre=np.sum(observable[left]&inside,axis=1)
  raw_post=np.sum(observable[right]&inside,axis=1)
  kept=events[retain]
  meta={"original_n":len(events),"retained_n":int(retain.sum()),
        "median_paired_offsets":float(np.median(both.sum(axis=1))) if len(events) else None,
        "unequal_raw_coverage":int(np.count_nonzero(raw_pre!=raw_post))}
 else:
  left=np.searchsorted(rf,events-h,side="left")
  middle=np.searchsorted(rf,events,side="left")
  right=np.searchsorted(rf,events+h,side="right")
  pre=middle>left
  post=right>np.searchsorted(rf,events,side="right")
  kept=events
  meta={"original_n":len(events),"retained_n":len(events)}
 po=post&~pre;pr=pre&~post
 x=int(po.sum());y=int(pr.sum());discord=x+y
 pval=float(binom.sf(x-1,discord,.5)) if discord else 1.
 positive=sum(int(np.sum(po[(kept>=a)&(kept<=b)])>
                  np.sum(pr[(kept>=a)&(kept<=b)])) for a,b in folds)
 return {**meta,"post_only":x,"pre_only":y,"discordant":discord,
         "p":pval,"positive_folds":positive}
def evaluate(candidate,rf,paired,details=False):
 selected={m:set() for m in ("M1","M2","M3")}
 low=0;rows={}
 for name,events in candidate.items():
  rows[name]={}
  for h in (6,12,24):
   s=classify(events,h,rf,paired)
   if s["discordant"]<8:low+=1
   if s["p"]<.05/12:
    selected["M1"].add(name)
    if s["discordant"]>=8:
     selected["M2"].add(name)
     if s["positive_folds"]>=3:selected["M3"].add(name)
   if details:rows[name][str(h*5)]=s
 return selected,low,rows
historical,historical_low,historical_rows=evaluate(driver,rf_base,False,True)
paired_base,paired_low,paired_rows=evaluate(driver,rf_base,True,True)
orbit={m:{"historical":0,"paired":0,"both":0,"changed":0} for m in ("M1","M2","M3")}
orbit_low={"historical":0,"paired":0}
for shift in range(72,n-72):
 rotated={name:np.sort((events+shift)%n) for name,events in driver.items()}
 old,old_low,_=evaluate(rotated,rf_base,False)
 new,new_low,_=evaluate(rotated,rf_base,True)
 orbit_low["historical"]+=old_low;orbit_low["paired"]+=new_low
 for m in orbit:
  orbit[m]["historical"]+=bool(old[m]);orbit[m]["paired"]+=bool(new[m])
  orbit[m]["both"]+=bool(old[m]) and bool(new[m])
  orbit[m]["changed"]+=old[m]!=new[m]
assert orbit["M1"]["historical"]==50 and orbit["M3"]["historical"]==50,orbit
print("completed orbit",orbit,flush=True)
injection={}
for truth,events in driver.items():
 for lag in (15,30,60):
  for seed in range(100):
   arr,_=inject_array(base,events,lag//5,1.0,scale,
                      duration_steps=3,activation_prob=.70,seed=420000+seed)
   rf=detect_drop_indices_fixed_threshold(arr,med,scale,threshold)
   for rule,flag in (("historical",False),("paired",True)):
    select,_,_=evaluate(driver,rf,flag)
    for method in ("M1","M3"):
     names=select[method]
     for group in ("pooled",truth):
      key=(rule,method,lag,group)
      if key not in injection:
       injection[key]={"trials":0,"truth_selected":0,
          "exclusive_truth":0,"distractor_coselected":0}
      row=injection[key]
      row["trials"]+=1
      row["truth_selected"]+=truth in names
      row["exclusive_truth"]+=truth in names and len(names)==1
      row["distractor_coselected"]+=any(x!=truth for x in names)
  print("completed injection",truth,lag,flush=True)
nested={}
for (rule,method,lag,group),counts in injection.items():
 entry=nested.setdefault(rule,{}).setdefault(method,{}).setdefault(str(lag),{})
 entry[group]={**counts,**{k+"_rate":v/counts["trials"] for k,v in counts.items() if k!="trials"}}
result={"classification":"post-audit observation-policy sensitivity; no field null calibration",
 "source_sha256":EXPECTED,"protocol_sha256":sha(PROTOCOL),
 "script_sha256":sha(Path(__file__)),"grid_bins":n,
 "observable_detector_bins":int(observable.sum()),
 "rf_events":len(rf_base),"natural_historical":historical_rows,
 "natural_paired":paired_rows,
 "natural_selected_historical":{k:sorted(v) for k,v in historical.items()},
 "natural_selected_paired":{k:sorted(v) for k,v in paired_base.items()},
 "natural_below_8_cells":{"historical":historical_low,"paired":paired_low},
 "orbit_offsets":n-144,"orbit_selection":orbit,
 "orbit_below_8_cells":orbit_low,"injection_1_reference_unit":nested,
 "warning":"This matched-offset rule was frozen after v23; neither its shift orbit nor reused-seed injection is independent field validation."}
OUT.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({"natural_below_8":result["natural_below_8_cells"],
 "orbit":orbit,"orbit_below_8":orbit_low,
 "pooled":{r:{m:{h:v["pooled"] for h,v in bylag.items()}
 for m,bylag in methods.items()} for r,methods in nested.items()}},indent=2))
