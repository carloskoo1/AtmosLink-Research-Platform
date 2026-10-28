# FEDU — auditoría exploratoria de calidad y etiquetas
Fecha de corte: 2026-10-26 (hora local de Perú). Datos de sistema en operación; los totales son instantáneas y no resultados de validación.

## Agregados comprobados
- 9 709 pruebas activas leídas en el segundo corte; 281 con estado ERROR.
- Cribado con separación máxima de 35 minutos: 27 grupos candidatos, 14 próximos a una transición de configuración (ventana de ±65 minutos), 13 fuera de ella.
- En 16 grupos se observaron errores de recolección RF próximos.
- Clasificación por patrones de texto de mensajes: 265 relacionados con rutas y 16 con problemas de conexión. La causa raíz no está verificada.
- Algunos ceros simultáneos de SNR y RSSI corresponden a lecturas sospechosas; excluir del análisis numérico hasta su validación.
- En otro corte de la tabla de integración meteorológica: 15 639 registros, 15 258 marcados con coincidencia meteorológica entre ambos extremos.

## Dictamen
**Ninguno de los 27 grupos queda todavía homologado como episodio de degradación RF independiente.** Un error de enrutamiento, de colector o de prueba no equivale automáticamente a falla física. Las ventanas próximas a intervenciones programadas no deben etiquetarse como degradación espontánea. La agrupación de 35 minutos y la guarda de 65 minutos son exclusivamente reglas exploratorias.

## Consecuencia sobre hipótesis
Mantener diferenciadas:
1. Tarea principal propuesta: anticipar episodios de degradación **si se obtiene un conjunto suficiente de episodios independientes y auditados**.
2. Tarea alternativa/contingente: predecir throughput activo medido futuro y otros indicadores RF con horizontes predefinidos, comparando con persistencia y modelos simples.

No modificar título del proyecto. No afirmar eficacia de ML con estos agregados.

## Trabajo pendiente
- Registrar verdad-terreno a partir de evidencia independiente de las características predictoras.
- Auditar disponibilidad temporal real y los valores inválidos 0.
- Segmentar por banda/ancho de canal, dirección y cambios de régimen.
- Fijar protocolo, ventana y horizonte antes de la evaluación reservada.
- Evitar particiones aleatorias de series temporales y pseudorreplicación por filas.

Este archivo no publica series crudas, ubicaciones precisas, direcciones IP ni secretos.
