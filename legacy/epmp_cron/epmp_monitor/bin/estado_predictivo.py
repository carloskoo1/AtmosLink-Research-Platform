#!/usr/bin/env python3
import pandas as pd
import os

BASE="/home/carlos/epmp_monitor"
IN=f"{BASE}/reportes/dataset_avanzado.csv"
OUT=f"{BASE}/reportes/dataset_predictivo.csv"

if not os.path.exists(IN):
    print("No existe dataset_avanzado.csv")
    exit()

df=pd.read_csv(IN)
df["ts"]=pd.to_datetime(df["ts"], errors="coerce")
df=df.dropna(subset=["ts"])

for c in ["dl_snr_db","dl_rssi_dbm","dl_rate","snr_diff","rate_diff","snr_std"]:
    if c in df.columns:
        df[c]=pd.to_numeric(df[c], errors="coerce")

df=df.sort_values("ts")
df["snr_trend_5"]=df["dl_snr_db"].diff(5)
df["rate_trend_5"]=df["dl_rate"].diff(5)
df["snr_avg_5"]=df["dl_snr_db"].rolling(5).mean()
df["rate_avg_5"]=df["dl_rate"].rolling(5).mean()
df["snr_std_10"]=df["dl_snr_db"].rolling(10).std()

def predecir(row):
    score=0

    if pd.notna(row["dl_snr_db"]) and row["dl_snr_db"] < 15:
        score += 3
    elif pd.notna(row["dl_snr_db"]) and row["dl_snr_db"] < 18:
        score += 2

    if pd.notna(row["snr_trend_5"]) and row["snr_trend_5"] < -4:
        score += 3
    elif pd.notna(row["snr_trend_5"]) and row["snr_trend_5"] < -2:
        score += 2

    if pd.notna(row["rate_trend_5"]) and row["rate_trend_5"] < -25:
        score += 3
    elif pd.notna(row["rate_trend_5"]) and row["rate_trend_5"] < -10:
        score += 1

    if pd.notna(row["snr_std_10"]) and row["snr_std_10"] > 4:
        score += 2

    if pd.notna(row["dl_rate"]) and row["dl_rate"] < 20:
        score += 3
    elif pd.notna(row["dl_rate"]) and row["dl_rate"] < 40:
        score += 1

    if score >= 6:
        return "POSIBLE_CAIDA"
    if score >= 3:
        return "RIESGO_PROXIMO"
    return "ESTABLE"

df["estado_predictivo"]=df.apply(predecir, axis=1)

def val(v):
    if v=="ESTABLE":
        return 3
    if v=="RIESGO_PROXIMO":
        return 2
    if v=="POSIBLE_CAIDA":
        return 1
    return 0

df["estado_predictivo_valor"]=df["estado_predictivo"].apply(val)

df.to_csv(OUT,index=False)
print("ESTADO PREDICTIVO OK:", OUT)
print(df[["ts","dl_snr_db","dl_rate","estado_predictivo"]].tail(10))
