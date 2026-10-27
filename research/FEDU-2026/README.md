# Proyecto FEDU 2026 — AtmosLink

**Título aprobado (no modificar):** DESARROLLO E IMPLEMENTACIÓN DE UN SISTEMA INTELIGENTE BASADO EN APRENDIZAJE AUTOMÁTICO PARA EL MONITOREO PREDICTIVO DE RADIOENLACES RURALES UTILIZANDO TELEMETRÍA RF.

**Estado al 26-10-2026:** protocolo metodológico en revisión y documentación reproducible en preparación. **No se declara todavía un modelo predictivo validado ni una mejora demostrada frente a umbrales.**

## Propósito
Desarrollar y validar sobre AtmosLink una capa predictiva que estime, con datos disponibles hasta el instante de emisión, el inicio futuro de episodios de degradación del enlace rural Cuñacales–San José; compararla con una referencia convencional basada en umbrales bajo un presupuesto comparable de falsas alertas.

## Delimitación científica
- Caso de estudio: **un radioenlace físico**, con dos extremos de observación CU01 y SJ01; no son dos réplicas independientes.
- El monitoreo y el dashboard existentes son infraestructura de soporte, no evidencia de predicción futura.
- Los cambios de frecuencia/ancho de la campaña experimental 3×2 se tratarán como cambios de régimen, no como eventos espontáneos de degradación.
- Periodos de entrenamiento, validación y prueba se separarán cronológicamente; la prueba se mantendrá reservada.
- El modelo no modificará parámetros RF; integración inicial en modo sombra (solo lectura).
- La generalización a otros enlaces **no se presume**.

## Documentación versionada
- [Protocolo científico y metodológico](protocolo-metodologico.md)
- [Matriz de consistencia — Anexo A](anexos/matriz-consistencia.md)
- [Operacionalización de variables — Anexo B](anexos/operacionalizacion-variables.md)
- [Plan de datos y validación](plan-de-datos-y-validacion.md)
- [Protocolo complementario de pronóstico de throughput activo](protocolo-pronostico-throughput.md)
- [Auditoría 003 — elegibilidad retrospectiva a 60 minutos](auditorias/2026-10-26-elegibilidad-pronostico-h60.md)
- [Script de auditoría 003 — solo lectura](scripts/auditar_pares_causales_h60.py)
- [Auditoría 004 — dataset retrospectivo privado congelado](auditorias/2026-10-26-construccion-dataset-retrospectivo-h60.md)
- [Generador de pares X/y privados](scripts/construir_pares_privados_h60.py)
- [Formato de informe final FEDU y estado](informe-final-fedu.md)
- [Bitácora de decisiones y pendientes](bitacora.md)

## Alcance del repositorio
Este directorio versiona el protocolo, matrices, definiciones y futuros resultados auditables. La implementación de adquisición AtmosLink permanece en el resto de este repositorio. La investigación predictiva FEDU **no se confunde** con otras tesis, experimentos 3×2 o el motor ASDE.

**Protección:** no publicar credenciales, tokens, claves, ubicaciones precisas no autorizadas, direcciones de acceso remoto, dumps privados ni datos personales. Los datasets se compartirán solo tras revisión de licencias, anonimización y autorización.

## Referencia maestra
La versión editable del proyecto FEDU se mantiene separada de esta representación Markdown. Al aprobar cambios, reconciliar ambos documentos; el título es inmutable.

## Avance analítico del 26 de octubre de 2026

Se verificaron 9 709 pruebas activas, 9 428 con estado OK; 9 367 tenían configuración RF completa y el intervalo mediano por dirección/régimen fue de 15 minutos. Se ha pre-registrado un **pronóstico complementario** de throughput medido a H=60 min (H=15 secundario), comparando contra persistencia. La auditoría de episodios continúa abierta; no hay todavía resultados de un modelo FEDU validado.

### Dataset retrospectivo con corte del 26-10-2026 a las 22:10 (Perú)

Se generaron 8 441 pares privados X/y, con 7 955 pares RF compatibles y 7 000 pares RF+meteorología. Archivos preservados en el controlador en carpeta privada y fuera de este repositorio. No hay verificación de `available_at` ni prueba predictiva prospectiva; no declarar superioridad de ML.

## Evaluación exploratoria de modelos, 26-10-2026

Se ejecutaron **dos validaciones cronológicas retrospectivas de desarrollo**, no una prueba prospectiva ni una contrastación de la hipótesis principal. En cohorte de historia sola, MAE (persistencia / Ridge / boosting) fue **3,344 / 3,862 / 4,319 Mbps** en el primer periodo y **4,772 / 5,370 / 5,695 Mbps** en el segundo. La persistencia resultó mejor en MAE; Ridge tuvo RMSE menor. La ablación con filas idénticas no demostró valor predictivo robusto de RF o meteorología frente a persistencia.

Documentos: [auditoría 005](auditorias/2026-10-26-modelos-dev-retrospectivos.md), [código de desarrollo](scripts/evaluacion_retrospectiva_desarrollo.py), [ablación idéntica](scripts/ablacion_cohorte_comun.py) y [esquema prospectivo sin despliegue](plan-registro-disponibilidad-prospectiva.md).

**No hay predictor FEDU validado ni servicio de inferencia implantado. Los resultados individuales permanecen privados.**
