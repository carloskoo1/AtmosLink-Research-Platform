#!/usr/bin/env python3
import pandas as pd
import glob, os

BASE="/home/carlos/epmp_monitor"
DATA=f"{BASE}/data"
OUT=f"{BASE}/reportes"
os.makedirs(OUT, exist_ok=True)

files=sorted(glob.glob(f"{DATA}/agg_ap_*.csv"))

if not files:
    print("No hay CSV")
    exit()

df=pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

# Convertir tiempo
df["ts"]=pd.to_datetime(df["ts"], errors="coerce")

# Convertir métricas
cols=["dl_mcs","ul_mcs","dl_snr_db","ul_snr_db","dl_rssi_dbm","ul_rssi_dbm","dl_rate"]
for c in cols:
    if c in df.columns:
        df[c]=pd.to_numeric(df[c], errors="coerce")

# Eliminar filas sin timestamp válido
df=df.dropna(subset=["ts"])

if df.empty:
    print("No hay datos válidos todavía (normal si estás en casa)")
    exit()

# ===== MODELO =====
def score(row):
    s=100

    if pd.notna(row["dl_snr_db"]) and row["dl_snr_db"] < 15:
        s-=30

    if pd.notna(row["dl_rssi_dbm"]) and row["dl_rssi_dbm"] < -75:
        s-=25

    if pd.notna(row["dl_mcs"]) and row["dl_mcs"] < 3:
        s-=25

    if pd.notna(row["dl_rate"]) and row["dl_rate"] < 20:
        s-=20

    return max(0, min(100, s))

df["IDOE_operativo"]=df.apply(score, axis=1)

def estado(v):
    if v >= 80: return "OPTIMO"
    if v >= 60: return "ACEPTABLE"
    if v >= 40: return "DEGRADADO"
    return "CRITICO"

df["estado_enlace"]=df["IDOE_operativo"].apply(estado)

# Guardar resultado
out_file=f"{OUT}/dataset_modelo_epmp.csv"
df.to_csv(out_file, index=False)

print("Modelo OK:", out_file)
print(df.tail(5))
