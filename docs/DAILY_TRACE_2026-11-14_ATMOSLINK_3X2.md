# AtmosLink — trazabilidad y clima, 2026-11-14 (America/Lima)

**Corte:** 2026-11-14 23:47–23:49 -05:00 (antes del cierre del día). **Procedimiento:** consultas de solo lectura mediante Desktop Commander a Controlador y dispositivo remoto conectado `rpi-cunacales`; SQLite abierto con URI `mode=ro`; lectura de systemd/journal y búsqueda de metadatos en Google Drive. No se cambió RF, PoE, VLAN, scripts, timers, servicios ni bases. No se realizó SSH separado a un host llamado literalmente `rpi-sanjose64`. La campaña factorial AtmosLink 3×2 está concluida; estos registros son seguimiento del laboratorio, no una nueva ejecución factorial. La vigilancia prospectiva de Luisita es independiente.

## RF, escenario y TCP
En `scientific_campaign_6g_integrated`, **363** observaciones del 14/11, todas a **7000 MHz / 20 MHz** (configuración de línea base observada), **363 LINK_OPERATIONAL_DUAL**, **0 COLLECTION_ERROR**. Último registro RF: `2026-11-14T22:51:51-05:00`. RSSI medio DL/UL: **−74.08/−80.43 dBm**; SNR medio DL/UL: **23.03/17.99 dB**. No se infiere elegibilidad experimental ni se afirma una transición a partir de la frecuencia observada.

`active_throughput_6g`: **186** pruebas **OK**, 93 DL (media **55.027 Mbps**, último inicio 23:45:08) y 93 UL (media **31.902 Mbps**, último inicio 23:45:23). Son mediciones descriptivas del día.

## Meteorología CU01/SJ01 e integración
`master_observations_multistation`: **2297** registros con fecha local 14/11: CU01 **1330**, temperatura media **20.55 °C**, humedad **59.66 %**, presión **753.34 hPa**, viento **0.32 m/s**, último 23:39:45; SJ01 **967**, temperatura **9.97 °C**, humedad **91.68 %**, presión **665.70 hPa**, viento **2.48 m/s**, último 23:40:36. `weather-logger-sj01.service` en `rpi-cunacales`: **active**, `Result=success`, `ExecMainStatus=0` (consulta a las 23:47).

El watermark de `scientific_campaign_6g_integrated` alcanzó `2026-11-14T22:51:51-05:00`, superior al control `2026-09-15T23:36:42-05:00`: **avance confirmado**. Correspondencia meteorológica del día: CU01 **354/363**, SJ01 **363/363**, dual **354/363** (**97.52 %**), nueve excepciones diarias. Histórico `F6655_B20`: **1923** filas, **1883** con matching dual, **40** excepciones acumuladas, última fila fechada 11/11. **No hay nuevas filas F6655_B20 del 14/11**; la comprobación de que toda futura fila cumpla `cu01_weather_matched=1` y `sj01_weather_matched=1` permanece abierta. No se alteran filas ni se imputan correspondencias.

## NASA POWER / ERA5-Land — seis series
Fechas máximas **de la base local** `SQLite/CU01/weather_local.db` en Controlador, no verificadas dentro del ZIP de Google Drive. Mapeo: CU01=`AP_CUNACALES`, SJ01=`SM_SAN_JOSE`, MID_LINK=`MID_LINK`.

| Fuente | CU01 | SJ01 | MID_LINK | Comparación con 13/11 |
|---|---|---|---|---|
| NASA POWER | 2026-11-12 18:00 -05:00 | 2026-11-12 18:00 -05:00 | 2026-11-12 18:00 -05:00 | **+1 día** en los tres sitios |
| ERA5-Land | 2026-10-09 23:00 -05:00 | 2026-10-09 23:00 -05:00 | 2026-10-09 23:00 -05:00 | **Sin avance** en los tres sitios |

No hay divergencia de fecha máxima entre sitios dentro de cada fuente. ERA5-Land continúa atrasado: causa y latencia de ingestión no verificadas. Se consultaron metadatos de Drive, incluida la ruta visible `AtmosLink_Backups/CU01/field`; la búsqueda no encontró el ZIP del 14/11 ni permitió inspeccionar el contenido del respaldo más reciente. **No se certifican las seis fechas dentro de Google Drive.**

## Servicios, timers, incidentes y recuperación
En Controlador estaban **active**: `atmoslink-dashboard`, `atmoslink-event-monitor`, `atmoslink-radio-config-6g`, `atmoslink-scheduler`, `weather-logger`. Timers programados observados: `atmoslink-backup-recovery`, `atmoslink-remote-sync`, `atmoslink-weather-watchdog`, `atmoslink-scientific-validation` y `atmoslink-remote-backup`.

**Incidente de respaldo crítico abierto:** a las **02:33:04 -05:00**, `atmoslink-remote-backup.service` terminó en error `rateLimitExceeded` (cuota Drive), `uploaded=False`, `verified=False`. Recuperador: a las **22:43:13**, copia `backup_CU01_20261114_200047.zip` **verificada en destino primario** (284833720 bytes), pero falló carga a destino UNC; a las **23:15:02**, otra ejecución falló por timeout de 60 s consultando el destino primario. Al corte, `atmoslink-remote-backup.service` y `atmoslink-backup-recovery.service` estaban **failed**. **Redundancia 2/2 no confirmada**. La copia primaria verificada no implica recuperación completa.

Se consultó una búsqueda acotada del journal para `SAFE_ABORT`, `executor_failure`, `WINDOW_VERIFIED`, `WINDOW_INTENT` y `CONTROLLER_ERROR`; no se obtuvo evidencia positiva en esa búsqueda, pero **no se certifica ausencia de eventos** sin conciliación exhaustiva de logs especializados, transiciones y acciones humanas. No se ejecutaron transiciones ni recuperaciones manuales durante la inspección. Decisión metodológica: separar observación operativa, calidad de matching, validez experimental y evidencia de respaldo; conservar excepciones históricas.

**Pendientes:** certificar contenido del ZIP más reciente en Drive; recuperar redundancia 2/2 mediante intervención autorizada separada; investigar ERA5-Land; conciliar 40 excepciones históricas F6655_B20 y 9 excepciones del día; auditar logs especializados y el host literal `rpi-sanjose64`. Documento textual sin credenciales, direcciones privadas, dumps ni información sensible.
