# AtmosLink 3×2 — Consolidación diaria de trazabilidad, 2026-10-23

**Campaña:** AtmosLink 3×2 (CU01/AP y SJ01/SM).  
**Ventana:** 2026-10-23T00:00:00-05:00 a 2026-10-23T23:59:59-05:00 (America/Lima).  
**Inspección:** 2026-10-24, aproximadamente 00:20–00:26 -05:00.  
**Alcance:** solo lectura sobre Controlador; datos SJ01 sincronizados en Controlador. Tailscale respondió desde `rpi-sanjose64` (ping ≈10 ms), pero SSH directo fue denegado explícitamente por la política del tailnet. No se eludió la restricción.  
**Integridad operativa:** la inspección no cambió RF, PoE, VLAN, servicios, timers ni bases de datos. Los reinicios automáticos consignados más abajo **son acciones preexistentes del watchdog**, no acciones del auditor.  
**Estado del informe:** **cierre operativo con export RF incompleto hasta medianoche**; los recuentos corresponden a la instantánea leída y pueden variar por conciliación posterior.

## 1. Escenario, RF y transición

Escenario confirmado **F6475_B20**, **6475 MHz / 20 MHz**, secuencia persistente **17**. El 23/10 se realizó la transición programada desde el escenario previo **F7000_B20 (7000 MHz / 20 MHz)**:

| Evento | Hora local (23/10, UTC−05) | Resultado |
|---|---|---|
| SWITCH_START | 00:00:00.882 | STARTED |
| TRIAL_APPLIED | 00:00:01.791 | OK |
| TRIAL_CONFIRMED | 00:02:40.052 | OK |
| SWITCH_COMMITTED | **00:02:58.489** | **OK** |

La aplicación contempló rollback automático de 300 s, pero **no se observó rollback ni SWITCH_FAILED** en esta transición. Se registraron comprobaciones de conectividad WAITING durante el establecimiento, seguidas de comprobaciones OK y commit. El estado persistente del ejecutor confirma F6475_B20. No confundir la interrupción de transición con una caída sostenida del enlace.

**`scientific_campaign_6g_integrated.csv`**, instantánea con modificación **2026-10-23T23:26:44-05:00**:

| Indicador RF | Valor |
|---|---:|
| Filas del 23/10 | **280** |
| LINK_OPERATIONAL_DUAL | **280/280** |
| COLLECTION_ERROR | **0** |
| Frecuencia/ancho reportados | **6475 MHz / 20 MHz (280/280)** |
| Concordancia AP/SM | **280/280** |
| Primera / última fila | **00:03:16 / 23:23:06** |
| RSSI medio DL/UL (dBm) | **−78.075 / −83.611** |
| SNR medio DL/UL (dB) | **21.582 / 17.846** |
| Último RSSI DL/UL (dBm) | −79 / −84 |
| Último SNR DL/UL (dB) | 21 / 17 |
| Último MCS codificado DL/UL | 203 / 202 |

**Frescura pendiente:** la última fila RF del día era de las 23:23:06; a la inspección (~00:20 del 24/10) aún no constaba el tramo final hasta 23:59. No extrapolar 280 observaciones a un cierre íntegro ni atribuir automáticamente el desfase a indisponibilidad física.

**Matching meteorológico RF del 23/10:** CU01 **264/280 (94.29 %)**, SJ01 **279/280 (99.64 %)**, ambos **264/280 (94.29 %)**. Hay **16 excepciones** (15 con CU01=0/SJ01=1 y una con CU01=0/SJ01=0). Horas locales: 07:24:39, 11:50:44, 13:46:05, 14:16:10, 14:31:13, 14:51:22, 16:46:44, 19:12:18, 19:42:24, 19:57:26, 20:32:32, 20:42:37, 21:37:47, 22:12:53, 22:17:54 y 23:23:06. Conservar todas sin imputación automática.

## 2. Meteorología CU01/SJ01

**`master_observations_multistation.csv`: 2238 filas** del 23/10, CU01 **1298**, SJ01 **940**.

| Métrica | CU01 | SJ01 |
|---|---:|---:|
| Temperatura media | 19.232 °C | 8.849 °C |
| Temperatura mín.–máx. | 16.53–26.41 °C | 6.88–17.80 °C |
| Humedad relativa media | 66.537 % | 95.145 % |
| Presión media | 741.266 hPa | 665.102 hPa |
| Viento medio | 0.282 m/s | 3.431 m/s |
| Ráfaga media | 0.669 m/s | 4.457 m/s |
| Último registro | 23:59:52 | 23:59:24 |
| Última temperatura | 17.02 °C | 7.26 °C |
| Última humedad relativa | 72.37 % | 100 % |
| Última presión | 742.85 hPa | 666.31 hPa |

