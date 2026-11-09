# AtmosLink — trazabilidad diaria 2026-11-08 (America/Lima)

**Inspección:** 2026-11-09 00:04–00:12 -05:00 (aproximado), Controlador mediante comandos y consultas SQLite exclusivamente de lectura. **Periodo:** 2026-11-08 00:00–23:59:59 -05:00. Fuente primaria: `SQLite/CU01/weather_local.db` con URI `mode=ro`; journal systemd y estados de unidades/Tailscale. `rpi-sanjose64` visible en Tailscale, pero no se realizó SSH directo: los datos SJ01 son sincronizados en Controlador. No se alteraron RF, PoE, VLAN, servicios, timers ni bases de datos. No se incluyen secretos, IP privadas ni dumps.

## RF e integración científica
- `scientific_campaign_6g_integrated`: **327** registros, **327 LINK_OPERATIONAL_DUAL**, **0 COLLECTION_ERROR**; última fila **2026-11-08T23:35:03-05:00**.
- Frecuencia/ancho registrados: **7000/40 MHz: 325**, **6655/20: 1**, **6475/40: 1**. Las dos observaciones aisladas requieren conciliación con la transición y la estabilidad AP/SM; no son por sí solas tratamientos elegibles.
- Medias sin ceros: RSSI DL/UL **−74.780/−80.623 dBm**, SNR DL/UL **22.443/18.788 dB**.
- Matching dual: **323/327 (98.78%)**; CU01 **323/327**, SJ01 **326/327**; **4** excepciones duales.
- Watermark de referencia **2026-09-15T23:36:42-05:00**: **superado** (última fila indicada).
- Histórico F6655_B20: **1735** filas; **1705** con matching dual; **30** excepciones históricas. **Una fila nueva** del **2026-11-08T12:02:26-05:00** con `cu01_weather_matched=1` y `sj01_weather_matched=1`. El matching de esta nueva fila está confirmado; su elegibilidad experimental NO está confirmada. Mantener vigilancia de filas futuras.

## Meteorología multisitio
Fuente `master_observations_multistation`, por `weather_timestamp_local`:
- **CU01**: **1401** registros, última **23:59:20**; temperatura media **20.01 °C**, HR **60.30 %**, presión **741.54 hPa**, viento **0.29 m/s**.
- **SJ01**: **988** registros, última **23:58:16**; temperatura media **8.67 °C**, HR **91.51 %**, presión **665.24 hPa**, viento **4.61 m/s**.
- La disponibilidad de registros sincronizados no certifica directamente la integridad del almacenamiento local de la Raspberry.

## Throughput
- `active_throughput_6g`: **90** pruebas el 8/11, **90 OK**; **45 DL** con media **72.952 Mbps** y **45 UL** con media **43.176 Mbps**; media conjunta **58.064 Mbps**. Último inicio **11:45:23 -05:00**.
- No se observaron pruebas posteriores a las 11:45:23 en esta tabla para la jornada. No interpretar ausencia como prueba fallida ni mezclar automáticamente con el factorial 3×2.
- `atmoslink-throughput-6g.timer` figura **disabled**; estas pruebas pueden proceder del controlador prospectivo.

## Transiciones e incidente crítico prospectivo
- **P01_S03, 7000 MHz/40 MHz:** `WINDOW_INTENT` **00:00:02**, `TRIAL_ACK` **00:00:03**, `CONFIRM_ACK` **00:00:56**, `WINDOW_VERIFIED` **00:01:23 -05:00**. Inicio analítico previsto **00:31:23**. `SETTLING` seguido de `MONITORING`. Transición operativa confirmada, no validación científica definitiva.
- **P01_S04, 6655 MHz/20 MHz:** `WINDOW_INTENT` y `TRIAL_ACK` **12:00:02**; **CONTROLLER_ERROR 12:03:05**: `Dual target/connectivity not stable before deadline; attempts=60 last_error=SM is not associated with the identified AP`. A las **12:03:06** se observó `HALTED`; persistieron errores del controlador durante la tarde. A partir de **19:33** se observaron estados `EXCLUDED_INCIDENT_WINDOW` repetidos hasta **23:59**. **No consta WINDOW_VERIFIED para P01_S04** en la revisión efectuada.
- **Decisión metodológica:** P01_S04 es ventana incidente/no elegible hasta una auditoría de continuidad y asociación AP/SM. No extrapolar los 90 TCP del segmento anterior a esta ventana. Mantener evidencia del fallo sin modificar ni reintentar la transición desde esta inspección.
- No se atribuye intervención humana concreta sin prueba de autoría. Los eventos de ejecución del controlador son automáticos; las acciones humanas anteriores, si las hubo, requieren revisión independiente.

## Servicios, timers, recuperaciones y seguridad
- `weather-logger`, `atmoslink-radio-config-6g`, `atmoslink-dashboard`, `atmoslink-scheduler` y `atmoslink-event-monitor`: **active** al inspeccionar.
- Timers prospectivo, sincronización remota, validación científica y respaldo remoto: **enabled**. `atmoslink-throughput-6g.timer`: **disabled**.
- Últimos resultados consultados: `luisita-prospective.service` y `atmoslink-remote-sync.service` **success** (ejecuciones recientes, no garantía de ventana elegible); `atmoslink-remote-backup.service` **failed**.
- **Respaldo programado:** el 8/11 falló por cuota de Google Drive, `uploaded=False`, `verified=False` (journal, 07:41:21 UTC). **Recuperaciones posteriores fallidas en destino UNC**: 21:38:54, 22:09:11, 23:12:53 y 23:49:42 -05:00, con copia preservada localmente. No certificar redundancia 2/2.
- Búsqueda acotada de journal para `SAFE_ABORT` y `executor_failure`: sin coincidencias observadas; **no constituye auditoría exhaustiva** de logs especializados.
- **Pendientes:** conciliar la fila F6655_B20 del piloto/transición, investigar las 30 excepciones históricas, revisar la causa de desasociación SM/AP sin cambios operativos en este procedimiento, confirmar elegibilidad de P01_S03, verificar recuperaciones 2/2 y ampliar auditoría de incidentes/acciones humanas.

**Proveniencia y límites:** resumen agregado obtenido de consultas read-only al Controlador el 2026-11-09. La observación de `rpi-sanjose64` en Tailscale no sustituye su inspección directa. Este archivo nuevo preserva el historial documental.
