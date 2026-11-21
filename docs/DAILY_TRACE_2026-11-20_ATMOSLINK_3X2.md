# AtmosLink — trazabilidad general y control meteorológico — 2026-11-20

**Corte de observación:** 2026-11-20 23:46–23:48 America/Lima. **Alcance:** seguimiento de laboratorio posterior al cierre de la campaña factorial 3×2 (28-10-2026), NO una nueva adquisición factorial ni evaluación de elegibilidad prospectiva de Luisita. Inspección operativa exclusivamente read-only mediante Desktop Commander en Controlador y equipo físico SJ01 identificado por hostname `rpi-cunacales` (alias histórico `rpi-sanjose64`). No se cambió configuración RF, PoE, VLAN, scripts, timers, servicios ni bases.

## RF e integración

Fuente: SQLite de producción de Controlador `SQLite/CU01/weather_local.db`, conexión SQLite URI `mode=ro`; filtro de `rf_timestamp_local` por fecha local 2026-11-20.

- `scientific_campaign_6g_integrated`: **371** observaciones; **371 LINK_OPERATIONAL_DUAL**; **0 COLLECTION_ERROR**. Escenarios observados: **6655 MHz / 40 MHz: 182**, **7000 MHz / 20 MHz: 189**. No atribuir estas observaciones a una repetición factorial 3×2.
- 6655/40: RSSI DL/UL medios −76.91/−81.44 dBm; SNR DL/UL 22.62/19.81 dB. 7000/20: RSSI −74.04/−80.35 dBm; SNR 22.65/17.66 dB.
- Último watermark integrado observado: **2026-11-20T23:30:37-05:00**, posterior a la referencia **2026-09-15T23:36:42-05:00**: **avance confirmado**.
- Matching meteorológico dual del día: **358/371**; **13** observaciones sin coincidencia dual.
- Histórico de registros 6655 MHz/20 MHz (criterio operativo F6655_B20): **2111** filas; **2066** con `cu01_weather_matched=1` y `sj01_weather_matched=1`; **45** excepciones acumuladas; **0** nuevas filas de ese escenario fechadas el 20-11. Por ello la comprobación de nuevas filas sigue abierta, y no debe declararse cumplida retroactivamente.
- `active_throughput_6g`: **90 DL OK** (media 61.870 Mbps) y **89 UL OK** (media 31.755 Mbps), **179/179 OK**.
- `master_observations_multistation`: **1321** filas CU01, temperatura media 21.30 °C, humedad media 60.69%, último 23:42:55; **927** filas SJ01, temperatura media 10.34 °C, humedad media 91.37%, último 23:41:56 (hora local).

## Clima externo: seis controles y contraste previo

Fuente **verificada en SQLite local del Controlador**, NO verificada dentro del ZIP de Google Drive:

| Serie | CU01 | SJ01 | MID_LINK | Cambio respecto al control del 19-11 |
|---|---|---|---|---|
| NASA POWER | 2026-11-18 18:00 -05 | 2026-11-18 18:00 -05 | 2026-11-18 18:00 -05 | +1 día en las tres series (anterior 2026-11-17) |
| ERA5-Land | 2026-10-09 23:00 -05 | 2026-10-09 23:00 -05 | 2026-10-09 23:00 -05 | Sin avance (anterior 2026-10-09) |

No hay discrepancia entre sitios dentro de cada fuente. **Anomalía abierta:** ERA5-Land presenta atraso persistente; comprobar pipeline incremental, origen y respaldos antes de atribuir causalidad. Se localizó en Google Drive la carpeta `AtmosLink_Backups` y su subcarpeta `CU01/field`, pero la búsqueda no recuperó el ZIP `backup_CU01_20261120_204409.zip`; por tanto no se certifican desde el respaldo remoto las seis fechas ni la integridad interna del ZIP.

## Servicios, incidentes y recuperación

- Controlador: `atmoslink-remote-backup.service` en estado **failed**; error a las **02:43:02–02:43:03** por **Google API 403 rateLimitExceeded** en destinos primario y UNC; `uploaded=False`, `verified=False` en ese intento.
- `atmoslink-backup-recovery.service`: falló una ejecución a las **23:00:57**; ejecución posterior **23:32:42** verificó por logs el archivo `backup_CU01_20261120_204409.zip` (**307472796 bytes**) en ambos destinos y declaró **RECOVERY COMPLETE 2/2**. Esto acredita el resultado del recuperador, **no** la inspección directa del contenido ZIP en Drive.
- `atmoslink-scientific-validation.service`: incidente a las **14:30:30–14:30:42**, **sqlite3.OperationalError: database is locked** al intentar regenerar `scientific_hourly_validation`; CU01 terminó con error. Requiere seguimiento, sin intervención operativa.
- `tailscale-serve-ap.service` en **failed** al corte; `weather-logger-sj01.service` **active** en SJ01; sin unidades systemd fallidas en SJ01.
- SJ01: avisos seriales de fragmentos no UTF-8 a las **23:42:56, 23:44:56 y 23:46:56**, intercalados con recepción válida y almacenamiento a las **23:43:56 y 23:45:56**. No confundir descartes de fragmentos con interrupción total del sensor.
- Timers observados programados: `atmoslink-remote-sync.timer`, `atmoslink-weather-watchdog.timer`, `atmoslink-backup-recovery.timer`, `atmoslink-scientific-validation.timer` y `atmoslink-remote-backup.timer`.
- **No auditado exhaustivamente**: búsquedas de `SAFE_ABORT`, `executor_failure`, todas las transiciones y acciones humanas; no afirmar ausencia de tales eventos. No se identificó en esta inspección una acción humana correctiva acreditada. La vigilancia prospectiva de Luisita se mantiene documental y metodológicamente separada.

## Decisiones metodológicas y límites

Preservar datos brutos y excepciones sin reparación retrospectiva; mantener las 45 excepciones F6655_B20 como incidencias de calidad, diferenciar los 13 casos de matching dual del día (todos los escenarios) del histórico F6655_B20. El watermark integrado avanzó, pero ello no prueba matching universal. Separar verificación local de SQLite, verificación por logs de backup y comprobación directa de contenido en Google Drive. Este informe documenta evidencia observable; no infiere causas ni certifica una ejecución de campaña factorial cerrada.

**Procedencia:** consultas read-only SQLite, systemctl/journalctl en Controlador y SJ01, y búsquedas de metadatos en Google Drive. Timestamps America/Lima, salvo indicación contraria. No se incluyen secretos, credenciales, IP privadas, volcados de bases de datos ni datos personales.
