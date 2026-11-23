# Protocolo metodológico FEDU — borrador controlado

**Título sin modificación:** DESARROLLO E IMPLEMENTACIÓN DE UN SISTEMA INTELIGENTE BASADO EN APRENDIZAJE AUTOMÁTICO PARA EL MONITOREO PREDICTIVO DE RADIOENLACES RURALES UTILIZANDO TELEMETRÍA RF.

**Versión:** 0.1 (26-10-2026). Propuesta sujeta a auditoría de datos y fijación prospectiva de parámetros antes de abrir la prueba.

## Problema general
¿En qué medida un sistema inteligente basado en aprendizaje automático, implementado sobre AtmosLink y alimentado con telemetría RF temporalmente válida, mejora la anticipación de eventos de degradación de un radioenlace rural, respecto a un monitoreo convencional basado en umbrales, bajo el mismo límite de falsas alarmas?

## Preguntas específicas
1. ¿Cómo implementar y verificar un flujo reproducible de adquisición, sincronización y control de calidad de telemetría RF y métricas operativas en los dos extremos del radioenlace?
2. ¿Cómo definir y auditar eventos de degradación y construir ventanas de observación con etiquetas futuras, sin utilizar información posterior al instante de predicción?
3. ¿Cuál es el desempeño de los modelos candidatos para estimar el riesgo futuro de degradación y cuál es la contribución incremental de las variables ambientales locales?
4. ¿Qué diferencia presenta el modelo seleccionado frente a un sistema convencional de umbrales en eventos anticipados, falsas alertas y tiempo de anticipación en una prueba temporal independiente?

## Objetivo general
Desarrollar, implementar y validar un sistema inteligente basado en aprendizaje automático, integrado en AtmosLink, que utilice telemetría RF temporalmente validada para anticipar eventos de degradación en un radioenlace rural, comparando su capacidad predictiva con un esquema convencional de monitoreo mediante umbrales.

## Objetivos específicos
1. Implementar y verificar adquisición multisede, sincronización, trazabilidad y calidad de datos RF y de red.
2. Definir eventos verificables y construir un dataset de ventanas históricas con etiquetas de inicio futuro, auditables y sin fuga temporal.
3. Entrenar, calibrar y comparar modelos en particiones cronológicas y explorar mediante ablación el aporte incremental de meteorología local.
4. Comparar el modelo seleccionado con umbrales convencionales en prueba independiente, midiendo recall por evento, falsas alertas, anticipación e incertidumbre.

## Hipótesis principal y contraste
**H1:** el modelo de aprendizaje automático anticipa una mayor proporción de eventos independientes que un esquema convencional de umbrales con un límite comparable de falsas alertas y sobre idéntico periodo temporal no utilizado para ajuste.

- H0: ΔR = R_ML − R_U ≤ 0.
- H1: ΔR > 0.
- R: recall **por evento** antes de su inicio, a presupuesto de falsas alertas fijado en validación.
- Criterio propuesto de respaldo: límite inferior del IC del 95 % de ΔR > 0, con cumplimiento del presupuesto por ambos métodos; intervalos calculados con bloques/episodios completos. Revisar procedimiento exacto cuando se conozca el número de eventos.
- Si no hay suficientes eventos independientes (umbral orientativo: 20), no sostener superioridad confirmatoria: reportar desempeño observado, intervalos y limitación.

**Los objetivos de ingeniería (1 y 2) se verifican técnicamente; no precisan hipótesis estadísticas artificiales.** El aporte meteorológico se trata inicialmente como análisis secundario.

## Variables y unidades
- **VI:** método de monitoreo, dos niveles emparejados: A=umbrales; B=ML supervisado integrado en AtmosLink.
- **VD:** desempeño de anticipación de eventos: resultado principal, recall por evento a tasa de falsas alertas comparable; resultados secundarios, falsas alertas/24 h elegibles, precisión de alertas, tiempo de anticipación, PR-AUC y calibración.
- **Control/contexto:** frecuencia, ancho de canal, firmware, dirección de prueba, régimen de intervención, cadencia, disponibilidad de fuentes, meteorología y calidad de datos.
- Unidad computacional: ventana histórica elegible; unidad principal de inferencia: evento independiente o bloque temporal, **no cada fila**.

## Diseño
Investigación aplicada de desarrollo tecnológico; enfoque cuantitativo; observacional, longitudinal y no experimental para fallas y meteorología, con evaluación comparativa pareada de estrategias sobre las mismas observaciones. Muestreo intencional de un enlace real Cuñacales–San José (CU01/SJ01).

## Método reproducible — siete fases
1. **Auditar fuentes:** equipos RF, cnMaestro, logs, ping, iperf3 y meteorología CU01/SJ01; documentar cadencias, disponibilidad y respaldos.
2. **Validar tiempo y regímenes:** conservar observed_at, ingested_at, available_at y procedencia; deduplicar; aislar intervenciones y cambios de configuración; uniones temporales causales.
3. **Construir verdad-terreno:** criterio técnico independiente del predictor; episodio sostenido, inicio/fin e incertidumbre temporal registrados; congelar criterio tras piloto y antes de prueba.
4. **Construir ventanas predictivas:** propuestas iniciales W=60 min históricos y H=60 min futuros, a confirmar tras inspección de cadencia. Etiqueta positiva únicamente si inicia un episodio nuevo en (t,t+H]; etiqueta indeterminada si no hay cobertura o el episodio ya está activo; purgar solapamientos.
5. **Entrenar/calibrar:** baseline de umbrales, regresión logística regularizada y modelos de árboles/boosting cuando los eventos lo permitan; transformaciones y selección solo en entrenamiento/validación; ablación RF vs RF+ambiente.
6. **Evaluar ciegamente:** bloquear modelos, umbrales, reglas y presupuesto de falsas alertas; medir predicciones en tramo posterior reservado sin reoptimización; evaluar por episodios, no por filas.
7. **Integrar en AtmosLink:** inferencia en modo sombra y solo lectura; registrar versión, instante de emisión, horizonte, entradas disponibles, calidad del dato, resultado y alertas.

## Prevención de sesgos
- Prohibido incluir futuras observaciones, registros reanalizados que todavía no estaban disponibles, o eventos determinados con la propia salida del modelo.
- Prohibidas particiones aleatorias convencionales, optimización del test y seudorreplicación.
- Medir los dos métodos sobre los mismos episodios y periodo, con umbrales no deliberadamente desfavorables.
- Excluir o estratificar transiciones de configuración, cortes eléctricos, mantenimientos y periodos contaminados.
- Cuando la detección solo ocurre en muestreos discretos, el inicio es intervalocensurado: no fabricar hora exacta.

## Salida esperada (NO lograda todavía)
Protocolo de datos auditado, catálogo de episodios, modelos validados, comparación justa y componente predictivo integrado en AtmosLink.
