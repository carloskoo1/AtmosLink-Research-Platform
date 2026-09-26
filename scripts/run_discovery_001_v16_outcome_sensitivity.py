#!/usr/bin/env python3
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.event_sequence_engine import robust_location_scale, detect_drop_events
from scientific_discovery.matched_trajectory_engine import matched_feature_differences

SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/v16_outcome_sensitivity"
OUT.mkdir(parents=True,exist_ok=True)

OUTCOMES={
    "all6":["dl_rssi_dbm","ul_rssi_dbm","dl_snr_db","ul_snr_db","dl_mcs","ul_mcs"],
    "analog4":["dl_rssi_dbm","ul_rssi_dbm","dl_snr_db","ul_snr_db"],
    "dl3":["dl_rssi_dbm","dl_snr_db","dl_mcs"],
    "ul3":["ul_rssi_dbm","ul_snr_db","ul_mcs"],
}
WEATHER="sj01_local_hum_avg_pct"
all_cols=sorted(set(sum(OUTCOMES.values(),[])+[WEATHER]))
df=pd.read_csv(SOURCE)
df["t"]=pd.to_datetime(df["rf_timestamp_utc"],utc=True,errors="raise")
X=df.set_index("t")[all_cols].resample("5min").median()

bounds=[
    (pd.Timestamp("2026-09-01T18:30:52Z"),pd.Timestamp("2026-09-04T08:02:17Z")),
    (pd.Timestamp("2026-09-04T08:12:19Z"),pd.Timestamp("2026-09-07T05:14:26Z")),
    (pd.Timestamp("2026-09-07T05:19:27Z"),pd.Timestamp("2026-09-09T18:41:57Z")),
    (pd.Timestamp("2026-09-09T18:46:58Z"),pd.Timestamp("2026-09-13T03:29:49Z")),
]

def rf_events(cols):
    med,scale=robust_location_scale(X[cols])
    q=((X[cols]-med)/scale).mean(axis=1)
    dq=q.diff(3)
    threshold=float(dq.quantile(.075))
    return detect_drop_events(dq,threshold,refractory_minutes=30),threshold

def wp(values):
    a=pd.Series(values).dropna().to_numpy(float)
    if len(a)<10 or np.allclose(a,0):
        return np.nan
    return float(wilcoxon(a).pvalue)

def match_rate(reference,other,tol_min=10):
    if not reference:
        return np.nan
    tol=pd.Timedelta(minutes=tol_min)
    return sum(any(abs(o-r)<=tol for o in other) for r in reference)/len(reference)

event_sets={}
rows=[]
for name,cols in OUTCOMES.items():
    events,thr=rf_events(cols)
    event_sets[name]=events
    m=matched_feature_differences(X,events,WEATHER,"std60",max_day_shift=10)
    fold_signs=[]
    for a,b in bounds:
        z=m[(m.event_time>=a)&(m.event_time<=b)]
        med=float(z.pre_diff.median()) if len(z) else np.nan
        fold_signs.append(int(np.sign(med)) if np.isfinite(med) and med!=0 else 0)
    rows.append({
        "outcome":name,"rf_features":";".join(cols),"rf_drop_threshold":thr,
        "rf_event_count":len(events),"matched_event_count":len(m),
        "pre_median_diff":float(m.pre_diff.median()) if len(m) else np.nan,
        "pre_p":wp(m.pre_diff),
        "post_median_diff":float(m.post_diff.median()) if len(m) else np.nan,
        "post_p":wp(m.post_diff),
        "fold_signs":";".join(map(str,fold_signs)),
        "negative_pre_folds":sum(s<0 for s in fold_signs),
    })

out=pd.DataFrame(rows)
out["pre_p_bonferroni"]=np.minimum(1.0,out["pre_p"]*len(out))
out["post_p_bonferroni"]=np.minimum(1.0,out["post_p"]*len(out))
ref=event_sets["all6"]
out["event_overlap_with_all6"]=out["outcome"].map(
    lambda n: match_rate(ref,event_sets[n],tol_min=10)
)
out["context_marker_consistent"]=(
    (out["pre_median_diff"]<0)
    & (out["post_median_diff"]<0)
    & (out["negative_pre_folds"]>=3)
)
out.to_csv(OUT/"outcome_sensitivity.csv",index=False)

payload={
    "experiment_id":"DISCOVERY-001",
    "version":"16.0-outcome-definition-sensitivity",
    "validation_accessed":False,
    "status":"EXPLORATORY_SENSITIVITY",
    "target":"CTX-0001 / SJ01 humidity std60 context marker",
    "important_limit":"Outcome definitions were examined after CTX-0001 was identified; this is robustness analysis, not independent confirmation.",
    "results":out.to_dict(orient="records")
}
(OUT/"v16_summary.json").write_text(json.dumps(payload,indent=2,default=str)+"\n")
print(out.to_string(index=False))
