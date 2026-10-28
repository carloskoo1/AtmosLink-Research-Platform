# FEDU — Reinicio controlado después de la campaña 3×2 (27-10-2026)

**Título FEDU aprobado e inalterable:** DESARROLLO E IMPLEMENTACIÓN DE UN SISTEMA INTELIGENTE BASADO EN APRENDIZAJE AUTOMÁTICO PARA EL MONITOREO PREDICTIVO DE RADIOENLACES RURALES UTILIZANDO TELEMETRÍA RF.

## Estado empírico confirmado

- La 3×2 finalizó en la medianoche del 27-oct-2026 (Perú), y el radioenlace retornó a **7000 MHz / 20 MHz** a las 00:02:58. Se conserva acta y backup local íntegro; el ZIP de cierre está en Drive Koo con MD5 igual al local. No mezclar la 3×2 con el bloque FEDU prospectivo.
- A las 01:39 del 27-oct, el controlador tenía NTP **sincronizado**, radioenlace 7000/20 con `LINK_OPERATIONAL_DUAL`, y al menos **6 mediciones DL + 6 UL posteriores al cierre** marcadas OK en `active_throughput_6g`.
- La evaluación retrospectiva FEDU de throughput **no mostró mejor MAE para ML frente a persistencia**: no se declara superioridad predictiva.
- La hipótesis principal de predicción de eventos independientes sigue **pendiente de verdad-terreno**; los 27 grupos de errores históricos son candidatos, no 27 fallas demostradas.

## Instrumento de disponibilidad prospectiva — estado de piloto

Código versionado: [first_seen_observer.py](scripts/first_seen_observer.py) v0.1.0.

### Prueba sintética ejecutada, PASS

- `init`: registra solo cursor máximo y **no retroetiqueta** observaciones antiguas.
- Tras simular una fila nueva por fuente, `poll` la registra en base separada.
- Segundo `poll` sin cambios: 0 registros nuevos, sin duplicación.
- SQLite de origen se abre con `mode=ro` y `PRAGMA query_only=ON`.
- El instrumento se ejecuta por invocación manual, **sin servicio persistente**.

### Inicialización real limitada, 27-10-2026

Se instaló una copia privada del script y se inicializó manualmente **en una base privada separada de la base de adquisición**. Los cursores iniciales fueron:

| Fuente | `id` máximo inicial | Backfill histórico |
|---|---:|---:|
| `active_throughput_6g` | 9735 | 0 |
| `radio_link_config_telemetry` | 15690 | 0 |

Se ejecutó inmediatamente un `poll` sin nuevos registros, resultado **0 filas** como correspondía. La base privada se protegió con permisos `0600`. **No existe todavía evidencia de una serie continua de `first_seen_at` ni se ha activado un temporizador.**

Importante: `first_seen_at` es la hora en que el lector observa por primera vez una fila ya disponible. Funciona como cota superior conservadora de disponibilidad para ese lector, **no es una medida directa de la hora real de ingesta**. Para utilizarla operativamente se requerirán relojes sincronizados, observador de duración limitada y auditoría de huecos/latencia.

## Puertas de control antes del ensayo FEDU

1. **Observabilidad temporal:** revisión de auditoría, límites de consultas, error/reinicio/duplicados y prueba controlada de captura periódica. Evidencia: marcas `first_seen_at` de filas nuevas y ventanas sin cobertura registradas. Sin inferencia automática si faltan entradas.
2. **Definición independiente de episodio:** ficha técnica I4; separar cortes de colector, reinicios, fallos de enrutamiento y cambios de configuración de una degradación radioeléctrica real. Con pocos episodios no sostener contraste confirmatorio por eventos.
3. **Decisión preregistrada de tarea predictiva:** (a) eventos futuros de degradación bajo presupuesto de falsas alertas comparable; **o**, si su evidencia no es suficiente, (b) throughput activo futuro como desenlace continuo con persistencia de referencia. Aprobar explícitamente cualquier cambio en pregunta, objetivo, hipótesis, variables, indicadores y anexos A/B antes del test.
4. **Bloque prospectivo independiente:** después de la instrumentación temporal, definir periodo y régimen estable, bloquear versiones e hiperparámetros antes de iniciar evaluación ciega; evitar seleccionar la métrica a posteriori y reportar cobertura y dependencia por días.
5. **Integración en sombra:** solo inferencia y registro; no órdenes al radio ni pruebas activas añadidas. No publicar archivos privados en GitHub.

**Estado actual de FEDU:** desarrollo metodológico y de instrumentación en curso. **No se ha desplegado un predictor validado ni iniciado el ensayo confirmatorio.**

### Comprobación de datos reales posteriores a la inicialización

Una segunda invocación manual de `poll` a las **01:45:27 (hora Perú)** detectó **1 nueva prueba de throughput y 1 nuevo registro RF**, después de inicializar los cursores. Ambos recibieron `first_seen_at_utc = 2026-10-27T06:45:27.890+00:00` y los cursores avanzaron a throughput **9736** y RF **15691**. No se incorporaron registros históricos anteriores.

**Interpretación:** el instrumento captura filas futuras en una lectura real manual, pero **NO existe una secuencia continua y auditada de sondeos**. Esta comprobación no permite estimar la latencia típica de adquisición ni validar `available_at` con precisión operacional. La configuración del radioenlace y los servicios permanecieron sin cambios.
