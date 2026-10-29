# AtmosLink 3×2 — Consolidación diaria de trazabilidad: 2026-10-28

**Enlace:** CU01 (AP Cuñacales) ↔ SJ01 (SM San José).  
**Ventana auditada:** 2026-10-28 00:00:00–23:59:59, America/Lima (UTC−05:00).  
**Inspección:** iniciada 2026-10-29T00:33:23-05:00; lecturas de servicios y fuentes efectuadas después de las 00:33.  
**Modalidad:** estrictamente read-only en Controlador. `rpi-sanjose64` respondió a `tailscale ping` (~28 ms), pero el SSH directo fue **denegado por la política del tailnet**. No se intentó eludirla. La evidencia SJ01 procede de los registros sincronizados en Controlador. **No se modificaron RF, PoE, VLAN, servicios, timers ni bases de datos.**

> **Separación metodológica:** el experimento factorial 3×2 concluyó el **2026-10-27 a las 00:00 −05:00**. El 28/10 corresponde a **línea base posterior**, no a un nuevo bloque factorial. Sus mediciones documentan continuidad y calidad de adquisición, pero no deben incorporarse automáticamente al análisis causal del 3×2.

## 1. Escenario, RF y transiciones

Estado persistente: `sequence=FINAL_BASELINE`, `scenario_id=BASE_7000_20`, **7000 MHz / 20 MHz**, fase `BASELINE` (bloque 0). La transición programada F7000_B40 → BASE_7000_20 fue confirmada el **2026-10-27T00:02:58-05:00** (`SWITCH_COMMITTED=OK`). El archivo `campaign_events.jsonl` no registra eventos nuevos después de esa transición; su última modificación es del 27/10. El diario del ejecutor del 28/10 tampoco mostró nuevos cambios de escenario.

`scientific_campaign_6g_integrated.csv`, filtrado por `rf_timestamp_local` del 28/10:

| Indicador | Resultado |
|---|---:|
| Observaciones RF | **287** |
| `LINK_OPERATIONAL_DUAL` | **287/287** |
| `COLLECTION_ERROR` | **0** |
| Configuración AP/SM concordante | **287/287** |
| Frecuencia / ancho en filas operativas | **7000 MHz / 20 MHz** |
| RSSI medio DL / UL | **−73.592 / −80.265 dBm** |
| SNR medio DL / UL | **23.463 / 18.282 dB** |
| Primera / última observación del día | **00:00:02 / 23:55:44** |
| Filas operativas con cero en RSSI/SNR | **0** |

No se encontraron errores RF del día en la exportación examinada. La última fila global visible durante la inspección corresponde a **2026-10-29T00:10:47-05:00**, posterior a la ventana diaria.

**Matching meteorológico del 28/10:** CU01 **280/287**, SJ01 **287/287**, dual **280/287 (97.56 %)**. Las **7 excepciones** CU01=0/SJ01=1 ocurrieron a las **00:50:16, 01:05:19, 02:05:36, 12:23:10, 16:29:02, 17:24:23 y 19:19:46**. Se preservan sin imputación.

## 2. Meteorología CU01/SJ01 — master_observations_multistation

**2341 registros** del 28/10: CU01 **1381**, SJ01 **960**.

| Indicador | CU01 | SJ01 |
|---|---:|---:|
| Temperatura media | **21.070 °C** | **10.109 °C** |
| Temperatura mínima / máxima | 16.36 / 30.41 °C | 5.55 / 18.27 °C |
| Humedad relativa media | **58.207 %** | **85.019 %** |
| Presión media | **741.170 hPa** | **665.277 hPa** |
| Viento medio | **0.298 m/s** | **1.579 m/s** |
| Ráfaga media | 0.684 m/s | 2.333 m/s |
| Última observación del día | **23:59:37** | **23:58:40** |
| `local_bme_ok=1` | **1381/1381** | **960/960** |

La última sincronización remota del 28/10 registrada a las **23:59:59** indicó `Status global: OK`. Se observaron fallos intermitentes anteriores, detallados abajo. El matching temporal y los flags de adquisición no equivalen a calibración o validación metrológica.

## 3. Rendimiento activo — active_throughput_6g

