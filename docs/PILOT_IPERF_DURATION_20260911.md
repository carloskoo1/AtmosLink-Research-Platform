# Piloto de selección de duración iperf3 para campaña experimental 6 GHz

**Proyecto:** AtmosLink / campaña experimental 3×2
**Enlace:** CU01 – SJ01
**Fecha del piloto:** 11 de septiembre de 2026
**Horario:** 15:24:42 – 16:11:55 (-05:00)
**Estado:** PILOTO PREVIO A CAMPAÑA FORMAL
**Campaña formal:** inicio previsto 15 de septiembre de 2026

## 1. Objetivo

Determinar una duración adecuada para las pruebas activas TCP con iperf3 que serán utilizadas en la campaña experimental formal 3×2, buscando un equilibrio entre:

- estabilidad de la medición de goodput;
- variabilidad entre repeticiones;
- comportamiento de retransmisiones TCP;
- carga inducida sobre el radioenlace;
- duración total de la campaña experimental.

Este piloto no forma parte de los tratamientos formales de la campaña 3×2.

## 2. Configuración controlada

Durante el piloto se mantuvo fija la configuración operacional del radioenlace.

Se evaluaron tres configuraciones de iperf3:

| Configuración | Duración | Omit | Flujos paralelos |
|---|---:|---:|---:|
| A | 8 s | 1 s | 1 |
| B | 15 s | 2 s | 1 |
| C | 30 s | 2 s | 1 |

Protocolo: **TCP**

Direcciones evaluadas:

- DL
- UL

Las direcciones fueron medidas secuencialmente.

## 3. Diseño experimental del piloto

Se empleó un diseño por bloques con orden variable de las tres duraciones para reducir el sesgo temporal.

Número de bloques: **10**

En cada bloque se ejecutaron las tres configuraciones de duración.

Cada configuración generó:

- 1 medición DL;
- 1 medición UL.

Por tanto:

- 10 mediciones por duración y dirección;
- 20 mediciones por duración;
- 60 mediciones totales.

Intervalo aproximado entre ejecuciones: **45 s**.

El timer operativo de AtmosLink:

`atmoslink-throughput-6g.timer`

fue detenido durante el piloto para evitar interferencia de las pruebas rutinarias de 8 s.

Antes del piloto se verificó:

- timer: inactive;
- service: inactive.

Al finalizar se restauró el timer y se verificó:

- `Active: active (waiting)`;
- siguiente disparo correctamente programado.

## 4. Identificación de los datos

Base de datos:

`SQLite/CU01/weather_local.db`

Tabla:

`active_throughput_6g`

Rango exclusivo correspondiente al piloto:

- ID inicial previo: 1882
- primer registro del piloto: 1883
- último registro del piloto: 1942
- total generado: 60 registros

Todas las mediciones del piloto utilizadas en el análisis finalizaron con estado:

`OK`

## 5. Resultados

### 5.1 Throughput DL

| Duración | n | Media Mbps | Mediana Mbps | Desv. estándar Mbps |
|---|---:|---:|---:|---:|
| 8 s | 10 | 47.517 | 46.863 | 3.871 |
| 15 s | 10 | 45.770 | 45.509 | 1.514 |
| 30 s | 10 | 46.333 | 46.278 | 2.062 |

La configuración de 15 s presentó la menor dispersión en DL.

### 5.2 Throughput UL

| Duración | n | Media Mbps | Mediana Mbps | Desv. estándar Mbps |
|---|---:|---:|---:|---:|
| 8 s | 10 | 32.073 | 32.113 | 0.064 |
| 15 s | 10 | 32.031 | 32.052 | 0.073 |
| 30 s | 10 | 32.045 | 32.051 | 0.040 |

Las tres configuraciones mostraron un comportamiento prácticamente equivalente en UL.

### 5.3 RTT promedio

| Duración | RTT promedio |
|---|---:|
| 8 s | 3.246 ms |
| 15 s | 3.464 ms |
| 30 s | 3.359 ms |

No se observaron diferencias relevantes en RTT entre las tres configuraciones.

### 5.4 Retransmisiones TCP

Mediana de retransmisiones normalizada por segundo:

| Duración | DL ret/s | UL ret/s |
|---|---:|---:|
| 8 s | 5.875 | 3.000 |
| 15 s | 4.867 | 2.467 |
| 30 s | 4.483 | 1.633 |

Las pruebas de mayor duración mostraron una menor tasa de retransmisiones por segundo.

No obstante, las retransmisiones absolutas no deben compararse directamente entre pruebas de diferente duración, debido a que una prueba más larga tiene mayor tiempo disponible para acumular eventos de retransmisión.

## 6. Interpretación

La configuración de 8 s presenta una mayor variabilidad en DL, por lo que resulta más sensible a condiciones instantáneas del enlace y a la dinámica transitoria de TCP.

La configuración de 30 s proporciona resultados estables, pero incrementa significativamente el tiempo de ocupación del enlace sin producir una mejora proporcional en el goodput medido.

La configuración de 15 s presenta:

- la menor desviación estándar en DL;
- throughput UL prácticamente idéntico a 8 s y 30 s;
- RTT equivalente;
- menor tasa de retransmisiones por segundo que 8 s;
- menor carga experimental que una prueba de 30 s.

Por ello, constituye el mejor compromiso entre estabilidad estadística, duración de prueba y carga sobre el radioenlace.

## 7. Decisión metodológica

Se adopta para la campaña experimental formal 3×2 el siguiente protocolo:

- **Protocolo:** TCP
- **Duración iperf3:** 15 s
- **Omit inicial:** 2 s
- **Flujos paralelos:** 1
- **Direcciones:** DL y UL
- **Ejecución:** secuencial, no simultánea

Esta configuración deberá mantenerse sin cambios durante los seis tratamientos de la campaña formal para preservar la comparabilidad experimental.

## 8. Separación entre AtmosLink y campaña formal

Las pruebas activas rutinarias de AtmosLink continuarán utilizando su configuración operacional de monitoreo:

- duración: 8 s;
- omit: 1 s;
- parallel streams: 1;
- ejecución periódica mediante systemd.

Estas pruebas tienen una finalidad distinta: supervisión continua del enlace.

La campaña experimental 3×2 utilizará exclusivamente el protocolo formal seleccionado en este piloto:

**15 s / omit 2 s / 1 stream**

Los datos generados antes del 15 de septiembre de 2026 deberán tratarse como:

`PILOT / BASELINE`

y no mezclarse con los datos de los tratamientos formales.

## 9. Conclusión

El piloto de 60 mediciones permitió comparar experimentalmente tres duraciones de prueba iperf3 bajo condiciones controladas.

La duración de 15 s proporcionó el mejor equilibrio entre estabilidad del goodput, variabilidad, retransmisiones TCP y tiempo de ocupación del enlace.

En consecuencia, se establece como configuración definitiva para las pruebas activas TCP de la campaña experimental formal 3×2:

**TCP — 15 s — omit 2 s — 1 flujo — DL/UL secuenciales.**
