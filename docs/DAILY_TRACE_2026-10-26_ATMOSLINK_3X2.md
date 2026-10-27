# AtmosLink 3×2 — Consolidación diaria de trazabilidad, 2026-10-26

**Campaña:** CU01 (AP Cuñacales) ↔ SJ01 (SM San José).  
**Ventana auditada:** 2026-10-26 00:00:00–23:59:59, America/Lima (UTC−05:00).  
**Inspección:** 2026-10-27, 00:47–00:49 (UTC−05:00), mediante consultas de solo lectura en Controlador.  
**Acceso SJ01:** Tailscale respondió (~4 ms); SSH directo a `rpi-sanjose64` fue denegado por la política del tailnet. No se eludió la restricción. Los datos SJ01 proceden de la sincronización registrada en Controlador.  
**Restricción:** no se modificaron RF, PoE, VLAN, servicios, timers ni bases de datos; tampoco se ejecutaron cambios sobre el equipo remoto. No se publican IP privadas, credenciales, secretos, dumps ni registros brutos sensibles.

> **Hallazgo de cierre:** la ventana experimental 3×2 de 42 días concluyó el **27/10/2026 a las 00:00 (-05:00)**. Se encontró un snapshot local de cierre ya existente con comprobación SQLite `quick_check=ok` y conciliación de 18 bloques. La transición posterior a la línea base `BASE_7000_20` se confirmó a las **00:02:58**. **El respaldo remoto dual del snapshot más reciente NO está verificado** y la validación histórica de matching F6655_B20 permanece abierta.

## 1. RF, escenario y transición

El **26/10** operó el escenario **F7000_B40, 7000 MHz / 40 MHz**, secuencia 18, confirmado el 25/10 a las 00:32:58 después de un intento fallido con rollback. El registro `campaign_events.jsonl` no contiene nuevas transiciones fechadas el 26/10 ni eventos `SAFE_ABORT`/`executor_failure` de ese día.

`scientific_campaign_6g_integrated.csv` registra **287 filas** del 26/10: **287/287 `LINK_OPERATIONAL_DUAL`**, **0 `COLLECTION_ERROR`**, **287/287 concordancia AP/SM** de frecuencia y ancho. Primera observación **00:04:40**, última **23:59:44**.

| Indicador RF, F7000_B40 | Resultado |
|---|---:|
| RSSI medio DL / UL | **−74.847 / −80.286 dBm** |
| SNR medio DL / UL | **22.582 / 19.143 dB** |
| Último RSSI DL / UL | −74 / −80 dBm |
| Último SNR DL / UL | 24 / 20 dB |
| Último MCS codificado DL / UL | 203 / 202 |
| Filas con RSSI o SNR igual a cero | 0 |

El **27/10**, después del cierre de la ventana 3×2, el ejecutor registró la transición **F7000_B40 → `BASE_7000_20` (7000 MHz / 20 MHz)**: `SWITCH_START` **00:00:01**, `TRIAL_APPLIED=OK` **00:00:02**, `TRIAL_CONFIRMED=OK` **00:02:40**, `SWITCH_COMMITTED=OK` **00:02:58**. Hubo sondas transitorias `WAITING` antes de recuperar diez comprobaciones consecutivas. `campaign_state.json` y `executor_state.json` confirman `BASE_7000_20`, secuencia `FINAL_BASELINE`. La última fila integrada global leída a las **00:29:49** ya registra 7000/20. **No mezclar esta línea base posterior con el tratamiento F7000_B40 del 26/10.**

## 2. Clima CU01/SJ01 — master_observations_multistation

**2285 filas** del 26/10: CU01 **1342**, SJ01 **943**.

| Indicador | CU01 | SJ01 |
|---|---:|---:|
| Temperatura media | 19.594 °C | 9.214 °C |
| Rango temperatura | 16.65–27.92 °C | 5.22–17.03 °C |
| Humedad relativa media | 61.130 % | 85.533 % |
| Presión media | 741.446 hPa | 665.516 hPa |
| Viento medio | 0.173 m/s | 1.326 m/s |
| Ráfaga máxima observada | 4.970 m/s | 12.233 m/s |
| `local_bme_ok=1` | 1342/1342 | 943/943 |
| Última observación | 23:59:26 | 23:58:34 |

La sincronización SJ01 concluyó con **`Status global: OK` a las 23:59:51**, con un registro recibido e insertado en el último lote. Hubo **13 fallos `timeout` de `atmoslink-remote-sync.service`** durante el día, seguidos de recuperaciones y sincronización final correcta. Las banderas `local_bme_ok` y el matching temporal no sustituyen validación instrumental.

## 3. Rendimiento — active_throughput_6g

**192 pruebas, 192 `OK`**, 96 DL y 96 UL, todas etiquetadas **7000 MHz / 40 MHz**. Primera prueba **00:00:04**, última **23:45:19**.

