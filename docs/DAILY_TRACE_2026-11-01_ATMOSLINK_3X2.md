# AtmosLink 3×2 — Consolidación diaria de trazabilidad: 2026-11-01

**Enlace:** CU01 (AP Cuñacales) ↔ SJ01 (SM San José).  
**Ventana auditada:** 2026-11-01 00:00:00–23:59:59, America/Lima (UTC−05:00).  
**Inspección de cierre:** 2026-11-02, aproximadamente 00:40–00:43 (-05:00), mediante Controlador.  
**Fase:** línea base posterior al factorial 3×2, reparación y piloto de la prospectiva de Luisita. **No es un bloque factorial ni una ventana prospectiva científica del 1/11.**  
**Alcance:** lectura exclusivamente de archivos, estados y journals operativos. No se modificaron RF, PoE, VLAN, servicios, timers ni bases de datos. El acceso SSH directo a SJ01 fue denegado por política del tailnet; se utilizó su telemetría sincronizada en Controlador. Se excluyen credenciales, tokens, IP/MAC, volcados y datos sensibles.

> **HALLAZGO PRINCIPAL:** durante el 1/11 se archivaron los intentos prospectivos fallidos del 30 y 31/10, se recuperó el controlador como **field_v3** y se verificó un piloto de seis configuraciones. A las **17:38:44** quedó habilitada una nueva campaña prospectiva, con inicio el **02/11 a las 00:00**. El evento posterior, **02/11 00:01:24**, confirmó la primera ventana **P01_S01 = 6655 MHz / 40 MHz**, con estado `MONITORING` a las 00:42. **La primera medición TCP científica, prevista a partir de las 00:45, aún no estaba comprobada al corte.** Estos hechos posteriores a medianoche se registran como transición crítica *interdiaria*, no como datos del 1/11.

## 1. RF, escenario, frecuencia y ancho

El estado persistente del **ejecutor factorial** permanece en `BASE_7000_20` (7000 MHz / 20 MHz), desde su `SWITCH_COMMITTED=OK` del **27/10 00:02:58**. No hay nuevas transiciones del ejecutor factorial en `campaign_events.jsonl` durante el 1/11. Los cambios RF del piloto prospectivo son intervenciones administrativas distintas, documentadas en §5.

`scientific_campaign_6g_integrated.csv` contiene **287 filas** fechadas el 1/11: **287/287 `LINK_OPERATIONAL_DUAL`**, **0 `COLLECTION_ERROR`**. Última fila **2026-11-01T23:49:51-05:00**; modificación del export **23:53:19**. No se debe inferir completitud de la medianoche ni disponibilidad RF continua a partir del estado categórico.

Configuración informada por AP: **284 filas 7000/20**, **2 filas 6655/40** y **1 fila 6655/20**. Hubo **dos discordancias transitorias AP/SM**: **17:33:42** (AP 6655/20; SM 7000/20) y **17:37:54** (AP 7000/20; SM 6475/20). No hubo métricas RSSI/SNR iguales a cero en las 287 filas. Las discordancias ocurrieron en la ventana de piloto y deben etiquetarse **QC/transición**, no como tratamientos RF estables.

Para las **283 filas 7000/20 con concordancia AP/SM y estado operativo**, los promedios descriptivos fueron RSSI DL **−75.473 dBm**, RSSI UL **−81.014 dBm**, SNR DL **22.011 dB** y SNR UL **17.516 dB**. Excluyen el piloto y las dos discordancias; no equivalen a estimaciones inferenciales de la campaña factorial.

## 2. Meteorología CU01/SJ01 — master_observations_multistation

`master_observations_multistation.csv` contiene **2321 filas del 1/11**: **CU01 1367** y **SJ01 954**.

| Indicador (media de registros disponibles) | CU01 | SJ01 |
|---|---:|---:|
| Temperatura | 19.408 °C | 9.105 °C |
| Humedad relativa | 66.356 % | 95.907 % |
| Presión | 740.379 hPa | 664.392 hPa |
| Viento | 0.204 m/s | 1.387 m/s |
| Última observación local | 23:59:03 | 23:59:53 |

La última sincronización SJ01 del 1/11 concluyó a las **23:58:01** con `Status global: OK`, `recibidos=2, insertados=2, ignorados=0`. El archivo maestro estaba actualizado hasta el **02/11 00:34:03** al inspeccionarse. Tailscale respondió a `rpi-sanjose64` (≈4 ms), pero SSH directo fue denegado por política. **No se accedió al journal local de SJ01**; sus indicadores son de la copia sincronizada, no de una auditoría directa del nodo.

## 3. Matching meteorológico y watermark

En las **287 filas integradas del 1/11**: `cu01_weather_matched=1` en **278/287**, `sj01_weather_matched=1` en **286/287** y matching dual en **278/287 = 96.86 %**. Nueve excepciones: CU01=0/SJ01=1 a las **00:09:48, 03:40:31, 05:35:55, 07:21:18, 09:16:45, 11:17:07, 13:27:42 y 13:42:45**, y CU01=0/SJ01=0 a las **23:49:51**. Horas UTC−05:00. No imputar ni reescribir originales.

