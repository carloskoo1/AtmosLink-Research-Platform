from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.cluster.vq import kmeans2

ATM_FEATURES = [
    "cu01_local_temp_avg_c", "cu01_local_hum_avg_pct", "cu01_local_press_hpa",
    "sj01_local_temp_avg_c", "sj01_local_hum_avg_pct", "sj01_local_press_hpa",
    "sj01_local_wind_speed_ms"
]
RF_FEATURES = [
    "dl_rssi_dbm", "ul_rssi_dbm", "dl_snr_db",
    "ul_snr_db", "dl_mcs", "ul_mcs"
]

def temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    x = df.set_index("t")[ATM_FEATURES + RF_FEATURES].resample("5min").median()
    for c in ATM_FEATURES + RF_FEATURES:
        x[c + "__d15"] = x[c].diff(3)
        x[c + "__std30"] = x[c].rolling(6, min_periods=4).std()
    return x

def fit_standardizer(frame: pd.DataFrame, cols: list[str]):
    clean = frame[cols].copy()
    mu = clean.mean()
    sigma = clean.std(ddof=0).replace(0, 1.0)
    return mu, sigma

def transform(frame: pd.DataFrame, cols: list[str], mu, sigma):
    return ((frame[cols] - mu) / sigma).replace([np.inf, -np.inf], np.nan)

def fit_states(z: pd.DataFrame, k: int, seed: int = 42):
    good = z.dropna()
    if len(good) < max(100, k * 20):
        raise RuntimeError("Insufficient complete rows for state discovery")
    centroids, labels = kmeans2(good.to_numpy(), k, minit="++", iter=100, seed=seed)
    out = pd.Series(index=z.index, dtype="Int64")
    out.loc[good.index] = labels
    return centroids, out

def assign_states(z: pd.DataFrame, centroids: np.ndarray):
    good = z.dropna()
    out = pd.Series(index=z.index, dtype="Int64")
    if len(good):
        a = good.to_numpy()
        d = ((a[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
        out.loc[good.index] = d.argmin(axis=1)
    return out

def state_profiles(frame: pd.DataFrame, labels: pd.Series, cols: list[str]):
    tmp = frame[cols].copy()
    tmp["state"] = labels
    return tmp.dropna(subset=["state"]).groupby("state")[cols].median()

def degraded_rf_state(rf_centroids: np.ndarray) -> int:
    # RF columns are oriented so larger standardized values imply better link state.
    quality = np.nanmean(rf_centroids, axis=1)
    return int(np.nanargmin(quality))

def transition_candidates(atm_state, rf_state, degraded_state, lags=(0, 15, 30, 60, 120)):
    rows = []
    valid_rf = rf_state.notna()
    baseline = float((rf_state[valid_rf] == degraded_state).mean()) if valid_rf.any() else np.nan
    for state in sorted(int(x) for x in atm_state.dropna().unique()):
        for lag in lags:
            steps = lag // 5
            future = rf_state.shift(-steps)
            mask = (atm_state == state) & future.notna()
            n = int(mask.sum())
            if n < 50 or not np.isfinite(baseline) or baseline <= 0:
                continue
            p = float((future[mask] == degraded_state).mean())
            rows.append({
                "atmospheric_state": state,
                "lag_minutes": lag,
                "support_n": n,
                "p_degraded": p,
                "baseline_p_degraded": baseline,
                "lift": p / baseline
            })
    return pd.DataFrame(rows).sort_values(["lift", "support_n"], ascending=[False, False])
