#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import sys
import pandas as pd

ROOT = Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0, str(ROOT))
from scientific_discovery.event_sequence_engine import (
    robust_location_scale, standardized_delta, multivariate_transition_score,
    detect_peaks, rf_quality_index, detect_drop_events,
    exact_direction_stats, block_risk_ratio, local_hour_profile,
)

SOURCE = ROOT / "Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
QC_REPORT = ROOT / "Data/exports/master_quality_report.csv"
OUT = ROOT / "Results/scientific_discovery/DISCOVERY-001/v3"
OUT.mkdir(parents=True, exist_ok=True)

DISCOVERY_N = 2145
CHAR_N = 715
ATM_DYNAMIC = [
    "cu01_local_temp_avg_c", "cu01_local_hum_avg_pct",
    "sj01_local_temp_avg_c", "sj01_local_hum_avg_pct",
    "sj01_local_press_hpa", "sj01_local_wind_speed_ms",
]
RF = ["dl_rssi_dbm","ul_rssi_dbm","dl_snr_db","ul_snr_db","dl_mcs","ul_mcs"]

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

df = pd.read_csv(SOURCE)
df["t"] = pd.to_datetime(df["rf_timestamp_utc"], utc=True, errors="raise")
if len(df) != DISCOVERY_N + CHAR_N:
    raise RuntimeError("Prevalidation snapshot does not match frozen manifest")
discovery_raw = df.iloc[:DISCOVERY_N].copy()
char_raw = df.iloc[DISCOVERY_N:].copy()

qc = pd.read_csv(QC_REPORT)
qc["t"] = pd.to_datetime(qc["timestamp"], utc=True, errors="coerce")
period_qc = qc[
    qc["t"].between(discovery_raw["t"].min(), char_raw["t"].max())
    & qc["severity"].isin(["warning","error","critical"])
]
cu_pressure_jumps = int(
    ((period_qc["station_id"] == "CU01") & (period_qc["issue_type"] == "PRESS_JUMP")).sum()
)

eligibility = {
    "cu01_local_press_hpa": {
        "level_context_allowed": True,
        "dynamic_transition_feature": False,
        "qc_issue": "PRESS_JUMP",
        "qc_events_in_prevalidation_period": cu_pressure_jumps,
        "reason": "Quarantined from dynamic discovery because recurrent instrument jump alerts can dominate derivatives."
    },
    "dynamic_features_used": ATM_DYNAMIC,
}
(OUT / "feature_eligibility.json").write_text(
    json.dumps(eligibility, indent=2) + "\n", encoding="utf-8"
)

def resample(x):
    return x.set_index("t")[ATM_DYNAMIC + RF].resample("5min").median()

D = resample(discovery_raw)
C = resample(char_raw)

Dz, delta_med, delta_scale = standardized_delta(D, ATM_DYNAMIC, periods=3)
Cz, _, _ = standardized_delta(C, ATM_DYNAMIC, periods=3, med=delta_med, scale=delta_scale)
Dscore = multivariate_transition_score(Dz, min_active=2, active_z=1.5)
Cscore = multivariate_transition_score(Cz, min_active=2, active_z=1.5)

Dq, rf_med, rf_scale = rf_quality_index(D)
Cq, _, _ = rf_quality_index(C, med=rf_med, scale=rf_scale)
Ddq = Dq.diff(3)
Cdq = Cq.diff(3)

grid_rows = []
for atm_q in [0.75, 0.80, 0.85, 0.90, 0.95]:
    atm_threshold = float(Dscore.quantile(atm_q))
    atm_D = detect_peaks(Dscore, atm_threshold)
    atm_C = detect_peaks(Cscore, atm_threshold)
    for rf_q in [0.05, 0.075, 0.10]:
        rf_threshold = float(Ddq.quantile(rf_q))
        rf_D = detect_drop_events(Ddq, rf_threshold)
        rf_C = detect_drop_events(Cdq, rf_threshold)
        for horizon in [30, 60, 120]:
            bd = block_risk_ratio(D.index, atm_D, rf_D, horizon)
            bc = block_risk_ratio(C.index, atm_C, rf_C, horizon)
            grid_rows.append({
                "atm_quantile": atm_q, "rf_drop_quantile": rf_q,
                "horizon_minutes": horizon,
                "atm_events_discovery": len(atm_D),
                "atm_events_characterization": len(atm_C),
                "rf_drop_events_discovery": len(rf_D),
                "rf_drop_events_characterization": len(rf_C),
                "rr_discovery": bd["risk_ratio"],
                "rr_characterization": bc["risk_ratio"],
                "both_rr_gt_1": bool(
                    bd["risk_ratio"] is not None and bc["risk_ratio"] is not None
                    and bd["risk_ratio"] > 1 and bc["risk_ratio"] > 1
                ),
            })
