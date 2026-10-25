# AtmosLink 3×2 — Consolidación diaria de trazabilidad, 2026-10-24

**Ventana auditada:** 2026-10-24 00:00:00–23:59:59, America/Lima (UTC−05:00).  
**Inspección:** 2026-10-25, aproximadamente 00:21–00:26 (UTC−05:00).  
**Modalidad:** lectura exclusivamente; no se modificaron RF, PoE, VLAN, servicios, timers ni bases de datos.  
**Clasificación:** evidencia operativa observada, incidentes, recuperación automática y límites metodológicos.  
**Alcance remoto:** Controlador consultado directamente. `rpi-sanjose64` respondió a Tailscale (5 ms), pero SSH directo fue denegado por política del tailnet. Los datos SJ01 se obtuvieron de exportaciones sincronizadas en Controlador; no se atribuyen a una inspección SSH de SJ01.

## 1. Escenario, RF y trazabilidad de configuración

Escenario vigente durante el 24/10: **F6475_B20, 6475 MHz, 20 MHz**. `campaign_state.json` y `executor_state.json` registran secuencia **17**, aplicada el **2026-10-23T00:00:00-05:00**. No se encontraron transiciones del 24/10 en `campaign_events.jsonl`.

`scientific_campaign_6g_integrated.csv` contiene **284 filas** fechadas el 24/10: **283 `LINK_OPERATIONAL_DUAL`** y **1 `COLLECTION_ERROR`**. Las 283 operativas informan 6475 MHz/20 MHz. Primera observación **00:03:13** y última **23:44:06**. Medias calculadas exclusivamente sobre filas operativas:

| Indicador RF | Media |
|---|---:|
| RSSI DL | −78.700 dBm |
| RSSI UL | −83.587 dBm |
| SNR DL | 21.184 dB |
| SNR UL | 17.975 dB |

**Incidente puntual de adquisición RF:** a las **09:50:54**, `COLLECTION_ERROR` por error SSH al consultar el SM (código 255, `No route to host`). No equivale por sí solo a una caída física demostrada del enlace; requiere diferenciar acceso de gestión y conectividad RF.

**Matching meteorológico del día:** CU01 **275/284**, SJ01 **283/284**, dual **275/284 = 96.83 %**. Nueve excepciones: **02:33:41, 05:49:46, 07:55:14, 13:11:40, 17:17:33, 17:27:35, 20:33:08, 20:43:09** (CU01=0, SJ01=1) y **23:44:06** (CU01=0, SJ01=0). Se conservan sin imputación. Los registros sincronizados y el export integrado tienen cadencias diferentes; no declarar pérdida RF por una brecha de exportación sin corroboración.

## 2. Meteorología — master_observations_multistation

**2298 filas** del 24/10: **1342 CU01**, **956 SJ01**.

| Indicador (media de observaciones disponibles) | CU01 | SJ01 |
|---|---:|---:|
| Temperatura | 19.280 °C | 8.987 °C |
| Humedad relativa | 63.513 % | 90.046 % |
| Presión | 741.599 hPa | 665.348 hPa |
| Viento | 0.287 m/s | 1.769 m/s |
| Ráfaga | 0.690 m/s | 2.373 m/s |
| Primera observación | 00:00:52 | 00:01:24 |
| Última observación | 23:59:02 | 23:59:27 |

El último registro global del export meteorológico consultado alcanzó **2026-10-25T00:15:27-05:00**. La sincronización `atmoslink-remote-sync` concluyó el 24/10 a las **23:59:37** con `Status global: OK` y resultado SJ01 `recibidos=1, insertados=1, ignorados=0`. El matching temporal no certifica calibración o exactitud de sensores.

## 3. Rendimiento activo — active_throughput_6g

**192 pruebas del 24/10, 192 `OK`**, con 96 DL y 96 UL, todas etiquetadas **6475 MHz/20 MHz**.

| Indicador sobre pruebas OK | DL | UL |
|---|---:|---:|
| Goodput medio | **34.960 Mbps** | **17.912 Mbps** |
| Retransmisiones TCP medias | 43.083 | 22.323 |
| RTT ICMP medio | 4.875 ms | 4.875 ms |

La última prueba global consultada ya corresponde al **25/10 00:15:19**. Goodput medido no equivale a tasa PHY. Las observaciones secuenciales no constituyen réplicas independientes; para inferencia, considerar bloques temporales, autocorrelación, clima y transición.

## 4. Watermark y requisito de matching F6655_B20

Watermark de referencia: **2026-09-15T23:36:42-05:00**. Última fila global observada del integrado: **2026-10-24T23:44:06-05:00**. **Avance temporal confirmado.**

Revisión retrospectiva de filas **F6655_B20 posteriores al watermark**: **1724 filas**, última **2026-10-18T23:55:49-05:00**. CU01 matched **1694/1724**, SJ01 matched **1724/1724**, dual **1694/1724 = 98.26 %**. **30 excepciones**: 16/09 (3), 07/10 (8), 08/10 (9), 17/10 (4) y 18/10 (6). El 24/10 no hay nuevas filas F6655_B20 porque el escenario fue F6475_B20. **La condición exigida de `cu01_weather_matched=1` y `sj01_weather_matched=1` en todas las nuevas filas F6655_B20 sigue SIN CONFIRMAR.** No se reescribieron exportaciones ni se imputaron datos.

