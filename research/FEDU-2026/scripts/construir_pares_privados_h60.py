#!/usr/bin/env python3
"""Construct a PRIVATE retrospective H=60 FEDU pairing dataset.

Source SQLite is read-only; outputs X/features and y/targets into an explicit
directory under /tmp only. Operational available_at remains UNKNOWN.
Not training, not a prospective holdout.
"""
import argparse
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import csv
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import statistics
import auditar_pares_causales_h60 as qa

SOURCE_COLS = [
    "timestamp_start_local","timestamp_end_local","status","direction",
    "operating_frequency_mhz","channel_bandwidth_mhz",
    "measured_throughput_mbps","route_verified","ping_status",
    "rf_timestamp_local","dl_rssi_dbm","ul_rssi_dbm","dl_snr_db","ul_snr_db",
    "cu01_weather_timestamp_local","sj01_weather_timestamp_local",
    "cu01_temp_c","sj01_temp_c","cu01_hum_pct","sj01_hum_pct",
    "cu01_press_hpa","sj01_press_hpa",
]
FEATURE_COLS = [
    "pair_id","anchor_end_local","direction","frequency_mhz","bandwidth_mhz",
    "anchor_hour","anchor_weekday",
    "t0_mbps","tminus1_mbps","tminus2_mbps","tminus3_mbps",
    "past4_median_mbps","past4_mean_mbps","past4_stdev_mbps",
    "rf_asof","wx_bilateral_asof",
    "rf_age_min","dl_rssi_dbm","ul_rssi_dbm","dl_snr_db","ul_snr_db",
    "cu01_wx_age_min","sj01_wx_age_min",
    "cu01_temp_c","cu01_hum_pct","cu01_press_hpa",
    "sj01_temp_c","sj01_hum_pct","sj01_press_hpa",
]
TARGET_COLS=["pair_id","future_end_local","actual_horizon_min","y_throughput_mbps"]


def age_min(s, anchor):
    t=qa.parse(s)
    return round((anchor-t).total_seconds()/60,4) if t else None