| Indicador | DL | UL |
|---|---:|---:|
| Goodput medio | **73.478 Mbps** | **44.740 Mbps** |
| Goodput mínimo–máximo | 21.207–90.059 Mbps | 9.568–66.331 Mbps |
| Retransmisiones TCP medias | 134.469 | 54.490 |
| Máximo de retransmisiones | **606** | **325** |
| RTT ICMP medio | 4.022 ms | 4.022 ms |
| Goodput cero con estado OK | 0 | 0 |

Pérdida ICMP media **0 %**. Se reporta goodput activo, no tasa física PHY. Las retransmisiones elevadas requieren análisis QC y sensibilidad; el estado `OK` no implica ausencia de degradación TCP.

## 4. Watermark científico y matching F6655_B20

Watermark de referencia: **`2026-09-15T23:36:42-05:00`**. Máximo del integrado observado durante la inspección: **`2026-10-27T00:29:49-05:00`**. **Avance temporal CONFIRMADO.**

Matching meteorológico del **26/10**: CU01 **280/287**, SJ01 **287/287**, dual **280/287 = 97.56 %**. Las **7 excepciones CU01=0 / SJ01=1** se registraron a las **01:14:54, 02:50:14, 05:30:52, 06:41:04, 08:16:28, 10:06:49 y 20:24:02**. No se imputaron ni alteraron.

Revisión retrospectiva **F6655_B20 posterior al watermark**: **1724 filas**, CU01 `matched=1` **1694/1724**, SJ01 `matched=1` **1724/1724**, matching dual **1694/1724 = 98.26 %**. Persisten **30 excepciones** distribuidas entre 16/09 (3), 07/10 (8), 08/10 (9), 17/10 (4) y 18/10 (6). Última fila F6655_B20: **2026-10-18T23:55:49-05:00**. El 26/10 no produjo filas nuevas F6655_B20. **La exigencia de que todas las nuevas filas F6655_B20 tengan `cu01_weather_matched=1` y `sj01_weather_matched=1` sigue SIN CONFIRMAR; no debe cerrarse por ausencia de filas nuevas.**

## 5. Servicios/timers, incidentes y recuperaciones

Al corte de inspección, `atmoslink-dashboard`, `atmoslink-scheduler`, `atmoslink-event-monitor`, `atmoslink-radio-config-6g` y `weather-logger` estaban **active/running**. Los servicios periódicos `andean-campaign`, `andean-throughput`, `atmoslink-throughput-6g`, `atmoslink-remote-sync`, `atmoslink-weather-watchdog` y `atmoslink-scientific-validation` estaban **inactive/success**, condición normal tras ejecutar. Sus timers, además de `atmoslink-remote-backup.timer` y `atmoslink-backup-recovery.timer`, figuraban programados. Los servicios de respaldo y recuperación estaban **failed/exit-code** al corte.

**Medición formal:** `andean-throughput.service` presentó **24 ejecuciones fallidas** el 26/10 por argumentos CLI incompatibles (`2/INVALIDARGUMENT`); no se confundieron con las 192 mediciones válidas del colector independiente `atmoslink-throughput-6g`.

**Meteorología local:** el watchdog registró **13 `RECUPERACIÓN AUTOMÁTICA`** de `weather-logger.service` por falta de nuevas mediciones durante aproximadamente 350–405 s en los eventos revisados; las recuperaciones mostraron posteriormente el servicio activo. Ejemplos: **07:11:53**, **08:18:58**, **10:10:44**, **11:03:36**, **11:17:49**, **12:12:43** y **20:26:25**. No atribuir causalidad directa a las siete excepciones de matching sin correlación temporal específica.

**Sincronización SJ01:** **13 timeouts** de `atmoslink-remote-sync.service` durante el 26/10; último lote exitoso **23:59:51**. La disponibilidad intermitente del servicio no equivale automáticamente a pérdida definitiva de datos.

**Validación científica:** `atmoslink-scientific-validation.service` finalizó **CU01: OK / SJ01: OK** a las **23:39:51**.

**Respaldo remoto:** `atmoslink-remote-backup.service` falló en su ejecución programada del 26/10 por cuota de Google Drive (`RATE_LIMIT_EXCEEDED`, `uploaded=False`, `verified=False`). El recuperador registró **44 ejecuciones fallidas** durante el 26/10 y **0 `RECOVERY COMPLETE 2/2`** en esa ventana. El **27/10 a las 00:29:03**, para la copia más reciente identificada (`backup_CU01_20261027_001149.zip`), **primary=verified**, pero **UNC=upload failed**, con copia local preservada. **No declarar respaldo dual completo ni recuperación de toda la cola histórica.**

