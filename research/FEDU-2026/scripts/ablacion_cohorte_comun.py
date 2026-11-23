#!/usr/bin/env python3
"""FEDU fixed-cohort RF/weather ablation. RETROSPECTIVE DEVELOPMENT ONLY.

Train/evaluate three feature families on *identical* X/y rows, time folds.
No prospective test, not a primary hypothesis evaluation.
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd
from fedu_dev_eval_models import BASE, RF, WX, FOLDS, models, score, day_block_ci, sha256


def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--dataset",required=True,type=Path)
    pa.add_argument("--out",required=True,type=Path)
    args=pa.parse_args()
    ds=args.dataset.resolve(); out=args.out.resolve()
    manifest=json.loads((ds/"manifest.json").read_text())
    for name in ("X_features.csv","y_targets.csv"):
        if sha256(ds/name)!=manifest["output_sha256"][name]:
            raise RuntimeError("SHA-256 did not match: "+name)
    a=pd.read_csv(ds/"X_features.csv")
    b=pd.read_csv(ds/"y_targets.csv")
    assert len(a)==len(b) and a.pair_id.is_unique and a.pair_id.equals(b.pair_id)
    a["y"]=b["y_throughput_mbps"]
    a["anchor_dt"]=pd.to_datetime(a["anchor_end_local"],utc=True)
    a["day"]=pd.to_datetime(a["anchor_end_local"]).dt.date.astype(str)
    a["direction_is_dl"]=(a["direction"]=="DL").astype(float)
    for f in (6475,6655,7000):
        a["frequency_is_"+str(f)]=(a["frequency_mhz"]==f).astype(float)
    a["bandwidth_is_40"]=(a["bandwidth_mhz"]==40).astype(float)
    cohort=a[a["wx_bilateral_asof"]==1].copy()
    if cohort[WX+["y"]].isna().any().any():
        raise RuntimeError("Missing feature among intended identical complete cases")
    results=[]
    for fold,train_end,eval_start,eval_end in FOLDS:
        train=cohort[cohort.anchor_dt<pd.Timestamp(train_end).tz_convert("UTC")]
        test=cohort[(cohort.anchor_dt>=pd.Timestamp(eval_start).tz_convert("UTC"))&
                    (cohort.anchor_dt<pd.Timestamp(eval_end).tz_convert("UTC"))]
        if len(train)<150 or len(test)<50:
            raise RuntimeError("Insufficient ablation rows")
        y=test["y"].to_numpy(float)
        base_error=np.abs(y-test["t0_mbps"].to_numpy(float))
        for level,cols in (("history",BASE),("history_rf",RF),
                           ("history_rf_weather",WX)):
            for model_name,model in models().items():
                model.fit(train[cols].to_numpy(float),train["y"].to_numpy(float))
                pred=model.predict(test[cols].to_numpy(float))
                z=score(y,pred)
                ci,n_days=day_block_ci(test["day"],base_error,np.abs(y-pred))
                results.append({
                    "fold":fold,"cohort":"EXACT_SAME_RF_WEATHER_ROWS",
                    "features":level,"model":model_name,
                    "n_train":len(train),"n_eval":len(test),"days":n_days,
                    "mae":z["mae_mbps"],"rmse":z["rmse_mbps"],
                    "delta_mae_vs_persistence":float(np.mean(base_error)-z["mae_mbps"]),
                    "ci95_delta_lo":ci[0],"ci95_delta_hi":ci[1]
                })
    if out==ds or ds in out.parents:
        raise RuntimeError("Cannot write into frozen input")
    out.mkdir(parents=True,exist_ok=True,mode=0o700);out.chmod(0o700)
    with (out/"ablation_metrics_private.csv").open("w",newline="") as f:
        wr=csv.DictWriter(f,fieldnames=list(results[0]));wr.writeheader();wr.writerows(results)
    (out/"ablation_manifest.json").write_text(json.dumps({
        "type":"retrospective exploratory ablation only; not prospectively validated",
        "cohort":"exactly same rows with RF+bilateral weather",
        "reference":"persistence error on same rows, same folds",
        "folds":FOLDS,
        "feature_levels":["history","history_rf","history_rf_weather"],
        "models":["Ridge(alpha=10)","HistGradientBoosting (fixed hyperparams)"],
        "data_available_at_verified":False,
        "dataset_sha256":manifest["output_sha256"],
        "rows":results
    },ensure_ascii=False,indent=2))
    for p in out.iterdir():p.chmod(0o600)
    print(json.dumps({"scope":"retrospective development only",
        "ablation":[{"fold":z["fold"],"features":z["features"],"model":z["model"],
                    "n_train":z["n_train"],"n_eval":z["n_eval"],
                    "mae":round(z["mae"],3),"rmse":round(z["rmse"],3),
                    "delta_vs_persist":round(z["delta_mae_vs_persistence"],3)}
                   for z in results]},indent=2))


if __name__=="__main__":
    main()
