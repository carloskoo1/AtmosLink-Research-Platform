# Bitácora del proyecto FEDU 2026

## 2026-10-26 — Apertura del registro metodológico
- Se conserva el título original del proyecto sin modificación.
- Se acuerda centrar la contrastación en **anticipación futura de episodios de degradación** y no en detección actual.
- Se distingue una sola infraestructura de radioenlace con dos extremos CU01/SJ01, evitando seudorreplicación.
- Se mantiene el juicio de expertos como validación de contenido opcional/complementaria; la prueba independiente decide el desempeño predictivo.
- Matriz de consistencia y tabla de operacionalización ubicadas en los anexos A y B.
- El informe final sigue 13 secciones; no agregar cronograma ni presupuesto por iniciativa propia.
- Se documenta el protocolo en rama dedicada, separada de código y de campañas en ejecución.
- La hipótesis y los objetivos aún **no** se consideran resueltos; W/H, presupuesto de alertas y verdad-terreno siguen pendientes de congelación.

## Prioridades con criterio de terminación
1. **Inventario y auditoría:** lista de tablas, timestamps, fuentes, cadencias, continuidad y latencias medidos. Evidencia: I1–I3 reproducibles.
2. **Catálogo de episodios:** fichas I4 corroboradas con fuentes independientes y resolución de inicio. Resultado: conteo de episodios elegibles por régimen.
3. **Pre-registro:** fijar etiqueta, W/H, regla de purga, particiones, presupuesto de falsas alertas. Resultado: protocolo versionado antes de examinar test.
4. **Baselines/ML:** primer entrenamiento reproducible, comparación cronológica y ablación meteorológica secundaria. Resultado: I6–I7 con semillas/manifiestos.
5. **Validación:** prueba ciega por episodio, IC95 %, falsas alertas/24h y tabla auditada de casos. Resultado: acta I8 y decisión de H0.
6. **Integración:** predicción en modo sombra sin modificación RF, dashboard con timestamp, validez de inputs, modelo y alertas auditables.
7. **Informe final FEDU:** convertir resultados efectivamente obtenidos a los 13 apartados, anexar matrices, evidencias y referencias contrastadas.

## Separación de estudios
No declarar como resultado FEDU el desempeño reportado en otros repositorios, tesis o ASDE. Es posible reutilizar componentes de infraestructura documentando procedencia, cambios y permisos, pero la validación FEDU requiere su propia partición y evidencias.

## 2026-10-27 — Cierre operativo 3×2 y restricción para prueba FEDU