**192 pruebas, 192 `OK`**: 96 DL y 96 UL. Primera prueba **00:00:04**, última **23:45:19**.

| Métrica sobre pruebas OK | DL | UL |
|---|---:|---:|
| Goodput medio medido | **63.931 Mbps** | **32.080 Mbps** |
| Goodput máximo | 67.487 Mbps | 32.263 Mbps |
| Retransmisiones TCP medias | 64.615 | 33.875 |
| Máximo de retransmisiones | 443 | 202 |
| Goodput cero con estado OK | 0 | 0 |

RTT ICMP medio **3.645 ms**; pérdida ICMP media **0 %**. **191/192** pruebas consignan explícitamente 7000 MHz/20 MHz. La prueba **UL de las 21:45:19**, aunque `OK` y con goodput 32.117 Mbps, carece de metadatos RF de frecuencia/ancho y de vínculo de telemetría. **Anomalía de completitud QC**, no prueba de cambio RF. No inferir capacidad PHY ni efectos factoriales a partir de estos promedios de línea base.

## 4. Watermark y control pendiente F6655_B20

Watermark de referencia: `2026-09-15T23:36:42-05:00`.  
Última observación global integrada al corte: `2026-10-29T00:10:47-05:00`.  
**Avance temporal: CONFIRMADO.**

Revisión retrospectiva de filas **F6655_B20** posteriores al watermark:

| Control | Resultado |
|---|---:|
| Filas | **1724** |
| `cu01_weather_matched=1` | **1694/1724** |
| `sj01_weather_matched=1` | **1724/1724** |
| Ambos flags en 1 | **1694/1724 (98.26 %)** |
| Excepciones duales | **30** |
| Última fila F6655_B20 | `2026-10-18T23:55:49-05:00` |

Distribución de excepciones: **16/09 (3), 07/10 (8), 08/10 (9), 17/10 (4), 18/10 (6)**. El 28/10 no se generaron filas F6655_B20: operó BASE_7000_20. **El requisito de matching dual del 100 % sigue NO CONFIRMADO**; no reinterpretar la ausencia de nuevas filas como validación positiva. Mantener conciliación retrospectiva, trazabilidad de versiones y revisión de las 30 excepciones sin alterar los datos fuente.

## 5. Servicios, timers, incidentes y recuperaciones

**Estado de servicios al inspeccionar el 29/10:** `atmoslink-dashboard`, `atmoslink-scheduler`, `atmoslink-event-monitor`, `atmoslink-radio-config-6g` y `weather-logger` **active/running**. Los servicios periódicos `andean-campaign`, `andean-throughput`, `atmoslink-throughput-6g`, `atmoslink-remote-sync`, `atmoslink-weather-watchdog`, `atmoslink-scientific-validation` y `atmoslink-backup-recovery` estaban **inactive/success**, estado normal entre ejecuciones. **`atmoslink-remote-backup.service` estaba failed/exit-code.** Se observaron timers programados para esos ocho procesos periódicos, incluido el de respaldo remoto.

**Medición formal:** `andean-throughput.service` tuvo **24 ejecuciones terminadas satisfactoriamente**, cada una con el aviso `Sin medición formal: fuera de fase EXPERIMENT`. Esto es correcto para la fase posterior, pero **no demuestra que se corrigiera el error de argumentos de la fase experimental**. El servicio independiente produjo las 192 pruebas activas descritas.

**Sincronización remota SJ01:** **13 ejecuciones fallidas** (`Failed with result`), con registros de timeout, a las **01:13:02, 02:58:42, 05:20:57, 06:42:26, 07:14:49, 11:04:30, 11:18:44, 12:31:54, 14:58:15, 16:54:13, 17:38:50, 18:05:22 y 21:02:11**. También se registraron **709 mensajes `Status global: OK`**; el último a las **23:59:59**. Los fallos de sincronización no acreditan por sí solos indisponibilidad del radioenlace.

**Watchdog meteorológico CU01:** **8 recuperaciones automáticas** de `weather-logger.service`, iniciadas a las **00:35:27, 00:53:46, 01:10:00, 02:08:59, 12:26:53, 16:32:51, 17:29:46 y 19:23:36**. Las ocho terminaron con `RECUPERACIÓN EJECUTADA | weather-logger.service=active`, entre 5 y 6 segundos después. Son **acciones automáticas, no humanas**.

