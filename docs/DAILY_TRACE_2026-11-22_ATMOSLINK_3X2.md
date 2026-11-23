# AtmosLink — trazabilidad diaria 2026-11-22 (America/Lima)

## Alcance, evidencia y límites
Consultas exclusivamente de lectura a Controlador (2026-11-22 23:50–23:52 -05) y rpi-cunacales, equipo físico SJ01. SQLite consultado mediante URI `mode=ro`: `/home/carlos/Proyectos/EstacionMeteorologica/SQLite/CU01/weather_local.db`; systemctl/journalctl sin cambios. Campaña factorial 3×2 terminada el 2026-10-28: lo observado es seguimiento de laboratorio, no nuevas exposiciones factoriales ni evaluación de elegibilidad prospectiva Luisita. Corte temporal de consulta; las estadísticas pueden cambiar si existen procesos de integración tardía.

## RF e integración
`scientific_campaign_6g_integrated` para fecha RF 2026-11-22: 236 observaciones, 235 `LINK_OPERATIONAL_DUAL` en 7000 MHz / 20 MHz y 1 `COLLECTION_ERROR` sin escenario asignable. Último `rf_timestamp_local`: 2026-11-22T23:02:55-05:00, posterior a 2026-09-15T23:36:42-05:00. Correspondencia meteorológica dual: 229/236 (97.03%). Error RF a 16:51:12: SSH a radio 192.168.1.8 falló por `No route to host`; no equivale a exposición válida.

`active_throughput_6g`: 118 pruebas fechadas 2026-11-22: 59 DL OK, media 31.857 Mbps; 59 UL OK, media 13.498 Mbps; última prueba a 23:45:24 -05.

`master_observations_multistation`: CU01 901 filas (temperatura media 19.25 °C; HR 65.44%; última 23:45:00), SJ01 743 (temperatura media 10.10 °C; HR 93.81%; última 23:45:34). Menor volumen que el control previo, sin atribución causal certificada. En rpi-cunacales `weather-logger-sj01.service` activo y lecturas válidas hasta 23:50:34; fragmento serial no UTF-8 descartado a 23:47:34, con recuperación de recepción válida a 23:48:34.

**F6655_B20:** consulta de condición frecuencia 6655 MHz y ancho 20 MHz: 2298 filas acumuladas, 2251 con `cu01_weather_matched=1` y `sj01_weather_matched=1`, 47 excepciones. Control publicado 2026-11-21: 2282/2234/48. Diferencia neta +16 filas, +17 con matching dual y -1 excepción; no puede interpretarse como 16 filas nuevas todas válidas sin auditoría por IDs y cambios de integración. **Inconsistencia de conciliación pendiente**: el control anterior reportó 171 filas nuevas el 21/11, mientras la agrupación actual por fecha RF 21/11 devuelve 187 filas, 185 válidas; posible diferencia de corte/actualización tardía, sin causa confirmada. La condición universal de matching dual no está satisfecha. No se alteraron filas.

## NASA POWER y ERA5-Land — seis series locales
| Fuente | CU01 / AP_CUNACALES | SJ01 / SM_SAN_JOSE | MID_LINK |
|---|---|---|---|
| NASA POWER | 2026-11-20T18:00:00-05:00 | 2026-11-20T18:00:00-05:00 | 2026-11-20T18:00:00-05:00 |
| ERA5-Land | 2026-10-09T23:00:00-05:00 | 2026-10-09T23:00:00-05:00 | 2026-10-09T23:00:00-05:00 |

Comparación con 2026-11-21: NASA POWER avanza un día en los tres sitios; ERA5-Land permanece inmóvil en los tres sitios (atraso persistente). No hay divergencia entre sitios en máximos temporales de cada fuente. Estas fechas provienen **solo de SQLite local**, no del contenido de un ZIP remoto. En Google Drive se localizaron carpetas `AtmosLink_Backups/CU01/field`, pero el conector no devolvió el ZIP del 22/11 ni permitió inspeccionar sus series. Los logs de rclone no sustituyen certificación de contenido.

## Servicios, incidentes y respaldo
`atmoslink-backup-recovery.service` y `tailscale-serve-ap.service` figuraron failed. Timers `atmoslink-remote-sync`, `atmoslink-weather-watchdog`, `atmoslink-scientific-validation` y `atmoslink-backup-recovery` programados. Validación científica 22:57:03: CU01 OK y SJ01 OK según logs.

Para `backup_CU01_20261122_165122.zip` (312107603 bytes), logs acreditan `RECOVERY COMPLETE 2/2` a las 22:31:49, después de un timeout UNC a las 21:57:52. **Sin embargo**, para el respaldo más reciente observado `backup_CU01_20261122_225341.zip` (313162760 bytes), a las 23:37:57 se verificó el destino primario, pero la carga UNC falló y se preservó localmente. Por tanto, **redundancia 2/2 del respaldo más reciente no confirmada**. Sin verificación de contenido ZIP ni hash independiente.

Auditoría de `SAFE_ABORT`, `executor_failure`, transiciones, recuperaciones completas y acciones humanas no exhaustiva; no se afirma ausencia. No se infiere causa de disminución de registros ni impacto científico por el error de SSH sin conciliación. Ninguna configuración RF/PoE/VLAN, servicio, timer, script o base de datos fue modificada.

## Decisiones metodológicas
Conservar evidencia de seguimiento posterior separada de la campaña factorial 3×2 concluida y de Luisita. Conciliar IDs y timestamps de F6655_B20 antes de declarar elegibilidad de todas las filas; conservar excepciones y cambios de matching. Mantener diferenciadas verificación local, confirmación de tamaño remoto por logs y certificación de contenido ZIP.
