# Informe de incidente — recuperación del cnMatrix EX1010-P de CU01

**Fecha:** 2026-09-20  
**Sitio:** CU01 — Cerro Cuñacales  
**Equipo:** Cambium Networks cnMatrix EX1010-P  
**System name:** `EX1010P-BA56E0`  
**Software observado:** `6.1.2-r4`  
**Estado final:** recuperado y **Online** en cnMaestro

## 1. Resumen ejecutivo

Durante la supervisión de CU01 se detectó que el cnMatrix `EX1010P-BA56E0` figuraba Offline en cnMaestro, aunque la LAN, los radios y el host Controlador seguían operativos.

El diagnóstico demostró que el switch no estaba averiado: continuaba conmutando tráfico, ejecutando RSTP, anunciándose por LLDP y suministrando PoE. La anomalía estaba concentrada en el plano de administración.

Se confirmaron dos problemas principales:
- la interfaz de administración `vlan1` tenía `192.168.1.1/24`;
- `192.168.1.1` ya correspondía al router Starlink de CU01;
- el switch no tenía ruta IPv4 por defecto.

La recuperación se realizó sin factory reset, sin reboot y sin cambios RF.
## 2. Evidencia de funcionamiento L2

Desde `Controlador` se verificó que `192.168.1.8` (AP 6 GHz) respondía con 0 % de pérdida y latencia aproximada de 0.5 ms, descartando una caída general de CU01.

Una captura Ethernet sobre `enp1s0` mostró BPDUs RSTP desde el cnMatrix:

```text
30:cb:c7:ba:56:e2 > 01:80:c2:00:00:00
STP 802.1w, Rapid STP
bridge-id 8000.30:cb:c7:ba:56:e1
```

LLDP identificó inequívocamente el equipo:

```text
System Name: EX1010P-BA56E0
Cambium Networks cnMatrix EX1010-P Ethernet Switch HW:01 SW:6.1.2-r4
Port ID: Gi0/2
Port Description: Ethernet Interface Port 2
Chassis MAC: 30:cb:c7:ba:56:e1
```

La MAC de inventario en cnMaestro era `30:CB:C7:BA:56:E0`; el switch empleaba MAC derivadas `...:E1` y `...:E2` en sus interfaces internas.
## 3. Hallazgo crítico: conflicto de IPv4

LLDP anunció la dirección de gestión:

```text
Management Address: 192.168.1.1
```

La GUI confirmó:

```text
Interface: vlan1
IP allocation: Manual
IPv4: 192.168.1.1
Mask: 255.255.255.0
```

En CU01, `192.168.1.1` corresponde al router Starlink y al gateway de la LAN. Existía por tanto una colisión directa:

```text
Starlink gateway       192.168.1.1
cnMatrix management    192.168.1.1
```

Además, la tabla de routing solo contenía `192.168.1.0/24` como red conectada y no existía una ruta `0.0.0.0/0`.

## 4. Recuperación mediante IPv6 link-local

Se identificó la dirección:

```text
fe80::32cb:c7ff:feba:56e1%enp1s0
```

Los puertos 22, 80 y 443 estaban abiertos. SSH rechazó las credenciales probadas, pero HTTPS permaneció disponible.
Desde una estación Windows se estableció temporalmente un túnel SSH a través de Controlador para alcanzar la GUI del cnMatrix por IPv6 link-local. Esto permitió recuperar acceso sin desplazamiento físico al sitio.

## 5. Corrección aplicada

Se modificó la gestión IPv4 de `vlan1`:

```text
IPv4:          192.168.1.32
Subnet mask:   255.255.255.0
Address type:  Primary
Allocation:    Manual
```

Se añadió la ruta por defecto:

```text
Destination:  0.0.0.0
Mask:         0.0.0.0
Gateway:      192.168.1.1
Metric:       1
Protocol:     Static
```

Se conservaron la ruta conectada `192.168.1.0/24 -> vlan1` y se configuraron DNS:

```text
8.8.8.8
192.168.1.1
```

La configuración fue guardada con `Save`.
## 6. Validación posterior

Desde Controlador:

```text
PING 192.168.1.32
4 packets transmitted
4 received
0% packet loss
RTT min/avg/max ≈ 2.285 / 2.344 / 2.378 ms
```

HTTPS respondió en `https://192.168.1.32`. Un `curl -I` devolvió HTTP 405 por el método HEAD, confirmando igualmente que el servidor `lighttpd/1.4.71` estaba activo.

Desde la herramienta IP Ping del propio cnMatrix se verificó el gateway:

```text
Target: 192.168.1.1
Requests sent: 3
Responses: 3
Packet loss: 0%
Average RTT: 2 ms
```

## 7. Recuperación de cnMaestro

En `System -> Remote Manager` se observó:

```text
Remote Management: Enabled
Remote Manager: cnMaestro
Connection State: Connected
Current Remote Manager URL: cloud.cambiumnetworks.com
cnMaestro Account ID: CONSORCIO_DISTRIBUIDOR
Last Action: Connected
```

Posteriormente cnMaestro mostró `EX1010P-BA56E0` como **Online**.
## 8. IPv6 observado

El switch mantiene IPv6 activa sobre `vlan1`, incluyendo una dirección global en el prefijo:

```text
2803:9810:614b:8708::/64
```

y una ULA en:

```text
fd68:8cb6:4698:8::/64
```

cnMaestro reportó la IPv6 global como dirección visible. El cliente DHCPv6 no estaba configurado; por ello, la obtención mediante Router Advertisement/SLAAC es una hipótesis operativa plausible, pero no fue verificada de manera concluyente durante esta intervención.

No se deshabilitó IPv6.

## 9. Reloj y SNTP

El sistema quedó en UTC (`+00:00`, sin horario de verano). SNTP mostraba:

```text
Administrative Status: Enabled
Client Version: Version 4
Addressing Mode: Unicast
Client Port: 123
Auto Discovery: Enabled
```

No existía un servidor unicast explícito. Los intentos de añadirlo desde GUI terminaron en `ERROR: Issue creating SNTP unicast server entry`. Se dejó este punto como pendiente no crítico para una ventana de mantenimiento o revisión por CLI.
## 10. Causa raíz y alcance

### Causa confirmada

La condición anómala principal fue el conflicto:

```text
cnMatrix management IPv4 = 192.168.1.1
Starlink gateway IPv4    = 192.168.1.1
```

acompañado por ausencia de ruta IPv4 por defecto.

La corrección de direccionamiento, routing y DNS produjo una gestión IPv4 coherente y fue seguida por la recuperación del estado Online en cnMaestro.

### Origen del cambio: no determinado

El switch mostraba aproximadamente un día de uptime, lo que confirma un reinicio reciente, pero no permite atribuir por sí solo el retorno a `192.168.1.1`.

No se demostró que hubiera ocurrido factory reset, corrupción de startup-config, cambio manual o cambio inducido por cnMaestro.

## 11. Estado final de referencia

| Parámetro | Valor |
|---|---|
| Sitio | CU01 — Cerro Cuñacales |
| Equipo | Cambium cnMatrix EX1010-P |
| System name | `EX1010P-BA56E0` |
| Software | `6.1.2-r4` |
| Management VLAN | `vlan1` |
| IPv4 management | `192.168.1.32/24` |
| Gateway | `192.168.1.1` |
| Default route | `0.0.0.0/0 -> 192.168.1.1` |
| DNS | `8.8.8.8`, `192.168.1.1` |
| HTTPS | operativo |
| RSTP | operativo |
| PoE | operativo |
| cnMaestro | Online / Connected |
| IPv6 | activa |
| SNTP | enabled / unicast / auto-discovery |
| Factory reset | no realizado |
| Reboot durante recuperación | no realizado |
## 12. Reglas operativas derivadas

1. `192.168.1.1` queda reservado exclusivamente para el gateway Starlink de CU01.
2. La IPv4 de administración estable del cnMatrix de CU01 es `192.168.1.32/24`.
3. Antes de cambiar IP, VLAN o routing del cnMatrix debe existir una vía alternativa de recuperación.
4. La IPv6 link-local es una ruta de rescate válida cuando falla el plano IPv4 de administración.
5. No ejecutar factory reset como primera medida mientras switching y PoE continúen operativos.
6. Verificar `Save` después de cualquier cambio persistente.
7. Un estado Offline en cnMaestro no implica necesariamente una falla del dataplane Ethernet.
8. En incidentes futuros revisar por separado L2, IPv4, IPv6, default route, DNS y Remote Manager.

## 13. Procedimiento mínimo futuro

1. Probar `ping 192.168.1.32`.
2. Verificar gateway y radios para descartar caída general.
3. Revisar ARP/ND y LLDP antes de reiniciar.
4. Si IPv4 falla, localizar IPv6 link-local mediante LLDP/tcpdump.
5. Probar HTTPS por IPv6 link-local.
6. Revisar `vlan1`, IPv4, default route, DNS y Remote Manager.
7. No resetear mientras L2/PoE permanezcan operativos.
8. Documentar cualquier modificación antes de reiniciar.

## 14. Conclusión

El incidente no correspondió a una falla física del cnMatrix. El switch continuó operativo en capa 2 durante el diagnóstico.

La combinación de observación pasiva RSTP/LLDP, recuperación por IPv6 link-local y corrección controlada del plano IPv4 permitió restablecer la administración y cnMaestro sin factory reset, sin reboot y sin alterar la configuración RF del experimento.

Este incidente refuerza la necesidad de mantener documentado y reservado el plan de direccionamiento de CU01 y conservar rutas independientes de recuperación para la infraestructura crítica.
