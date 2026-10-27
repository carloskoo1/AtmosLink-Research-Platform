# FEDU — Auditoría 011: incidente de cable del AP 6 GHz localizado el 01-09-2026

**Fecha de análisis:** 27-oct-2026. **Zona de referencia:** America/Lima (UTC−05).  
**Fuente instrumental:** SQLite histórico del cierre 3×2, copia de solo lectura, tablas `radio_link_local`, `radio_link_config_telemetry` y `active_throughput_6g`.  
**Fuente de corroboración física:** extracto de conversación de trabajo fechado **1-sep-2026** que el operador aportó expresamente en la revisión de 27-oct. Se registra aquí una **paráfrasis sin nombres de participantes ni copia de chat**. El original sigue en custodia del operador y no se publica.  
**Identificación:** AOP-UTP-SEP-001, **fecha de incidente probable ya resuelta al 01-sep-2026** por coincidencia de hora, componente y recuperación. **Causa PoE y tiempo exacto de pérdida RF siguen sin verificación directa**.

## 1. Secuencia reconstruida (hora Perú)

| Momento | Fuente | Evidencia observada |
|---|---|---|
| **19:33:39** | RF 5-min | `LINK_OPERATIONAL_DUAL`; RF CU01/SJ01 válido |
| **19:36:37** | `radio_link_local` 1-min | Última fila normal documentada antes de la anomalía |
| **19:37:48** | `radio_link_local` | Primera fila `SM_NOT_ASSOCIATED`, sin métricas normales; nota generada por el colector, **no bitácora independiente de desasociación del firmware** |
| **19:38** | Conversación de campo | Se comenta un **adaptador asociado al puerto 3**, separado del problema posterior del puerto 6; no confundir los puertos |
| **19:38:42** | RF 5-min | Primer `COLLECTION_ERROR` al consultar el AP mediante SSH, `No route to host` |
| **19:43:45, 19:48:48, 19:53:52** | RF 5-min | Reintentos de lectura del AP fallan con `No route to host` |
| **19:57** | Conversación de campo | Responsable remoto solicita verificar el cable del **puerto 6** que parece haberse movido; pide priorizar recuperación del 6 sobre intervenciones al 3 |
| **19:59** | Conversación de campo | Personal local **confirma cable del puerto 6 movido y reconectado** |
| **19:59:06** | RF 5-min | Aún existe una lectura fallida SSH hacia el SM; el timestamp y duración del comando no acreditan qué sucedía precisamente al 19:59:00 |
| **19:59:52** | `radio_link_local` | Última fila `SM_NOT_ASSOCIATED` antes del reinicio de métricas normales |
| **20:00:53** | `radio_link_local` | Estado transitorio `UNEXPECTED_SM` con valores faltantes/sospechosos (0.0.0.0, RF cero); no usar como señal física válida |
| **20:01:53** | `radio_link_local` | Primera fila nuevamente `ok`, con MCS/SNR/RSSI válidos |
| **20:04:07** | RF 5-min | `LINK_OPERATIONAL_DUAL`, `sm_direct_access_ok=1`, DL/UL RSSI ~−74/−80 dBm y SNR ~23/18 dB |

**Cotas temporales:** la pérdida de telemetría normal aparece entre 19:36:37 y 19:37:48. La recuperación de lecturas normales aparece entre 20:00:53 y 20:01:53, y se reafirma a las 20:04:07. **No se conoce por estas muestras el instante exacto de desconexión física ni la duración de una eventual caída física del enlace RF.**

## 2. Identificación del equipo

En la bitácora interna de recuperación del enlace del **15-sep** quedó verificado el mapeo del cnMatrix de CU01: **puerto 6 = AP 6 GHz**; **puerto 3 = AP 5,8 GHz**, protegido. La conversación de **1-sep 19:38** menciona adaptador/puerto 3, pero a las **19:57–19:59** la recuperación se atribuye explícitamente a **cable movido del puerto 6**. No confundir reparación del adaptador del puerto 3 con reconexión de AP 6 GHz.

La evidencia temporal **establece con alta confianza una anomalía de acceso y observabilidad del AP/SM asociada a la reconexión reportada del cable del puerto 6**, en lugar de las fechas retrospectivas inicialmente recordadas (02 o 03-sep). Sigue sin verificarse con históricos originales del switch si **PoE del AP fue interrumpido**, si perdió alimentación, y cuánto tiempo el radio 6 GHz estuvo realmente desasociado.

## 3. Controles de fechas alternativas

- **02-sep, 18:00–19:59:** 24 de 24 observaciones RF con `LINK_OPERATIONAL_DUAL` y acceso al SM, y 16 de 16 pruebas throughput DL+UL `OK` con ping y ruta válidos. **No coincide con reconexión física de un AP apagado a esa hora**.
- **03-sep, 18:00–19:59:** mismo resultado; 24 RF `LINK_OPERATIONAL_DUAL` y 16 throughput `OK`.
- En el total 02–03-sep los estados se conservaron continuamente normales en las fuentes examinadas. La reconstrucción del **01-sep 19:37–20:04** es un candidato muy superior porque el documento contemporáneo nombra puerto 6 y la recuperación cerca de las 20:00.

## 4. Consecuencia metodológica FEDU

**Dos evidencias diferenciadas, ambas auditables:**

1. **Física/operativa:** el cable del **puerto 6** fue reportado como movido y vuelto a conectar a las **19:59** por personal en el sitio, contemporáneamente.
2. **Instrumental:** el controlador registró pérdida de métricas normales de AP/SM y fallos de acceso SSH desde ~19:37 y recuperación entre ~20:01 y ~20:04.

**Lo que NO queda acreditado aún:**
- Que el AP 6 GHz se haya apagado por ausencia de alimentación PoE: falta evento `PoE down/up` o estado de energía del switch.
- Una pérdida física RF durante toda la ventana: `SM_NOT_ASSOCIATED` derivado y `COLLECTION_ERROR` no equivalen a confirmación independiente por firmware.
- Que el episodio fuera anticipable por RF antes de ~19:37. Una desconexión física súbita **no debe computarse como fallo de un predictor de degradación progresiva sin reglas preregistradas**.
- Que este episodio corresponda a cualquiera de los ocho candidatos I4 construidos a partir de `iperf3 ERROR`; es un **incidente adicional, 01-sep**, distinto del 04-sep y 10-sep.

**Estado del expediente:** `RECONEXION_PUERTO6_CORROBORADA_POR_TESTIMONIO_CONTEMPORANEO_Y_RECUPERACION_TELEMETRICA`; `CAIDA_RF_FISICA_PENDIENTE_CONFIRMACION_INDEPENDIENTE`. Conservar conversación original con custodia del usuario y registrar cualquier exportación AP/SM/switch con huella y TZ; en GitHub solo resumen sin datos personales. **No introducir etiqueta ML ni modificar ocho fichas I4 todavía**.

## 5. Acción siguiente sin intervención en radios

Buscar en el histórico (si conservado) del **mismo cnMatrix**: `port6 link-down/link-up`, `PoE power-loss/restore`, eventos de asociación de AP/SM e indicios de reboot/uptime entre 19:30 y 20:15 del 01-sep. Una pérdida coincidente de PoE y AP + una confirmación del SM permitiría elevar la certeza de caída física. No controlar PoE, no reconfigurar switch y no ensayar una nueva desconexión para demostrar un evento pasado.
