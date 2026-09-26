from __future__ import annotations
import numpy as np
import pandas as pd

RF_FEATURES = [
    "dl_rssi_dbm","ul_rssi_dbm","dl_snr_db",
    "ul_snr_db","dl_mcs","ul_mcs"
]

def fit_rf_quality_reference(discovery: pd.DataFrame):
    med = discovery[RF_FEATURES].median()
    mad = (discovery[RF_FEATURES] - med).abs().median().replace(0, 1.0)
    scale = 1.4826 * mad
    q = ((discovery[RF_FEATURES] - med) / scale).mean(axis=1)
    threshold = float(q.quantile(0.10))
    return med, scale, threshold

def rf_degraded(frame: pd.DataFrame, med, scale, threshold):
    quality = ((frame[RF_FEATURES] - med) / scale).mean(axis=1)
    return quality <= threshold

def block_risk(frame: pd.DataFrame, exposure: pd.Series, degraded: pd.Series, minutes=30):
    x = pd.DataFrame({
        "t": frame["t"],
        "exposure": exposure.astype(bool),
        "degraded": degraded.astype(bool)
    }).dropna(subset=["t"])
    x["block"] = x["t"].dt.floor(f"{minutes}min")
    b = x.groupby("block").agg(
        exposure_fraction=("exposure","mean"),
        degraded=("degraded","max")
    )
    b["exposed"] = b["exposure_fraction"] >= 0.5
    tab = pd.crosstab(b["exposed"], b["degraded"])
    def risk(flag):
        if flag not in tab.index:
            return np.nan, 0
        n = int(tab.loc[flag].sum())
        events = int(tab.loc[flag].get(True, 0))
        return (events / n if n else np.nan), n
    re, ne = risk(True)
    ru, nu = risk(False)
    rr = re / ru if np.isfinite(re) and np.isfinite(ru) and ru > 0 else np.nan
    return {"risk_exposed": re, "risk_unexposed": ru, "risk_ratio": rr,
            "blocks_exposed": ne, "blocks_unexposed": nu}
