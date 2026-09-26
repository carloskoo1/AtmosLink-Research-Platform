#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,math,subprocess,sys
import numpy as np
import pandas as pd

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.synthetic_benchmark import (
    RF_FEATURES,robust_z,robust_reference,
    rf_drop_threshold_from_array,detect_drop_indices_fixed_threshold,
    directional_test_indices,inject_array
)

SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
PROTOCOL=ROOT/"docs/ASDE_END_TO_END_BENCHMARK_PROTOCOL.md"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/v21_end_to_end_audit"

EXPECTED_SOURCE_SHA="eed7df2621f6952b9ea2eaa7524f735a706b69494d3d272fd2dd828b52a97387"
EXPECTED_RF_THRESHOLD=-0.5620817932460992
DRIVERS={
    "cu01_local_temp_avg_c__rise":(1.5308007671599377,23),
    "sj01_local_temp_avg_c__fall":(1.2876641771825945,28),
    "sj01_local_hum_avg_pct__fall":(1.6365945597866016,28),
    "sj01_local_press_hpa__rise":(0.8993210126363124,28),
}

VARS=sorted({name.rsplit("__",1)[0] for name in DRIVERS})
HORIZONS=[30,60,120]
EFFECTS=[0.5,1.0,1.5]
LAGS=[15,30,60]
TRIALS=100
NULL_TRIALS=1000
ALPHA=.05/(len(DRIVERS)*len(HORIZONS))

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def git_state():
    status=subprocess.check_output(
        ["git","status","--porcelain"],cwd=ROOT,text=True
    )
    if status.strip():
        raise RuntimeError("Audit refused: Git working tree is not clean.")
    return subprocess.check_output(
        ["git","rev-parse","HEAD"],cwd=ROOT,text=True
    ).strip()

def fixed_peaks(score,threshold,refractory_min=360):
    events=[]; last=None
    for t,v in score.dropna().items():
        if v<threshold: continue
        local=score.loc[t-pd.Timedelta("10min"):t+pd.Timedelta("10min")]
        if v<local.max(): continue
        if last is None or t-last>=pd.Timedelta(minutes=refractory_min):
            events.append(t); last=t
    return events

def proximity_overlap(a,b,tol_min=60):
    tol=pd.Timedelta(minutes=tol_min)
    ma=sum(any(abs(x-y)<=tol for y in b) for x in a)
    mb=sum(any(abs(y-x)<=tol for x in a) for y in b)
    return min(1.0,max(ma,mb)/min(len(a),len(b)))

commit=git_state()
source_sha=sha256(SOURCE)
if source_sha!=EXPECTED_SOURCE_SHA:
    raise RuntimeError(f"Source SHA mismatch: {source_sha}")

df=pd.read_csv(SOURCE)
df["t"]=pd.to_datetime(df["rf_timestamp_utc"],utc=True,errors="raise")
X=df.set_index("t")[VARS+RF_FEATURES].resample("5min").median()

driver_events={}
driver_idx={}
for name,(threshold,expected_n) in DRIVERS.items():
    col,direction=name.rsplit("__",1)
    z=robust_z(X[col].diff(3))
    score=z if direction=="rise" else -z
    ev=fixed_peaks(score,threshold,360)
    if len(ev)!=expected_n:
        raise RuntimeError(f"{name}: expected {expected_n} events, got {len(ev)}")
    driver_events[name]=ev
    driver_idx[name]=np.asarray([X.index.get_loc(t) for t in ev],dtype=int)

for i,a in enumerate(DRIVERS):
    for b in list(DRIVERS)[i+1:]:
        ov=proximity_overlap(driver_events[a],driver_events[b],60)
        if ov>0.35+1e-12:
            raise RuntimeError(f"Frozen library overlap violation {a} vs {b}: {ov}")

