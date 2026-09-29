#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import plotly.express as px
import os

BASE="/home/carlos/epmp_monitor"
FILE=f"{BASE}/reportes/dataset_avanzado.csv"

st.set_page_config(page_title="NOC ePMP", layout="wide")

st.title("📡 NOC ePMP / Starlink - Dashboard PRO")

# =========================
# CARGA
# =========================

if not os.path.exists(FILE):
    st.error("No existe dataset_avanzado.csv")
    st.stop()

df = pd.read_csv(FILE)
df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
df = df.dropna(subset=["ts"])

# =========================
# FILTROS
# =========================

st.sidebar.header("Filtros")

evento_sel = st.sidebar.multiselect(
    "Evento",
    options=df["evento"].unique(),
    default=df["evento"].unique()
)

riesgo_sel = st.sidebar.multiselect(
    "Riesgo",
    options=df["riesgo_nivel"].unique(),
    default=df["riesgo_nivel"].unique()
)

df = df[
    (df["evento"].isin(evento_sel)) &
    (df["riesgo_nivel"].isin(riesgo_sel))
]

# =========================
# KPIs
# =========================

ult = df.tail(1).iloc[0]

c1, c2, c3, c4 = st.columns(4)

c1.metric("Estado Evento", ult["evento"])
c2.metric("Riesgo", ult["riesgo_nivel"])
c3.metric("SNR DL", round(ult["dl_snr_db"],2))
c4.metric("Rate DL", round(ult["dl_rate"],2))

# =========================
# ALERTA VISUAL
# =========================

if ult["riesgo_nivel"] == "ALTO":
    st.error("🔴 ALERTA CRÍTICA: Riesgo alto de caída de enlace")

elif ult["riesgo_nivel"] == "MEDIO":
    st.warning("🟡 Riesgo medio detectado")

else:
    st.success("🟢 Enlace estable")

# =========================
# GRÁFICAS
# =========================

st.subheader("📈 Métricas RF")

fig1 = px.line(df, x="ts", y="dl_snr_db", title="SNR DL")
st.plotly_chart(fig1, width='stretch')

fig2 = px.line(df, x="ts", y="dl_rssi_dbm", title="RSSI DL")
st.plotly_chart(fig2, width='stretch')

fig3 = px.line(df, x="ts", y="dl_rate", title="Throughput DL")
st.plotly_chart(fig3, width='stretch')

# =========================
# EVENTOS
# =========================

st.subheader("⚠️ Eventos detectados")

eventos_df = df[df["evento"] != "NORMAL"]

fig4 = px.scatter(
    eventos_df,
    x="ts",
    y="dl_snr_db",
    color="evento",
    title="Eventos RF"
)

st.plotly_chart(fig4, width='stretch')

# =========================
# RIESGO
# =========================

st.subheader("📊 Riesgo del Enlace")

fig5 = px.line(df, x="ts", y="riesgo", title="Nivel de Riesgo")
st.plotly_chart(fig5, width='stretch')

# =========================
# TABLA
# =========================

st.subheader("📋 Últimos registros")

st.dataframe(df.tail(100), use_container_width=True)
