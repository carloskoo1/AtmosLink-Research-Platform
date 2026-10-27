# FEDU — Registro preliminar de incidente físico UTP/PoE y pérdida de acceso remoto

**Fecha de registro del testimonio:** 27 de octubre de 2026 (Perú).  
**Código provisional:** AOP-UTP-SEP-001.  
**Estado:** `OPERADOR_REPORTADO_NO_VERIFICADO`.  
**Ámbito:** exclusivamente la infraestructura del radioenlace físico CU01–SJ01 y sus conexiones de red/supervisión.  
**No constituye etiqueta de degradación RF ni episodio confirmado de corte de servicio.**

## 1. Testimonio del responsable de campo

El responsable recuerda que, **pocos días después de comenzar la experimentación de septiembre de 2026**, se desconectó del switch un **cable UTP/PoE correspondiente al AP del radioenlace de 6 GHz**, tras lo cual perdió acceso remoto. **Aclaración explícita del operador del 27-oct-2026:** el cable estaba conectado al **AP de 6 GHz**, no al Controlador ni a Starlink. En la declaración inicial consideraba posible que no se hubiera perdido el enlace, pero esa impresión no está sustentada por una comprobación local registrada del AP y SM durante la interrupción.

**Queda confirmado por testimonio qué equipo estaba al extremo del cable: el AP de 6 GHz.** No se conoce todavía la fecha exacta, el puerto preciso, la duración ni si la desconexión interrumpió la alimentación PoE del AP. Si esa era su única alimentación y el cable fue físicamente retirado, el AP habría quedado sin energía, por lo que **la continuidad física del enlace AP–SM sería muy improbable**. No convertir esta consecuencia condicionada en hecho observado sin comprobar eventos del switch, uptime y asociación del SM.

## 2. Confrontación con registros existentes sin atribución indebida

- **15-sep:** una transición a F6655_B20 falló y hubo pérdida de acceso al extremo remoto; se realizó **un ciclo PoE intencional** en puerto 6 del cnMatrix (AP 6 GHz), como recuperación. Eso **no es evidencia de un cable UTP accidentalmente desenchufado**.
- **19-sep ~13:34 a 20-sep ~09:19:** incidente documentado de pérdida de controlador de CU01 por interrupción de energía; los informes de campaña indican continuidad física RF y adquisición local SJ01. **No describen desconexión UTP**. Candidato a explorar por coincidencia temporal y de síntoma de inaccesibilidad, sin igualarlo al testimonio.
- **20-sep:** cnMatrix `Offline` en cnMaestro debido a problemas del plano de gestión IPv4/ruta, mientras LAN, PoE y radios seguían operativos. **No se documenta retirada de un cable**. Otro candidato contextual, no equivalente.
- No asignar este testimonio a ninguno de los ocho I4 C001, C002, C003, C011, C016, C020, C022 o C024. Corresponden a otros días y no existe correspondencia individual acreditada.

Referencias locales bajo el controlador:
- `Andean-6GHz-Link-Experiment/INCIDENT_2026-09-15.md`
- `Andean-6GHz-Link-Experiment/INCIDENT_2026-09-19_POWER_CU01.md`
- `EstacionMeteorologica/docs/INCIDENT_2026-09-20_CNMatrix_CU01_RECOVERY.md`
- `EstacionMeteorologica/docs/DAILY_TRACE_2026-09-20_ATMOSLINK_3X2.md`

## 3. Hipótesis técnicas alternativas, no diagnóstico

