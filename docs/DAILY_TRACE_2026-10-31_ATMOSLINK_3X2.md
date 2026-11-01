# AtmosLink 3×2 — Consolidación diaria de trazabilidad: 2026-10-31

**Enlace:** CU01 (AP Cuñacales) ↔ SJ01 (SM San José).  
**Ventana auditada:** 2026-10-31 00:00:00–23:59:59, America/Lima (UTC−05:00).  
**Inspección:** 2026-11-01, aproximadamente 00:09–00:13 (-05:00), desde Controlador; consultas exclusivamente de lectura.  
**Clasificación:** fase de línea base posterior al factorial 3×2, más piloto de recuperación y segundo intento de campaña prospectiva de Luisita. No corresponde a un bloque factorial válido.  
**Alcance de seguridad:** la inspección no modificó RF, PoE, VLAN, servicios, timers, bases de datos ni archivos de evidencia en los equipos. Este documento es una síntesis textual apta para el repositorio público; no incluye credenciales, secretos, IP privadas, dumps ni telemetría cruda sensible.

> **INCIDENTE CRÍTICO DEL DÍA:** tras una recuperación y piloto satisfactorios a las 11:24, el arranque real de la prospectiva a las 12:00 falló repetidamente por `max_user_number_reached` en la autenticación del AP. A las **12:10:00** el controlador registró `MISSED_WINDOW_HALT` para **P01_S01** y quedó **HALTED**. No se confirmó una ventana prospectiva válida. El timer continuó activo, generando fallos periódicos del servicio. No atribuir validez experimental a esta jornada.

## 1. RF, frecuencia, ancho y estados de adquisición

**Estado persistente del ejecutor factorial:** `BASE_7000_20`, **7000 MHz / 20 MHz**, fase `BASELINE`, desde el 27/10 a las 00:02:58 (-05:00). `campaign_events.jsonl` del ejecutor factorial no incorporó transiciones fechadas el 31/10. La recuperación prospectiva sí produjo configuraciones RF temporales verificadas, detalladas en §5, que **no** son tratamientos factoriales.

`scientific_campaign_6g_integrated.csv` registra **281 filas** del 31/10; **281/281** tienen `collection_status=LINK_OPERATIONAL_DUAL` y **0** tienen `COLLECTION_ERROR`. El último registro integrado es **2026-10-31T23:24:40-05:00**; el archivo fue modificado a las **23:25:55**. La exportación no alcanza el cierre de medianoche, pese a existir meteorología posterior: **conciliación pendiente**.

Distribución de configuraciones observadas desde el AP: **279 filas 7000/20**, **1 fila 6655/40** (11:16:00, piloto) y **1 fila 7000/40** (11:17:03, piloto). A las **11:22:04**, una fila clasificada `LINK_OPERATIONAL_DUAL` indica **AP 7000/20 frente a SM 6475/20**, con RSSI y SNR igual a cero; debe clasificarse como **discordancia transitoria/QC**, no como estado estable. La fila de **11:17:03** también tiene los cuatro indicadores RSSI/SNR en cero pese al estado operativo. No usar estas filas sin cribado.

Para las **279 filas con configuración AP 7000/20**, promedios **excluyendo ceros no físicos**: RSSI DL **−74.777 dBm**, RSSI UL **−81.241 dBm**, SNR DL **22.313 dB**, SNR UL **17.342 dB**. Estos resúmenes son descriptivos y no sustituyen la depuración de concordancia AP/SM ni la separación del piloto.

## 2. Meteorología CU01/SJ01 — master_observations_multistation

`master_observations_multistation.csv`: **2317 filas** del 31/10, distribuidas en **CU01: 1357** y **SJ01: 960**.

| Indicador (media de registros disponibles) | CU01 | SJ01 |
|---|---:|---:|
| Temperatura | 19.944 °C | 8.531 °C |
| Humedad relativa | 61.568 % | 96.472 % |
| Presión | 740.233 hPa | 664.346 hPa |
| Velocidad de viento | 0.272 m/s | 1.277 m/s |
| Última observación local | 23:59:27 | 23:58:50 |

La última sincronización remota del 31/10 fue satisfactoria a las **23:58:52** (`SJ01 | OK | recibidos=2 | insertados=2 | ignorados=0`). En el Controlador se obtuvo respuesta Tailscale de `rpi-sanjose64` (≈4 ms), pero SSH directo fue **denegado por la política del tailnet**. No se eludió la restricción. Los indicadores SJ01 provienen de registros sincronizados en Controlador, no de una sesión SSH directa.

## 3. Matching meteorológico y watermark científico

En las **281 filas integradas** del día: `cu01_weather_matched=1` en **272/281**, `sj01_weather_matched=1` en **280/281**, y matching dual en **272/281 = 96.80 %**. Se identificaron **9 excepciones**: ocho CU01=0/SJ01=1 a las **00:29:34, 00:54:39, 03:15:25, 03:35:29, 07:16:08, 07:31:11, 11:17:03 y 15:02:44**, y una CU01=0/SJ01=0 a las **23:24:40**. Todas las horas son UTC−05:00. Mantenerlas sin imputación y conciliar la última tras actualizar el integrado.