**Watermark exigido:** `2026-09-15T23:36:42-05:00`. **Máximo global integrado:** `2026-11-01T23:49:51-05:00`. **Avance temporal CONFIRMADO**, pero el matching y la completitud de la jornada no están totalmente cerrados.

**F6655_B20 después del watermark:** **1725 filas**, CU01 matched **1695/1725**, SJ01 matched **1725/1725**, dual **1695/1725 = 98.26 %**; persisten **30 excepciones históricas** (16/09: 3; 07/10: 8; 08/10: 9; 17/10: 4; 18/10: 6). **Nueva fila del 1/11 a las 17:33:42:** `cu01_weather_matched=1` y `sj01_weather_matched=1`, **ambas condiciones verificadas para esta fila**. Sin embargo, presenta discordancia RF AP 6655/20 vs. SM 7000/20 durante el piloto, por lo que **no es una exposición F6655_B20 válida**. La condición de matching para nuevas filas observadas se satisface en esta única fila, pero **no se cierra la auditoría histórica ni se certifica calidad RF de todas las filas**. Continuar verificando cada nueva fila.

## 4. active_throughput_6g

`active_throughput_6g.csv` registra **4 pruebas del 1/11, 4/4 `OK`**, todas del **piloto de recuperación** `LUISITA_SERVICE_PILOT_20261101_LIVE` y **excluidas del factorial y de la prospectiva científica**.

| Inicio local | RF | Dirección | Goodput medido |
|---|---|---|---:|
| 17:30:26 | 6655 MHz / 40 MHz | DL | 64.381 Mbps |
| 17:30:42 | 6655 MHz / 40 MHz | UL | 21.627 Mbps |
| 17:37:59 | 7000 MHz / 20 MHz | DL | 21.565 Mbps |
| 17:38:15 | 7000 MHz / 20 MHz | UL | 14.418 Mbps |

El informe de recuperación registra ruta verificada, pruebas TCP de 8 s, omisión de 1 s y un flujo; las diferencias meteorológicas SJ01 de las cuatro pruebas fueron **94, 110, 67 y 83 segundos**, respectivamente. Se conserva la trazabilidad RF viva por test/dirección en el sistema prospectivo. No comparar estos cuatro valores como efecto causal de la frecuencia/ancho: son pruebas de aceptación y no réplicas independientes.

Los timers factoriales `andean-campaign.timer`, `andean-throughput.timer` y `atmoslink-throughput-6g.timer` permanecían **disabled**. La ausencia de serie throughput regular del 1/11 es **ausencia por diseño operativo**, no un conjunto de fallos de medición.

## 5. Recuperación, transiciones y acciones humanas observadas

**Antes de la reparación:** los intentos prospectivos del **30/10** y **31/10** habían quedado `HALTED`, sin pruebas TCP prospectivas científicas. El journal del 1/11 registra **1048 líneas `Failed with result`** de `luisita-prospective.service`, reflejo de reintentos/ejecuciones fallidas del controlador heredado; **no equivalen a 1048 incidentes independientes**.

**Durante el 1/11:** la documentación administrativa `prospective_28d/recovery_20261101/RECOVERY.md` acredita intervención **previa a esta inspección**, recuperación como **field_v3**, 32 pruebas unitarias en Python normal y 32 en modo optimizado, 12 ciclos de autenticación/lectura/cierre de sesión verificado, comprobaciones de prearranque y piloto desde la unidad systemd instalada. Se documentó un piloto previo fallido por lectura atrasada del dashboard SM; el controlador revisado contrasta la asociación RF viva y conserva la procedencia del dashboard. **No atribuir la intervención humana a la inspección read-only.**

**17:30–17:38:** piloto de seis configuraciones, con diez verificaciones consecutivas antes y después de la confirmación: **6655/40, 7000/40, 6655/20, 6475/40, 6475/20 y 7000/20**. Se confirmó retorno a referencia 7000/20 a las **17:38:28**. Las dos discordancias del export RF son observaciones transitorias de ese proceso, no evidencia de que el piloto global haya fallado.

**17:38:44:** evento `SESSION_RECOVERY_HANDOVER` y habilitación de `LUISITA_PROSPECTIVE_28D_20261102` (release `field_v3`), con calendario **02/11 00:00 → 30/11 00:00**. Se archivaron los intentos anteriores. El plan conserva **42 exposiciones de 12 horas y siete reservas de 24 horas**. **El 1/11 no debe contarse como jornada prospectiva válida.**

**Transición interdiaria crítica, posterior a la ventana auditada:** el **02/11 00:00:02** se registró `WINDOW_INTENT` para `P01_S01` (6655/40); `TRIAL_ACK` a las **00:00:04**, `CONFIRM_ACK` a las **00:00:56** y **`WINDOW_VERIFIED` a las 00:01:24** tras diez comprobaciones consecutivas. Hubo probes transitorios con timeout SSH y asociación ambigua durante la transición, seguidos de confirmación. A las **00:42** `STATUS.json` informa `MONITORING`. **No consta aún, al corte, la primera prueba TCP científica de las 00:45 ni el cierre de la ventana P01_S01**. Su verificación corresponde a la siguiente consolidación.

