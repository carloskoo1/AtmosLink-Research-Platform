# AtmosLink 3×2 — Consolidación diaria de trazabilidad: 2026-10-29

**Enlace:** CU01 (AP Cuñacales) ↔ SJ01 (SM San José).  
**Ventana:** 2026-10-29 00:00:00–23:59:59, America/Lima (UTC−05:00).  
**Corte efectivo de inspección:** 2026-10-29T23:55:07-05:00. **Informe provisional de fin de día:** no incluye adquisiciones ni reexportaciones posteriores al corte.  
**Modalidad:** lectura exclusivamente desde Controlador (systemd/journald, CSV, JSON de estado y Tailscale). `rpi-sanjose64` respondió a Tailscale (~4 ms), pero el SSH directo fue denegado por la política del tailnet; no se eludió. La evidencia SJ01 procede de los registros sincronizados en Controlador. **No se modificaron RF, PoE, VLAN, servicios, timers ni bases de datos.**

> **Separación científica:** el factorial AtmosLink 3×2 finalizó el 2026-10-27 a las 00:00 (-05:00). El 29/10 corresponde a **línea base posterior**, no a un bloque experimental factorial. El CSV integrado conserva el valor genérico `deployment_phase=FIELD_OPERATION`; para delimitar tratamientos debe prevalecer el estado del ejecutor y la cronología de transiciones, no esa etiqueta genérica.

## 1. Escenario, RF y transiciones

`campaign_state.json`: `active_scenario=BASE_7000_20`, **7000 MHz / 20 MHz**, fase `BASELINE`, bloque 0. `executor_state.json`: `sequence=FINAL_BASELINE`; aplicado el **2026-10-27T00:00:00-05:00**. Último `SWITCH_COMMITTED=OK`: **2026-10-27T00:02:58-05:00** (F7000_B40 → BASE_7000_20). No hubo nuevas transiciones del 29/10 en el registro de eventos ni en el diario del ejecutor: los ciclos informaron «Sin transición: BASE_7000_20 ya fue aplicado».

`scientific_campaign_6g_integrated.csv`, filtrado por `rf_timestamp_local` del 29/10:

| Indicador | Valor al corte |
|---|---:|
| Observaciones RF | **283** |
| `LINK_OPERATIONAL_DUAL` | **283/283** |
| `COLLECTION_ERROR` | **0** |
| Frecuencia/ancho AP y SM | **7000 MHz / 20 MHz**, concordancia 283/283 |
| RSSI medio DL / UL | **−75.095 / −81.095 dBm** |
| SNR medio DL / UL | **22.198 / 17.558 dB** |
| Primera / última observación | **00:00:45 / 23:35:37** |
| Último RSSI DL/UL | −75 / −81 dBm |
| Último SNR DL/UL | 22 / 17 dB |
| Último MCS nominal DL/UL | 203 / 202 |
| `field_analysis_valid=1` | 283/283 |

El export RF tenía modificación a las **23:37:34**. Al corte, la última observación era 23:35:37: **no declarar cierre definitivo de medianoche**. El campo `rate_metric_type=CAMBIUM_REPORTED_LINK_RATE_NOT_ACTIVE_THROUGHPUT` indica que la tasa reportada por el radio no debe confundirse con goodput activo.

**Matching meteorológico del día:** CU01 **277/283**, SJ01 **282/283**, dual **276/283 (97.53 %)**. Siete excepciones, conservadas sin imputación:

| Hora local (-05:00) | CU01 matched | SJ01 matched |
|---|---:|---:|
| 01:56:08 | 0 | 1 |
| 03:16:24 | 0 | 1 |
| 08:42:40 | 0 | 1 |
| 09:47:56 | 0 | 1 |
| 17:24:23 | 0 | 1 |
| 21:25:11 | 0 | 1 |
| 23:35:37 | 1 | 0 |

Las primeras seis excepciones son de CU01; la última es de SJ01. No atribuir automáticamente la excepción SJ01 a una caída del enlace.

## 2. Meteorología CU01/SJ01 — master_observations_multistation

**2284 registros** disponibles al corte: **CU01 1358** y **SJ01 926**.

