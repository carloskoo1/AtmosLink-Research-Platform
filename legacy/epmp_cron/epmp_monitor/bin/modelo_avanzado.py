#!/usr/bin/env python3
import pandas as pd
import numpy as np
import os

BASE="/home/carlos/epmp_monitor"
DATA=f"{BASE}/data"
OUT=f"{BASE}/reportes"
os.makedirs(OUT, exist_ok=True)

files=sorted([f for f in os.listdir(DATA) if f.endswith(".csv")])
if not files:
    print("No hay archivos CSV")
    exit()

df_list=[]
for f in files:
    try:
        temp=pd.read_csv(f"{DATA}/{f}", on_bad_lines="skip")
        df_list.append(temp)
        print(f"✔ Cargado: {f}")
    except Exception as e:
        print(f"✖ Error leyendo {f}: {e}")

if not df_list:
    print("No se pudo cargar CSV válido")
    exit()

df=pd.concat(df_list, ignore_index=True)

expected=[
    "ts","role","ip","peer_ip","dl_mcs","ul_mcs",
    "dl_snr_db","ul_snr_db","dl_rssi_dbm","ul_rssi_dbm",
    "dl_rate","note"
]
df=df[[c for c in expected if c in df.columns]]

df["ts"]=pd.to_datetime(df["ts"], errors="coerce")
for c in ["dl_mcs","ul_mcs","dl_snr_db","ul_snr_db","dl_rssi_dbm","ul_rssi_dbm","dl_rate"]:
    if c in df.columns:
        df[c]=pd.to_numeric(df[c], errors="coerce")

df=df.dropna(subset=["ts"])
df=df.dropna(subset=["dl_snr_db","dl_rssi_dbm","dl_rate"])

if df.empty:
    print("No hay datos válidos todavía")
    exit()

df=df.sort_values("ts")

df["snr_diff"]=df["dl_snr_db"].diff()
df["rssi_diff"]=df["dl_rssi_dbm"].diff()
df["rate_diff"]=df["dl_rate"].diff()
df["snr_avg"]=df["dl_snr_db"].rolling(5).mean()
df["rate_avg"]=df["dl_rate"].rolling(5).mean()
df["snr_std"]=df["dl_snr_db"].rolling(10).std()

def detectar_evento(row):
    if row["dl_snr_db"] < 12:
        return "CRITICO_SNR"
    if row["dl_rssi_dbm"] < -80:
        return "CRITICO_RSSI"
    if row["dl_rate"] < 10:
        return "CAIDA_RATE"
    if pd.notna(row["snr_diff"]) and abs(row["snr_diff"]) > 5:
        return "INTERFERENCIA"
    if pd.notna(row["snr_std"]) and row["snr_std"] > 4:
        return "INESTABLE"
    return "NORMAL"

df["evento"]=df.apply(detectar_evento, axis=1)

df["riesgo"]=0
df.loc[df["snr_avg"] < 15, "riesgo"] += 2
df.loc[df["rate_avg"] < 20, "riesgo"] += 2
df.loc[df["snr_std"] > 3, "riesgo"] += 1

def nivel(v):
    if v >= 4:
        return "ALTO"
    if v >= 2:
        return "MEDIO"
    return "BAJO"

df["riesgo_nivel"]=df["riesgo"].apply(nivel)

out=f"{OUT}/dataset_avanzado.csv"
df.to_csv(out,index=False)
print("MODELO AVANZADO OK:", out)
print(df[["ts","dl_snr_db","dl_rate","evento","riesgo_nivel"]].tail(10))
