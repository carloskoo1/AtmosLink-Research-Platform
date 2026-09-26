#!/usr/bin/env python3
from pathlib import Path
import json
import sys
import pandas as pd

ROOT = Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0, str(ROOT))
from scientific_discovery.robust_screening import (
    fit_rf_quality_reference, rf_degraded, block_risk
)

SOURCE = ROOT / "Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
OUT = ROOT / "Results/scientific_discovery/DISCOVERY-001/v2"
df = pd.read_csv(SOURCE)
df["t"] = pd.to_datetime(df["rf_timestamp_utc"], utc=True, errors="raise")

discovery = df.iloc[:2145].copy()
characterization = df.iloc[2145:2860].copy()
med, scale, threshold = fit_rf_quality_reference(discovery)

def cold_humid_calm(x):
    return (
        (x["sj01_local_hum_avg_pct"] >= 90)
        & (x["sj01_local_temp_avg_c"] <= 8)
        & (x["sj01_local_wind_speed_ms"] <= 3)
        & (x["cu01_local_hum_avg_pct"] >= 55)
        & (x["cu01_local_temp_avg_c"] <= 19)
    )

disc_exp = cold_humid_calm(discovery)
char_exp = cold_humid_calm(characterization)
disc_bad = rf_degraded(discovery, med, scale, threshold)
char_bad = rf_degraded(characterization, med, scale, threshold)

disc_block = block_risk(discovery, disc_exp, disc_bad, minutes=30)
char_block = block_risk(characterization, char_exp, char_bad, minutes=30)
same_direction = (
    disc_block["risk_ratio"] is not None
    and char_block["risk_ratio"] is not None
    and disc_block["risk_ratio"] > 1
    and char_block["risk_ratio"] > 1
)

result = {
    "experiment_id": "DISCOVERY-001",
    "version": "2.1-consensus-screen",
    "validation_accessed": False,
    "candidate_id": "RFATM-0003",
    "candidate_name": "cold_humid_calm_atmospheric_regime",
    "candidate_origin": "recurrent atmospheric state across k/seed ablations",
    "operational_definition": {
        "sj01_humidity_pct_min": 90,
        "sj01_temperature_c_max": 8,
        "sj01_wind_ms_max": 3,
        "cu01_humidity_pct_min": 55,
        "cu01_temperature_c_max": 19
    },
    "rf_degradation_definition": {
        "metric": "mean robust-z across RSSI/SNR/MCS DL+UL",
        "threshold": threshold,
        "threshold_source": "10th percentile of D_discovery only"
    },
    "temporal_independence_screen": {
        "block_minutes": 30,
        "discovery": disc_block,
        "characterization": char_block
    },
    "same_direction_after_blocking": bool(same_direction),
    "status": "HUMAN_REVIEWED" if same_direction else "SCREENED_OUT",
    "reason": (
        "Candidate preserved elevated block-level RF degradation risk."
        if same_direction else
        "Candidate failed temporal-independence replication in characterization."
    )
}
(OUT / "consensus_screening.json").write_text(json.dumps(result, indent=2, default=str)+"\n", encoding="utf-8")
print(json.dumps(result, indent=2, default=str))
