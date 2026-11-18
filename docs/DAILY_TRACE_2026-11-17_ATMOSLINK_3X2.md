# AtmosLink — trazabilidad diaria 2026-11-17 (America/Lima)

## Alcance y procedencia
Inspección de solo lectura realizada 2026-11-17 23:48:44–23:49:47 -05:00, con consultas SQLite URI `mode=ro`, `systemctl` y `journalctl` en Controlador, y lectura de `weather-logger-sj01.service` en dispositivo conectado `rpi-cunacales` (SJ01). No se probó separadamente el alias literal `rpi-sanjose64`. Google Drive consultado mediante conector, carpeta `AtmosLink_Backups/CU01/field`. La campaña factorial 3×2 terminó el 28/10/2026: **los registros del 17/11 son seguimiento posterior**, no nuevas exposiciones factoriales. La vigilancia prospectiva de Luisita permanece separada.

## RF y escenario
`scientific_campaign_6g_integrated`: 364 observaciones RF fechadas 17/11, 364 `LINK_OPERATIONAL_DUAL`, 0 `COLLECTION_ERROR`; 6475 MHz / 40 MHz (176) y 6655 MHz / 20 MHz (188). RSSI promedio DL/UL −75.90/−79.70 dBm; SNR promedio DL/UL 23.69/19.16 dB. Último RF 2026-11-17T23:08:51-05:00. No interpretar estos escenarios como nuevas corridas de la campaña 3×2 ni inferir elegibilidad prospectiva.

## Throughput y estaciones
`active_throughput_6g`: 180/180 pruebas OK: DL 90, media 71.200 Mbps, última 23:45:08; UL 90, media 35.001 Mbps, última 23:45:24 -05:00.

`master_observations_multistation` del 17/11: CU01 1340 registros, temperatura media 20.02 °C, HR 61.53 %, presión 739.75 hPa, viento 0.26 m/s, último 23:42:40; SJ01 932 registros, temperatura 10.23 °C, HR 85.71 %, presión 664.10 hPa, viento 1.59 m/s, último 23:43:46 -05:00. En `rpi-cunacales`, `weather-logger-sj01.service` activo/running, Result=success a las 23:49:34. Se observó `GUARDADO` a las 23:48:46; también aviso de fragmento serial no UTF-8 descartado a las 23:47:46, seguido de `RX_VALIDO` y `GUARDADO` a las 23:48:46. Esto documenta anomalía serial puntual sin demostrar interrupción prolongada.

## Integración científica y matching
Watermark `scientific_campaign_6g_integrated`: 2026-11-17T23:08:51-05:00, posterior a referencia 2026-09-15T23:36:42-05:00: **avance confirmado**. Matching dual diario 352/364 (96.70 %); 12 observaciones no cumplen matching dual. Histórico F6655_B20: 2111 filas, 2066 con matching dual, **45 excepciones acumuladas**; 188 filas F6655_B20 del 17/11, de ellas **183 con matching dual y 5 sin él**. Comparado con control del 16/11: 1923→2111 (+188), 1883→2066 (+183), excepciones 40→45 (+5). Por tanto, la condición `cu01_weather_matched=1 AND sj01_weather_matched=1` para **todas** las nuevas filas F6655_B20 **NO se cumple**. Preservar excepciones, investigar desfases sin imputar ni modificar datos originales.

## NASA POWER / ERA5-Land — seis series
Fechas máximas **verificadas en SQLite local** (`SQLite/CU01/weather_local.db`), no leídas dentro del ZIP:
| Fuente | CU01 (AP_CUNACALES) | SJ01 (SM_SAN_JOSE) | MID_LINK | Cambio vs 16/11 |
|---|---|---|---|---|
| NASA POWER | 2026-11-15 18:00 -05 | 2026-11-15 18:00 -05 | 2026-11-15 18:00 -05 | +1 día en los tres |
| ERA5-Land | 2026-10-09 23:00 -05 | 2026-10-09 23:00 -05 | 2026-10-09 23:00 -05 | Sin avance en los tres |

No se detecta divergencia de fecha máxima entre sitios para una misma fuente. ERA5-Land permanece rezagada: investigar proceso incremental y disponibilidad upstream sin afirmar causa. Se **localizó en Google Drive** el ZIP `backup_CU01_20261117_202154.zip` en `AtmosLink_Backups/CU01/field`, modificado 2026-11-18T01:23:22Z, enlace https://drive.google.com/file/d/1t7KVBvR76DHmIUzq0iPGLVMBM1ifbPrz/view . **El contenido interno del ZIP no fue inspeccionado**, por lo que sus seis fechas máximas y su integridad interna siguen sin certificar. No confundir comprobación de presencia remota con validación del contenido.

## Servicios, timers, incidentes y recuperación
Aproximadamente 23:49:22 -05:00 activos: `atmoslink-radio-config-6g`, `atmoslink-dashboard`, `atmoslink-event-monitor`, `atmoslink-scheduler`, `weather-logger`. `atmoslink-remote-backup.service` y `atmoslink-backup-recovery.service` inactivos con Result=success (ejecuciones tipo oneshot, no interpretar inactividad como fallo). Timers observados programados: `atmoslink-remote-sync`, `atmoslink-weather-watchdog`, `atmoslink-backup-recovery`, `atmoslink-scientific-validation`, `atmoslink-remote-backup`.

En logs del 17/11, recuperador verificó respaldo `backup_CU01_20261117_202154.zip` (296592366 bytes) en primario y UNC, con `RECOVERY COMPLETE 2/2` a las 21:56:45, 22:33:48 y 23:35:50 -05:00. A las 23:03:03 se observó un **timeout de 60 segundos** en consulta UNC de `rclone lsf`, con fallo de una ejecución de recuperación, seguido de recuperación 2/2 a las 23:35:50. Confirmación de redundancia **por logs**, no por inspección del ZIP ni auditoría histórica de copias.

Búsqueda acotada en journal general del 17/11 de `SAFE_ABORT`, `executor_failure`, `CONTROLLER_ERROR`, `HALTED`, `WINDOW_VERIFIED` sin coincidencias en la salida consultada. **No es auditoría exhaustiva de registros especializados**; no certificar ausencia de eventos o de transiciones. No se atribuyeron acciones humanas específicas sin evidencia. Las transiciones prospectivas pertenecen a la vigilancia separada de Luisita.

## Decisiones y límites
Conservar 5 nuevas excepciones F6655_B20 y 12 discordancias de matching dual del día como incidencias de calidad; no declarar elegibilidad científica por simple asociación RF o throughput OK. Mantener abierto el seguimiento de ERA5-Land y la certificación del contenido remoto; registrar la recuperación del backup tras timeout como evidencia observacional, no reparación manual. Inspección operacional estrictamente read-only: ninguna modificación de RF, PoE, VLAN, scripts, timers, servicios o bases. Este archivo es documentación textual nueva sin credenciales, secretos, IP privadas, dumps ni datos personales.