def hash_file(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--db",required=True,type=Path)
    a.add_argument("--schedule",required=True,type=Path)
    a.add_argument("--events",required=True,type=Path)
    a.add_argument("--output",required=True,type=Path)
    a.add_argument("--cutoff-local",default="2026-10-26T22:10:00-05:00")
    args=a.parse_args()
    root=Path("/tmp").resolve()
    output=args.output.resolve()
    if output==root or root not in output.parents:
        a.error("--output debe estar dentro de /tmp para no modificar producción")
    cutoff=qa.parse(args.cutoff_local)
    if not cutoff or cutoff.utcoffset() is None:
        a.error("--cutoff-local requiere fecha con zona horaria")
    c=sqlite3.connect(args.db.resolve().as_uri()+"?mode=ro",uri=True,timeout=2)
    c.execute("PRAGMA query_only=ON")
    cols={x[1] for x in c.execute("PRAGMA table_info(active_throughput_6g)")}
    if set(SOURCE_COLS)-cols:
        raise RuntimeError("Faltan columnas: "+str(sorted(set(SOURCE_COLS)-cols)))
    lines=c.execute("select "+",".join('"'+k+'"' for k in SOURCE_COLS)+
        " from active_throughput_6g order by timestamp_end_local").fetchall()
    c.close()
    transitions,_=qa.load_transitions(args.schedule,args.events)
    by=defaultdict(list)
    count=Counter()
    for line in lines:
        r=dict(zip(SOURCE_COLS,line))
        t=qa.parse(r["timestamp_end_local"])
        if not t or t>cutoff:
            count["excluded_after_cutoff_or_invalid_time"]+=1
            continue
        count["tests_in_cutoff"]+=1
        if not qa.valid_basic(r):
            count["excluded_basic"]+=1
            continue
        r["t"]=t
        key=(int(r["operating_frequency_mhz"]),
             int(r["channel_bandwidth_mhz"]),r["direction"])
        by[key].append(r)
    features=[]
    targets=[]
    cohort=Counter()
    for key,arr in by.items():
        arr.sort(key=lambda z:z["t"])
        tt=[r["t"] for r in arr]
        for i,r in enumerate(arr):
            if i<3: continue
            h=arr[i-3:i+1]
            steps=[h[j]["t"]-h[j-1]["t"] for j in (1,2,3)]
            if any(not (qa.MIN_STEP<=v<=qa.MAX_STEP) for v in steps):
                continue
            if h[0]["t"]<r["t"]-qa.HISTORY: continue
            if qa.near_intervention(r["t"],transitions):continue
            target=r["t"]+qa.HORIZON
            ix=bisect_left(tt,target)
            eligible=[j for j in (ix-1,ix) if 0<=j<len(arr)
                      and arr[j]["t"]>r["t"]
                      and abs(arr[j]["t"]-target)<=qa.TOL]
            if not eligible:continue
            fut=arr[min(eligible,key=lambda j:abs(arr[j]["t"]-target))]
            validrf=qa.valid_rf(r,r["t"])
            validwx=validrf and qa.valid_weather(r,r["t"])
            mm=[x["measured_throughput_mbps"] for x in h]
            pid=f"F{len(features)+1:06d}"
            feat={
                "pair_id":pid,"anchor_end_local":r["timestamp_end_local"],
                "direction":r["direction"],"frequency_mhz":key[0],
                "bandwidth_mhz":key[1],"anchor_hour":r["t"].hour,
                "anchor_weekday":r["t"].weekday(),
                "t0_mbps":mm[-1],"tminus1_mbps":mm[-2],
                "tminus2_mbps":mm[-3],"tminus3_mbps":mm[-4],
                "past4_median_mbps":statistics.median(mm),
                "past4_mean_mbps":statistics.mean(mm),
                "past4_stdev_mbps":statistics.pstdev(mm),
                "rf_asof":int(validrf),"wx_bilateral_asof":int(validwx),
            }
            if validrf:
                feat.update({
                    "rf_age_min":age_min(r["rf_timestamp_local"],r["t"]),
                    "dl_rssi_dbm":r["dl_rssi_dbm"],"ul_rssi_dbm":r["ul_rssi_dbm"],
                    "dl_snr_db":r["dl_snr_db"],"ul_snr_db":r["ul_snr_db"],
                })
            if validwx:
                for prefix in ("cu01","sj01"):
                    feat[prefix+"_wx_age_min"]=age_min(r[prefix+"_weather_timestamp_local"],r["t"])
                    for suffix in ("temp_c","hum_pct","press_hpa"):
                        feat[prefix+"_"+suffix]=r[prefix+"_"+suffix]
            features.append(feat)
            targets.append({
                "pair_id":pid,"future_end_local":fut["timestamp_end_local"],
                "actual_horizon_min":round((fut["t"]-r["t"]).total_seconds()/60,4),
                "y_throughput_mbps":fut["measured_throughput_mbps"],
            })
            cohort["retrospective_pairs"]+=1
            cohort["rf_eligible"]+=int(validrf)
            cohort["dual_weather_eligible"]+=int(validwx)
            cohort["regime_"+str(key[0])+"_"+str(key[1])+"_"+key[2]]+=1
    output.mkdir(parents=True,exist_ok=True)
    for filename,columns,records in [
        ("X_features.csv",FEATURE_COLS,features),
        ("y_targets.csv",TARGET_COLS,targets),
    ]:
        with (output/filename).open("w",newline="",encoding="utf-8") as fo:
            wr=csv.DictWriter(fo,fieldnames=columns,extrasaction="raise")
            wr.writeheader()
            wr.writerows(records)
    manifest={
      "status":"PRIVATE RETROSPECTIVE PAIRS; availability unverified",
      "forecast_validation_completed":False,
      "model_training_completed":False,
      "cutoff_local":args.cutoff_local,
      "source_database_mode":"readonly SQLite query_only",
      "history":"four tests including anchor, intervals 9-21min, <=60min",
      "horizon_target":"60min +-4min after test end, same direction/regime",
      "transition_guard":"exclude start/end horizon within +-90min of interventions",
      "observed_timestamp_asof_only":True,
      "available_at_verified":False,
      "data_quality":"OK, route=1, ping OK, frequency and bandwidth known",
      "rf_weather_age_max_minutes":10,
      "future_missingness":"targets only from successful future tests; coverage bias",
      "counts":dict(count),"cohorts":dict(cohort),
      "output_sha256":{name:hash_file(output/name) for name in ("X_features.csv","y_targets.csv")},
      "privacy":"Local only; do not upload raw records to public GitHub",
    }
    with (output/"manifest.json").open("w",encoding="utf-8") as fh:
        json.dump(manifest,fh,ensure_ascii=False,indent=2)
    # Print only aggregated, non-sensitive metadata, not samples or absolute paths.
    print(json.dumps({"pairs":len(features),"rf":cohort["rf_eligible"],
       "rf_weather":cohort["dual_weather_eligible"],
       "tests_in_cutoff":count["tests_in_cutoff"],
       "config_direction_counts":{k:v for k,v in cohort.items() if k.startswith("regime_")},
       "sha256":manifest["output_sha256"],
       "availability_verified":False},ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
