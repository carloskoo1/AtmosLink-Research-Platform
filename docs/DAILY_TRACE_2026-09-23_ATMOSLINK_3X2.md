# AtmosLink 3×2 — Consolidación diaria 2026-09-23

**Ventana principal:** 2026-09-23 00:00–23:59 (-05:00). **Inspección:** 2026-09-24 00:17–00:21 (-05:00), exclusivamente read-only. Se referencia además la transición automática inmediatamente posterior al cierre diario por su relevancia experimental.

## Resumen ejecutivo

Durante el 23/09 el escenario experimental fue **F6475_B20 (6475 MHz / 20 MHz)**. `active_throughput_6g` registró 192 pruebas en el día: 191 `OK` y 1 `ERROR`; 94 pares DL/UL `OK` quedaron asociados explícitamente a 6475/20. El último par del escenario, 23:45, produjo DL 20.144 Mbps y UL 4.588 Mbps, pérdida ping 0 % y RTT medio 6.215 ms.

A las 00:00 del 24/09 el orquestador inició automáticamente la transición prevista a **F6655_B40 (6655 MHz / 40 MHz)**. `TRIAL_APPLIED` fue registrado a 00:00:02, hubo una ventana de `CONNECTIVITY_PROBE=WAITING`, la conectividad alcanzó 10/10 confirmaciones a 00:02:48 y `SWITCH_COMMITTED=OK` a 00:03:07. No se observó `SAFE_ABORT`, rollback ni `executor_failure` nuevo. `campaign_state.json` y `executor_state.json` confirman F6655_B40 activo.

## RF, throughput y clima

La primera telemetría RF posterior a la transición confirma `LINK_OPERATIONAL_DUAL`. A 00:17:31 del 24/09: 6655 MHz, 40 MHz, AP Tx 10 dBm, SM Tx 3 dBm, RSSI DL -79 dBm, SNR DL 21 dB, MCS DL/UL 103/100, tasa DL reportada 68 Mbps. La telemetría del SM fue obtenida por el colector a través del AP; el acceso administrativo directo a `rpi-sanjose64` no estuvo disponible en esta inspección.

CU01 permaneció fresco: a 00:20:24 registró 15.86 °C, 73.59 % HR y 742.51 hPa. En `active_throughput_6g`, 191/192 pruebas del 23/09 tuvieron clima CU01 asociado, pero 0/192 tuvieron clima SJ01 asociado. El último SJ01 disponible en `station_observations` es 2026-09-21T23:04:11-05:00 (7.27 °C, 99.86 % HR, 665.61 hPa, viento 2.6 m/s). Por tanto, la meteorología SJ01 central está desactualizada y no debe tratarse como clima contemporáneo del 23/09.

La única prueba throughput fallida del 23/09 ocurrió a 16:45:05 (DL): fallo del socket/servidor iperf, `Connection refused`, con 80 % de pérdida ping. La adquisición se recuperó sin intervención documentada y las pruebas posteriores volvieron a `OK`, incluyendo el cierre 23:45.

## Integración científica y validación histórica

`master_observations_multistation` contiene 148443 filas y su watermark permanece en 2026-09-20T21:34:00+00:00. `scientific_campaign_6g_integrated` contiene 5253 filas y su watermark permanece en **2026-09-20T16:31:04-05:00**. Ambos productos están atrasados respecto de la adquisición RF/throughput actual.

La validación solicitada respecto de `2026-09-15T23:36:42-05:00` queda confirmada parcialmente y cerrada con excepción explícita: el integrado avanzó 1115 filas posteriores al watermark de referencia. Para F6655_B20 hay 578 filas posteriores: SJ01 `weather_matched=1` en 578/578, CU01 en 575/578 y ambas estaciones en 575/578. Las tres excepciones CU01 son 2026-09-16 01:27:01, 07:28:19 y 22:41:16 (-05:00); se preservan sin imputación.

## Servicios, incidentes y decisiones metodológicas

El registro interno de tareas muestra `sync_master_dataset`, `health_monitor`, `enrich_master_dataset`, `master_quality_check`, `build_station_observations`, `scientific_comparison` y `atmospheric_master_reconcile` completando sin error en la inspección. ERA5 y NASA ejecutaron correctamente el 23/09, aunque el monitor clasifica las fuentes externas como `STALE` por latencia de disponibilidad.

Persisten tres fallos de integración que requieren tratamiento separado de la operación RF: `build_multistation_master` falla desde su último éxito 20/09 16:31:50 por una vista que referencia `scientific_campaign_6g_integrated_old`; `scientific_campaign_export` falla por la misma dependencia, último éxito 20/09 16:35:15; `scientific_hourly_6g` falla porque el módulo Python no existe, último éxito 20/09 15:34:36. No se corrigieron ni reiniciaron durante esta inspección.

El backup remoto más reciente verificable es `backup_CU01_20260923_024401.zip`, 141132652 bytes, `uploaded=true`, `verified=true`, con **2/2 destinos** verificados (Drive principal y Drive UNC).

**Decisión metodológica:** mantener el escenario F6655_B40 recién confirmado sin intervención manual; preservar la evidencia de la transición y del fallo throughput aislado; no imputar las tres filas F6655_B20 sin matching CU01; y tratar los productos multisitio/integrados posteriores al 20/09 como pendientes hasta reparar, de forma controlada y fuera de esta inspección read-only, la cadena de integración. No se modificaron RF, PoE, VLAN, servicios, timers ni bases de datos.

## Trazabilidad de acciones humanas

Durante esta consolidación solo se realizaron lecturas de archivos, consultas SQLite/CSV y revisión del estado Git. La única escritura corresponde a este documento de evidencia y a su commit Git. No se ejecutaron acciones humanas sobre el radioenlace ni sobre la infraestructura de adquisición.
