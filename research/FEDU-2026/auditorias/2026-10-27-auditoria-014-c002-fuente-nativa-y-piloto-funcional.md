# FEDU — Auditoría 014: C002, fuentes nativas y primer piloto funcional AP/SM

**Fecha:** 27 de octubre de 2026. **Ámbito:** enlace de 6 GHz CU01 AP — SJ01 SM, Controlador y archivos propios de AtmosLink.  
**Modo de trabajo:** recuperación de fuentes existentes y ensayo ICMP acotado. **Sin intervención sobre RF, PoE, cnMatrix, firmware o servicio de adquisición.** No se abrió test de hipótesis.

## 1. Objetivo puntual

Intentar corroborar por evidencia **nativa e independiente** el candidato **C002 (04-sep-2026, desde 09:15)** y, si ese histórico no estaba disponible desde las conexiones autorizadas, probar una fuente complementaria de **conectividad funcional local** con marcas de tiempo y archivo privado.

## 2. Contraste C002 ya sustentado

- Fichas I4 v02: 56 mediciones de throughput con estado `ERROR`, 2 muestras RF válidas y 84 errores del colector alrededor de la ventana definida en auditoría 008. Estos indicadores son muestras/accesos, no demostraciones de causa RF.
- Captura cruda `epmp_monitor/logs/raw_show_sta_2026-09-04.log`, auditada con SHA-256 `287d3de1900f53591981f68227983bfc5341d3a30a1e7b0969295aaa09381712`.
- En la **ventana exacta C002** usada en auditoría 013: **403 capturas**, **392** con texto de sesiones SSH pero sin tabla `cambiumAPConnectedSTATable`; **11** sin respuesta interpretable; **0** con SM esperado en tabla.
- Los **392 banners SSH** indican respuesta textual de la administración del AP; no documentan un evento firmware nativo de desasociación, porque se desconocen semántica de la ausencia de tabla y código de salida del comando, y el script de adquisición original contiene `|| true`.
- Alerta de plataforma `UNKNOWN` del 04-sep a las 10:34:25, con observación retrasada, solo confirma un problema de **observabilidad**, no causa RF.

**Dictamen C002:** `AP_PEER_NOT_OBSERVED_IN_RAW_SHOW_STA`; `THROUGHPUT_TEST_ERRORS_OBSERVED`; `PHYSICAL_RF_OUTAGE_INDETERMINATE`. Etiqueta `y` de degradación física RF **NA**, no negativa.

## 3. Alcance de búsqueda de archivos y limitación de acceso

Se revisaron rutas **autorizadas**:
1. Controlador: archivos originales `epmp_monitor/logs`, `epmp_monitor/backup`; documentación, `runtime` y proyectos privados del mismo enlace.
2. Nodo remoto `rpi-cunacales`: `/home/ckoo/Proyectos/EstacionMeteorologica/Logs`, `backups`, `provenance` y `docs`. Los directorios inspeccionados no mostraron exportaciones históricas de firmware AP/SM o de cnMaestro aplicables a C002.
3. El `journalctl --list-boots` del Controlador se inicia el 07-oct, por lo que ese registro del sistema no permite reconstruir retrospectivamente el 04-sep.
4. Un inventario de archivos con nombres `*syslog*`, `*cnmaestro*`, `*alarm*` y `*event*` en los proyectos autorizados encontró principalmente eventos procesados de AtmosLink y código; **no se obtuvo un export de eventos nativos del fabricante** durante esta revisión.

**Limitación delimitada:** `NO_EXPORT_NATIVE_C002_DISPONIBLE_EN_FUENTES_LOCALES_INSPECCIONADAS`. **No** significa que el evento no exista en el historial **cloud cnMaestro**, al que esta auditoría no tuvo sesión autenticada. No intentar atribuir el estado RF a un tercero o a otra infraestructura.

## 4. Comprobación local y diseño del instrumento complementario

Se verificó la ruta local Controlador → SM por la interfaz de red de CU01. Se ejecutaron de forma manual, en solo observación, dos comprobaciones cortas:
- AP CU01: 3 paquetes ICMP enviados, 3 respuestas, **0 % pérdida**, RTT observado 0,394–0,498 ms, media ~0,456 ms.
- SM SJ01: 3 paquetes ICMP enviados, 3 respuestas, **0 % pérdida**, RTT observado 2,101–4,354 ms, media ~2,886 ms.

Esos resultados solo se refieren a **la hora del piloto del 27-oct**, no al incidente histórico. La respuesta ICMP a ambos equipos es evidencia de **alcanzabilidad de gestión local**, no prueba de servicio TCP, conectividad desde el SM en sentido inverso ni causa física de eventuales fallos.