## 6. Cierre científico local 3×2 — hallazgo posterior al cierre

Se inspeccionaron, **sin crearlos ni modificarlos**, los artefactos existentes de cierre local `3x2_cierre_2026-10-27`: manifiesto, conciliación, estado del ejecutor, eventos, cronograma y snapshot SQLite. El manifiesto informa una copia local creada entre **00:11:35 y 00:13:36** del 27/10, con tamaño **1 773 711 360 bytes**, SHA-256 **`2fdc7134b6a2b09da3c6370e36cd972a1759ed498eea1a2b04962186d41cccb7`** y `sqlite_quick_check=ok`. La autoría de esa creación no puede atribuirse con los registros consultados; **no fue una acción de esta inspección**. El manifiesto advierte que el respaldo remoto no está confirmado.

La conciliación existente informa **42 días (15/09–27/10), 18 bloques, seis combinaciones RF con tres exposiciones programadas por combinación**. En su definición de cobertura nominal: **8064 pruebas previstas**, **7143 registradas (88.58 %)**, **7070 `OK`** y **73 `ERROR`**; **81** con configuración desconocida, **34** discordancias de configuración, **4** discordancias posteriores a 45 minutos y **1** `OK` con incidencia QC. Estas categorías no se deben sumar como mutuamente excluyentes sin verificar la lógica de clasificación. El primer bloque F6655_B20 alcanzó **96/576 (16.67 %)**, y el segundo escenario del bloque inicial F7000_B40 **156/576 (27.08 %)**; esta cobertura desigual impide interpretar el 88.58 % global como uniformidad por tratamiento.

**Diferencia que requiere conciliación:** el manifiesto del snapshot SQLite informa como última fila de `scientific_campaign_6g_integrated` **2026-10-26T23:24:38-05:00**, mientras que el export CSV inspeccionado contiene filas del 26/10 hasta **23:59:44** y del 27/10 hasta **00:29:49**. El snapshot es consistente según SQLite, pero **no se ha demostrado que contenga todas las filas del export más reciente**. Verificar la procedencia/orden de actualización y congelar una versión analítica reproducible antes de la prueba de hipótesis; no modificar el snapshot ni las fuentes originales durante esta auditoría.

## 7. SAFE_ABORT, executor_failure, intervenciones y decisiones metodológicas

En el registro estructurado `campaign_events.jsonl` no se identificaron eventos fechados el **26/10**; por tanto, **no hay nuevos `SAFE_ABORT`, `executor_failure`, `SWITCH_FAILED` ni rollbacks registrados para ese día en esa fuente**. Sí se documentó la transición normal del 27/10 a `BASE_7000_20`. La ausencia en un archivo no constituye auditoría universal de todos los posibles eventos. No se identificaron modificaciones RF manuales atribuibles en las fuentes examinadas. Las recuperaciones de watchdog y sincronización fueron **acciones automáticas observadas**, no intervenciones humanas atribuibles. La generación del snapshot de cierre es una acción previa de autoría no determinada.

**Decisiones metodológicas:** preservar las siete excepciones meteorológicas del 26/10 y las treinta F6655_B20 sin imputación; distinguir operación RF, éxito de pruebas activas, calidad TCP, matching meteorológico y disponibilidad de servicios; separar la línea base posterior al cierre de los 18 bloques experimentales; no considerar intentos fallidos de transición como tratamientos confirmados; documentar las coberturas desiguales y controlar bloque, tiempo, autocorrelación y clima en el análisis inferencial; no atribuir causalidad por promedios diarios; reconciliar export y snapshot antes de fijar el dataset final. La campaña 3×2 **terminó según cronograma**, pero el **cierre científico definitivo sigue condicionado** a QC, matching, conciliación y respaldo verificado.

## 8. Fuentes y límites

Fuentes de solo lectura en Controlador: `Data/exports/scientific_campaign_6g_integrated.csv`, `Data/exports/master_observations_multistation.csv`, `Data/exports/active_throughput_6g.csv`, `campaign_runtime/campaign_state.json`, `campaign_runtime/executor_state.json`, `campaign_runtime/campaign_events.jsonl`, `systemctl`, `journalctl`, estado y ping Tailscale, y metadatos de `3x2_cierre_2026-10-27`. SSH directo a SJ01 denegado por política. Los conteos son los observados a las **00:47–00:49** del 27/10 y pueden variar si las exportaciones se regeneran. No se publican datos brutos, secretos ni direcciones privadas.

**Estado de documentación:** informe textual diario para la rama predeterminada vigente de `carloskoo1/AtmosLink-Research-Platform`, `feature/atmoslink-ui-v2`; archivo nuevo `docs/DAILY_TRACE_2026-10-26_ATMOSLINK_3X2.md`. La creación del archivo en GitHub es una operación documental separada de la inspección operativa read-only.