**Watermark solicitado:** `2026-09-15T23:36:42-05:00`. **Máximo integrado observado:** `2026-10-31T23:24:40-05:00`. **Avance temporal: CONFIRMADO.** Esto no certifica la completitud de las filas del día.

**Control retrospectivo F6655_B20 posterior al watermark:** **1724 filas** hasta `2026-10-18T23:55:49-05:00`; CU01 matched **1694/1724**, SJ01 matched **1724/1724**, dual **1694/1724 = 98.26 %**, **30 excepciones** (16/09: 3; 07/10: 8; 08/10: 9; 17/10: 4; 18/10: 6). **No hubo nuevas filas F6655_B20 el 31/10.** La exigencia de que todas las nuevas filas F6655_B20 tengan `cu01_weather_matched=1` y `sj01_weather_matched=1` **no puede darse por cerrada**: no hay nuevas filas para comprobar y permanecen 30 excepciones históricas. Continuar verificando en cada ejecución, sin modificar originales.

## 4. active_throughput_6g

`active_throughput_6g.csv` contiene **2 pruebas del 31/10, ambas `OK`**, realizadas durante el piloto de recuperación en **6655 MHz / 40 MHz** (una DL y una UL; última prueba iniciada a las **11:16:19**). Goodput medido: **DL 88.411 Mbps**, **UL 44.040 Mbps**; RTT ICMP medio de ambas pruebas **3.345 ms**. El informe local de recuperación identifica estas pruebas como `LUISITA_RECOVERY_PILOT_20261031`, fuera del factorial; el matching meteorológico SJ01 presenta desfases de 136 y 151 segundos, superiores al criterio secundario de 120 segundos. No se relajó ese umbral.

Los timers `andean-throughput.timer` y `atmoslink-throughput-6g.timer` estaban deshabilitados. **No hubo una serie diaria regular de throughput** ni pruebas prospectivas confirmadas después del intento de las 12:00. No transformar la ausencia de mediciones en ensayos fallidos ni usar el par piloto para estimar el efecto factorial.

## 5. Transiciones, incidente crítico y acciones humanas documentadas

**00:00–11:24:** el controlador prospectivo heredado continuó inicialmente en `HALTED` tras el incidente del 30/10. La documentación de recuperación del 31/10 informa una intervención administrativa **previa a esta inspección**: se detectó una lista de búsqueda de 40 MHz vacía en el SM y una lista extensa de 20 MHz. Se ajustaron las listas de búsqueda del SM a las frecuencias del estudio y se ejecutó un piloto controlado con verificación dual y retorno a referencia. Estas fueron **acciones humanas/administrativas observadas retrospectivamente**, no cambios realizados por esta inspección.

**11:15:59–11:24:02:** piloto de seis configuraciones, con readback AP/SM verificado: **6655/40, 7000/40, 6655/20, 6475/40, 6475/20 y 7000/20**. La última confirmó retorno a referencia 7000/20. Las discordancias transitorias observadas en telemetría no constituyen tratamientos estables. El piloto fue documentado como **no factorial**.

**11:24:54:** activación del release prospectivo V2, campaña `LUISITA_PROSPECTIVE_28D_20261031`, ventana planificada 31/10 12:00–28/11 12:00. La validación local previa reportó 19/19 hashes conformes y 21 pruebas aisladas en cada modalidad de Python. **11:25–11:59:** ticks `WAITING_START`.

**12:00:00–12:09:01:** diez intentos consecutivos del servicio prospectivo fallaron por **`Autenticación rechazada por el AP: max_user_number_reached`**. La evidencia acredita rechazo de autenticación/sesiones del AP; **no demuestra aún qué proceso ocupó las sesiones**. No hubo confirmación de la ventana RF ni de una exposición prospectiva válida.

**12:10:00:** `MISSED_WINDOW_HALT` para **P01_S01**; `HALT.json` registra `Missed window start by >600 seconds`. Desde entonces el controlador continuó `HALTED`, con `CONTROLLER_ERROR` repetidos. Al corte del **01/11 00:11**, `STATUS.json` seguía `HALTED` y `luisita-prospective.service` figuraba **failed/exit-code**. El timer seguía **active/enabled**. El informe de recuperación de las 11:27 es evidencia válida de un piloto anterior, **pero no prueba éxito del arranque del mediodía**.

**Decisión metodológica:** no contar el 31/10 como primer día prospectivo válido, no contabilizar P01_S01 como tratamiento confirmado, preservar ambos intentos del 30 y 31/10 y exigir una nueva validación explícita de adquisición, elegibilidad y cronograma antes de aceptar observaciones prospectivas. El diagnóstico del AP requiere revisión de sesiones/concurrencia con acceso autorizado, separada de este procedimiento read-only.

## 6. Servicios, timers, incidentes auxiliares y recuperaciones