| Indicador | CU01 | SJ01 |
|---|---:|---:|
| Temperatura media | **19.120 °C** | **8.769 °C** |
| Humedad relativa media | **66.477 %** | **94.482 %** |
| Presión media | **741.206 hPa** | **664.915 hPa** |
| Viento medio | **0.169 m/s** | **1.118 m/s** |
| Ráfaga media | 0.450 m/s | 1.607 m/s |
| Última observación al corte | **23:48:32** | **23:48:43** |
| `local_bme_ok=1` | 1358/1358 | 926/926 |

Última modificación del export meteorológico: **23:51:13**. La sincronización remota registró `Status global: OK` a las **23:52:52**. Los flags de adquisición y el matching temporal no acreditan por sí solos calibración ni validez metrológica.

## 3. Rendimiento — active_throughput_6g

**192 pruebas, 192 `OK`**, con **96 DL y 96 UL**; primera prueba 00:00:04, última 23:45:20. Última modificación del export: **23:45:32**.

| Métrica sobre pruebas OK | DL | UL |
|---|---:|---:|
| Goodput medio medido | **51.399 Mbps** | **30.796 Mbps** |
| Retransmisiones TCP medias | **45.521** | **34.417** |
| Máximo de retransmisiones | 177 | 185 |
| Pruebas con goodput cero | 0 | 0 |
| Pruebas sin frecuencia/ancho | 0 | 0 |

RTT ICMP medio por dirección: **4.654 ms**. Pérdida ICMP media: **0 %**. Son mediciones de goodput activo, no de tasa PHY. No usar estos promedios posteriores al factorial para estimar efectos causales de frecuencia/ancho sin un diseño específico.

## 4. Watermark y requisito pendiente F6655_B20

**Watermark requerido:** `2026-09-15T23:36:42-05:00`.  
**Última fila global integrada al corte:** `2026-10-29T23:35:37-05:00`.  
**Avance temporal del integrado: CONFIRMADO.**

Revisión retrospectiva de **F6655_B20** (6655 MHz / 20 MHz) posterior al watermark:

| Control | Resultado |
|---|---:|
| Filas | **1724** |
| `cu01_weather_matched=1` | **1694/1724** |
| `sj01_weather_matched=1` | **1724/1724** |
| Ambos flags en 1 | **1694/1724 (98.26 %)** |
| Excepciones duales | **30** |
| Última fila F6655_B20 | `2026-10-18T23:55:49-05:00` |

Excepciones por fecha: 16/09 (3), 07/10 (8), 08/10 (9), 17/10 (4) y 18/10 (6). **No hay nuevas filas F6655_B20 el 29/10**, porque el sistema estaba en BASE_7000_20. **El requisito de matching dual del 100 % permanece NO CONFIRMADO**: la ausencia de filas nuevas no constituye una validación positiva. Mantener revisión de las 30 excepciones y vigilancia si vuelve a generarse F6655_B20; no alterar las fuentes.

## 5. Servicios, timers, incidentes y recuperaciones

**Servicios al corte:** `atmoslink-dashboard`, `atmoslink-scheduler`, `atmoslink-event-monitor`, `atmoslink-radio-config-6g` y `weather-logger` en `active/running`. Los servicios periódicos `andean-campaign`, `andean-throughput`, `atmoslink-throughput-6g`, `atmoslink-remote-sync`, `atmoslink-weather-watchdog` y `atmoslink-scientific-validation` en `inactive/success`, normal entre ejecuciones. **`atmoslink-remote-backup.service` y `atmoslink-backup-recovery.service` en `failed/exit-code`**. Se verificaron timers programados para `andean-campaign`, `andean-throughput`, `atmoslink-throughput-6g`, `atmoslink-remote-sync`, `atmoslink-weather-watchdog`, `atmoslink-scientific-validation`, `atmoslink-remote-backup` y `atmoslink-backup-recovery`.

**Medición formal:** `andean-throughput.service` terminó correctamente **24 veces**, con el aviso «Sin medición formal: fuera de fase EXPERIMENT» (00:05–23:05). Esto es coherente con la línea base y no demuestra reparación retrospectiva de fallos durante el factorial. El colector independiente produjo 192 pruebas válidas.

**Sincronización SJ01:** `atmoslink-remote-sync.service` registró **9 fallos por timeout**, el último a las **23:49:45**, y **705 mensajes `Status global: OK`**, el último a las **23:52:52**. Un timeout del sincronizador no acredita una interrupción física del radioenlace.

