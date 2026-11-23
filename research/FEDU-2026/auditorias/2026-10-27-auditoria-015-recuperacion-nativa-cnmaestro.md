# FEDU — Auditoría 015: recuperación directa de eventos nativos cnMaestro (1 y 4 de septiembre)

**Fecha de auditoría:** 27-oct-2026. **Estado:** evidencia autenticada descargada; adjudicación del plano físico RF en revisión. **Equipo de análisis:** Windows Research, Firefox cnMaestro Cloud, cuenta previamente autenticada del operador. **Intervención:** exclusivamente navegación en `Notifications > Events`, filtros temporales y exportación CSV. No hubo operaciones sobre RF, configuración, firmware ni PoE.

## 1. Evidencia de custodia y procedencia

Los CSV originales proceden de los dispositivos vinculados al radioenlace 6 GHz y fueron guardados en la carpeta privada de Windows `Documentos/FEDU_2026_Privado/cnMaestro_2026-10-27/`. Existen además en Descargas y un `manifest_exports.json` con hash SHA-256, número de filas y límites temporales.

| Dispositivo / exportación | Muestras | SHA-256 del CSV original | Alcance |
|---|---:|---|---|
| **SM SanJose6** — eventos filtrados 03–05-sep, página completa | **18** | `C5C96D37D143E0EB11E343B028673068BAC7CBBD6DE611C647CF43C06F713B6B` | Gestión SM `STATUS_DOWN/STATUS_UP` |
| **Switch EX1010P-BA56E0** — eventos filtrados 31-ago–06-sep, página 1 de 100 filas | **100** | `D6BADDFB19F9A20262560ABD563D937E10D050E3D0A5506BA51988E4F059BCDB` | `LINK_ST` de puertos, estado de gestión |
| **Switch** — filtro previo 03–05-sep, página de 3 filas | **3** | `59E37EA03F7C702F097E0025D742DAB76066639C186017AF3342453EBE39BF32` | Parte de los mismos eventos; no sumar como sucesos nuevos |
| **AP Cunacales6** — página de eventos recientes 27-oct | **10** | `8ABC5C6AC46FBDD69869032ACECE52298AB5696694F7082C82F47A70C9E6D0C1` | Contexto y prueba de exportación, no datos de sep |

**Precaución temporal:** el campo `Raised Time` de los CSV no lleva zona horaria ni offset, a diferencia de muchos archivos originales de AtmosLink. La interfaz de cnMaestro mostró las mismas horas y el usuario opera en Perú; comparar con series locales es **consistente**, pero el huso del archivo requiere comprobación documental del ajuste de la cuenta. En las conclusiones se habla de **horas mostradas por cnMaestro** hasta su verificación.

El archivo de **100 eventos del switch** contiene el episodio del 01-sep. Es una **página**, no una exportación exhaustiva del histórico anual: el portal indicó `Showing 1-100 of Many`. No declarar respaldo global completo de cnMaestro.

## 2. Hallazgo AOP-UTP-SEP-001 — fuente nativa del puerto 6

En CSV original del **switch** aparece la interfaz **`0/6`**, mapeada documentalmente al AP CU01 de 6 GHz, con eventos nativos:

| Marca `Raised Time` | `Event ID` | Mensaje original |
|---|---|---|
| **01-sep 19:37:15** | `LINK_ST` | `Link status change (down) - interface 0/6` |
| **01-sep 19:58:22** | `LINK_ST` | `Link status change (up) - interface 0/6` |
| 01-sep 19:58:27 | `LINK_ST` | `Link status change (down) - interface 0/6` |
| 01-sep 19:58:30 | `LINK_ST` | `Link status change (up) - interface 0/6` |
| 01-sep 19:58:39 | `LINK_ST` | `Link status change (down) - interface 0/6` |
| 01-sep 19:58:41 | `LINK_ST` | `Link status change (up) - interface 0/6` |
| 01-sep 19:59:40 | `LINK_ST` | `Link status change (down) - interface 0/6` |
| **01-sep 19:59:42** | `LINK_ST` | `Link status change (up) - interface 0/6` |

**Primer intervalo sin enlace Ethernet (según cambios registrados):** **19:37:15 a 19:58:22**, **21 min 07 s**, con rebotes adicionales hasta las 19:59:42. No interpretar como tiempo total de AP apagado ni duración de pérdida de asociación RF.

En el mismo CSV hay un `LINK_ST down` de la interfaz `0/3` a las **19:08:18** del 01-sep. Esta es otra conexión (asociada al AP de legado 5,8 GHz) y no debe confundirse con `0/6`.

**Triangulación:** El usuario aportó conversación de campo contemporánea donde a las 19:57 pide verificar el puerto 6 y a las 19:59 el técnico informa que el cable estaba movido y fue conectado nuevamente. La adquisición AP de `radio_link_local` pasó de normal 19:36:37 a anómala 19:37:48, y volvió a normal 20:01:53. `radio_link_config_telemetry` volvió `LINK_OPERATIONAL_DUAL` a 20:04:07. Tres clases de evidencia concordantes: **switch físico enlace de puerto**, **operación de campo contemporánea**, **telemetría de acceso RF recuperada**.

