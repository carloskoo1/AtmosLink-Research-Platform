# AtmosLink 3×2 — Consolidación diaria de trazabilidad, 2026-10-25

**Campaña:** AtmosLink 3×2, CU01 (AP Cuñacales) ↔ SJ01 (SM San José).  
**Ventana auditada:** 2026-10-25 00:00:00–23:59:59, zona America/Lima (UTC−05:00).  
**Inspección:** 2026-10-26, aproximadamente 00:34–00:45 (UTC−05:00).  
**Modalidad:** consultas de solo lectura a Controlador. `rpi-sanjose64` respondió por Tailscale (~6 ms), pero el SSH directo devolvió `tailnet policy does not permit you to SSH as user "carlos"`. No se intentó eludir la política. Los datos de SJ01 provienen de los registros sincronizados en Controlador. **No se alteraron RF, PoE, VLAN, servicios, timers ni bases de datos.**

> **Dictamen:** el escenario F7000_B40 se confirmó después de un intento fallido y rollback. La adquisición del día continuó, pero hay valores RF nulos codificados como cero, dos pruebas de throughput erróneas durante la transición, dos pruebas UL con goodput cero pese a estado OK, incidencias de sincronización, 13 recuperaciones automáticas del logger y respaldo reciente no verificado en ambos destinos. No confundir continuidad operativa con elegibilidad científica completa.

## 1. Escenario, transiciones y estado persistente

- **00:00:00:** `SWITCH_START` F6475_B20 → **F7000_B40 (7000 MHz / 40 MHz)**.
- **00:00:01:** `TRIAL_APPLIED=OK`.
- **00:03:02:** `SWITCH_FAILED=ERROR`, detalle `No se recuperó el enlace.`.
- **00:04:57:** `ROLLBACK_COMMITTED=OK` a **F6475_B20 (6475 MHz / 20 MHz)**.
- **00:30:01:** segundo `SWITCH_START` hacia F7000_B40.
- **00:30:02:** `TRIAL_APPLIED=OK`.
- **00:32:40:** `TRIAL_CONFIRMED=OK`.
- **00:32:58:** **`SWITCH_COMMITTED=OK`**.

Las horas anteriores se convirtieron desde los timestamps UTC del registro estructurado a UTC−05:00. `campaign_state.json` y `executor_state.json` confirman **F7000_B40, secuencia 18**, aplicado el 25/10 a las 00:30. **El primer intento no constituye exposición válida al tratamiento; el segundo sí quedó confirmado.** No se observaron transiciones adicionales del 25/10.

## 2. Radiofrecuencia — scientific_campaign_6g_integrated

**287 filas** fechadas el 25/10: **285 `LINK_OPERATIONAL_DUAL` y 2 `COLLECTION_ERROR`**. Primera fila 00:04:12; última 23:59:40. Distribución: 5 filas operativas F6475_B20, **280 filas operativas F7000_B40** y 2 errores sin configuración RF recuperada. Las 280 filas F7000_B40 concuerdan en frecuencia y ancho AP/SM (**280/280**).

| Métrica, F7000_B40 | Resultado |
|---|---:|
| RSSI DL medio, excluyendo ceros QC | −76.918 dBm (n=279) |
| RSSI UL medio, excluyendo ceros QC | −81.262 dBm (n=275) |
| SNR DL medio, excluyendo ceros QC | 20.699 dB (n=279) |
| SNR UL medio, excluyendo ceros QC | 18.105 dB (n=275) |
| RSSI DL/UL medio sin depurar ceros | −76.643 / −79.811 dBm (n=280) |
| SNR DL/UL medio sin depurar ceros | 20.625 / 17.782 dB (n=280) |
| Última observación RF | 23:59:40 |

**Hallazgo QC:** seis filas operativas F7000_B40 contienen RSSI o SNR exactamente 0, potencialmente códigos de ausencia de telemetría, no valores físicos fiables: 00:34:21, 00:39:22, 00:44:23, 00:49:24, 00:54:25 y 02:45:36. Se presentan tanto los promedios brutos como los depurados, sin cambiar la fuente. La interpretación definitiva de esos ceros requiere verificar la semántica del fabricante.

Los `COLLECTION_ERROR` ocurrieron a **00:04:12** (SSH hacia SM: `No route to host`) y **02:04:59** (timeout SSH). Son fallos de colección/acceso; no equivalen por sí solos a caída física del radioenlace.