**Asociación temporal que merece auditoría:** las **7/7 excepciones CU01 del matching** anteceden a una recuperación del watchdog entre **3 min 23 s y 5 min 23 s**. Este patrón temporal es compatible con ventanas de falta de frescura meteorológica; **no prueba causalidad**. Debe evaluarse mediante comparación de timestamps de adquisición, tolerancia de matching, estado del logger y cronología del watchdog.

**Validación científica:** 24 ejecuciones horarias con `CU01: OK` y `SJ01: OK`; la última terminó a las **23:43:49**. Esto no elimina las excepciones de matching observadas en el integrado.

**Respaldo remoto:** `atmoslink-remote-backup.service` falló el **28/10 a las 02:46:42** por cuota de Google Drive (`RATE_LIMIT_EXCEEDED`, `uploaded=False`, `verified=False`). El recuperador registró **15 eventos `RECOVERY COMPLETE 2/2`** y **29 ejecuciones fallidas** durante el 28/10. El respaldo identificado como `backup_CU01_20261028_182310.zip` quedó **verificado en ambos destinos a las 23:41:56**, y fue nuevamente verificado el **29/10 a las 00:15:43**. En los directorios locales inspeccionados, ese fue el archivo de respaldo del 28/10 más reciente localizado. **La verificación de esa copia no certifica la totalidad de la cola histórica.** No se alteraron servicios ni se ejecutaron recuperaciones manuales.

## 6. SAFE_ABORT, executor_failure, acciones humanas y decisiones metodológicas

No se identificaron eventos nuevos `SAFE_ABORT`, `executor_failure`, `SWITCH_FAILED` ni `ROLLBACK` fechados el 28/10 en `campaign_events.jsonl`; el diario de `andean-campaign.service` no mostró cambios de escenario. La última transición confirmada continúa siendo la del **27/10 a las 00:02:58**. No se identificaron intervenciones humanas RF atribuibles en las fuentes examinadas. Estas constataciones no equivalen a una auditoría exhaustiva de todos los accesos.

**Clasificación:** línea base estable y validación horaria = operación normal; fallos de sincronización, respaldo y metadatos incompletos = incidentes de adquisición/servicios; reinicios de logger y verificación de copias = recuperaciones automáticas; cambios RF manuales = no evidenciados; inspección actual = consultas de lectura.

**Decisiones metodológicas:** (1) mantener separada la fase BASELINE del diseño factorial 3×2; (2) conservar las siete excepciones CU01 y las 30 históricas F6655_B20 sin imputación; (3) auditar la asociación temporal entre excepciones y reinicios del logger sin atribuir causalidad; (4) marcar la prueba UL de las 21:45:19 como `RF_METADATA_MISSING` a efectos de QC documental, sin modificar el CSV; (5) distinguir goodput de tasa PHY y éxito del servicio de completitud científica; (6) preservar la procedencia de los respaldos y no declarar cerrada la cola histórica sin verificación; (7) no inferir efectos causales del factorial a partir de observaciones posteriores al cierre.

## 7. Procedencia, límites y seguridad

Fuentes leídas en Controlador: `Data/exports/scientific_campaign_6g_integrated.csv`, `Data/exports/master_observations_multistation.csv`, `Data/exports/active_throughput_6g.csv`, `campaign_runtime/campaign_state.json`, `campaign_runtime/executor_state.json`, `campaign_runtime/campaign_events.jsonl`, `systemctl`, `journalctl`, `tailscale status/ping/ssh` (SSH denegado). Cifras basadas en las exportaciones existentes durante la inspección; pueden requerir conciliación por reexportaciones retrospectivas. Se omitieron credenciales, secretos, direcciones privadas, volcados de bases de datos y registros brutos sensibles.

**Documento nuevo:** `docs/DAILY_TRACE_2026-10-28_ATMOSLINK_3X2.md` en la rama predeterminada verificada `feature/atmoslink-ui-v2`. Se comprobó previamente que la ruta no existía; crear sin sobrescribir documentos anteriores.
