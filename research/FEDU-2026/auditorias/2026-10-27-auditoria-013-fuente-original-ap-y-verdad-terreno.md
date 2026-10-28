# FEDU — Auditoría 013: rescate de `show sta` original y control de etiquetas I4

**Fecha:** 27 de octubre de 2026 (hora Perú, UTC−05).  
**Alcance:** radioenlace CU01 AP — SJ01 SM de 6 GHz y fuentes AtmosLink. **Lectura retrospectiva, sin intervenciones RF ni de red.**  
**Propósito:** identificar cuánto aporta la respuesta **original** del AP a los ocho candidatos I4 y qué queda realmente indeterminado antes de entrenar modelos.

## I. Nuevo inventario de fuente histórica

Se encontró en la infraestructura original del mismo enlace un histórico local por día:
- `epmp_monitor/logs/raw_show_sta_YYYY-MM-DD.log`: respuesta cruda de consultas `show sta` al AP, aproximadamente cada minuto.
- `epmp_monitor/logs/agg_ap_YYYY-MM-DD.err.log`: stderr de adquisiciones, **sin marcas de tiempo por intento** suficientes para atribuirlas automáticamente a una captura.
- `epmp_monitor/data/agg_ap_YYYY-MM-DD.csv`: agregados de la misma adquisición.

Se inspeccionó `epmp_monitor/bin/capture_agg_ap.sh` y se verificó que invoca `ssh ... "show sta" 2>>ERR || true`. **La cláusula `|| true` anula la detección de error SSH en ese colector**, por lo que un bloque vacío en `raw_show_sta` **NO** significa desasociación: puede ser fallo de SSH/gestión. Los CSV y `radio_link_local` provienen de esta lectura o de la misma fuente AP; **no son corroboraciones independientes**.

La salida `Connected sessions:` es encabezado de **sesiones de administración SSH**, no una lista de estaciones RF. Si no aparece una tabla `[cambiumAPConnectedSTATable]` válida, clasificar como **respuesta sin tabla RF** y no como `SM desconectado` demostrado.

## II. Clases de observación, exclusivamente para el resumen original AP

- **`PEER_EXPECTED_IN_TABLE`**: `show sta` devolvió `cambiumAPConnectedSTATable` y `connectedSTAIP` con el IP esperado del SM. Evidencia de asociación reportada **en esa lectura**; no garantiza servicio extremo a extremo ni continuidad entre muestras.
- **`TABLE_OTHER_OR_ZERO_PEER`**: existe tabla de estaciones pero el `connectedSTAIP` no es el del SM esperado, incluyendo `0.0.0.0`. Es **respuesta inválida o incongruente para acreditar asociación al SM esperado**; no atribuir automáticamente fallo radioeléctrico.
- **`SSH_BANNER_NO_RADIO_TABLE`**: hay respuesta textual de sesión SSH, sin tabla `cambiumAPConnectedSTATable`. **Falta de evidencia RF interpretable**, no prueba de desasociación del firmware.
- **`NO_USABLE_RESPONSE`**: bloque sin contenido de respuesta interpretable. **Fallo/ausencia de observabilidad**, no prueba física.

**Nunca** convertir filas de los tres últimos grupos directamente en etiqueta `LINK_DOWN`.

## III. Auditoría exacta en las ocho ventanas (sin márgenes)

Los rangos horarios son los de los informes I4, con comparación inclusiva de los instantes de captura `YYYY-MM-DDTHH:MM:SS`. Los conteos son muestras AP **originales**, no eventos independientes.

| Caso | Capturas AP | SM esperado en tabla | Tabla con peer diferente / cero | Banner SSH sin tabla RF | Sin respuesta útil | Estado de etiqueta RF |
|---|---:|---:|---:|---:|---:|---|
| C001 | 30 | 22 | 0 | 4 | 4 | Indeterminado |
| C002 | 403 | 0 | 0 | **392** | 11 | Indeterminado |
| C003 | 1 040 | 0 | 0 | 0 | **1 040** | Indeterminado |
| C011 | 30 | 0 | 0 | 0 | **30** | Indeterminado |
| C016 | 15 | 0 | **8** | 7 | 0 | Indeterminado |
| C020 | 75 | **41** | **22** | 12 | 0 | Indeterminado |
| C022 | 105 | **2** | **31** | **72** | 0 | Indeterminado |
| C024 | 15 | **5** | **3** | 7 | 0 | Indeterminado |

**Corrección importante:** la primera clasificación exploratoria detectaba tablas presentes pero **no verificaba si el peer era realmente el SM esperado**; por ello habría sobreestimado asociaciones en C016, C020, C022 y C024. Los conteos anteriores son los corregidos y **ninguna asociación a `0.0.0.0` se cuenta como válida**.