**Dictamen revisado para AOP-UTP-SEP-001:** `PHYSICAL_ETHERNET_LINK_DOWN_AP6_PORT6_CONFIRMED` y `PHYSICAL_ETHERNET_LINK_RESTORED_CONFIRMED`; alta confianza para el enlace Ethernet físico. **No** está acreditada caída de alimentación PoE con log eléctrico, ni confirmación de asociación RF AP–SM con evento nativo separado. No etiquetar automáticamente como `DEGRADACION_RF_GRADUAL` predictiva (falla súbita exógena).

## 3. Hallazgo C001 / C002 — estados nativos del SM

El CSV autenticado de **SanJose6** registra:

| Ventana de interés | `STATUS_DOWN` | `STATUS_UP` | Duración de estado offline mostrado |
|---|---|---|---|
| C001 | **04-sep 08:00:21** | **04-sep 08:33:23** | 33 min 02 s |
| Intervalo intermedio | 04-sep 08:54:21 | 04-sep 08:57:55 | 3 min 34 s |
| **C002** | **04-sep 09:11:51** | **04-sep 16:14:17** | **7 h 02 min 26 s** |
| Episodio corto cercano al cierre C002 | 04-sep 16:18:52 | 04-sep 16:21:57 | 3 min 05 s |

Otros pares `STATUS_DOWN/UP` cortos fueron observados el 03-sep 14:28 y 04-sep a las 19:16, 20:55, 21:44 y 21:49, todos preservados en el CSV original.

La duración aproximada de 7 horas concuerda temporalmente con 56 `iperf3 ERROR` y las **403 capturas `show sta`** auditadas (392 respuestas de sesión SSH sin tabla `cambiumAPConnectedSTATable`, 11 sin respuesta útil y 0 con SM esperado en tabla) en la ventana C002. Este es un **hallazgo de coincidencia entre el plano de gestión cloud y fallos operativos locales** que hace mucho más plausible que no fuera solamente un error aislado del script de colección.

**Límite de independencia:** el estado `STATUS_DOWN` de cnMaestro significa que el **dispositivo no era alcanzable en el plano de gestión reportado**; también pueden explicarlo pérdida de uplink, Internet, agente, alimentación o radio. Por ello **no es una confirmación inequívoca de corte físico RF causado por propagación**. Del mismo modo, las dos filas cloud `STATUS_DOWN` de SM y switch en 04-sep 08:00:21 podrían compartir causa o derivación y no representan automáticamente dos sensores autónomos.

**Dictamen revisado C001:** `SM_CLOUD_MANAGEMENT_OFFLINE_CORROBORATED`, `RF_PHYSICAL_CAUSE_UNRESOLVED`.  
**Dictamen revisado C002:** `SM_CLOUD_MANAGEMENT_OFFLINE_LONG_INTERVAL_CORROBORATED`, `THROUGHPUT_ERRORS_CORROBORATED`, `AP_STA_TABLE_MISSING_CORROBORATED`, `RF_PHYSICAL_CAUSE_UNRESOLVED`.

Ninguno autoriza etiquetar `RF_SOFT_DEGRADATION` ni entrenar/validar un predictor confirmatorio por propagación sin una definición independiente de **servicio** y una regla de exclusiones. **No asignar `y=0` a intervalos sin observación válida**.

## 4. Otros hallazgos del switch

- **04-sep 03:25:59**: `LINK_ST down - interface 0/1`.
- **04-sep 03:26:00**: `LINK_ST up - interface 0/1`.
- **04-sep 08:00:21**: `STATUS_DOWN` de gestión del switch.

No atribuir eventos de la interfaz `0/1` al puerto `0/6`. `STATUS_DOWN` no identifica por sí solo el puerto o PoE y coincide con pérdida de gestión del SM en C001.

## 5. Siguiente adjudicación y requisitos

1. **Preservación completada** de originales descargados en Windows privado, con hashes en `manifest_exports.json`. No publicar CSV brutos, identificadores de dispositivos ni credenciales.
2. Exportar eventos de **AP Cunacales6** del 01-sep y del 04-sep si hay historial; la consulta del AP 03–05-sep inicialmente devolvió `No Data Available` y no permite afirmar nada sobre la física del enlace.
3. Revisar `Alarms History` del SM, AP y switch si la cuenta los retiene; mantener distinguidas notificaciones de gestión vs eventos RF nativos.
4. Revisar enlace AP–SM por entradas inequívocas `STA_REG/STA_DROP/STA_REJECT`, usando ventanas reales y reloj declarado; no completar supuestos desde `STATUS_DOWN`.
5. Incorporar a [registro de adjudicación](../anexos/registro_adjudicacion_verdad_terreno_v0.csv) nuevas **columnas separadas** de cambio físico de switch, gestión cloud, estado RF nativo, servicio funcional y causa. Mantener `NA` cuando no haya test independiente para tarea concreta.
6. Definir antes de test prospectivo cuál variable objetivo (degradación de servicio vs de asociación RF) puede ser verificada sin circularidad.

**Resultado:** la falta de verdad-terreno de C002 se ha **reducido sustancialmente** con archivo cloud auténtico, pero la causa RF física sigue abierta. En cambio AOP-UTP-SEP-001 ha avanzado de relato de operador a **fallo/recuperación física Ethernet corroborados por el propio switch cnMatrix**, sin afirmar PoE o propagación.

