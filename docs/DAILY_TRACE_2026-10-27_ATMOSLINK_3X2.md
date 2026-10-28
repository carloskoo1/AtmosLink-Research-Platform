# AtmosLink 3×2 — Consolidación diaria de trazabilidad: 2026-10-27

**Enlace:** CU01 (AP Cuñacales) ↔ SJ01 (SM San José).  
**Ventana auditada:** 2026-10-27 00:00:00–23:59:59, America/Lima (UTC−05:00).  
**Inspección:** 2026-10-28, 00:48–00:51 (UTC−05:00).  
**Modalidad:** lectura únicamente sobre Controlador. Se comprobó presencia de `rpi-sanjose64` en Tailscale; SSH directo fue rechazado por la política del tailnet («policy does not permit ... SSH»). No se intentó eludir el control. La evidencia SJ01 procede de datos sincronizados y logs en Controlador. No se modificaron RF, PoE, VLAN, servicios, timers ni bases de datos.

> **Delimitación esencial:** la campaña factorial 3×2 terminó el **2026-10-27 a las 00:00:00 −05:00** (42 días, 18 bloques). Este día corresponde a la **fase posterior de línea base**, no a un bloque experimental 3×2. Las observaciones de este informe se conservan para continuidad operativa y trazabilidad, **no** se agregan automáticamente al análisis factorial.

## 1. Escenario, transición y RF

El estado persistente del ejecutor indica `sequence=FINAL_BASELINE`, escenario **BASE_7000_20**, frecuencia **7000 MHz**, ancho **20 MHz**, fase `BASELINE` (bloque 0). Se documentó la transición programada desde la configuración previa de **7000 MHz/40 MHz**:

| Evento | Fecha y hora local | Resultado |
|---|---|---|
| `SWITCH_START` | 2026-10-27 00:00:01 | STARTED |
| `TRIAL_APPLIED` | 2026-10-27 00:00:02 | OK |
| `TRIAL_CONFIRMED` | 2026-10-27 00:02:40 | OK |
| `SWITCH_COMMITTED` | **2026-10-27 00:02:58** | **OK** |

El archivo estructurado `campaign_events.jsonl` presenta **77 eventos** del 27/10, incluidos 21 `CONNECTIVITY_PROBE=OK` y 52 `CONNECTIVITY_PROBE=WAITING` durante el cambio. No se observaron nuevos cambios de escenario posteriores al commit en esa fuente.

**`scientific_campaign_6g_integrated.csv`**, filas con `rf_timestamp_local` del 27/10:

| Métrica | Valor |
|---|---:|
| Observaciones integradas | **285** |
| `LINK_OPERATIONAL_DUAL` | **284** |
| `COLLECTION_ERROR` | **1** |
| Configuración AP/SM concordante en observaciones operativas | **284/284** |
| RSSI medio DL / UL (solo operativas) | **−74.648 / −80.658 dBm** |
| SNR medio DL / UL (solo operativas) | **22.616 / 17.958 dB** |
| Primera / última fila | **00:04:45 / 23:50:00** |
| Frecuencia y ancho en filas operativas | **7000 MHz / 20 MHz** |

La única fila `COLLECTION_ERROR`, a las **17:48:33**, reporta «La consulta respondió, pero faltan variables obligatorias». Se clasifica como **error de adquisición/integridad de variables**, no como prueba de caída física del enlace. No se observaron ceros en los cuatro indicadores RSSI/SNR de las 284 filas operativas. El export integrado estaba actualizado hasta las 23:50:00 al corte; la ausencia de filas posteriores no se interpreta automáticamente como pérdida de conectividad.

**Matching meteorológico integrado del 27/10:** CU01 **280/285**, SJ01 **285/285**, dual **280/285 (98.25 %)**. Las cinco excepciones CU01=0/SJ01=1 ocurrieron a las **00:14:47, 00:24:48, 07:51:34, 09:11:50 y 20:34:17**. Conservarlas sin imputación.

## 2. Clima CU01 y SJ01 — `master_observations_multistation.csv`

**2320 filas** del día: CU01 **1383**, SJ01 **937**. Los promedios se calcularon sobre los valores numéricos disponibles de cada estación.

