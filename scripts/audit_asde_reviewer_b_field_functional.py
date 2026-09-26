#!/usr/bin/env python3
"""Frozen post-audit, same-link cross-configuration goodput corroboration."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path("/home/carlos/Proyectos/EstacionMeteorologica")
SRC = ROOT / "Data/exports/active_throughput_6g.csv"
DEV = ROOT / "Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
PROTOCOL = ROOT / "docs/ASDE_REVIEWER_B_FIELD_FUNCTIONAL_PROTOCOL.md"
OUT = ROOT / "Results/scientific_discovery/DISCOVERY-001/reviewer_b_field_functional.json"
EXPECTED = "bcd2e0391ff86b3e3cf0e9a428b1de8355b354f60c32d56735f5085f48b85722"
EXPECTED_DEV = "eed7df2621f6952b9ea2eaa7524f735a706b69494d3d272fd2dd828b52a97387"
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):
            h.update(block)
    return h.hexdigest()
if sha(SRC)!=EXPECTED or sha(DEV)!=EXPECTED_DEV:
    raise RuntimeError("Frozen source digest changed")
cols=["direction","timestamp_start_utc","status","protocol","route_verified",
      "duration_seconds","parallel_streams","measured_throughput_mbps",
      "rf_time_delta_seconds","operating_frequency_mhz","channel_bandwidth_mhz",
      "ap_tx_power_dbm","sm_tx_power_dbm","dl_rssi_dbm","dl_snr_db",
      "ul_rssi_dbm","ul_snr_db"]
a=pd.read_csv(SRC,usecols=cols)
a["t"]=pd.to_datetime(a.timestamp_start_utc,utc=True,errors="coerce")
start=pd.Timestamp("2026-09-01T18:30:52Z")
end=pd.Timestamp("2026-09-13T03:29:49Z")
episodes={"later_6475_20":a[(a.operating_frequency_mhz==6475)&
                           (a.channel_bandwidth_mhz==20)],
          "development_7000_20":a[(a.operating_frequency_mhz==7000)&
                                   (a.channel_bandwidth_mhz==20)&
                                   a.t.between(start,end)]}

def scale(s):
    med=s.median()
    mad=(s-med).abs().median()
    iqr=(s.quantile(.75)-s.quantile(.25))/1.349
    sd=s.std(ddof=0)
    return med, next((v for v in [1.4826*mad,iqr,sd,1.] if pd.notna(v) and v>0))
def summarize(g):
    q1,q3=g.q.quantile([.25,.75])
    low=g[g.q<=q1].measured_throughput_mbps
    high=g[g.q>=q3].measured_throughput_mbps
    lo,hi=float(low.median()),float(high.median())
    rho=g[["q","measured_throughput_mbps"]].corr(method="spearman").iloc[0,1]
    return {"n":len(g),"rho_spearman":float(rho) if pd.notna(rho) else None,
            "score_q1":float(q1),"score_q3":float(q3),
            "bottom_n":len(low),"top_n":len(high),
            "bottom_median_mbps":lo,"top_median_mbps":hi,
            "top_minus_bottom_mbps":hi-lo,"bottom_top_ratio":lo/hi if hi else None}
result={"classification":"post-audit descriptive, same physical link; no p-values",
        "source_sha256":EXPECTED,"development_source_sha256":EXPECTED_DEV,
        "protocol_sha256":sha(PROTOCOL),"code_sha256":sha(Path(__file__)),
        "episodes":{}}
for name,frame in episodes.items():
    record={"raw_rows":len(frame),"start_utc":str(frame.t.min()),
            "end_utc":str(frame.t.max()),"directions":{}}
    for direction in ["DL","UL"]:
        g=frame[frame.direction==direction].copy()
        d={"raw_rows":len(g),"exclusions_sequential":{}}
        checks=[
          ("status",g.status.eq("OK")),
          ("tcp_route",g.protocol.eq("TCP") & g.route_verified.eq(1)),
          ("test_settings",g.duration_seconds.eq(8)&g.parallel_streams.eq(1)),
          ("tx_powers",g.ap_tx_power_dbm.eq(10)&g.sm_tx_power_dbm.eq(3)),
          ("rf_offset",g.rf_time_delta_seconds.abs().le(300)),
          ("goodput",np.isfinite(g.measured_throughput_mbps)&g.measured_throughput_mbps.gt(0)),
          ("analog",np.isfinite(g[f"{direction.lower()}_rssi_dbm"])&
                    np.isfinite(g[f"{direction.lower()}_snr_db"]))]
        for label,valid in checks:
            n0=len(g); g=g.loc[valid.loc[g.index]]; d["exclusions_sequential"][label]=n0-len(g)
        x,y=f"{direction.lower()}_rssi_dbm",f"{direction.lower()}_snr_db"
        refs={v:scale(g[v]) for v in [x,y]}
        g["q"]=sum((g[v]-refs[v][0])/refs[v][1] for v in [x,y])/2
        d["reference"]={v:{"median":float(m),"scale":float(s)} for v,(m,s) in refs.items()}
        d["summary"]=summarize(g)
        d["by_utc_day"]={}
        for date,day in g.groupby(g.t.dt.strftime("%Y-%m-%d")):
            if len(day)>=20:
                d["by_utc_day"][date]=summarize(day)
        record["directions"][direction]=d
    result["episodes"][name]=record
result["directional_consistency"]={
    direction:all(result["episodes"][name]["directions"][direction]["summary"]["rho_spearman"]>0
              and result["episodes"][name]["directions"][direction]["summary"]["top_minus_bottom_mbps"]>0
              for name in episodes)
    for direction in ["DL","UL"]}
result["all_four_consistent"]=all(result["directional_consistency"].values())
OUT.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
print(json.dumps(result,indent=2,allow_nan=False))
