# FEDU 2026 — Protocolo de clasificación causal, predictibilidad y evidencia (propuesta controlada)

**Estado: borrador metodológico para evaluación; NO sustituye las hipótesis registradas sin conciliación formal con el proyecto presentado.**  
**Fecha:** 27-oct-2026 (Perú).  
**Título FEDU, sin modificar:** DESARROLLO E IMPLEMENTACIÓN DE UN SISTEMA INTELIGENTE BASADO EN APRENDIZAJE AUTOMÁTICO PARA EL MONITOREO PREDICTIVO DE RADIOENLACES RURALES UTILIZANDO TELEMETRÍA RF.  
**Unidad de estudio:** un radioenlace físico Cuñacales–San José con AP CU01 y SM SJ01 y sus sistemas de observación AtmosLink. **No** usar datos ni registros de otros proyectos o dispositivos ajenos al radioenlace.

## A. Motivación de campo (antecedentes reportados, NO etiquetas confirmadas)

El responsable de campo refiere haber presenciado pérdida del servicio del enlace por ausencia de energía en la propia infraestructura, problemas de alineación (raros en el enlace actual de 6 GHz) y una desconexión de cable Ethernet entre el AP y el switch. También refiere interrupciones de Starlink que posiblemente no afectan el tráfico local CU01–SJ01.

**Estatus de estos cuatro antecedentes:** declaración operativa retrospectiva sin fecha/evento correlacionado ni inspección documental suficiente para convertirla en `ground truth`. Obtener fecha, dispositivo extremo, condiciones, duración y registro del incidente, cuando exista. No fabricar fechas ni introducir eventos retrospectivos en el conjunto de evaluación sin evidencia.

## B. Taxonomía de fallas; separar causa, efecto y disponibilidad

| Código | Categoría | Manifestación y posible origen | Se anticipa con RF histórico | Qué puede afirmar FEDU |
|---|---|---|---|---|
| RF-SOFT | Degradación gradual RF | caída sostenida de SNR/MCS/calidad, fluctuación RSSI, pérdida progresiva de margen | **Potencial**, sujeto a evidencia antes del desenlace y evaluación temporal | riesgo futuro y anticipación, si la etiqueta futura es independiente |
| RF-HARD | Desasociación/indisponibilidad de radio | AP–SM dejan de mantener enlace radio o reasocian | no necesariamente: si súbita, sin precursor útil | detección de evento; anticipación solo en subconjunto con precursor demostrable |
| POWER | Interrupción de alimentación propia de AP/SM o nodo de campo | equipo se apaga/no responde, cesa la adquisición | generalmente **no** con RF solo; posible con sensores propios de alimentación instrumentados y disponibles antes | detectar/atribuir con registros del mismo enlace, no fingir predictor RF |
| LAN | Ethernet AP–switch, PoE, interfaz, VLAN/ruta | fallan pruebas o gestión aun si el aire es estable; si el cable lleva PoE puede apagar AP | en general **no** con métricas RF históricas | detectar/localizar y distinguir radio de transporte, con diagnósticos de puertos del mismo enlace |
| WAN | Backhaul Starlink/Internet | falla cnMaestro cloud o telemetría remota mientras el tráfico local puede continuar | no es objetivo de predicción RF CU01–SJ01 | **control negativo** para evitar falsa alarma de `LINK_DOWN` local |
| INSTR | Servidor iperf/SSH, recolector, hueco de datos o error de consulta | `ERROR` o `COLLECTION_ERROR` sin evidencia autónoma de caída de servicio | no aplica como evento RF | alerta de salud de observabilidad; resultado `UNKNOWN` cuando no se puede juzgar enlace |
| MAINT | Cambios programados RF, firmware o trabajos manuales | caídas temporales durante reconfiguración | conocidas por agenda, no predictibles espontáneamente | excluir del contraste principal o documentar como régimen distinto |
| UNCERTAIN | Evidencia insuficiente o contradictoria | fuentes ausentes, incompatibles o sin sincronizar | no evaluable | conservar como indeterminado; no convertir en clase negativa |

**Regla de precisión:** `WAN_DOWN`, `MGMT_OFFLINE`, `RF_LINK_DOWN`, `LOCAL_SERVICE_DOWN`, `SENSOR_UNAVAILABLE` son estados diferentes. No asumir equivalencia. Un `SM_NOT_ASSOCIATED` derivado de valores RF faltantes en el colector no demuestra evento de desasociación del firmware.

## C. Arquitectura lógica propuesta, sin intervención sobre producción

**Capa 1: observabilidad** — relojes sincronizados, `observed_at`, `first_seen_at`, frescura de RF, cobertura y calidad; si no hay suficientes datos, abstenerse (`INSUFFICIENT_EVIDENCE`). Se mantiene el observador privado v0.1 en fase piloto.

**Capa 2: pronóstico** — modelo supervisado de **episodios de degradación anticipable** definidos por resultado funcional independiente del vector X; comparar ML contra umbrales en mismas horas y presupuesto de falsas alarmas. Sin datos previos adecuados no emitir predicción calibrada.

