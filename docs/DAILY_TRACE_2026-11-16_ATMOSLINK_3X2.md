# AtmosLink — trazabilidad diaria 2026-11-16 (America/Lima)

## Alcance y procedencia
Inspección de solo lectura realizada el 2026-11-16 aproximadamente 23:51–23:52 -05:00. Controlador: consultas SQLite mediante URI `mode=ro`, `systemctl` y `journalctl`; equipo remoto conectado como `rpi-cunacales`: `weather-logger-sj01.service` activo a las 23:51:47. No se probó por separado el alias literal `rpi-sanjose64`. La campaña factorial 3×2 terminó el 28/10; los datos de hoy son seguimiento posterior, no nuevas exposiciones de la campaña. La vigilancia prospectiva de Luisita se mantiene separada.

## RF y escenario
En `scientific_campaign_6g_integrated`: 372 observaciones del 16/11, 370 `LINK_OPERATIONAL_DUAL` y 2 `COLLECTION_ERROR`. Configuraciones observadas: 6655 MHz / 40 MHz (186), 7000 MHz / 20 MHz (184), dos errores sin configuración. RSSI promedio DL/UL −75.45/−81.40 dBm y SNR promedio DL/UL 23.04/18.49 dB (promedios sobre filas con valores). Última observación 23:43:14 -05:00. Errores a las 05:03:53 (`database is locked`) y 12:00:22 (faltan variables obligatorias). Estas observaciones no certifican por sí solas la elegibilidad de ventanas o transiciones.

## TCP y estaciones
`active_throughput_6g`: 178 pruebas OK (89 DL, promedio 63.284 Mbps; 89 UL, promedio 41.411 Mbps), últimas pruebas iniciadas 23:45:08 y 23:45:25 -05:00.

`master_observations_multistation`: CU01 1343 filas, temperatura media 19.48 °C, humedad 64.24 %, presión 740.97 hPa, viento 0.18 m/s, último registro 23:46:18; SJ01 919 filas, temperatura 9.80 °C, humedad 92.30 %, presión 665.19 hPa, viento 1.37 m/s, último registro 23:43:42 -05:00. Logger remoto SJ01 activo. No se alteraron servicios.

## Integración científica y calidad
El watermark de `scientific_campaign_6g_integrated` alcanzó 2026-11-16T23:43:14-05:00, posterior al control 2026-09-15T23:36:42-05:00. Matching del día: CU01 362/372, SJ01 371/372, dual 362/372 (97.31 %). Histórico F6655_B20: 1923 filas, 1883 con matching dual, **40 excepciones históricas**; 0 filas nuevas F6655_B20 fechadas el 16/11. El criterio para *futuras* filas F6655_B20 permanece abierto; no se declara subsanación histórica.

## NASA POWER y ERA5-Land
Fechas máximas verificadas **en SQLite local de Controlador, no dentro del ZIP de Google Drive**:

| Fuente | CU01 | SJ01 | MID_LINK | Comparación con 15/11 |
|---|---|---|---|---|
| NASA POWER | 2026-11-14 18:00 -05 | 2026-11-14 18:00 -05 | 2026-11-14 18:00 -05 | +1 día en los tres sitios |
| ERA5-Land | 2026-10-09 23:00 -05 | 2026-10-09 23:00 -05 | 2026-10-09 23:00 -05 | Sin avance |

No hay divergencias entre sitios para una misma fuente. ERA5-Land sigue rezagada y debe auditarse su actualización incremental. Google Drive devolvió la carpeta `AtmosLink_Backups`, pero la búsqueda exacta del respaldo `backup_CU01_20261116_201402.zip` no devolvió archivo; **contenido y fechas dentro del respaldo remoto no verificados**. No extrapolar fechas locales a ZIP.

## Servicios, incidentes y respaldos
Activos en Controlador: `atmoslink-radio-config-6g`, `atmoslink-dashboard`, `atmoslink-event-monitor`, `atmoslink-scheduler`, `weather-logger`. Timers observados: `atmoslink-remote-sync`, `atmoslink-weather-watchdog`, `atmoslink-backup-recovery`, `atmoslink-scientific-validation`, `atmoslink-remote-backup`. En estado failed: `atmoslink-remote-backup.service` y `tailscale-serve-ap.service`. El respaldo independiente de madrugada falló parcialmente por `rateLimitExceeded` (02:47:46); registró verificación UNC, pero resultado global `uploaded=False, verified=False`. Recuperador: tras fallos intermedios, el log registró `RECOVERY COMPLETE 2/2` del respaldo `backup_CU01_20261116_201402.zip` a las 23:21:51 y 23:44:54, con verificación primaria y UNC por logs (292844420 bytes). Esto **no certifica la inspección directa del ZIP** ni conciliación de toda la historia.

No se acreditó una auditoría exhaustiva de `SAFE_ABORT`, `executor_failure`, transiciones ni acciones humanas; no se declara ausencia. Los dos errores de recolección se conservan como incidentes observables. Cualquier transición de campaña prospectiva requiere documentación en su vigilancia separada.

## Decisiones y límites
No atribuir a la campaña 3×2 terminada nuevas exposiciones; conservar errores RF, diez discordancias de matching dual del día y 40 excepciones F6655_B20 sin imputación. Distinguir la confirmación de respaldo por logs de la verificación del contenido remoto. Inspección operativa exclusivamente read-only; sólo este documento textual se escribió en GitHub. Sin credenciales, IP privadas, volcados de bases ni secretos.
