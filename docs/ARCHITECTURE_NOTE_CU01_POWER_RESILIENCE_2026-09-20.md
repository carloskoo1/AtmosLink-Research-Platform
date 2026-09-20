# Nota arquitectónica — resiliencia energética de CU01

## Evento que motiva esta nota

Durante el escenario F7000_B40 de la campaña experimental 3×2, el 19–20 de septiembre de 2026, una interrupción de energía dejó fuera de servicio a la laptop Controlador de CU01.

El radioenlace de 6 GHz permaneció operativo. La afectación correspondió al nodo de adquisición/control de CU01, no a una caída RF. SJ01, basado en Raspberry Pi, mantuvo adquisición local y posteriormente sus datos pudieron sincronizarse.

El informe operacional completo se conserva en `carloskoo1/Andean-6GHz-Link-Experiment` como `INCIDENT_2026-09-19_POWER_CU01.md`.

## Limitación arquitectónica identificada

La laptop de CU01 puede sostener temporalmente la operación mediante batería, pero si llega a apagarse por completo no recupera automáticamente la ejecución cuando retorna la alimentación eléctrica y requiere intervención humana presencial.

SJ01 presenta mayor resiliencia porque su Raspberry Pi reinicia automáticamente cuando retorna la energía y los servicios de adquisición pueden recuperarse mediante el sistema de inicio.

## Decisión durante la campaña 3×2

No se modificará la arquitectura de CU01 ni se incorporará failover entre nodos durante la campaña 3×2 en curso.

La prioridad es preservar la consistencia instrumental y evitar introducir cambios que puedan actuar como variables adicionales durante el experimento.

## Evolución prevista después de la campaña

Después de finalizar la campaña 3×2 se evaluará reemplazar la laptop Controlador de CU01 por una Raspberry Pi u otro SBC adecuado para operación autónoma 24/7.

Requisito de diseño: ante pérdida total y posterior recuperación de energía, CU01 debe recuperar automáticamente adquisición, almacenamiento local, sincronización y supervisión sin intervención humana.

También podrá evaluarse posteriormente una arquitectura store-and-forward entre CU01 y SJ01, manteniendo trazabilidad de procedencia y evitando control RF concurrente desde ambos nodos.

Esta nota documenta una decisión de arquitectura futura; no introduce cambios en la plataforma experimental actualmente desplegada.
