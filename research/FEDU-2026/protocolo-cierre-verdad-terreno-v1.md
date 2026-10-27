# FEDU — Procedimiento v1 propuesto para cerrar la verdad-terreno sin sesgo

**Estado:** BORRADOR DE CRITERIOS DE ADJUDICACIÓN, sujeto a aprobación ANTES de etiquetar datos y antes del periodo de test; no sustituye el protocolo/hipótesis de la Universidad.  
**Fecha:** 27-oct-2026. **Alcance:** único enlace RF Cuñacales–San José, AP CU01 y SM SJ01, con instrumentación AtmosLink.  
**Entradas auditadas:** [acta 013](auditorias/2026-10-27-auditoria-013-fuente-original-ap-y-verdad-terreno.md), [registro de 12 casos](anexos/registro_adjudicacion_verdad_terreno_v0.csv), fichas privadas I4 v02 y actas 008–012.

## 1. Qué significa «cerrar la verdad-terreno»

No significa forzar un `0` o `1` para cada fallo de `iperf3`. Significa que **cada intervalo candidato termina con una decisión motivada, documentada y reproducible**:
1. `EVENTO_FUNCIONAL_CONFIRMADO`: pérdida/degradación del **servicio local medido** con un instrumento cuya observación es suficiente e independiente de las variables predictor; comienzo intervalocensurado y retorno o censura registrados.
2. `NO_EVENTO_FUNCIONAL_OBSERVADO`: hubo cobertura funcional suficiente en la ventana completa pertinente, servicio dentro de referencia, sin interrupción compatible, control de frescura y régimen. **Jamás** utilizar silencio de logs para este estado.
3. `EVENTO_DE_ASOCIACION_CONFIRMADO`: existe una declaración inequívoca de firmware/AP-SM o registros nativos verificables de desasociación/rea­sociación **con hora**, sin confundirla con un error SSH o un banner sin tabla.
4. `INTERRUPCION_EXOGENA_DOCUMENTADA`: intervención humana de cable/PoE, trabajo programado de configuración, reinicio o corte de un componente propio del enlace, con fuente y hora; no implica anticipabilidad por RF.
5. `FALLO_OBSERVABILIDAD`: fuente o colector dejó de reportar o proporcionó datos inválidos. Puede coexistir con evento físico, pero no lo demuestra.
6. `INDETERMINADO`: no existe evidencia suficiente o hay discordancia instrumental irresuelta. Es una **salida final legítima de adjudicación** si el histórico no puede recuperarse; **no es dato negativo para supervisión**.

Estas categorías no son excluyentes en el diagnóstico: se registra el estado **funcional**, el estado **RF**, el estado **instrumental** y la **causa operativa** en columnas distintas. La etiqueta predictiva principal se deriva solo de una definición aprobada y de cobertura suficiente, no de la categoría del operador.

## 2. Fuente, unidad y dependencia

| Fuente disponible | Qué permite observar | Qué NO prueba |
|---|---|---|
| `raw_show_sta_YYYY-MM-DD.log` | tabla de estación asociada **si el peer esperado es real y coincide** en el instante muestreado | continuidad RF o causa de ausencia de estación |
| `agg_ap_*.csv` / `radio_link_local` | variables derivadas de la misma captura anterior | testigo independiente adicional |
| `radio_link_config_telemetry` | gestión AP/SM y métricas de ambos extremos cuando lectura válida | interrupción física solo por `COLLECTION_ERROR` |
| `active_throughput_6g` con `OK` + ruta/ping válido | éxito de la prueba en ese instante y ruta medida | éxito continuo entre pruebas; causa RF de un `ERROR` |
| Registros originales firmware AP/SM | asociación, reboot, radio status si conservados y verificada marca temporal | causa eléctrica vs radio si no existe switch/PoE |
| cnMatrix puerto AP 6 GHz + PoE (misma instalación) | link port, alimentación, intervención puerto y tiempo si logs históricos disponibles | pérdida RF causada por propagación |
| Mensaje contemporáneo de personal en campo | acción humana, puerto y hora aproximada | pérdida RF exacta si no midió RF |
| Evento `PLATFORM_HEALTH` | frescura/adquisición de plataforma | caída RF |
| cnMaestro `Offline` | plano de gestión cloud | caída RF sin controles de LAN/servicio |

Exigir trazabilidad de **observed_at, first_seen/available_at, zona horaria, firmware, fuente, versión, intervalos con muestras, calidad, configuración/régimen**. Los registros RF en CU01/SJ01 derivados del mismo `show sta` cuentan como **una** fuente. No exponer credenciales, MAC ni archivos completos de campo en repositorio público.

## 3. Algoritmo de adjudicación sin mirar predicciones ML