**Capa 3: detección/diagnóstico** — reglas deterministas y evidencia de AP/SM, switch/PoE de CU01, servicio de red y cnMaestro; distinguir motivo probable tras un incidente. Las explicaciones son hipótesis diagnósticas con nivel de certeza; no equivalen a anticipación.

**Capa 4: alerta explicable** — registrar `event_type`, `evidence_source`, `observed_at`, `first_seen_at`, `rf_state`, `service_state`, `wan_state`, `classification_confidence`, `model_version` y `prediction_emitted_at`. Guardar `UNKNOWN` ante observabilidad insuficiente. Toda alerta inicial en **modo sombra**, sin órdenes a radios ni switches.

## D. Unidad de contraste: evitar un resultado sesgado

1. **Evento objetivo principal propuesto (aún por aprobar):** comienzo de un **episodio de degradación del servicio local CU01–SJ01 con antecedente de comportamiento RF utilizable**, ocurrido después del instante `t`, cuya corroboración funcional provenga de fuente que no sea la predicción ni el propio RSSI/SNR predictor. El tipo de evento y elegibilidad deben congelarse **antes** de observar la prueba reservada.
2. **No seleccionar solo eventos «fáciles» después de evaluarlos**. Registrar antes de abrir test los criterios físicos/operativos de inclusión y exclusión. Separar `RF-SOFT` de `RF-HARD` sin inspeccionar las predicciones del modelo.
3. **H0/H1 vigente se preserva provisionalmente** hasta que exista verdad-terreno y se acuerde formalmente si el objetivo primario sigue siendo eventos o se orienta a throughput. No cambiar pregunta, hipótesis ni métricas solo por conveniencia.
4. **Métricas de predicción:** `recall` por evento a tasa de falsas alarmas/24 h elegibles comparable, anticipación en minutos, `precision`, cobertura de abstenciones e IC/intervalos por bloques o eventos. Calibrar umbrales en desarrollo, no en test. Reportar además número y tipo de eventos por causa y cuántos quedan fuera de elegibilidad.
5. **Métricas diagnósticas separadas:** latencia de detección después del incidente, clasificación verificada por causa, indeterminados y alertas improcedentes. **Nunca presentar la detección retrospectiva como predicción.**
6. **Eventos súbitos exógenos:** energía, cable, falla inesperada de equipo —registrar y medir tiempo de detección; **no contar como fracasos de pronóstico RF si se excluyen mediante reglas congeladas ex ante y se informa su frecuencia**. Tampoco excluirlos a posteriori para elevar el resultado.
7. **Control negativo Starlink:** demostrar que al perder WAN se mantienen AP↔SM local y prueba local, si la topología y la instrumentación lo permiten; no asumirlo sin contrastación observacional.
8. **Control no experimental:** una sola infraestructura física; observaciones repetidas y dos extremos no equivalen a réplicas independientes. Separación temporal prospectiva obligatoria.

## E. Evidencia requerida por clase (solo AtmosLink y su radioenlace)

- **RF:** eventos firmware AP/SM con timestamps, estado de asociación, reinicio y configuración; series RF válidas anteriores y posteriores.
- **LAN:** logs del puerto específico del AP en el **switch de la misma instalación Cuñacales–San José**, `link up/down`, PoE presente/ausente si el equipo lo registra, registro de intervención humana. No recuperar ni usar otras plantas solares o inversores.
- **Alimentación:** registros de estado o reinicio del propio radio, Controlador o nodo SJ01; documentación técnica de la incidencia en esa misma infraestructura. Si no hay mediciones propias de tensión anteriores al corte, declarar predictibilidad por energía **no evaluable**, no inventar predictor.
- **WAN:** estado Internet/cnMaestro contra ping o prueba funcional *local* CU01–SJ01, con relojes y ruta verificados. Pérdida exclusiva de nube no se etiqueta como falla local.
- **Instrumentación:** trazas del servidor `iperf3`, fallos del recolector, `first_seen_at`, huecos, reinicios y errores de consulta, siempre con procedencia.
- **Registro de usuario/operador:** evidencias narrativas se clasifican como `OPERADOR_REPORTADO_NO_VERIFICADO` hasta adjuntar fecha y corroboración documental.

## F. Puerta de decisión antes de abrir ensayo confirmatorio

| Control | Requisito |
|---|---|
| Documentar topología | AP/SM, switch, PoE, ruta local de iperf, Starlink/cloud y relojes |
| Corroboración I4 | Revisión de los ocho candidatos con logs históricos específicos, distinguir 0/no accesible/indeterminado |
| Etiqueta independiente | resultado funcional local independiente de las variables RF predictoras |
| N elegible | conteo de episodios independientes suficiente para precisión; si insuficiente, alcance exploratorio |
| Datos causalmente disponibles | registro `first_seen_at` / `available_at` y control de latencia probado prospectivamente |
| Congelamiento | W/H, clasificador, umbrales, presupuesto de falsas alertas, periodo y reglas de abstención antes de test |
| Consentimiento del equipo | aprobación del protocolo revisado y reconciliación de anexos A/B si se altera definición principal |

**Situación al redactar:** ocho I4 sin degradación RF confirmada por evidencia independiente. No se desplegó ML ni se abrió test. Este documento es una **propuesta de protocolo** y no modifica el título ni la hipótesis aprobada automáticamente.
