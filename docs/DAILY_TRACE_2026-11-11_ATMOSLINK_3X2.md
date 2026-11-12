# AtmosLink — trazabilidad y clima, 2026-11-11 (America/Lima)

**Corte de inspección:** 2026-11-11 23:48–23:50 -05:00 (día aún no cerrado). **Acceso:** Desktop Commander a Controlador y a Raspberry SJ01 identificada como `rpi-cunacales`; consultas SQLite URI `mode=ro`, systemd y journal, sin intervención operativa. Campaña factorial 3×2 cerrada; estas observaciones son seguimiento y campaña prospectiva separada, no repetición factorial.

## RF, TCP y clima local
`scientific_campaign_6g_integrated`: 372 observaciones RF, todas `LINK_OPERATIONAL_DUAL`, sin `COLLECTION_ERROR`; 189 a 7000 MHz/20 MHz y 183 a 6655 MHz/20 MHz. Medias para 7000/20: RSSI DL/UL -74.14/-80.59 dBm, SNR DL/UL 22.92/17.89 dB; para 6655/20: -76.49/-81.96 dBm y 22.65/18.86 dB. Último registro RF: 23:36:20 -05:00. No interpretar estos promedios observacionales como efecto causal del tratamiento.

`active_throughput_6g`: 180 pruebas `OK` (DL 90, media 54.69 Mbps; UL 90, media 17.64 Mbps), último inicio UL 23:45:24 -05:00. Sin fallos reportados en la agrupación del día.

`master_observations_multistation`: CU01 1327 filas, temperatura 19.21 °C, HR 60.59%, presión 742.32 hPa, viento 0.29 m/s, última 23:43:06; SJ01 927 filas, 8.84 °C, HR 90.59%, presión 665.97 hPa, viento 3.41 m/s, última 23:42:26. En Raspberry remota `weather-logger-sj01.service` estaba `active/running` y el watchdog SJ01 timer `active/waiting`. No se alteró la configuración.

## Integración y condición F6655_B20
Watermark de referencia: 2026-09-15T23:36:42-05:00. Último integrado 2026-11-11T23:36:20-05:00: **avance confirmado**. Matching meteorológico dual diario: **359/372 (96.51%)**, 13 excepciones. Histórico F6655_B20: **1918** filas, **1878** con matching dual y **40** excepciones; al cierre anterior eran 1735/1705/30. Se añadieron 183 filas F6655_B20 hoy; **173** cumplen ambos flags y **10 no**. La condición exigida de que todas las nuevas filas tengan `cu01_weather_matched=1` y `sj01_weather_matched=1` **NO se cumple**. Excepciones nuevas observadas en CU01; SJ01 flag 1 en las filas nuevas. Mantenerlas identificadas como problemas de correspondencia y no como prueba automática de fallo RF ni de invalidez completa de la ventana. Investigar desfases/ausencia de registros sin alterar datos originales.

## Servicios, transiciones e incidentes
Controlador: activos `atmoslink-dashboard`, `atmoslink-event-monitor`, `atmoslink-radio-config-6g`, `atmoslink-scheduler` y `weather-logger`; `atmoslink-remote-backup.service` figuraba `failed`. Timers visibles habilitados: `luisita-prospective`, `atmoslink-remote-sync`, `atmoslink-weather-watchdog`, `atmoslink-scientific-validation`, `atmoslink-remote-backup`, `atmoslink-backup-recovery`. Las unidades oneshot inactivas entre invocaciones no implican por sí solas fallo.

Como referencia documental, el journal del controlador prospectivo contiene `WINDOW_VERIFIED` para P02_S01 (7000/20, 00:00:03 local; `changed=false`) y P02_S02 (6655/20, confirmación alrededor de 12:01:22 local). No constituye por sí mismo dictamen de elegibilidad; el análisis prospectivo de Luisita se mantiene en su tarea separada. Búsqueda acotada sin confirmación de nuevos `SAFE_ABORT`/`executor_failure`; no se afirma ausencia global.

Respaldo: fallo del recuperador registrado a las 21:46:57 local del 10/11 (02:46:57 UTC del 11/11); posteriormente el 11/11 se verificó la copia `backup_CU01_20261111_194334.zip` en destinos primario y UNC, con `RECOVERY COMPLETE 2/2` (última confirmación 23:24:54 local). Esto acredita esa copia, no todas las copias históricas ni su contenido meteorológico específico. No se verificaron intervenciones humanas operativas; esta inspección es lectura asistida.

## NASA POWER y ERA5-Land: estado de seis series
Se consultaron las tablas locales `nasa_power_hourly` y `era5_land_hourly` de la base de Controlador, **NO el contenido del respaldo más reciente en Google Drive**. La búsqueda del conector Drive identificó la carpeta `AtmosLink_Backups` pero no permitió localizar/inspeccionar una copia reciente con estas tablas; por ello no se certifica que las fechas siguientes coincidan con el último respaldo ni se certifica avance frente al control anterior (no recuperado).

| Fuente | CU01 (AP_CUNACALES) | SJ01 (SM_SAN_JOSE) | MID_LINK |
|---|---|---|---|
| NASA POWER | 2026-11-09 18:00 -05 | 2026-11-09 18:00 -05 | 2026-11-09 18:00 -05 |
| ERA5-Land | 2026-10-09 23:00 -05 | 2026-10-09 23:00 -05 | 2026-10-09 23:00 -05 |

Las fechas son homogéneas entre los tres sitios dentro de cada fuente. ERA5-Land aparece 33 días anterior al corte, lo que **amerita comprobar latencia y proceso incremental**; sin el control anterior y sin verificación del respaldo no puede diagnosticarse un estancamiento nuevo ni su causa. No emitir aviso meteorológico adicional basado en una comparación no demostrada.

**Decisiones metodológicas:** preservar íntegros los datos y excepciones; mantener la separación entre campaña 3×2 cerrada y prospectiva; verificar temporalidad, matching y elegibilidad por separado; no imputar muestras ni atribuir efectos causales; no certificar el contenido de Drive por logs de subida. **Seguridad:** solo documentación textual agregada, sin credenciales, direcciones privadas, dumps, secretos ni cambios de RF/PoE/VLAN/servicios/timers/bases.
