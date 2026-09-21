# Consolidación diaria de trazabilidad — AtmosLink 3×2

**Fecha operacional:** 2026-09-20 (America/Lima)
**Inspección de cierre:** 2026-09-20 23:54–23:58 -05:00
**Modo:** read-only para RF, PoE, VLAN, servicios, timers y bases de datos
**Escenario vigente:** F7000_B40 — 7000 MHz / 40 MHz

## Estado ejecutivo y RF

`campaign_runtime/executor_state.json` conserva `sequence=2`, `scenario_id=F7000_B40`, aplicado el 2026-09-18 00:00:01.053089 -05:00. En la inspección de cierre no se encontró un archivo `SAFE_ABORT` ni un `executor_failure.json` activo.

La última fila integrada disponible del día corresponde a 2026-09-20 16:31:04 -05:00 y reporta `LINK_OPERATIONAL_DUAL`, 7000 MHz / 40 MHz, DL/UL RSSI -75/-81 dBm, SNR 22/17 dB, MCS 203/201, DL link rate 137 Mbps y TX quality/capacity AP 100/20 %. Ambos extremos estaban representados en la adquisición.

## Clima y consolidación multisitio

Última fila CU01 observada en `master_observations_multistation`: 2026-09-20 16:33:14 -05:00; T=17.65 °C, HR=60.21 %, P=740.83 hPa, lluvia 1 min=0.0 mm. La misma fila conserva telemetría RF cercana (16:33:29): MCS 202/201, SNR 22/17 dB y RSSI STA -75/-82 dBm.

Última fila SJ01 del export multisitio: 2026-09-20 16:34:07 -05:00; T=7.24 °C, HR=89.69 %, P=664.82 hPa, lluvia 1 min=0.56 mm, viento=0.7 m/s, dirección=181.7°, ráfaga=2.33 m/s.

Una comprobación directa read-only en `rpi-sanjose64` confirmó `weather-logger-sj01.service=active` y un `GUARDADO` a las 23:57:08 -05:00: T=5.97 °C, HR=86.52 %, P=666.16 hPa, lluvia 1 min=0.0 mm y `wind_ok=1`.
## Throughput y dataset científico

`active_throughput_6g` continuó avanzando hasta al menos 23:45:28 -05:00. La última prueba observada fue UL, estado OK, 7000/40, throughput medido 43.778 Mbps, 62 retransmisiones y ping 0 % loss con RTT promedio 3.031 ms. La muestra incorporó clima CU01 (15.11 °C, 66.11 %, 743.01 hPa) y SJ01 (6.26 °C, 85.33 %, 666.17 hPa).

Los exports inspeccionados contenían 32,910 registros de `active_throughput_6g` más cabecera, 148,443 de `master_observations_multistation` más cabecera y 5,256 de `scientific_campaign_6g_integrated` más cabecera. El watermark integrado observado fue 2026-09-20 16:31:04 -05:00, por lo que está inequívocamente por encima del watermark pendiente 2026-09-15 23:36:42 -05:00.

La última fila integrada observada presenta `cu01_weather_matched=1`, `sj01_weather_matched=1` y `both_weather_stations_matched=1`. La validación histórica de F6655_B20 ya había establecido 121 filas posteriores al watermark de referencia: SJ01 121/121, CU01 119/121 y ambas 119/121. Las dos excepciones CU01 se preservan sin imputación; por tanto no se redefine retrospectivamente el criterio como 121/121 para CU01.

## Incidente y acción humana del día

El 2026-09-20 se documentó separadamente el incidente de administración del cnMatrix EX1010-P de CU01 (`docs/INCIDENT_2026-09-20_CNMatrix_CU01_RECOVERY.md`). El switch aparecía Offline en cnMaestro aunque LAN, radios y PoE continuaban operativos. Se identificó conflicto de administración IPv4 y ausencia de ruta por defecto. La recuperación fue una acción humana sobre el plano de administración, sin factory reset, sin reboot y sin cambios RF. El estado final documentado fue Online en cnMaestro.

Este incidente no se interpreta como caída RF de F7000_B40. La evidencia científica posterior conserva enlace dual y las mediciones activas continuaron durante el día.

## Decisión metodológica

Mantener F7000_B40 sin intervención RF y preservar la continuidad de adquisición. El incidente cnMatrix se clasifica como incidente del plano de administración y se referencia de forma separada de la serie experimental. No se imputan observaciones meteorológicas faltantes y no se reescribe evidencia histórica. La consolidación de hoy se limita a evidencia textual y a lecturas de fuentes existentes.