**Matching meteorológico del día:** CU01 **279/287**, SJ01 **287/287**, dual **279/287 = 97.21 %**. Ocho excepciones CU01=0: **02:40:35, 09:11:53, 11:02:13, 11:57:24, 13:57:44, 15:48:07, 16:48:17 y 19:58:54**. No se imputaron datos. El matching se evalúa separadamente del estado de colección RF.

## 3. Meteorología — master_observations_multistation

**2287 observaciones**: **CU01 1351**, **SJ01 936**.

| Variable | CU01 | SJ01 |
|---|---:|---:|
| Temperatura media | 19.561 °C | 9.297 °C |
| Rango de temperatura | 15.43–27.84 °C | 6.57–17.14 °C |
| Humedad relativa media | 62.811 % | 91.324 % |
| Presión media | 741.819 hPa | 665.734 hPa |
| Viento medio | 0.251 m/s | 1.413 m/s |
| Ráfaga máxima observada | 6.93 m/s | 8.767 m/s |
| Última observación | 23:59:00 | 23:59:30 |
| `local_bme_ok` | 1351/1351 con 1 | 936/936 con 1 |

La sincronización de SJ01 registró `Status global: OK` a las **23:58:49**, con dos registros recibidos e insertados en el lote final. Hubo fallos intermitentes de `atmoslink-remote-sync.service`, pese a la recuperación posterior. Las banderas instrumentales positivas no garantizan por sí mismas ausencia de sesgos.

## 4. Rendimiento — active_throughput_6g

**190 pruebas registradas:** **188 OK y 2 ERROR**, distribuidas en 95 DL y 95 UL. Las dos fallidas se iniciaron a **00:00:05 (DL)** y **00:00:27 (UL)**, durante el primer intento de transición. Dos pruebas OK aún conservaban la configuración F6475_B20; el análisis de régimen estable **F7000_B40** utiliza **186 pruebas OK (93 DL + 93 UL)**.

| Métrica en F7000_B40, pruebas OK | DL | UL |
|---|---:|---:|
| Goodput medio | **60.644 Mbps** | **36.321 Mbps** |
| Goodput máximo | 90.137 Mbps | 66.191 Mbps |
| Retransmisiones TCP medias | 55.011 | 50.441 |
| Retransmisiones máximas | 206 | 345 |

RTT ICMP medio en F7000_B40 **5.410 ms**, pérdida ICMP media **0 %** en las pruebas OK con medición válida. **QC adicional:** dos pruebas UL clasificadas como OK muestran **goodput=0** a las **02:00:19 y 02:15:19**. No deben tratarse automáticamente como rendimiento válido ni eliminarse sin auditoría de su estado, bytes y registro iperf. El goodput medido no es la tasa PHY reportada por Cambium.

## 5. Watermark y validación pendiente F6655_B20

**Watermark de referencia:** `2026-09-15T23:36:42-05:00`.  
**Última fila global del integrado observada:** `2026-10-26T00:04:40-05:00`.  
**Avance temporal: CONFIRMADO.** El día 25/10 también alcanzó las 23:59:40.

Revisión retrospectiva de **F6655_B20** posterior al watermark: **1724 filas**, última `2026-10-18T23:55:49-05:00`; **CU01 1694/1724**, **SJ01 1724/1724**, **matching dual 1694/1724 = 98.26 %**. Persisten **30 excepciones**, repartidas en 16/09 (3), 07/10 (8), 08/10 (9), 17/10 (4) y 18/10 (6). El 25/10 no hubo nuevas filas F6655_B20, porque operaron F6475_B20 durante rollback y F7000_B40 después de confirmación.

**Estado del requisito: PENDIENTE / NO CONFIRMADO.** No se ha demostrado `cu01_weather_matched=1` y `sj01_weather_matched=1` en todas las filas F6655_B20 posteriores al watermark. Mantener la vigilancia si reaparece ese escenario y conciliar retrospectivamente las 30 excepciones sin reescribir datos originales.

## 6. Servicios y timers críticos

En la inspección del 26/10: `atmoslink-dashboard`, `atmoslink-scheduler`, `atmoslink-event-monitor`, `atmoslink-radio-config-6g` y `weather-logger` **active/success**. `atmoslink-throughput-6g`, `atmoslink-remote-sync`, `atmoslink-scientific-validation`, `atmoslink-remote-backup`, `atmoslink-weather-watchdog` y `andean-campaign` **inactive/success** tras sus ejecuciones periódicas. **`andean-throughput` y `atmoslink-backup-recovery` figuraban failed/exit-code** al corte.

