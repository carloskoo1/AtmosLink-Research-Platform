#!/usr/bin/env python3
from pathlib import Path
import json, sys
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, combine_pvalues

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.event_sequence_engine import rf_quality_index, detect_drop_events
from scientific_discovery.matched_trajectory_engine import (
    matched_feature_differences, benjamini_hochberg
)

SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/v6"
OUT.mkdir(parents=True,exist_ok=True)

ATM=[
    "cu01_local_temp_avg_c","cu01_local_hum_avg_pct",
    "sj01_local_temp_avg_c","sj01_local_hum_avg_pct",
    "sj01_local_press_hpa","sj01_local_wind_speed_ms"
]
RF=["dl_rssi_dbm","ul_rssi_dbm","dl_snr_db","ul_snr_db","dl_mcs","ul_mcs"]
KINDS=["d30","d60","std60"]

df=pd.read_csv(SOURCE)
df["t"]=pd.to_datetime(df["rf_timestamp_utc"],utc=True,errors="raise")
X=df.set_index("t")[ATM+RF].resample("5min").median()
q,_,_=rf_quality_index(X)
dq=q.diff(3)
rf_drop_threshold=float(dq.quantile(.075))
drops=detect_drop_events(dq,rf_drop_threshold)

bounds=[
    (pd.Timestamp("2026-09-01T18:30:52Z"),pd.Timestamp("2026-09-04T08:02:17Z")),
    (pd.Timestamp("2026-09-04T08:12:19Z"),pd.Timestamp("2026-09-07T05:14:26Z")),
    (pd.Timestamp("2026-09-07T05:19:27Z"),pd.Timestamp("2026-09-09T18:41:57Z")),
    (pd.Timestamp("2026-09-09T18:46:58Z"),pd.Timestamp("2026-09-13T03:29:49Z")),
]

def signed_rank(values):
    x=pd.Series(values).dropna().to_numpy(dtype=float)
    if len(x)<8 or np.allclose(x,0):
        return np.nan
    return float(wilcoxon(x).pvalue)

rows=[]
for column in ATM:
    for kind in KINDS:
        m=matched_feature_differences(X,drops,column,kind,max_day_shift=10)
        fold_stats=[]
        for a,b in bounds:
            z=m[(m.event_time>=a)&(m.event_time<=b)]
            vals=z.pre_diff.dropna()
            fold_stats.append({
                "n":len(vals),
                "median":float(vals.median()) if len(vals) else np.nan,
                "p":signed_rank(vals),
            })
        signs=[np.sign(f["median"]) for f in fold_stats
               if f["n"]>=8 and np.isfinite(f["median"]) and f["median"]!=0]
        sign_consistency=max(sum(s>0 for s in signs),sum(s<0 for s in signs)) if signs else 0
        valid_p=[f["p"] for f in fold_stats if np.isfinite(f["p"])]
        combined_p=float(combine_pvalues(valid_p,method="fisher").pvalue) if len(valid_p)>=3 else np.nan
        post=m.post_diff.dropna()
        post_median=float(post.median()) if len(post) else np.nan
        post_p=signed_rank(post)
        row={
            "feature":f"{column}__{kind}","column":column,"kind":kind,
            "n_events":len(m),"sign_consistency":sign_consistency,
            "eligible_folds":len(signs),"combined_pre_p":combined_p,
            "pooled_pre_median":float(m.pre_diff.median()) if len(m) else np.nan,
            "pooled_post_median":post_median,"pooled_post_p":post_p,
        }
        for i,f in enumerate(fold_stats,1):
            row.update({f"fold{i}_n":f["n"],f"fold{i}_median":f["median"],f"fold{i}_p":f["p"]})
        rows.append(row)
screen=pd.DataFrame(rows)
screen["combined_pre_q"]=benjamini_hochberg(screen["combined_pre_p"])

def classify(r):
    robust=(r.sign_consistency==4 and r.eligible_folds==4 and r.combined_pre_q<=.05)
    post_same=(np.isfinite(r.pooled_post_median)
               and np.sign(r.pooled_pre_median)==np.sign(r.pooled_post_median))
    if robust and (not np.isfinite(r.pooled_post_p) or r.pooled_post_p>.10):
        return "PRECURSOR_CANDIDATE"
    if robust and np.isfinite(r.pooled_post_p) and r.pooled_post_p<=.05 and post_same:
        return "CONTEXT_MARKER"
    return "INTERNAL_SIGNAL_ONLY" if robust else "SCREENED"

screen["classification"]=screen.apply(classify,axis=1)
screen=screen.sort_values(["classification","combined_pre_q","sign_consistency"])
screen.to_csv(OUT/"regime_marker_screen.csv",index=False)

markers=screen[screen.classification=="CONTEXT_MARKER"]
precursors=screen[screen.classification=="PRECURSOR_CANDIDATE"]
summary={
    "experiment_id":"DISCOVERY-001",
    "version":"6.0-regime-marker-separation",
    "validation_accessed":False,
    "development_folds":4,
    "rf_drop_events_total":len(drops),
    "rf_drop_events_by_fold":[sum(a<=t<=b for t in drops) for a,b in bounds],
    "features_screened":len(screen),
    "precursor_candidates":len(precursors),
    "context_markers":len(markers),
    "decision":"NO_PRECURSOR_READY" if len(precursors)==0 else "PRECURSOR_INTERNAL_CANDIDATE",
    "context_marker_rows":markers.to_dict(orient="records"),
}
(OUT/"v6_summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
print(json.dumps(summary,indent=2,default=str))
