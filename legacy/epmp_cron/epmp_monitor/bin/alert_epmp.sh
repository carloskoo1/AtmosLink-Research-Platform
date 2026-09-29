#!/usr/bin/env bash

CSV="/home/carlos/epmp_monitor/data/agg_ap_$(date +%F).csv"

LAST_LINE=$(tail -n 1 "$CSV")

echo "$LAST_LINE"

if echo "$LAST_LINE" | grep -q "LOW"; then
    echo "⚠ ALERTA DETECTADA"
    echo "$LAST_LINE"
fi
