from __future__ import annotations
import numpy as np
import pandas as pd

RF_FEATURES = [
    "dl_rssi_dbm", "ul_rssi_dbm", "dl_snr_db",
    "ul_snr_db", "dl_mcs", "ul_mcs"
]

def robust_location_scale(frame: pd.DataFrame):
    med = frame.median()
    mad = (frame - med).abs().median()
    iqr = (frame.quantile(0.75) - frame.quantile(0.25)) / 1.349
    std = frame.std(ddof=0)
    scale = (1.4826 * mad).where(mad > 0, iqr)
    scale = scale.where(scale > 0, std).replace(0, 1.0).fillna(1.0)
    return med, scale

def standardized_delta(frame, cols, periods, med=None, scale=None, clip=8.0):
    delta = frame[cols].diff(periods)
    if med is None or scale is None:
        med, scale = robust_location_scale(delta)
    z = ((delta - med) / scale).clip(-clip, clip)
    return z, med, scale

def multivariate_transition_score(z, min_active=2, active_z=1.5):
    active = (z.abs() >= active_z).sum(axis=1)
    score = np.sqrt((z * z).mean(axis=1))
    return score.where(active >= min_active)

def detect_peaks(score, threshold, refractory_minutes=30, local_window_minutes=10):
    events = []
    last = None
    for t, value in score.dropna().items():
        if value < threshold:
            continue
        local = score.loc[
            t - pd.Timedelta(minutes=local_window_minutes):
            t + pd.Timedelta(minutes=local_window_minutes)
        ]
        if value < local.max():
            continue
        if last is None or t - last >= pd.Timedelta(minutes=refractory_minutes):
            events.append(t)
            last = t
    return events

def rf_quality_index(frame, med=None, scale=None):
    if med is None or scale is None:
        med, scale = robust_location_scale(frame[RF_FEATURES])
    quality = ((frame[RF_FEATURES] - med) / scale).mean(axis=1)
    return quality, med, scale

def detect_drop_events(delta_quality, threshold, refractory_minutes=30):
    events = []
    last = None
    for t, value in delta_quality.dropna().items():
        if value > threshold:
            continue
        local = delta_quality.loc[t-pd.Timedelta("10min"):t+pd.Timedelta("10min")]
        if value > local.min():
            continue
        if last is None or t - last >= pd.Timedelta(minutes=refractory_minutes):
            events.append(t)
            last = t
    return events

def exact_direction_stats(atmospheric_events, rf_events, horizon_minutes):
    horizon = pd.Timedelta(minutes=horizon_minutes)
    future = 0
    past = 0
    for t in atmospheric_events:
        future += int(any(t < r <= t + horizon for r in rf_events))
        past += int(any(t - horizon <= r < t for r in rf_events))
    n = len(atmospheric_events)
    return {
        "n_atmospheric_events": n,
        "future_events": future,
        "past_events": past,
        "future_risk": future / n if n else None,
        "past_risk": past / n if n else None,
        "future_minus_past": (future - past) / n if n else None,
        "direction_pass": bool(n and future > past),
    }

def block_risk_ratio(index, atmospheric_events, rf_events, horizon_minutes):
    anchors = pd.date_range(
        index.min().floor("30min"), index.max().ceil("30min"),
        freq="30min", inclusive="left"
    )
    rows = []
    horizon = pd.Timedelta(minutes=horizon_minutes)
    for t in anchors:
        exposed = any(t <= a < t + pd.Timedelta("30min") for a in atmospheric_events)
        outcome = any(t <= r < t + horizon for r in rf_events)
        rows.append((exposed, outcome))
    tab = pd.crosstab(
        pd.Series([r[0] for r in rows], name="exposed"),
        pd.Series([r[1] for r in rows], name="outcome"),
    ).reindex(index=[False, True], columns=[False, True], fill_value=0)
    def risk(flag):
        row = tab.loc[flag]
        n = int(row.sum())
        events = int(row.get(True, 0))
        return (events / n if n else np.nan), n, events
    re, ne, ee = risk(True)
    ru, nu, eu = risk(False)
    rr = re / ru if np.isfinite(re) and np.isfinite(ru) and ru > 0 else np.nan
    return {
        "risk_ratio": float(rr) if np.isfinite(rr) else None,
        "risk_exposed": float(re) if np.isfinite(re) else None,
        "risk_unexposed": float(ru) if np.isfinite(ru) else None,
        "n_exposed_blocks": ne, "n_unexposed_blocks": nu,
        "outcomes_exposed": ee, "outcomes_unexposed": eu,
    }

def local_hour_profile(events, utc_offset_hours=-5):
    bins = {k: 0 for k in ["00-02","03-05","06-08","09-11","12-14","15-17","18-20","21-23"]}
    for t in events:
        h = (t + pd.Timedelta(hours=utc_offset_hours)).hour
        key = ["00-02","03-05","06-08","09-11","12-14","15-17","18-20","21-23"][h // 3]
        bins[key] += 1
    return bins
