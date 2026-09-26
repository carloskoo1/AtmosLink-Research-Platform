# AtmosLink — SJ01 Synchronization Incident and Recovery
## 26 September 2026

### 1. Scope

This record documents the temporary loss of remote meteorological
synchronization from station SJ01 to the central AtmosLink controller
during the active 6 GHz field campaign.

The incident affected remote data transfer and dashboard freshness
indicators. It did not interrupt the 6 GHz radio link, CU01 acquisition,
RF telemetry, active throughput measurements or the SJ01 weather logger.

No loss of scientific observations was detected.

---

### 2. Initial condition

The AtmosLink dashboard reported:

- SJ01: `SIN DATOS RECIENTES`;
- `Sync SJ01`: error;
- global platform health: error.

The latest centrally available SJ01 observation was approximately
22.9 hours old. The synchronization timer remained active and retried
the operation every two minutes.

### 3. Diagnosis

Read-only diagnostics established that:

- `rpi-sanjose64` was online in Tailscale;
- ICMP latency was 2–5 ms with 0% packet loss;
- TCP port 22 was reachable;
- the SSH handshake completed successfully;
- Tailscale SSH required an additional interactive authorization check;
- `weather-logger-sj01.service` remained active.

Therefore, the failure was isolated to the Tailscale SSH authorization
layer used by the unattended remote synchronizer. It was not an RF,
routing, database or sensor acquisition failure.

The temporary authorization URL and all authentication material were
intentionally excluded from this repository.

---

### 4. Recovery

After the Tailscale authorization check was completed, the next
scheduled synchronization recovered automatically without restarting
services or modifying application code.

Recovery cycle at approximately 00:06 -05:

- remote logger status: active;
- received: 889 observations;
- inserted: 889 observations;
- ignored: 0 observations;
- local sequence advanced from 43358 to 44247;
- synchronization status: OK.

The multi-station master was rebuilt successfully:

- total rows: 161010;
- CU01 latest observation: 2026-09-26 00:04 -05;
- SJ01 latest observation: 2026-09-26 00:04 -05;
- builder status: OK.

---

### 5. Automatic-cycle validation

A second unattended timer execution was observed at approximately
00:08 -05:

- received: 2 new observations;
- inserted: 2 observations;
- ignored: 0 observations;
- local sequence advanced to 44249;
- synchronization status: OK.

This confirmed that recovery was not limited to a single manual
connection and that the scheduled synchronization path was operational.

---

### 6. Final state and impact

At closure:

- CU01 data: fresh;
- SJ01 data: fresh;
- RF telemetry: fresh;
- `Sync SJ01`: healthy;
- global system health: healthy;
- active RF configuration: 6655 MHz / 40 MHz;
- 6 GHz campaign: active.

No radio, frequency, channel width, VLAN, PoE, scheduler or scientific
database configuration was changed during the recovery.

The incident is technically closed. AtmosLink remains in continuous
acquisition mode.