## 5. Servicios, timers, incidentes y recuperaciones

En el corte del 25/10: `atmoslink-dashboard`, `atmoslink-scheduler`, `atmoslink-event-monitor` y `atmoslink-radio-config-6g` **activos**. Las unidades periódicas `andean-campaign`, `andean-throughput`, `atmoslink-throughput-6g`, `atmoslink-remote-sync`, `atmoslink-scientific-validation` y `atmoslink-weather-watchdog` estaban inactivas con resultado `success` (estado normal entre ejecuciones). Timers programados para campaña, medición, sincronización, watchdog, validación y respaldo; `atmoslink-backup-recovery` estaba en ejecución al corte.

**Incidente de servicio de medición formal:** `andean-throughput.service` registró **24 ejecuciones fallidas** entre **00:05 y 23:05** del 24/10 (journal `Failed with result 'exit-code'`; falla de argumentos incompatible registrada en jornadas anteriores). El colector independiente `atmoslink-throughput-6g` siguió operando con 192 pruebas válidas. No se intervino.

**Incidente de respaldo remoto:** `atmoslink-remote-backup.service` falló a las **02:43:05** del 24/10 por cuota de Google Drive (`RATE_LIMIT_EXCEEDED`; `uploaded=False`, `verified=False`). El recuperador confirmó `RECOVERY COMPLETE 2/2` para la copia generada el **24/10 17:55:48**, con verificaciones posteriores a las **22:31:50**, **23:07:48** y **23:41:55**. Al corte del 25/10, el recuperador había iniciado otra ejecución a las **00:14:29** y no constaba su cierre; no se certifica la totalidad de la cola histórica.

**Incidente meteorológico:** el watchdog registró **14 mensajes de recuperación automática** del `weather-logger.service` durante el 24/10, asociados a ausencia temporal de mediciones nuevas; el último a las **23:29:00**. Se observó posterior `weather-logger.service=active`. Este patrón requiere QC temporal y no demuestra por sí mismo falla del sensor.

**Validación científica:** `atmoslink-scientific-validation.service` finalizó el **24/10 a las 23:34:18** con **CU01: OK / SJ01: OK**.

## 6. SAFE_ABORT, executor_failure, transiciones y acciones humanas

No se encontraron eventos de campaña fechados localmente el **24/10** en `campaign_events.jsonl`; por tanto, en esa fuente no se identificaron `SAFE_ABORT`, `executor_failure`, `SWITCH_FAILED`, transiciones o rollbacks nuevos de ese día. No se identificaron cambios RF manuales atribuibles. La ausencia se limita a las fuentes inspeccionadas y no representa auditoría universal.

**Incidente crítico posterior al cierre — 25/10:** transición programada **F6475_B20 → F7000_B40**. `SWITCH_START` **00:00:00.880**, `TRIAL_APPLIED=OK` **00:00:01.962**, `SWITCH_FAILED` **00:03:02.966** (`No se recuperó el enlace.`), `ROLLBACK_START` **00:03:02.967** y **`ROLLBACK_COMMITTED=OK` 00:04:57.975** con diez comprobaciones consecutivas satisfactorias. **F7000_B40 NO quedó confirmado** en ese intento. El estado persistente continuaba en **F6475_B20, secuencia 17** durante la inspección. Registrar este episodio en la consolidación propia del 25/10; no computarlo como exposición válida a F7000_B40.

**Decisiones metodológicas:** mantener `COLLECTION_ERROR` separado del régimen estable; no equiparar errores SSH con fallas RF; preservar las nueve excepciones meteorológicas del día y las 30 F6655_B20 históricas; no imputar ni borrar; clasificar recuperaciones automáticas como eventos operativos; tratar la transición fallida del 25/10 como intento no confirmado; no hacer inferencia causal simple entre promedios de días diferentes.

## 7. Procedencia, seguridad y publicación

Fuentes consultadas en modo lectura: `Data/exports/scientific_campaign_6g_integrated.csv`, `Data/exports/master_observations_multistation.csv`, `Data/exports/active_throughput_6g.csv`, `campaign_runtime/campaign_state.json`, `campaign_runtime/executor_state.json`, `campaign_runtime/campaign_events.jsonl`, `systemctl`, `journalctl`, `tailscale status/ping`. Ruta base de exports en Controlador: `/home/carlos/Proyectos/EstacionMeteorologica/`; ejecutor: `/home/carlos/Proyectos/Andean-6GHz-Link-Experiment/`. La lectura de SJ01 fue indirecta por política de SSH. No se incluyen credenciales, secretos, dumps de bases de datos, direcciones privadas ni datos personales.

**Publicación prevista:** `carloskoo1/AtmosLink-Research-Platform`, rama predeterminada verificada `feature/atmoslink-ui-v2`, nuevo archivo `docs/DAILY_TRACE_2026-10-24_ATMOSLINK_3X2.md`. Se conserva la documentación previa sin sobrescribirla.