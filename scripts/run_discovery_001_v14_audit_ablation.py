#!/usr/bin/env python3
from pathlib import Path
import json,math
import numpy as np
import pandas as pd

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
SRC=ROOT/"Results/scientific_discovery/DISCOVERY-001/v12_audit/benchmark_trials.csv"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/v14_audit_ablation"
OUT.mkdir(parents=True,exist_ok=True)

df=pd.read_csv(SRC)
df=df[df["horizon_min"]>0].copy()
df["discordant"]=df["post_only"].fillna(0)+df["pre_only"].fillna(0)

ALPHA=.05
ALPHA_BONF=.05/3

def flags(g):
    return {
        "M0_naive_uncorrected":bool((g.p_value<ALPHA).any()),
        "M1_bonferroni_only":bool((g.p_value<ALPHA_BONF).any()),
        "M2_bonferroni_support":bool(((g.p_value<ALPHA_BONF)&(g.discordant>=8)).any()),
        "M3_ASDE_full":bool((((g.p_value<ALPHA_BONF)&(g.discordant>=8))&(g.positive_folds>=3)).any()),
    }

trial_rows=[]
for key,g in df.groupby(["mode","effect_sd","lag_min","seed"],dropna=False):
    row=dict(zip(["mode","effect_sd","lag_min","seed"],key))
    row.update(flags(g))
    trial_rows.append(row)
trials=pd.DataFrame(trial_rows)
trials.to_csv(OUT/"ablation_trials.csv",index=False)

def wilson(k,n,z=1.96):
    if n==0: return (np.nan,np.nan)
    p=k/n; den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return center-half,center+half

methods=["M0_naive_uncorrected","M1_bonferroni_only","M2_bonferroni_support","M3_ASDE_full"]
rows=[]
for method in methods:
    null=trials[trials["mode"]=="null_shift"]
    k=int(null[method].sum()); n=len(null); lo,hi=wilson(k,n)
    rows.append({"method":method,"metric":"false_positive_rate",
                 "effect_sd":0.0,"lag_min":np.nan,"trials":n,
                 "rate":k/n,"ci95_low":lo,"ci95_high":hi})
    inj=trials[trials["mode"]=="injected"]
    for (effect,lag),g in inj.groupby(["effect_sd","lag_min"]):
        k=int(g[method].sum()); n=len(g); lo,hi=wilson(k,n)
        rows.append({"method":method,"metric":"recovery_rate",
                     "effect_sd":effect,"lag_min":lag,"trials":n,
                     "rate":k/n,"ci95_low":lo,"ci95_high":hi})

summary=pd.DataFrame(rows)
summary.to_csv(OUT/"ablation_summary.csv",index=False)

fpr=(summary[summary.metric=="false_positive_rate"]
     [["method","rate","ci95_low","ci95_high"]].sort_values("rate"))
moderate=(summary[(summary.metric=="recovery_rate")&(summary.effect_sd==1.0)&
                  (summary.lag_min.isin([15.0,30.0,60.0]))]
          [["method","lag_min","rate","ci95_low","ci95_high"]]
          .sort_values(["lag_min","method"]))
payload={
    "experiment_id":"DISCOVERY-001",
    "version":"14.0-audit-grade-ablation",
    "validation_accessed":False,
    "source":"v12_audit confirmatory trials",
    "false_positive_rates":fpr.to_dict(orient="records"),
    "moderate_signal_recovery":moderate.to_dict(orient="records"),
}
(OUT/"v14_summary.json").write_text(json.dumps(payload,indent=2,default=str)+"\n")
print(json.dumps(payload,indent=2,default=str))
