#!/usr/bin/env python3
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd

ROOT = Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0, str(ROOT))
from scientific_discovery.structured_state_engine import (
    ATM_FEATURES, RF_FEATURES, temporal_features, fit_standardizer,
    transform, fit_states, assign_states, state_profiles,
    degraded_rf_state, transition_candidates
)

SOURCE = ROOT / "Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
OUT = ROOT / "Results/scientific_discovery/DISCOVERY-001/v2"
OUT.mkdir(parents=True, exist_ok=True)

DISCOVERY_N = 2145
CHAR_N = 715
ATM_K = 4
RF_K = 3

df = pd.read_csv(SOURCE)
df["t"] = pd.to_datetime(df["rf_timestamp_utc"], utc=True, errors="raise")
if len(df) != DISCOVERY_N + CHAR_N:
    raise RuntimeError("Prevalidation snapshot row count mismatch")

disc_raw = df.iloc[:DISCOVERY_N].copy()
char_raw = df.iloc[DISCOVERY_N:].copy()

disc = temporal_features(disc_raw)
char = temporal_features(char_raw)

atm_cols = ATM_FEATURES + [c for c in disc.columns if c.startswith(tuple(ATM_FEATURES)) and ("__d15" in c or "__std30" in c)]
rf_cols = RF_FEATURES

atm_mu, atm_sigma = fit_standardizer(disc, atm_cols)
rf_mu, rf_sigma = fit_standardizer(disc, rf_cols)

disc_atm_z = transform(disc, atm_cols, atm_mu, atm_sigma)
disc_rf_z = transform(disc, rf_cols, rf_mu, rf_sigma)
char_atm_z = transform(char, atm_cols, atm_mu, atm_sigma)
char_rf_z = transform(char, rf_cols, rf_mu, rf_sigma)

atm_centroids, disc_atm_state = fit_states(disc_atm_z, ATM_K, seed=42)
rf_centroids, disc_rf_state = fit_states(disc_rf_z, RF_K, seed=84)

char_atm_state = assign_states(char_atm_z, atm_centroids)
char_rf_state = assign_states(char_rf_z, rf_centroids)

bad_rf = degraded_rf_state(rf_centroids)

disc_candidates = transition_candidates(disc_atm_state, disc_rf_state, bad_rf)
char_candidates = transition_candidates(char_atm_state, char_rf_state, bad_rf)

merged = disc_candidates.merge(
    char_candidates,
    on=["atmospheric_state", "lag_minutes"],
    how="left",
    suffixes=("_discovery", "_characterization")
)
merged["same_direction"] = (
    (merged["lift_discovery"] > 1) & (merged["lift_characterization"] > 1)
)
merged["min_lift"] = merged[["lift_discovery","lift_characterization"]].min(axis=1)
merged["stable_candidate"] = (
    merged["same_direction"]
    & (merged["support_n_characterization"] >= 30)
    & (merged["min_lift"] >= 1.20)
)
merged = merged.sort_values(
    ["stable_candidate","min_lift","support_n_discovery"],
    ascending=[False,False,False]
)

disc_profiles = state_profiles(disc, disc_atm_state, ATM_FEATURES)
char_profiles = state_profiles(char, char_atm_state, ATM_FEATURES)
rf_profiles = state_profiles(disc, disc_rf_state, RF_FEATURES)

disc_profiles.to_csv(OUT / "atmospheric_state_profiles_discovery.csv")
char_profiles.to_csv(OUT / "atmospheric_state_profiles_characterization.csv")
rf_profiles.to_csv(OUT / "rf_state_profiles_discovery.csv")
merged.to_csv(OUT / "transition_candidates_screened.csv", index=False)

stable = merged[merged["stable_candidate"]].copy()
stable.to_csv(OUT / "stable_candidates.csv", index=False)

summary = {
    "experiment_id": "DISCOVERY-001",
    "version": "2.0",
    "validation_accessed": False,
    "prevalidation_snapshot_only": True,
    "atmospheric_states_k": ATM_K,
    "rf_states_k": RF_K,
    "degraded_rf_state": bad_rf,
    "discovery_state_rows": int(disc_atm_state.notna().sum()),
    "characterization_state_rows": int(char_atm_state.notna().sum()),
    "candidate_pairs_tested": int(len(merged)),
    "stable_candidates": int(len(stable)),
    "stable_candidate_definition": "same lift direction, characterization support >=30, min lift >=1.20",
    "novelty_filter": "multivariate atmospheric state -> future RF state; known direct RF-control relations excluded by construction",
    "physical_consistency": "fixed 7000/20 configuration; atmospheric representation excludes RF variables; temporal direction enforced",
    "top_candidates": stable.head(10).to_dict(orient="records")
}
(OUT / "v2_summary.json").write_text(json.dumps(summary, indent=2, default=str)+"\n", encoding="utf-8")
print(json.dumps(summary, indent=2, default=str))
