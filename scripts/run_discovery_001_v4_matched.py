#!/usr/bin/env python3
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd

ROOT = Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0, str(ROOT))
from scientific_discovery.event_sequence_engine import (
    rf_quality_index, detect_drop_events,
)
from scientific_discovery.matched_trajectory_engine import (
    matched_feature_differences, signed_rank_p, benjamini_hochberg,
)

SOURCE = ROOT / "Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
OUT = ROOT / "Results/scientific_discovery/DISCOVERY-001/v4"
OUT.mkdir(parents=True, exist_ok=True)

DISCOVERY_N = 2145
ATM = [
    "cu01_local_temp_avg_c", "cu01_local_hum_avg_pct",
    "sj01_local_temp_avg_c", "sj01_local_hum_avg_pct",
    "sj01_local_press_hpa", "sj01_local_wind_speed_ms",
]
RF = ["dl_rssi_dbm","ul_rssi_dbm","dl_snr_db","ul_snr_db","dl_mcs","ul_mcs"]
KINDS = ["d30", "d60", "std60"]
RF_DROP_QUANTILE = 0.075

df = pd.read_csv(SOURCE)
df["t"] = pd.to_datetime(df["rf_timestamp_utc"], utc=True, errors="raise")
D0 = df.iloc[:DISCOVERY_N].copy()
C0 = df.iloc[DISCOVERY_N:].copy()

def resample(x):
    return x.set_index("t")[ATM + RF].resample("5min").median()

D = resample(D0)
C = resample(C0)

Dq, rf_med, rf_scale = rf_quality_index(D)
Cq, _, _ = rf_quality_index(C, med=rf_med, scale=rf_scale)
Ddq = Dq.diff(3)
Cdq = Cq.diff(3)
rf_drop_threshold = float(Ddq.quantile(RF_DROP_QUANTILE))
drop_D = detect_drop_events(Ddq, rf_drop_threshold)
drop_C = detect_drop_events(Cdq, rf_drop_threshold)

rows = []
for column in ATM:
    for kind in KINDS:
        md = matched_feature_differences(D, drop_D, column, kind)
        mc = matched_feature_differences(C, drop_C, column, kind)
        rows.append({
            "feature": f"{column}__{kind}",
            "column": column,
            "kind": kind,
            "n_discovery": len(md),
            "median_controls_discovery": float(md["n_controls"].median()) if len(md) else np.nan,
            "pre_median_discovery": float(md["pre_diff"].median()) if len(md) else np.nan,
            "pre_p_discovery": signed_rank_p(md["pre_diff"]) if len(md) else np.nan,
            "post_median_discovery": float(md["post_diff"].median()) if len(md) else np.nan,
            "post_p_discovery": signed_rank_p(md["post_diff"]) if len(md) else np.nan,
            "n_characterization": len(mc),
            "median_controls_characterization": float(mc["n_controls"].median()) if len(mc) else np.nan,
            "pre_median_characterization": float(mc["pre_diff"].median()) if len(mc) else np.nan,
            "pre_p_characterization": signed_rank_p(mc["pre_diff"]) if len(mc) else np.nan,
            "post_median_characterization": float(mc["post_diff"].median()) if len(mc) else np.nan,
            "post_p_characterization": signed_rank_p(mc["post_diff"]) if len(mc) else np.nan,
        })

screen = pd.DataFrame(rows)
screen["pre_q_discovery"] = benjamini_hochberg(screen["pre_p_discovery"])
screen["pre_q_characterization"] = benjamini_hochberg(screen["pre_p_characterization"])
screen["same_sign"] = (
    np.sign(screen["pre_median_discovery"]) ==
    np.sign(screen["pre_median_characterization"])
)
screen["fdr_pass_both"] = (
    (screen["pre_q_discovery"] <= 0.05)
    & (screen["pre_q_characterization"] <= 0.05)
)
screen["post_negative_control_pass"] = (
    (screen["post_p_discovery"] > 0.05)
    & (screen["post_p_characterization"] > 0.05)
)
screen["control_support_pass"] = (
    (screen["median_controls_discovery"] >= 2)
    & (screen["median_controls_characterization"] >= 2)
    & (screen["n_discovery"] >= 30)
    & (screen["n_characterization"] >= 20)
)
screen["all_gates"] = (
    screen["same_sign"]
    & screen["fdr_pass_both"]
    & screen["post_negative_control_pass"]
    & screen["control_support_pass"]
)
screen.to_csv(OUT / "matched_trajectory_screen.csv", index=False)

eligible = screen[screen["same_sign"]].copy()
eligible["worst_q"] = eligible[
    ["pre_q_discovery","pre_q_characterization"]
].max(axis=1)
top = eligible.sort_values(
    ["worst_q","pre_p_discovery","pre_p_characterization"],
    ascending=True,
).iloc[0]

candidate = {
    "candidate_id": "RFATM-0005",
    "candidate_pattern": (
        "Matched same-clock atmospheric trajectory associated with subsequent RF-quality drop"
    ),
    "selected_exploratory_feature": top["feature"],
    "selection_rule": "lowest worst FDR q-value among features preserving effect sign across discovery and characterization",
    "discovery": {
        "n_events": int(top["n_discovery"]),
        "median_controls_per_event": float(top["median_controls_discovery"]),
        "pre_median_difference": float(top["pre_median_discovery"]),
        "pre_p": float(top["pre_p_discovery"]),
        "pre_q": float(top["pre_q_discovery"]),
        "post_median_difference": float(top["post_median_discovery"]),
        "post_p": float(top["post_p_discovery"]),
    },
    "characterization": {
        "n_events": int(top["n_characterization"]),
        "median_controls_per_event": float(top["median_controls_characterization"]),
        "pre_median_difference": float(top["pre_median_characterization"]),
        "pre_p": float(top["pre_p_characterization"]),
        "pre_q": float(top["pre_q_characterization"]),
        "post_median_difference": float(top["post_median_characterization"]),
        "post_p": float(top["post_p_characterization"]),
    },
    "gates": {
        "same_sign": bool(top["same_sign"]),
        "fdr_pass_both": bool(top["fdr_pass_both"]),
        "post_negative_control_pass": bool(top["post_negative_control_pass"]),
        "control_support_pass": bool(top["control_support_pass"]),
    },
    "status": "HUMAN_REVIEWED" if bool(top["all_gates"]) else "SCREENED_OUT",
}
failed = [k for k,v in candidate["gates"].items() if not v]
candidate["failed_gates"] = failed
candidate["reason"] = (
    "All matched-trajectory screening gates passed."
    if not failed else
    "Candidate did not satisfy: " + ", ".join(failed)
)
(OUT / "RFATM-0005_screening.json").write_text(
    json.dumps(candidate, indent=2) + "\n", encoding="utf-8"
)

summary = {
    "experiment_id": "DISCOVERY-001",
    "version": "4.0-matched-trajectory",
    "validation_accessed": False,
    "external_replication_accessed": False,
    "rf_drop_quantile": RF_DROP_QUANTILE,
    "rf_drop_threshold": rf_drop_threshold,
    "rf_drop_events": {
        "discovery": len(drop_D),
        "characterization": len(drop_C),
    },
    "features_screened": int(len(screen)),
    "features_same_sign": int(screen["same_sign"].sum()),
    "features_fdr_pass_both": int(screen["fdr_pass_both"].sum()),
    "features_all_gates": int(screen["all_gates"].sum()),
    "candidate": candidate,
    "hypothesis_ready": bool(candidate["status"] == "HUMAN_REVIEWED"),
}
(OUT / "v4_summary.json").write_text(
    json.dumps(summary, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(summary, indent=2))