El sincronizador remoto seguía informando **Status global: OK** en ejecuciones posteriores a medianoche. La accesibilidad de SJ01 fue verificada por Tailscale; la inspección directa de procesos en la Raspberry **no** fue posible por política SSH. No aplicar a SJ01 los umbrales de presión de CU01 por su diferente altitud.

## 3. Rendimiento activo

**`active_throughput_6g.csv`: 192 pruebas** del 23/10, **190 OK** (95 DL + 95 UL), **2 ERROR** (00:00:05 DL y 00:00:31 UL), ambas durante la transición y todavía etiquetadas 7000/20. No contabilizarlas como exposición estable a F6475_B20.

| Métrica (pruebas OK) | DL | UL |
|---|---:|---:|
| Pruebas OK | 95 | 95 |
| Goodput medio | **38.738 Mbps** | **19.820 Mbps** |
| Goodput máximo | 56.125 Mbps | 29.225 Mbps |
| Retransmisiones TCP medias | 42.716 | 24.316 |
| Retransmisiones TCP máximas | 243 | 94 |
| RTT ICMP medio | 5.420 ms | 5.420 ms |
| Pérdida ICMP media | 0 % | 0 % |

**QC adicional:** una prueba UL marcada OK carece de metadatos de frecuencia/ancho en el CSV; no asignarla a un tratamiento específico sin cotejo de procedencia. Goodput medido no equivale a tasa PHY; los promedios no identifican por sí solos un efecto causal de frecuencia/ancho.

## 4. Watermark y requisito pendiente F6655_B20

**Watermark de referencia:** `2026-09-15T23:36:42-05:00`.  
**Máximo `rf_timestamp_local` observado en el integrado:** `2026-10-23T23:23:06-05:00`.  
**Validación de avance temporal:** **CONFIRMADA**. **Validación de cierre completo del 23/10:** **PENDIENTE**.

En las filas F6655_B20 **posteriores** al watermark, el export actual contiene **1724 observaciones** (desde 2026-09-15T23:41:43-05:00 hasta 2026-10-18T23:55:49-05:00):

| Requisito | Resultado |
|---|---:|
| `cu01_weather_matched=1` | **1694/1724** |
| `sj01_weather_matched=1` | **1724/1724** |
| Ambos =1 | **1694/1724 (98.26 %)** |
| Excepciones duales | **30** |

Distribución de excepciones: 16/09 (3), 07/10 (8), 08/10 (9), 17/10 (4), 18/10 (6). El 23/10 no se añadieron filas F6655_B20 porque el tratamiento activo fue F6475_B20. **El requisito de matching dual al 100 % continúa NO CONFIRMADO.** Mantener vigilancia de futuras filas F6655_B20 y reconciliar versiones retrospectivas; no imputar ni reescribir registros originales.

## 5. Servicios y timers críticos

En el corte del 24/10 estaban **active/running**: `atmoslink-dashboard`, `atmoslink-scheduler`, `atmoslink-event-monitor`, `atmoslink-radio-config-6g`. Los servicios periódicos `atmoslink-throughput-6g`, `atmoslink-remote-sync`, `atmoslink-scientific-validation`, `andean-campaign` y `atmoslink-weather-watchdog` estaban **inactive/dead con Result=success** (normal entre ejecuciones). Los timers `andean-campaign`, `andean-throughput`, `atmoslink-throughput-6g`, `atmoslink-remote-sync`, `atmoslink-weather-watchdog`, `atmoslink-scientific-validation`, `atmoslink-remote-backup` y `atmoslink-backup-recovery` estaban programados.

**Incidente I1 — servicio formal de throughput:** `andean-throughput.service` registró **24 fallos** del 23/10, entre **00:05 y 23:05**, por argumentos CLI incompatibles (`2/INVALIDARGUMENT`). El colector independiente de throughput sí produjo las 190 pruebas OK. No se corrigió ni reinició manualmente el servicio.