bounds_time=[
    (pd.Timestamp("2026-09-01T18:30:52Z"),pd.Timestamp("2026-09-04T08:02:17Z")),
    (pd.Timestamp("2026-09-04T08:12:19Z"),pd.Timestamp("2026-09-07T05:14:26Z")),
    (pd.Timestamp("2026-09-07T05:19:27Z"),pd.Timestamp("2026-09-09T18:41:57Z")),
    (pd.Timestamp("2026-09-09T18:46:58Z"),pd.Timestamp("2026-09-13T03:29:49Z")),
]
bounds=[(int(X.index.searchsorted(a)),int(X.index.searchsorted(b,side="right")-1))
        for a,b in bounds_time]

med_s,scale_s=robust_reference(X)
med=med_s.to_numpy(float); scale=scale_s.to_numpy(float)
base=X[RF_FEATURES].to_numpy(float)
rf_threshold=rf_drop_threshold_from_array(base,med,scale,quantile=.075)
if not math.isclose(rf_threshold,EXPECTED_RF_THRESHOLD,rel_tol=0,abs_tol=1e-12):
    raise RuntimeError(f"RF threshold mismatch: {rf_threshold}")
baseline_rf=detect_drop_indices_fixed_threshold(base,med,scale,rf_threshold)

def fold_positive(driver,rf,hsteps):
    positive=0
    for a,b in bounds:
        de=driver[(driver>=a)&(driver<=b)]
        re=rf[(rf>=a-hsteps)&(rf<=b+hsteps)]
        s=directional_test_indices(de,re,hsteps)
        positive+=int(s["post_only"]>s["pre_only"])
    return positive

def search_library(candidate_idx,rf):
    result=[]
    for name,drv in candidate_idx.items():
        horizon_rows=[]
        selected=False
        for h in HORIZONS:
            hs=h//5
            s=directional_test_indices(drv,rf,hs)
            pos=fold_positive(drv,rf,hs)
            passed=bool(s["p_value"]<ALPHA and s["discordant"]>=8 and pos>=3)
            selected=selected or passed
            horizon_rows.append((h,float(s["p_value"]),int(pos),passed))
        min_p=min(r[1] for r in horizon_rows)
        result.append({"driver":name,"selected":selected,"min_p":min_p,
                       "horizons":horizon_rows})
    result.sort(key=lambda r:(r["min_p"],r["driver"]))
    min_p=result[0]["min_p"]
    tied=[r["driver"] for r in result if r["min_p"]==min_p]
    unique_top=tied[0] if len(tied)==1 else None
    return result,unique_top,tied

trial_rows=[]
for truth,truth_idx in driver_idx.items():
    for effect in EFFECTS:
        for lag in LAGS:
            for seed in range(TRIALS):
                sim,activated=inject_array(
                    base,truth_idx,lag//5,effect,scale,
                    duration_steps=3,activation_prob=.70,seed=310000+seed
                )
                rf=detect_drop_indices_fixed_threshold(sim,med,scale,rf_threshold)
                found,unique_top,tied=search_library(driver_idx,rf)
                selected_names=[r["driver"] for r in found if r["selected"]]
                truth_selected=truth in selected_names
                distractor=any(x!=truth for x in selected_names)
                trial_rows.append({
                    "mode":"injected","truth_driver":truth,"effect_sd":effect,
                    "lag_min":lag,"seed":seed,"activated_events":len(activated),
                    "detected_rf_events":len(rf),
                    "truth_selected":truth_selected,
                    "exclusive_truth_selected":bool(truth_selected and not distractor),
                    "unique_top1_correct":unique_top==truth,
                    "ranking_ambiguous":len(tied)>1,
                    "distractor_coselected":distractor,
                    "n_selected":len(selected_names),
                    "selected_drivers":";".join(selected_names),
                    "unique_top_driver":unique_top or "",
                    "top_tied_drivers":";".join(tied),
                    "truth_min_p":next(r["min_p"] for r in found if r["driver"]==truth),
                    "global_min_p":found[0]["min_p"]
                })

