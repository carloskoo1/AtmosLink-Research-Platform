#!/usr/bin/env bash
set -euo pipefail

REMOTE_DIR="atmoslink_drive:AtmosLink_Backups/CU01/field"
PATTERN="backup_CU01_*.zip"
PROJECT_DIR="$HOME/Proyectos/EstacionMeteorologica"
LOG_DIR="$PROJECT_DIR/logs"
AUDIT_DIR="$PROJECT_DIR/Data/audits/backup_retention"
LOCK_FILE="/tmp/atmoslink_remote_retention.lock"

mkdir -p "$LOG_DIR" "$AUDIT_DIR"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "$(date --iso-8601=seconds) | OMITIDO | ya existe otra retención en ejecución"
    exit 0
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
REPORT="$AUDIT_DIR/retention_${STAMP}.tsv"
SUMMARY="$AUDIT_DIR/retention_${STAMP}_summary.txt"
WORK_DIR="$(mktemp -d)"
INVENTORY="$WORK_DIR/inventory.tsv"
KEEP="$WORK_DIR/keep.tsv"
DELETE="$WORK_DIR/delete.tsv"

cleanup() {
    rm -rf -- "$WORK_DIR"
}
trap cleanup EXIT

exec > >(tee -a "$LOG_DIR/remote_retention.log") 2>&1

echo
echo "============================================================"
echo "RETENCIÓN REMOTA ATMOSLINK"
echo "Fecha: $(date --iso-8601=seconds)"
echo "Carpeta: $REMOTE_DIR"
echo "============================================================"

if ! command -v rclone >/dev/null 2>&1; then
    echo "ERROR: rclone no está instalado."
    exit 1
fi

if ! timeout 120 rclone lsf "$REMOTE_DIR" \
    --max-depth 1 \
    --files-only \
    --include "$PATTERN" \
    --contimeout 10s \
    --timeout 60s \
    >/dev/null
then
    echo "ERROR: no se pudo acceder al remoto."
    exit 1
fi

timeout 300 rclone lsf "$REMOTE_DIR" \
    --max-depth 1 \
    --files-only \
    --include "$PATTERN" \
    --format 'tsp' \
    --contimeout 10s \
    --timeout 60s \
    | awk -F';' '
        NF >= 3 {
            timestamp=$1
            size=$2
            path=$3
            for (i=4; i<=NF; i++) {
                path=path ";" $i
            }
            print timestamp "\t" size "\t" path
        }
    ' \
    | sort > "$INVENTORY"

TOTAL_FILES="$(wc -l < "$INVENTORY")"
TOTAL_BYTES="$(awk -F'\t' '{s += $2} END {printf "%.0f", s+0}' "$INVENTORY")"

echo "Archivos encontrados: $TOTAL_FILES"
echo "Espacio encontrado: $(numfmt --to=iec-i --suffix=B "$TOTAL_BYTES")"

if [ "$TOTAL_FILES" -eq 0 ]; then
    echo "No existen archivos con el patrón $PATTERN."
    exit 0
fi

NOW_EPOCH="$(date +%s)"
LIMIT_24H="$((NOW_EPOCH - 24 * 3600))"
LIMIT_30D="$((NOW_EPOCH - 30 * 24 * 3600))"
LIMIT_12M="$((NOW_EPOCH - 365 * 24 * 3600))"

LATEST_FILE="$(tail -n 1 "$INVENTORY" | cut -f3-)"

declare -A KEEP_REASON
declare -A DAILY_SELECTED
declare -A MONTHLY_SELECTED

while IFS=$'\t' read -r TIMESTAMP SIZE FILE; do
    FILE_EPOCH="$(date -d "$TIMESTAMP" +%s 2>/dev/null || echo 0)"

    if [ "$FILE_EPOCH" -eq 0 ]; then
        KEEP_REASON["$FILE"]="fecha_no_interpretable"
        continue
    fi

    DAY_KEY="$(date -d "$TIMESTAMP" +%Y-%m-%d)"
    MONTH_KEY="$(date -d "$TIMESTAMP" +%Y-%m)"

    if [ "$FILE" = "$LATEST_FILE" ]; then
        KEEP_REASON["$FILE"]="ultimo_respaldo"
    elif [ "$FILE_EPOCH" -ge "$LIMIT_24H" ]; then
        KEEP_REASON["$FILE"]="ultimas_24_horas"
    elif [ "$FILE_EPOCH" -ge "$LIMIT_30D" ]; then
        DAILY_SELECTED["$DAY_KEY"]="$FILE"
    elif [ "$FILE_EPOCH" -ge "$LIMIT_12M" ]; then
        MONTHLY_SELECTED["$MONTH_KEY"]="$FILE"
    fi
done < "$INVENTORY"

for KEY in "${!DAILY_SELECTED[@]}"; do
    FILE="${DAILY_SELECTED[$KEY]}"
    KEEP_REASON["$FILE"]="respaldo_diario"
done

