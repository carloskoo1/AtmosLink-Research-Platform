# FEDU — Auditoría 008: rectificación de alcance y revisión de ocho fichas I4

**Fecha:** 27 de octubre de 2026 (Perú). **Estado:** cribado de incidentes; no contrastación de hipótesis. **Alcance:** únicamente el radioenlace rural Cuñacales–San José y la instrumentación AtmosLink vinculada directamente a él.

## 1. Rectificación y trazabilidad

La versión inicial de ocho fichas I4 introdujo campos genéricos sobre registros de alimentación y categorías no fundamentadas en las fuentes examinadas. Esos campos **no proporcionaron datos** ni se utilizaron para calcular el inventario, pero su presencia podía inducir a atribuciones indebidas. La versión inicial quedó preservada con advertencia de obsolescencia.

Se regeneraron y validaron **ocho fichas I4 v02** desde el snapshot SQLite íntegro de cierre usando solo las tablas:
- `active_throughput_6g`: estados de las pruebas activas, ping/ruta registrados en la misma prueba, dirección y límites observados de continuidad.
- `radio_link_config_telemetry`: muestras RF contemporáneas, códigos de colector y control de anomalías RSSI.

Se excluyen expresamente fuentes externas al radioenlace. **No se consultaron ni usaron dispositivos de supervisión ajenos a AtmosLink para emitir juicios sobre los casos**.

Script reproducible: [generar_fichas_i4_atmoslink.py](../scripts/generar_fichas_i4_atmoslink.py). Los registros por incidente y las fechas detalladas se conservan solo en directorio privado; no publicar nombres de gestión, direcciones de equipos o datos crudos.

## 2. Los ocho candidatos — verificación limitada

Los conteos RF son observaciones dentro del intervalo de incidentes con margen de ±15 min. No miden personas, fallas físicas independientes ni estaciones diferentes. Una muestra `LINK_OPERATIONAL` con RSSI válido demuestra solo el estado reportado en ese instante. Un `COLLECTION_ERROR` es un fallo de recuperación de telemetría, **no** pérdida demostrada de señal RF.

| ID I4 | Primera prueba con ERROR (Perú) | Pruebas ERROR | Muestras RF válidas | Errores del colector RF | Estado científico |
|---|---|---:|---:|---:|---|
| C001 | 04-sep 08:00 | 4 | 10 | 2 | Indeterminado |
| C002 | 04-sep 09:15 | 56 | 2 | 84 | Indeterminado |
| C003 | 10-sep 19:00 | 148 | 1 | 222 | Indeterminado |
| C011 | 05-oct 15:45 | 6 | 5 | 7 | Indeterminado |
| C016 | 13-oct 13:45 | 3 | 3 | 6 | Indeterminado |
| C020 | 21-oct 02:45 | 9 | 0 | 20 | Indeterminado |
| C022 | 21-oct 06:00 | 13 | 3 | 24 | Indeterminado |
| C024 | 21-oct 10:15 | 4 | 4 | 4 | Indeterminado |

**Observaciones:**
- **C002 y C003:** periodos prolongados con pruebas TCP fallidas y predominio de registros RF no recuperados. Existe evidencia fuerte de pérdida de *observabilidad*; **la causa de las pruebas fallidas no se puede atribuir exclusivamente al medio radioeléctrico**.
- **C020:** cero observaciones RF operativas utilizables cerca del incidente. No hay base para afirmar degradación RF.
- **C001, C011, C016 y C024:** sí existen muestras RF de estado operacional alrededor de errores TCP. Son casos apropiados para examinar hipótesis de transporte, servidor de pruebas, ruta o intermitencia, sin declarar su causa.
- **C022:** predominio de errores del colector con tres observaciones RF válidas; requiere determinar si las rutas de adquisición son independientes de la ruta TCP fallida.
- **C024:** una lectura RF sospechosa de cero debe excluirse o marcarse como no válida.
- Algunas ventanas incluyen pruebas `OK` y `ERROR` dentro del mismo grupo temporal; no se puede transformar el rango completo en una interrupción continua.
- C001, C002 y C003 son anteriores a la fase factorial 3×2. Los candidatos del 21-oct ocurren en la jornada con transiciones retrasadas y deben analizarse con régimen efectivo comprobado.

## 3. Evidencia que falta para cerrar las fichas

1. Registros propios del AP/SM y de cnMaestro/AtmosLink que permitan diferenciar pérdida de radio, conexión de gestión y servicio de red durante cada intervalo; sus códigos y relojes deben auditarse.
2. Comprobaciones de conectividad de un instrumento realmente independiente de las pruebas iperf si existe, sin introducirlo retrospectivamente como prueba disponible cuando no lo era.
3. Documentación de intervenciones y versiones de equipos de la **misma infraestructura del enlace**.
4. Determinación del intervalo entre última observación sana y primera observación afectada; no fabricar comienzo físico exacto desde muestreos discretos.
5. Decisión I4 justificada, por un revisor que desconozca la salida de los modelos ML. Admitir categoría indeterminada.

**Fichas con evento RF independientemente corroborado: 0 de 8.** La ausencia de corroboración no significa que se demostró ausencia de fallos. La hipótesis principal FEDU permanece pendiente.

## 4. Estado de seguridad y siguiente decisión

- No se modificaron parámetros RF, ni se iniciaron pruebas activas, ni se instalaron temporizadores FEDU permanentes.
- El registro `first_seen_at` solo ha superado pruebas manuales y una secuencia acotada, no una campaña prospectiva completa.
- No iniciar prueba de superioridad ML frente a umbrales sin etiquetas independientes y protocolo de falsas alarmas congelado.
- Si la tarea por eventos resulta no viable, cualquier sustitución por throughput futuro requiere revisión formal y coherente del problema, objetivos, hipótesis, variables e instrumentos; no sustituir silenciosamente la hipótesis vigente.

**Decisión:** continuar inspección documental dentro del alcance AtmosLink y mantener ocho fichas en estado **INDETERMINADO_PENDIENTE_VERDAD_TERRENO**.
