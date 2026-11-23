# Anexo A — Matriz de consistencia y trazabilidad

**Proyecto FEDU 2026.** Los objetivos de ingeniería se verifican con criterios de aceptación; la hipótesis confirmatoria se reserva a la comparación final. Ver [protocolo](../protocolo-metodologico.md).

| Pregunta | Objetivo | Hipótesis o criterio | Variable / indicador | Técnica e instrumento |
|---|---|---|---|---|
| PG: ¿ML anticipa más episodios que umbrales al mismo nivel de falsas alertas? | OG: desarrollar e implementar AtmosLink predictivo y validarlo comparativamente | HG/H1: ΔR=Recall_ML−Recall_umbrales>0 en prueba temporal independiente | VI método A/B; VD recall **por episodio**, falsas alertas por 24 h elegibles, lead time | Comparación pareada de episodios; I4, I6, I7, I8; IC por bloques |
| PE1: ¿Cómo obtener fuentes temporalmente utilizables? | OE1: adquirir, sincronizar, trazar y controlar calidad | Criterio de ingeniería: fuentes, continuidad, frescura, procedencia verificables | Completitud %, cobertura temporal, desfase, porcentaje válido | Observación automatizada y auditoría; I1–I3 |
| PE2: ¿Cómo definir eventos y ventanas sin fuga temporal? | OE2: construir protocolo de episodios y dataset con etiquetas futuras | Criterio de ingeniería: etiquetas, ventanas, particiones y reglas documentadas y reproducibles | % episodios auditados; % ventanas elegibles; auditoría de available_at | Revisión de registros, catálogo, prueba de reconstrucción; I2–I5 |
| PE3: ¿Qué modelos estiman mejor riesgo futuro y qué añade meteorología? | OE3: evaluar modelos y análisis exploratorio de ablación | Comparación **secundaria/exploratoria**, no una superioridad confirmatoria añadida | PR-AUC, recall, calibración y diferencias RF vs RF+ambiente | Particiones cronológicas, reporte de modelos; I5–I7 |
| PE4: ¿Qué diferencia muestra ML frente a umbrales en el periodo reservado? | OE4: cuantificar ΔR, falsas alarmas, precisión, anticipación e incertidumbre | Contraste principal H0/H1 bajo presupuesto equivalente de falsas alarmas | Δ recall por episodio; falsas alertas/24 h; precisión; mediana lead time; IC95 % | Evaluación ciega por episodio y bootstrap por bloques; I4, I6–I8 |

**Lectura de la matriz:** PG/OG/HG y PE4/OE4 articulan un único contraste primario. PE1–PE2 son verificaciones técnicas; PE3 es selección de modelos y estudio secundario.
