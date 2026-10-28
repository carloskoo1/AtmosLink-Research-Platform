# FEDU — Auditoría 012: evaluación de precursores y dependencia instrumental del evento UTP del 1-sep

**Fecha de auditoría:** 27-oct-2026, Perú. **Alcance:** AP 6 GHz CU01 y SM SJ01 del mismo radioenlace, evidencia AtmosLink y comunicación contemporánea de personal de campo. **Fuente:** copia SQLite íntegra de cierre de campaña 3×2 consultada mediante `sqlite3 -readonly`; NO se modificaron tablas, switch, radio ni servicios.

## A. Pregunta metodológica

El evento del cable del **puerto 6** se identificó con conversación de campo del 1-sep-2026, reconexión reportada **19:59**, y anomalía de obtención de telemetría desde aproximadamente **19:37** hasta su recuperación **20:01–20:04**. ¿Existían señales RF precursoras medibles con anterioridad que permitan justificar una etiqueta de evento *predecible*?

## B. Señal RF ANTES del cambio

En `radio_link_config_telemetry`, con intervalo local **18:33:00 a 19:33:39** del 1-sep-2026, hay **12 muestras completas** (últimos ~60 min; `LINK_OPERATIONAL_DUAL`, `sm_direct_access_ok=1` en las doce):

| Indicador | Mínimo | Máximo | Media o comportamiento |
|---|---:|---:|---|
| RSSI DL (dBm) | −74 | −73 | −73,58 |
| RSSI UL (dBm) | −80 | −80 | −80 |
| SNR DL (dB) | 23 | 24 | Estable en banda 23–24 |
| SNR UL (dB) | 18 | 19 | Estable en banda 18–19 |
| MCS DL | 204 | 204 | Sin cambio |
| MCS UL | 202 | 203 | Alternancia 202–203 |

**Interpretación:** no se detectó en estos parámetros una degradación RF gradual obvia durante la hora anterior. **No equivale a demostrar ausencia universal de precursor ni a evaluar un algoritmo ML**, pues no se calcularon tendencias multivariables preregistradas ni un test ciego.

## C. Transición de telemetría y fuente de campo

| Hora Perú | Evidencia |
|---|---|
| 19:33:39 | Última muestra `radio_link_config_telemetry=LINK_OPERATIONAL_DUAL` previa |
| 19:36:37 | Última muestra normal en `radio_link_local` |
| 19:37:48 | `radio_link_local=SM_NOT_ASSOCIATED` (regla derivada de ausencia de métricas, **no evento firmware**) |
| 19:38:42 | Error SSH al AP: `No route to host` |
| 19:43:45, 19:48:48 y 19:53:52 | Nuevos errores SSH al AP |
| 19:57 | Responsable remoto solicita verificar cable movido del puerto 6 (AP 6 GHz, según mapa del cnMatrix) |
| 19:59 | Personal en CU01 informa que cable del puerto 6 estaba movido y **ya se había reconectado** |
| 19:59:06 | Error SSH de consulta del SM persistente en su slot |
| 19:59:52 | Última fila `SM_NOT_ASSOCIATED` del recolector local |
| 20:00:53 | `UNEXPECTED_SM`, valor de estación/radio inválido, NO señal utilizable |
| 20:01:53 | Primera nueva fila `radio_link_local=ok` con RF válido |
| 20:04:07 | `LINK_OPERATIONAL_DUAL` y acceso al SM restaurados |

**No se puede inferir el instante físico exacto de retirada del cable** desde marcas periódicas. La comunicación contemporánea y el cambio del colector respaldan un incidente de conectividad/reconexión asociado al puerto 6, no comprueban por sí solos una caída PoE o un intervalo completo de `RF_LINK_DOWN`.

## D. Hallazgo de pseudorreplicación

Se cotejaron los registros de `radio_link_local` en **19:30–20:10** por `timestamp_local`, emparejando `station_id='CU01'` y `station_id='SJ01'`. Se encontraron **39 pares**, y en **los 39** coinciden exactamente `note`, `error`, `mcs_dl` y `snr_dl`. Los dos `station_id` en esta tabla son **dos etiquetas de una misma adquisición referida al enlace**, no dos observadores estadísticamente independientes. Por ello, no contar `SM_NOT_ASSOCIATED` dos veces, ni alegar corroboración independiente entre ambas filas.

