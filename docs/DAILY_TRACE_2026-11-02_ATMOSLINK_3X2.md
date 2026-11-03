# AtmosLink 3×2 — trazabilidad diaria 2026-11-02 (America/Lima)

**Corte operativo:** 2026-11-02 23:53 -05:00. **Origen:** consultas read-only en Controlador, exportaciones CSV y journalctl/systemctl; sin acceso directo a rpi-sanjose64 (Tailscale indica offline desde ~4 h). Datos del día **provisionales** hasta cierre y resincronización SJ01. La campaña factorial de 42 días terminó el 27 de octubre; las mediciones actuales corresponden a la campaña prospectiva y a la línea base, no deben agregarse sin estratificación al factorial.

## RF y configuración
scientific_campaign_6g_integrated.csv: **349** filas del 02/11, **307 LINK_OPERATIONAL_DUAL**, **42 COLLECTION_ERROR**. Configuración AP registrada: **187 a 6655 MHz/40 MHz**, **120 a 7000 MHz/20 MHz**, **42 sin metadatos RF** (errores). Última fila RF: **23:13:26 -05:00**. Promedios sobre valores numéricos presentes (no estimación de disponibilidad): DL/UL RSSI **−78.127/−81.954 dBm**, DL/UL SNR **20.593/18.130 dB**. Los 42 errores comienzan a las **19:44:35 -05:00**; requieren investigación de pérdida de acceso/telemetría y no prueban por sí solos caída física de enlace. La coexistencia de configuraciones exige separar por ventanas verificadas, sin inferir automáticamente transiciones exitosas a partir de frecuencia observada.

## Throughput TCP activo
active_throughput_6g.csv: **144** pruebas, **143 OK y 1 ERROR**; 72 DL y 72 UL. Goodput promedio entre pruebas OK: **51.049 Mbps DL**, **22.528 Mbps UL**. Última prueba **19:30:24 -05:00**. No imputar mediciones ausentes tras esa hora como fallos TCP; revisar relación temporal con la pérdida de conectividad y distinguir estado de la ventana prospectiva.

## Meteorología multisitio
master_observations_multistation.csv: **CU01 1336** filas (última **23:46:01**); temperatura media **19.086 °C**, HR **67.848 %**, presión **740.431 hPa**, viento **0.219 m/s**. **SJ01 778** filas (última **19:38:56**); temperatura **9.113 °C**, HR **95.181 %**, presión **664.234 hPa**, viento **2.216 m/s**. Son medias descriptivas de filas presentes, no de muestreo completo. El servicio de sincronización remota registra **No route to host** hacia SJ01 y terminó en estado failed; los datos SJ01 posteriores a 19:38:56 no están disponibles en el export revisado. Tailscale reporta rpi-sanjose64 **offline** (última conexión hace ~4 h); no se eludió el control de acceso.

## Integración y emparejamiento
scientific_campaign_6g_integrated.csv contiene filas posteriores al watermark **2026-09-15T23:36:42-05:00** (avance temporal confirmado por última fila 2026-11-02T23:13:26-05:00). Para el 02/11: **302/349 matching dual**, 5 CU01=0/SJ01=1, 37 CU01=1/SJ01=0, 5 ambos=0; **47 excepciones**. No reinterpretar los indicadores como causalidad ni corregir manualmente.
F6655_B20 histórico: **1733 filas**, **1703** con ambos indicadores =1, **30** con CU01=0/SJ01=1; última fila F6655_B20 **2026-11-01T17:33:42-05:00**. **No hubo nuevas filas F6655_B20 el 02/11**. La validación de *nuevas filas* con cu01_weather_matched=1 y sj01_weather_matched=1 permanece como control continuo, sin observaciones nuevas hoy; las 30 excepciones históricas siguen abiertas. No se modificó ni imputó información.

## Servicios, timers e incidentes
Al corte: atmoslink-dashboard, atmoslink-event-monitor, atmoslink-scheduler, atmoslink-radio-config-6g y weather-logger **active**; atmoslink-remote-sync y atmoslink-remote-backup **failed**. Timers luisita-prospective, atmoslink-remote-sync, atmoslink-weather-watchdog, atmoslink-scientific-validation, atmoslink-backup-recovery y atmoslink-remote-backup estaban programados. Watchdog de weather-logger reportó **OK** a las **23:53:08**, última medición CU01 **23:53:01** (fuente journal); no equivale a certificar SJ01.

**Incidente crítico:** pérdida de ruta SSH hacia la estación remota SJ01, simultánea a 42 errores de recolección RF desde 19:44. El controlador prospectivo registró **CONTROLLER_ERROR 23:45:03 -05:00**, al fallar SSH hacia el SM, y la unidad luisita-prospective.service falló en esa ejecución; las siguientes ejecuciones devolvieron MONITORING. No atribuir continuidad RF, recuperación física ni validez de ventanas sin confirmación adicional.

**Respaldo:** atmoslink-remote-backup falló por cuota/rateLimitExceeded (registro de 02/11). El recuperador reportó **RECOVERY COMPLETE 2/2** para una copia de las **18:53:32** a las **23:49:57 -05:00**; esto verifica esa copia, no toda la cola ni la copia más reciente.

**SAFE_ABORT/executor_failure:** no se dispone de evidencia positiva de nuevos eventos bajo esas etiquetas en las fuentes aquí examinadas; la ausencia de una auditoría exhaustiva de todos los registros no permite certificar cero eventos. El evento CONTROLLER_ERROR sí está confirmado. **Acciones humanas:** no se atribuyeron cambios manuales de RF ni servicios a partir de estas consultas; la inspección fue solo lectura.

## Decisiones metodológicas y pendientes
1. Mantener separados factorial 3×2 cerrado, línea base y campaña prospectiva.
2. Marcar las 42 observaciones COLLECTION_ERROR y las 47 excepciones de matching como QC pendiente, sin imputación.
3. No considerar las ventanas prospectivas afectadas como válidas hasta verificar conectividad dual, estado RF confirmado, throughput y matching climático.
4. Revisar cronología de caída SJ01, eventos de controlador y retorno de sincronización; reconciliar exportaciones tras restablecimiento autorizado.
5. Conservar como pendiente la resolución de las 30 excepciones históricas F6655_B20 y confirmar matching dual de cada nueva fila futura.
6. Verificar en seguimiento posterior SAFE_ABORT/executor_failure y transiciones en logs completos, así como integridad y cobertura de respaldos.

**Seguridad:** solo evidencia textual agregada, sin IP internas, credenciales, dumps ni datos personales; no se cambiaron RF, PoE, VLAN, servicios, timers o bases de datos.