| Indicador | CU01 | SJ01 |
|---|---:|---:|
| Temperatura media | **19.822 °C** | **9.364 °C** |
| Temperatura mínima / máxima | 14.73 / 28.79 °C | 6.15 / 16.06 °C |
| Humedad relativa media | **60.190 %** | **87.722 %** |
| Presión media | **741.285 hPa** | **665.318 hPa** |
| Viento medio | **0.224 m/s** | **1.245 m/s** |
| Última observación | **23:59:40** | **23:59:37** |
| `local_bme_ok` distinto de 1 | 0 | 0 |

La sincronización de SJ01 finalizó con `Status global: OK` a las **23:58:53** y una nueva ejecución satisfactoria a las **23:59:34**. El matching por minuto y los flags de adquisición no constituyen, por sí solos, calibración ni validación metrológica.

## 3. Rendimiento activo — `active_throughput_6g.csv`

**190 pruebas del 27/10: 190 OK**, distribuidas en **95 DL y 95 UL**. Todas las filas registran **7000 MHz / 20 MHz**. Primera prueba **00:15:06**; última **23:45:19**.

| Métrica de pruebas OK | DL | UL |
|---|---:|---:|
| Goodput medio medido | **54.384 Mbps** | **29.902 Mbps** |
| Goodput máximo | **66.373 Mbps** | **32.247 Mbps** |
| Retransmisiones TCP medias | **55.084** | **30.779** |
| Máximo de retransmisiones | 304 | 194 |
| Pruebas OK con goodput cero | 0 | 0 |

RTT ICMP medio de las 190 pruebas: **3.983 ms**; pérdida ICMP media: **0 %**. Se trata de **goodput activo**, no de tasa física PHY reportada por Cambium. No inferir efectos del factor frecuencia/ancho a partir de estos datos de línea base posteriores al experimento.

## 4. Watermark y validación pendiente F6655_B20

**Watermark de referencia:** `2026-09-15T23:36:42-05:00`.  
**Última fila global del integrado al corte:** `2026-10-27T23:50:00-05:00`.  
**Resultado:** **avance temporal CONFIRMADO**.

Para filas retrospectivas de **F6655_B20** posteriores al watermark, la exportación actual contiene **1724 observaciones**, desde `2026-09-15T23:41:43-05:00` hasta `2026-10-18T23:55:49-05:00`:

- `cu01_weather_matched=1`: **1694/1724**.
- `sj01_weather_matched=1`: **1724/1724**.
- Ambos indicadores en 1: **1694/1724 (98.26 %)**.
- **30 excepciones** CU01=0/SJ01=1, distribuidas: 16/09 (3), 07/10 (8), 08/10 (9), 17/10 (4) y 18/10 (6).

No se generaron filas nuevas F6655_B20 el 27/10, pues la configuración activa era la línea base de 7000/20. **La condición de matching dual del 100 % sigue NO CONFIRMADA.** Mantenerla como control abierto, sin rellenar ni alterar registros originales, y reconciliar versiones históricas antes de congelar el conjunto científico.

## 5. Servicios, timers, incidentes y recuperaciones

**Servicios de ejecución continua al corte:** `atmoslink-dashboard`, `atmoslink-scheduler`, `atmoslink-event-monitor` y `atmoslink-radio-config-6g` en estado **active**. Los servicios periódicos `atmoslink-throughput-6g`, `atmoslink-remote-sync` y `atmoslink-scientific-validation` estaban **inactive/success**, comportamiento normal entre ejecuciones. Se observaron timers programados para `andean-campaign`, `andean-throughput`, `atmoslink-throughput-6g`, `atmoslink-remote-sync`, `atmoslink-weather-watchdog`, `atmoslink-backup-recovery`, `atmoslink-scientific-validation` y `atmoslink-remote-backup`.

**Medición formal:** `andean-throughput.service` registró **24 ejecuciones terminadas con success** el 27/10. Los logs aclaran `Sin medición formal: fuera de fase EXPERIMENT`. **No interpretar este éxito como reparación del fallo de argumentos observado durante la fase experimental ni como 24 pruebas adicionales.** El colector independiente sí produjo las 190 pruebas activas descritas.

