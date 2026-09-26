from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.cluster.vq import kmeans2

ATM_TRANSITION_FEATURES = [
    "cu01_local_temp_avg_c",
    "cu01_local_hum_avg_pct",
    "sj01_local_temp_avg_c",
    "sj01_local_hum_avg_pct",
    "sj01_local_press_hpa",
    "sj01_local_wind_speed_ms",
]
RF_FEATURES = [
    "dl_rssi_dbm","ul_rssi_dbm","dl_snr_db",
    "ul_snr_db","dl_mcs","ul_mcs"
]

def robust_scale(discovery_delta: pd.DataFrame):
    med = discovery_delta.median()
    mad = (discovery_delta - med).abs().median()
    iqr = (discovery_delta.quantile(.75) - discovery_delta.quantile(.25)) / 1.349
    std = discovery_delta.std(ddof=0)
    scale = (1.4826 * mad).where(mad > 0, iqr).where(lambda s: s > 0, std)
    return med, scale.replace(0, 1.0)

def transition_matrix(frame: pd.DataFrame, med, scale, steps=3):
    delta = frame[ATM_TRANSITION_FEATURES].diff(steps)
    z = ((delta - med) / scale).clip(-8, 8)
    active = (z.abs() >= 1.5).sum(axis=1)
    score = np.sqrt((z * z).mean(axis=1)).where(active >= 2)
    return z, score, active

def detect_peaks(score: pd.Series, threshold: float, refractory_min=30):
    events, last = [], None
    for t, v in score.dropna().items():
        if v < threshold:
            continue
        local = score.loc[t-pd.Timedelta("10min"):t+pd.Timedelta("10min")]
        if v < local.max():
            continue
        if last is None or t-last >= pd.Timedelta(minutes=refractory_min):
            events.append(t)
            last = t
    return events

def fit_archetypes(event_z: pd.DataFrame, k: int, seed=42):
    centers, labels = kmeans2(event_z.to_numpy(), k, minit="++", iter=100, seed=seed)
    return centers, pd.Series(labels, index=event_z.index)

def assign_archetypes(event_z: pd.DataFrame, centers):
    arr = event_z.to_numpy()
    dist = ((arr[:,None,:] - centers[None,:,:])**2).sum(axis=2)
    return pd.Series(dist.argmin(axis=1), index=event_z.index)

def rf_quality_reference(discovery: pd.DataFrame):
    med = discovery[RF_FEATURES].median()
    mad = (discovery[RF_FEATURES] - med).abs().median()
    iqr = (discovery[RF_FEATURES].quantile(.75)-discovery[RF_FEATURES].quantile(.25))/1.349
    std = discovery[RF_FEATURES].std(ddof=0)
    scale = (1.4826*mad).where(mad>0,iqr).where(lambda s:s>0,std).replace(0,1.0)
    q = ((discovery[RF_FEATURES]-med)/scale).mean(axis=1)
    return med, scale, float(q.quantile(.10))

def rf_entry_events(frame: pd.DataFrame, med, scale, threshold, refractory_min=30):
    q = ((frame[RF_FEATURES]-med)/scale).mean(axis=1)
    bad = q <= threshold
    out, last, prev = [], None, False
    for t, b in bad.fillna(False).items():
        if b and not prev:
            if last is None or t-last >= pd.Timedelta(minutes=refractory_min):
                out.append(t); last=t
        prev = bool(b)
    return out

def archetype_event_risk(index, event_times, labels, rf_entries, archetype, horizon_min):
    starts = pd.date_range(index.min().floor("30min"), index.max().ceil("30min"),
                           freq="30min", inclusive="left")
    exposed, outcome = [], []
    selected = set(labels[labels == archetype].index)
    for t in starts:
        exposed.append(any(t <= e < t+pd.Timedelta("30min") for e in selected))
        outcome.append(any(t <= r < t+pd.Timedelta(minutes=horizon_min) for r in rf_entries))
    tab = pd.crosstab(pd.Series(exposed), pd.Series(outcome)).reindex(
        index=[False,True], columns=[False,True], fill_value=0)
    def risk(flag):
        row=tab.loc[flag]; n=int(row.sum()); ev=int(row.get(True,0))
        return (ev/n if n else np.nan), n, ev
    re, ne, ee = risk(True); ru, nu, eu = risk(False)
    rr = re/ru if np.isfinite(re) and np.isfinite(ru) and ru>0 else np.nan
    return {"risk_ratio":rr,"risk_exposed":re,"risk_unexposed":ru,
            "blocks_exposed":ne,"blocks_unexposed":nu,
            "events_exposed":ee,"events_unexposed":eu}

def risk_ratio_ci(events_exposed, total_exposed, events_unexposed, total_unexposed, z=1.96):
    if min(total_exposed, total_unexposed) <= 0:
        return np.nan, np.nan, np.nan
    # Haldane-Anscombe correction only when a cell is zero.
    a=float(events_exposed); b=float(total_exposed-events_exposed)
    c=float(events_unexposed); d=float(total_unexposed-events_unexposed)
    if min(a,b,c,d) == 0:
        a+=0.5; b+=0.5; c+=0.5; d+=0.5
    re=a/(a+b); ru=c/(c+d)
    rr=re/ru
    se=np.sqrt((1/a)-(1/(a+b))+(1/c)-(1/(c+d)))
    lo=np.exp(np.log(rr)-z*se)
    hi=np.exp(np.log(rr)+z*se)
    return float(rr), float(lo), float(hi)
