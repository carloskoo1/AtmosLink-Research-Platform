# Plan de datos, verdad-terreno y evaluación — pre-registro técnico

**Estado: por auditar / parámetros preliminares.** No declarar predicción demostrada ni métricas calculadas con estos archivos.

## 1. Origen y disponibilidad de cada observación
Unificar datos de telemetría RF, pruebas activas IP y sensores ambientales por fuente y estación. Cada muestra debe contener como mínimo:
- `station_id`, `link_id`, `source_id`, `metric_name`, `value`, `unit`.
- `observed_at_utc` (momento observado), `ingested_at_utc` (ingreso a repositorio), `available_at_utc` (momento real en que podía usarse para predecir).
- `quality_code`, `configuration_id`, `campaign_phase`, `direction`, `software_version`.

No usar un dato meteorológico de reanálisis posterior como si hubiera estado disponible al momento `t`. Evitar uniones por mera cercanía de marcas temporales cuando la fuente es vieja o no comparable.

## 2. Segmentación de regímenes
Identificar por bitácora las combinaciones frecuencia/ancho, mantenimiento, cortes, cambios automáticos, reinicios y operaciones de prueba. Separar la campaña factorial 3×2 de la fase de validación prospectiva estable; impedir que una transición deliberada se etiquete como fallo espontáneo.

## 3. Definición verificable de episodio
Definir el evento primario a partir de evidencia de servicio **independiente de los predictores** cuando sea posible. Propuesta exclusivamente piloto (NO congelada):
- caída sostenida del throughput medido ≥30 % respecto de la mediana de régimen/dirección en dos pruebas consecutivas; o
- pérdida de paquetes ≥1 % en dos ventanas contiguas; o
- falta de conectividad ≥2 min si la cadencia real es suficiente.

Auditar la resolución temporal del criterio; establecer inicio, fin y recuperación del episodio. Cuando faltan medidas, etiqueta **indeterminada**, no negativa automática. Anotar incidentes por operación, energía, hardware o meteorología sin asumir causa.

## 4. Tarea pronóstica
- Momento `t`: emitir una probabilidad de que se **inicie un evento nuevo** en el intervalo futuro `(t,t+H]`.
- Historia candidata `W=60 min`; horizonte candidato `H=60 min`; ambos dependen de auditoría piloto y se congelarán ANTES del test.
- `y_t=1` si comienza evento nuevo dentro del horizonte con evidencia suficiente; `y_t=0` si hay observación completa sin evento; `y_t=NA` si falta cobertura o ya hay un evento activo.
- Nunca usar ventanas del episodio o futuro dentro de características de entrada.

## 5. Partición y selección
Dividir cronológicamente `train → validation → test`, purgando cruces por ventanas `W+H`. Ajustar limpieza con parámetros aprendidos, escalado, imputación, selección de variables, hiperparámetros, umbrales y presupuesto de falsas alertas sin mirar test. Seleccionar método con protocolo previamente acordado.

## 6. Comparador justo
Evaluar baseline de umbrales y ML en el mismo tramo y con igual definición de episodio. Fijar en validación un presupuesto de falsas alertas por 24 h elegibles; no retocar después. Consolidar alarmas consecutivas antes de contar falsos avisos.

## 7. Métrica primaria y decisión
`R = episodios correctamente anticipados / episodios elegibles`; `ΔR = R_ML - R_umbrales`.
- Resultado primario: diferencia de recall **por episodio** al mismo presupuesto de falsos avisos.
- Secundarios: falsas alertas por 24 h, precisión de alertas, lead time, PR-AUC, calibración y rendimiento desagregado.
- Incertidumbre: intervalos al 95 % respetando dependencia por bloques de días y episodios; no asumir independencia de filas de un minuto.
- Si la prueba no reúne eventos suficientes, reportar viabilidad y métricas con incertidumbre, **no** afirmar confirmación de superioridad.

## 8. Checklist para abrir la prueba final
- [ ] Inventario de fuentes/cadencias y calidad firmado o validado.
- [ ] Criterio de episodio, rangos y límites fijados por protocolo.
- [ ] `W`, `H`, purga y exclusiones congelados.
- [ ] Particiones y manifiestos versionados con hashes.
- [ ] Modelos, umbrales y límite de falsas alertas fijados.
- [ ] Periodo de evaluación reservado y no inspeccionado para ajuste.
- [ ] Registro en modo sombra habilitado, con reloj de emisión y calidad de entrada.

**Seguridad:** nunca subir bases de datos crudas no revisadas, .env, APIs, secretos o credenciales.
