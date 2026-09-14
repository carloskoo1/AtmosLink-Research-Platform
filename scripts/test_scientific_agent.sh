#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/carlos/Proyectos/EstacionMeteorologica"
PY="$ROOT/venv/bin/python"
AGENT="$ROOT/weather_station/agents/scientific_agent.py"

cd "$ROOT"

echo "=== 1. SELFTEST ==="
"$PY" "$AGENT" selftest

echo
echo "=== 2. ESTADO ACTUAL ==="
"$PY" "$AGENT" ask "¿Cuál es el estado actual de AtmosLink?" --format narrative

echo
echo "=== 3. ANALISIS 24H ==="
"$PY" "$AGENT" ask "Compara SNR, RSSI y goodput con humedad durante las últimas 24 horas" --format narrative

echo
echo "=== 4. REPORTE REPRODUCIBLE 24H ==="
"$PY" "$AGENT" report --hours 24

echo
echo "=== 5. COMPARACION PILOTO VS PRIMER ESCENARIO FORMAL ==="
"$PY" "$AGENT" compare --freq-a 7000 --bw-a 20 --freq-b 6655 --bw-b 20 --format narrative

echo
echo "=== FIN ==="
echo "Si SELFTEST muestra all_ok=true, el agente está operativo y protegido contra escritura."


echo "=== 6. CAMPAIGN GUARD 3x2 ==="
$PY $AGENT campaign-guard

echo "=== 7. PRIMER ESCENARIO FORMAL ==="
$PY $AGENT formal-scenario --freq 6655 --bw 20
