#!/usr/bin/env python3
import pandas as pd
import requests
import os

BASE="/home/carlos/epmp_monitor"
FILE=f"{BASE}/reportes/dataset_avanzado.csv"
LOG=f"{BASE}/logs/alertas.log"

# ===== CONFIGURAR TELEGRAM =====
TOKEN=os.environ.get("EPMP_TELEGRAM_BOT_TOKEN")
CHAT_ID=os.environ.get("EPMP_TELEGRAM_CHAT_ID")

def enviar_telegram(msg):
    if not TOKEN or not CHAT_ID:
        print("Telegram no configurado: faltan variables de entorno")
        return

    try:
        url=f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ===== CARGA =====
if not os.path.exists(FILE):
    print("No hay dataset")
    exit()

df=pd.read_csv(FILE)

if df.empty:
    exit()

ult=df.tail(1).iloc[0]

mensaje = None

# ===== REGLAS =====

if ult["riesgo_nivel"] == "ALTO":
    mensaje = f"🔴 ALERTA CRÍTICA\nSNR: {ult['dl_snr_db']}\nRate: {ult['dl_rate']}"

elif ult["evento"] != "NORMAL":
    mensaje = f"⚠ Evento: {ult['evento']}\nSNR: {ult['dl_snr_db']}"

# ===== ENVÍO =====

if mensaje:
    print("Enviando alerta...")
    enviar_telegram(mensaje)

    with open(LOG, "a") as f:
        f.write(mensaje + "\n")
from subprocess import check_output

pred = check_output([
    "/home/carlos/epmp_monitor/venv/bin/python",
    "/home/carlos/epmp_monitor/bin/ia_predictiva.py"
]).decode()

if "CAIDA" in pred:
    enviar_telegram("⚠ PREDICCIÓN IA: posible caída de enlace")
