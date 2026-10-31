# AtmosLink 3×2 — Consolidación diaria de trazabilidad: 2026-10-30

**Enlace:** CU01 (AP Cuñacales) ↔ SJ01 (SM San José).  
**Ventana:** 2026-10-30 00:00:00–23:59:59, America/Lima (UTC−05:00).  
**Inspección:** 2026-10-31, aproximadamente 00:09–00:13 (-05:00); los tres exports se consultaron en Controlador.  
**Modalidad:** consultas operativas de solo lectura. No se modificaron RF, PoE, VLAN, servicios, timers, bases de datos ni archivos de evidencia. La escritura de este informe Markdown en GitHub es la única acción documental autorizada.

> **Separación de fases:** el factorial 3×2 terminó el 27/10. El 30/10 corresponde a línea base posterior, con un intento fallido de inicio de la campaña prospectiva de 28 días. **No incluir este día como un bloque factorial ni contabilizar el intento prospectivo como exposición confirmada.**

## 1. RF, escenario, frecuencia y ancho

El estado persistente de la campaña 3×2 conserva **BASE_7000_20, 7000 MHz / 20 MHz, secuencia FINAL_BASELINE**, aplicada el 27/10 a las 00:00 (-05:00). No hay eventos nuevos del ejecutor factorial el 30/10; el último evento estructurado es `SWITCH_COMMITTED=OK` del 27/10 a las 00:02:58 (-05:00).

`scientific_campaign_6g_integrated.csv` contiene **288 filas** del 30/10, de **00:00:59** a **23:59:27**:
- **286 `LINK_OPERATIONAL_DUAL`** con configuración 7000 MHz / 20 MHz y concordancia AP/SM en las observaciones operativas.
- **2 `COLLECTION_ERROR`** a las **12:01:04** y **12:06:19**; el mensaje señala fallo de acceso SSH al equipo RF (`No route to host`). **No demostrar una caída física del enlace a partir de este error instrumental.**

Promedios calculados únicamente sobre las 286 filas operativas con valores RF no nulos:

| Variable | Media | Mínimo | Máximo |
|---|---:|---:|---:|
| RSSI DL | −74.455 dBm | −77 | −73 |
| RSSI UL | −81.073 dBm | −83 | −80 |
| SNR DL | 22.619 dB | 20 | 24 |
| SNR UL | 17.430 dB | 15 | 19 |

Última observación operativa, **23:59:27**: RSSI DL/UL **−76/−82 dBm**; SNR DL/UL **21/17 dB**; MCS codificado DL/UL **204/202**; AP/SM TX **10/3 dBm**. Los códigos MCS son nominales, no una escala comparable sin normalización entre firmwares.

## 2. Meteorología — master_observations_multistation

**2301 filas** del 30/10: **CU01 1340** y **SJ01 961**. Última observación de ambas estaciones: **23:59:47**.

| Métrica (media de registros disponibles) | CU01 | SJ01 |
|---|---:|---:|
| Temperatura | 20.556 °C | 8.875 °C |
| Humedad relativa | 60.170 % | 94.375 % |
| Presión | 740.274 hPa | 664.228 hPa |
| Viento | 0.321 m/s | 1.226 m/s |
| Temperatura mínima–máxima | 16.11–29.25 °C | 5.98–15.08 °C |

La sincronización remota terminó con `Status global: OK` a las **23:58:00**; la última ejecución observada en la inspección, ya el 31/10 a las **00:08:07–00:08:09**, también finalizó correctamente.

`rpi-sanjose64` respondió a **Tailscale ping** el 31/10 a las **00:11:27** (~5 ms), pero el acceso SSH directo fue **denegado por la política del tailnet**. No se eludió el control. Los datos SJ01 proceden de la sincronización hacia Controlador y **no constituyen auditoría local directa de la Raspberry**.

## 3. Rendimiento — active_throughput_6g

El export del 30/10 contiene **16/16 pruebas OK**, **8 DL y 8 UL**, desde **00:00:04** hasta **01:45:19**. Última modificación del CSV: **01:45:31**. No se registraron pruebas posteriores en ese export durante el resto del día.

| Indicador (solo pruebas OK) | DL | UL |
|---|---:|---:|
| Pruebas | 8 | 8 |
| Goodput medio | **44.054 Mbps** | **31.229 Mbps** |
| Goodput mínimo–máximo | 43.769–44.212 Mbps | 29.622–32.245 Mbps |
| Retransmisiones TCP medias | 46.750 | 29.875 |
| RTT ICMP medio | 6.402 ms | 6.402 ms |
| Goodput cero | 0 | 0 |

