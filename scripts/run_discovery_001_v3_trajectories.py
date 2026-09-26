#!/usr/bin/env python3
from pathlib import Path
import json, sys
import numpy as np
import pandas as pd

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.trajectory_engine import *

SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/v3"
OUT.mkdir(parents=True,exist_ok=True)

df=pd.read_csv(SOURCE)
df["t"]=pd.to_datetime(df["rf_timestamp_utc"],utc=True,errors="raise")
D=df.iloc[:2145].copy().set_index("t")
C=df.iloc[2145:2860].copy().set_index("t")
D5=D[ATM_TRANSITION_FEATURES+RF_FEATURES].resample("5min").median()
C5=C[ATM_TRANSITION_FEATURES+RF_FEATURES].resample("5min").median()

d_delta=D5[ATM_TRANSITION_FEATURES].diff(3)
med,scale=robust_scale(d_delta)
Dz,Ds,_=transition_matrix(D5,med,scale,steps=3)
Cz,Cs,_=transition_matrix(C5,med,scale,steps=3)
threshold=float(Ds.quantile(.75))
Devents=detect_peaks(Ds,threshold,30)
Cevents=detect_peaks(Cs,threshold,30)

D_event_z=Dz.loc[Devents].dropna()
C_event_z=Cz.loc[Cevents].dropna()

rf_med,rf_scale,rf_thr=rf_quality_reference(D5)
D_rf_entries=rf_entry_events(D5,rf_med,rf_scale,rf_thr,30)
C_rf_entries=rf_entry_events(C5,rf_med,rf_scale,rf_thr,30)

records=[]
for k in [2,3,4]:
    centers,Dlabels=fit_archetypes(D_event_z,k,seed=700+k)
    Clabels=assign_archetypes(C_event_z,centers)
    for a in range(k):
        dcount=int((Dlabels==a).sum())
        ccount=int((Clabels==a).sum())
        profile={c:float(v) for c,v in zip(ATM_TRANSITION_FEATURES,centers[a])}
        for horizon in [30,60,120]:
            dr=archetype_event_risk(D5.index,Devents,Dlabels,D_rf_entries,a,horizon)
            cr=archetype_event_risk(C5.index,Cevents,Clabels,C_rf_entries,a,horizon)
            drr=dr["risk_ratio"]; crr=cr["risk_ratio"]
            d_ci=risk_ratio_ci(dr["events_exposed"],dr["blocks_exposed"],
                               dr["events_unexposed"],dr["blocks_unexposed"])
            c_ci=risk_ratio_ci(cr["events_exposed"],cr["blocks_exposed"],
                               cr["events_unexposed"],cr["blocks_unexposed"])
            same=np.isfinite(drr) and np.isfinite(crr) and drr>1 and crr>1
            sufficient=dcount>=10 and ccount>=8 and dr["events_exposed"]>=3 and cr["events_exposed"]>=3
            directional=bool(same and sufficient and min(drr,crr)>=1.25)
            precise=bool(d_ci[1]>1 and c_ci[1]>1)
            stable=bool(directional and precise)
            accumulating=bool(directional and not precise)
            records.append({
                "k":k,"archetype":a,"horizon_min":horizon,
                "discovery_events":dcount,"characterization_events":ccount,
                "discovery_risk_ratio":drr,"characterization_risk_ratio":crr,
                "discovery_exposed_outcomes":dr["events_exposed"],
                "characterization_exposed_outcomes":cr["events_exposed"],
                "same_direction":bool(same),"sufficient_events":bool(sufficient),
                "discovery_rr_ci95_low":d_ci[1],"discovery_rr_ci95_high":d_ci[2],
                "characterization_rr_ci95_low":c_ci[1],"characterization_rr_ci95_high":c_ci[2],
                "directionally_replicated":directional,
                "evidence_accumulating":accumulating,
                "stable_candidate":stable,
                **{f"profile_z__{c}":v for c,v in profile.items()}
            })

out=pd.DataFrame(records)
out["min_rr"]=out[["discovery_risk_ratio","characterization_risk_ratio"]].min(axis=1)
out=out.sort_values(["stable_candidate","sufficient_events","min_rr"],
                    ascending=[False,False,False])
out.to_csv(OUT/"trajectory_archetypes.csv",index=False)

stable=out[out["stable_candidate"]]
accumulating=out[out["evidence_accumulating"]]
summary={
    "experiment_id":"DISCOVERY-001",
    "version":"3.0-trajectories",
    "validation_accessed":False,
    "prevalidation_snapshot_only":True,
    "excluded_transition_variable":"cu01_local_press_hpa",
    "exclusion_reason":"388 PRESS_JUMP QC events in prevalidation interval; rapid pressure changes are not eligible discovery features.",
    "transition_definition":"15-min multivariate changes, clipped robust z, at least two active atmospheric dimensions",
    "transition_threshold_source":"75th percentile of eligible D_discovery transition score",
    "discovery_atmospheric_events":len(Devents),
    "characterization_atmospheric_events":len(Cevents),
    "discovery_rf_entry_events":len(D_rf_entries),
    "characterization_rf_entry_events":len(C_rf_entries),
    "archetype_tests":len(out),
    "stable_candidates":len(stable),
    "evidence_accumulating_candidates":len(accumulating),
    "directional_rule":"same RR direction; >=10 discovery and >=8 characterization archetype events; >=3 exposed RF outcomes in each; min RR >=1.25",
    "precision_rule":"95% RR confidence interval lower bound must exceed 1 in both discovery and characterization before hypothesis promotion",
    "decision":(
        "HYPOTHESIS_CANDIDATE_AVAILABLE" if len(stable)
        else "EVIDENCE_ACCUMULATING" if len(accumulating)
        else "INSUFFICIENT_REPRODUCIBLE_EVENT_STRUCTURE"
    ),
    "top_rows":out.head(12).to_dict(orient="records")
}
(OUT/"trajectory_summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
print(json.dumps(summary,indent=2,default=str))