## 6. Servicios, timers e incidentes auxiliares

Al corte, `atmoslink-dashboard`, `atmoslink-scheduler`, `atmoslink-event-monitor`, `atmoslink-radio-config-6g` y `weather-logger` estaban **active/running**. `luisita-prospective.service` estaba **inactive/success**, normal entre ejecuciones del timer; `luisita-prospective.timer` **enabled/active**. Servicios periódicos de sincronización, watchdog, validación y recuperador estaban **inactive/success**; sus timers habilitados. `atmoslink-remote-backup.service` estaba **failed/exit-code**, con timer habilitado. Los tres timers factoriales/throughput citados permanecían deshabilitados.

**Sincronización SJ01:** el journal registra **16 eventos de fallo de unidad** durante el 1/11, aunque también **708 líneas `Status global: OK`**; la última sincronización fue satisfactoria a las **23:58:01**. Son contadores de logs, no necesariamente eventos independientes o ausencia de datos.

**Watchdog CU01:** **10 recuperaciones automáticas** de `weather-logger.service`, a las **00:13:00, 03:42:27, 05:38:18, 06:00:39, 07:23:59, 09:19:53, 11:21:49, 13:29:52, 13:44:02 y 15:48:02**. Cada recuperación informó posterior estado `active`. **Ocho** de las nueve excepciones meteorológicas del integrado precedieron a una recuperación entre aproximadamente **1 y 5 minutos**. Esto es una **asociación temporal**, no una demostración causal. La excepción de las 23:49:51 requiere conciliación con el maestro meteorológico más reciente.

**Validación científica:** **24 ejecuciones horarias**, todas con `CU01: OK` y `SJ01: OK`; última a las **23:51:15**. No sustituyen las verificaciones de matching.

**Respaldo programado:** fallo a las **02:45:42** por cuota de Google Drive, `uploaded=False`, `verified=False`. **Recuperador:** **21 eventos de fallo de unidad** y **23 líneas `RECOVERY COMPLETE 2/2`** en el journal del día (conteos de ejecuciones, no de respaldos distintos). Se verificó la copia generada a las **18:45:03** en ambos destinos a las **23:30:51**; una nueva ejecución comenzó a las **23:59:29**. La verificación de esa copia **no acredita toda la cola histórica ni las observaciones posteriores a su generación**.

## 7. SAFE_ABORT, executor_failure y clasificación de incidentes

En `campaign_runtime/campaign_events.jsonl`, el último evento factorial sigue siendo `SWITCH_COMMITTED=OK` del **27/10 00:02:58**. No hay eventos factoriales nuevos `SAFE_ABORT`, `executor_failure`, `SWITCH_FAILED` ni rollback del 1/11 en esa fuente. **Sí** se documentaron errores del controlador prospectivo heredado, un piloto de recuperación inicialmente fallido, recuperaciones del logger, fallos de sincronización y respaldo, y la transición interdiaria posterior. La ausencia de eventos del ejecutor factorial **no implica ausencia de incidentes operativos**.

**Decisiones metodológicas:** separar factorial cerrado, línea base posterior, piloto de aceptación y nueva prospectiva; conservar sin imputación las nueve excepciones meteorológicas, las treinta históricas F6655_B20 y las dos discordancias AP/SM; no inferir causalidad entre watchdog y matching; no atribuir pruebas del piloto a tratamientos; no declarar exposición prospectiva científicamente validada antes de confirmar el primer TCP y la elegibilidad del segmento. Mantener timestamps locales y procedencia por fuente.

## 8. Procedencia, limitaciones y trazabilidad

Fuentes de Controlador consultadas **sin escritura**: `Data/exports/scientific_campaign_6g_integrated.csv` (mod. 01/11 23:53:19), `Data/exports/master_observations_multistation.csv` (mod. 02/11 00:36:40), `Data/exports/active_throughput_6g.csv` (mod. 01/11 17:38:27); `campaign_runtime/campaign_state.json`, `campaign_events.jsonl`; `prospective_runtime/ENABLED.json`, `state.json`, `STATUS.json`, `events.jsonl`; `prospective_28d/recovery_20261101/RECOVERY.md`, `HEALTH.json`, `service_pilot/PASSED.json`; `systemctl`, `journalctl`, `tailscale ping` y prueba SSH rechazada. Las observaciones RF del piloto pueden contener telemetría atrasada en el dashboard SM; la evidencia de asociación viva se conserva en el runtime científico prospectivo.

**Referencia anterior:** [Informe del 31/10, incidente `MISSED_WINDOW_HALT`](DAILY_TRACE_2026-10-31_ATMOSLINK_3X2.md). Este informe registra su recuperación, el nuevo release y el inicio verificado del 02/11, **sin reinterpretar los intentos fallidos como exposiciones válidas**.

**Estado documental:** archivo nuevo exclusivamente textual, sin sobrescribir informes previos. No se publican secretos, credenciales, datos personales, IP/MAC, volcados de bases de datos ni telemetría cruda.
