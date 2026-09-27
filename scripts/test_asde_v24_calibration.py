#!/usr/bin/env python3
from pathlib import Path
from datetime import date,timedelta
import sys
import numpy as np
import pandas as pd

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0,str(ROOT))
from scientific_discovery.v24_calibration import (
    RF_FEATURES,DRIVER_SPECS,CELL_ORDER,TZ,
    frozen_weather_events,frozen_rf_events,rf_observable_mask,
    joint_unit_profiles,accepted_profile_shams,event_times_to_indices,
    paired_directional_cell,cellwise_empirical_p,
    build_a2_minp_distribution,familywise_empirical_p,
    selected_cells,OPERATING_ALPHA,CALIBRATION_CEILING,
    clopper_pearson_upper,conditional_n1_pass,
    local_day_eligibility,
)

SOURCE=ROOT/"Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"

# Integration check on D_development only.
df=pd.read_csv(SOURCE)
df["t"]=pd.to_datetime(df.rf_timestamp_utc,utc=True)
weather_cols=[str(v["column"]) for v in DRIVER_SPECS.values()]
X=df.set_index("t")[weather_cols+list(RF_FEATURES)].resample("5min").median()

ev=frozen_weather_events(X[weather_cols])
expected={
 "cu01_local_temp_avg_c__rise":23,
 "sj01_local_temp_avg_c__fall":28,
 "sj01_local_hum_avg_pct__fall":28,
 "sj01_local_press_hpa__rise":28,
}
got={k:len(v) for k,v in ev.items()}
assert got==expected,(got,expected)

rf=X[list(RF_FEATURES)].to_numpy(float)
rf_events=frozen_rf_events(rf)
assert len(rf_events)==158,len(rf_events)
obs=rf_observable_mask(rf)
assert int(obs.sum())==2753,int(obs.sum())

# Toy joint-profile generator: exact time-of-day/count preservation and refractory.
days=[date(2026,1,1)+timedelta(days=i) for i in range(10)]
toy={}
for di,driver in enumerate(DRIVER_SPECS):
    times=[]
    for d in days:
        # One event/day/driver, distinct local clock across drivers.
        minute=60*(2+di*4)
        t=(pd.Timestamp(d)+pd.Timedelta(minutes=minute)).tz_localize(TZ)
        times.append(t)
    toy[driver]=pd.DatetimeIndex(times)

starts,profiles=joint_unit_profiles(toy,days,unit_days=1)
assert len(starts)==10 and len(profiles)==10
shams,proposals=accepted_profile_shams(
    toy,days,seed=12345,required=20,proposal_cap=10000,unit_days=1
)
assert len(shams)==20 and proposals<=10000
for schedule,perm in shams:
    assert np.all(perm!=np.arange(len(days)))
    for driver in DRIVER_SPECS:
        original=toy[driver].tz_convert(TZ)
        moved=schedule[driver].tz_convert(TZ)
        assert len(moved)==len(original)
        assert sorted((x.hour,x.minute) for x in moved)==sorted((x.hour,x.minute) for x in original)
        if len(moved)>1:
            gaps=np.diff(moved.sort_values().asi8)/1e9/60
            assert np.all(gaps>=360)

# Same generator must operate on 48-h profiles.
shams48,props48=accepted_profile_shams(
    toy,days,seed=12346,required=5,proposal_cap=10000,unit_days=2
)
assert len(shams48)==5 and props48<=10000