for KEY in "${!MONTHLY_SELECTED[@]}"; do
    FILE="${MONTHLY_SELECTED[$KEY]}"
    KEEP_REASON["$FILE"]="respaldo_mensual"
done

while IFS=$'\t' read -r TIMESTAMP SIZE FILE; do
    if [ -n "${KEEP_REASON[$FILE]+x}" ]; then
        printf '%s\t%s\t%s\t%s\n' \
            "$TIMESTAMP" "$SIZE" "$FILE" "${KEEP_REASON[$FILE]}" >> "$KEEP"
    else
        printf '%s\t%s\t%s\n' \
            "$TIMESTAMP" "$SIZE" "$FILE" >> "$DELETE"
    fi
done < "$INVENTORY"

touch "$KEEP" "$DELETE"

KEEP_FILES="$(wc -l < "$KEEP")"
DELETE_FILES="$(wc -l < "$DELETE")"
KEEP_BYTES="$(awk -F'\t' '{s += $2} END {printf "%.0f", s+0}' "$KEEP")"
DELETE_BYTES="$(awk -F'\t' '{s += $2} END {printf "%.0f", s+0}' "$DELETE")"

if ! grep -Fq $'\t'"$LATEST_FILE"$'\t' "$KEEP"; then
    echo "ERROR: el respaldo más reciente no quedó protegido."
    exit 1
fi

if [ "$KEEP_FILES" -lt 1 ]; then
    echo "ERROR: la política no seleccionó ningún respaldo para conservar."
    exit 1
fi

if [ "$DELETE_FILES" -ge "$TOTAL_FILES" ]; then
    echo "ERROR: la política intentaría retirar todos los respaldos."
    exit 1
fi

{
    echo "Fecha: $(date --iso-8601=seconds)"
    echo "Remoto: $REMOTE_DIR"
    echo "Total: $TOTAL_FILES"
    echo "Conservar: $KEEP_FILES"
    echo "Retirar: $DELETE_FILES"
    echo "Espacio recuperable: $(numfmt --to=iec-i --suffix=B "$DELETE_BYTES")"
    echo "Último respaldo protegido: $LATEST_FILE"
} | tee "$SUMMARY"

{
    printf 'accion\tfecha_remota\ttamano_bytes\tarchivo\tresultado\n'

    while IFS=$'\t' read -r TIMESTAMP SIZE FILE REASON; do
        printf 'CONSERVAR\t%s\t%s\t%s\t%s\n' \
            "$TIMESTAMP" "$SIZE" "$FILE" "$REASON"
    done < "$KEEP"
} > "$REPORT"

echo
echo "Se conservarán: $KEEP_FILES"
echo "Espacio conservado: $(numfmt --to=iec-i --suffix=B "$KEEP_BYTES")"
echo "Se enviarán a la papelera: $DELETE_FILES"
echo "Espacio recuperable: $(numfmt --to=iec-i --suffix=B "$DELETE_BYTES")"
echo "Último respaldo protegido: $LATEST_FILE"
echo
echo "Iniciando eliminación controlada..."

REMOVED=0
FAILED=0

while IFS=$'\t' read -r TIMESTAMP SIZE FILE; do
    TARGET="$REMOTE_DIR/$FILE"

    if timeout 180 rclone deletefile "$TARGET" \
        --drive-use-trash=true \
        --contimeout 10s \
        --timeout 120s
    then
        printf 'PAPELERA\t%s\t%s\t%s\tOK\n' \
            "$TIMESTAMP" "$SIZE" "$FILE" >> "$REPORT"
        REMOVED=$((REMOVED + 1))
    else
        printf 'PAPELERA\t%s\t%s\t%s\tERROR\n' \
            "$TIMESTAMP" "$SIZE" "$FILE" >> "$REPORT"
        FAILED=$((FAILED + 1))
    fi
done < "$DELETE"

echo
echo "===== VERIFICACIÓN POSTERIOR ====="

if timeout 120 rclone lsf "$REMOTE_DIR/$LATEST_FILE" \
    --files-only \
    --contimeout 10s \
    --timeout 60s \
    >/dev/null
then
    echo "Último respaldo: VERIFICADO"
else
    echo "ERROR: no se pudo verificar el último respaldo."
    exit 1
fi

REMAINING="$(
    timeout 300 rclone lsf "$REMOTE_DIR" \
        --max-depth 1 \
        --files-only \
        --include "$PATTERN" \
        --contimeout 10s \
        --timeout 60s \
        | wc -l
)"

{
    echo "Enviados a papelera: $REMOVED"
    echo "Fallidos: $FAILED"
    echo "Respaldos restantes: $REMAINING"
    echo "Informe: $REPORT"
} | tee -a "$SUMMARY"

echo
echo "RETENCIÓN COMPLETADA"
echo "Los archivos retirados permanecen recuperables en la papelera."
echo "Informe: $REPORT"

if [ "$FAILED" -gt 0 ]; then
    exit 1
fi
