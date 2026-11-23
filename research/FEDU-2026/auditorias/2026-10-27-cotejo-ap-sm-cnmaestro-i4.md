# FEDU — Auditoría 009: cotejo documental AP/SM y cnMaestro, ocho candidatos I4

**Fecha de revisión:** 27-10-2026 (Perú).  
**Unidad experimental/observacional:** un único radioenlace Cuñacales–San José, extremos AP CU01 y SM SJ01.  
**Condición científica:** *corroboración parcial de problemas de adquisición; ninguna de las ocho fichas acreditada como degradación RF*.  
**Fuentes excluidas:** todo equipo o registro no perteneciente a AtmosLink y a ese radioenlace.

## 1. Documentos y registros consultados

1. Snapshot de cierre, auditado anteriormente, de `active_throughput_6g` y `radio_link_config_telemetry`; ocho fichas I4 privadas, regeneradas como versión v02 desde **solo esas tablas**.
2. Registro `scientific_events.json` de AtmosLink: el **04-sep-2026 10:34:25 (Perú)** se documenta transición de salud de plataforma a `UNKNOWN` en CU01, con `observation_age_seconds=551` y `operational_state=DELAYED`. Este evento ocurre dentro de C002, y se refiere a retraso de adquisición, **no al estado físico RF**. En otras fechas se encontraron eventos de frescura NASA o salud en horas fuera de las ventanas de candidatos: no se trasladan como corroboración.
3. `INCIDENT_2026-09-15.md` y `docs/incidents/2026-09-15-campaign-transition-failure.md`: registro de una **transición fallida independiente** de la campaña, con AP local accesible y SM/extremo remoto inalcanzables, recuperada mediante intervención controlada sobre la alimentación del AP. **No coincide en fecha con los ocho I4**: es evidencia de tipo de fallo y controles, no prueba directa de ellos.
4. `INCIDENT_2026-09-20_CNMatrix_CU01_RECOVERY.md`: el cnMatrix estuvo `Offline` en cnMaestro mientras seguía conmutando y los radios funcionaban. Se confirmó anomalía de **gestión del switch**, corregida después. No corresponde a la ventana C002/C003 ni al 21-oct. Ilustra por qué `Offline` en una consola de gestión **no equivale a LINK_DOWN**.
5. `INCIDENT_2026-09-19_POWER_CU01.md`: pérdida de adquisición/control del nodo de campo, con radioenlace reportado operativo. Su fecha no coincide con los ocho I4. La evidencia proviene de la infraestructura del propio enlace, pero **no se usa como señal causal externa ni como etiqueta positiva de esos ocho casos**.
6. Revisión del inventario de fuentes accesibles en controlador y nodo de adquisición: **no se localizó una exportación histórica AP/SM/cnMaestro por evento, con marca temporal verificable, que permita adjudicar independientemente los ocho intervalos concretos**. Tampoco se obtuvo una extracción autenticada de eventos históricos de cnMaestro para esas ventanas. Esta es una limitación de acceso/evidencia, **no prueba de ausencia de sucesos**.

**Precaución:** las lecturas de `ping_status` y RSSI/SNR unidas al mismo `active_throughput_6g` pueden depender de la misma ruta de instrumentación. No etiquetar un incidente como fallo RF usando únicamente variables que también serán entradas del predictor.

## 2. Confrontación por candidato (sin etiquetas impuestas)

Los números de RF se calcularon con margen ±15 min alrededor de la ventana temporal de errores de pruebas, usando el snapshot de cierre. Cada caso es un grupo temporal, **no necesariamente una interrupción continua**.

