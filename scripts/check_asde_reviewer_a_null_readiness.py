#!/usr/bin/env python3
"""Historical pinned metadata-only readiness helper.

This helper belongs to the 270080c readiness line and is NOT part of v24
prospective calibration. It is intentionally pinned to source SHA-256
389792038327c9b6a65ddceaa32452d6bf272abdddfb8202dc36f96687290bf3.

The pinned snapshot is not the current live export. Do not update EXPECTED to
make this script pass on newer data. A new metadata snapshot requires a new
experiment/readiness record.
"""
from pathlib import Path
import hashlib,json,math
import pandas as pd
ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
SOURCE=ROOT/"Data/exports/scientific_campaign_6g_integrated.csv"
PROTOCOL=ROOT/"docs/ASDE_REVIEWER_A_PHYSICAL_NULL_PROTOCOL.md"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/reviewer_a_physical_null_readiness.json"
EXPECTED="389792038327c9b6a65ddceaa32452d6bf272abdddfb8202dc36f96687290bf3"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):h.update(block)
 return h.hexdigest()
if sha(SOURCE)!=EXPECTED:raise RuntimeError("Export hash changed; freeze a new metadata snapshot")
cols=["rf_timestamp_utc","operating_frequency_mhz","channel_bandwidth_mhz",
      "field_analysis_valid","collection_status","ap_tx_power_dbm","sm_tx_power_dbm"]
df=pd.read_csv(SOURCE,usecols=cols)
df["t"]=pd.to_datetime(df.rf_timestamp_utc,utc=True,errors="coerce")
df=df.loc[~((df.operating_frequency_mhz==7000)&(df.channel_bandwidth_mhz==20))]
df=df.loc[df.operating_frequency_mhz.notna()&df.channel_bandwidth_mhz.notna()&df.t.notna()]
episodes=[]
for (frequency,width),g in df.groupby(["operating_frequency_mhz","channel_bandwidth_mhz"]):
 g=g.sort_values("t").copy()
 good=(g.field_analysis_valid.eq(1)&g.collection_status.eq("LINK_OPERATIONAL_DUAL")&
       g.ap_tx_power_dbm.eq(10)&g.sm_tx_power_dbm.eq(3))
 regime=g[["collection_status","ap_tx_power_dbm","sm_tx_power_dbm","field_analysis_valid"]].fillna("MISSING").astype(str)
 change=regime.ne(regime.shift()).any(axis=1)
 boundary=g.t.diff().gt(pd.Timedelta("15min"))|change|~good
 g["segment"]=boundary.cumsum()
 for _,s in g.loc[good].groupby("segment"):
  start,end=s.t.iloc[0],s.t.iloc[-1]
  bins=s.t.dt.floor("5min").nunique()
  expected=int((end.floor("5min")-start.floor("5min"))/pd.Timedelta("5min"))+1
  duration=(end-start).total_seconds()/3600
  geometry=max(0,math.floor((duration*60-240)/360)+1)
  coverage=bins/expected
  episodes.append({"frequency_mhz":int(frequency),"width_mhz":int(width),
    "start_utc":start.isoformat(),"end_utc":end.isoformat(),
    "rows":len(s),"duration_hours":duration,"observed_5min_bins":bins,
    "expected_5min_bins":expected,"cadence_coverage":coverage,
    "max_360min_anchors_with_2h_margins":geometry,
    "complete_72h_blocks":int(duration//72),
    "passes_metadata_gate":bool(duration>=288 and geometry>=23 and coverage>=.95),
    "previously_used_in_reviewer_b":bool(frequency==6475 and width==20)})
best={}
for e in episodes:
 key=f"{e['frequency_mhz']}/{e['width_mhz']}"
 if key not in best or e["duration_hours"]>best[key]["duration_hours"]:
  best[key]=e
result={"status":"NOT_READY" if not any(e["passes_metadata_gate"] for e in episodes)
        else "METADATA_READY_ONLY",
 "scope":"operating metadata only; 7000/20 development and validation omitted from analysis",
 "source_sha256":EXPECTED,"protocol_sha256":sha(PROTOCOL),
 "script_sha256":sha(Path(__file__)),"assessed_rows":len(df),
 "read_scope_note":"The shared source file bytes were read; no 7000/20 RF/weather outcome columns were selected.",
 "necessary_gate":{"stable_72h_blocks":4,"min_scheduled_coverage":.95,
  "min_refractory_anchor_geometry":23,
  "claim":"necessary metadata conditions, not sufficient null adjudication or statistical PASS"},
 "best_stable_segment_by_configuration":best,
 "segments":episodes}
OUT.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({"status":result["status"],"source_sha256":EXPECTED,"best":best},indent=2))
