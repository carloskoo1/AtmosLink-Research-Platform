# AtmosLink — trazabilidad diaria 2026-11-18 (America/Lima)

## Procedencia y límites
Inspección de solo lectura del 18/11/2026, aproximadamente 23:54–23:56 -05:00, mediante Desktop Commander en **Controlador** y **rpi-cunacales** (dispositivo SJ01; alias literal rpi-sanjose64 no probado independientemente). SQLite abierta mediante URI `mode=ro`; consultas `systemctl` y `journalctl`. La campaña factorial 3×2 concluyó el 28/10/2026: estas son observaciones posteriores de laboratorio, no nuevas exposiciones factoriales. No se realiza aquí la evaluación prospectiva independiente de Luisita.

## RF / escenario
En `scientific_campaign_6g_integrated`, 373 observaciones del 18/11, todas `LINK_OPERATIONAL_DUAL`, ninguna `COLLECTION_ERROR`; todas a **7000 MHz / 20 MHz**. RSSI DL/UL medio −74.52/−81.47 dBm; SNR DL/UL medio 22.63/17.12 dB. Última observación 2026-11-18T23:34:10-05:00. Matching meteorológico dual 369/373 (98.93 %), cuatro excepciones.

## TCP y estaciones
`active_throughput_6g`: 184/184 mediciones OK, DL 92 con promedio 45.965 Mbps (última 23:45:08); UL 92 con promedio 25.454 Mbps (última 23:45:29). No inferir elegibilidad científica a partir de status OK.

`master_observations_multistation`: CU01 1391 registros, temperatura media 21.53 °C, HR 56.72 %, presión 739.36 hPa, viento 0.39 m/s, último 23:51:22. SJ01 954 registros, temperatura media 11.05 °C, HR 87.63 %, presión 663.89 hPa, viento 2.24 m/s, último 23:52:49. `weather-logger-sj01.service` activo, Result=success en rpi-cunacales a las 23:54 -05:00.

## Integración científica y F6655_B20
Watermark integrado 2026-11-18T23:34:10-05:00: **avance respecto a 2026-09-15T23:36:42-05:00 confirmado**. Histórico F6655_B20: **2111 filas**, **2066** con `cu01_weather_matched=1 AND sj01_weather_matched=1`, **45 excepciones**. Nuevas filas F6655_B20 fechadas 18/11: **0**. No hay nuevos casos del día para comprobar; la exigencia sobre futuras filas continúa abierta. No modificar ni imputar observaciones originales.

## NASA POWER / ERA5-Land — control local de seis series
Fechas máximas obtenidas **en SQLite local de Controlador** (`SQLite/CU01/weather_local.db`), no en el interior de ZIP remoto:

| Fuente | CU01 | SJ01 | MID_LINK | Diferencia frente al 17/11 |
|---|---|---|---|---|
| NASA POWER | 2026-11-16T18:00:00-05:00 | 2026-11-16T18:00:00-05:00 | 2026-11-16T18:00:00-05:00 | +1 día en los tres |
| ERA5-Land | 2026-10-09T23:00:00-05:00 | 2026-10-09T23:00:00-05:00 | 2026-10-09T23:00:00-05:00 | Sin avance |

No hay discrepancia de fecha máxima entre sitios dentro de cada fuente. El retraso de ERA5-Land continúa pendiente de investigación; no se infiere causa. Conector Google Drive localizó carpeta `AtmosLink_Backups`, pero las búsquedas por nombre de ZIP del 18/11 no devolvieron archivo; **no se pudo inspeccionar el contenido del respaldo remoto** ni certificar desde él las seis series.

## Servicios, timers, incidentes y recuperación
Alrededor de 23:56 -05:00 activos: `atmoslink-radio-config-6g`, `atmoslink-dashboard`, `atmoslink-event-monitor`, `atmoslink-scheduler`, `weather-logger`. Timers programados: `atmoslink-remote-sync`, `atmoslink-weather-watchdog`, `atmoslink-backup-recovery`, `atmoslink-scientific-validation`, `atmoslink-remote-backup`. `atmoslink-remote-backup.service` inactivo con Result=success (oneshot); `atmoslink-backup-recovery.service` failed con Result=exit-code en consulta.

En journal del 18/11 se observó respaldo `backup_CU01_20261118_202902.zip` (298634634 bytes), con verificaciones de destino primario y UNC y `RECOVERY COMPLETE 2/2` a las **22:16:57** y **23:18:51 -05:00**. Posteriormente, a las **23:49:09**, falló otra ejecución del recuperador por timeout de 60 s al consultar el destino primario mediante `rclone lsf`. Se conserva la distinción entre recuperación 2/2 **según logs** y fallo posterior del servicio; no se certifica contenido interno del ZIP ni ausencia de problemas futuros.

Se solicitó búsqueda acotada de `SAFE_ABORT`, `executor_failure`, `CONTROLLER_ERROR`, `HALTED`, `WINDOW_VERIFIED` en journal general; no se obtuvo resultado final completo de esa búsqueda en esta inspección. **No se certifica ausencia de eventos**, transiciones ni acciones humanas. La vigilancia prospectiva de Luisita permanece en su tarea separada. No se observaron ni atribuyeron reparaciones humanas concretas.

## Decisiones metodológicas y seguridad
Conservar las cuatro discordancias de matching dual del día y las 45 excepciones históricas F6655_B20 para conciliación posterior. No reinterpretar el seguimiento posterior como campaña factorial nueva; no declarar elegibilidad prospectiva. Mantener seguimiento de ERA5-Land y pendiente de validación de contenido del ZIP en Google Drive. No se cambiaron RF, PoE, VLAN, scripts, timers, servicios ni bases. Este informe incluye sólo agregados y evidencia textual, sin credenciales, secretos, IP privadas ni dumps.