# Paired directional support: eight post-only events on eight days must be eligible.
n=10*288
observable=np.ones(n,dtype=bool)
rf_idx=[]
event_idx=[]
local_dates=[]
start=date(2026,1,1)
for i in range(n):
    local_dates.append(start+timedelta(days=i//288))
for d in range(8):
    e=d*288+100
    event_idx.append(e)
    rf_idx.append(e+1)
cell=paired_directional_cell(
    event_idx,6,rf_idx,observable,local_dates,0,n-1
)
assert cell.post_only==8 and cell.pre_only==0
assert cell.discordant==8 and cell.discordant_days==8
assert cell.eligible
assert abs(cell.score-np.sqrt(8))<1e-12

# Empirical calibration: family remains 12 cells; ineligible target gets p=1.
rng=np.random.default_rng(7)
a1=rng.normal(size=(50,len(CELL_ORDER)))
a1e=np.ones_like(a1,dtype=bool)
a1e[:10,0]=False
target=rng.normal(size=len(CELL_ORDER))
te=np.ones(len(CELL_ORDER),dtype=bool);te[3]=False
praw=cellwise_empirical_p(a1,a1e,target,te)
assert len(praw)==12 and praw[3]==1.0

# A cell with no eligible A1 reference must be nonselectable, not spuriously extreme.
a1_none=np.array(a1,copy=True)
a1e_none=np.array(a1e,copy=True)
a1e_none[:,0]=False
target_only=np.zeros(len(CELL_ORDER),dtype=float)
target_only_e=np.zeros(len(CELL_ORDER),dtype=bool)
target_only_e[0]=True
p_none=cellwise_empirical_p(a1_none,a1e_none,target_only,target_only_e)
assert p_none[0]==1.0

# Positive per-cell rescaling must not change rank-based empirical p-values.
scale_vec=np.linspace(0.5,2.0,len(CELL_ORDER))
p_scaled=cellwise_empirical_p(
    a1*scale_vec,a1e,target*scale_vec,te
)
assert np.allclose(praw,p_scaled)

a2=rng.normal(size=(40,len(CELL_ORDER)))
a2e=np.ones_like(a2,dtype=bool)
a2e[:,5]=False
u=build_a2_minp_distribution(a1,a1e,a2,a2e)
assert len(u)==40 and np.all((u>0)&(u<=1))
pf=familywise_empirical_p(a1,a1e,u,target,te)
assert len(pf)==12 and pf[3]==1.0

# Frozen operating alpha is 0.04, distinct from the 0.05 calibration ceiling.
assert OPERATING_ALPHA==0.04
assert CALIBRATION_CEILING==0.05
probe=np.ones(len(CELL_ORDER),dtype=float)
probe[0]=0.045
probe[1]=0.035
elig=np.ones(len(CELL_ORDER),dtype=bool)
picked=selected_cells(probe,elig)
assert CELL_ORDER[0] not in picked
assert CELL_ORDER[1] in picked

# Frozen conditional calibration boundary.
assert conditional_n1_pass(224,5000)
assert not conditional_n1_pass(225,5000)
assert clopper_pearson_upper(224,5000)<0.05
assert clopper_pearson_upper(225,5000)>0.05

# Frozen local-day eligibility: 274/288 passes; 273 fails; any hard exclusion fails.
idx=pd.date_range(
    "2026-01-01 00:00",periods=3*288,freq="5min",tz=TZ
)
op=np.ones(len(idx),dtype=bool)
wq=np.ones(len(idx),dtype=bool)
hx=np.zeros(len(idx),dtype=bool)

# Day 1: exactly 274 operational and weather-QC bins -> eligible.
op[0:14]=False
wq[14:28]=False

# Day 2: only 273 operational bins -> ineligible.
d2=288
op[d2:d2+15]=False

# Day 3: perfect coverage but one hard exclusion -> ineligible.
d3=2*288
hx[d3+100]=True

daycheck=local_day_eligibility(idx,op,wq,hx)
assert daycheck["eligible"].tolist()==[True,False,False]
assert daycheck.loc[0,"operational_good_bins"]==274
assert daycheck.loc[1,"operational_good_bins"]==273
assert daycheck.loc[2,"hard_exclusion_bins"]==1
assert daycheck["grid_exact"].tolist()==[True,True,True]

# A duplicated 5-min timestamp plus one missing bin must fail exact-grid integrity.
bad_idx=idx[:288].tolist()
bad_idx[-1]=bad_idx[-2]
bad_idx=pd.DatetimeIndex(bad_idx)
bad=np.ones(288,dtype=bool)
badcheck=local_day_eligibility(bad_idx,bad,bad,np.zeros(288,dtype=bool))
assert badcheck.loc[0,"grid_bins"]==288
assert not bool(badcheck.loc[0,"grid_exact"])
assert not bool(badcheck.loc[0,"eligible"])

print("ASDE_V24_CALIBRATION_TEST_PASS")
print("weather_event_counts",got)
print("rf_event_count",len(rf_events))
print("rf_observable_bins",int(obs.sum()))
print("toy_24h_proposals",proposals)
print("toy_48h_proposals",props48)
print("cp_upper_224",clopper_pearson_upper(224,5000))
print("cp_upper_225",clopper_pearson_upper(225,5000))
print("day_eligibility",daycheck["eligible"].tolist())