| Conexión eventualmente interrumpida | Pérdida probable | Continuidad del radioenlace |
|---|---|---|
| Puerto del switch que transporta Ethernet **y PoE al AP 6 GHz** | AP podría apagarse y dejar de emitir, además de perderse gestión | **No presumible**; requiere respaldo o alimentación por otra ruta |
| Puerto de enlace superior hacia router/Starlink o acceso de gestión remota | Internet/cnMaestro/acceso externo, posiblemente sin afectar el tráfico local AP–SM | **Posible**, verificar con adquisiciones y pruebas locales |
| Puerto del controlador/gestión local sin alimentación del AP | Acceso al Controlador, generación de logs centralizados y pruebas remotas | **Posible**, verificar telemetría conservada en SJ01 y estado AP–SM |
| Cable no identificado o topología desconocida | Efectos no deducibles | **INDETERMINADO** |

La afirmación «se perdió mi acceso remoto» demuestra únicamente **pérdida de observabilidad remota** según testimonio. No equivale a `RF_LINK_DOWN`, `LOCAL_SERVICE_DOWN` ni a una falla predictible RF.

## 4. Evidencias por recuperar, solo de la infraestructura de este enlace

1. Identidad del **puerto físico** del switch y de ambos extremos del cable (AP 6 GHz, Controlador, router/Starlink, uplink, etc.) a partir de plano/topología, fotografía, nota de mantenimiento o recuerdo preciso del operador.
2. Fecha y hora de retirada y reposición, si existen bitácoras de intervención humana.
3. Logs **históricos propios del switch cnMatrix**: `link-up/link-down` del puerto, estado PoE, `ifOperStatus`, LLDP o contadores de errores, con hora y retención documentados; consultas de **solo lectura** y sin ciclos de PoE.
4. Registros firmware **AP CU01 / SM SJ01** (uptime, asociación, disponibilidad RF, interrupciones), y pruebas funcionales locales de 6 GHz que sean independientes de Internet/gestión.
5. Comprobar continuidad de la adquisición local en SJ01 y posible interrupción solo de centralización/Internet. La ausencia de filas CU01 no prueba corte RF.
6. Contrastar primero ventanas del 15, 19 y 20 de septiembre, **sin fijar una fecha por semejanza de síntomas**.

## 5. Destino metodológico

**Clase provisional:** `ACCESS_REMOTE_LOST_UNVERIFIED_UTP` (fuente: testimonio). Solo después de verificar topología y registros podrá considerarse `MANAGEMENT/WAN_ONLY`, `LAN_ACCESS`, `AP_POWER_INTERRUPTED`, `LOCAL_SERVICE_INTERRUPTED` o `RF_LINK_INTERRUPTED`.

Para FEDU, este episodio sería especialmente útil como **control negativo** de un detector que no deba etiquetar pérdidas de acceso remoto como caídas RF, **si** se acredita que el AP–SM y el servicio local persistieron. Si el cable desconectado alimentaba el AP, podría tratarse de un evento súbito **no anticipable con telemetría RF sola**, separando detección de predicción. No utilizar el testimonio como etiqueta positiva o negativa ni sumar el episodio al número de eventos confirmado.

**Acciones ejecutadas:** auditoría documental. **Sin cambios** en RF, switch, PoE, red, adquisición o campaña.

## 6. Rectificación por declaración del operador (27-oct-2026)

El operador precisó inequívocamente: «al AP de 6GHZ». En consecuencia, se **descarta como hipótesis principal** que se tratara del cable del Controlador o del uplink Starlink. En este caso, el foco es identificar **qué puerto del switch alimentaba/comunicaba al AP 6 GHz**, registrar si hubo `PoE off`/ausencia de alimentación, y determinar cuánto tiempo el SM estuvo desasociado, si ocurrió. El incidente de ciclo PoE intencional del 15-sep sigue siendo **otro evento documentado, no necesariamente el mismo**.

La clase preliminar se refina a `AP_6GHZ_UTP_DISCONNECTED_OPERATOR_REPORTED`. **No asignar todavía `RF_LINK_DOWN` confirmado ni usar el episodio como control negativo de caída RF.** Para evaluar predicción de este hecho, distinguir el corte **exógeno abrupto** (probablemente no anticipable por una serie RF) de su **detección** mediante evidencia del switch, AP y SM.