`radio_link_config_telemetry` incluye lecturas a través del mismo plano local de gestión de AP/SM, por lo que su fracaso puede compartir el mecanismo de ausencia de acceso que genera el estado local. **La conversación contemporánea** es la fuente independiente del cambio físico de cable, aunque no incluye medición directa de estado RF.

## E. Falta de prueba funcional contemporánea

En `active_throughput_6g`, la primera medición del **1-sep** presente en el snapshot fue **21:40:56 (hora Perú)**. Por tanto, **NO hubo prueba de throughput archivada durante 19:37–20:04** con la cual corroborar el estado de servicio extremo a extremo. No se puede convertir automáticamente los errores SSH en prueba iperf fallida. Las pruebas del 2/3-sep entre 18:00–20:00 están normales y **no** corresponden a la intervención documentada del 1-sep.

## F. Decisión de evidencia / etiqueta

| Enunciado | Estado |
|---|---|
| El cable del puerto 6 se encontró movido y se reconectó a las 19:59 | **CORROBORADO POR COMUNICACIÓN CONTEMPORÁNEA APORTADA POR EL OPERADOR** |
| El sistema perdió acceso normal al AP/SM durante ~19:37–20:01 | **CORROBORADO POR TELEMETRÍA LOCAL Y ERRORES SSH** |
| La reconexión precedió recuperación de telemetría normal ~20:01–20:04 | **COINCIDENCIA TEMPORAL CORROBORADA** |
| El puerto 6 alimentaba físicamente el AP y cayó tensión PoE | **PENDIENTE: historial del switch/PoE** |
| El firmware confirmó desasociación / reinicio RF de AP–SM | **PENDIENTE: logs del AP/SM** |
| Hubo degradación gradual RF antes del corte | **NO EVIDENCIADA EN 12 MUESTRAS EXAMINADAS**; no es una prueba estadística de ausencia |
| El evento es positivo para H1 de predicción de degradación RF | **NO ELEGIBLE SIN CRITERIOS PREREGISTRADOS Y ETIQUETA INDEPENDIENTE** |

**Clasificación vigente:** `AP6_PORT6_CABLE_RECONNECTED_FIELD_CORROBORATED` / `ACCESS_LOSS_TELEMETRY_OBSERVED` / `RF_PHYSICAL_OUTAGE_UNDETERMINED`. Es un **caso de diagnóstico y detección de fallo abrupto**, potencial control de estrés, pero **no una etiqueta de evento RF de degradación gradual para entrenamiento confirmatorio**.

**Acción pendiente:** buscar solo en el propio cnMatrix, firmware AP y SM del 6 GHz eventos de `port6 link-down/up`, `PoE power off/on`, uptime/AP reboot y asociación/reasociación del 1-sep 19:20–20:20. Si el sistema no retiene esos logs, declarar **limitación histórica no recuperable**, no llenar con datos de otros dispositivos. Mantener evidencia original de conversación fuera del repositorio público.

## G. Consultas reproducibles (únicamente en snapshot; acceso RO)

```sql
-- Precursores RF sin interpolación:
SELECT COUNT(*) n, MIN(dl_rssi_dbm), MAX(dl_rssi_dbm),
       ROUND(AVG(dl_rssi_dbm),2),
       MIN(ul_rssi_dbm), MAX(ul_rssi_dbm),
       MIN(dl_snr_db), MAX(dl_snr_db),
       MIN(ul_snr_db), MAX(ul_snr_db)
FROM radio_link_config_telemetry
WHERE timestamp_local >= '2026-09-01T18:33:00'
  AND timestamp_local <= '2026-09-01T19:33:39'
  AND collection_status = 'LINK_OPERATIONAL_DUAL';

-- Verificar fuentes instrumentales NO independientes:
SELECT COUNT(*) total_pares,
       SUM(CASE WHEN a.note IS b.note
                   AND a.error IS b.error
                   AND a.mcs_dl IS b.mcs_dl
                   AND a.snr_dl IS b.snr_dl
                THEN 1 ELSE 0 END) pares_iguales
FROM radio_link_local AS a
JOIN radio_link_local AS b
  ON a.timestamp_local = b.timestamp_local
 AND a.station_id = 'CU01'
 AND b.station_id = 'SJ01'
WHERE a.timestamp_local >= '2026-09-01T19:30'
  AND a.timestamp_local <  '2026-09-01T20:10';
```

La coincidencia en estos campos no demuestra de por sí identidad absoluta de cualquier registro, pero sí desautoriza tratar esas dos etiquetas como corroboraciones estadísticamente independientes sin trazabilidad adicional.