Timers programados observados: `andean-campaign`, `andean-throughput`, `atmoslink-throughput-6g`, `atmoslink-remote-sync`, `atmoslink-weather-watchdog`, `atmoslink-scientific-validation`, `atmoslink-remote-backup` y `atmoslink-backup-recovery`. La validación científica CU01/SJ01 concluyó **OK a las 23:38:18** del 25/10.

## 7. Incidentes, recuperaciones y acciones humanas

**Incidente — medición formal:** `andean-throughput.service` presentó **24 ejecuciones fallidas** del 25/10, última a las **23:05:00**, con `2/INVALIDARGUMENT` por parámetros CLI no reconocidos. El colector independiente `atmoslink-throughput-6g` siguió produciendo datos (188 pruebas OK del día). No se modificó el servicio.

**Incidente — sincronización:** `atmoslink-remote-sync.service` registró **28 eventos `Failed with result`** el 25/10 (exit-code/timeout), último a las **22:56:44**; a las **23:58:49** se documentó sincronización SJ01 `OK`. No atribuir los faltantes meteorológicos exclusivamente a este incidente sin contrastar tiempos y política de matching.

**Incidente — logger meteorológico:** el watchdog documentó **13 eventos `RECUPERACIÓN AUTOMÁTICA`** por ausencia de mediciones nuevas, entre las **00:19:51 y 20:00:59**, reiniciando `weather-logger.service`. El logger estaba activo al corte. Son acciones automáticas del sistema, no intervenciones humanas de esta inspección.

**Respaldos:** `atmoslink-remote-backup.service` generó una copia a las **02:39:37** y confirmó ambos destinos Google Drive principal/UNC a las **02:47:57** (`backup_CU01_20261025_023937.zip`). El recuperador también registró `RECOVERY COMPLETE 2/2` para una copia de las **05:59:57**, con última verificación registrada a las **11:31:51**. Sin embargo, intentos posteriores de recuperar la copia **`backup_CU01_20261025_180346.zip`** fallaron y la conservaron localmente. El **26/10 a las 00:24:53**, `atmoslink-backup-recovery.service` seguía fallando (`exit-code 3`) al intentar otra copia. **No está verificada la recuperación dual de la copia más reciente ni toda la cola pendiente.**

**SAFE_ABORT / executor_failure:** no se identificaron eventos con esas etiquetas el 25/10 en `campaign_events.jsonl`. Sí existió un `SWITCH_FAILED` crítico a las 00:03:02 con rollback y reintento exitoso; debe referenciarse por su nombre real y no ocultarse por ausencia de `SAFE_ABORT`. **Acciones humanas:** no se observaron cambios RF manuales atribuibles en el registro estructurado; esta inspección fue de lectura. El alcance de ausencia de eventos se limita a las fuentes consultadas.

## 8. Decisiones metodológicas observables y límites

1. Separar **intento fallido, rollback, reintento confirmado y operación estable**; excluir ventanas no confirmadas de la exposición válida al tratamiento F7000_B40.
2. Preservar las dos filas `COLLECTION_ERROR` y las dos pruebas activas `ERROR` como evidencia de incidente; no tratarlas como mediciones de régimen estable.
3. Etiquetar los seis ceros RF y las dos pruebas UL `OK` con goodput cero para auditoría de semántica, instrumentación y elegibilidad; conservar resultados brutos y análisis de sensibilidad sin alterar la fuente.
4. Mantener sin imputación las ocho excepciones meteorológicas del día y las 30 históricas F6655_B20.
5. Distinguir fallos auxiliares de sincronización/backup y adquisición SSH de interrupciones físicas del radioenlace.
6. No inferir efectos causales de frecuencia o ancho a partir de medias diarias sin controlar diseño factorial, bloques temporales, meteorología, autocorrelación y pérdidas de datos. No declarar cerrada la campaña ni validado al 100 % el matching F6655_B20.

## 9. Procedencia y seguridad

Consultas de lectura sobre Controlador: `Data/exports/scientific_campaign_6g_integrated.csv`, `Data/exports/master_observations_multistation.csv`, `Data/exports/active_throughput_6g.csv`, `campaign_runtime/campaign_state.json`, `campaign_runtime/executor_state.json`, `campaign_runtime/campaign_events.jsonl`, `systemctl`, `systemctl list-timers`, `journalctl`, `tailscale status/ping`. No se extrajeron ni se incluyen credenciales, contraseñas, secretos, volcados de bases de datos, payloads RF sin depurar ni datos personales. Las cifras reflejan el estado de exportación observado; una reexportación posterior puede modificar recuentos históricos y debe quedar versionada.
