# FEDU — Auditoría 010: recuperación histórica de eventos AP/SM y cnMaestro

**Fecha de revisión:** 27-oct-2026 (Perú). **Alcance exclusivo:** enlace físico Cuñacales–San José (AP CU01 y SM SJ01), cnMaestro correspondiente a ese enlace y registros AtmosLink propios. **Sin acceso a datos ajenos al enlace.**

## 1. Resultado de auditoría de fuentes

- **Se localizaron documentos históricos propios del enlace**: incidente de transición del 15-sep y recuperaciones documentadas del 19/20-sep. No coinciden con las ventanas de los ocho candidatos I4; por tanto, no justifican etiquetarlos.
- Se revisó el fichero AtmosLink `runtime/scientific_events.json`. **C002, 04-sep a las 10:34:25 −05**, presenta `PLATFORM_HEALTH = UNKNOWN`, `operational_state = DELAYED` y observación envejecida 551 s. Es una corroboración de la pérdida de frescura de adquisición, **no** de caída RF.
- **Fuente adicional identificada:** el recolector propio `weather_station/telemetry/cambium_local_collector.py` conserva filas de `radio_link_local` (incluida marca UTC/local, `station_id`, `radio_role`, `note`, `error`, MCS, SNR, RSSI y tasas). Define los códigos `SM_NOT_ASSOCIATED`, `LOW_SNR`, `LOW_RSSI`, `LOW_MCS`, `LOW_RATE`, `LINK_OPERATIONAL`.
- **Precaución indispensable:** en ese código `SM_NOT_ASSOCIATED` se deriva de la falta simultánea de campos RF en la respuesta del AP: no es, por sí solo, un evento independiente de asociación del firmware y podría confundirse con ausencia de métricas. Los umbrales `LOW_*` son categorías del recolector, no verdad-terreno RF ajena a la señal predictora.
- El recolector más específico `radio_config_6g_collector.py` consulta el AP y SM y almacena sus métricas y `collection_status` en `radio_link_config_telemetry`, **pero no se ha demostrado que almacene bitácoras históricas de asociación/desasociación del firmware**.
- En los directorios de trabajo de AtmosLink y del ejecutor 3×2 **no se encontró una exportación histórica identificable de cnMaestro** para estas ventanas. No se obtuvo acceso autenticado a los eventos cloud AP/SM. El acceso a comandos remotos de análisis estuvo restringido durante esta revisión, por lo que **no se completó la consulta SQL de `radio_link_local` ni se afirma un conteo de estados**.
- El fabricante documenta un endpoint de consulta de eventos **`GET /events`** y exportación CSV. Se deberá usar únicamente el mecanismo de **lectura** aprobado en la cuenta, evitando APIs de configuración y sin publicar tokens.

