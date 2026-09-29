#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import plotly.express as px
import os

BASE="/home/carlos/epmp_monitor"
DATA=f"{BASE}/data"
MODEL=f"{BASE}/reportes/dataset_modelo_epmp.csv"

st.set_page_config(page_title="Dashboard ePMP", layout="wide")
st.title("📡 Dashboard Monitoreo ePMP / Starlink")

# Verificar archivo
if not os.path.exists(MODEL):
    st.error("No existe dataset_modelo_epmp.csv")
    st.stop()

df=pd.read_csv(MODEL)

df["ts"]=pd.to_datetime(df["ts"], errors="coerce")
df=df.dropna(subset=["ts"])

# Último registro
ult=df.tail(1).iloc[0]

# KPIs
c1,c2,c3,c4=st.columns(4)

c1.metric("Estado", ult["estado_enlace"])
c2.metric("IDOE", int(ult["IDOE_operativo"]))
c3.metric("SNR DL", ult["dl_snr_db"])
c4.metric("Rate DL", ult["dl_rate"])

# Gráficas
st.subheader("📈 Tendencias")

fig1=px.line(df, x="ts", y="IDOE_operativo", title="IDOE")
st.plotly_chart(fig1, use_container_width=True)

fig2=px.line(df, x="ts", y="dl_snr_db", title="SNR DL")
st.plotly_chart(fig2, use_container_width=True)

fig3=px.line(df, x="ts", y="dl_rssi_dbm", title="RSSI DL")
st.plotly_chart(fig3, use_container_width=True)

fig4=px.line(df, x="ts", y="dl_rate", title="Rate DL")
st.plotly_chart(fig4, use_container_width=True)

# Tabla
st.subheader("📊 Últimos registros")
st.dataframe(df.tail(50))
