#!/usr/bin/env python3
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.synthetic_benchmark import (
    RF_FEATURES,driver_score,peak_events,robust_reference,
    detect_drop_indices_from_array,directional_test_indices,inject_array
)

SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/v7"
OUT.mkdir(parents=True,exist_ok=True)

ATM=["sj01_local_temp_avg_c","sj01_local_hum_avg_pct"]
df=pd.read_csv(SOURCE)
df["t"]=pd.to_datetime(df["rf_timestamp_utc"],utc=True,errors="raise")
X=df.set_index("t")[ATM+RF_FEATURES].resample("5min").median()
driver_events,driver_threshold=peak_events(driver_score(X),quantile=.85,refractory_min=60)
driver_idx=np.asarray([X.index.get_loc(t) for t in driver_events],dtype=int)

bounds_time=[
    (pd.Timestamp("2026-09-01T18:30:52Z"),pd.Timestamp("2026-09-04T08:02:17Z")),
    (pd.Timestamp("2026-09-04T08:12:19Z"),pd.Timestamp("2026-09-07T05:14:26Z")),
    (pd.Timestamp("2026-09-07T05:19:27Z"),pd.Timestamp("2026-09-09T18:41:57Z")),
    (pd.Timestamp("2026-09-09T18:46:58Z"),pd.Timestamp("2026-09-13T03:29:49Z")),
]
bounds_idx=[]
for a,b in bounds_time:
    ia=int(X.index.searchsorted(a,side="left"))
    ib=int(X.index.searchsorted(b,side="right")-1)
    bounds_idx.append((ia,ib))

rf_med_s,rf_scale_s=robust_reference(X)
rf_med=rf_med_s.to_numpy(dtype=float)
rf_scale=rf_scale_s.to_numpy(dtype=float)
base=X[RF_FEATURES].to_numpy(dtype=float)
baseline_rf_idx,baseline_drop_threshold=detect_drop_indices_from_array(
    base,rf_med,rf_scale,quantile=.075,refractory_steps=6
)

HORIZON_STEPS=12
EFFECTS=[0.5,1.0,1.5,2.0]
LAGS=[15,30,60]
TRIALS=50

def fold_stats(driver,rf):
    positive=nonnegative=0
    details=[]
    for a,b in bounds_idx:
        de=driver[(driver>=a)&(driver<=b)]
        re=rf[(rf>=a-HORIZON_STEPS)&(rf<=b+HORIZON_STEPS)]
        s=directional_test_indices(de,re,HORIZON_STEPS)
        details.append(s)
        positive+=int(s["post_only"]>s["pre_only"])
        nonnegative+=int(s["post_only"]>=s["pre_only"])
    return details,positive,nonnegative

rows=[]
for effect in EFFECTS:
    for lag in LAGS:
        lag_steps=lag//5
        for seed in range(TRIALS):
            sim,activated=inject_array(
                base,driver_idx,lag_steps,effect,rf_scale,
                duration_steps=3,activation_prob=.70,seed=10000+seed
            )
            rf_idx,_=detect_drop_indices_from_array(
                sim,rf_med,rf_scale,quantile=.075,refractory_steps=6
            )
            overall=directional_test_indices(driver_idx,rf_idx,HORIZON_STEPS)
            _,pos,nonneg=fold_stats(driver_idx,rf_idx)
            detected=(overall["p_value"]<.05 and overall["discordant"]>=8 and pos>=3)
            rows.append({
                "mode":"injected","effect_sd":effect,"lag_min":lag,"seed":seed,
                "activated_events":len(activated),"detected_rf_events":len(rf_idx),
                "overall_p":overall["p_value"],"post_only":overall["post_only"],
                "pre_only":overall["pre_only"],"discordant":overall["discordant"],
                "positive_folds":pos,"nonnegative_folds":nonneg,
                "detected":bool(detected),
            })

rng=np.random.default_rng(20260926)
n=len(X)
for trial in range(200):
    shift=int(rng.integers(72,max(73,n-72)))
    shifted=(driver_idx+shift)%n
    shifted=np.sort(shifted)
    overall=directional_test_indices(shifted,baseline_rf_idx,HORIZON_STEPS)
    _,pos,nonneg=fold_stats(shifted,baseline_rf_idx)
    detected=(overall["p_value"]<.05 and overall["discordant"]>=8 and pos>=3)
    rows.append({
        "mode":"null_shift","effect_sd":0.0,"lag_min":np.nan,"seed":trial,
        "activated_events":0,"detected_rf_events":len(baseline_rf_idx),
        "overall_p":overall["p_value"],"post_only":overall["post_only"],
        "pre_only":overall["pre_only"],"discordant":overall["discordant"],
        "positive_folds":pos,"nonnegative_folds":nonneg,
        "detected":bool(detected),
    })

results=pd.DataFrame(rows)
results.to_csv(OUT/"benchmark_trials.csv",index=False)
inj=results[results["mode"]=="injected"]
power=(inj.groupby(["effect_sd","lag_min"])
       .agg(trials=("detected","size"),
            recovery_rate=("detected","mean"),
            median_p=("overall_p","median"),
            median_post_only=("post_only","median"),
            median_pre_only=("pre_only","median"),
            median_positive_folds=("positive_folds","median"),
            median_activated_events=("activated_events","median"))
       .reset_index())
power.to_csv(OUT/"benchmark_power.csv",index=False)
null=results[results["mode"]=="null_shift"]

summary={
    "experiment_id":"DISCOVERY-001",
    "version":"7.0-synthetic-ground-truth-benchmark",
    "validation_accessed":False,
    "external_replication_accessed":False,
    "source":"prevalidation development snapshot only",
    "driver_definition":"top-15% local peaks of robust 15-min SJ01 warming-minus-humidity-drop score, 60-min refractory",
    "driver_events_total":len(driver_idx),
    "driver_events_by_fold":[int(((driver_idx>=a)&(driver_idx<=b)).sum()) for a,b in bounds_idx],
    "driver_threshold":driver_threshold,
    "baseline_rf_drop_events":len(baseline_rf_idx),
    "injection":{
        "effect_sd":EFFECTS,"lags_min":LAGS,"duration_min":15,
        "activation_probability":0.70,"trials_per_cell":TRIALS
    },
    "detection_gate":"one-sided exact p<0.05, >=8 discordant events, positive post>pre direction in >=3/4 temporal folds",
    "empirical_null_trials":len(null),
    "empirical_false_positive_rate":float(null["detected"].mean()),
    "power_table":power.to_dict(orient="records"),
}
(OUT/"v7_summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
print(json.dumps(summary,indent=2,default=str))