### Interpretación limitada por caso

- **C001:** 22 muestras muestran el SM asociado dentro del grupo de ensayos con errores. No puede presentarse el grupo completo como caída RF continua.
- **C002:** 392 bloques del AP contienen únicamente encabezado SSH sin tabla RF entre aproximadamente 09:26 y 16:00. Conjuntamente con 56 errores TCP y predominio de fallos del otro colector, constituye un **candidato prioritario a auditar con registros nativos de asociación**, no un `RF_LINK_DOWN` automáticamente confirmado.
- **C003 y C011:** las capturas originales carecen de respuesta útil en las ventanas; **el AP no puede juzgarse desde esa fuente**. No implica falla del enlace.
- **C016:** hay tablas, pero **ninguna acredita peer esperado** en los 15 sondeos. Requiere registros propios del SM, fuente independiente funcional y régimen operativo.
- **C020:** 41/75 capturas sí acreditan asociación del SM esperado durante la ventana, aunque el colector de configuración RF tuvo 0 muestras válidas cercanas en la auditoría 008. **No concluir indisponibilidad RF continua**.
- **C022:** 2/105 capturas tienen peer esperado, 31 peer nulo/ajeno y 72 banner sin tabla. Posible alternancia de estado, pero no se puede equiparar a causa física ni afirmar una duración exacta.
- **C024:** 5/15 capturas contienen peer esperado, 3 peer inválido y 7 sin tabla. Los valores RSSI/SNR cero siguen inválidos.

**Fuentes no independientes:** el `raw_show_sta`, su CSV agregado y la tabla `radio_link_local` son tres representaciones de un mismo acto de adquisición. Igual advertencia para el colector de configuración: aunque ejecuta consultas AP y SM, comparte infraestructura de gestión y no se declara corroboración plenamente externa por simple coincidencia de estado.

## IV. Huellas SHA-256 de los originales privados (para repetibilidad)

Los archivos permanecen en el Controlador. Estas huellas describen la versión examinada, sin publicar datos RF detallados, direcciones o credenciales.

| Fecha del archivo `raw_show_sta` | SHA-256 |
|---|---|
| 2026-09-04 | `287d3de1900f53591981f68227983bfc5341d3a30a1e7b0969295aaa09381712` |
| 2026-09-10 | `b591b9f75675f74d75a33ef0d24be84ec7460bbacb3c5a9b14c3179b40b32033` |
| 2026-09-11 | `3fa55c1889c7ce311dc7cb7ac3945bec9ddacf49d4a8c5db9a7e82ca9a86c71b` |
| 2026-10-05 | `0ce09a660138b8c84f73ea655a4ff44d31cfde0554e69cc0f6298820303127f3` |
| 2026-10-13 | `410c9c6315adb25280b9fafb69ffb5c134ec53b46e263ef702221fd0d9079089` |
| 2026-10-21 | `d17a1b3e08a48a393622b6fb237d8bc777563fc8089f46f475ec64ba306c7150` |

**Reproducción:** [script de auditoría de capturas](../scripts/auditar_capturas_originales_ap_i4.py), que exige IP esperado del SM solo en configuración local, no lo imprime ni lo incorpora al repositorio.

## V. Decisión formal para FEDU al cierre de esta auditoría

**Dos tareas científicas distintas:**
1. **Registrar hechos observados**: estado de asociación del SM en instantes válidos (`PEER_EXPECTED_IN_TABLE`), anomalía del instrumento, fallo de prueba activa y eventos manuales verificables; cada hecho conserva su propia fuente.
2. **Etiquetar un episodio futuro de degradación funcional**: exigir criterio **independiente del vector de predictores** (ensayos funcionales válidos en ambos extremos o registro nativo AP/SM y conectividad verificable), con cobertura temporal suficiente y adjudicación ciega a predicciones ML. Faltas de evidencia producen `NA`, nunca `0`.

**Balance:** Ocho fichas I4 permanecen `INDETERMINADO_PENDIENTE_VERDAD_TERRENO` para la hipótesis de anticipación de degradación física; **0/8** están confirmadas bajo el criterio independiente de episodio RF. La evidencia nueva permite **descartar la simplificación de que todas las ventanas de ERROR son una caída continua del enlace** y priorizar de manera fundada qué exportar de cnMaestro/firmware.

**Próxima puerta de cierre:** exportación de eventos firmware AP/SM y del switch propio, cuando aún estén retenidos; local ping independiente y con marcas disponibles; decidir adjudicación usando tabla por evento antes de entrenar, congelar reglas y prueba temporal. Si las fuentes históricas faltan, consignarlo y fundamentar fase prospectiva de recopilación de verdad-terreno, no sustituir etiquetas por proxies sin declaración.