- Campaña 3×2 finalizada programáticamente 27-oct 00:00 (Perú); retorno físico al régimen base 7000 MHz / 20 MHz confirmado mediante `SWITCH_COMMITTED OK` a las **00:02:58**; telemetría posterior coincidió con la base.
- Backup privado y consistente de SQLite posterior al cierre: **1 773 711 360 bytes**, `PRAGMA quick_check=ok`; SHA-256 y evidencia de transiciones conservadas en un manifiesto privado en el controlador.
- Balance de la fase factorial: 18 bloques (6 combinaciones × 3 repeticiones), 7143 mediciones activas frente a 8064 nominales (88,58% de cobertura de filas), 7070 OK y 73 ERROR. Los dos primeros bloques tuvieron cobertura del 16,67% y 27,08%.
- Servicio formal de throughput presentó 472 invocaciones fallidas por argumentos incompatibles; se documenta por separado de las pruebas activas que sí existen.
- **Backup remoto aún NO verificado:** estado reporta `403 storageQuotaExceeded` para Drive; mantener respaldo local íntegro y no publicar datos crudos.
- Referencia pública: [acta científica de cierre 3×2](https://github.com/carloskoo1/Andean-6GHz-Link-Experiment/blob/research/cierre-campana-3x2-2026/research/cierre_3x2_2026-10-27.md) y [PR de revisión](https://github.com/carloskoo1/Andean-6GHz-Link-Experiment/pull/1).
- **Restricción FEDU:** no convertir el tramo 3×2 en test prospectivo intacto. La nueva evaluación exige registro prospectivo de `first_seen_at`, mismo régimen estable, cierre de fuentes e instrumentación previamente verificados, modelos/baselines congelados y periodo independiente sin inspección para ajuste.
- **No se activó ninguna campaña ASDE ni despliegue de inferencia.** Su transición operativa continúa pendiente de aprobación separada.

## 2026-10-27 — Piloto first_seen y reanudación FEDU

- Se verificaron el régimen base 7000/20, reloj NTP sincronizado, telemetría operativa y 6 DL + 6 UL con `OK` en tramo poscampaña hasta las 01:30 (hora de Perú).
- Se desarrolló y probó con SQLite sintético un observador de `first_seen_at`, leyendo fuentes en `mode=ro`; pruebas de `init`, `poll` y no duplicación: PASS.
- Se inicializaron manualmente cursores reales en una base privada independiente (throughput 9735, RF 15690), sin recuperar retrospectivamente historiales. `poll` inmediato: 0 filas nuevas. Estado: PILOTO LIMITADO, **sin sondeo automático** y sin verificación de `available_at` operacional.
- El respaldo ZIP de cierre 3×2 del Drive Koo fue verificado por coincidencia de MD5 local y remoto. El respaldo UNC 2/2 permanece pendiente; la cuota futura del Drive principal es baja.
- No se entrenaron modelos nuevos ni se abrió prueba independiente FEDU. La tarea predictiva principal por episodios sigue supeditada a verdad-terreno independiente y eventual revisión formal de hipótesis.
- [Documentación de reinicio](retoma-post-3x2-2026-10-27.md).

## 2026-10-27 — Prueba acotada first_seen y catálogo de incidentes

- 14 sondeos de 25 s completados sin errores, 6 registros RF y 5 TCP nuevos durante ensayo; la captura incremental mostró 9,94–24,94 s de demora observada, no de ingesta certificada. No hubo servicio permanente.
- Catálogo de 27 grupos derivados de 281 fallos iperf: 3 grupos/208 fallos en periodo previo; 24 grupos/73 fallos durante 3×2. 14 próximos a transiciones, 8 bidireccionales fuera de guarda sin corroboración y 5 errores de prueba restantes.
- Las señales de ping, colector y RSSI inválido se conservaron como pistas, **no como causalidad ni etiquetas confirmadas**. Pendientes fichas I4 con fuentes independientes y revisión de cambios de régimen.
- [Informe 007](auditorias/2026-10-27-piloto-firstseen-y-catalogo.md); [catálogo reproducible](scripts/catalogar_candidatos_rf.py). Datos de casos privados. Sin predictor desplegado ni test confirmatorio.

## 2026-10-27 — Corrección de alcance: exclusión de panel-solar

Se rectifica expresamente la inclusión exploratoria del dispositivo remoto `panel-solar` / inversor Growatt en la revisión FEDU. **No forma parte del caso de estudio, del dataset, de las fuentes I4 admisibles ni de los instrumentos de validación.** No usar sus logs, avisos de conectividad ni registros eléctricos para atribuir causalidad a las incidencias CU01–SJ01. Las fichas I4 fueron elaboradas sobre snapshot de AtmosLink y pruebas TCP/RF, sin registros Growatt. Las causas ajenas al sistema RF solo podrán mencionarse como **desconocidas**, a menos que exista evidencia originada en la propia infraestructura Cuñacales–San José y validada documentalmente. Se conserva una sola unidad física de enlace y dos extremos de observación.

## 2026-10-27 — Fichas I4 v02 exclusivamente AtmosLink

- Corregidas las ocho fichas privadas I4: campos y posibles atribuciones provenientes de fuentes ajenas al radioenlace quedaron excluidos; la v01 se conserva solo como antecedente, marcada como obsoleta.
- Revisados individualmente C001, C002, C003, C011, C016, C020, C022 y C024 mediante el snapshot local íntegro (tablas TCP activo y telemetría RF); resultado **8 indeterminados / 0 RF corroborados**.
- Confirmados 0 datos RF operativos válidos alrededor de C020; en C002 y C003 predominan errores de extracción de telemetría. No imputar pérdida de radio a partir del colector, errores TCP ni medición eléctrica ajena.
- [Informe técnico 008](auditorias/2026-10-27-i4-alcance-y-ocho-casos.md). No se abrió prueba de hipótesis ni se cambiaron equipos o procesos.

## 2026-10-27 — Auditoría 012: incidente del cable AP6 (01-sep)

Se comprobaron en el snapshot 12 muestras RF completas de la hora anterior a la pérdida de acceso del AP. RSSI y SNR estaban estables, sin precursor gradual evidente. En 39/39 pares locales CU01 y SJ01 coincidían estado, error, MCS y SNR: esas filas no son dos fuentes independientes. La primera prueba activa throughput del día ocurrió a las 21:40:56, después del incidente. Documento: [Auditoría 012](auditorias/2026-10-27-auditoria-012-precursores-independencia-UTP.md). Sigue pendiente confirmar PoE y eventos de firmware; no se cambió producción ni se etiquetó una caída RF confirmada.

## 2026-10-27 — Auditoría 013 y apertura de registro de adjudicación

Se halló el archivo original AP `raw_show_sta` en el monitor de la instalación, se verificó dependencia de `radio_link_local` con esos datos y se detectó que `capture_agg_ap.sh` no conserva el código de fallo SSH (`|| true`). Se clasificaron las ocho ventanas por muestras de **peer esperado, peer diferente/cero, banner SSH sin tabla y respuesta ausente**: C001 22/30, C002 0/403, C003 0/1040, C011 0/30, C016 0/15, C020 41/75, C022 2/105, C024 5/15 capturas con peer esperado. Se fijaron seis huellas SHA-256 y se publicó [acta 013](auditorias/2026-10-27-auditoria-013-fuente-original-ap-y-verdad-terreno.md), [script solo lectura](scripts/auditar_capturas_originales_ap_i4.py), [registro de evidencia v0](anexos/registro_adjudicacion_verdad_terreno_v0.csv) y [propuesta de regla de cierre](protocolo-cierre-verdad-terreno-v1.md).

Se mantienen los **8 casos RF como indeterminados**, sin confundir tabla ausente con desasociación demostrada ni dos derivados del mismo muestreo como testigos independientes. Siguiente dependencia: registros nativos AP/SM/cnMatrix o declaración de histórica irrecoverable, y validación de observador local independiente en fase prospectiva. No se modificaron equipos, sistemas de adquisición o scripts de producción.

## 2026-10-27 — Auditoría 014: C002 nativo no resuelto; fuente funcional ICMP piloto

Cotejadas capturas AP originales C002 y rutas de exportaciones históricas en Controlador y rpi-cunacales; no se halló archivo nativo de eventos AP/SM/cnMaestro para la ventana Sep 04, sin concluir que el cloud carezca de él. C002 conserva etiqueta física RF NA. Se creó [sonda funcional acotada](scripts/piloto_ping_funcional_ro.py) con marcas de inicio/disponibilidad y resultado AP/SM; se ejecutaron **tres rondas** locales separadas 10 s, ambas rutas 3/3 `ICMP_REPLY`. JSONL privado con permisos 0600 y SHA-256 auditada. No se instaló servicio permanente, no hubo cambios RF, PoE ni adquisición. [Acta 014](auditorias/2026-10-27-auditoria-014-c002-fuente-nativa-y-piloto-funcional.md). Siguiente dependencia: verificar histórico Events/Alarms separado AP y SM en cnMaestro, documentar retención, cotejar C002. 
