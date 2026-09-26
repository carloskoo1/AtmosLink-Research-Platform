#!/usr/bin/env python3
from pathlib import Path
import json, sys
import numpy as np
import pandas as pd
from scipy.stats import binomtest

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.trajectory_engine import *

SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/v5"
OUT.mkdir(parents=True,exist_ok=True)

df=pd.read_csv(SOURCE)
df["t"]=pd.to_datetime(df["rf_timestamp_utc"],utc=True,errors="raise")
D=df.iloc[:2145].copy().set_index("t")
C=df.iloc[2145:2860].copy().set_index("t")
D5=D[ATM_TRANSITION_FEATURES+RF_FEATURES].resample("5min").median()
C5=C[ATM_TRANSITION_FEATURES+RF_FEATURES].resample("5min").median()

med,scale=robust_scale(D5[ATM_TRANSITION_FEATURES].diff(3))
Dz,Ds,_=transition_matrix(D5,med,scale,3)
Cz,Cs,_=transition_matrix(C5,med,scale,3)
threshold=float(Ds.quantile(.75))
De=detect_peaks(Ds,threshold,30); Ce=detect_peaks(Cs,threshold,30)
DE=Dz.loc[De].dropna(); CE=Cz.loc[Ce].dropna()
rf_med,rf_scale,rf_thr=rf_quality_reference(D5)
Dre=rf_entry_events(D5,rf_med,rf_scale,rf_thr,30)
Cre=rf_entry_events(C5,rf_med,rf_scale,rf_thr,30)

def direction_stats(labels,rf_entries,archetype,horizon):
    selected=labels[labels==archetype].index
    post_only=pre_only=both=neither=0
    for event in selected:
        pre=any(event-pd.Timedelta(minutes=horizon)<=r<event for r in rf_entries)
        post=any(event<r<=event+pd.Timedelta(minutes=horizon) for r in rf_entries)
        if post and not pre: post_only+=1
        elif pre and not post: pre_only+=1
        elif pre and post: both+=1
        else: neither+=1
    discordant=post_only+pre_only
    p=binomtest(post_only,discordant,.5,alternative="greater").pvalue if discordant else 1.0
    return dict(n_events=len(selected),post_only=post_only,pre_only=pre_only,
                both=both,neither=neither,p_value=float(p))

rows=[]
for k in [2,3,4,5,6]:
    centers,Dlabels=fit_archetypes(DE,k,seed=700+k)
    Clabels=assign_archetypes(CE,centers)
    for archetype in range(k):
        for horizon in [30,60,120]:
            ds=direction_stats(Dlabels,Dre,archetype,horizon)
            cs=direction_stats(Clabels,Cre,archetype,horizon)
            rows.append({"k":k,"archetype":archetype,"horizon_min":horizon,
                         **{f"discovery_{a}":b for a,b in ds.items()},
                         **{f"characterization_{a}":b for a,b in cs.items()}})
out=pd.DataFrame(rows)

def bh(series):
    p=series.fillna(1).to_numpy(); m=len(p); order=np.argsort(p); q=np.ones(m); prev=1.0
    for rank,idx in reversed(list(enumerate(order,start=1))):
        prev=min(prev,p[idx]*m/rank); q[idx]=prev
    return q

out["discovery_q"]=bh(out["discovery_p_value"])
out["characterization_q"]=bh(out["characterization_p_value"])
out["direction_preserved"]=(
    (out.discovery_post_only>out.discovery_pre_only)
    & (out.characterization_post_only>out.characterization_pre_only)
)
out["support_ok"]=(out.discovery_n_events>=10)&(out.characterization_n_events>=8)
out["strict_pass"]=out.direction_preserved & out.support_ok
out.to_csv(OUT/"directionality_grid.csv",index=False)

d_days=(D5.index.max()-D5.index.min()).total_seconds()/86400
c_days=(C5.index.max()-C5.index.min()).total_seconds()/86400
d_rate=len(Dre)/d_days
c_rate=len(Cre)/c_days
pooled_rate=(len(Dre)+len(Cre))/(d_days+c_days)
target_entries=30
budget={
    "discovery_rf_entries":len(Dre),
    "characterization_rf_entries":len(Cre),
    "discovery_days":d_days,
    "characterization_days":c_days,
    "rf_entry_rate_per_day_discovery":d_rate,
    "rf_entry_rate_per_day_characterization":c_rate,
    "pooled_reference_rate_per_day":pooled_rate,
    "illustrative_target_independent_rf_entries_per_characterization_block":target_entries,
    "additional_entries_to_target":max(0,target_entries-len(Cre)),
    "estimated_additional_days_at_characterization_rate":(
        max(0,target_entries-len(Cre))/c_rate if c_rate>0 else None
    ),
    "note":"Operational evidence-budget estimate only; not a formal power calculation and not permission to open D_validation."
}
(OUT/"evidence_budget.json").write_text(json.dumps(budget,indent=2)+"\n")
summary={
    "experiment_id":"DISCOVERY-001","version":"5.0-strict-directionality",
    "validation_accessed":False,"external_replication_accessed":False,
    "tests":len(out),"strict_directionality_passes":int(out.strict_pass.sum()),
    "fdr_pass_both":int(((out.discovery_q<.05)&(out.characterization_q<.05)).sum()),
    "decision":"NO_TRAJECTORY_HYPOTHESIS_READY",
    "rfatm_0006_status":"SCREENED_OUT",
    "rfatm_0006_failed_gate":"strict_pre_post_temporal_direction",
    "evidence_budget":budget
}
(OUT/"v5_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))