| I4 | Ventana inicial Perú | Pruebas ERROR | RF operativo/RSSI válido cerca | Fallos del colector cerca | Evidencia adicional / decisión |
|---|---|---:|---:|---:|---|
| C001 | 04-sep 08:00 | 4 | 10 | 2 | Hay pruebas OK dentro del grupo; **no es interrupción continua acreditada**. Sin eventos independientes de AP/SM pareados. **Indeterminado** |
| C002 | 04-sep 09:15 | 56 | 2 | 84 | Alerta `PLATFORM_HEALTH=UNKNOWN` a las 10:34:25 y retraso de datos. **Corrobora falla de observabilidad, no de radio**. **Indeterminado** |
| C003 | 10-sep 19:00 | 148 | 1 | 222 | Ausencia casi total de RF operativo durante errores de medición; sin log AP/SM del periodo. **Indeterminado** |
| C011 | 05-oct 15:45 | 6 | 5 | 7 | Hay muestras RF operativas; faltan logs específicos AP/SM y ruta/iperf. **Indeterminado** |
| C016 | 13-oct 13:45 | 3 | 3 | 6 | La alerta de salud de plataforma de ese día (07:44) queda **fuera** de ventana; no sirve para validar este caso. **Indeterminado** |
| C020 | 21-oct 02:45 | 9 | 0 | 20 | Sin muestras RF operativas utilizables. Las transiciones de campaña previas en la misma fecha requieren trazabilidad, pero no determinan causa. **Indeterminado** |
| C022 | 21-oct 06:00 | 13 | 3 | 24 | Predominan fallos de adquisición con recuperación parcial de RF. Sin registro histórico AP/SM independiente por ventana. **Indeterminado** |
| C024 | 21-oct 10:15 | 4 | 4 | 4 | Muestra RSSI cero sospechosa y otras muestras RF válidas; no hay prueba independiente de degradación RF. **Indeterminado** |

## 3. Reglas para evitar conclusiones falsas

- Un fallo de `iperf3` no acredita caída RF: puede ser servicio de prueba, TCP, ruta, temporización o instrumentación.
- `COLLECTION_ERROR` de telemetría RF indica que el lector no obtuvo la medición, no que el enlace perdió señal.
- Un estado `Online` / `Offline` de cnMaestro indica **gestión de dispositivo**; debe contrastarse con conectividad AP–SM y datos independientes del enlace antes de declarar falla de servicio.
- Si no se pudo acceder a eventos históricos de AP/SM o de cnMaestro para una ventana, registrar `SIN_EVIDENCIA_DISPONIBLE`, no `SIN_FALLA`.
- Conservan el estado `INDETERMINADO_PENDIENTE_VERDAD_TERRENO` las **8 de 8 fichas**; **0/8 eventos RF independientemente confirmados**.

## 4. Puerta de control I4 antes de entrenar modelo de eventos

**Pendiente obtener, solo de los propios equipos y plataformas del enlace**:
1. Exportación fechada de log de asociación/reasociación AP↔SM, radio up/down, reinicios y posibles cambios de configuración, con retención temporal y reloj documentados.
2. Eventos de estado del AP y SM en cnMaestro, distinguiendo pérdida del agente de gestión y pérdida de servicio de radio.
3. Evidencia de ping/servicio observada por un proceso independiente de `iperf3` (si existe en histórico), incluyendo fuente, dirección, cadencia, pérdida y calidad.
4. Diagnóstico causal por revisor, con los episodios intervalocensurados: última observación sana y primera anómala; reconocer `INDETERMINADO` cuando no existen fuentes independientes.
5. Fijar protocolo W/H, definición de episodio, regla de purga y presupuesto de falsas alarmas antes de abrir prospectivo.

Los incidentes conocidos del **15, 19 y 20 de septiembre** son registros operativos importantes, pero **no respaldan por coincidencia temporal** ninguno de estos ocho candidatos.

**Conclusión:** se puede elaborar el inventario preliminar de anomalías de adquisición, pero aún **no está habilitada la contrastación de H0/H1 de FEDU por anticipación de degradación física**. El estudio no cambia de objetivo ni hipótesis de modo implícito. No se realizaron cambios RF ni acciones sobre cnMaestro.
