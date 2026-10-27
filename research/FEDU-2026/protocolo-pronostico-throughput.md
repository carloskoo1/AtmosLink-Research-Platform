# FEDU 2026 — Protocolo complementario de pronóstico de throughput activo

**Versión:** 0.1, 26 de octubre de 2026. **Estado:** pre-registro metodológico propuesto; no se ha entrenado ni validado un predictor FEDU conforme a este protocolo.  
**Título aprobado, sin modificación:** DESARROLLO E IMPLEMENTACIÓN DE UN SISTEMA INTELIGENTE BASADO EN APRENDIZAJE AUTOMÁTICO PARA EL MONITOREO PREDICTIVO DE RADIOENLACES RURALES UTILIZANDO TELEMETRÍA RF.

> Este documento desarrolla una línea predictiva complementaria. **No sustituye de manera automática la hipótesis principal de anticipación de episodios**. La decisión de convertirlo en objetivo principal requiere un cambio formal y simultáneo de pregunta, objetivo, hipótesis, variables, indicadores e instrumentos ANTES de reservar/evaluar datos prospectivos.

## 1. Justificación empírica y delimitación

Inventario de solo lectura del nodo CU01 (corte nocturno del 26-10-2026):
- 9 709 pruebas activas de red; 9 428 con estado OK y 281 ERROR.
- 9 367 de las pruebas OK incluyen frecuencia y ancho de canal; 61 no los identifican.
- Existen observaciones para seis combinaciones de frecuencia/ancho, y ambas direcciones DL y UL.
- El intervalo mediano entre pruebas de una misma dirección dentro del régimen es de aproximadamente 15 minutos; **hay huecos y periodos sin cobertura**.
- No se confunde `measured_throughput_mbps` de iperf3 con la tasa negociada `reported_dl_link_rate_mbps`.
- Las dos estaciones meteorológicas tuvieron `both_weather_stations_matched=1` en 15 258 de 15 639 registros científicos al corte previo: coincidencia de marcas de tiempo no demuestra disponibilidad causal ni integridad de variables.
- Es un único enlace físico CU01–SJ01: no generalizar a otros sin replicación.

Estas cifras describen **datos adquiridos**, no calidad predictiva ni disponibilidad de un test prospectivo.

## 2. Pregunta y objetivo complementarios (NO activos como hipótesis principal)

**Pregunta complementaria:** ¿En qué medida un modelo de aprendizaje automático, alimentado con telemetría RF histórica y contexto de operación disponible antes de la predicción, reduce el error de pronóstico del throughput activo a 60 minutos frente a la persistencia temporal, en periodos estables del radioenlace rural estudiado?

**Objetivo complementario:** Diseñar y evaluar modelos reproducibles de pronóstico a 60 minutos del throughput TCP activo medido por iperf3 en DL y UL, comparándolos en periodos cronológicamente posteriores con persistencia y mediana móvil, y evaluando de forma secundaria la contribución de datos ambientales locales.

**Hipótesis técnica candidata, solo si se formaliza como principal:** H0: MAE_ML >= MAE_persistencia; H1: MAE_ML < MAE_persistencia, bajo la misma población de pares pronóstico–medición y el mismo régimen de operación. El contraste primario será bilateral/direccional emparejado en bloques de días; fijar la regla de decisión antes de la prueba.

## 3. Variable respuesta, unidad y horizonte

- **Y(t+H):** throughput TCP medido en Mbps de una prueba iperf3 futura EXITOSA en la **misma dirección**, con H=60 minutos como horizonte principal. H=15 minutos es un análisis secundario.
- **X(t):** información observada y **disponible para el sistema en t**: métricas RF RF/MCS, últimas mediciones activas de esa dirección, frecuencia/ancho actuales, estado de la fuente, y opcionalmente meteorología local causal.
- **Unidad observacional:** pareja anclada (t, t+H), dentro de la misma configuración estable; **unidad de incertidumbre:** bloque temporal por día/episodio, no fila independiente.
- **Tolerancia propuesta de emparejamiento del objetivo:** ±4 minutos del instante t+H. Cada prueba futura se asigna como máximo una vez por origen en el protocolo final; auditar duplicados y evitar emparejamiento oportunista.
- Una prueba futura ERROR, ausente o sin ruta válida se identifica como **objetivo no medido / censurado**, **nunca** se convierte en throughput=0 ni se imputa usando el futuro.
- Reportar por separado cobertura de pronósticos y fallos de medición para evitar el sesgo de evaluar únicamente periodos favorables.

## 4. Predictores y controles

**Mínimos RF/Red:** RSSI DL/UL, SNR DL/UL, MCS DL/UL, throughput TCP pasado medido, historial de retransmisiones y RTT disponible, tasa de pérdidas si existe; fecha, dirección y configuración.

**Historia:** últimas cuatro pruebas elegibles del mismo régimen (hasta ~60 minutos), retardos t-15, t-30, t-45, t-60 y resúmenes móviles causales. No cruzar reinicios ni saltos de régimen. No utilizar un dato de la prueba futura como entrada.

**Ablación secundaria:** (A) historia de throughput + configuración; (B) + RF; (C) + meteorología CU01 y SJ01 local sincronizada. ERA5-Land/NASA POWER histórico o reanálisis solo si se demuestra que el dato estaba publicado en t; en caso contrario fuera del modelo operativo.

## 5. Elegibilidad y reglas de calidad

