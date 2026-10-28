#!/usr/bin/env python3
"""FEDU 2026: audit pairs for future throughput without modifying production.

This is a retrospective ELIGIBILITY audit, not evidence of operational data
availability or model validation. Prints aggregate statistics only.
"""
import argparse
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import csv
import json
import math
import sqlite3
from pathlib import Path

VALID_FREQ = {6475, 6655, 7000}
VALID_BW = {20, 40}
HORIZON = timedelta(minutes=60)
TOL = timedelta(minutes=4)
HISTORY = timedelta(minutes=60)
EXTRA_GUARD = timedelta(minutes=30)
MAX_SOURCE_AGE = timedelta(minutes=10)
MIN_STEP = timedelta(minutes=9)
MAX_STEP = timedelta(minutes=21)


def parse(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def source_usable(source_time, anchor):
    observed = parse(source_time)
    return observed is not None and (anchor - MAX_SOURCE_AGE) <= observed <= anchor


def load_transitions(schedule, events):
    transitions = []
    with open(schedule, encoding="utf-8", newline="") as fh:
        lines = list(csv.DictReader(fh))
    for row in lines[1:]:
        stamp = parse(row.get("start_local"))
        if stamp:
            transitions.append(stamp)
    counts = Counter()
    with open(events, encoding="utf-8") as fh:
        for line in fh:
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                counts["invalid_json"] += 1
                continue
            name = ev.get("event", "")
            counts[name] += 1
            if name in {"SWITCH_START", "SWITCH_FAILED", "SWITCH_COMMITTED",
                        "ROLLBACK_START", "ROLLBACK_FAILED", "ROLLBACK_COMMITTED"}:
                stamp = parse(ev.get("timestamp_utc"))
                if stamp:
                    transitions.append(stamp)
    return sorted(set(transitions)), counts


def near_intervention(ts, transitions):
    # History [t-60,t] and future (t,t+60] must not intersect changes;
    # add 30 minutes for stabilization, conservatively.
    left = ts - HISTORY - EXTRA_GUARD
    right = ts + HORIZON + EXTRA_GUARD
    i = bisect_left(transitions, left)
    return i < len(transitions) and transitions[i] <= right


def valid_basic(x):
    if x["status"] != "OK":
        return False
    if x["route_verified"] != 1:
        return False
    if x["ping_status"] != "OK":
        return False
    if x["direction"] not in ("DL", "UL"):
        return False
    if x["operating_frequency_mhz"] not in VALID_FREQ:
        return False
    if x["channel_bandwidth_mhz"] not in VALID_BW:
        return False
    y = x["measured_throughput_mbps"]
    return isinstance(y, (int, float)) and math.isfinite(y) and y >= 0


def valid_rf(x, anchor):
    if not source_usable(x.get("rf_timestamp_local"), anchor):
        return False
    # Prevent false "zero signal": 0 dBm RSSI on this RF link is not
    # a valid ordinary reading. Do not turn missing/sentinel values into 0.
    for k in ("dl_rssi_dbm", "ul_rssi_dbm", "dl_snr_db", "ul_snr_db"):
        value = x.get(k)
        if value is None or not math.isfinite(value):
            return False
    if x["dl_rssi_dbm"] >= 0 or x["ul_rssi_dbm"] >= 0:
        return False
    return True


def valid_weather(x, anchor):
    for prefix in ("cu01", "sj01"):
        if not source_usable(x.get(prefix+"_weather_timestamp_local"), anchor):
            return False
        for feature in ("temp_c", "hum_pct", "press_hpa"):
            value = x.get(prefix+"_"+feature)
            if value is None or not math.isfinite(value):
                return False
    return True


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--db", type=Path, required=True)
    a.add_argument("--schedule", type=Path, required=True)
    a.add_argument("--events", type=Path, required=True)
    args = a.parse_args()
    conn = sqlite3.connect(args.db.resolve().as_uri()+"?mode=ro", uri=True, timeout=2)
    conn.execute("PRAGMA query_only=ON")
    names = [
        "timestamp_start_local","timestamp_end_local","status","direction",
        "operating_frequency_mhz","channel_bandwidth_mhz",
        "measured_throughput_mbps","route_verified","ping_status",
        "rf_timestamp_local","dl_rssi_dbm","ul_rssi_dbm","dl_snr_db","ul_snr_db",
        "cu01_weather_timestamp_local","sj01_weather_timestamp_local",
        "cu01_temp_c","sj01_temp_c","cu01_hum_pct","sj01_hum_pct",
        "cu01_press_hpa","sj01_press_hpa"]
    columns = {row[1] for row in conn.execute("PRAGMA table_info(active_throughput_6g)")}
    missing = set(names)-columns
    if missing:
        raise RuntimeError("missing expected columns: " + ", ".join(sorted(missing)))
    data = conn.execute("SELECT "+",".join('"'+n+'"' for n in names)+
                        " FROM active_throughput_6g ORDER BY timestamp_end_local").fetchall()
    conn.close()
    transitions, event_counts = load_transitions(args.schedule, args.events)
    counts=Counter()
    by_key=defaultdict(list)
    for item in data:
        x=dict(zip(names,item))
        counts["all_tests"]+=1
        ts=parse(x["timestamp_end_local"])
        if not ts or not valid_basic(x):
            counts["rejected_basic"]+=1
            continue
        x["t"]=ts
        k=(int(x["operating_frequency_mhz"]),int(x["channel_bandwidth_mhz"]),x["direction"])
        by_key[k].append(x)
        counts["basic_eligible"]+=1
    per=defaultdict(Counter)
    retrospective_days=set()
    for key, arr in by_key.items():
        arr.sort(key=lambda x:x["t"])
        tt=[x["t"] for x in arr]
        for i,x in enumerate(arr):
            c=per[key]
            c["basic_eligible"]+=1
            if i < 3:
                continue
            hist=arr[i-3:i+1]
            if any(not(MIN_STEP <= hist[j]["t"]-hist[j-1]["t"] <= MAX_STEP)
                   for j in range(1,4)):
                continue
            if hist[0]["t"] < x["t"]-HISTORY:
                continue
            counts["history_eligible"]+=1
            c["history_eligible"]+=1
            if near_intervention(x["t"],transitions):
                counts["rejected_transition_guard"]+=1
                c["rejected_transition_guard"]+=1
                continue
            counts["stable_history_eligible"]+=1
            c["stable_history_eligible"]+=1
            future=x["t"]+HORIZON
            j=bisect_left(tt, future)
            choices=[u for u in (j-1,j) if 0<=u<len(arr)
                     and 0< (arr[u]["t"]-x["t"]).total_seconds()
                     and abs(arr[u]["t"]-future)<=TOL]
            if not choices:
                counts["missing_matched_future_test"]+=1
                c["missing_matched_future_test"]+=1
                continue
            y=arr[min(choices,key=lambda u:abs(arr[u]["t"]-future))]["measured_throughput_mbps"]
            counts["throughput_only_pairs"]+=1
            c["throughput_only_pairs"]+=1
            retrospective_days.add(x["t"].date().isoformat())
            if valid_rf(x,x["t"]):
                counts["rf_asof_pairs"]+=1
                c["rf_asof_pairs"]+=1
                if valid_weather(x,x["t"]):
                    counts["dual_weather_asof_pairs"]+=1
                    c["dual_weather_asof_pairs"]+=1
            if not valid_rf(x,x["t"]):
                c["excluded_rf"]+=1
            elif not valid_weather(x,x["t"]):
                c["excluded_weather"]+=1
    summary={
        "purpose":"RETROSPECTIVE ELIGIBILITY ONLY - NO PREDICTIVE MODEL TRAINED",
        "operational_available_at_proven":False,
        "db_production_access":"SQLite URI mode=ro, PRAGMA query_only=ON",
        "forecast_target":"future measured iperf3 throughput, same config and direction",
        "forecast_anchor":"timestamp_end_local (provisional observed data time; ingestion unavailable)",
        "horizon_minutes":60,"target_tolerance_minutes":4,
        "past_history": "4 measurements, 9-21 min apart, covering <=60 min",
        "transition_rule":"exclude interventions within anchor [-90,+90] minutes",
        "rf_weather_data_age":"max 10 min and timestamp <= anchor",
        "transitions_read":len(transitions),
        "campaign_events":dict(event_counts),
        "counts":dict(counts),
        "retrospective_distinct_anchor_days":len(retrospective_days),
        "by_configuration_direction":{
            str(k[0])+"_"+str(k[1])+"_"+k[2]:dict(v)
            for k,v in sorted(per.items())},
        "limitations":[
            "No ingested_at or available_at in source schema; source timestamp <=t is necessary but not sufficient.",
            "No prospective holdout examined. Results are eligibility counts, NOT predictive accuracy.",
            "Future OK targets are observable-subset only; missing or ERROR targets excluded from MAE, coverage must be reported.",
            "Intervention filters are exploratory, must be version-frozen before final evaluation.",
            "Two observation stations share a single radio link; no independent link replication."
        ]
    }
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
