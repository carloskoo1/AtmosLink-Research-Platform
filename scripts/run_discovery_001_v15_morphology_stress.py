#!/usr/bin/env python3
from pathlib import Path
import json,sys,math
import numpy as np
import pandas as pd

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.synthetic_benchmark import (
    RF_FEATURES,driver_score,peak_events,robust_reference,
    rf_drop_threshold_from_array,detect_drop_indices_fixed_threshold,
    directional_test_indices
)

SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/v15_morphology_stress"
OUT.mkdir(parents=True,exist_ok=True)

ATM=["sj01_local_temp_avg_c","sj01_local_hum_avg_pct"]
df=pd.read_csv(SOURCE); df["t"]=pd.to_datetime(df.rf_timestamp_utc,utc=True)
X=df.set_index("t")[ATM+RF_FEATURES].resample("5min").median()
driver,_=peak_events(driver_score(X),quantile=.85,refractory_min=180)
driver_idx=np.asarray([X.index.get_loc(t) for t in driver],dtype=int)
med_s,scale_s=robust_reference(X)
med=med_s.to_numpy(float); scale=scale_s.to_numpy(float)
base=X[RF_FEATURES].to_numpy(float)
threshold=rf_drop_threshold_from_array(base,med,scale,.075)

bounds_time=[
(pd.Timestamp("2026-09-01T18:30:52Z"),pd.Timestamp("2026-09-04T08:02:17Z")),
(pd.Timestamp("2026-09-04T08:12:19Z"),pd.Timestamp("2026-09-07T05:14:26Z")),
(pd.Timestamp("2026-09-07T05:19:27Z"),pd.Timestamp("2026-09-09T18:41:57Z")),
(pd.Timestamp("2026-09-09T18:46:58Z"),pd.Timestamp("2026-09-13T03:29:49Z"))]
bounds=[(int(X.index.searchsorted(a)),int(X.index.searchsorted(b,side="right")-1)) for a,b in bounds_time]

IDX={name:i for i,name in enumerate(RF_FEATURES)}
MORPHOLOGIES={
    "joint_step15":{"cols":list(range(6)),"shape":"step","duration":3},
    "snr_only_step15":{"cols":[IDX["dl_snr_db"],IDX["ul_snr_db"]],"shape":"step","duration":3},
    "rssi_only_step15":{"cols":[IDX["dl_rssi_dbm"],IDX["ul_rssi_dbm"]],"shape":"step","duration":3},
    "mcs_only_step15":{"cols":[IDX["dl_mcs"],IDX["ul_mcs"]],"shape":"step","duration":3},
    "joint_ramp30":{"cols":list(range(6)),"shape":"ramp","duration":6},
    "joint_sustained60":{"cols":list(range(6)),"shape":"step","duration":12},
}

def inject(base,event_idx,lag_steps,effect_sd,spec,seed):
    rng=np.random.default_rng(seed); arr=np.array(base,copy=True)
    activated=0
    cols=np.asarray(spec["cols"],dtype=int)
    for e in event_idx:
        if rng.random()>.70: continue
        s=e+lag_steps
        if s>=len(arr): continue
        dur=spec["duration"]; ee=min(len(arr),s+dur)
        if spec["shape"]=="step":
            weights=np.ones(ee-s)
        else:
            weights=np.linspace(1/max(1,ee-s),1,ee-s)
        for j,w in enumerate(weights):
            arr[s+j,cols]-=effect_sd*w*scale[cols]
        activated+=1
    return arr,activated

def fold_positive(rf_idx,hsteps):
    pos=0
    for a,b in bounds:
        de=driver_idx[(driver_idx>=a)&(driver_idx<=b)]
        re=rf_idx[(rf_idx>=a-hsteps)&(rf_idx<=b+hsteps)]
        st=directional_test_indices(de,re,hsteps)
        pos+=int(st["post_only"]>st["pre_only"])
    return pos

def gate(rf_idx,hmin):
    hs=hmin//5
    st=directional_test_indices(driver_idx,rf_idx,hs)
    pos=fold_positive(rf_idx,hs)
    return bool(st["p_value"]<(.05/3) and st["discordant"]>=8 and pos>=3)

TRIALS=100
rows=[]
for name,spec in MORPHOLOGIES.items():
    for effect in [0.5,1.0,1.5,2.0]:
        for lag in [15,30,60]:
            for seed in range(TRIALS):
                sim,activated=inject(base,driver_idx,lag//5,effect,spec,120000+seed)
                rf=detect_drop_indices_fixed_threshold(sim,med,scale,threshold)
                passed=any(gate(rf,h) for h in [30,60,120])
                rows.append({"morphology":name,"effect_sd":effect,"lag_min":lag,
                             "seed":seed,"activated":activated,"detected":passed})

res=pd.DataFrame(rows)
res.to_csv(OUT/"morphology_trials.csv",index=False)

def wilson(k,n,z=1.96):
    p=k/n; den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return center-half,center+half

summary=[]
for (m,e,l),g in res.groupby(["morphology","effect_sd","lag_min"]):
    k=int(g.detected.sum()); n=len(g); lo,hi=wilson(k,n)
    summary.append({"morphology":m,"effect_sd":e,"lag_min":l,
                    "trials":n,"recovery_rate":k/n,"ci95_low":lo,"ci95_high":hi})
s=pd.DataFrame(summary)
s.to_csv(OUT/"morphology_recovery.csv",index=False)
payload={
 "experiment_id":"DISCOVERY-001",
 "version":"15.0-morphology-stress-exploratory",
 "validation_accessed":False,
 "protocol_status":"EXPLORATORY_STRESS_TEST",
 "fixed_rf_drop_threshold":threshold,
 "driver_refractory_min":180,
 "trials_per_cell":TRIALS,
 "results":s.to_dict(orient="records")
}
(OUT/"v15_summary.json").write_text(json.dumps(payload,indent=2,default=str)+"\n")
print(s[(s.effect_sd==1.0)].to_string(index=False))
