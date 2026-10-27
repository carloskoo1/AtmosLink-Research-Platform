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

## Retoma FEDU tras la campaña 3×2 — 27 de octubre de 2026

[Informe metodológico de reinicio y primera instrumentación de `first_seen_at`](retoma-post-3x2-2026-10-27.md) · [Código del observador](scripts/first_seen_observer.py).

El equipo volvió a 7000 MHz / 20 MHz y la captura RF y throughput sigue operativa. Se probó el instrumento con una base sintética y se inicializaron cursores de lectura reales en un **registro privado distinto**; **no se activó ningún temporizador del piloto FEDU**. El análisis prospectivo de hipótesis aún no ha comenzado. El ZIP 3×2 del 27-oct fue posteriormente verificado por coincidencia de MD5 local/remoto en Drive Koo; persisten pendientes de redundancia UNC y capacidad futura de Drive.

## Evidencia FEDU 27-oct-2026 — piloto temporal y candidatos

[Auditoría 007: first_seen y catálogo de candidatos](auditorias/2026-10-27-piloto-firstseen-y-catalogo.md) · [Script de cribado](scripts/catalogar_candidatos_rf.py).

Se ejecutaron 14 sondeos manuales acotados cada 25 s; se capturaron 6 registros RF y 5 TCP posteriores al inicio del ensayo, sin servicio permanente ni intervención de equipo. La primera llegada incremental mostró 9,94–24,94 s entre observación y primera lectura; no equivale a tiempo exacto de ingesta. 

Se reconstruyeron 27 grupos de error: 14 próximos a cambios, 8 candidatos bidireccionales no corroborados, 5 grupos de error de prueba. 208 errores ocurrieron antes de la 3×2 y 73 durante ella. **No se verificó todavía ningún episodio RF de manera independiente**; no se ha abierto test de hipótesis.

## Revisión del alcance FEDU — ocho fichas I4

El análisis de los casos se realiza exclusivamente con **AtmosLink y el radioenlace Cuñacales–San José**. Se regeneraron las ocho fichas I4 privadas como v02 desde `active_throughput_6g` y `radio_link_config_telemetry`, excluyendo referencias a fuentes ajenas al enlace. **Las ocho permanecen indeterminadas**, sin eventos RF corroborados independientemente.

[Auditoría 008 y tabla de casos](auditorias/2026-10-27-i4-alcance-y-ocho-casos.md) · [Generador I4 v02](scripts/generar_fichas_i4_atmoslink.py).

### Auditoría 009 — cotejo AP/SM y cnMaestro (27-10-2026)

Se cotejaron las ocho fichas I4 con los documentos de incidencias internas disponibles y el registro científico `scientific_events.json`. En C002 se halló alerta de plataforma `UNKNOWN` y datos retrasados a las 10:34 del 4-sep, evidencia de adquisición no de degradación RF. Los incidentes documentados de AP/SM y cnMatrix del 15 y 20-sep **no coinciden con los ocho I4**. Los logs históricos por dispositivo para esas ocho ventanas no se obtuvieron; **0/8 causas RF independientemente corroboradas**. [Acta 009](auditorias/2026-10-27-cotejo-ap-sm-cnmaestro-i4.md).

### Taxonomía de causas y alcance predictivo (27-oct-2026)

[Propuesta controlada de clasificación de incidentes y predictibilidad](protocolo-taxonomia-fallos-y-predicibilidad.md). Los reportes de campo incluyen fallos de la propia alimentación, alineación infrecuente en 6 GHz, enlace Ethernet AP-switch y fallos de Starlink. Estos antecedentes se documentan como **testimonio por corroborar**, no como nuevas etiquetas del dataset. Se distingue riesgo RF futuro de detección de cortes abruptos, gestión y WAN. La hipótesis aprobada y el título no se han modificado; el cotejo de las ocho fichas I4 permanece abierto.

### AOP-UTP-SEP-001: incidente corroborado instrumentalmente el 01-sep-2026

La [Auditoría 011](auditorias/2026-10-27-auditoria-011-desconexion-ap-6ghz-septiembre.md) cotejó un extracto de conversación de campo de **01-sep** con la telemetría RF y local conservada. El cable del **puerto 6, identificado como AP 6 GHz**, fue reportado como movido y **reconectado a las 19:59**; AtmosLink tenía lecturas normales hasta **19:33–19:36**, fallos de asociación derivada y SSH **19:37–19:59**, `radio_link_local=ok` a las **20:01:53** y `LINK_OPERATIONAL_DUAL` a las **20:04:07**. El **puerto 3 y su adaptador** referidos en la misma conversación son asunto separado (AP 5,8 GHz).