**Incidente I2 — backup remoto:** `atmoslink-remote-backup.service` falló el **23/10 a las 02:44:06** por `RATE_LIMIT_EXCEEDED` (`uploaded=False`, `verified=False`). El recuperador verificó **2/2 destinos** para una copia de **11:50:02** (última confirmación de ese respaldo a las **17:23:51**). Para una copia posterior de **17:51:30**, se verificó el destino principal, pero la subida al destino UNC siguió fallando (observado hasta **23:21:58**). La copia local más reciente, de **23:52:23**, tampoco pudo subirse al principal a las **23:55:10** y quedó preservada localmente. En la inspección `atmoslink-remote-backup.service` y `atmoslink-backup-recovery.service` constaban **failed**. **No declarar recuperación 2/2 del respaldo más reciente.**

**Incidente I3 — intermitencia de logger meteorológico:** el watchdog registró **22 recuperaciones automáticas** del servicio `weather-logger.service` el 23/10, desde **02:58:14** hasta **23:27:51**; las 22 informaron posterior estado `active`. Se registraron además **5 eventos de espera por cooldown**. El mayor intervalo sin mediciones señalado fue **924 s** a las **22:22:49**. Es una incidencia de continuidad de adquisición meteorológica que debe analizarse junto con las 16 excepciones de matching, **sin asumir causalidad automática**. Estos reinicios fueron ejecutados por el watchdog operativo, **no por la inspección**.

**Sincronización y validación:** `atmoslink-remote-sync` registró `Status global: OK` tras el cierre; `atmoslink-scientific-validation` concluyó el **23/10 a las 23:32:09** con **CU01: OK** y **SJ01: OK**. Un resultado de validación de estación OK no sustituye la comprobación de matching RF por fila.

## 6. SAFE_ABORT, executor_failure y acciones humanas

En `campaign_events.jsonl` se registraron **79 eventos** entre las fechas UTC 23/10 y 24/10 consultadas, asociados a una transición (incluyendo 54 sondas WAITING y 21 OK). **No se observaron eventos `SAFE_ABORT`, `executor_failure`, `SWITCH_FAILED` ni `ROLLBACK_COMMITTED`** en ese registro para la transición del 23/10. Tampoco se identificaron modificaciones RF humanas atribuibles. Estas afirmaciones se limitan a las fuentes inspeccionadas; no constituyen prueba de ausencia en otros registros.

**Clasificación de acciones:** transición y recuperación de conectividad: **automáticas programadas**; 22 reinicios de weather logger: **recuperaciones automáticas preexistentes**; inspección: **lectura humana sin intervención**; cambios manuales RF: **no identificados**.

## 7. Decisiones metodológicas observables y pendientes

1. Mantener las dos pruebas ERROR de la transición fuera de estimaciones de régimen estable, pero conservarlas como evidencia de cambio de escenario.
2. No asignar la prueba UL OK sin metadatos RF a un tratamiento para inferencia estratificada hasta su cotejo.
3. Conservar las 16 excepciones de matching del día y las 30 históricas F6655_B20; no imputar ni sobrescribir observaciones.
4. Analizar los 22 reinicios automáticos del weather logger como posible factor de calidad y faltantes, sin atribuirles causalidad no demostrada.
5. Reconciliar la frescura del export RF hasta medianoche; diferenciar fin de adquisición y momento de exportación.
6. En inferencia 3×2, controlar bloque/ventana, condiciones meteorológicas, autocorrelación y transición; no tratar cada muestra temporal como réplica experimental independiente.
7. Mantener la distinción entre operación normal, incidentes, recuperaciones automáticas y acciones humanas.

## 8. Procedencia, límites y seguridad

Fuentes leídas desde Controlador: `Data/exports/scientific_campaign_6g_integrated.csv`, `Data/exports/master_observations_multistation.csv`, `Data/exports/active_throughput_6g.csv`, `campaign_runtime/campaign_state.json`, `campaign_runtime/executor_state.json`, `campaign_runtime/campaign_events.jsonl`, `systemctl`, `journalctl`, `tailscale status` y `tailscale ping`. La información meteorológica de SJ01 es **evidencia sincronizada**, no una inspección SSH directa. Se publican solo agregados, estados y marcas temporales pertinentes: **sin credenciales, secretos, IPs privadas, dumps, JSON bruto, logs completos ni datos sensibles**.

**Trazabilidad documental:** nuevo archivo independiente del 23/10; no reemplaza informes anteriores. No se alteró ningún equipo ni dato de la campaña durante esta inspección.