**Discontinuidad instrumental con causa administrativa documentada:** el 30/10 a las **01:59:06**, durante la instalación del controlador prospectivo, se detuvo y deshabilitó `atmoslink-throughput-6g.timer`. También se detuvieron/deshabilitaron `andean-campaign.timer` y `andean-throughput.timer`. La falta de pruebas posteriores **no debe imputarse como caída de throughput RF ni como 176 pruebas fallidas**. Las 16 pruebas son mediciones de línea base, no tratamientos factoriales.

`andean-throughput.service` tuvo dos ejecuciones satisfactorias (00:05 y 01:05) que declararon `Sin medición formal: fuera de fase EXPERIMENT`. No se interpretan como corrección retroactiva de errores de otros días.

## 4. Watermark y matching meteorológico

**Watermark de referencia:** `2026-09-15T23:36:42-05:00`.  
**Máximo integrado observado:** `2026-10-30T23:59:27-05:00`.  
**Avance temporal: CONFIRMADO** (export modificado el 31/10 a las 00:01:37).

Matching en las **288 filas del 30/10**:
- `cu01_weather_matched=1`: **277/288**.
- `sj01_weather_matched=1`: **287/288**.
- Ambos: **277/288 = 96.18 %**.
- **11 excepciones**: diez con CU01=0/SJ01=1 (**01:21:13, 01:31:15, 01:56:19, 07:05:08, 09:00:28, 09:10:30, 13:11:32, 19:43:16, 20:03:25 y 23:39:24**) y una con **ambos=0** a las **23:59:27**. No imputar ni eliminar; la última puede requerir conciliación por actualización posterior del join.

**Validación F6655_B20, desde el watermark:** **1724 filas**, última **2026-10-18T23:55:49-05:00**. CU01 matched **1694/1724**; SJ01 matched **1724/1724**; dual **1694/1724 = 98.26 %**. **30 excepciones** por día: 16/09 (3), 07/10 (8), 08/10 (9), 17/10 (4), 18/10 (6). **Nuevas filas F6655_B20 el 30/10: cero**. Por tanto, el requisito de que todas las nuevas filas F6655_B20 tengan ambos flags iguales a 1 **sigue pendiente de confirmación** y el histórico no alcanza el 100 %. La ausencia de filas nuevas no valida la condición por vacuidad.

## 5. Servicios, timers, watchdog y sincronización

En la inspección estaban **activos** `atmoslink-dashboard`, `atmoslink-scheduler`, `atmoslink-event-monitor`, `atmoslink-radio-config-6g` y `weather-logger`. Las unidades periódicas `atmoslink-remote-sync`, `atmoslink-weather-watchdog`, `atmoslink-scientific-validation` y `atmoslink-backup-recovery` estaban `inactive/success` tras su última ejecución, comportamiento normal para servicios one-shot. Permanecían programados los timers de sincronización, watchdog, validación científica, backup y recuperación. El timer `luisita-prospective.timer` estaba **enabled/active**, pero su controlador quedó **HALTED** (véase §6). Los tres timers de campaña/throughput antes citados estaban **disabled/inactive** después de las 01:59:06.

**Watchdog meteorológico:** **15 eventos `RECUPERACIÓN AUTOMÁTICA`** de `weather-logger.service` (00:57:54, 01:12:05, 01:24:20, 01:34:31, 02:00:57, 07:09:53, 09:03:42, 09:13:52, 11:11:43, 11:56:23, 13:13:39, 17:52:00, 19:45:57, 20:06:17 y 23:43:46). En los diez casos CU01=0/SJ01=1, la excepción precedió a una recuperación posterior del watchdog por aproximadamente **2–5 minutos**. Es una **asociación temporal observacional**, no evidencia causal suficiente; contrastar frescura del logger y ventana del join.

**Sincronización remota:** **16 ejecuciones con resultado `timeout`** en systemd y registros adicionales de `Status global: ERROR`. Se observaron ejecuciones posteriores `OK`, incluida la de las 23:58:00. Un resultado final satisfactorio no elimina las interrupciones intermedias.

**Validación científica:** el servicio terminó el 30/10 a las **23:47:19** con `CU01: OK` y `SJ01: OK`. Esto no equivale a matching dual del 100 %.

## 6. Incidente crítico: transición administrativa y controlador prospectivo

