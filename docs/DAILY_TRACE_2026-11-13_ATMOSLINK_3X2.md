# AtmosLink — trazabilidad y clima, 2026-11-13 (America/Lima)

**Corte observado:** 2026-11-13 23:55–23:56 -05:00, antes del cierre diario. **Método:** consultas operativas de solo lectura mediante Desktop Commander a Controlador y dispositivo remoto identificado como `rpi-cunacales`; SQLite CU01 abierto con URI `mode=ro`; consultas a systemd/journal; búsqueda de metadatos de Google Drive. Sin cambios en RF, PoE, VLAN, timers, servicios, scripts ni bases. La campaña factorial 3×2 ya concluyó: los registros son seguimiento del laboratorio, no nueva ejecución factorial. La vigilancia prospectiva de Luisita se mantiene separada; aquí se registran únicamente evidencias operativas relevantes.

## RF y TCP
En `scientific_campaign_6g_integrated` se observaron **369** filas fechadas el 13/11, última `2026-11-13T23:26:39-05:00`: **180** a 6655 MHz/40 MHz y **189** a 7000 MHz/40 MHz, todas `LINK_OPERATIONAL_DUAL`, cero `COLLECTION_ERROR`. No se infiere elegibilidad de ventanas prospectivas por estas filas. `active_throughput_6g`: **180** pruebas `OK`, 90 DL (media **81.630 Mbps**) y 90 UL (media **43.891 Mbps**), último inicio `23:45:24-05:00`. Son métricas descriptivas del día; no sustituyen evaluación de causalidad ni de estabilidad de ventana.

## Meteorología e integración
`master_observations_multistation`: **2312** registros al corte, CU01 **1357** (temperatura media **20.21 °C**, humedad media **58.18%**, último `23:53:52`) y SJ01 **955** (temperatura media **9.65 °C**, humedad media **88.73%**, último `23:53:33`). `weather-logger-sj01.service` estaba **active**, resultado **success**, en dispositivo conectado `rpi-cunacales` a las `23:56:10-05:00`; no se verificó por conexión separada un host denominado literalmente `rpi-sanjose64`.

El watermark integrado `2026-11-13T23:26:39-05:00` supera `2026-09-15T23:36:42-05:00`: **avance confirmado**. Matching meteorológico del 13/11: CU01 **359/369**, SJ01 **368/369**, dual **359/369**; **10** excepciones de matching dual. Histórico `F6655_B20`: **1923** filas, **1883** matching dual, **40** excepciones acumuladas; **cero filas nuevas con fecha 13/11**. El requisito para futuras filas F6655_B20 continúa bajo seguimiento; no se declara subsanado el histórico.

## NASA POWER y ERA5-Land
Consulta a la base **local** `SQLite/CU01/weather_local.db`, no al contenido del ZIP remoto. Se conserva el mapeo de `site_tag`: CU01 = `AP_CUNACALES`, SJ01 = `SM_SAN_JOSE`, MID_LINK = `MID_LINK`.

| Fuente | CU01 | SJ01 | MID_LINK | Cambio respecto al control local del 12/11 |
|---|---|---|---|---|
| NASA POWER | 2026-11-11 18:00 -05:00 | 2026-11-11 18:00 -05:00 | 2026-11-11 18:00 -05:00 | +1 día en los tres sitios (fecha máxima diaria 11/11 frente a 10/11) |
| ERA5-Land | 2026-10-09 23:00 -05:00 | 2026-10-09 23:00 -05:00 | 2026-10-09 23:00 -05:00 | Sin avance |

Las fechas coinciden entre los tres sitios dentro de cada fuente. ERA5-Land sigue atrasado; corresponde verificar ingestión incremental y latencia del proveedor, sin imputar una causa. La búsqueda de Google Drive no devolvió el ZIP `backup_CU01_20261113...`; **no se inspeccionó ni certificó el contenido del respaldo más reciente en Drive**. Las fechas anteriores describen únicamente la base local.

## Servicios, incidentes y recuperaciones
`atmoslink-dashboard.service`, `atmoslink-event-monitor.service`, `atmoslink-radio-config-6g.service`, `atmoslink-scheduler.service` y `weather-logger.service` estaban **active/running**. Los timers `atmoslink-remote-sync`, `atmoslink-weather-watchdog`, `atmoslink-backup-recovery`, `atmoslink-scientific-validation` y `atmoslink-remote-backup` aparecían programados; sus servicios oneshot pueden figurar `inactive/dead` entre ejecuciones y ello no prueba falla.

**Incidente de respaldo:** `atmoslink-remote-backup.service` **failed** a las **02:44:58 -05:00**, error `rateLimitExceeded`, `uploaded=False`, `verified=False`. `atmoslink-backup-recovery.service` **failed** a las **23:31:50 -05:00** por `subprocess.TimeoutExpired` (60 s) al consultar el destino UNC mediante rclone para `backup_CU01_20261113_195359.zip`. No se confirmó redundancia 2/2 ni recuperación posterior en este corte. Se trata de incidentes de respaldo, no de prueba de interrupción de adquisición RF.

La búsqueda acotada de eventos en journal se inició, pero no se completó una conciliación exhaustiva de `SAFE_ABORT`, `executor_failure`, transiciones ni acciones humanas; **no se certifica su ausencia**. La inspección no ejecutó transiciones ni recuperaciones operativas. Se conserva como decisión metodológica separar estado operativo, validez científica y evidencia de respaldo.

**Pendientes:** inspeccionar contenido del ZIP más reciente de Drive; verificar control de seis series dentro del ZIP; auditar logs especializados de transiciones y SAFE_ABORT/executor_failure; conciliar las 40 excepciones históricas F6655_B20; comprobar redundancia 2/2. Este documento no contiene credenciales, direcciones de acceso privadas, dumps ni datos sensibles.
