#!/usr/bin/env python3
import pandas as pd
import os
from sklearn.ensemble import RandomForestClassifier

BASE="/home/carlos/epmp_monitor"
FILE=f"{BASE}/reportes/dataset_avanzado.csv"
OUT=f"{BASE}/reportes/modelo_rf.pkl"

if not os.path.exists(FILE):
    print("No dataset")
    exit()

df=pd.read_csv(FILE)

# ===== LIMPIEZA =====
df=df.dropna()

# ===== TARGET =====
# 1 = riesgo alto, 0 = normal
df["target"] = df["riesgo_nivel"].apply(lambda x: 1 if x=="ALTO" else 0)

# ===== FEATURES =====
X = df[[
    "dl_snr_db",
    "dl_rssi_dbm",
    "dl_rate",
    "snr_diff",
    "snr_std"
]]

y = df["target"]

# ===== MODELO =====
model = RandomForestClassifier(n_estimators=50)
model.fit(X,y)

# ===== PREDICCIÓN =====
pred = model.predict(X.tail(1))[0]

print("\n===== IA PREDICTIVA =====")
print("Predicción próxima:", "CAIDA" if pred==1 else "ESTABLE")
