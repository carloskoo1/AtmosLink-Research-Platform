#!/usr/bin/env python3
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.synthetic_benchmark import (
    RF_FEATURES,robust_z,robust_reference,
    rf_drop_threshold_from_array,detect_drop_indices_fixed_threshold,
    directional_test_indices
)

SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
METRICS=ROOT/"Results/scientific_discovery/DISCOVERY-001/v21_end_to_end_audit/end_to_end_metrics.csv"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/v22_background_hardness"
OUT.mkdir(parents=True,exist_ok=True)

DRIVERS={
"cu01_local_temp_avg_c__rise":1.5308007671599377,
"sj01_local_temp_avg_c__fall":1.2876641771825945,
"sj01_local_hum_avg_pct__fall":1.6365945597866016,
"sj01_local_press_hpa__rise":0.8993210126363124,
}
df=pd.read_csv(SOURCE); df["t"]=pd.to_datetime(df.rf_timestamp_utc,utc=True)
vars=sorted({x.rsplit("__",1)[0] for x in DRIVERS})
X=df.set_index("t")[vars+RF_FEATURES].resample("5min").median()

def fixed_peaks(score,threshold):
    events=[]; last=None
    for t,v in score.dropna().items():
        if v<threshold: continue
        local=score.loc[t-pd.Timedelta("10min"):t+pd.Timedelta("10min")]
        if v<local.max(): continue
        if last is None or t-last>=pd.Timedelta("360min"):
            events.append(t); last=t
    return events

med_s,scale_s=robust_reference(X)
med=med_s.to_numpy(float); scale=scale_s.to_numpy(float)
base=X[RF_FEATURES].to_numpy(float)
rf_thr=rf_drop_threshold_from_array(base,med,scale,.075)
rf=detect_drop_indices_fixed_threshold(base,med,scale,rf_thr)

bounds=[
(pd.Timestamp("2026-09-01T18:30:52Z"),pd.Timestamp("2026-09-04T08:02:17Z")),
(pd.Timestamp("2026-09-04T08:12:19Z"),pd.Timestamp("2026-09-07T05:14:26Z")),
(pd.Timestamp("2026-09-07T05:19:27Z"),pd.Timestamp("2026-09-09T18:41:57Z")),
(pd.Timestamp("2026-09-09T18:46:58Z"),pd.Timestamp("2026-09-13T03:29:49Z"))]

metrics=pd.read_csv(METRICS)
rows=[]
for name,thr in DRIVERS.items():
    col,direction=name.rsplit("__",1)
    z=robust_z(X[col].diff(3)); score=z if direction=="rise" else -z
    ev=fixed_peaks(score,thr)
    idx=np.asarray([X.index.get_loc(t) for t in ev],dtype=int)
    fold_counts=[sum(a<=t<=b for t in ev) for a,b in bounds]
    for h in [30,60,120]:
        st=directional_test_indices(idx,rf,h//5)
        rows.append({
            "driver":name,"horizon_min":h,"event_count":len(ev),
            "fold1_events":fold_counts[0],"fold2_events":fold_counts[1],
            "fold3_events":fold_counts[2],"fold4_events":fold_counts[3],
            "baseline_post_only":st["post_only"],"baseline_pre_only":st["pre_only"],
            "baseline_post_minus_pre":st["post_minus_pre"],
            "baseline_directional_p":st["p_value"],
        })
hard=pd.DataFrame(rows)

# Attach audit-grade per-driver recovery at 1.0 SD for context.
m=metrics[(metrics.scope=="per_driver")&(metrics.effect_sd==1.0)&
          (metrics.metric.isin(["truth_selected","unique_top1_correct"]))].copy()
wide=m.pivot_table(index=["truth_driver","lag_min"],columns="metric",values="rate").reset_index()
hard.to_csv(OUT/"baseline_driver_hardness.csv",index=False)
wide.to_csv(OUT/"audit_recovery_by_driver_1sd.csv",index=False)

payload={
 "experiment_id":"DISCOVERY-001","version":"22.0-background-hardness-diagnostic",
 "status":"POST_AUDIT_DIAGNOSTIC",
 "validation_accessed":False,
 "interpretation":"Natural RF-event background differs across frozen atmospheric drivers. This affects directional-test headroom and must be reported when interpreting end-to-end recovery.",
 "baseline":hard.to_dict(orient="records"),
 "audit_recovery_1sd":wide.to_dict(orient="records")
}
(OUT/"v22_summary.json").write_text(json.dumps(payload,indent=2,default=str)+"\n")
print(hard.to_string(index=False))
print("\nAudit recovery @ 1 SD")
print(wide.to_string(index=False))
