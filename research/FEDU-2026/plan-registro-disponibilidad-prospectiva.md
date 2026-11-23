# FEDU — Diseño de observabilidad temporal prospectiva (PENDIENTE DE DESPLIEGUE)

**Versión:** v0.1 · 26-10-2026. La instrumentación descrita aquí **NO se encuentra activa en producción**. Debe implementarse y comprobarse únicamente después del cierre y conciliación de la campaña 3×2.

## Problema observado en la auditoría

Las bases históricas permiten leer el instante de medición (`observed_at`) y los resultados de iperf3, pero no certifican de manera uniforme el instante en que cada registro estuvo disponible para la aplicación predictiva. La comprobación `observed_at <= t` es NECESARIA pero no suficiente para evitar fuga temporal en un despliegue en tiempo real.

## Definiciones distintas

- `observed_at_utc`: marca de observación registrada por el dispositivo o aplicación de medición.
- `ingested_at_utc`: marca de confirmación de escritura/ingesta en base operativa, solo si existe y se obtiene de un registro de ingesta real.
- `first_seen_at_utc`: instante en que un proceso independiente de consulta, corriendo con reloj UTC validado, **detectó por primera vez** el registro ya disponible en la base. Es una cota superior conservadora de su disponibilidad en el almacén consultado, NO la hora real exacta de ingestión.
- `prediction_issued_at_utc`: marca de emisión efectiva del pronóstico.
- `available_at_utc`: solamente declarar un valor demostrado por instrumentación de la canalización; si no hay evidencia, NA (nunca copiar `observed_at` automáticamente).

**Regla conservadora para un piloto que usa la misma base consultada:** únicamente habilitar un dato cuya primera observación por el proceso `first_seen_at_utc <= prediction_issued_at_utc` y cuya calidad sea válida. Esto no prueba el instante exacto de disponibilidad, pero evita usar retrospectivamente datos descubiertos después de la decisión.

## Esquema de registro propuesto

| Campo | Tipo | Obtención |
|---|---|---|
| source_table | Texto | Fuente de origen controlada |
| source_pk | Entero | Identificador de registro único |
| observed_at_utc | UTC ISO 8601 | Marca declarada de la medición |
| first_seen_at_utc | UTC ISO 8601 | Reloj del proceso lector cuando observó el registro por primera vez |
| lag_observed_to_first_seen_s | Segundos | Diferencia; auditar valores negativos |
| station_id / direction | Texto opcional | Metadatos de fuente disponibles en instancia privada |
| observer_version | Texto | Versión exacta del lector |
| sample_quality_code | Texto | NO evaluado, válido, sospechoso, ausente |
| clock_sync_status | Estado | Evidencia de sincronización de reloj del lector |

## Restricciones de despliegue

1. No activar ni programar sondeo durante la 3×2; no instalar un servicio ni reiniciar equipos.
2. La primera operación debe ser una **inicialización de cursor** que omita los registros históricos para no simular que estuvieron disponibles cuando se pone en marcha el lector.
3. Después se ejecutaría un sondeo ligero de lectura en modo `mode=ro`, con temporización y consultas indexadas `id > last_id`; almacenar solo metadatos de observabilidad en una base privada separada.
4. Definir intervalos máximos admisibles y tiempo de bloqueo de lecturas antes de probar un proceso continuo.
5. Registrar fecha de cierre real de campaña, estado de NTP/RTC y cualquier salto de reloj. `first_seen_at` es fiable solo en la medida en que lo sea el reloj del observador.
6. Integrar posteriormente con inferencia **en sombra** que no emita órdenes al ePMP ni realice iperf adicionales.
7. Publicar métricas de completitud/frescura por fuente, con evidencia de instalación, pero no publicar filas crudas, IP de gestión o credenciales.

## Criterio de aceptación antes de evaluación prospectiva

- Registro completo, trazable y no retroactivo de `first_seen_at`.
- El código no altera las tablas productivas ni sus servicios.
- Los filtros de elegibilidad, modelo, parámetros e hiperparámetros se han congelado por commit ANTES del inicio de prueba.
- Periodo futuro posterior al cierre real de la 3×2 delimitado y sin ajuste sobre sus resultados.
- Registro independiente de emisión `prediction_issued_at`, y reglas preestablecidas de omisión cuando la fuente está retrasada.

El documento sirve como instrumento de implementación y trazabilidad, **no** demuestra que el observador esté funcionando.
