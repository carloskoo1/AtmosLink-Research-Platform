# AtmosLink — trazabilidad diaria 2026-11-15 (America/Lima)

## Alcance y procedencia
Inspección de solo lectura efectuada 2026-11-15 entre 23:50:05 y 23:51:07 -05:00. Fuentes: Controlador (SQLite de producción consultado mediante URI mode=ro; systemctl/journalctl) y equipo remoto identificado como `rpi-cunacales` (estado del logger). No se realizó SSH al nombre literal `rpi-sanjose64`. La campaña factorial AtmosLink 3×2 ya finalizó; los datos aquí descritos son seguimiento de laboratorio y no una nueva ejecución factorial. La vigilancia científica prospectiva de Luisita es independiente; aquí sólo se consignan incidentes operativos observables.

## RF y enlace
En `scientific_campaign_6g_integrated`, 356 filas del 15/11 hasta 23:16:50 -05:00: 355 `LINK_OPERATIONAL_DUAL`, una `COLLECTION_ERROR` (20:41:20, «faltan variables obligatorias»). Configuraciones observadas: 6475 MHz / 20 MHz (178), 7000 MHz / 40 MHz (177), y una fila sin frecuencia/ancho (error). RSSI medio DL/UL -78.48/-82.51 dBm; SNR medio DL/UL 20.21/17.60 dB. Estas configuraciones no prueban por sí solas una transición válida ni una ventana elegible.

## TCP y estaciones
`active_throughput_6g`: 158 pruebas OK (79 DL y 79 UL); throughput medio DL 47.410 Mbps, UL 21.847 Mbps. Últimos inicios: DL 23:45:08 y UL 23:45:24 -05:00.

`master_observations_multistation`: CU01 1341 filas, temperatura media 19.47 °C, humedad media 65.26 %, último registro 23:44:36; SJ01 950 filas, temperatura media 9.06 °C, humedad media 97.96 %, último registro 23:45:39 -05:00. En `rpi-cunacales`, `weather-logger-sj01.service` estaba `active` y `Result=success` a las 23:51:07.

## Integración y criterios de calidad
`scientific_campaign_6g_integrated` avanzó hasta 2026-11-15T23:16:50-05:00, posterior al watermark de referencia 2026-09-15T23:36:42-05:00. Matching meteorológico dual del día: 352/356 (98.88 %); cuatro filas no satisfacen el matching dual. Histórico F6655_B20: 1923 filas, 1883 con ambos indicadores =1, **40 excepciones**. Nuevas filas F6655_B20 fechadas el 15/11: **0**; el control de que *todas las futuras filas nuevas* tengan `cu01_weather_matched=1` y `sj01_weather_matched=1` permanece abierto. No se modificaron ni imputaron datos.

## NASA POWER / ERA5-Land
Fechas máximas **en la SQLite local del Controlador**, NO certificadas dentro del ZIP de Google Drive:
| Fuente | CU01 (AP_CUNACALES) | SJ01 (SM_SAN_JOSE) | MID_LINK | Comparación con control 14/11 |
|---|---|---|---|---|
| NASA POWER | 2026-11-13 18:00 -05 | 2026-11-13 18:00 -05 | 2026-11-13 18:00 -05 | +1 día en los tres sitios |
| ERA5-Land | 2026-10-09 23:00 -05 | 2026-10-09 23:00 -05 | 2026-10-09 23:00 -05 | Sin avance en los tres sitios |

No hay disparidad de fecha máxima entre sitios dentro de cada fuente. ERA5-Land sigue rezagada y requiere auditoría del incremental. Se consultó el conector Google Drive: se localizó la carpeta `AtmosLink_Backups`, pero la búsqueda no encontró el ZIP reciente y no se inspeccionó su contenido; por tanto, no se certifica integridad meteorológica del respaldo remoto.

## Servicios, incidentes y recuperación
En Controlador estaban activos: `atmoslink-radio-config-6g`, `atmoslink-dashboard`, `atmoslink-event-monitor`, `atmoslink-scheduler` y `weather-logger`. Timers habilitados/observados: `atmoslink-remote-sync`, `atmoslink-weather-watchdog`, `atmoslink-backup-recovery`, `atmoslink-scientific-validation`, `atmoslink-remote-backup`. `atmoslink-remote-backup.service` figuraba `failed`; `tailscale-serve-ap.service` también `failed`. No se cambió ningún servicio o timer.

Se observó `CONTROLLER_ERROR/HALTED` en journal de `luisita-prospective.service` durante la madrugada (por ejemplo 02:33 -05:00). Se referencia únicamente como incidente de operación compartida; su análisis y elegibilidad pertenecen a la vigilancia prospectiva separada. La búsqueda de `SAFE_ABORT`, `executor_failure` y transiciones no fue exhaustiva: no se certifica ausencia de tales eventos ni se infieren acciones humanas.

Respaldo `backup_CU01_20261115_200811.zip`: los logs del recuperador informaron `RECOVERY COMPLETE 2/2` y verificación primaria/UNC, nuevamente a las **23:44:49 -05:00** (289434850 bytes). Es una confirmación **por logs** de esa copia, no una inspección directa de su ZIP ni conciliación histórica de todos los respaldos.

## Decisiones metodológicas y límites
Se mantiene separada la campaña factorial terminada de las mediciones posteriores; no se convierten transiciones ni mediciones TCP en exposiciones científicas válidas sin criterios de elegibilidad. Se conservan las 40 excepciones F6655_B20 y cuatro discordancias duales del día como indicadores de calidad, sin reparación retroactiva. Las consultas operativas fueron sólo lectura; la única escritura autorizada fue este documento Markdown en GitHub. Sin credenciales, IP privadas, identificadores sensibles, dumps ni JSON crudo.
