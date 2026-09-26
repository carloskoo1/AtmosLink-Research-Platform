#!/usr/bin/env python3
from pathlib import Path
import json,sys,math
import numpy as np
import pandas as pd

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.synthetic_benchmark import (
    RF_FEATURES,driver_score,peak_events,robust_reference,
    directional_test_indices
)

SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
STRESS=ROOT/"Results/scientific_discovery/DISCOVERY-001/v15_morphology_stress/morphology_recovery.csv"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/v16b_multiview"
OUT.mkdir(parents=True,exist_ok=True)

ATM=["sj01_local_temp_avg_c","sj01_local_hum_avg_pct"]
df=pd.read_csv(SOURCE); df["t"]=pd.to_datetime(df.rf_timestamp_utc,utc=True)
X=df.set_index("t")[ATM+RF_FEATURES].resample("5min").median()
driver,_=peak_events(driver_score(X),quantile=.85,refractory_min=180)
driver_idx=np.asarray([X.index.get_loc(t) for t in driver],dtype=int)
med_s,scale_s=robust_reference(X)
med=med_s.to_numpy(float); scale=scale_s.to_numpy(float)
base=X[RF_FEATURES].to_numpy(float)
IDX={name:i for i,name in enumerate(RF_FEATURES)}
VIEWS={
 "global":list(range(6)),
 "rssi":[IDX["dl_rssi_dbm"],IDX["ul_rssi_dbm"]],
 "snr":[IDX["dl_snr_db"],IDX["ul_snr_db"]],
 "mcs":[IDX["dl_mcs"],IDX["ul_mcs"]],
}
bounds_time=[
(pd.Timestamp("2026-09-01T18:30:52Z"),pd.Timestamp("2026-09-04T08:02:17Z")),
(pd.Timestamp("2026-09-04T08:12:19Z"),pd.Timestamp("2026-09-07T05:14:26Z")),
(pd.Timestamp("2026-09-07T05:19:27Z"),pd.Timestamp("2026-09-09T18:41:57Z")),
(pd.Timestamp("2026-09-09T18:46:58Z"),pd.Timestamp("2026-09-13T03:29:49Z"))]
bounds=[(int(X.index.searchsorted(a)),int(X.index.searchsorted(b,side="right")-1)) for a,b in bounds_time]

def view_quality(arr,cols):
    cols=np.asarray(cols,dtype=int)
    return ((arr[:,cols]-med[cols])/scale[cols]).mean(axis=1)

def view_threshold(cols):
    q=view_quality(base,cols)
    dq=np.full(len(q),np.nan); dq[3:]=q[3:]-q[:-3]
    return float(np.nanquantile(dq,.075))

THRESHOLDS={v:view_threshold(c) for v,c in VIEWS.items()}

def view_events(arr,cols,thr,refractory=6):
    q=view_quality(arr,cols)
    dq=np.full(len(q),np.nan); dq[3:]=q[3:]-q[:-3]
    cand=np.flatnonzero(dq<=thr)
    out=[]; last=-10**9
    for i in cand:
        if i-last>=refractory:
            out.append(int(i)); last=int(i)
    return np.asarray(out,dtype=int)

def fold_positive(rf,hsteps):
    pos=0
    for a,b in bounds:
        de=driver_idx[(driver_idx>=a)&(driver_idx<=b)]
        re=rf[(rf>=a-hsteps)&(rf<=b+hsteps)]
        s=directional_test_indices(de,re,hsteps)
        pos+=int(s["post_only"]>s["pre_only"])
    return pos

ALPHA=.05/(len(VIEWS)*3)
def multiview_gate(arr):
    hits=[]
    for view,cols in VIEWS.items():
        rf=view_events(arr,cols,THRESHOLDS[view])
        for h in [30,60,120]:
            hs=h//5; s=directional_test_indices(driver_idx,rf,hs)
            pos=fold_positive(rf,hs)
            if s["p_value"]<ALPHA and s["discordant"]>=8 and pos>=3:
                hits.append((view,h,float(s["p_value"]),pos))
    return hits

MORPH={
 "joint_step15":list(range(6)),
 "snr_only_step15":VIEWS["snr"],
 "rssi_only_step15":VIEWS["rssi"],
 "mcs_only_step15":VIEWS["mcs"],
}
def inject(cols,lag,effect,seed):
    rng=np.random.default_rng(seed); arr=np.array(base,copy=True)
    cols=np.asarray(cols,dtype=int)
    for e in driver_idx:
        if rng.random()>.70: continue
        s=e+lag//5; ee=min(len(arr),s+3)
        if s<len(arr): arr[s:ee,cols]-=effect*scale[cols]
    return arr

rows=[]
for name,cols in MORPH.items():
    for lag in [15,30,60]:
        for seed in range(100):
            arr=inject(cols,lag,1.0,150000+seed)
            hits=multiview_gate(arr)
            rows.append({"mode":"injected","morphology":name,"lag_min":lag,
                         "seed":seed,"detected":bool(hits),
                         "hit_views":";".join(sorted(set(h[0] for h in hits)))})
rng=np.random.default_rng(2026092603); n=len(base)
for seed in range(500):
    shift=int(rng.integers(72,max(73,n-72)))
    shifted=np.sort((driver_idx+shift)%n)
    original=driver_idx.copy(); driver_idx[:]=shifted
    hits=multiview_gate(base)
    driver_idx[:]=original
    rows.append({"mode":"null","morphology":"null_shift","lag_min":np.nan,
                 "seed":seed,"detected":bool(hits),
                 "hit_views":";".join(sorted(set(h[0] for h in hits)))})
res=pd.DataFrame(rows); res.to_csv(OUT/"multiview_trials.csv",index=False)

def wilson(k,n,z=1.96):
    p=k/n; den=1+z*z/n
    c=(p+z*z/(2*n))/den
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return c-h,c+h
summary=[]
for (mode,morph,lag),g in res.groupby(["mode","morphology","lag_min"],dropna=False):
    k=int(g.detected.sum()); nn=len(g); lo,hi=wilson(k,nn)
    summary.append({"mode":mode,"morphology":morph,"lag_min":lag,
                    "trials":nn,"rate":k/nn,"ci95_low":lo,"ci95_high":hi})
s=pd.DataFrame(summary); s.to_csv(OUT/"multiview_summary.csv",index=False)
payload={"version":"16b.0-multiview-exploratory","validation_accessed":False,
         "alpha_per_view_horizon":ALPHA,"thresholds":THRESHOLDS,
         "summary":s.to_dict(orient="records")}
(OUT/"v16_summary.json").write_text(json.dumps(payload,indent=2,default=str)+"\n")
print(s.to_string(index=False))
