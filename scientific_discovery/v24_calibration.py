"""Prospective v24 calibration primitives.

Pure functions only: no project-file I/O and no access to D_validation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from math import ceil, sqrt
from typing import Dict, Iterable, Iterator, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.stats import beta

TZ = "America/Lima"

RF_FEATURES = (
    "dl_rssi_dbm","ul_rssi_dbm","dl_snr_db",
    "ul_snr_db","dl_mcs","ul_mcs",
)
RF_MEDIAN = np.array([-74.0,-80.0,23.0,18.0,204.0,202.0],dtype=float)
RF_SCALE = np.array([
    0.7412898443291327,
    0.7412898443291327,
    0.7412898443291327,
    1.4826,
    5.896045450988336,
    1.4826,
],dtype=float)
RF_DROP_THRESHOLD = -0.5620817932460992
RF_REFRACTORY_STEPS = 6
OPERATING_ALPHA = 0.04
CALIBRATION_CEILING = 0.05

DRIVER_SPECS = {
    "cu01_local_temp_avg_c__rise": {
        "column":"cu01_local_temp_avg_c","way":"rise",
        "diff15_median":-0.07000000000000028,
        "diff15_scale":0.34099799999999536,
        "z_threshold":1.5308007671599377,
    },
    "sj01_local_temp_avg_c__fall": {
        "column":"sj01_local_temp_avg_c","way":"fall",
        "diff15_median":-0.020000000000000462,
        "diff15_scale":0.3261719999999983,
        "z_threshold":1.2876641771825945,
    },
    "sj01_local_hum_avg_pct__fall": {
        "column":"sj01_local_hum_avg_pct","way":"fall",
        "diff15_median":0.0,
        "diff15_scale":1.5715560000000033,
        "z_threshold":1.6365945597866016,
    },
    "sj01_local_press_hpa__rise": {
        "column":"sj01_local_press_hpa","way":"rise",
        "diff15_median":0.009999999999990905,
        "diff15_scale":0.13343399999987862,
        "z_threshold":0.8993210126363124,
    },
}
HORIZONS_MIN = (30,60,120)
CELL_ORDER = tuple((driver,h) for driver in DRIVER_SPECS for h in HORIZONS_MIN)


@dataclass(frozen=True)
class DirectionalCell:
    post_only: int
    pre_only: int
    discordant: int
    discordant_days: int
    score: float
    eligible: bool
    retained_events: int


def _frozen_driver_score(series: pd.Series, spec: Mapping[str,float|str]) -> pd.Series:
    diff = series.diff(3)
    z = (diff - float(spec["diff15_median"])) / float(spec["diff15_scale"])
    return z if spec["way"] == "rise" else -z


def frozen_weather_events(frame: pd.DataFrame) -> Dict[str,pd.DatetimeIndex]:
    """Detect the frozen four weather-event families without future renormalization."""
    if not isinstance(frame.index,pd.DatetimeIndex):
        raise TypeError("frame index must be DatetimeIndex")
    out={}
    for name,spec in DRIVER_SPECS.items():
        score=_frozen_driver_score(frame[str(spec["column"])],spec)
        threshold=float(spec["z_threshold"])
        events=[];last=None
        for t,v in score.dropna().items():
            if v < threshold:
                continue
            local=score.loc[t-pd.Timedelta("10min"):t+pd.Timedelta("10min")]
            if v < local.max():
                continue
            if last is None or t-last >= pd.Timedelta("360min"):
                events.append(t);last=t
        out[name]=pd.DatetimeIndex(events)
    return out


def frozen_rf_quality(rf_array: np.ndarray) -> np.ndarray:
    arr=np.asarray(rf_array,dtype=float)
    if arr.ndim!=2 or arr.shape[1]!=len(RF_FEATURES):
        raise ValueError("rf_array must be n x 6 in frozen RF feature order")
    return ((arr-RF_MEDIAN)/RF_SCALE).mean(axis=1)


def frozen_rf_events(rf_array: np.ndarray) -> np.ndarray:
    q=frozen_rf_quality(rf_array)
    dq=np.full(len(q),np.nan,dtype=float)
    dq[3:]=q[3:]-q[:-3]
    cand=np.flatnonzero(dq<=RF_DROP_THRESHOLD)
    events=[];last=-10**9
    for i in cand:
        if int(i)-last>=RF_REFRACTORY_STEPS:
            events.append(int(i));last=int(i)
    return np.asarray(events,dtype=int)


def rf_observable_mask(rf_array: np.ndarray) -> np.ndarray:
    arr=np.asarray(rf_array,dtype=float)
    complete=np.isfinite(arr).all(axis=1)
    out=np.zeros(len(arr),dtype=bool)
    out[3:]=complete[3:] & complete[:-3]
    return out


def paired_directional_cell(
    event_idx: Sequence[int],
    horizon_steps: int,
    rf_event_idx: Sequence[int],
    observable: np.ndarray,
    local_dates: Sequence[date],
    fold_lo: int,
    fold_hi: int,
) -> DirectionalCell:
    """Matched-offset pre/post classification restricted to one fold."""
    e=np.asarray(event_idx,dtype=int)
    rfmask=np.zeros(len(observable),dtype=bool)
    rfmask[np.asarray(rf_event_idx,dtype=int)]=True
    if len(e)==0:
        return DirectionalCell(0,0,0,0,0.0,False,0)

    offsets=np.arange(1,horizon_steps+1,dtype=int)
    left=e[:,None]-offsets[None,:]
    right=e[:,None]+offsets[None,:]
    inside=(left>=fold_lo)&(right<=fold_hi)
    left_clip=np.clip(left,0,len(observable)-1)
    right_clip=np.clip(right,0,len(observable)-1)
    both=inside & observable[left_clip] & observable[right_clip]
    required=ceil(horizon_steps/2)
    retain=both.sum(axis=1)>=required
    kept=e[retain]
    if len(kept)==0:
        return DirectionalCell(0,0,0,0,0.0,False,0)

    pre=(both & rfmask[left_clip]).any(axis=1)[retain]
    post=(both & rfmask[right_clip]).any(axis=1)[retain]
    post_only=post & ~pre
    pre_only=pre & ~post
    disc=post_only | pre_only
    p=int(post_only.sum()); r=int(pre_only.sum()); d=p+r
    days={local_dates[int(i)] for i in kept[disc]}
    score=(p-r)/sqrt(max(d,1))
    eligible=(d>=8 and len(days)>=4)
    return DirectionalCell(
        post_only=p,pre_only=r,discordant=d,discordant_days=len(days),
        score=float(score),eligible=bool(eligible),retained_events=len(kept)
    )


def schedule_score_vector(
    events_by_driver: Mapping[str,Sequence[int]],
    rf_event_idx: Sequence[int],
    observable: np.ndarray,
    local_dates: Sequence[date],
    fold_lo: int,
    fold_hi: int,
):
    scores=[];eligible=[];cells=[]
    for driver,hmin in CELL_ORDER:
        cell=paired_directional_cell(
            events_by_driver.get(driver,()),
            hmin//5,rf_event_idx,observable,local_dates,fold_lo,fold_hi,
        )
        scores.append(cell.score)
        eligible.append(cell.eligible)
        cells.append(cell)
    return np.asarray(scores,float),np.asarray(eligible,bool),tuple(cells)


def _midnight_local(d: date) -> pd.Timestamp:
    return pd.Timestamp(d).tz_localize(TZ)


def joint_unit_profiles(
    events_by_driver: Mapping[str,pd.DatetimeIndex],
    fold_days: Sequence[date],
    unit_days: int = 1,
):
    """Build joint 24-h or 48-h event profiles from consecutive local days."""
    days=list(fold_days)
    if unit_days not in (1,2):
        raise ValueError("unit_days must be 1 or 2")
    if len(days)==0 or len(days)%unit_days:
        raise ValueError("fold day count must be nonzero and divisible by unit_days")
    for a,b in zip(days[:-1],days[1:]):
        if b-a != timedelta(days=1):
            raise ValueError("fold_days must be consecutive calendar days")

    local_events={}
    for driver in DRIVER_SPECS:
        idx=pd.DatetimeIndex(events_by_driver.get(driver,pd.DatetimeIndex([])))
        if len(idx) and idx.tz is None:
            raise ValueError("event timestamps must be timezone-aware")
        local_events[driver]=idx.tz_convert(TZ) if len(idx) else idx

    starts=[];profiles=[]
    for i in range(0,len(days),unit_days):
        start=_midnight_local(days[i])
        end=start+pd.Timedelta(days=unit_days)
        profile={driver:[] for driver in DRIVER_SPECS}
        for driver,idx in local_events.items():
            if not len(idx):
                continue
            use=idx[(idx>=start)&(idx<end)]
            profile[driver]=[
                int((t-start)/pd.Timedelta("1min")) for t in use
            ]
        starts.append(start)
        profiles.append(profile)
    return tuple(starts),tuple(profiles)


def propose_joint_profile_derangement(
    starts: Sequence[pd.Timestamp],
    profiles: Sequence[Mapping[str,Sequence[int]]],
    rng: np.random.Generator,
    min_same_driver_gap_min: int = 360,
):
    """Uniform permutation proposal; return None if derangement/refractory fails."""
    n=len(starts)
    if n<2 or len(profiles)!=n:
        raise ValueError("need matching profile/start sequences with at least 2 units")
    perm=rng.permutation(n)
    if np.any(perm==np.arange(n)):
        return None

    moved={driver:[] for driver in DRIVER_SPECS}
    for src,target_idx in enumerate(perm):
        target_start=starts[int(target_idx)]
        for driver in DRIVER_SPECS:
            for minute in profiles[src].get(driver,()):
                moved[driver].append(target_start+pd.Timedelta(minutes=int(minute)))

    for driver,times in moved.items():
        times.sort()
        if len(times)>1:
            ns=pd.DatetimeIndex(times).asi8
            gaps=np.diff(ns)/1e9/60.0
            if np.any(gaps < min_same_driver_gap_min):
                return None
    return {k:pd.DatetimeIndex(v) for k,v in moved.items()},np.asarray(perm,dtype=int)


def accepted_profile_shams(
    events_by_driver: Mapping[str,pd.DatetimeIndex],
    fold_days: Sequence[date],
    seed: int,
    required: int,
    proposal_cap: int = 1_000_000,
    unit_days: int = 1,
):
    """Generate IID accepted schedules by rejection sampling with replacement."""
    starts,profiles=joint_unit_profiles(events_by_driver,fold_days,unit_days)
    rng=np.random.default_rng(seed)
    accepted=[];proposals=0
    while len(accepted)<required and proposals<proposal_cap:
        proposals+=1
        result=propose_joint_profile_derangement(starts,profiles,rng)
        if result is not None:
            accepted.append(result)
    return accepted,proposals


def event_times_to_indices(
    events_by_driver: Mapping[str,pd.DatetimeIndex],
    time_index: pd.DatetimeIndex,
):
    if time_index.tz is None:
        raise ValueError("time_index must be timezone-aware")
    lookup={t:i for i,t in enumerate(time_index)}
    out={}
    for driver in DRIVER_SPECS:
        vals=[]
        for t in pd.DatetimeIndex(events_by_driver.get(driver,pd.DatetimeIndex([]))):
            tt=t.tz_convert(time_index.tz)
            if tt not in lookup:
                raise ValueError(f"event timestamp not found on grid: {tt}")
            vals.append(lookup[tt])
        out[driver]=np.asarray(sorted(vals),dtype=int)
    return out


def _validate_reference_matrices(scores: np.ndarray, eligible: np.ndarray):
    s=np.asarray(scores,dtype=float)
    e=np.asarray(eligible,dtype=bool)
    if s.shape!=e.shape or s.ndim!=2 or s.shape[1]!=len(CELL_ORDER):
        raise ValueError("score/eligibility matrices must be n x 12")
    return s,e


def cellwise_empirical_p(
    a1_scores: np.ndarray,
    a1_eligible: np.ndarray,
    score_vector: Sequence[float],
    eligible_vector: Sequence[bool],
) -> np.ndarray:
    """A1 one-sided empirical tails conditional on cellwise support eligibility.

    A target cell that is support-ineligible receives p=1. If no A1 schedule is
    eligible for that cell, the target also receives p=1 and cannot be selected.
    """
    ref,ref_e=_validate_reference_matrices(a1_scores,a1_eligible)
    s=np.asarray(score_vector,dtype=float)
    e=np.asarray(eligible_vector,dtype=bool)
    if s.shape!=(len(CELL_ORDER),) or e.shape!=s.shape:
        raise ValueError("target score/eligibility vector must have length 12")
    p=np.ones(len(CELL_ORDER),dtype=float)
    for j in range(len(CELL_ORDER)):
        if not e[j]:
            continue
        use=ref_e[:,j]
        m=int(use.sum())
        if m==0:
            continue
        p[j]=(1+int(np.sum(ref[use,j]>=s[j])))/(m+1)
    return p


def build_a2_minp_distribution(
    a1_scores: np.ndarray,
    a1_eligible: np.ndarray,
    a2_scores: np.ndarray,
    a2_eligible: np.ndarray,
) -> np.ndarray:
    a2s=np.asarray(a2_scores,float);a2e=np.asarray(a2_eligible,bool)
    if a2s.shape!=a2e.shape or a2s.ndim!=2 or a2s.shape[1]!=len(CELL_ORDER):
        raise ValueError("A2 matrices must be n x 12")
    out=[]
    for s,e in zip(a2s,a2e):
        p=cellwise_empirical_p(a1_scores,a1_eligible,s,e)
        out.append(float(np.min(p)))
    return np.asarray(out,float)


def familywise_empirical_p(
    a1_scores: np.ndarray,
    a1_eligible: np.ndarray,
    a2_minp: Sequence[float],
    score_vector: Sequence[float],
    eligible_vector: Sequence[bool],
) -> np.ndarray:
    """Family-wise adjusted p for one schedule using frozen A1/A2 references."""
    raw=cellwise_empirical_p(
        a1_scores,a1_eligible,score_vector,eligible_vector
    )
    e=np.asarray(eligible_vector,dtype=bool)
    u=np.asarray(a2_minp,dtype=float)
    out=np.ones(len(CELL_ORDER),dtype=float)
    for j in range(len(CELL_ORDER)):
        if e[j]:
            out[j]=(1+int(np.sum(u<=raw[j])))/(len(u)+1)
    return out


def selected_cells(
    familywise_p: Sequence[float],
    eligible_vector: Sequence[bool],
    alpha: float = OPERATING_ALPHA,
):
    p=np.asarray(familywise_p,float)
    e=np.asarray(eligible_vector,bool)
    return tuple(
        CELL_ORDER[j] for j in range(len(CELL_ORDER))
        if e[j] and p[j]<=alpha
    )


def clopper_pearson_upper(k: int,n: int,confidence: float=0.95) -> float:
    if not (0<=k<=n) or n<=0:
        raise ValueError("require 0 <= k <= n and n > 0")
    if k==n:
        return 1.0
    return float(beta.ppf(confidence,k+1,n-k))


def conditional_n1_pass(
    k: int,n: int=5000,ceiling: float=CALIBRATION_CEILING
) -> bool:
    rate=k/n
    return bool(
        rate<=ceiling
        and clopper_pearson_upper(k,n,0.95)<=ceiling
    )


def local_day_eligibility(
    time_index: pd.DatetimeIndex,
    operational_ok: Sequence[bool],
    weather_qc_ok: Sequence[bool],
    hard_exclusion: Sequence[bool],
    min_good_bins: int = 274,
):
    """Evaluate frozen v24 day eligibility on a complete 5-min local grid.

    RF magnitude/availability must not be encoded in any input mask.
    """
    if time_index.tz is None:
        raise ValueError("time_index must be timezone-aware")
    n=len(time_index)
    op=np.asarray(operational_ok,dtype=bool)
    wq=np.asarray(weather_qc_ok,dtype=bool)
    hx=np.asarray(hard_exclusion,dtype=bool)
    if any(len(x)!=n for x in (op,wq,hx)):
        raise ValueError("eligibility masks must match time_index length")

    local=time_index.tz_convert(TZ)
    dates=np.asarray(local.date,dtype=object)
    rows=[]
    for d in pd.unique(dates):
        m=dates==d
        day_index=local[m]
        bins=int(m.sum())
        expected=pd.date_range(
            _midnight_local(d),periods=288,freq="5min"
        )
        grid_exact=bool(
            bins==288
            and day_index.is_unique
            and np.array_equal(day_index.asi8,expected.asi8)
        )
        op_good=int(op[m].sum())
        weather_good=int(wq[m].sum())
        hard=int(hx[m].sum())
        eligible=(
            grid_exact
            and op_good>=min_good_bins
            and weather_good>=min_good_bins
            and hard==0
        )
        rows.append({
            "local_date":d,
            "grid_bins":bins,
            "grid_exact":grid_exact,
            "operational_good_bins":op_good,
            "weather_qc_good_bins":weather_good,
            "hard_exclusion_bins":hard,
            "eligible":bool(eligible),
        })
    return pd.DataFrame(rows)
