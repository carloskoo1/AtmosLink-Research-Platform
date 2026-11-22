# AtmosLink — trazabilidad diaria 2026-11-21 (America/Lima)

## Alcance y procedencia
Inspección de solo lectura de Controlador y rpi-cunacales (equipo SJ01), conectados el 2026-11-21 ~23:48–23:50 -05:00. La campaña factorial 3×2 finalizó el 2026-10-28: los registros del día son seguimiento posterior de laboratorio, no nuevos segmentos de la campaña factorial. No se modifica adquisición ni se evalúa elegibilidad prospectiva de Luisita.

Origen: SQLite local /home/carlos/Proyectos/EstacionMeteorologica/SQLite/CU01/weather_local.db, consultado mediante URI mode=ro; systemctl/journalctl de lectura. Las estadísticas corresponden al corte consultado y no implican auditoría completa de eventos.

## RF e integración
scientific_campaign_6g_integrated: 361 observaciones fechadas 2026-11-21; último rf_timestamp_local 2026-11-21T22:56:23-05:00, posterior al control histórico 2026-09-15T23:36:42-05:00.
- 6655 MHz / 20 MHz: 171 observaciones LINK_OPERATIONAL_DUAL.
- 7000 MHz / 40 MHz: 189 observaciones LINK_OPERATIONAL_DUAL.
- 1 COLLECTION_ERROR sin frecuencia/ancho asignables.
- Matching CU01: 347/361; SJ01: 360/361; dual: 347/361 (96.12%).
- F6655_B20 acumulado: 2282 filas; dual válido: 2234; excepciones: 48. Respecto al control 2026-11-20 (2111/2066/45), hay 171 filas adicionales, 168 con matching dual y 3 excepciones nuevas. La condición universal cu01_weather_matched=1 y sj01_weather_matched=1 **no se cumple**. No se corrigen ni descartan datos originales.

active_throughput_6g: 180 pruebas del 2026-11-21, 90 DL OK (media 34.826 Mbps) y 90 UL OK (media 12.842 Mbps); máximo timestamp_start_local 2026-11-21T23:45:23-05:00.

master_observations_multistation: 2256 observaciones del día: CU01 1340 (temperatura media 21.17 °C; último master_timestamp_local 23:46:00), SJ01 916 (temperatura media 10.90 °C; último 23:45:59). weather-logger-sj01.service activo en rpi-cunacales.

## Series meteorológicas (SQLite local, no ZIP certificado)
| Fuente | CU01/AP_CUNACALES | SJ01/SM_SAN_JOSE | MID_LINK |
|---|---|---|---|
| NASA POWER | 2026-11-19 18:00 -05 | 2026-11-19 18:00 -05 | 2026-11-19 18:00 -05 |
| ERA5-Land | 2026-10-09 23:00 -05 | 2026-10-09 23:00 -05 | 2026-10-09 23:00 -05 |

Comparado con el control local del 2026-11-20: NASA POWER avanza un día en los tres sitios; ERA5-Land no avanza y continúa retrasado. No hay divergencia de fechas máximas entre sitios dentro de una misma fuente. Se localizó la carpeta AtmosLink_Backups en Drive, pero la búsqueda del ZIP del día no devolvió un archivo inspeccionable. No se certifica el contenido meteorológico del respaldo de Drive.

## Servicios, respaldos e incidencias
Controlador: atmoslink-remote-backup.service y tailscale-serve-ap.service figuran failed; atmoslink-weather-watchdog.timer y atmoslink-scientific-validation.timer programados. atmoslink-remote-sync.timer y atmoslink-backup-recovery.timer con ejecución reciente. La validación científica finalizó CU01 OK / SJ01 OK a las 23:34:09 aprox. (salida UTC 2026-11-22T04:34:09Z).

El respaldo backup_CU01_20261121_205152.zip (309907863 bytes) tuvo fallos previos de transferencia UNC, pero los logs registran verificación primaria y UNC y RECOVERY COMPLETE 2/2 a 2026-11-21 23:22:45 -05. Este registro no equivale a inspección del contenido ZIP en Google Drive ni certificación criptográfica independiente.

Pendiente: inspección exhaustiva de SAFE_ABORT, executor_failure, transiciones, acciones humanas y eventos de recuperación; inspección directa del ZIP de Drive y verificación de integridad de sus series. No se infiere ausencia de incidentes. No se reconfiguraron RF, PoE, VLAN, scripts, timers, servicios ni bases de datos.

## Criterio metodológico
Separar trazabilidad del seguimiento de laboratorio y campaña 3×2 concluida de la auditoría prospectiva Luisita. Conservar 48 excepciones F6655_B20 y documentar su causa antes de cualquier contraste científico. No tratar un error de colección como una exposición RF válida.
