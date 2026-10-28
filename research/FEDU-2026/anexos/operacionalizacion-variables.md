# Anexo B — Operacionalización de variables

| Variable/dimensión | Indicador y definición operacional | Escala / unidad / origen | Técnica / instrumento |
|---|---|---|---|
| **VI: método de monitoreo** | Estrategia que emite alertas sobre el inicio de evento en (t,t+H]: A=reglas de umbral; B=modelo supervisado ML congelado | Nominal A/B; manifiesto de modelo/umbrales | Comparación pareada; I6–I8 |
| **VD: anticipación correcta** | Recall por evento = episodios elegibles con ≥1 alerta válida previa / total de episodios elegibles | Proporción [0,1]; catálogo de episodios y alertas | Concordancia evento-alerta; I4, I7, I8 |
| **VD: control de falsos avisos** | Alertas sin correspondencia a episodio / 24 horas elegibles de observación | Tasa (alertas/24 h), logs de alarma | Agrupación de alertas y evaluación; I7, I8 |
| **VD: precisión de alertas** | Alertas válidas con evento asociado / total de alertas emitidas agrupadas | Proporción [0,1] | Comparación con verdad-terreno; I4, I7, I8 |
| **VD: anticipación temporal** | Tiempo entre primera alerta válida y comienzo documentado del episodio; expresar incertidumbre si tiempo inicial es intervalocensurado | Minutos (lead time) | Línea temporal y acta de episodios; I4, I8 |
| **VD: desempeño complementario** | PR-AUC, curva precisión–recall y calibración de probabilidad si el soporte de episodios lo permite | Escalas propias de cada índice | Pipeline de evaluación; I6, I7 |
| **Control: régimen RF/operativo** | Frecuencia, ancho, dirección, firmware, intervalo de intervención, condiciones de ensayo | Categórica / numérica; configuración y bitácoras | Segmentación y auditoría; I1, I3, I4 |
| **Control: calidad de observación** | Completitud %, frescura, retraso, desfase temporal, cobertura elegible | Porcentaje, segundos, minutos | Auditoría temporal; I1–I3 |

## Instrumentos normalizados I1–I8
- **I1:** inventario de arquitectura, fuentes, versiones, cadencias y flujo de datos.
- **I2:** script/acta de auditoría temporal y disponibilidad (observed_at/available_at).
- **I3:** reporte automatizado de calidad, completitud, exclusiones y regímenes.
- **I4:** ficha de verdad-terreno de episodio (evidencias, hora/rango de inicio, configuración).
- **I5:** script reproducible de extracción y etiquetado de ventanas; manifiesto de particiones.
- **I6:** especificación parametrizada del baseline convencional y manifiestos ML.
- **I7:** pipeline de entrenamiento, calibración y evaluación versionado.
- **I8:** registro de predicciones/alertas y acta de comparación por episodio con estimación de incertidumbre.

**Juicio de expertos (opcional/complementario):** especialistas en radioenlaces, software/ML y metodología pueden revisar pertinencia de criterios e instrumentos. Su opinión no sustituye los ensayos de funcionamiento ni la validación predictiva en prueba independiente.
