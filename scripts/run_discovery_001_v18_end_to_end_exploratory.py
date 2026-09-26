#!/usr/bin/env python3
from pathlib import Path
import json,sys,math
import numpy as np
import pandas as pd

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.synthetic_benchmark import (
    RF_FEATURES,robust_z,peak_events,robust_reference,
    rf_drop_threshold_from_array,detect_drop_indices_fixed_threshold,
    directional_test_indices,inject_array
)

SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
LIB=ROOT/"Results/scientific_discovery/DISCOVERY-001/v17_candidate_library/v17_summary.json"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/v18_end_to_end"
OUT.mkdir(parents=True,exist_ok=True)

VARS=[
    "cu01_local_temp_avg_c","cu01_local_hum_avg_pct",
    "sj01_local_temp_avg_c","sj01_local_hum_avg_pct",
    "sj01_local_press_hpa","sj01_local_wind_speed_ms"
]
df=pd.read_csv(SOURCE)
df["t"]=pd.to_datetime(df["rf_timestamp_utc"],utc=True,errors="raise")
X=df.set_index("t")[VARS+RF_FEATURES].resample("5min").median()

scores={}
for col in VARS:
    z=robust_z(X[col].diff(3))
    scores[f"{col}__rise"]=z
    scores[f"{col}__fall"]=-z

selected=json.load(open(LIB))["selected_drivers"]
driver_events={}
driver_idx={}
for name in selected:
    ev,_=peak_events(scores[name],quantile=.85,refractory_min=180)
    driver_events[name]=ev
    driver_idx[name]=np.asarray([X.index.get_loc(t) for t in ev],dtype=int)

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
ALPHA=.05/(len(selected)*len(HORIZONS))
EFFECTS=[0.5,1.0]
LAGS=[15,30,60]
TRIALS=50

def fold_positive(driver,rf,hsteps):
    pos=0
    for a,b in bounds:
        de=driver[(driver>=a)&(driver<=b)]
        re=rf[(rf>=a-hsteps)&(rf<=b+hsteps)]
        s=directional_test_indices(de,re,hsteps)
        pos+=int(s["post_only"]>s["pre_only"])
    return pos

def search_library(candidate_idx,rf):
    rows=[]
    for name,drv in candidate_idx.items():
        best_p=1.0; passed=False; best_h=None
        for h in HORIZONS:
            hs=h//5
            s=directional_test_indices(drv,rf,hs)
            pos=fold_positive(drv,rf,hs)
            ok=(s["p_value"]<ALPHA and s["discordant"]>=8 and pos>=3)
            if s["p_value"]<best_p:
                best_p=float(s["p_value"]); best_h=h
            passed=passed or ok
        rows.append((name,passed,best_p,best_h))
    rows.sort(key=lambda z:z[2])
    return rows

trials=[]
for truth in selected:
    truth_idx=driver_idx[truth]
    for effect in EFFECTS:
        for lag in LAGS:
            for seed in range(TRIALS):
                sim,_=inject_array(
                    base,truth_idx,lag//5,effect,scale,
                    duration_steps=3,activation_prob=.70,seed=150000+seed
                )
                rf=detect_drop_indices_fixed_threshold(sim,med,scale,frozen_threshold)
                found=search_library(driver_idx,rf)
                selected_names=[x[0] for x in found if x[1]]
                top=found[0][0] if found else None
                trials.append({
                    "mode":"injected","truth_driver":truth,"effect_sd":effect,
                    "lag_min":lag,"seed":seed,
                    "true_selected":truth in selected_names,
                    "top1_correct":top==truth,
                    "n_selected":len(selected_names),
                    "false_driver_selected":any(x!=truth for x in selected_names),
                    "selected_drivers":";".join(selected_names),
                    "top_driver":top,
                    "top_p":found[0][2] if found else np.nan
                })

# Library-wide empirical null: circularly shift all driver sets together.
rng=np.random.default_rng(2026092603)
n=len(X)
for seed in range(500):
    shift=int(rng.integers(72,max(73,n-72)))
    shifted={name:np.sort((idx+shift)%n) for name,idx in driver_idx.items()}
    found=search_library(shifted,baseline_rf)
    selected_names=[x[0] for x in found if x[1]]
    trials.append({
        "mode":"null","truth_driver":"","effect_sd":0.0,"lag_min":np.nan,"seed":seed,
        "true_selected":False,"top1_correct":False,
        "n_selected":len(selected_names),
        "false_driver_selected":len(selected_names)>0,
        "selected_drivers":";".join(selected_names),
        "top_driver":found[0][0] if found else None,
        "top_p":found[0][2] if found else np.nan
    })

res=pd.DataFrame(trials)
res.to_csv(OUT/"end_to_end_trials.csv",index=False)

def wilson(k,n,z=1.96):
    if n==0: return (np.nan,np.nan)
    p=k/n; den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return center-half,center+half

rows=[]
inj=res[res["mode"]=="injected"]
for (effect,lag),g in inj.groupby(["effect_sd","lag_min"]):
    for metric in ["true_selected","top1_correct","false_driver_selected"]:
        k=int(g[metric].sum()); n0=len(g); lo,hi=wilson(k,n0)
        rows.append({"effect_sd":effect,"lag_min":lag,"metric":metric,
                     "trials":n0,"rate":k/n0,"ci95_low":lo,"ci95_high":hi})
summary=pd.DataFrame(rows)
summary.to_csv(OUT/"end_to_end_summary.csv",index=False)

null=res[res["mode"]=="null"]
k=int(null["false_driver_selected"].sum()); nn=len(null); lo,hi=wilson(k,nn)
payload={
    "experiment_id":"DISCOVERY-001",
    "version":"18.0-end-to-end-exploratory",
    "validation_accessed":False,
    "status":"EXPLORATORY_END_TO_END",
    "candidate_library_size":len(selected),
    "horizons_min":HORIZONS,
    "familywise_alpha_per_driver_horizon":ALPHA,
    "effects_sd":EFFECTS,
    "lags_min":LAGS,
    "trials_per_truth_effect_lag":TRIALS,
    "null_trials":nn,
    "library_false_selection_rate":k/nn,
    "library_false_selection_ci95":[lo,hi],
    "important_limit":"Candidate library and benchmark design were developed adaptively on D_development; results are exploratory until protocol is frozen and rerun with reserved seeds.",
    "aggregate":summary.to_dict(orient="records")
}
(OUT/"v18_summary.json").write_text(json.dumps(payload,indent=2,default=str)+"\n")
print(json.dumps(payload,indent=2,default=str))
