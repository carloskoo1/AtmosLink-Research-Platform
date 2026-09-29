#!/usr/bin/env bash
set -e

BASE="/home/carlos/epmp_monitor"
LOG_DIR="$BASE/logs"
PYTHON="$BASE/venv/bin/python"

SECRETS_FILE="${EPMP_DB_SECRETS_FILE:-/home/carlos/.config/atmoslink/epmp_db.env}"

if [[ ! -r "$SECRETS_FILE" ]]; then
    echo "ERROR: no se puede leer $SECRETS_FILE" >&2
    exit 1
fi

set -a
source "$SECRETS_FILE"
set +a

if [[ -z "${EPMP_DB_URL:-}" ]]; then
    echo "ERROR: EPMP_DB_URL no configurado" >&2
    exit 1
fi

mkdir -p "$LOG_DIR"

echo "===== PIPELINE $(date) =====" >> "$LOG_DIR/pipeline.log"

CSV_COUNT=$(find "$BASE/data" -maxdepth 1 -type f -name "agg_ap_*.csv" | wc -l)

if [ "$CSV_COUNT" -eq 0 ]; then
    echo "No hay CSV diarios en $BASE/data" >> "$LOG_DIR/pipeline.log"
    echo "===== FIN PIPELINE =====" >> "$LOG_DIR/pipeline.log"
    exit 0
fi

echo "CSV detectados: $CSV_COUNT" >> "$LOG_DIR/pipeline.log"

if [ -f "$BASE/bin/merge_nuevos.py" ]; then
    "$PYTHON" "$BASE/bin/merge_nuevos.py" >> "$LOG_DIR/merge.log" 2>&1
else
    echo "merge_nuevos.py no existe, se omite" >> "$LOG_DIR/pipeline.log"
fi

"$PYTHON" "$BASE/bin/modelo_avanzado.py" >> "$LOG_DIR/modelo.log" 2>&1
"$PYTHON" "$BASE/bin/estado_predictivo.py" >> "$LOG_DIR/predictivo.log" 2>&1

"$PYTHON" "$BASE/bin/db_writer.py" >> "$LOG_DIR/db.log" 2>&1
"$PYTHON" "$BASE/bin/db_writer_predictivo.py" >> "$LOG_DIR/db_predictivo.log" 2>&1
"$PYTHON" "$BASE/bin/ia_operador.py" >> "$LOG_DIR/ia.log" 2>&1

echo "===== FIN PIPELINE =====" >> "$LOG_DIR/pipeline.log"
