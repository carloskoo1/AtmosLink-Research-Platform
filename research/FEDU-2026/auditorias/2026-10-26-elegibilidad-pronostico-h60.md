# FEDU — Auditoría 003 de elegibilidad para pronóstico de throughput (H=60 min)

**Fecha de consulta:** 26 de octubre de 2026, Perú.  
**Estado:** corte retrospectivo exploratorio de una base en ejecución, **NO** resultados de modelo ni evidencia de causalidad operacional completa.  
**Fuente:** tabla `active_throughput_6g` de AtmosLink CU01; bitácora y cronograma 3×2.  
**Instrumento:** [auditar_pares_causales_h60.py](../scripts/auditar_pares_causales_h60.py), SQLite de **solo lectura**, sin cambiar la red ni iniciar iperf3.

## Procedimiento para construir pares temporales compatibles

1. Ancla `t`: finalización de una prueba TCP real (`timestamp_end_local`). El instante de **ingestión/disponibilidad efectiva todavía no está registrado**. La consideración temporal es provisional.
2. Seleccionar únicamente mediciones `OK`, con ruta verificada, ping OK, Mbps finitos no negativos y configuración conocida (6475, 6655, 7000 MHz × 20/40 MHz; DL o UL).
3. Exigir cuatro mediciones consecutivas previas o hasta el ancla, separadas entre 9 y 21 min y contenidas dentro de 60 min; no cruzar huecos relevantes.
4. Excluir anclas con cambios de configuración programados o de la bitácora dentro de `[t−90 min, t+90 min]`, para proteger historia, futuro y estabilización.
5. Buscar objetivo válido de la misma dirección y configuración a `t+60 min ±4 min`; ausencia/error de prueba futura significa *sin objetivo medido*, **no** rendimiento igual a cero.
6. Exigir para cohorte RF marca de telemetría no posterior a `t`, como máximo 10 min anterior, RSSI DL/UL válidos negativos y SNR numéricos. No aceptar `RSSI=0 dBm` como señal normal.
7. Exigir adicionalmente para cohorte RF+meteorología dos marcas locales CU01 y SJ01 no futuras y con antigüedad máxima 10 min, además de temperatura, humedad y presión numéricas.
8. Contabilizar cada dirección y régimen por separado; los pares solapados **no son observaciones estadísticamente independientes**.

## Resultado agregado del corte

| Filtro acumulativo | Registros o anclas |
|---|---:|
| Pruebas activas inspeccionadas | 9 711 |
| Pruebas con calidad mínima y régimen completo | 9 365 |
| Con historia de cuatro mediciones compatible | 8 805 |
| Luego de excluir proximidad a cambios de régimen | 8 519 |
| Con objetivo futuro disponible a 60 ±4 min | **8 443** |
| Además con RF disponible según marca observacional | **7 957** |
| Además con meteorología local bilateral temporalmente compatible | **7 002** |

Hubo **286** anclas excluidas después del filtro de historia por proximidad a intervenciones y **76** sin objetivo futuro coincidente entre las 8 519 anclas restantes. El examen cubrió **51 días calendario con anclas elegibles**, no 51 días independientes necesariamente ni 51 días de cobertura completa.

### Distribución final por escenario

| Frecuencia MHz | Canal MHz | Pares throughput DL | Pares throughput UL | Pares RF+ambiente DL+UL |
|---|---:|---:|---:|---:|
| 6475 | 20 | 611 | 606 | 842 |
| 6475 | 40 | 618 | 613 | 833 |
| 6655 | 20 | 358 | 346 | 703 |
| 6655 | 40 | 619 | 619 | 878 |
| 7000 | 20 | 1 661 | 1 644 | 3 049 |
| 7000 | 40 | 374 | 374 | 697 |
| **Total** | | **4 241** | **4 202** | **7 002** |

## Hallazgos que limitan la inferencia

- **No hay `ingested_at` / `available_at` demostrado** en el esquema de las tablas examinadas. Que el dato esté fechado antes de `t` **no prueba** que fuera conocido por el predictor antes de emitir su decisión.
- Se usaron únicamente pruebas futuras `OK` para construir objetivos numéricos; esto puede subrepresentar los periodos de indisponibilidad. Debe publicarse cobertura y análisis de sesgo por ausencia de resultado.
- La cohorte de 7 002 pares no demuestra que meteorología mejore pronósticos: la ablación es una pregunta todavía abierta.
- El régimen 7000 MHz/20 MHz tiene considerablemente más pares que otros; promedios globales deben complementarse con estratos por dirección/configuración y comparación de períodos.
- Los cambios de configuración 3×2 requieren segmentación y guardas, pues no son degradaciones espontáneas.
- El número de pares **no** equivale a número de fallas confirmadas ni al tamaño muestral independiente para inferencia. Usar días o bloques en el cálculo de incertidumbre.
- Sin periodo prospectivo intacto y sin resultados de modelos, NO afirmar capacidad predictiva validada.

## Decisión metodológica adoptada

Se declara **factible preparar** un dataset retrospectivo de pares `(t, t+60)` para los modelos de throughput. No se declara construido un dataset de operación predictiva con disponibilidad causal certificada. La tarea sigue siendo **complementaria** mientras el proyecto conserva la hipótesis principal sobre episodios de degradación.

### Para convertirlo en prueba independiente

1. Incorporar, para datos **futuros**, trazas `observed_at`, `ingested_at`, `available_at`, versión del modelo y registro de emisión; instrumentar primero en una rama y desplegar solo cuando no comprometa las campañas.
2. Fijar elegibilidad, régimen, rezagos de fuente, ventanas, límites y referencias en un commit anterior al tramo de prueba.
3. Registrar y reservar un bloque cronológicamente posterior al cierre real de 3×2, sin optimizar sobre él.
4. Evaluar el mismo conjunto elegible contra persistencia, mediana móvil, Ridge y ML; reportar MAE/RMSE por dirección/configuración, cobertura y bootstrap por días.
5. Mantener como pendiente la validación independiente de episodios de degradación para la hipótesis principal.

**Confidencialidad:** sin rutas internas de gestión, credenciales, nombres de personas ni dumps. Este documento publica solo agregados técnicos.