**Watchdog CU01:** se documentaron **11 recuperaciones automáticas** de `weather-logger.service`, todas con confirmación posterior `weather-logger.service=active`. Horas de inicio: **00:44:41, 01:00:56, 02:01:55, 03:17:06, 06:58:39, 08:17:56, 08:44:20, 09:49:24, 17:28:41, 17:40:55 y 21:28:31**. Las confirmaciones siguieron aproximadamente 5 s después. Son acciones automáticas, **no humanas**.

**Hallazgo QC:** las **6/6 excepciones CU01** del día antecedieron a una recuperación del watchdog dentro de aproximadamente **42 s a 5 min 47 s**. Existe asociación temporal compatible con pérdida de frescura meteorológica, **sin evidencia causal concluyente**. La excepción SJ01 de las 23:35:37 debe auditarse separadamente.

**Validación científica:** 24 ejecuciones horarias con `CU01: OK` y `SJ01: OK`, última a las **23:45:22**. Este estado no elimina las siete excepciones de matching.

**Respaldo remoto:** `atmoslink-remote-backup.service` falló a las **02:42:07** por cuota de Google Drive (`RATE_LIMIT_EXCEEDED`, `uploaded=False`, `verified=False`). El recuperador registró **29 eventos `RECOVERY COMPLETE 2/2`** y **15 ejecuciones fallidas** el 29/10; los eventos exitosos pueden repetir la verificación de la misma copia y no representan 29 respaldos distintos. La última confirmación dual encontrada fue a las **18:10:47**, para `backup_CU01_20261029_122724.zip`. Existe localmente una copia posterior `backup_CU01_20261029_182837.zip`, pero **no quedó confirmada su verificación dual** al corte. La última ejecución fallida del recuperador fue a las **23:34:59** por timeout de consulta remota. **No declarar recuperada la copia más reciente ni toda la cola histórica.** No se realizaron reintentos manuales.

## 6. SAFE_ABORT, executor_failure, acciones humanas y metodología

`campaign_events.jsonl` tiene su última modificación el **27/10 a las 00:02:58**. No contiene eventos fechados el 29/10: **no se observaron nuevos `SAFE_ABORT`, `executor_failure`, `SWITCH_FAILED`, rollbacks ni transiciones** en esa fuente. El diario de `andean-campaign.service` tampoco mostró cambios de escenario. No se identificaron intervenciones humanas RF atribuibles. Estas constataciones se limitan a las fuentes inspeccionadas, no son auditoría exhaustiva de todos los accesos.

**Clasificación y decisiones metodológicas observables:** operación normal = RF dual estable, pruebas activas y validación horaria; incidentes = timeouts de sincronización, fallos de respaldo y excepciones de matching; recuperaciones = watchdog y verificaciones automáticas de copias; acciones humanas = solo inspección de lectura, sin cambios operativos. Conservar las siete excepciones del día y las 30 históricas F6655_B20 sin imputación; separar BASELINE del factorial; investigar la asociación con watchdog sin atribución causal; distinguir estado de servicio, disponibilidad RF, matching temporal y validez instrumental; evitar pseudorreplicación y confusión entre tasa PHY y goodput.

## 7. Procedencia, límites y publicación

Fuentes leídas en Controlador: `Data/exports/scientific_campaign_6g_integrated.csv`, `Data/exports/master_observations_multistation.csv`, `Data/exports/active_throughput_6g.csv`, `campaign_runtime/campaign_state.json`, `campaign_runtime/executor_state.json`, `campaign_runtime/campaign_events.jsonl`, `systemctl`, `journalctl`, `tailscale ping/status` y un intento SSH directo denegado por política. No se publican direcciones IP, credenciales, secretos, volcados de bases de datos, datos personales ni registros brutos sensibles. Los recuentos corresponden a exportaciones al corte y podrían variar con conciliación/reexportación posterior.

**Archivo nuevo:** `docs/DAILY_TRACE_2026-10-29_ATMOSLINK_3X2.md` en la rama predeterminada verificada `feature/atmoslink-ui-v2`. La ruta se verificó ausente antes de crearla. Esta operación incorpora solo documentación textual, preservando la evidencia anterior.
