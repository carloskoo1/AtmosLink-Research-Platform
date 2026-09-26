from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import binomtest

RF_FEATURES=["dl_rssi_dbm","ul_rssi_dbm","dl_snr_db","ul_snr_db","dl_mcs","ul_mcs"]

def robust_z(series: pd.Series):
    med=series.median()
    mad=(series-med).abs().median()
    scale=1.4826*mad
    if not np.isfinite(scale) or scale<=0:
        scale=series.std(ddof=0)
    if not np.isfinite(scale) or scale<=0:
        scale=1.0
    return (series-med)/scale

def driver_score(frame: pd.DataFrame):
    dt=frame["sj01_local_temp_avg_c"].diff(3)
    dh=frame["sj01_local_hum_avg_pct"].diff(3)
    return (robust_z(dt)-robust_z(dh))/np.sqrt(2)

def peak_events(score: pd.Series, quantile=.85, refractory_min=60):
    threshold=float(score.quantile(quantile))
    out=[]; last=None
    for t,v in score.dropna().items():
        if v<threshold:
            continue
        local=score.loc[t-pd.Timedelta("10min"):t+pd.Timedelta("10min")]
        if v<local.max():
            continue
        if last is None or t-last>=pd.Timedelta(minutes=refractory_min):
            out.append(t); last=t
    return out,threshold

def robust_reference(frame: pd.DataFrame):
    med=frame[RF_FEATURES].median()
    mad=(frame[RF_FEATURES]-med).abs().median()
    iqr=(frame[RF_FEATURES].quantile(.75)-frame[RF_FEATURES].quantile(.25))/1.349
    std=frame[RF_FEATURES].std(ddof=0)
    scale=(1.4826*mad).where(mad>0,iqr).where(lambda s:s>0,std).replace(0,1.0)
    return med,scale

def rf_quality(frame: pd.DataFrame, med, scale):
    return ((frame[RF_FEATURES]-med)/scale).mean(axis=1)

def inject_degradation(frame: pd.DataFrame, event_times, lag_min, effect_sd,
                       duration_min=15, activation_prob=.70, seed=0):
    rng=np.random.default_rng(seed)
    x=frame.copy()
    med,scale=robust_reference(frame)
    activated=[]
    for t in event_times:
        if rng.random()>activation_prob:
            continue
        start=t+pd.Timedelta(minutes=lag_min)
        end=start+pd.Timedelta(minutes=duration_min)
        mask=(x.index>=start)&(x.index<end)
        if not mask.any():
            continue
        x.loc[mask,RF_FEATURES]=x.loc[mask,RF_FEATURES]-effect_sd*scale.values
        activated.append(t)
    return x,activated

def detect_drop_entries(frame, med, scale, quantile=.075, refractory_min=30):
    q=rf_quality(frame,med,scale)
    dq=q.diff(3)
    thr=float(dq.quantile(quantile))
    low=dq<=thr
    events=[]; last=None
    for t,b in low.fillna(False).items():
        if b and (last is None or t-last>=pd.Timedelta(minutes=refractory_min)):
            events.append(t); last=t
    return events,thr

def directional_test(driver_events, rf_events, horizon_min):
    post_only=pre_only=both=neither=0
    for e in driver_events:
        pre=any(e-pd.Timedelta(minutes=horizon_min)<=r<e for r in rf_events)
        post=any(e<r<=e+pd.Timedelta(minutes=horizon_min) for r in rf_events)
        if post and not pre: post_only+=1
        elif pre and not post: pre_only+=1
        elif pre and post: both+=1
        else: neither+=1
    discordant=post_only+pre_only
    p=binomtest(post_only,discordant,.5,alternative="greater").pvalue if discordant else 1.0
    return {
        "n_driver_events":len(driver_events),
        "post_only":post_only,
        "pre_only":pre_only,
        "both":both,
        "neither":neither,
        "discordant":discordant,
        "p_value":float(p),
        "post_minus_pre":post_only-pre_only,
    }

def fold_consistency(driver_events,rf_events,bounds,horizon_min):
    stats=[]
    for a,b in bounds:
        de=[t for t in driver_events if a<=t<=b]
        re=[t for t in rf_events if a-pd.Timedelta(minutes=horizon_min)<=t<=b+pd.Timedelta(minutes=horizon_min)]
        stats.append(directional_test(de,re,horizon_min))
    positive=sum(s["post_only"]>s["pre_only"] for s in stats)
    nonnegative=sum(s["post_only"]>=s["pre_only"] for s in stats)
    return stats,positive,nonnegative

def detect_drop_indices_from_array(rf_array, med, scale, quantile=.075, refractory_steps=6):
    q=((rf_array-med)/scale).mean(axis=1)
    dq=np.full(len(q),np.nan,dtype=float)
    dq[3:]=q[3:]-q[:-3]
    threshold=float(np.nanquantile(dq,quantile))
    cand=np.flatnonzero(dq<=threshold)
    events=[]
    last=-10**9
    for i in cand:
        if i-last>=refractory_steps:
            events.append(int(i)); last=int(i)
    return np.asarray(events,dtype=int),threshold

def directional_test_indices(driver_idx,rf_idx,horizon_steps):
    rf_idx=np.asarray(rf_idx,dtype=int)
    post_only=pre_only=both=neither=0
    for e in np.asarray(driver_idx,dtype=int):
        l=np.searchsorted(rf_idx,e-horizon_steps,side="left")
        m=np.searchsorted(rf_idx,e,side="left")
        r=np.searchsorted(rf_idx,e+horizon_steps,side="right")
        pre=m>l
        post=r>np.searchsorted(rf_idx,e,side="right")
        if post and not pre: post_only+=1
        elif pre and not post: pre_only+=1
        elif pre and post: both+=1
        else: neither+=1
    discordant=post_only+pre_only
    p=binomtest(post_only,discordant,.5,alternative="greater").pvalue if discordant else 1.0
    return {
        "n_driver_events":len(driver_idx),"post_only":post_only,
        "pre_only":pre_only,"both":both,"neither":neither,
        "discordant":discordant,"p_value":float(p),
        "post_minus_pre":post_only-pre_only,
    }

def inject_array(base_array,event_idx,lag_steps,effect_sd,scale,duration_steps=3,
                 activation_prob=.70,seed=0):
    rng=np.random.default_rng(seed)
    arr=np.array(base_array,copy=True)
    activated=[]
    for e in np.asarray(event_idx,dtype=int):
        if rng.random()>activation_prob:
            continue
        s=e+lag_steps
        if s>=len(arr):
            continue
        ee=min(len(arr),s+duration_steps)
        arr[s:ee,:]-=effect_sd*scale
        activated.append(int(e))
    return arr,np.asarray(activated,dtype=int)

def rf_drop_threshold_from_array(rf_array, med, scale, quantile=.075):
    q=((rf_array-med)/scale).mean(axis=1)
    dq=np.full(len(q),np.nan,dtype=float)
    dq[3:]=q[3:]-q[:-3]
    return float(np.nanquantile(dq,quantile))

def detect_drop_indices_fixed_threshold(rf_array, med, scale, threshold,
                                        refractory_steps=6):
    q=((rf_array-med)/scale).mean(axis=1)
    dq=np.full(len(q),np.nan,dtype=float)
    dq[3:]=q[3:]-q[:-3]
    cand=np.flatnonzero(dq<=threshold)
    events=[]
    last=-10**9
    for i in cand:
        if i-last>=refractory_steps:
            events.append(int(i)); last=int(i)
    return np.asarray(events,dtype=int)