grid = pd.DataFrame(grid_rows)
grid.to_csv(OUT / "sequence_sensitivity_grid.csv", index=False)

# Exploratory central reference point in the sensitivity grid.
ATM_Q = 0.80
RF_Q = 0.075
HORIZON = 60
atm_threshold = float(Dscore.quantile(ATM_Q))
rf_threshold = float(Ddq.quantile(RF_Q))
atm_D = detect_peaks(Dscore, atm_threshold)
atm_C = detect_peaks(Cscore, atm_threshold)
rf_D = detect_drop_events(Ddq, rf_threshold)
rf_C = detect_drop_events(Cdq, rf_threshold)

block_D = block_risk_ratio(D.index, atm_D, rf_D, HORIZON)
block_C = block_risk_ratio(C.index, atm_C, rf_C, HORIZON)
direction_D = exact_direction_stats(atm_D, rf_D, HORIZON)
direction_C = exact_direction_stats(atm_C, rf_C, HORIZON)
direction_pass = direction_D["direction_pass"] and direction_C["direction_pass"]

candidate = {
    "candidate_id": "RFATM-0004",
    "candidate_pattern": "multivariate atmospheric transition followed by 15-minute RF-quality drop",
    "stage": "EXPLORATORY_SCREENING",
    "canonical_exploratory_parameters": {
        "atmospheric_score_quantile": ATM_Q,
        "rf_drop_quantile": RF_Q,
        "horizon_minutes": HORIZON,
        "atmospheric_delta_minutes": 15,
        "rf_delta_minutes": 15,
    },
    "block_association": {"discovery": block_D, "characterization": block_C},
    "strict_temporal_direction": {"discovery": direction_D, "characterization": direction_C},
    "direction_pass_both": bool(direction_pass),
    "status": "HUMAN_REVIEWED" if direction_pass else "SCREENED_OUT",
    "reason": (
        "Strict future-over-past temporal direction reproduced."
        if direction_pass else
        "Block association did not survive strict temporal ordering: RF drops were not more frequent after atmospheric transitions than before them."
    ),
}
(OUT / "RFATM-0004_screening.json").write_text(
    json.dumps(candidate, indent=2) + "\n", encoding="utf-8"
)

summary = {
    "experiment_id": "DISCOVERY-001",
    "version": "3.0-sequence-engine",
    "source_snapshot_sha256": sha256(SOURCE),
    "validation_accessed": False,
    "external_replication_accessed": False,
    "cu01_pressure_dynamic_quarantined": True,
    "cu01_pressure_jump_alerts": cu_pressure_jumps,
    "sensitivity_cells": int(len(grid)),
    "cells_rr_gt_1_in_both": int(grid["both_rr_gt_1"].sum()),
    "canonical_atmospheric_events": {
        "discovery": len(atm_D), "characterization": len(atm_C)
    },
    "canonical_rf_drop_events": {
        "discovery": len(rf_D), "characterization": len(rf_C)
    },
    "local_hour_profiles": {
        "atmospheric_discovery": local_hour_profile(atm_D),
        "rf_drop_discovery": local_hour_profile(rf_D),
        "atmospheric_characterization": local_hour_profile(atm_C),
        "rf_drop_characterization": local_hour_profile(rf_C),
    },
    "candidate": candidate,
    "hypothesis_ready": False,
    "next_gate": "No validation access until a candidate survives QC, sensitivity, strict temporal direction, characterization replication, physical plausibility and human review."
}
(OUT / "v3_summary.json").write_text(
    json.dumps(summary, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(summary, indent=2))
