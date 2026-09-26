#!/usr/bin/env python3
"""Post-audit RF event-window observability sensitivity on D_development only."""
from pathlib import Path
import hashlib, json, sys
import numpy as np
import pandas as pd
from scipy.stats import binom

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.synthetic_benchmark import (
    RF_FEATURES,robust_z,robust_reference,
    rf_drop_threshold_from_array,detect_drop_indices_fixed_threshold)
SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
PROTOCOL=ROOT/"docs/ASDE_REVIEWER_A_OBSERVABILITY_PROTOCOL.md"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/reviewer_a_observability.json"
EXPECTED="eed7df2621f6952b9ea2eaa7524f735a706b69494d3d272fd2dd828b52a97387"
DRIVERS={"cu01_local_temp_avg_c__rise":(1.5308007671599377,23),
         "sj01_local_temp_avg_c__fall":(1.2876641771825945,28),
         "sj01_local_hum_avg_pct__fall":(1.6365945597866016,28),
         "sj01_local_press_hpa__rise":(0.8993210126363124,28)}
BOUNDS=[("2026-09-01T18:30:52Z","2026-09-04T08:02:17Z"),
        ("2026-09-04T08:12:19Z","2026-09-07T05:14:26Z"),
        ("2026-09-07T05:19:27Z","2026-09-09T18:41:57Z"),
        ("2026-09-09T18:46:58Z","2026-09-13T03:29:49Z")]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE)==EXPECTED
df=pd.read_csv(SOURCE)
df["t"]=pd.to_datetime(df.rf_timestamp_utc,utc=True)
vars_=sorted({x.rsplit("__",1)[0] for x in DRIVERS})
X=df.set_index("t")[vars_+RF_FEATURES].resample("5min").median()
idx={}
for name,(threshold,expected) in DRIVERS.items():
    col,direction=name.rsplit("__",1)
    z=robust_z(X[col].diff(3)); score=z if direction=="rise" else -z
    ev=[]; last=None
    for t,v in score.dropna().items():
        if v<threshold or v<score.loc[t-pd.Timedelta("10min"):t+pd.Timedelta("10min")].max(): continue
        if last is None or t-last>=pd.Timedelta("360min"): ev.append(t);last=t
    assert len(ev)==expected,(name,len(ev))
    idx[name]=np.array([X.index.get_loc(t) for t in ev],dtype=int)
n=len(X);assert n==3276
med,scale=robust_reference(X)
base=X[RF_FEATURES].to_numpy(float)
med,scale=med.to_numpy(float),scale.to_numpy(float)
thr=rf_drop_threshold_from_array(base,med,scale,quantile=.075)
assert abs(thr-(-.5620817932460992))<1e-12
rf=detect_drop_indices_fixed_threshold(base,med,scale,thr)
q=((base-med)/scale).mean(axis=1)
observed=np.zeros(n,dtype=bool)
observed[3:]=np.isfinite(q[3:])&np.isfinite(q[:-3])
prefix=np.r_[0,np.cumsum(observed)]
bounds=[(int(X.index.searchsorted(pd.Timestamp(a))),
         int(X.index.searchsorted(pd.Timestamp(b),side="right")-1)) for a,b in BOUNDS]
def coverage(events,h):
    events=np.asarray(events,dtype=int)
    pre=np.zeros(len(events),dtype=int);post=pre.copy()
    for i,e in enumerate(events):
        a=max(0,e-h);b=min(n,e)
        c=max(0,e+1);d=min(n,e+h+1)
        pre[i]=prefix[b]-prefix[a] if a<b else 0
        post[i]=prefix[d]-prefix[c] if c<d else 0
    return pre,post,(pre==h)&(post==h)
def direction(events,h):
    events=np.asarray(events,dtype=int)
    left=np.searchsorted(rf,events-h,side="left")
    mid=np.searchsorted(rf,events,side="left")
    right=np.searchsorted(rf,events+h,side="right")
    pre=mid>left
    post=right>np.searchsorted(rf,events,side="right")
    po=int(np.count_nonzero(post&~pre));pr=int(np.count_nonzero(pre&~post))
    support=po+pr
    return {"post_only":po,"pre_only":pr,"discordant":support,
            "p":float(binom.sf(po-1,support,.5)) if support else 1.}
def selected(candidate,eligible):
    m1=set();m3=set();low_support=0
    for name,events in candidate.items():
        for h in (6,12,24):
            ev=events
            if eligible:
                _,_,keep=coverage(events,h);ev=events[keep]
            s=direction(ev,h)
            if s["discordant"]<8:low_support+=1
            if s["p"]<.05/12:
                m1.add(name)
                if s["discordant"]>=8:
                    pos=sum((lambda v:v["post_only"]>v["pre_only"])(
                        direction(ev[(ev>=a)&(ev<=b)],h)) for a,b in bounds)
                    if pos>=3:m3.add(name)
    return m1,m3,low_support
details={}
for name,events in idx.items():
    details[name]={}
    for h in (6,12,24):
        pre,post,keep=coverage(events,h)
        details[name][str(h*5)]={"events":len(events),"fully_observed":int(keep.sum()),
            "unequal_observed_bins":int(np.count_nonzero(pre!=post)),
            "mean_pre_observed":float(pre.mean()),"mean_post_observed":float(post.mean()),
            "original":direction(events,h),"complete_window":direction(events[keep],h)}
orig0,orig3,origlow=selected(idx,False)
new0,new3,newlow=selected(idx,True)
counts={"original_m1":0,"original_m3":0,"complete_m1":0,"complete_m3":0,
        "m1_changed":0,"m3_changed":0,"m1_both":0,"m3_both":0}
low_total={"original":0,"complete":0}
retained=[]
for shift in range(72,n-72):
    rotated={name:np.sort((events+shift)%n) for name,events in idx.items()}
    om1,om3,olow=selected(rotated,False)
    cm1,cm3,clow=selected(rotated,True)
    counts["original_m1"]+=bool(om1);counts["original_m3"]+=bool(om3)
    counts["complete_m1"]+=bool(cm1);counts["complete_m3"]+=bool(cm3)
    counts["m1_changed"]+=om1!=cm1;counts["m3_changed"]+=om3!=cm3
    counts["m1_both"]+=bool(om1) and bool(cm1)
    counts["m3_both"]+=bool(om3) and bool(cm3)
    low_total["original"]+=olow;low_total["complete"]+=clow
    for ev in rotated.values():
        for h in (6,12,24):
            retained.append(int(coverage(ev,h)[2].sum()))
assert counts["original_m1"]==50 and counts["original_m3"]==50,counts
result={"scope":"post-audit observation sensitivity; fixed D_development",
        "source_sha256":EXPECTED,"protocol_sha256":sha(PROTOCOL),
        "script_sha256":sha(Path(__file__)),"grid_bins":n,
        "ascertainable_detector_bins":int(observed.sum()),"rf_events":len(rf),
        "event_windows":details,
        "natural_driver_selection":{"original_m1":sorted(orig0),"original_m3":sorted(orig3),
           "complete_m1":sorted(new0),"complete_m3":sorted(new3),
           "original_low_support_cells":origlow,"complete_low_support_cells":newlow},
        "shift_orbit":{"offsets":n-144,"selection_counts":counts,
           "below_8_discordant_cells":low_total,
           "total_driver_horizon_cells":(n-144)*4*3,
           "fully_observed_event_count_per_cell":{"min":int(np.min(retained)),
              "median":float(np.median(retained)),"max":int(np.max(retained))}},
        "warning":"Neither shift orbit nor complete-window analysis establishes exchangeability or calibrated field Type-I error."}
OUT.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
