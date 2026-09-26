from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

def trajectory_stat(series: pd.Series, t: pd.Timestamp, kind: str, direction: str):
    if direction not in {"pre", "post"}:
        raise ValueError("direction must be pre or post")
    sign = -1 if direction == "pre" else 1
    t30 = t + sign * pd.Timedelta("30min")
    t60 = t + sign * pd.Timedelta("60min")
    if t not in series.index or t30 not in series.index or t60 not in series.index:
        return None
    v0, v30, v60 = series.loc[t], series.loc[t30], series.loc[t60]
    if pd.isna(v0) or pd.isna(v30) or pd.isna(v60):
        return None
    if kind == "d30":
        return float(v0 - v30) if direction == "pre" else float(v30 - v0)
    if kind == "d60":
        return float(v0 - v60) if direction == "pre" else float(v60 - v0)
    if kind == "std60":
        a, b = (t60, t) if direction == "pre" else (t, t60)
        win = series.loc[a:b]
        if win.notna().sum() < 8:
            return None
        return float(win.std())
    raise ValueError(f"unknown kind: {kind}")

def matched_feature_differences(frame, rf_events, column, kind, max_day_shift=10):
    rows = []
    start, end = frame.index.min(), frame.index.max()
    rf_events = list(rf_events)
    for t in rf_events:
        event_pre = trajectory_stat(frame[column], t, kind, "pre")
        event_post = trajectory_stat(frame[column], t, kind, "post")
        if event_pre is None or event_post is None:
            continue
        control_pre, control_post = [], []
        for shift in range(-max_day_shift, max_day_shift + 1):
            if shift == 0:
                continue
            tc = t + pd.Timedelta(days=shift)
            if tc < start or tc > end:
                continue
            if any(abs((r - tc).total_seconds()) <= 1800 for r in rf_events):
                continue
            cpre = trajectory_stat(frame[column], tc, kind, "pre")
            cpost = trajectory_stat(frame[column], tc, kind, "post")
            if cpre is not None and cpost is not None:
                control_pre.append(cpre)
                control_post.append(cpost)
        if not control_pre:
            continue
        rows.append({
            "event_time": t,
            "n_controls": len(control_pre),
            "pre_diff": event_pre - float(np.median(control_pre)),
            "post_diff": event_post - float(np.median(control_post)),
        })
    return pd.DataFrame(rows)

def signed_rank_p(values):
    x = pd.Series(values).dropna().to_numpy(dtype=float)
    if len(x) < 10 or np.allclose(x, 0):
        return np.nan
    try:
        return float(wilcoxon(x).pvalue)
    except Exception:
        return np.nan

def benjamini_hochberg(pvalues):
    p = np.asarray(pvalues, dtype=float)
    q = np.full(len(p), np.nan)
    valid = np.isfinite(p)
    vals = p[valid]
    if not len(vals):
        return q
    order = np.argsort(vals)
    ranked = vals[order]
    m = len(ranked)
    adjusted = ranked * m / np.arange(1, m + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    restored = np.empty(m)
    restored[order] = np.minimum(adjusted, 1.0)
    q[np.where(valid)[0]] = restored
    return q