Para obtener evidencia temporal complementaria se creó un instrumento **Python de biblioteca estándar y ejecución acotada**:
- [`scripts/piloto_ping_funcional_ro.py`](../scripts/piloto_ping_funcional_ro.py), sin credenciales ni IP de campo hardcodeadas.
- Una sonda ICMP por destino AP/SM por ronda, como máximo 5 rondas por invocación, intervalo mínimo 10 segundos; sin systemd/cron.
- Marca `start_utc`, `available_at_utc`, duración, respuesta y RTT por destino; devuelve `PROBE_ERROR` distinto de `ICMP_NO_REPLY`.
- Interpreta `BOTH_MANAGEMENT_ENDPOINTS_RESPOND`, `SM_PATH_NO_REPLY_CHECK_RF_OR_MANAGEMENT`, `BOTH_PATHS_NO_REPLY_CHECK_LOCAL_NETWORK`, `INSTRUMENT_ERROR` y asimetrías. **Ninguna** de ellas se convierte por defecto en `RF_LINK_DOWN`.

**Piloto controlado completado** en Controlador 27-oct-2026, entre UTC 17:23:46 y 17:24:06 (Perú 12:23:46–12:24:06), 3 rondas separadas 10 s:
- **AP: 3/3 `ICMP_REPLY`**, RTT 0,644 / 0,599 / 0,576 ms.
- **SM: 3/3 `ICMP_REPLY`**, RTT 2,32 / 2,40 / 3,73 ms.
- **Sin errores de instrumento, sin paquetes perdidos en esas tres rondas**.

Archivo privado `FEDU_2026_Privado/observabilidad_piloto/ping_funcional_piloto_20261027.jsonl`, **3 registros**, **modo 0600**, 2087 bytes. SHA-256: `06a71ae120092321cd8ef1f183a59db196715a71c02a1ed62714f0fac971b8a9`. Se mantiene fuera del repositorio público y sin direcciones IP en los registros.

**Importante:** este es un piloto de calidad/viabilidad de la observación, **no un sistema de monitoreo desplegado**. No se ha activado ninguna tarea permanente o servicio que genere tráfico periódico indefinidamente.

## 5. Dependencia para adjudicar C002 sin sesgo

Necesitamos recuperar, si existen todavía en el servicio del fabricante, **Eventos y Alarm History** del AP CU01 y del SM SJ01, **por separado**:
- Intervalo primario: **04-sep-2026 08:30–17:00**, hora Perú. Anotar huso de exportación, autorreporte AP/SM, cambios en asociación, reinicios, `radio down/up`, estado de gestión y severidad.
- Intervalos secundarios tras C002: **10-sep 18:30 a 11-sep 14:00** (C003), **13-oct 13:15–14:45** (C016), **21-oct 05:30–08:15** (C022).
- Incidente de control AP del puerto 6: **01-sep 19:20–20:20** en switch/PoE y AP/SM; conversación contemporánea ya corrobora cable reconectado a las 19:59.
- Descargar CSV original sin transformaciones, preservar información de dispositivo, `event time`, código/tipo/severidad, estado, `raised/cleared`, fabricante, TZ, y calcular huella privada. **No subir datos crudos privados al repositorio público.**

**Procedimiento cnMaestro Cloud** (según documentación del fabricante, sujeto al menú real de su versión): `System > Notifications > Events` y `Alarms`/historial, filtros por dispositivo y fecha, `Export all as CSV`, y descargar en el `Download Manager`. No confundir `Offline` de gestión con RF físico. Fuente oficial de exportación: https://docs.cloud.cambiumnetworks.com/help/5.2.5/Content/UG_files/Onboarding%20Devices/export-all-csv.htm

**Si la retención ya no cubre septiembre**, establecer fecha máxima/mínima del histórico realmente visible; declarar `HISTORICO_NATIVO_NO_DISPONIBLE` con fecha de inspección. No clasificar C002 como caída confirmada únicamente por capturas SSH.

## 6. Resultado y siguiente puerta

**C002 permanece indeterminado** como episodio RF físico y no entra al test predictivo H1. Sí se verificó pérdida de observabilidad y pruebas `ERROR`. Se completó un piloto independiente del **proceso de captura RF**, pero comparte las rutas de red y no acredita por sí solo la causa física; no se anuncia como sensor RF independiente.

**Siguiente decisión:** preservar exportaciones históricas del fabricante si accesibles; cotejar sus marcas con C002 y, de ser insuficientes, aprobar separadamente un **periodo prospectivo de monitoreo de conectividad AP/SM**, con cadencia, fuente, inicio y punto de cierre definidos. No inducir fallas, no modificar H1 ni contar épocas sin etiqueta como negativos.
