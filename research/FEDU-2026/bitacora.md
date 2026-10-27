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
