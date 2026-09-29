#!/usr/bin/env python3
import os
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestClassifier

BASE="/home/carlos/epmp_monitor"
IN=f"{BASE}/reportes/dataset_avanzado.csv"
OUT=f"{BASE}/reportes/dataset_operador.csv"
DB_URL=os.environ.get("EPMP_DB_URL")
if not DB_URL:
    raise RuntimeError("EPMP_DB_URL no configurado")
if not os.path.exists(IN):
    print("No existe dataset_avanzado.csv")
    exit()

df=pd.read_csv(IN)
df["ts"]=pd.to_datetime(df["ts"], errors="coerce")
df=df.dropna(subset=["ts"])

cols=["dl_snr_db","dl_rssi_dbm","dl_rate","snr_diff","rssi_diff","rate_diff","snr_avg","rate_avg","snr_std","riesgo"]
for c in cols:
    if c in df.columns:
        df[c]=pd.to_numeric(df[c], errors="coerce")

df=df.sort_values("ts")
df["target_caida"]=((df["dl_snr_db"] < 15) | (df["dl_rate"] < 25) | (df["riesgo_nivel"] == "ALTO")).astype(int)

features=["dl_snr_db","dl_rssi_dbm","dl_rate","snr_diff","rssi_diff","rate_diff","snr_avg","rate_avg","snr_std","riesgo"]
work=df.dropna(subset=features+["target_caida"]).copy()

if len(work) < 20 or work["target_caida"].nunique() < 2:
    print("Pocos datos o falta variedad. Uso scoring heurístico.")
    df["prob_caida"]=0.0
    df.loc[df["dl_snr_db"] < 18, "prob_caida"] += 0.25
    df.loc[df["dl_snr_db"] < 15, "prob_caida"] += 0.35
    df.loc[df["dl_rate"] < 40, "prob_caida"] += 0.20
    df.loc[df["dl_rate"] < 25, "prob_caida"] += 0.25
    df.loc[df["snr_std"] > 3, "prob_caida"] += 0.20
    df["prob_caida"]=df["prob_caida"].clip(0,1)
else:
    X=work[features]
    y=work["target_caida"]
    model=RandomForestClassifier(n_estimators=150, random_state=42, class_weight="balanced")
    model.fit(X,y)
    valid=df.dropna(subset=features).copy()
    df["prob_caida"]=0.0
    df.loc[valid.index,"prob_caida"]=model.predict_proba(valid[features])[:,1]

df["estado_operador"]=pd.cut(
    df["prob_caida"],
    bins=[-0.01,0.35,0.65,1.01],
    labels=["ESTABLE","RIESGO","CRITICO"]
)

df.to_csv(OUT,index=False)

engine=create_engine(DB_URL)
df.to_sql("metricas_operador", engine, if_exists="replace", index=False)

print("IA OPERADOR OK:", OUT)
print(df[["ts","dl_snr_db","dl_rate","prob_caida","estado_operador"]].tail(10))
