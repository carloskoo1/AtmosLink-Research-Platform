#!/usr/bin/env python3
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta, timezone

BASE="/home/carlos/epmp_monitor"
DATA=f"{BASE}/data"
os.makedirs(DATA, exist_ok=True)

today=datetime.now().strftime("%Y-%m-%d")
out=f"{DATA}/agg_ap_{today}.csv"

rows=[]
now=datetime.now().replace(second=0, microsecond=0)

for i in range(240):
    ts=now - timedelta(minutes=240-i)

    # Escenarios: normal, degradación leve, caída fuerte, recuperación
    if i < 90:
        snr=np.random.normal(24, 2)
        rssi=np.random.normal(-62, 3)
        mcs=np.random.choice([6,7,8,9], p=[0.15,0.35,0.35,0.15])
        rate=np.random.normal(85, 10)
        note="ok"
    elif i < 140:
        snr=np.random.normal(18, 2)
        rssi=np.random.normal(-71, 3)
        mcs=np.random.choice([4,5,6], p=[0.25,0.45,0.30])
        rate=np.random.normal(45, 8)
        note="DEGRADACION_LEVE"
    elif i < 180:
        snr=np.random.normal(12, 2)
        rssi=np.random.normal(-79, 3)
        mcs=np.random.choice([1,2,3], p=[0.35,0.45,0.20])
        rate=np.random.normal(15, 5)
        note="CRITICO_SIMULADO"
    else:
        snr=np.random.normal(23, 2)
        rssi=np.random.normal(-64, 3)
        mcs=np.random.choice([6,7,8], p=[0.25,0.45,0.30])
        rate=np.random.normal(78, 9)
        note="RECUPERADO"

    rows.append({
        "ts": ts.isoformat(),
        "role": "AP",
        "ip": "192.168.1.2",
        "peer_ip": "192.168.1.3",
        "dl_mcs": int(max(1, min(9, round(mcs)))),
        "ul_mcs": int(max(1, min(9, round(mcs-1 if mcs>1 else mcs)))),
        "dl_snr_db": round(float(snr),2),
        "ul_snr_db": round(float(snr-1.5),2),
        "dl_rssi_dbm": round(float(rssi),2),
        "ul_rssi_dbm": round(float(rssi-2),2),
        "dl_rate": round(float(max(1, rate)),2),
        "note": note
    })

df=pd.DataFrame(rows)
df.to_csv(out, index=False)
print("CSV simulado generado:", out)
print(df.tail(10))
