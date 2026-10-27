# FEDU — Auditoría 007: prueba temporal acotada y catálogo de candidatos

**Fecha:** 27-10-2026, hora Perú. **Estado:** instrumentación piloto y cribado de episodios. Ninguna inferencia predictiva confirmatoria.

## A. Validación de `first_seen_at` sin interferencia operativa

Se ejecutaron **14 sondeos en 325 segundos**, separados en intervalos programados de 25 s (02:12:17 a 02:17:42, hora Perú), desde el controlador sobre SQLite productiva mediante `mode=ro` y `PRAGMA query_only=ON`. La base auxiliar de auditoría reside fuera de producción, con permisos restrictivos; fue inicializada previamente sin retroetiquetar filas históricas. No se instalaron servicios, timers ni tareas persistentes, y no se generaron pruebas iperf adicionales.

| Comprobación | Resultado |
|---|---|
| Polls programados / ejecutados | 14 / 14 |
| Polls con error | 0 |
| Registros nuevos de throughput capturados **durante el ensayo acotado** | 5 |
| Registros nuevos de RF capturados **durante el ensayo acotado** | 6 |
| Registros totales conservados en libro privado contando prueba previa manual | 6 throughput y 7 RF |
| Duplicación observada en ensayos sintéticos | Ninguna |
| Sin cambios de equipos RF ni servicio de adquisición | Confirmado por procedimiento |

Al comienzo del ensayo se recuperaron en un lote registros posteriores al último sondeo manual, por lo cual aparecen retrasos aparentes superiores a 10 minutos (hasta 1609,93 s para pruebas y 1330,93 s para RF). **Esos retrasos incluyen tiempo sin sondear**, y no miden retraso del colector.

En el lote incremental detectado alrededor de las **02:15:37**, el RF recién llegado tenía una diferencia `first_seen-observed` de **24,94 s**. Los dos registros TCP nuevos tenían diferencias **9,94 y 24,94 s**. Son cotas superiores conservadoras de primera visibilidad al observador, **no una medición exacta de `ingested_at`**.

El reloj del controlador figuraba sincronizado por NTP al comienzo de la jornada. La observación no permite extrapolar percentiles de latencia a una operación sostenida.

**Criterios aún abiertos:** continuidad y tolerancia a reinicios, observaciones tardías con ID previamente asignado, cobertura en dos estaciones meteorológicas, límites de sondeo/IO, desfases UTC y disponibilidad causal al instante de una emisión predictiva. El piloto **NO** habilita por sí solo una prueba confirmatoria.

## B. Cribado de candidatos históricos sin clasificación forzada

La copia del cierre 3×2 fue recorrida por [catalogar_candidatos_rf.py](../scripts/catalogar_candidatos_rf.py), junto con cronograma y bitácora de cambios; algoritmo exploratorio de agrupación si separación entre errores <=35 min y cercanía a transición <=90 min.

| Categoría de revisión (NO son etiquetas) | Grupos |
|---|---:|
| Cerca de transiciones de configuración | 14 |
| Incidencias bidireccionales fuera de guarda, NO verificadas | 8 |
| Otros errores de prueba, NO verificados | 5 |
| **Total** | **27** |

- El snapshot contiene **281** registros de pruebas activas con `ERROR`, agrupados en 27 grupos.
- **Antes del factorial 3×2:** 208 pruebas `ERROR` en tres grupos.
- **Durante el factorial:** 73 pruebas `ERROR` en 24 grupos; no son 24 degradaciones del RF.
- Hubo 18 grupos con errores temporales próximos del recolector, 13 con ping no OK y 7 con RSSI cero sospechoso.
- La bitácora `campaign_events.jsonl` comienza el 15-sep: NO sirve para inferir las causas de los grandes incidentes del 4 o 10 de septiembre.
- La salida privada de revisión incluye rangos temporales y banderas de evidencia; **no se publica la tabla de casos ni datos crudos**.

**Total de episodios de degradación RF independientemente corroborados en esta fase:** **0 corroborados**, que significa **pendientes de validación**, no inexistentes.

## C. Implicaciones para la metodología FEDU

El título no cambia. La hipótesis principal sobre anticipación de degradaciones **no se puede someter todavía a contrastación** con un catálogo de errores no verificados. Para avanzar, revisar las fichas I4: evidencia de red independientemente registrada, reloj/inicios intervalocensurados, reinicios de AP/SM o del colector propios del radioenlace, cambios de frecuencia/ancho, fallos iperf y categorización de indeterminados. No usar RSSI/SNR predictor como única prueba de verdad-terreno.

Solo después de corroborar un número adecuado de episodios debe congelarse `W/H`, umbrales y presupuesto de falsas alarmas. Si insuficiente, proponer revisión formal de pregunta, objetivo, hipótesis, variables, indicadores e instrumentos hacia pronóstico continuo de throughput y **actualizar anexos A/B antes de abrir test**. La evaluación retrospectiva ya realizada NO favoreció superioridad ML sobre persistencia en MAE; no ocultar ese resultado ni elegir RMSE retroactivamente.

**No se abrió test prospectivo**, no se instaló servicio de predicción y no se activó nueva campaña experimental.

## Nota de alcance: panel-solar excluido

**Rectificación de alcance:** el equipo remoto llamado `panel-solar`, los registros Growatt y sus servicios no intervienen en FEDU y **no se utilizaron en el catálogo derivado de la base SQLite de AtmosLink**. Los candidatos I4 deben revisarse únicamente con observaciones del radioenlace CU01–SJ01, sus radios, telemetría RF, pruebas de red y bitácoras de la propia infraestructura. Los errores TCP y RF siguen **indeterminados**, no atribuidos a energía, radio ni otra causa por extrapolación de sistemas ajenos.
