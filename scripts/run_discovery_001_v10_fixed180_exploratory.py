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
    directional_test_indices,inject_array
)

SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/v10_fixed180"
OUT.mkdir(parents=True,exist_ok=True)

ATM=["sj01_local_temp_avg_c","sj01_local_hum_avg_pct"]
df=pd.read_csv(SOURCE)
df["t"]=pd.to_datetime(df.rf_timestamp_utc,utc=True,errors="raise")
X=df.set_index("t")[ATM+RF_FEATURES].resample("5min").median()
driver_events,_=peak_events(driver_score(X),quantile=.85,refractory_min=180)
driver_idx=np.asarray([X.index.get_loc(t) for t in driver_events],dtype=int)

bounds_time=[
    (pd.Timestamp("2026-09-01T18:30:52Z"),pd.Timestamp("2026-09-04T08:02:17Z")),
    (pd.Timestamp("2026-09-04T08:12:19Z"),pd.Timestamp("2026-09-07T05:14:26Z")),
    (pd.Timestamp("2026-09-07T05:19:27Z"),pd.Timestamp("2026-09-09T18:41:57Z")),
    (pd.Timestamp("2026-09-09T18:46:58Z"),pd.Timestamp("2026-09-13T03:29:49Z")),
]
bounds=[(int(X.index.searchsorted(a)),int(X.index.searchsorted(b,side="right")-1)) for a,b in bounds_time]

med_s,scale_s=robust_reference(X)
med=med_s.to_numpy(float); scale=scale_s.to_numpy(float)
base=X[RF_FEATURES].to_numpy(float)
frozen_threshold=rf_drop_threshold_from_array(base,med,scale,quantile=.075)
baseline_rf=detect_drop_indices_fixed_threshold(base,med,scale,frozen_threshold)

HORIZONS=[30,60,120]
EFFECTS=[0.5,1.0,1.5,2.0]
LAGS=[15,30,60]
TRIALS=50
ALPHA_H=.05/len(HORIZONS)

def fold_positive(driver,rf,hsteps):
    positive=0
    for a,b in bounds:
        de=driver[(driver>=a)&(driver<=b)]
        re=rf[(rf>=a-hsteps)&(rf<=b+hsteps)]
        s=directional_test_indices(de,re,hsteps)
        positive+=int(s["post_only"]>s["pre_only"])
    return positive

def gate(driver,rf,hmin):
    hs=hmin//5
    s=directional_test_indices(driver,rf,hs)
    pos=fold_positive(driver,rf,hs)
    passed=(s["p_value"]<ALPHA_H and s["discordant"]>=8 and pos>=3)
    return bool(passed),float(s["p_value"]),int(pos),int(s["post_only"]),int(s["pre_only"])

rows=[]
for effect in EFFECTS:
    for lag in LAGS:
        for seed in range(TRIALS):
            sim,_=inject_array(base,driver_idx,lag//5,effect,scale,
                               duration_steps=3,activation_prob=.70,seed=30000+seed)
            rf=detect_drop_indices_fixed_threshold(sim,med,scale,frozen_threshold)
            passes=[]
            for h in HORIZONS:
                passed,pv,pos,post,pre=gate(driver_idx,rf,h)
                passes.append(passed)
                rows.append({"mode":"injected","effect_sd":effect,"lag_min":lag,
                             "seed":seed,"horizon_min":h,"p_value":pv,
                             "positive_folds":pos,"post_only":post,"pre_only":pre,
                             "pass_full":passed})
            rows.append({"mode":"injected_any","effect_sd":effect,"lag_min":lag,
                         "seed":seed,"horizon_min":0,"p_value":np.nan,
                         "positive_folds":np.nan,"post_only":np.nan,"pre_only":np.nan,
                         "pass_full":bool(any(passes))})

rng=np.random.default_rng(20260926)
n=len(X)
for trial in range(200):
    shift=int(rng.integers(72,max(73,n-72)))
    shifted=np.sort((driver_idx+shift)%n)
    passes=[]
    for h in HORIZONS:
        passed,pv,pos,post,pre=gate(shifted,baseline_rf,h)
        passes.append(passed)
        rows.append({"mode":"null_shift","effect_sd":0.0,"lag_min":np.nan,
                     "seed":trial,"horizon_min":h,"p_value":pv,
                     "positive_folds":pos,"post_only":post,"pre_only":pre,
                     "pass_full":passed})
    rows.append({"mode":"null_any","effect_sd":0.0,"lag_min":np.nan,
                 "seed":trial,"horizon_min":0,"p_value":np.nan,
                 "positive_folds":np.nan,"post_only":np.nan,"pre_only":np.nan,
                 "pass_full":bool(any(passes))})

res=pd.DataFrame(rows)
res.to_csv(OUT/"benchmark_trials.csv",index=False)

def wilson(k,n,z=1.96):
    if n==0:
        return (np.nan,np.nan)
    p=k/n
    den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return center-half,center+half

surface=[]
sub=res[res["mode"]=="injected"]
for (effect,lag,h),g in sub.groupby(["effect_sd","lag_min","horizon_min"]):
    k=int(g.pass_full.sum())
    n0=len(g)
    lo,hi=wilson(k,n0)
    surface.append({
        "effect_sd":effect,"lag_min":lag,"horizon_min":h,
        "trials":n0,"recovery_rate":k/n0,
        "ci95_low":lo,"ci95_high":hi
    })
surface=pd.DataFrame(surface)
surface.to_csv(OUT/"detection_surface.csv",index=False)

family=[]
for (effect,lag),g in res[res["mode"]=="injected_any"].groupby(["effect_sd","lag_min"]):
    k=int(g.pass_full.sum())
    n0=len(g)
    lo,hi=wilson(k,n0)
    family.append({
        "effect_sd":effect,"lag_min":lag,"trials":n0,
        "familywise_recovery_rate":k/n0,
        "ci95_low":lo,"ci95_high":hi
    })
family=pd.DataFrame(family)
family.to_csv(OUT/"familywise_recovery.csv",index=False)

null=res[res["mode"]=="null_any"]
k=int(null.pass_full.sum())
nn=len(null)
lo,hi=wilson(k,nn)

summary={
    "experiment_id":"DISCOVERY-001",
    "version":"10b.0-frozen-threshold-benchmark",
    "validation_accessed":False,
    "external_replication_accessed":False,
    "frozen_rf_drop_threshold":frozen_threshold,
    "baseline_rf_drop_events":len(baseline_rf),
    "familywise_null_trials":nn,
    "familywise_false_positive_rate":k/nn,
    "familywise_false_positive_ci95":[lo,hi],
    "familywise_recovery":family.to_dict(orient="records"),
    "surface":surface.to_dict(orient="records"),
    "design_note":"RF drop threshold learned once from unmodified development data and frozen before all injections."
}
(OUT/"v10_summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
print(json.dumps(summary,indent=2,default=str))