La búsqueda del **02–03-sep entre 18:00–20:00** encontró telemetría operativa y pruebas de throughput normales y, por tanto, no corresponde a la reconexión relatada. **Se rectifican las fechas retrospectivas estimadas**; el expediente original preserva la trazabilidad de esas hipótesis. Existe **corroboración fuerte de interrupción de acceso y recuperación asociada al cable**, pero falta el log del switch/AP para confirmar **pérdida efectiva de PoE, apagado del AP y duración de desasociación RF**. Es un nuevo antecedente de incidente, no uno de los ocho I4 basados en errores TCP. No se incorpora como etiqueta RF definitiva ni al contraste de ML.

### Auditoría 012 — señal RF anterior y dependencia de adquisición (27-oct-2026)

En los ~60 minutos previos al incidente del **01-sep 19:37**, hubo **12 muestras RF completas**, todas `LINK_OPERATIONAL_DUAL`, con RSSI DL −74 a −73 dBm, RSSI UL −80 dBm, SNR DL 23–24 dB y SNR UL 18–19 dB. **No se observa un precursor de degradación RF evidente** en esas variables, sin equivaler a evaluación de un modelo. Se comprobó que **39/39 pares etiquetados CU01/SJ01 de `radio_link_local` coinciden en nota/error/MCS/SNR**, por lo que no se cuentan como fuentes independientes. La primera prueba activa throughput archivada del 01-sep es a las **21:40:56**, posterior al episodio. [Auditoría 012 con SQL reproducible](auditorias/2026-10-27-auditoria-012-precursores-independencia-UTP.md). El evento queda documentado para diagnóstico de fallo abrupto, pero **no se convierte en etiqueta confirmatoria de riesgo RF anticipable**.

### Cierre de verdad-terreno: auditoría 013 y protocolo de adjudicación (27-oct-2026)

Se localizaron y analizaron capturas originales `show sta` del AP 6 GHz y su código de recolección. Este código usa `|| true`, por lo que no distingue adecuadamente fallos SSH; además, las capturas con `0.0.0.0` no prueban asociación del SM. Conteos corregidos, por ventana I4: C001 peer válido 22/30; C002 0/403; C003 0/1040 (sin respuesta útil); C011 0/30 (sin respuesta útil); C016 0/15; C020 41/75; C022 2/105; C024 5/15. **Son muestras, no eventos, y no equivalen a caída física de RF**. La evidencia original no vuelve independientes a sus CSV o registros derivados.

Se creó [Auditoría 013 — fuente original AP](auditorias/2026-10-27-auditoria-013-fuente-original-ap-y-verdad-terreno.md), [script de reconstrucción reproducible](scripts/auditar_capturas_originales_ap_i4.py), [registro de adjudicación v0](anexos/registro_adjudicacion_verdad_terreno_v0.csv) y [procedimiento propuesto de cierre y punto de parada](protocolo-cierre-verdad-terreno-v1.md). Las ocho fichas I4 conservan etiqueta RF **indeterminada** hasta corroboración independiente; no abrir validación ML por eventos todavía.

### Auditoría 014 — búsqueda de históricos C002 y piloto ICMP funcional (27-oct-2026)

[Informe C002 y piloto prospectivo acotado](auditorias/2026-10-27-auditoria-014-c002-fuente-nativa-y-piloto-funcional.md) · [Instrumento de sondeo sin servicio](scripts/piloto_ping_funcional_ro.py).

Se revisaron rutas de Controlador y rpi-cunacales sin hallar una exportación local de eventos nativos cnMaestro/firmware AP/SM para C002; la retención de la cuenta cloud **NO** ha sido comprobada. C002 conserva 392 respuestas SSH sin tabla de estaciones y 11 sin respuesta útil, junto a errores de pruebas: **no hay etiqueta RF física confirmada**. En paralelo, 3 rondas locales independientes del proceso de `show sta` obtuvieron **3/3 respuestas AP y 3/3 SM**, con marcas UTC y archivo privado JSONL `0600`, SHA-256 auditada. **No se activó sondeo permanente**. El siguiente bloqueo comprobable es una exportación por separado de Events/Alarms del AP y SM desde cnMaestro o firmware, con fecha y zona horaria.
