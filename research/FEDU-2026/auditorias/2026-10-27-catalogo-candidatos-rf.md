# FEDU — Auditoría 006: catálogo provisional de incidentes y verificación de verdad-terreno

**Fecha:** 27 de octubre de 2026 (Perú). **Datos utilizados:** snapshot SQLite posterior al cierre de la 3×2 con `quick_check=ok`, cronograma y bitácora de eventos preservados con manifest de hashes. **Nivel de evidencia:** cribado reproducible, no etiquetas confirmadas de degradación RF.

## Instrumento reproducible

[Script de catálogo de incidentes](../scripts/catalogar_candidatos_rf.py). Uso exclusivo de `sqlite3 mode=ro`; agrupa pruebas `status=ERROR` separadas por <=35 min y marca si están a <=90 min de una transición programada/registrada. Contrasta señales auxiliares: `ping_status`, `route_verified`, muestras de radio `collection_status`, RSSI cero/sospechoso e incidencias del cronograma. Los valores de guarda 35/90 min son parámetros **exploratorios**, no una verdad-terreno científica. El registro individual permanece en `candidate_review_private.csv` **solo en el controlador**, fuera de GitHub.

## Resultado del inventario

| Clasificación operativa del grupo (NO etiqueta RF) | Cantidad |
|---|---:|
| Coincidente con transición programada o registrada | **14** |
| Candidato bidireccional, todavía no corroborado | **8** |
| Falla de prueba no corroborada | **5** |
| **Total** | **27** |

- 281 pruebas con `status=ERROR`; las agrupaciones **no son 27 fallas físicas**.
- De esos registros, **208 errores** y **3 grupos** ocurrieron antes del comienzo del periodo factorial 3×2 (15-sep 00:00 Perú). **73 errores** y **24 grupos** ocurrieron durante el periodo factorial. La distinta procedencia impide asumir que los 281 errores reflejen el mismo régimen.
- 25 grupos tuvieron incidencias en DL y UL (esto, sin más fuentes, sigue siendo evidencia operativa, no causa física).
- 18 grupos tuvieron errores del colector RF próximos temporalmente.
- 13 grupos presentaron al menos una comprobación de ping diferente de OK en las mismas pruebas activas.
- 24 grupos incluyeron muestras RF con `LINK_OPERATIONAL...` cercanas, pero eso no indica necesariamente continuidad completa.
- 7 grupos contenían valores RF sospechosos (RSSI cero); no usarlos como muestras válidas.
- La bitácora de transición tiene `CONNECTIVITY_PROBE` desde 15-sep a 27-oct (1943 registros: 447 `OK`, 1496 `WAITING`), pero **`WAITING` no debe interpretarse como pérdida física de conectividad**: se usa dentro de un procedimiento de confirmación de secuencias de pruebas y requiere inspección contextual.

**Eventos RF confirmados por fuente independiente hasta esta auditoría: NINGUNO VERIFICADO.** Esta frase significa que **no hemos acreditado ninguno aún**, no que no hayan ocurrido degradaciones reales.

## Criterio recomendado de verdad-terreno I4 (POR APROBAR Y CONGELAR)

1. Establecer un desenlace futuro explícito **independiente de los predictores**: caída de servicio, indisponibilidad o degradación sostenida de una medición operativa independiente (no inferirla del código `ERROR` ni de RSSI que también se introduce en X).
2. Identificar el instante de inicio como intervalo entre última prueba sana y primera prueba anómala, si la cadencia es discreta; auditar inicio, recuperación, dirección y estado RF.
3. Exigir corroboración de bitácoras independientes (dispositivo y energía, red, servicio, mantenimiento) y asignar causa: RF posible, transporte/ruta, instrumentación, corte de alimentación, transición experimental, indeterminada.
4. Mantener categoría **indeterminada** en ventanas con datos ausentes o cortes instrumentales; no tratarlas como clase negativa.
5. Revisión técnica registrada con evidencia de cada caso y fecha; el revisor no debe conocer la predicción del modelo.
6. Congelar reglas, horizonte y elegibilidad **ANTES** de abrir prueba prospectiva.

## Consecuencia para el proyecto FEDU

La hipótesis general de anticipación de degradaciones **NO PUEDE CONTRASTARSE todavía** con estos datos sin validación independiente de episodios. La auditoría no justifica declarar ninguna victoria o fracaso de ML. El pronóstico de throughput medido es una tarea alternativa cuantitativamente viable, pero la persistencia superó a Ridge y boosting en MAE retrospectivo. Una eventual sustitución formal de la tarea primaria requiere actualizar pregunta, objetivo, hipótesis, variable independiente/dependiente, indicadores, técnicas e instrumentos en el cuerpo, y matrices de consistencia/operacionalización en anexos A/B, antes del test.

**Pendientes**: completar fichas I4 de los grupos más plausibles; revisar fuentes eléctricas y gestión de red sin intervenciones sobre radios; delimitar un bloque prospectivo realmente independiente; registrar `first_seen_at` de datos entrantes para reducir fuga temporal. 