Documentación de fabricante:
- [API cnMaestro 5.2.0 (GET /events)](https://docs.cloud.cambiumnetworks.com/api/5.2.0/index.html)
- [Cambium Community: informes de eventos, Alarm History y exportación](https://community.cambiumnetworks.com/t/how-to-generate-different-types-of-reports-in-cnmaestro-cloud-and-on-premises-servers/50409)

## 2. Ventanas I4 precisas para recuperación

Todos los rangos siguientes están en zona **America/Lima, UTC−05:00**, y son **ventanas observadas de fallos de ensayo**; ninguna se considera inicio/fin de falla física.

| ID | Desde | Hasta | Exportar dos radios | Estado |
|---|---|---|---|---|
| C001 | 2026-09-04 08:00:07 | 2026-09-04 08:30:25 | CU01 AP, SJ01 SM | Pendiente |
| C002 | 2026-09-04 09:15:07 | 2026-09-04 16:00:21 | CU01 AP, SJ01 SM | Pendiente |
| C003 | 2026-09-10 19:00:06 | 2026-09-11 13:15:18 | CU01 AP, SJ01 SM | Pendiente |
| C011 | 2026-10-05 15:45:06 | 2026-10-05 16:15:18 | CU01 AP, SJ01 SM | Pendiente |
| C016 | 2026-10-13 13:45:06 | 2026-10-13 14:00:05 | CU01 AP, SJ01 SM | Pendiente |
| C020 | 2026-10-21 02:45:05 | 2026-10-21 04:00:27 | CU01 AP, SJ01 SM | Pendiente |
| C022 | 2026-10-21 06:00:06 | 2026-10-21 07:45:24 | CU01 AP, SJ01 SM | Pendiente |
| C024 | 2026-10-21 10:15:06 | 2026-10-21 10:30:24 | CU01 AP, SJ01 SM | Pendiente |

**Extracción:** incluir al menos **30 minutos antes y 30 minutos después** de cada ventana para recuperar última condición sana, alarmas de inicio/fin y secuencia de recuperación. Para periodos extendidos como C003 exportar ambos días. **Verificar la zona horaria del propio portal/CSV** antes de alinear.

## 3. Ruta de exportación desde la cuenta autorizada

En cnMaestro Cloud, seleccionar primero **el AP CU01**, abrir sus **Notifications / Events** (y Alarm History si está disponible), aplicar filtro de fecha y exportar todos los resultados a CSV; **repetir de forma independiente con el SM SJ01**. No asumir que seleccionar el AP incluye los eventos del SM. Si no aparecen registros antiguos en la UI, comprobar la sección de informes de eventos y la retención disponible de la cuenta; la ausencia puede ser limitación de histórico, no ausencia de incidentes. Según permisos/versión, la ruta visual puede variar.

Para cada archivo capturar **dispositivo (AP/SM), procedencia de exportación, fecha/hora de exportación, zona horaria, rango solicitado, número de registros, cobertura realmente devuelta, esquema de columnas y SHA-256**. Archivar el **CSV original intacto** en espacio privado. No incluir contraseñas, tokens, IP administrativas o MAC no autorizadas en GitHub.

## 4. Auditoría paralela de `radio_link_local`

Preparar una consulta SQL **en un snapshot de lectura**, sin iniciar el colector ni sondeos extra, para las ocho ventanas, por estación y `note`:

```sql
SELECT
  timestamp_local, station_id, radio_role, note,
  CASE WHEN error IS NULL OR error = '' THEN 0 ELSE 1 END AS collector_error,
  mcs_dl, mcs_ul, snr_dl, snr_ul, sta_dl_rssi, sta_ul_rssi,
  dl_rate, ul_rate
FROM radio_link_local
WHERE timestamp_local >= :start_local
  AND timestamp_local < :end_local
ORDER BY timestamp_local;
```

El script de origen confirma los campos; verificar antes la definición en el snapshot elegido y que las marcas `timestamp_local` sean comparables. Los estados `SM_NOT_ASSOCIATED` y `LOW_*` deben separarse de errores SSH/parsing y de observaciones RF válidas; no usarlos como única etiqueta porque comparten instrumental con las variables predictor.

## 5. Reglas de adjudicación científica

- `cnMaestro device Offline` o `AP unreachable` puede significar falla del **plano de gestión**, no caída física AP↔SM.
- Un evento explícito de **desasociación** proveniente del firmware con hora confiable, corroborado por una fuente separada de servicio, es una evidencia fuerte; no convertirlo automáticamente en causalidad física si hay reinicios o intervenciones.
- `iperf3 ERROR`, `ping ERROR` y `RF COLLECTION_ERROR` pueden compartir una misma dependencia instrumental. Documentar independencia de cada fuente antes de sumar votos.
- La verdad-terreno puede ser **indeterminada**, con inicio/fin intervalocensurado y posibilidad de episodios no observables. Nunca etiquetar por ausencia de archivos.
- El registro de exportación no autoriza ninguna modificación RF ni nuevas pruebas de tráfico.

## 6. Estado y limitación al cierre de esta auditoría

**Sin nueva extracción histórica autenticada de cnMaestro y sin lectura SQL adicional de `radio_link_local`**, por límites de acceso de esta revisión. Los ocho I4 siguen `INDETERMINADO_PENDIENTE_VERDAD_TERRENO`. Se ha localizado una fuente interna adicional y documentado un procedimiento de rescate específico. No se afirma ninguna contrastación estadística ni se inicia la campaña prospectiva. La hipótesis FEDU y el título aprobado permanecen sin cambios.