Al corte: `atmoslink-dashboard`, `atmoslink-scheduler`, `atmoslink-event-monitor`, `atmoslink-radio-config-6g` y `weather-logger` estaban **active/running**. `atmoslink-remote-sync`, `atmoslink-scientific-validation`, `atmoslink-remote-backup`, `atmoslink-backup-recovery` y `atmoslink-weather-watchdog` estaban **inactive/success**, estado compatible con servicios periódicos. Timers de sincronización, watchdog, validación, respaldo y recuperador **active/enabled**; timers factoriales `andean-campaign` y `andean-throughput`, y el timer independiente de throughput, **inactive/disabled**. **`luisita-prospective.timer` active/enabled**, pero su servicio **failed**, incidente no resuelto.

**Sincronización SJ01:** **20 fallos de ejecución** del servicio, con eventos de timeout; última sincronización correcta **23:58:52**. No confundir fallos intermitentes del proceso con ausencia total de meteorología.

**Logger CU01:** **11 recuperaciones automáticas** de `weather-logger.service` por falta de datos frescos; cada una reportó posterior estado `active`. Ocho excepciones CU01 del integrado anteceden recuperaciones del watchdog en pocos minutos. **Asociación temporal, no causalidad demostrada**; se requiere confrontar la edad de medición, los límites de matching y los timestamps de reinicio. La novena excepción, de las 23:24:40, requiere conciliación con el export actualizado.

**Validación científica:** **24 ejecuciones horarias** el 31/10 con `CU01: OK` y `SJ01: OK`; última a las **23:49:47**. El resultado del validador no reemplaza el cribado de matching ni la validación del arranque prospectivo.

**Backup programado:** copia local consistente de las **02:30:55**, subida y **verificada en ambos destinos** a las **02:39:52**. **Recuperador:** **9 ejecuciones fallidas** durante el día, pero se verificó en ambos destinos la copia `backup_CU01_20261031_183950.zip` (generada a las 18:39:50) a las **23:53:40**, con `RECOVERY COMPLETE 2/2`. Esto **no** demuestra conciliación de toda la cola histórica ni que exista un respaldo de las últimas observaciones del día.

## 7. SAFE_ABORT, executor_failure y alcance de ausencia de eventos

No se encontraron nuevos `SAFE_ABORT`, `executor_failure`, `SWITCH_FAILED` ni rollbacks del **ejecutor factorial** fechados el 31/10 en `campaign_events.jsonl`, cuyo último cambio corresponde al cierre del 27/10. **Sí** existen los eventos críticos de la **prospectiva** `CONTROLLER_ERROR` (autenticación del AP y posteriores rechazos por HALTED) y **`MISSED_WINDOW_HALT` a las 12:10**. No equiparar la ausencia de `SAFE_ABORT` factorial con ausencia de incidentes operativos. No se verificó directamente el journal de SJ01 por la política de SSH; las conclusiones de ausencia se limitan a las fuentes inspeccionadas.

## 8. Reglas de integridad y procedencia

Separar estrictamente: **(a)** factorial 3×2 finalizado el 27/10; **(b)** línea base posterior 7000/20; **(c)** piloto de recuperación del 31/10, excluido de inferencia; **(d)** arranque prospectivo fallido, sin exposición confirmada. Preservar las observaciones con RSSI/SNR cero, las discordancias AP/SM y los errores de matching como **marcas QC**, no corregirlas en origen. Evitar pseudorreplicación, imputación automática, mezcla de fases y atribuciones causales no verificadas. La existencia de filas `LINK_OPERATIONAL_DUAL` no implica por sí sola una exposición experimental elegible.

**Fuentes consultadas en Controlador, solo lectura:** `Data/exports/scientific_campaign_6g_integrated.csv` (mod. 31/10 23:25:55), `Data/exports/master_observations_multistation.csv` (mod. 01/11 00:07:29), `Data/exports/active_throughput_6g.csv` (mod. 31/10 11:16:33); `campaign_runtime/campaign_state.json` y `campaign_events.jsonl`; `prospective_runtime/HALT.json`, `STATUS.json`, `events.jsonl`; `prospective_28d/recovery_20261031/RECOVERY_REPORT.md`, `PILOT_PASSED.json`; `prospective_28d/field_v2/DEPLOYMENT.json` y `VALIDATION.json`; `systemctl`, `journalctl`, `tailscale ping` y prueba SSH denegada. La inspección terminó aproximadamente el **01/11 00:13 (-05:00)**.

**Trazabilidad cruzada:** [Consolidación del 30/10 — primer intento prospectivo fallido](DAILY_TRACE_2026-10-30_ATMOSLINK_3X2.md). El incidente del 31/10 es **distinto**: recuperación/piloto inicialmente satisfactorios, seguidos de rechazo de autenticación del AP al inicio real y HALT por ventana vencida.

**Estado documental:** archivo nuevo, sin sobrescribir informes anteriores; únicamente resumen textual sanitario para GitHub. La operación de documentación no implica autorización para modificar la campaña.
