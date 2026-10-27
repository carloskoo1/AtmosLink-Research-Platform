# FEDU 2026 — Auditoría 005: evaluación retrospectiva de modelos (desarrollo)

**Fecha de ejecución:** 26 de octubre de 2026, hora Perú.  
**Clasificación:** DIAGNÓSTICO RETROSPECTIVO EXPLORATORIO. **No constituye contraste confirmatorio de la hipótesis FEDU ni prueba de operación en tiempo real.**

## 1. Material auditado

Se utilizó únicamente el dataset privado congelado en el controlador CU01 con corte del **26-10-2026 a las 22:10 −05:00**, 8 441 parejas X/y (7 955 con RF y 7 000 con RF+meteorología). Se verificaron SHA-256 antes del entrenamiento.

Los resultados con predicciones individuales y las huellas de salida se guardaron en la carpeta **privada** del proyecto FEDU; GitHub contiene solo código y agregados. Se utilizó un entorno Python aislado de producción con scikit-learn 1.7.2; no se modificaron servicios ni radios.

Código:
- [Evaluación temporal de desarrollo](../scripts/evaluacion_retrospectiva_desarrollo.py)
- [Ablación de idéntica cohorte RF/clima](../scripts/ablacion_cohorte_comun.py)
- [Protocolo complementario](../protocolo-pronostico-throughput.md)

## 2. Diseño temporal y criterios

**Pronóstico:** throughput TCP activo medido con iperf3 en el mismo régimen/dirección, H=60 min; X contiene cuatro medidas previas con datos RF/meteorología solo si su marca observacional no excedía t.

Se ejecutaron dos ventanas retrospectivas, con separación de al menos 48 horas:

| Ventana | Entrenamiento antes de | Evaluación | n historia | n historia+RF | n historia+RF+clima |
|---|---|---|---:|---:|---:|
| D1 | 29-sep 00:00 | 01-oct a 09-oct | 1 561 | 1 415 | 1 403 |
| D2 | 13-oct 00:00 | 15-oct a 26-oct | 2 026 | 1 986 | 1 970 |

**Modelos con hiperparámetros fijados en script antes de ejecución:** persistencia t0; mediana de cuatro valores; Ridge(alpha=10), con imputación y escalado aprendidos SOLO del entrenamiento; HistGradientBoostingRegressor(120 iteraciones, 15 hojas, tasa 0,05, L2 1). Sin partición aleatoria de filas ni reajuste sobre el periodo de evaluación. Los intervalos por bootstrap de días (600 remuestreos, semilla 42) son meramente descriptivos.

## 3. Resultados: cohorte de historia sola

### MAE, menor es mejor (Mbps)

| Modelo | D1 (n=1 561) | D2 (n=2 026) |
|---|---:|---:|
| **Persistencia** | **3,344** | **4,772** |
| Mediana cuatro | 3,723 | 5,040 |
| Ridge | 3,862 | 5,370 |
| Boosting de árboles | 4,319 | 5,695 |

**ΔMAE = MAE(persistencia) − MAE(modelo).** Es negativo para Ridge: −0,518 Mbps (D1; IC descriptivo días [−0,701, −0,326]) y −0,598 Mbps (D2; [−1,060, −0,180]). No se evidencia reducción del MAE respecto a persistencia en estos cortes.

### RMSE, menor es mejor (Mbps)

| Modelo | D1 | D2 |
|---|---:|---:|
| Persistencia | 7,417 | 9,820 |
| Ridge | **7,018** | **9,233** |
| Boosting de árboles | 7,375 | 9,867 |

Ridge logra RMSE más bajo pese a un MAE superior; esto sugiere diferencias en errores extremos, pero NO autoriza una hipótesis reformulada a posteriori sin preregistro y prueba independiente.

### Resultados por dirección: MAE persistencia (Mbps)

| Dirección | D1 | D2 |
|---|---:|---:|
| Descarga (DL) | 4,227 | 6,339 |
| Subida (UL) | 2,456 | 3,182 |

Mantener dirección como estrato sustantivo, junto con frecuencia/ancho y régimen. No interpretar diferencias descriptivas como efectos causales.

## 4. Ablación justa con EXACTAMENTE la misma cohorte

Se fijaron las mismas filas en las tres condiciones (n D1=1 403; n D2=1 970), y **se reentrenaron** los modelos de cada condición sobre el mismo conjunto de entrenamiento (n D1=2 465; n D2=4 697). Por tanto, las diferencias NO se deben al tamaño desigual de las cohortes.

**MAE Boosting (Mbps):**

| Predictores | D1 | D2 |
|---|---:|---:|
| Solo historia | 4,543 | 5,677 |
| Historia + RF | 4,400 | 5,789 |
| Historia + RF + clima | 4,248 | 5,632 |
| Persistencia (referencia misma cohorte) | **3,483** | **4,828** |

El clima produjo ligera mejora interna del boosting respecto de solo historia, pero los modelos continúan peores que la persistencia en MAE. **No se evidencia ganancia robusta y concluyente de meteorología**. En Ridge, el MAE fue 3,997/5,460 (historia), 4,205/5,450 (historia+RF) y 4,228/5,542 (con clima), sin mejora consistente de su inclusión.

## 5. Limitaciones determinantes

1. **No se ha probado `available_at` ni `ingested_at` operacional** en datos históricos; marca observada <= t no demuestra recepción antes de la predicción.
2. Los pares contienen solo resultados FUTUROS de pruebas OK. Los fallos/muestras ausentes no se imputaron como throughput 0: el modelo puede parecer mejor en tramos observables que durante incidentes.
3. Los periodos D1/D2 son **retrospectivos y ya inspeccionados** durante el desarrollo del proyecto: son validación de ingeniería, no un test intacto.
4. Un solo radioenlace físico en dos puntos: no hay replicación espacial ni generalización externa.
5. Las ventanas de muestra solapan historia y horizontes; bootstrap por días sigue siendo exploratorio con dependencia entre días y pocos bloques.
6. Campaña 3×2 cambió deliberadamente frecuencia/ancho: segmentar y excluir transiciones, evitando atribuir diferencias al clima.
7. Hiperparámetros y variables elegidos con fines de desarrollo; toda decisión final debe congelarse **antes** de mirar el próximo periodo prospectivo.

## 6. Decisión y siguiente hito

**No confirmar superioridad de ML frente a persistencia en MAE** con esta evidencia. Conservar el título aprobado FEDU y la hipótesis primaria de anticipación de episodios mientras se verifica verdad-terreno independiente.

Para una eventual hipótesis de pronóstico continuo, formular ANTES de la prueba la relación de variables, objetivo y criterio de contraste completo; elegir una sola métrica principal y evitar seleccionar el RMSE retrospectivamente porque Ridge resultó favorable.

Preparar, sin activar aún en producción, un registro de disponibilidad temporal de futuras mediciones que distinga:
- `observed_at`: instante de medición,
- `first_seen_at`: primera vez que un proceso de lectura capturó el registro,
- `available_at`: disponibilidad real verificada (si es demostrable), de lo contrario NA.

No implementar servicios adicionales ni modificar adquisición mientras no exista acta de cierre de la campaña 3×2. La evaluación prospectiva en régimen estable deberá mantenerse sin inspección para ajuste de modelos.
