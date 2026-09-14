# AtmosLink Scientific Agent v0.1

Estado: prototipo funcional, 14-sep-2026.

## Objetivo

Proveer una interfaz analítica segura para consultar datos científicos de AtmosLink sin modificar las fuentes originales.

Principio rector: **la IA y los agentes trabajan sobre datos en modo solo lectura**. La adquisición, las tablas científicas y los datos crudos continúan siendo responsabilidad de AtmosLink Core.

## Fuente de datos

Base principal:
`SQLite/CU01/weather_local.db`

El agente abre SQLite con `mode=ro` y además activa `PRAGMA query_only=ON`.

Tablas utilizadas en v0.1:
- `master_observations_multistation`
- `radio_link_local`
- `active_throughput_6g`
- `scientific_hourly_6g_general`
## Capacidades actuales

`status` devuelve el estado científico más reciente de CU01 y SJ01, la última telemetría RF y la última prueba activa.

`window --hours N` resume una ventana horaria validada y calcula asociaciones exploratorias RF–meteorología.

`quality --hours N` reporta cobertura y validez temporal de los datos científicos horarios.

`campaign --campaign-id ID` resume throughput, RTT, retransmisiones, SNR y RSSI por dirección, frecuencia y ancho de canal.

## Ejemplos

```bash
venv/bin/python -m weather_station.agents.scientific_agent status
venv/bin/python -m weather_station.agents.scientific_agent window --hours 24
venv/bin/python -m weather_station.agents.scientific_agent quality --hours 24
venv/bin/python -m weather_station.agents.scientific_agent campaign --campaign-id CAMPAIGN_6G_20260831
```

La salida es JSON estructurado para que pueda ser consumida posteriormente por ChatGPT, Copilot, Power BI u otros agentes sin acceso de escritura a la base científica.
## Limitaciones de v0.1

- No interpreta lenguaje natural por sí solo; expone un backend analítico estructurado.
- Las correlaciones de `window` son exploratorias y no prueban causalidad.
- No modifica configuración de radios, servicios ni sensores.
- No escribe en SQLite ni en los CSV científicos.
- La campaña formal 3×2 debe analizarse con su identificador y reglas metodológicas correspondientes.

## Siguiente incremento propuesto

v0.2: capa de lenguaje natural y catálogo de consultas científicas controladas.

v0.3: exportación de reportes reproducibles y conexión con Power BI / Microsoft 365.

v0.4: agentes separados por rol: operacional, científico, tesistas y reportes.

## Gobernanza

Toda respuesta derivada de AtmosLink debe conservar fuente, ventana temporal, cobertura, filtros y advertencias metodológicas. Los datos crudos son inmutables para la capa de IA.