1. Usar únicamente `status=OK`, `route_verified=1`, throughput activo válido y configuración completa; registrar exclusiones y sus razones.
2. Valores simultáneos SNR=0 y RSSI=0 o campos nulos/incompatibles: dato RF **sospechoso/no elegible** hasta corroboración; no codificarlos como desvanecimiento.
3. Para características externas: `observed_at <= available_at <= t`. Si `available_at` falta o es dudoso, aplicar lag conservador documentado o excluir la fuente.
4. Excluir t cuyo historial o horizonte cruce una transición programada o recuperación. Usar guarda a ambos lados de la transición igual a la ventana máxima de historia más H; regla definitiva antes del test.
5. Mantener DL y UL separados en los reportes, e identificar el régimen de frecuencia/ancho.
6. No utilizar filtrado de anomalías sobre toda la serie antes de separar datos. Transformadores e imputación aprendidos solo en entrenamiento.

## 6. Modelos y referencias (evaluación justa)

- **P0: persistencia:** predice la última medición válida de la misma dirección y configuración.
- **P1: mediana causal:** mediana de las últimas cuatro mediciones válidas.
- **P2: regresión Ridge:** referente paramétrico entrenado, con escalado aprendido solo en entrenamiento.
- **M1: HistGradientBoostingRegressor:** modelo no lineal de tabulares, con ajuste solo por validación.
- Un modelo adicional solo se admitirá si está justificado previamente; no añadir un LSTM por estética o sin soporte experimental.

El conjunto de predictores y las mismas filas elegibles se utilizarán para la comparación pareada.

## 7. Separación temporal, estimando principal y regla de contraste

### Validación retrospectiva exploratoria
Bloques cronológicos sobre las repeticiones 3+2+2 de campaña 3×2, con separación/purga del máximo historial + horizonte. Nunca mezclar aleatoriamente filas del mismo experimento. Esta comparación mide **estabilidad de entrenamiento y calidad de pronóstico histórica**, pero los periodos ya fueron inspeccionados descriptivamente: no presentarlos como test intacto.

### Validación prospectiva confirmatoria (condicionada)
Reservar periodos posteriores al cierre real de 3×2, con configuración operativa estable y sin reoptimización. **No suponer que el régimen poscampaña reproduce las seis combinaciones**. Si solo existe una configuración futura, limitar la inferencia principal a ella y a las direcciones medidas. Duración sugerida: al menos 14 días de registro elegible y preferentemente 28, **sujeta a cobertura y régimen real**.

Antes de abrir el tramo de prueba deben registrarse en GitHub con commit: reglas de calidad, fecha de corte, modelo e hiperparámetros elegidos, historia, horizonte, guardas, referencia y regla estadística. No leer la prueba para elegir el método.

### Desempeño principal y secundario
- **Primario:** MAE en Mbps para H=60, con diferencia apareada `ΔMAE = MAE_persistencia - MAE_ML`.
- **Secundarios:** RMSE, mediana del error absoluto, sesgo, proporción de pronósticos disponibles, MAE H=15, desagregación DL/UL, por régimen y ablación meteorológica.
- **Incertidumbre:** intervalo de confianza de ΔMAE mediante bootstrap por **días completos**, evitando tratar muestras de 15 min como independientes. Informar número real de días elegibles.
- Considerar diferencia favorable solo si ΔMAE>0 y el intervalo al 95 % excluye 0 por el lado de mejora bajo el procedimiento fijado. Si cobertura, días o régimen no permiten este contraste, declarar resultado exploratorio y su incertidumbre.

## 8. Trazabilidad pregunta–variable–indicador–instrumento

| Elemento | Definición | Indicador / unidad | Instrumento |
|---|---|---|---|
| Pregunta/objetivo complementarios | Pronosticar throughput TCP futuro medido a 60 min | ΔMAE frente a persistencia | I9 – generador de pares causales |
| Independiente, método predictivo | Persistencia, mediana, Ridge y ML | Categoría nominal; versión de modelo | I10 – manifiesto de modelos y parámetros |
| Dependiente, error predictivo | Distancia entre forecast y medición futura | MAE, RMSE (Mbps), sesgo | I11 – evaluación emparejada |
| Control, régimen | Dirección y frecuencia/ancho, switches/mantenimiento | Régimen, elegibilidad de bloques | I3/I4 – bitácora y calidad de fuentes |
| Control, latencia y trazabilidad | Datos disponibles en t | % de predicciones con fuentes frescas; exclusiones | I2/I9 – auditor de causalidad temporal |

I9: script de pares t / t+H sin mirar futuro en X; I10: manifiesto de parámetros/semillas; I11: reporte de pérdidas apareadas e IC por día.

## 9. Puerta de decisión científica

El proyecto principal conservará su hipótesis de episodios hasta que una auditoría de evidencia independiente determine si hay episodios suficientes para contrastarla. Si no los hay, **antes de analizar el test** debe aprobarse una sustitución integral y simultánea de pregunta, objetivo, hipótesis, operacionalización, instrumentos y matriz de consistencia. La mera presencia de 9 000+ mediciones no resuelve la falta de episodios corroborados.

## 10. Controles de seguridad y declaración de resultados

Protocolo exclusivamente analítico, inicial en modo sombra: **sin cambiar frecuencia, canal, potencia, temporizadores ni plan de adquisición; sin pruebas iperf adicionales**. No publicar datos crudos, direcciones de administración, credenciales, configuración sensible o resultados no verificados. No informar que el predictor está entrenado/validado hasta que existan sus manifiestos, logs y tablas reproducibles.

Referencia interna: [Plan de datos y validación](plan-de-datos-y-validacion.md); [Auditoría de calidad y etiquetas](auditorias/2026-10-26-calidad-etiquetas.md).
