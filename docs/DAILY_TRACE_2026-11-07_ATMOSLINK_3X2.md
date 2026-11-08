# AtmosLink — trazabilidad diaria 2026-11-07 (America/Lima)

**Inspección:** 2026-11-08 00:45–00:51 -05:00, Controlador (consultas de solo lectura). **Alcance:** jornada local 2026-11-07 00:00–23:59:59. Fuente: SQLite CU01 consultada con URI `mode=ro`, journal de systemd y estado Tailscale. No se modificaron configuraciones, servicios, timers ni bases de datos. No se accedió directamente por SSH a rpi-sanjose64; SJ01 se contrastó con datos sincronizados en Controlador. Este documento no contiene credenciales, IP privadas ni dumps.

## RF e integración científica
- `scientific_campaign_6g_integrated`: **377** observaciones del día; **377 LINK_OPERATIONAL_DUAL**, **0 COLLECTION_ERROR**; última `2026-11-07T23:59:21-05:00`.
- Configuraciones registradas: **6655 MHz/40 MHz: 188**; **7000 MHz/20 MHz: 189**. No atribuir automáticamente todos los registros a ventanas elegibles sin comprobar criterios de asentamiento y medidas.
- Medias RF (excluyendo ceros): RSSI DL/UL **−75.127/−80.767 dBm**, SNR DL/UL **23.313/18.952 dB**.
- Matching meteorológico dual **370/377 (98.14%)**; **7 excepciones**. El matching no equivale a elegibilidad científica completa.
- Watermark histórico `2026-09-15T23:36:42-05:00`: **superado**, última observación arriba indicada.
- Histórico F6655_B20: **1734** filas, **1704** matching dual; **30** excepciones. No hubo nuevas filas F6655_B20 el 7/11. La última nueva fila observada (2026-11-06 13:54:53 -05:00) tenía `cu01_weather_matched=1` y `sj01_weather_matched=1`. La comprobación de todas las futuras filas F6655_B20 sigue abierta.

## Meteorología
Fuente `master_observations_multistation`, filtrada por `weather_timestamp_local`:
- **CU01:** 1366 filas; última 23:59:10 -05:00; temperatura media 19.29 °C; humedad 62.01%; presión 740.80 hPa; viento 0.23 m/s.
- **SJ01:** 964 filas; última 23:59:13 -05:00; temperatura media 9.00 °C; humedad 89.82%; presión 664.75 hPa; viento 2.24 m/s.
- Tailscale mostró `rpi-sanjose64` presente. No se ha certificado mediante inspección directa de su almacenamiento local.

## Throughput
`active_throughput_6g`: **180** pruebas del día, **180 status=OK**, media de `measured_throughput_mbps` **56.346 Mbps** (agregada, no separada por dirección); última prueba iniciada `2026-11-07T23:45:25-05:00`. No mezclar esta media con un contraste factorial sin segmentación por dirección, escenario y elegibilidad.

## Transiciones prospectivas (críticas; journal)
- **P01_S01**, 6655/40: `WINDOW_INTENT` 00:00:02, `TRIAL_ACK` 00:00:03, `CONFIRM_ACK` 00:01:18, `WINDOW_VERIFIED` **00:01:45 -05:00**; `analysis_start` 00:31:45.
- **P01_S02**, 7000/20: `WINDOW_INTENT` 12:00:02, `TRIAL_ACK` 12:00:03, `CONFIRM_ACK` 12:00:55, `WINDOW_VERIFIED` **12:01:21 -05:00**; `analysis_start` 12:31:21.
- Se observaron estados `SETTLING` y `MONITORING`. Las dos transiciones están **operativamente verificadas**, no se declara por ello validación científica definitiva de las ventanas. No se atribuye acción humana sin evidencia de autor/orden.

## Servicios, incidentes y respaldos
- Timer de sincronización remota y validación científica: habilitados; últimas ejecuciones de sincronización y validación observadas como satisfactorias. Timer prospectivo presente. La inspección no constituye inventario exhaustivo de todas las unidades.
- **Incidente de respaldo:** `atmoslink-remote-backup` falló por cuota el 7/11 (registro 07:51:44 UTC: `uploaded=False, verified=False`).
- **Recuperación parcial posterior:** registro del 8/11 04:49:36 UTC verificó copia en destino primario; 04:50:50 UTC falló la subida al destino UNC y preservó copia local. **No está confirmada la redundancia 2/2**. Estos dos registros posteriores se incluyen como seguimiento del incidente, no como eventos ocurridos el 7/11 local.
- En la revisión acotada no se obtuvo confirmación de nuevos `SAFE_ABORT` o `executor_failure`; no se declara ausencia exhaustiva.
- No se identificaron acciones humanas atribuibles con seguridad en las fuentes resumidas.

## Decisiones metodológicas y pendientes
1. Tratar P01_S01 y P01_S02 como ventanas con transición RF verificada, pero exigir evaluación de elegibilidad de cada exposición (asentamiento, throughput, meteorología dual y continuidad).
2. Mantener identificadas las 7 excepciones de matching del día y las 30 históricas F6655_B20; no rellenar ni imputar mediciones.
3. Mantener incidente de respaldo UNC abierto hasta verificar copia 2/2.
4. Mantener auditoría exhaustiva de `SAFE_ABORT`, `executor_failure`, eventos especializados y acciones humanas como pendiente; la inspección de journal fue acotada.

**Proveniencia:** consultas read-only al Controlador, realizadas el 2026-11-08; resumen agregado sin material sensible. Este informe se añade como archivo nuevo, sin sobrescribir evidencia histórica.