Para cada candidato, el adjudicador debe:
1. Inspeccionar datos brutos y hashes en **copia de lectura**, sin refinar o borrar errores.
2. Segmentar por las primeras y últimas **observaciones interpretables**, no por agrupar filas `ERROR` en una sola falla prolongada.
3. Marcar si la **prueba local end-to-end** es suficiente: muestra observada, dirección, servidor accesible/ruta, confiabilidad de reloj, cadencia y criterios definidos anticipadamente. Si existen solo `ERROR`, el servicio queda `INDETERMINADO` hasta poder distinguir causa.
4. Confrontar `show sta` original con estado nativo AP/SM: `PEER_EXPECTED_IN_TABLE` confirma **asociación momentánea**; `TABLE_OTHER_OR_ZERO_PEER`, `SSH_BANNER_NO_RADIO_TABLE` y `NO_USABLE_RESPONSE` son **no acreditación**, no «RF caído».
5. Comprobar cambios programados, intervenciones documentadas, reinicios y dependencia entre sensores. La causa solo se atribuye cuando hay soporte específico.
6. Registrar por separado `service_label`, `rf_association_status`, `instrument_status`, `operator_incident`, `exogenous_flag`, `confidence`, `last_known_good`, `first_suspect`, `first_restored`, `missing_evidence` y `reason`.
7. Excluir del modelo confirmatorio las filas sin verdad-terreno o con fuente de etiquetas circular respecto de las variables predictor; registrar cuántas quedan fuera y por qué.
8. Realizar una segunda revisión ciega respecto a la salida ML y resolver desacuerdos mediante acta; cuando falte histórico, documentar **IRRECUPERABLE_CON_FUENTES_ACTUALES** y mantener `NA`.

## 4. Decisión por tipo de evento y métricas

- **Objetivo primario vigente en FEDU:** anticipar **inicio futuro** de episodios verificables de degradación frente a umbrales, manteniendo las definiciones oficiales y sin modificar silenciosamente la H1. La definición concreta de degradación de servicio (p. ej. dos ensayos con caída de capacidad/loss) está **propuesta, no congelada** y requiere resolución/cadencia compatible.
- **La telemetría RF histórica hasta t constituye X**; la etiqueta futura no puede derivar exclusivamente del RSSI/SNR que ya se usará como entrada o de una ausencia del mismo recolector.
- **El incidente de cable del 01-sep**: incidente de puerto 6 comunicado y pérdida/recuperación de acceso corroborada; diagnóstico de interrupción abrupta. No contarlo como episodio de degradación gradual anticipable sin criterio de elegibilidad fijado antes del test.
- **Los ocho I4**: todos `INDETERMINADO` para la hipótesis de degradación RF en esta versión; hallazgos AP original sirven para acotar tiempos/estados, no reemplazar fuentes independientes.
- **Métricas de adjudicación**: `n_candidatos`, `n_confirmados_por_clase`, `n_descartados_con_cobertura`, `n_indeterminados`, `n_exogenos`, `n_elegibles_prediccion`, intervalo de precisión de tiempo y `coverage_hours`, no «accuracy» de etiquetas supuestas.

## 5. Secuencia de cierre priorizada y punto de parada

**Etapa A: recuperación documental, solo lectura**
- Prioridad 1: fuente de **firmware AP/SM y cnMaestro histórico** para **C002 (4-sep)**, **C003 (10–11-sep)** y **C016/C022 (13/21-oct)**. Estos casos tienen ausencia o inconsistencia de pares AP y suficientes pruebas ERROR para ser informativos.
- Prioridad 2: **C001/C020/C024** para distinguir intermitencia de ventanas completas y controles de éxito; luego C011.
- Extra: el caso AOP 01-sep, con hora de reconexión ya corroborada, requiere solo bitácora del **puerto 6/PoE** y firmware para el estado físico, no más análisis de RSSI.
- Para cada fuente exportar rango local ±30 min del candidato, metadatos de huso/retención y SHA-256; conservar originales privados intactos.

**Etapa B: dictamen**
- Si la exportación no contiene históricos o no hay acceso autorizado, **cerrar como `INDETERMINADO_SIN_FUENTE_HISTORICA`** con evidencia de limitación y no seguir buscando cíclicamente.
- Dictamen ciego en [registro adjudicación](anexos/registro_adjudicacion_verdad_terreno_v0.csv) y reconciliación de matriz de consistencia si hay necesidad de alterar la tarea.

**Etapa C: diseño prospectivo si los eventos verificables son insuficientes**
- Sin tocar radio/switch, implantar **observador separado** de enlace local (pings de un extremo al otro sin depender de Internet), captura del evento de asociación del firmware en modo de solo lectura, salud del colector y marcas temporales completas; el modelo ML queda en sombra.
- Someter implementación a preflight de relojes, carga, permisos y estabilidad antes de habilitar servicios persistentes.
- Recopilar eventos **naturales**, sin desconectar cables ni inducir cortes para crear etiquetas; no forzar artificialmente incidentes.
- Congelar protocolo W/H, presupuestos de falsas alarmas, partición temporal y criterios de exclusión **antes de abrir el test**. La potencia inferencial depende del número de episodios elegibles, no solo de días tomados.

**Puerta de decisión final:** si hay suficientes episodios verificables bajo este protocolo, entrenar y evaluar; si no, documentar viabilidad de monitoreo/detección y proponer revisión formal del objetivo predictivo antes de cualquier nuevo test. **Nunca afirmar la hipótesis por ausencia de eventos o porque una clase fue imputada.**

## 6. Situación al finalizar la auditoría 013

- **Nuevo**: 6 archivos originales `show sta` auditados con hashes y 8 ventanas adjudicadas solo como evidencia momentánea. Se corrigieron capturas con peer `0.0.0.0` que parecían positivas.
- **No hay todavía** eventos RF degradación validados independientemente dentro de los 8 I4.
- **Existe** incidente físico de reconexión AP puerto 6 documentado y fallas instrumentales corroboradas.
- Se creó script reproducible [auditar_capturas_originales_ap_i4.py](scripts/auditar_capturas_originales_ap_i4.py) y registro v0. La prueba confirmatoria sigue cerrada, sin modelo desplegado ni modificaciones de campaña.
