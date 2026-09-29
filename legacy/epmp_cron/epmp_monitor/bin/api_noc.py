#!/usr/bin/env python3
from fastapi import FastAPI
import pandas as pd
import os

app = FastAPI()

BASE="/home/carlos/epmp_monitor"
FILE=f"{BASE}/reportes/dataset_avanzado.csv"

@app.get("/")
def root():
    return {"status": "NOC activo"}

@app.get("/estado")
def estado():
    if not os.path.exists(FILE):
        return {"error": "sin datos"}

    df = pd.read_csv(FILE)
    ult = df.tail(1).iloc[0]

    return {
        "evento": ult["evento"],
        "riesgo": ult["riesgo_nivel"],
        "snr": float(ult["dl_snr_db"]),
        "rate": float(ult["dl_rate"])
    }

@app.get("/estado_full")
def estado_full():
    if not os.path.exists(FILE):
        return {"error": "sin datos"}

    df = pd.read_csv(FILE)
    ult = df.tail(1).iloc[0]

    return {
        "timestamp": ult["ts"],
        "evento": ult["evento"],
        "riesgo": ult["riesgo_nivel"],
        "snr": float(ult["dl_snr_db"]),
        "rssi": float(ult["dl_rssi_dbm"]),
        "rate": float(ult["dl_rate"]),
        "snr_std": float(ult.get("snr_std",0)),
        "tendencia": float(ult.get("snr_diff",0))
    }

@app.get("/historico")
def historico():
    if not os.path.exists(FILE):
        return {"error": "sin datos"}

    df = pd.read_csv(FILE)
    return df.tail(50).to_dict(orient="records")
