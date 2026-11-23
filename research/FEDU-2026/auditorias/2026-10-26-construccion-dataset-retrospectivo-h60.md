# FEDU — Auditoría 004: construcción de dataset retrospectivo H=60 minutos

**Corte congelado:** 2026-10-26 22:10:00 −05:00 (Perú).  
**Objeto:** copia de trabajo de pares temporalmente compatibles; NO sistema causal operativo validado ni modelo entrenado.

## Ejecución y control de integridad

Se ejecutó el script reproducible [construir_pares_privados_h60.py](../scripts/construir_pares_privados_h60.py) sobre una conexión SQLite de solo lectura. La herramienta importa las mismas reglas de [auditar_pares_causales_h60.py](../scripts/auditar_pares_causales_h60.py).

El resultado se almacenó **fuera del repositorio público**, en una carpeta privada y separada de los servicios de producción del controlador, con permisos de acceso restringido. No se modificaron tablas, servicio, radio, temporizadores ni campaña.

Se generaron tres archivos:
- `X_features.csv`: 8 441 filas de predictores fechados hasta la ancla, historia de cuatro pruebas, configuración/dirección y banderas de elegibilidad RF y meteorológica.
- `y_targets.csv`: 8 441 valores futuros emparejados por `pair_id`, medidos con iperf3, separados físicamente de los predictores.
- `manifest.json`: fecha límite, reglas de exclusión, conteos agregados y SHA-256 de los archivos.

### Corte y tamaño

| Concepto | Cantidad |
|---|---:|
| Pruebas anteriores o iguales al corte | 9 709 |
| Pruebas excluidas por calidad básica | 346 |
| Pares retrospectivos generados | **8 441** |
| Pares con telemetría RF temporalmente compatible | **7 955** |
| Pares con RF y meteorología bilateral compatible | **7 000** |
| Identificadores `pair_id` diferentes | **8 441** |
| Filas del archivo X | **8 441** |
| Filas del archivo y | **8 441** |

El cribado previo sobre la base viva produjo 8 443 pares; este archivo tiene **dos menos** porque incluye un corte temporal explícito anterior a las últimas mediciones. No es una divergencia científica de la regla de selección.

### Verificaciones automáticas de salida

- `X` e `y` contienen exactamente los mismos identificadores y el mismo orden: **PASS**.
- Sin identificadores duplicados: **PASS**.
- Intervalos efectivos al objetivo: mínimo **59,2 minutos**, máximo **60,6 minutos**.
- No aparecen valores RF en columnas ocultadas cuando `rf_asof=0`: **PASS**.
- No aparecen valores meteorológicos en columnas ocultadas cuando `wx_bilateral_asof=0`: **PASS**.
- Se generaron hashes SHA-256 para permitir comprobar que la copia no cambió.

## Distribución por régimen y dirección

| Configuración MHz/MHz | DL | UL | Total |
|---|---:|---:|---:|
| 6475/20 | 611 | 606 | 1 217 |
| 6475/40 | 618 | 613 | 1 231 |
| 6655/20 | 358 | 346 | 704 |
| 6655/40 | 619 | 619 | 1 238 |
| 7000/20 | 1 661 | 1 644 | 3 305 |
| 7000/40 | 373 | 373 | 746 |
| **Total** | **4 240** | **4 201** | **8 441** |

## Advertencia metodológica de primer orden

El origen carece de marcas `available_at` o `ingested_at` plenamente verificadas. Los filtros aseguran que las marcas **observacionales** RF y ambientales no sean posteriores a la ancla `t`; esto es **necesario pero insuficiente** para certificar que eran utilizables durante la operación en tiempo real. Hasta instrumentar esas marcas, la palabra *causal* debe restringirse a **orden temporal retrospectivo**, no a disponibilidad operacional demostrada.

Tampoco se ha evaluado `MAE`, `RMSE`, `ΔMAE`, ni entrenado ML. La base generada se mantendrá como cohorte de preparación histórica; no se presentará como prueba confirmatoria reservada. Las observaciones solapadas no son réplicas independientes.

## Próximo punto de control

1. Verificar disponibilidad operacional real de colectores y respaldo, proponer registro de `available_at` para datos futuros.
2. Congelar manifiestos y la elección de predictor/referencia en rama de investigación; no desplegar hasta confirmar cierre técnico de campañas.
3. Establecer segmento prospectivo estable, cronológicamente posterior e independiente, estratificado por dirección y configuración disponible.
4. Si el objetivo principal de episodios se modifica, actualizar antes de prueba independiente la pregunta, hipótesis, variables, indicadores e instrumentos del proyecto FEDU.

**Seguridad:** no se publicaron filas crudas, telemetría individual, coordenadas, direcciones de acceso ni claves.
