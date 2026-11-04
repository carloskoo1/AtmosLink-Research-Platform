# AtmosLink — trazabilidad diaria, 2026-11-03 (America/Lima)

**Corte de inspección:** 2026-11-03 23:54–23:56 -05:00. **Estado:** consolidación provisional (no incluye adquisiciones posteriores al corte). **Procedimiento:** lectura de CSV exportados y metadatos de sistema/journal en Controlador mediante conexión autorizada. Sin cambios en RF, PoE, VLAN, servicios, timers ni bases de datos. No se realizó intervención humana desde esta inspección.

## Contexto metodológico
La campaña factorial AtmosLink 3×2 de 42 días terminó el 2026-10-27; los registros de hoy pertenecen a operación posterior de línea base y **no** se incorporan como nuevas exposiciones factoriales. El escenario RF de las observaciones válidas del día fue BASE_7000_20: 7000 MHz, 20 MHz. La campaña prospectiva de Luisita es una fase distinta y su estado se audita por separado.

## RF / scientific_campaign_6g_integrated
Fuente: export local `scientific_campaign_6g_integrated.csv` (mtime 2026-11-03 23:41:54 -05:00). Filtrado por `rf_timestamp_local` de 2026-11-03: **281 filas**, de las cuales **181 LINK_OPERATIONAL_DUAL** y **100 COLLECTION_ERROR** (35.59%). En 181 filas operativas: frecuencia 7000 MHz y ancho 20 MHz; las 100 filas con error no informan frecuencia/ancho y no deben interpretarse como tratamientos alternativos. Último timestamp RF observado: **2026-11-03T23:36:52-05:00**. Medias RF disponibles, sin imputación de errores: RSSI DL/UL **−75.680/−79.503 dBm**, SNR DL/UL **21.740/17.232 dB**. Los errores de adquisición no prueban por sí mismos caída física del enlace. Se requiere correlacionar los 100 eventos con logs de conectividad y SSH antes de asignar causa.

El integrado **sí avanzó** respecto a `2026-09-15T23:36:42-05:00` (último registro actual indicado arriba). Matching meteorológico del 03/11: CU01 **277/281**, SJ01 **281/281**, ambos **277/281 (98.58%)**, cuatro excepciones CU01. La comprobación se refiere al export inspeccionado, no a una certificación global de integridad.

Para el escenario histórico F6655_B20 (filtro de frecuencia=6655 MHz y ancho=20 MHz), el export contiene **1733 filas**. **No hubo nuevas filas F6655_B20 el 03/11**. Se mantiene pendiente la verificación retrospectiva de que cada fila tenga `cu01_weather_matched=1` y `sj01_weather_matched=1`; los informes previos documentaron 30 excepciones históricas. No declarar el 100% ni cerrar la incidencia sin una conciliación fila a fila.

## Clima / master_observations_multistation
Fuente: `master_observations_multistation.csv` (mtime 23:52:43 -05:00). Registros del 03/11: **2315**: CU01 **1382**, SJ01 **933**. Promedios CU01: temperatura **18.809 °C**, humedad **67.835%**, presión **740.927 hPa**, viento **0.235 m/s**; última observación **23:51:10 -05:00**. Promedios SJ01: temperatura **8.968 °C**, humedad **96.129%**, presión **664.815 hPa**, viento **1.853 m/s**; última observación **23:51:00 -05:00**. Tailscale del Controlador muestra `rpi-sanjose64` presente; **no se realizó acceso SSH directo a la Raspberry**, por lo que la evidencia SJ01 procede del export sincronizado. No inferir disponibilidad integral de la Raspberry a partir de Tailscale.

## active_throughput_6g
Fuente: `active_throughput_6g.csv`, última actualización de archivo **2026-11-02 19:30:36 -05:00**. **0 pruebas fechadas el 03/11**; último inicio registrado **2026-11-02T19:30:24-05:00**. No estimar goodput ni registrar mediciones ausentes como fallos TCP. `andean-throughput.service` figuró `inactive` con último resultado `success`, lo cual no demuestra ejecución de pruebas del día.

## Servicios, timers, incidentes y recuperaciones
Inspección `systemctl show` y `list-timers` aproximadamente 23:54 -05:00:
- `luisita-prospective.service`: **failed**, resultado `exit-code`, código 1; timer activo/programado cada minuto. En `journalctl` 23:54:01–23:54:02 se registra **HALTED / CONTROLLER_ERROR**, con error «Prospective campaign is HALTED; see HALT.json and diagnostic events». La reiteración del error del servicio no representa nuevas exposiciones experimentales. No se verificó transición RF válida ni recuperación de la campaña prospectiva en esta inspección.
- `atmoslink-remote-sync.service`: `inactive`, resultado `success`, timer programado.
- `weather-logger.service`: **active**, resultado `success`; `atmoslink-weather-watchdog.service`: `inactive`, último resultado `success`, timer programado.
- `atmoslink-scientific-validation.service`: `inactive`, último resultado `success`, timer programado.
- `atmoslink-remote-backup.service`: **failed** (código 1). A las **02:33:24** se registró error de cuota `storageQuotaExceeded` de Google Drive UNC y `uploaded=False, verified=False`.
- `atmoslink-backup-recovery.service`: **failed** (código 3). A las **23:46:43**, el respaldo de **18:59:15** quedó verificado en destino primario, pero falló su subida a UNC y se preservó localmente. **No se confirma redundancia dual** para esa copia.

**SAFE_ABORT/executor_failure:** no se obtuvo evidencia afirmativa de eventos nuevos en las fuentes consultadas, pero **no se realizó una búsqueda exhaustiva de todos los archivos estructurados del ejecutor**; su ausencia no está certificada. **Transiciones:** no se confirmó transición RF válida del 03/11; escenario observado 7000/20. **Acciones humanas:** esta inspección no ejecutó cambios operativos; no se auditó exhaustivamente la autoría de modificaciones externas.

## Decisiones metodológicas y pendientes
1. Segregar los registros de línea base posterior al 27/10 de los 18 bloques factoriales; segregar igualmente los pilotos y ventanas prospectivas.
2. No considerar válida ninguna ventana prospectiva mientras el controlador permanezca `HALTED` y no se verifiquen configuración dual AP/SM, TCP y meteorología.
3. Investigar los **100 COLLECTION_ERROR** mediante timestamps y logs de acceso antes de atribuir una caída física del radioenlace.
4. Conservar sin imputación las cuatro excepciones CU01 del día y las **30 excepciones históricas F6655_B20** previamente reportadas; completar conciliación por fila.
5. Investigar por qué no hubo nuevos registros en `active_throughput_6g` el 03/11.
6. No declarar respaldo dual completo: destino UNC sigue sin verificación para la copia de 18:59:15.
7. Mantener abierta la revisión estructurada de `SAFE_ABORT`, `executor_failure` y auditoría de acciones humanas.

**Limitaciones:** inspección del Controlador; SJ01 solo mediante export sincronizado y estado Tailscale. Datos agregados al corte, no auditoría exhaustiva de logs del ejecutor ni certificación de todos los registros históricos. No se publican IP internas, secretos, JSON RF bruto ni volcados de bases de datos.
