# AtmosLink — trazabilidad y clima, 2026-11-12 (America/Lima)

**Corte:** 2026-11-12 23:46–23:48 -05:00; día no cerrado. **Origen:** consultas read-only mediante Desktop Commander a Controlador y Raspberry remota identificada como `rpi-cunacales`. SQLite CU01 abierto mediante URI `mode=ro`; systemd/journal consultados sin intervenciones. **Campaña factorial 3×2 concluida:** registros del día son seguimiento de laboratorio y de ventanas prospectivas independientes, no una nueva ejecución factorial.

## RF, TCP y clima
`scientific_campaign_6g_integrated`: 362 observaciones, 362 `LINK_OPERATIONAL_DUAL`, 0 `COLLECTION_ERROR`, último RF 2026-11-12T23:01:17-05:00. Configuraciones: 6475 MHz/40 MHz, 188 observaciones (RSSI DL medio -79.38 dBm, SNR DL 20.88 dB; valores UL 0 deben tratarse como ausentes/no interpretables); 6475 MHz/20 MHz, 174 observaciones (RSSI DL/UL -76.68/-83.13 dBm; SNR DL/UL 23.05/18.32 dB). No inferir causalidad de comparaciones observacionales.

`active_throughput_6g`: 178 pruebas OK: DL 89 (34.977 Mbps promedio, último inicio 23:45:07) y UL 89 (13.793 Mbps promedio, último inicio 23:45:25). No imputar pruebas futuras.

`master_observations_multistation`: CU01 1347 filas (temperatura 18.84 °C, HR 60.44%, presión 741.60 hPa, viento 0.30 m/s, última 23:43:49); SJ01 969 filas (8.96 °C, HR 86.79%, presión 665.15 hPa, viento 3.56 m/s, última 23:42:29). Raspberry remota: `weather-logger-sj01.service` active; `weather-watchdog-sj01.timer` inactive en comprobación puntual; verificar nombre y programación efectiva antes de clasificar incidencia.

## Integración y condición F6655_B20
Watermark histórico 2026-09-15T23:36:42-05:00. Último integrado 2026-11-12T23:01:17-05:00: avance confirmado. Matching dual diario 352/362 (97.24%); 10 excepciones. Histórico F6655_B20: 1923 filas, 1883 con ambos flags 1 y 40 excepciones. Frente al corte anterior documentado (1918/1878/40), aumentaron cinco filas, todas con matching dual; no hubo nuevas filas F6655_B20 el 12/11. La condición de nuevas filas del día es vacua, y las diez excepciones del 11/11 siguen abiertas: NO declarar matching histórico 100%. Las cinco filas adicionales acumuladas requieren conciliación temporal específica antes de atribuirles fecha de adquisición.

## Servicios, incidentes y recuperaciones
Controlador: activos `atmoslink-dashboard`, `atmoslink-event-monitor`, `atmoslink-radio-config-6g`, `atmoslink-scheduler`, `weather-logger`; `atmoslink-remote-backup.service` failed. Timers visibles: remote-sync, weather-watchdog, luisita-prospective, backup-recovery, scientific-validation, remote-backup. La inspección no cambia unidades. La búsqueda de eventos `SAFE_ABORT`, `executor_failure` y transiciones quedó acotada/no concluida: no certificar ausencia. Mantener la evaluación prospectiva de Luisita en su circuito independiente.

Incidente de respaldo: el journal registra para `backup_CU01_20261112_194854.zip` verificación en destino primario, pero fallo reiterado de subida a UNC, último a las 23:39:25 -05. Redundancia 2/2 NO confirmada; tampoco se inspeccionó el contenido meteorológico del ZIP. No hay intervención humana operativa atribuible a esta sesión.

## NASA POWER y ERA5-Land (seis series)
Fechas máximas consultadas en **base local de Controlador**, NO en el contenido del respaldo más reciente de Google Drive:

| Fuente | CU01 | SJ01 | MID_LINK |
|---|---|---|---|
| NASA POWER | 2026-11-10 18:00 -05 | 2026-11-10 18:00 -05 | 2026-11-10 18:00 -05 |
| ERA5-Land | 2026-10-09 23:00 -05 | 2026-10-09 23:00 -05 | 2026-10-09 23:00 -05 |

Respecto al control del 11/11 (NASA 09/11 18:00 en los tres sitios; ERA5 09/10 23:00): NASA POWER avanzó **un día en los tres sitios**; ERA5-Land **no avanzó en ninguno**. No hay desfase entre sitios en fechas máximas, pero ERA5-Land continúa atrasada y requiere revisión de latencia/proceso incremental. Se buscó la carpeta `AtmosLink_Backups` mediante conector Drive y un archivo de respaldo del 12/11 sin localizar contenido ZIP verificable; el log de subida al primario no sustituye lectura del respaldo. No certificar seis fechas del respaldo.

**Decisiones:** preservar datos y errores originales; separar RF operativo, matching, elegibilidad prospectiva y control meteorológico; no inventar adquisición factorial ni recuperaciones; mantener incidentes y limitaciones visibles. No se publican secretos, IP privadas, dumps, archivos binarios ni credenciales.