**Logger meteorológico:** el watchdog registró **9 recuperaciones automáticas** de `weather-logger.service`, cada una seguida de `RECUPERACIÓN EJECUTADA | ...=active`: **00:16:00, 00:26:18, 07:12:49, 07:53:29, 09:14:47, 12:58:19, 13:12:34, 18:29:37 y 20:37:39**. Los disparadores fueron períodos sin nuevas mediciones de aproximadamente 301–422 s. Se trata de **acciones automáticas**, no humanas. Algunas son próximas a excepciones CU01; **no se afirma causalidad sin alineación temporal detallada**.

**Sincronización remota:** `atmoslink-remote-sync.service` registró **22 resultados fallidos** el 27/10 (predominaron timeouts), pero también sincronizaciones satisfactorias; el cierre de las **23:58:53** fue OK. Los fallos de sincronización no equivalen necesariamente a pérdida de conectividad RF.

**Respaldo remoto:** `atmoslink-remote-backup.service` falló a las **02:46:51** por cuota de Google Drive (`RATE_LIMIT_EXCEEDED`; `uploaded=False`, `verified=False`). El recuperador verificó **ambos destinos** para la copia identificada como `backup_CU01_20261027_181654.zip` a las **23:34:56** (`RECOVERY COMPLETE 2/2`). Esto certifica **esa copia**, no toda la cola histórica ni cualquier copia posterior. En la inspección del 28/10 el servicio de recuperación figuraba en estado **failed** por un intento posterior; una nueva copia del 28/10 todavía no tenía verificación dual. No se modificaron servicios para corregirlo.

**Validación científica:** `atmoslink-scientific-validation.service` terminó a las **23:41:18** con `CU01: OK` y `SJ01: OK`.

## 6. SAFE_ABORT, executor_failure y acciones humanas

En `campaign_events.jsonl` **no aparecieron eventos `SAFE_ABORT` ni `executor_failure` fechados el 27/10**. Sí se verificó la transición de cierre `SWITCH_COMMITTED=OK` a las 00:02:58. No se identificaron cambios RF manuales atribuibles en los registros estructurados inspeccionados. Estas constataciones se limitan a las fuentes examinadas; no equivalen a una auditoría exhaustiva de todos los accesos.

**Clasificación:** transición programada y confirmada = operación normal; `COLLECTION_ERROR`, fallos de sincronización y de respaldo = incidentes de adquisición/servicios; reinicios del watchdog y recuperación de backup = acciones automáticas; inspección actual = acción de lectura; acciones humanas RF = no evidenciadas.

## 7. Cierre 3×2 y decisiones metodológicas

El archivo local `3x2_cierre_2026-10-27/conciliation_3x2.json` identifica **42 días, 18 bloques, seis combinaciones**, **8064 pruebas nominales** y **7143 registradas** (**88.58 % de cobertura nominal**). Esta conciliación procede de un snapshot local de cierre y debe contrastarse con las exportaciones vivas antes de declarar el dataset definitivo.

Se adopta para el análisis: (1) **separar la línea base posterior del diseño factorial**; (2) preservar fallos y excepciones como evidencia QC, sin imputación; (3) distinguir error de consulta, caída del enlace y reinicio automático; (4) tratar matching temporal, plausibilidad instrumental y validez estadística como controles diferentes; (5) no atribuir causalidad a promedios entre días sin controlar bloque, condiciones meteorológicas y autocorrelación; (6) no cerrar la conciliación de F6655_B20 hasta resolver las 30 excepciones y las discrepancias retrospectivas; (7) mantener pendiente la comprobación de redundancia de los respaldos más recientes.

## 8. Procedencia y seguridad

Consultas de **solo lectura** desde Controlador a: `Data/exports/scientific_campaign_6g_integrated.csv`, `Data/exports/master_observations_multistation.csv`, `Data/exports/active_throughput_6g.csv`, `campaign_runtime/campaign_state.json`, `campaign_runtime/executor_state.json`, `campaign_runtime/campaign_events.jsonl`, `3x2_cierre_2026-10-27/conciliation_3x2.json`, `systemctl`, `journalctl` y `tailscale status`. Los recuentos representan el **estado de exportación al corte**, sujeto a conciliación posterior. No se incluyen credenciales, secretos, IP privadas, volcados de bases de datos ni datos brutos sensibles.

**Archivo documental:** `docs/DAILY_TRACE_2026-10-27_ATMOSLINK_3X2.md`, destinado a la rama predeterminada vigente `feature/atmoslink-ui-v2`. Crear como archivo nuevo, preservando el historial y sin sobrescribir evidencia anterior.
