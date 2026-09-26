#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import pandas as pd

ROOT = Path("/home/carlos/Proyectos/EstacionMeteorologica")
SOURCE = ROOT / "Data/exports/scientific_campaign_6g_integrated.csv"
OUT = ROOT / "Results/scientific_discovery/DISCOVERY-001"
EXPECTED_SHA256 = "2c19cc4ee1a66d23765bb79cc9eb840c1c531b3833ea72e8ffba848a0c96ff6c"

CORE_RF = [
    "dl_rssi_dbm", "ul_rssi_dbm", "dl_snr_db",
    "ul_snr_db", "dl_mcs", "ul_mcs"
]
ATM = [
    "cu01_local_temp_avg_c", "cu01_local_hum_avg_pct",
    "cu01_local_press_hpa", "sj01_local_temp_avg_c",
    "sj01_local_hum_avg_pct", "sj01_local_press_hpa",
    "sj01_local_wind_speed_ms"
]
LAGS_MIN = [0, 5, 10, 15, 30, 60, 90, 120]

def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_discovery():
    if sha256_file(SOURCE) != EXPECTED_SHA256:
        raise RuntimeError("Source dataset hash differs from frozen manifest")
    use = ["rf_timestamp_utc", "field_analysis_valid",
           "operating_frequency_mhz", "channel_bandwidth_mhz"] + CORE_RF + ATM
    df = pd.read_csv(SOURCE, usecols=use)
    df["t"] = pd.to_datetime(df["rf_timestamp_utc"], utc=True, errors="coerce")
    df = df[(df["field_analysis_valid"] == 1)
            & (df["operating_frequency_mhz"] == 7000)
            & (df["channel_bandwidth_mhz"] == 20)]
    df = df.dropna(subset=CORE_RF + ATM).sort_values("t").reset_index(drop=True)
    if len(df) != 3576:
        raise RuntimeError(f"Frozen cohort expected 3576 rows, found {len(df)}")
    return df.iloc[:2145].copy()

def build_features(df):
    x = df.set_index("t")[ATM + CORE_RF].resample("5min").median()
    for c in ATM + CORE_RF:
        x[c + "__d5"] = x[c].diff()
        x[c + "__d15"] = x[c].diff(3)
    return x

def discover(x):
    atmospheric = ATM + [c for c in x.columns
                         if (c.endswith("__d5") or c.endswith("__d15"))
                         and any(c.startswith(a) for a in ATM)]
    responses = CORE_RF + [c for c in x.columns
                           if (c.endswith("__d5") or c.endswith("__d15"))
                           and any(c.startswith(r) for r in CORE_RF)]
    rows = []
    for a in atmospheric:
        for r in responses:
            for lag in LAGS_MIN:
                steps = lag // 5
                pair = pd.concat([x[a], x[r].shift(-steps)], axis=1).dropna()
                if len(pair) < 100:
                    continue
                rho = pair.iloc[:, 0].corr(pair.iloc[:, 1], method="spearman")
                rows.append({
                    "atmospheric_feature": a,
                    "rf_response": r,
                    "lag_minutes": lag,
                    "n": len(pair),
                    "spearman_rho": float(rho)
                })
    out = pd.DataFrame(rows)
    out["abs_rho"] = out["spearman_rho"].abs()
    return out.sort_values(["abs_rho", "n"], ascending=[False, False])

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    discovery = load_discovery()
    features = build_features(discovery)
    candidates = discover(features)
    candidates.head(50).to_csv(OUT / "discovery_candidates.csv", index=False)
    dynamic = candidates[
        candidates["atmospheric_feature"].str.contains("__d", regex=False)
        & candidates["rf_response"].str.contains("__d", regex=False)
    ]
    dynamic.head(50).to_csv(OUT / "dynamic_candidates.csv", index=False)
    summary = {
        "experiment_id": "DISCOVERY-001",
        "stage": "DISCOVERY_ONLY",
        "validation_accessed": False,
        "source_sha256": EXPECTED_SHA256,
        "discovery_rows": len(discovery),
        "resampled_5min_rows": len(features),
        "candidate_tests": len(candidates),
        "top_candidate": candidates.iloc[0].to_dict() if len(candidates) else None,
        "interpretation": "Exploratory ranking only; not statistical confirmation."
    }
    (OUT / "discovery_run_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))
    print("\nTop 10 exploratory associations:")
    print(candidates.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
