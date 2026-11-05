# AtmosLink 3×2 — trazabilidad diaria 2026-11-04 (America/Lima)

**Inspección:** 2026-11-05 00:05–00:10 -05:00, Controlador; consultas read-only. **Periodo:** 2026-11-04 00:00–23:59:59 -05:00. **Clasificación:** fase posterior a la campaña factorial 3×2, no nueva exposición factorial. Los resultados corresponden a las exportaciones disponibles al momento de la inspección, que pueden tener rezago.

## RF y escenario

Fuente: `Data/exports/scientific_campaign_6g_integrated.csv` del Controlador, filtrada por `rf_timestamp_local`. **276 observaciones**, todas `LINK_OPERATIONAL_DUAL`; **0 `COLLECTION_ERROR`** en el subconjunto. **7000 MHz / 20 MHz** en 276/276 observaciones; escenario operativo de línea base **BASE_7000_20** (etiqueta inferida de la configuración y del historial, no de un campo de escenario en el CSV). RSSI medio DL/UL **−73.862/−80.192 dBm**; SNR medio DL/UL **23.152/18.301 dB**, excluyendo ceros y usando filas `LINK_OPERATIONAL_DUAL`. Última fila RF del día **2026-11-04T23:02:09-05:00**. No confundir el límite de la exportación con una pérdida física de enlace.

## Meteorología CU01/SJ01

Fuente: `Data/exports/master_observations_multistation.csv`, filtrada por `weather_timestamp_local`. **2319 filas**: CU01 **1350**, SJ01 **969**. CU01: temperatura **19.973 °C**, humedad **62.854 %**, presión **740.317 hPa**, viento **0.272 m/s**; última fila **23:58:30 -05:00**. SJ01: temperatura **9.358 °C**, humedad **93.679 %**, presión **664.496 hPa**, viento **2.604 m/s**; última fila **23:58:03 -05:00**. Promedios de valores no vacíos. `rpi-sanjose64` visible en Tailscale; acceso SSH directo rechazado por política de tailnet, sin evasión. La evidencia SJ01 es la sincronizada en Controlador; no hay inspección directa del equipo.

## Throughput

Fuente: `Data/exports/active_throughput_6g.csv`: **0 filas del 2026-11-04**; última prueba de toda la exportación **2026-11-02T19:30:24-05:00**. No se imputan mediciones ni se consideran fallos TCP inexistentes. `andean-throughput.service` tenía resultado de última ejecución `success` pero ello no demuestra adquisición efectiva. La ausencia de pruebas constituye discontinuidad documental/operativa.

## Integración científica y validación pendiente

`scientific_campaign_6g_integrated.csv`: **276 filas** el 4 de noviembre; **268/276 (97.10 %) matching dual**, **8 excepciones CU01**, **0 excepciones SJ01**. Última fila **2026-11-04T23:02:09-05:00**, posterior al watermark **2026-09-15T23:36:42-05:00**: **avance confirmado en la exportación**. Para **F6655_B20** en el histórico exportado: **1733 filas**, **1703 matching dual**, **30 excepciones**; última fila de ese escenario **2026-11-01T17:33:42-05:00**; **0 filas nuevas F6655_B20 el 4 de noviembre**. Por tanto la exigencia `cu01_weather_matched=1` y `sj01_weather_matched=1` para nuevas filas queda **pendiente de validación prospectiva**; las 30 excepciones históricas no están resueltas. No modificar ni rellenar retrospectivamente.

## Servicios, timers, incidentes y recuperaciones

Inspección de `systemctl show` y `systemctl list-timers --all` a las 00:05–00:07 del 5 de noviembre: `weather-logger.service` **active/success**; `atmoslink-remote-sync.service` **inactive/success**; `atmoslink-remote-backup.service` **failed/exit-code 1**; `atmoslink-backup-recovery.service` **failed/exit-code 3**; `atmoslink-scientific-validation.service` **inactive/success**; `atmoslink-weather-watchdog.service` **inactive/success**; `luisita-prospective.service` **failed/exit-code 1**; `andean-throughput.service` **inactive/success**. Timers observados: prospectivo, recuperación de respaldos, validación científica, respaldo remoto, sincronización y watchdog (los dos últimos pueden aparecer sin próxima hora por su programación). El diario de sincronización incluyó mensajes de fallo/timeout; un recuento por coincidencias de texto dio **30**, no necesariamente 30 ejecuciones distintas.

**Incidente persistente:** el controlador prospectivo continuó **HALTED**; a **2026-11-04 23:56–23:59 -05:00** emitió `CONTROLLER_ERROR` y fallos de `luisita-prospective.service` por estado HALTED. No confundir los reintentos por minuto con transiciones independientes ni declarar ventanas experimentales válidas. **Respaldo:** a **2026-11-04 23:54:52 -05:00** el recuperador confirmó una copia del 4 de noviembre en el destino primario y registró fallo de subida al destino UNC, preservando copia local. Redundancia dual de esa copia **no confirmada**.

No se observó evidencia positiva de nuevas transiciones RF, `SAFE_ABORT` ni `executor_failure` en las fuentes consultadas; esto **no equivale a auditoría exhaustiva** de todos los registros estructurados. No se atribuyeron acciones humanas nuevas sin registro positivo. El escenario 7000/20 se mantiene como línea base; no incorporar mediciones de línea base ni pilotos a las 18 exposiciones factoriales. Las ocho excepciones meteorológicas requieren conciliación temporal, sin inferir causalidad.

## Procedencia, límites y seguridad

Se consultaron exportaciones CSV, metadatos systemd, temporizadores, journal y Tailscale desde **Controlador**, sin cambios operativos ni escrituras en las bases. SSH a SJ01 fue denegado por política. Este documento contiene solo agregados y marcas temporales, sin credenciales, direcciones privadas, volcados de bases ni registros brutos sensibles. La única escritura autorizada es este nuevo documento en GitHub.