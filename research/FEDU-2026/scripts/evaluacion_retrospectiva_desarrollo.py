#!/usr/bin/env python3
"""FEDU retrospective model DEVELOPMENT diagnostics on frozen PRIVATE X/y.

Does NOT produce confirmatory evidence, validate operational available_at,
alter production, or consume a prospective holdout. Outputs remain local.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import csv
import hashlib
import json
import math
import platform

import numpy as np
import pandas as pd
import sklearn
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor


FOLDS = [
    ("dev_01", "2026-09-29T00:00:00-05:00", "2026-10-01T00:00:00-05:00", "2026-10-10T00:00:00-05:00"),
    ("dev_02", "2026-10-13T00:00:00-05:00", "2026-10-15T00:00:00-05:00", "2026-10-26T22:10:00-05:00"),
]
BASE = [
    "t0_mbps", "tminus1_mbps", "tminus2_mbps", "tminus3_mbps",
    "past4_median_mbps", "past4_mean_mbps", "past4_stdev_mbps",
    "anchor_hour", "anchor_weekday", "direction_is_dl",
    "frequency_is_6475", "frequency_is_6655", "frequency_is_7000",
    "bandwidth_is_40"
]
RF = BASE + ["rf_age_min","dl_rssi_dbm","ul_rssi_dbm","dl_snr_db","ul_snr_db"]
WX = RF + ["cu01_wx_age_min","sj01_wx_age_min",
           "cu01_temp_c","cu01_hum_pct","cu01_press_hpa",
           "sj01_temp_c","sj01_hum_pct","sj01_press_hpa"]
COHORTS = [("history", BASE, None), ("history_rf",RF,"rf_asof"),
           ("history_rf_weather",WX,"wx_bilateral_asof")]


def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for buf in iter(lambda:f.read(1048576),b""):
            h.update(buf)
    return h.hexdigest()


def score(y, pred):
    d=np.asarray(y)-np.asarray(pred)
    return {"mae_mbps":float(np.mean(np.abs(d))),
            "rmse_mbps":float(np.sqrt(np.mean(d*d))),
            "bias_prediction_minus_actual_mbps":float(-np.mean(d))}


def day_block_ci(day, baseline_error, ml_error, seed=42, replicates=600):
    """Exploratory percentile bootstrap sampling whole days, *not* event-independent."""
    records=defaultdict(list)
    for d,b,m in zip(day,baseline_error,ml_error):
        records[str(d)].append(float(b)-float(m))
    days=sorted(records)
    if len(days)<4:
        return [None,None],len(days)
    s=np.array([sum(records[d]) for d in days],dtype=float)
    n=np.array([len(records[d]) for d in days],dtype=float)
    rng=np.random.default_rng(seed)
    ix=rng.integers(0,len(days),size=(replicates,len(days)))
    means=np.sum(s[ix],axis=1)/np.sum(n[ix],axis=1)
    return [float(x) for x in np.percentile(means,[2.5,97.5])], len(days)


def models():
    return {
        "ridge_alpha10":Pipeline([
            ("imputer",SimpleImputer(strategy="median")),
            ("scaler",StandardScaler()),
            ("est",Ridge(alpha=10.0))
        ]),
        "hgb_120leaf15":Pipeline([
            ("imputer",SimpleImputer(strategy="median")),
            ("est",HistGradientBoostingRegressor(
                max_iter=120,max_leaf_nodes=15,learning_rate=0.05,
                l2_regularization=1.0,random_state=42,early_stopping=False))
        ]),
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    ds=args.dataset.resolve(); out=args.output.resolve()
    # Keep files in a distinct private FEDU area, never in AtmosLink.
    if not ds.is_dir() or not (ds/"manifest.json").exists():
        p.error("Falta dataset privado congelado y manifiesto")
    if out == ds or ds in out.parents:
        p.error("La salida no puede sobrescribir el dataset de entrada")
    manifest=json.loads((ds/"manifest.json").read_text(encoding="utf-8"))
    if manifest.get("available_at_verified", True):
        p.error("Expected dataset with unverified available_at for exploratory analysis")
    for fn in ["X_features.csv","y_targets.csv"]:
        if sha256(ds/fn)!=manifest["output_sha256"][fn]:
            raise RuntimeError("SHA-256 mismatch, refused to train: "+fn)
    a=pd.read_csv(ds/"X_features.csv")
    b=pd.read_csv(ds/"y_targets.csv")
    if len(a)!=len(b) or a["pair_id"].duplicated().any() or b["pair_id"].duplicated().any():
        raise RuntimeError("Misaligned or duplicate X/y")
    if not np.array_equal(a["pair_id"].to_numpy(),b["pair_id"].to_numpy()):
        raise RuntimeError("Pair id or order mismatch")
    if not ((b["actual_horizon_min"]>=56)&(b["actual_horizon_min"]<=64)).all():
        raise RuntimeError("Future horizon out of tolerance")
    a["anchor_dt"]=pd.to_datetime(a["anchor_end_local"],utc=True)
    b["future_dt"]=pd.to_datetime(b["future_end_local"],utc=True)
    if not (b["future_dt"]>a["anchor_dt"]).all():
        raise RuntimeError("Future target not after input")
    a["y"]=b["y_throughput_mbps"]
    a["day"]=pd.to_datetime(a["anchor_end_local"]).dt.date.astype(str)
    a["direction_is_dl"]=(a["direction"]=="DL").astype(float)
    for f in [6475,6655,7000]:
        a["frequency_is_"+str(f)]=(a["frequency_mhz"]==f).astype(float)
    a["bandwidth_is_40"]=(a["bandwidth_mhz"]==40).astype(float)
    metrics=[]; prediction_rows=[]
    fold_details=[]

    for cohort, cols, flag in COHORTS:
        data=a if flag is None else a[a[flag]==1]
        # No imputation of RF/weather absent: cohorts are separately defined.
        if data[cols+["y"]].isna().any().any():
            raise RuntimeError("Missing required values in cohort "+cohort)
        for fold_name,train_end,eval_start,eval_end in FOLDS:
            train=data[data["anchor_dt"]<pd.Timestamp(train_end).tz_convert("UTC")]
            test=data[(data["anchor_dt"]>=pd.Timestamp(eval_start).tz_convert("UTC"))&
                      (data["anchor_dt"]<pd.Timestamp(eval_end).tz_convert("UTC"))]
            if len(train)<150 or len(test)<50: 
                fold_details.append({"cohort":cohort,"fold":fold_name,
                                     "status":"insufficient rows","n_train":len(train),
                                     "n_eval":len(test)})
                continue
            fold_details.append({
                "cohort":cohort,"fold":fold_name,"status":"evaluated",
                "train_until_exclusive":train_end,"eval_from":eval_start,
                "eval_until_exclusive":eval_end,"n_train":len(train),
                "n_eval":len(test),"n_eval_days":test["day"].nunique(),
                "eval_first":test["anchor_end_local"].min(),
                "eval_last":test["anchor_end_local"].max()})
            y=test["y"].to_numpy(dtype=float)
            pred_map={
                "persistence":test["t0_mbps"].to_numpy(dtype=float),
                "past4_median":test["past4_median_mbps"].to_numpy(dtype=float)
            }
            for name, model in models().items():
                model.fit(train[cols].to_numpy(dtype=float),
                          train["y"].to_numpy(dtype=float))
                pred_map[name]=model.predict(test[cols].to_numpy(dtype=float))
            p0_err=np.abs(y-pred_map["persistence"])
            for name,pred in pred_map.items():
                met=score(y,pred)
                ci, n_days=day_block_ci(test["day"],
                         p0_err,np.abs(y-pred))
                met.update({
                    "cohort":cohort,"fold":fold_name,"model":name,
                    "n_train":len(train),"n_eval":len(test),"n_eval_days":n_days,
                    "delta_MAE_vs_persistence_mbps":
                        float(np.mean(p0_err)-np.mean(np.abs(y-pred))),
                    "delta_MAE_day_bootstrap_CI95_lo":ci[0],
                    "delta_MAE_day_bootstrap_CI95_hi":ci[1],
                    "eval_status":"EXPLORATORY_RETROSPECTIVE_ONLY",
                })
                metrics.append(met)
                for row, yy, pp in zip(test.itertuples(index=False),y,pred):
                    prediction_rows.append({
                        "pair_id":row.pair_id,"anchor_dt":row.anchor_end_local,
                        "cohort":cohort,"fold":fold_name,"model":name,
                        "direction":row.direction,
                        "frequency_mhz":row.frequency_mhz,
                        "bandwidth_mhz":row.bandwidth_mhz,
                        "y":float(yy),"prediction":float(pp)
                    })
    if not metrics:
        raise RuntimeError("No folds evaluated")
    out.mkdir(parents=True,exist_ok=True,mode=0o700)
    out.chmod(0o700)
    csv_cols=list(metrics[0])
    with (out/"metrics_private.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=csv_cols)
        w.writeheader();w.writerows(metrics)
    with (out/"predictions_private.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(prediction_rows[0]))
        w.writeheader();w.writerows(prediction_rows)
    meta={
        "classification":"DEVELOPMENT_ONLY_RETROSPECTIVE; NOT CONFIRMATORY",
        "data_asof_operationally_verified":False,
        "real_prospective_test_consulted":False,
        "primary_degradation_hypothesis_tested":False,
        "split_design":"2 predetermined forward folds with >=48h gaps; no random CV",
        "models":{"persistence":"last valid measurement",
                  "past4_median":"median of 4 previous readings",
                  "ridge_alpha10":"fixed alpha 10, standardize/impute trained only on past",
                  "hgb_120leaf15":"fixed 120 iterations, 15 leaves, lr .05, l2 1"},
        "bootstrapping":"exploratory 600 resamples of whole calendar days (95% percentile)",
        "cohorts":[z[0] for z in COHORTS],
        "folds":fold_details,
        "package_versions":{"python":platform.python_version(),
                            "numpy":np.__version__,"pandas":pd.__version__,
                            "sklearn":sklearn.__version__},
        "dataset_sha256":manifest["output_sha256"],
        "risk":"no available_at; source/label missingness; changes in regime; inspected retrospective data; two sites one link",
        "outputs_private":["metrics_private.csv","predictions_private.csv"],
    }
    (out/"run_manifest.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    for f in out.glob("*"):
        if f.is_file():f.chmod(0o600)
    # Print only aggregate metrics. No individual rows or sensor data.
    print(json.dumps({
        "evaluation":"exploratory only; not a FEDU hypothesis test",
        "folds":fold_details,
        "metric_rows":[{
            "cohort":m["cohort"],"fold":m["fold"],"model":m["model"],
            "n_eval":m["n_eval"],"mae_mbps":round(m["mae_mbps"],3),
            "rmse_mbps":round(m["rmse_mbps"],3),
            "delta_vs_persistence_mbps":round(m["delta_MAE_vs_persistence_mbps"],3),
            "day_bootstrap_ci95":[round(z,3) if z is not None else None for z in
             [m["delta_MAE_day_bootstrap_CI95_lo"],m["delta_MAE_day_bootstrap_CI95_hi"]]]
        } for m in metrics],
        "output_integrity":{f.name:sha256(f) for f in sorted(out.iterdir()) if f.is_file()}
    },ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
