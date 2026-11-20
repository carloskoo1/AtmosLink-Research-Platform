# AtmosLink — trazabilidad y clima — 2026-11-19

**Zona horaria:** America/Lima (-05:00). **Inspección:** 2026-11-19 23:49–23:50, lectura exclusiva de Controlador y rpi-cunacales (equipo SJ01); consulta de metadatos Google Drive y repositorio GitHub. **Alcance:** seguimiento de laboratorio posterior al cierre de la campaña factorial 3×2 (28-10-2026); no se presenta como nueva adquisición factorial. Vigilancia prospectiva de Luisita separada.

## RF y escenario
Consulta SQLite con conexión `mode=ro`, `PRAGMA query_only=ON`, tabla `scientific_campaign_6g_integrated`, filtro `rf_timestamp_local LIKE '2026-11-19%'`: 362 observaciones `LINK_OPERATIONAL_DUAL`, 0 errores de colección: 6475 MHz/20 MHz 174 observaciones (RSSI DL/UL medio -76.34/-82.69 dBm; SNR DL/UL 23.20/18.64 dB); 6475 MHz/40 MHz 188 (RSSI -77.97/-82.02 dBm; SNR 22.57/19.82 dB). Se describen escenarios observados, no se atribuye transición causal ni elegibilidad científica. Último timestamp integrado 2026-11-19T23:00:08-05:00.

## Throughput y clima
`active_throughput_6g`: DL 90 OK, media 50.712 Mbps; UL 90 OK, media 23.420 Mbps (fecha de inicio local 19-11). `master_observations_multistation`: CU01 1299 filas, T media 21.74 °C, HR 57.70%, presión 739.99 hPa, viento 0.30 m/s, última 23:46:49; SJ01 977 filas, T 10.61 °C, HR 88.66%, presión 664.44 hPa, viento 1.86 m/s, última 23:45:52. `weather-logger-sj01.service` activo en rpi-cunacales; log mostró fragmentos seriales no UTF-8 descartados 23:44:52 y 23:46:52 y recepción válida posterior a 23:47:52: incidencia de integridad serial acotada, sin inferir interrupción global.

## Calidad de integración
`scientific_campaign_6g_integrated` supera la referencia 2026-09-15T23:36:42-05:00: watermark 2026-11-19T23:00:08-05:00. Matching CU01 341/362, SJ01 362/362, dual 341/362 (94.20%); 21 excepciones de matching dual en las filas del día. Histórico de configuración F6655_B20: 2111 filas, 2066 matching dual, **45 excepciones acumuladas**; 0 nuevas filas de esa configuración el 19-11. La condición obligatoria `cu01_weather_matched=1 AND sj01_weather_matched=1` para nuevas filas F6655_B20 sigue bajo vigilancia, sin nueva cohorte del día para validarla.

## Meteorología NASA POWER y ERA5-Land
Fuente de las seis fechas: SQLite **local** `/home/carlos/Proyectos/EstacionMeteorologica/SQLite/CU01/weather_local.db`, no contenido ZIP remoto.
- NASA POWER: CU01 (AP_CUNACALES) 2026-11-17 18:00 -05; SJ01 (SM_SAN_JOSE) igual; MID_LINK igual. Frente al control local reportado el 18-11 (máximo 16-11), **avance de un día** en las tres series.
- ERA5-Land: CU01, SJ01, MID_LINK 2026-10-09 23:00 -05; **sin avance** respecto al control anterior; atraso persistente, causa no establecida.
- Coincidencia de fechas máximas entre sitios dentro de cada fuente. No se halló el ZIP del 19-11 mediante búsqueda Drive por nombre; no se verificaron las seis series **dentro del respaldo más reciente**. Se localizó la carpeta `AtmosLink_Backups` por metadatos. No equiparar coincidencia de máximos locales con integridad del ZIP.

## Servicios, respaldos, incidentes y límites
En Controlador, `systemctl --failed` reportó `atmoslink-remote-backup.service` y `tailscale-serve-ap.service` fallidos; timers `atmoslink-remote-sync`, `atmoslink-weather-watchdog`, `atmoslink-backup-recovery`, `atmoslink-scientific-validation`, `atmoslink-remote-backup` listados y programados. Logs de `atmoslink-backup-recovery.service` registraron `RECOVERY COMPLETE 2/2` para `backup_CU01_20261119_203703.zip`, 304273004 bytes, a 2026-11-20T04:03:52Z (19-11 23:03:52 -05) y 2026-11-20T04:39:30Z (19-11 23:39:30 -05), con verificaciones declaradas primary/UNC. **Esto no acredita inspección interna ni consistencia científica del ZIP.** Hubo fallos de respaldo en el historial de servicio, sin establecer aquí su causalidad puntual. Auditoría exhaustiva de `SAFE_ABORT`, `executor_failure`, transiciones, acciones humanas y todos los servicios no completada; no declarar ausencia de eventos. Sin intervención humana ejecutada por esta inspección.

**Decisión metodológica:** preservar filas originales, distinguir adquisición de laboratorio de factorial concluido y de vigilancia prospectiva de Luisita, mantener excepciones de matching sin imputarlas, no convertir estados de recuperación en validación del contenido de respaldo. Ningún cambio en RF, PoE, VLAN, scripts, timers, servicios o bases de datos. Solo evidencia textual agregada, sin credenciales, IP privadas ni dumps.