**Acción administrativa registrada, ajena a esta inspección:** el journal de Controlador muestra el **30/10 a las 01:59:05** una ejecución de `install.sh` mediante `sudo` bajo la cuenta `carlos`. La instalación detuvo/deshabilitó los tres timers de campaña/throughput mencionados, reinició el colector `atmoslink-radio-config-6g.service` (01:59:06) y habilitó `luisita-prospective.timer` (01:59:09). Los registros acreditan la cuenta utilizada, **no permiten certificar si una persona o automatización inició la acción**. La inspección actual no ejecutó esa instalación.

El estado prospectivo registra autorización previa y un primer segmento **P01_S01, 6655 MHz / 40 MHz**, con ventana prevista **30/10 12:00 → 31/10 00:00**:
- **12:00:01** — `WINDOW_INTENT`.
- **12:00:02** — `TRIAL_ACK`.
- **12:02:33** — **`CONTROLLER_ERROR`**: `Dual target/connectivity not stable before deadline`; servicio con salida 1/FAILURE.
- Desde **12:02:33** y hasta el final del día, el controlador respondió **`HALTED`**. El archivo `HALT.json` conserva la misma razón.
- No existe `SWITCH_COMMITTED` del segmento prospectivo en los eventos revisados; tampoco un `ROLLBACK_COMMITTED` explícito en ese registro. Las observaciones RF posteriores confirman nuevamente la línea base **7000/20**. **No clasificar P01_S01 como exposición prospectiva válida** ni inferir el instante preciso de restitución RF sin evidencia adicional.

La secuencia `TRIAL_ACK → CONTROLLER_ERROR → HALTED` constituye el **incidente crítico del día**. El timer prospectivo continuaba activo, pero el servicio permanecía en estado lógico HALTED; no confundir actividad del timer con campaña en ejecución. La revisión y eventual reanudación requieren una decisión operativa independiente, **no realizada aquí**.

## 7. Respaldo remoto, recuperaciones y seguridad

El backup programado comenzó a las **02:30:10**. El respaldo local consistente se creó a las **02:31:19** y se verificó en el destino principal a las **02:34:41**. El segundo destino falló a las **02:38:38** por cuota de API (`rateLimitExceeded`); `atmoslink-remote-backup.service` quedó `failed/exit-code`.

El recuperador registró fallos intermedios, pero confirmó **`RECOVERY COMPLETE 2/2`** para una copia generada el **30/10 a las 18:34:09**, con última verificación observada a las **23:54:44**. Esto verifica **esa copia en ambos destinos**, no certifica toda la cola histórica ni la inexistencia de respaldos locales más recientes.

En `campaign_runtime/campaign_events.jsonl` **no hay eventos nuevos fechados el 30/10**; su último evento es el `SWITCH_COMMITTED=OK` de línea base del 27/10. No se observaron eventos llamados `SAFE_ABORT` ni `executor_failure` en las fuentes examinadas del día. **Sí se observó el incidente prospectivo `CONTROLLER_ERROR`**: no debe ocultarse por no tener aquellas etiquetas. No se registró una transición factorial nueva ni se atribuyeron acciones RF manuales adicionales sin evidencia.

## 8. Decisiones metodológicas y límites

1. **Separar factorial, línea base y prospectiva**. El 30/10 no es un día experimental 3×2; P01_S01 no está confirmado.
2. **Marcar discontinuidad de throughput como cambio administrativo del instrumento** desde las 01:59, no como fallo de enlace; conservar solo las 16 pruebas realmente observadas.
3. **Mantener las 11 excepciones meteorológicas del día y las 30 históricas F6655_B20** como banderas QC, sin imputación ni alteración de las fuentes.
4. **Distinguir adquisición, conectividad y disponibilidad RF**: los dos errores SSH de mediodía no demuestran por sí solos caída del enlace.
5. **No interpretar el estado `HALTED` como recuperación prospectiva**; el ensayo no se incorpora a análisis causal hasta auditar la transición y la conectividad dual.
6. **Conservar cronología de watchdog y matching** para un análisis de asociación temporal con controles por lag, frecuencia de muestreo y autocorrelación.
7. **No equiparar goodput TCP con capacidad PHY**, ni interpretar promedios de línea base como efecto de tratamientos.

**Procedencia:** exports `Data/exports/{active_throughput_6g,master_observations_multistation,scientific_campaign_6g_integrated}.csv`, estados y eventos de `campaign_runtime` y `prospective_runtime`, `systemctl`, `journalctl`, `tailscale status/ping`. Todos los archivos y servicios se inspeccionaron sin escrituras. Se omiten credenciales, tokens, IP privadas, volcados de bases de datos y payloads crudos de telemetría.

**Estado documental:** nuevo informe aditivo; no reemplaza los informes de días anteriores.