rng=np.random.default_rng(2026092605)
n=len(X)
for seed in range(NULL_TRIALS):
    shift=int(rng.integers(72,max(73,n-72)))
    shifted={name:np.sort((idx+shift)%n) for name,idx in driver_idx.items()}
    found,unique_top,tied=search_library(shifted,baseline_rf)
    selected_names=[r["driver"] for r in found if r["selected"]]
    trial_rows.append({
        "mode":"null","truth_driver":"","effect_sd":0.0,"lag_min":np.nan,
        "seed":seed,"activated_events":0,"detected_rf_events":len(baseline_rf),
        "truth_selected":False,"exclusive_truth_selected":False,
        "unique_top1_correct":False,"ranking_ambiguous":len(tied)>1,
        "distractor_coselected":len(selected_names)>0,
        "n_selected":len(selected_names),
        "selected_drivers":";".join(selected_names),
        "unique_top_driver":unique_top or "",
        "top_tied_drivers":";".join(tied),
        "truth_min_p":np.nan,"global_min_p":found[0]["min_p"]
    })

res=pd.DataFrame(trial_rows)

def wilson(k,n,z=1.96):
    if n==0: return (np.nan,np.nan)
    p=k/n; den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return center-half,center+half

metrics=[
    "truth_selected","exclusive_truth_selected","unique_top1_correct",
    "ranking_ambiguous","distractor_coselected"
]
aggregate=[]
inj=res[res["mode"]=="injected"]
for (effect,lag),g in inj.groupby(["effect_sd","lag_min"]):
    for metric in metrics:
        k=int(g[metric].sum()); n0=len(g); lo,hi=wilson(k,n0)
        aggregate.append({"scope":"aggregate","truth_driver":"ALL",
                          "effect_sd":effect,"lag_min":lag,"metric":metric,
                          "trials":n0,"rate":k/n0,"ci95_low":lo,"ci95_high":hi})
    aggregate.append({"scope":"aggregate","truth_driver":"ALL",
                      "effect_sd":effect,"lag_min":lag,"metric":"mean_selected_count",
                      "trials":len(g),"rate":float(g["n_selected"].mean()),
                      "ci95_low":np.nan,"ci95_high":np.nan})

for (truth,effect,lag),g in inj.groupby(["truth_driver","effect_sd","lag_min"]):
    for metric in metrics:
        k=int(g[metric].sum()); n0=len(g); lo,hi=wilson(k,n0)
        aggregate.append({"scope":"per_driver","truth_driver":truth,
                          "effect_sd":effect,"lag_min":lag,"metric":metric,
                          "trials":n0,"rate":k/n0,"ci95_low":lo,"ci95_high":hi})

summary_df=pd.DataFrame(aggregate)
null=res[res["mode"]=="null"]
k=int((null["n_selected"]>0).sum()); nn=len(null); nlo,nhi=wilson(k,nn)

OUT.mkdir(parents=True,exist_ok=False)
res.to_csv(OUT/"end_to_end_trials.csv",index=False)
summary_df.to_csv(OUT/"end_to_end_metrics.csv",index=False)

payload={
    "experiment_id":"DISCOVERY-001",
    "version":"21.0-audit-grade-hidden-driver",
    "protocol_git_commit":commit,
    "protocol_sha256":sha256(PROTOCOL),
    "development_snapshot_sha256":source_sha,
    "validation_accessed":False,
    "external_replication_accessed":False,
    "candidate_library":{
        name:{"threshold":DRIVERS[name][0],"event_count":len(driver_events[name])}
        for name in DRIVERS
    },
    "candidate_library_size":len(DRIVERS),
    "horizons_min":HORIZONS,
    "bonferroni_alpha_per_driver_horizon":ALPHA,
    "frozen_rf_drop_threshold":rf_threshold,
    "effects_sd":EFFECTS,
    "lags_min":LAGS,
    "trials_per_truth_effect_lag":TRIALS,
    "injection_seed_range":"310000-310099",
    "null_trials":NULL_TRIALS,
    "null_rng_seed":2026092605,
    "library_wide_null_fwer":k/nn,
    "library_wide_null_fwer_ci95":[nlo,nhi],
    "aggregate_metrics":summary_df[summary_df.scope=="aggregate"].to_dict(orient="records")
}
(OUT/"v21_summary.json").write_text(json.dumps(payload,indent=2,default=str)+"\n")
print(json.dumps(payload,indent=2,default=str))
