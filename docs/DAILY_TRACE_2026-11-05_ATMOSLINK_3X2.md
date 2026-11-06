# AtmosLink — trazabilidad diaria, 2026-11-05 (America/Lima)

**Inspección:** 2026-11-06 00:17–00:25 -05:00 (aprox.). **Alcance:** observaciones del 2026-11-05 00:00–23:59:59 -05:00. **Fuente:** Controlador, SQLite en modo `mode=ro`, journalctl/systemctl/tailscale solo lectura. `rpi-sanjose64` visible en Tailscale; no se obtuvo sesión directa ni se eludieron restricciones de acceso. Los datos SJ01 proceden de la copia sincronizada en Controlador. No se modificaron equipos, RF, PoE, VLAN, servicios, timers ni bases de datos.

## RF y escenario
`scientific_campaign_6g_integrated`: **281** filas del día, desde 00:02:27 hasta 23:28:34 -05:00; **281 LINK_OPERATIONAL_DUAL**, cero COLLECTION_ERROR. Todas reportan **7000 MHz / 20 MHz** (línea base BASE_7000_20; no exposición factorial 3×2). Medias excluyendo ceros: RSSI DL/UL **−75.794/−81.495 dBm**, SNR DL/UL **21.349/17.093 dB**. No se observó una transición RF confirmada del día en la consulta de eventos systemd; esto no equivale a auditoría exhaustiva de todos los logs especializados.

## Meteorología
`master_observations_multistation`: **2294** filas del día. CU01: **1352**, temperatura media **20.386 °C**, humedad **61.037 %**, presión **739.925 hPa**, viento **0.284 m/s**, última 23:59:30. SJ01: **942**, temperatura media **9.739 °C**, humedad **88.834 %**, presión **664.184 hPa**, viento **2.182 m/s**, última 23:59:06. Las medias son descriptivas, sin evaluación de calibración ni completitud minuto a minuto.

## Throughput y validación científica
`active_throughput_6g`: **0 filas** con inicio el 2026-11-05. Último registro histórico: **2026-11-02T19:30:24-05:00**. Discontinuidad de medición, no imputar pruebas como fallidas ni extrapolar goodput.
`scientific_campaign_6g_integrated`: última observación **2026-11-05T23:28:34-05:00**, posterior al watermark **2026-09-15T23:36:42-05:00**: **avance confirmado**. Matching del día: CU01 **276/281**, SJ01 **280/281**, dual **276/281 (98.22 %)**; cinco filas sin matching dual.
Histórico F6655_B20: **1733 filas**, CU01 **1703**, SJ01 **1733**, dual **1703**; **30 excepciones históricas**. Última fila de esa configuración: **2026-11-01T17:33:42-05:00**. **No hay nuevas filas F6655_B20 del 5 de noviembre**, por lo que la condición exigida de que *las nuevas filas* tengan `cu01_weather_matched=1` y `sj01_weather_matched=1` no puede validarse prospectivamente hoy. Mantener abierta la validación y no modificar datos históricos.

## Servicios, incidentes, recuperaciones y acciones
Al inspeccionar el 6 de noviembre: `atmoslink-dashboard`, `atmoslink-event-monitor`, `atmoslink-radio-config-6g`, `atmoslink-scheduler` y `weather-logger` activos; `luisita-prospective.service` y `atmoslink-remote-backup.service` en estado failed. Timers de sincronización, watchdog, recuperación de respaldos, validación científica, respaldo y prospectivo listados con próximas ejecuciones; ello no certifica la ejecución exitosa de cada ciclo.
- **Prospectiva Luisita:** a **2026-11-05 23:59:00 -05:00**, el servicio falla con `Prospective campaign is HALTED` (exit-code 1). Es persistencia del incidente del controlador, no una nueva exposición válida. Separar sus datos de la campaña factorial concluida.
- **Respaldo:** **02:47:33**, respaldo remoto dual fallido (`uploaded=False; verified=False`; evidencia de problema de cuota). A **23:38:54**, `RECOVERY COMPLETE 2/2` para copia `backup_CU01_20261105_191056.zip`; acredita esa copia, no la totalidad de pendientes.
- **Sincronización:** últimas ejecuciones 23:57:04 y 23:58:16 terminan satisfactoriamente; no prueba ausencia de fallos anteriores.
- **Watchdog:** últimas ejecuciones hasta 23:58:15 terminan satisfactoriamente; no se cuantificaron reinicios del logger.
- **Validación científica:** servicio termina satisfactoriamente a **23:58:21**; se generaron artefactos de validación SJ01 (sin publicar datos).
- **SAFE_ABORT / executor_failure / transiciones:** sin coincidencias en búsqueda acotada de journal del día. Resultado **no exhaustivo**; revisar logs especializados antes de declarar ausencia definitiva.
- **Acciones humanas:** no se atribuyen cambios manuales al día sin registro positivo; esta inspección fue estrictamente read-only.

## Decisiones metodológicas
1. Conservar la fase **BASE_7000_20** separada de los seis tratamientos factoriales 3×2 y de la prospectiva de Luisita.
2. No declarar válido ningún bloque prospectivo con controlador HALTED, ni inventar throughput durante el vacío de adquisición.
3. Mantener como hallazgos abiertos cinco faltas de matching dual del día y 30 históricas F6655_B20; no ajustar hipótesis ni datos post hoc.
4. Verificar posteriormente logs especializados de transiciones/SAFE_ABORT y cobertura completa de backups, sin intervención sobre sistemas de producción.

**Proveniencia y límites:** conteos y medias calculados mediante SELECT sobre vistas de `SQLite/CU01/weather_local.db` abierta con URI `mode=ro`; estados y eventos consultados por `systemctl`/`journalctl`. No se adjuntan secretos, IP privadas, dumps ni datos de usuarios. Este documento añade evidencia textual sin sobrescribir registros anteriores.
