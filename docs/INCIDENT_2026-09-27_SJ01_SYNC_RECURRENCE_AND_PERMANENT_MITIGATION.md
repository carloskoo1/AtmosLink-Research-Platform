# AtmosLink — SJ01 Synchronization Recurrence and Permanent Mitigation
## 27 September 2026

### 1. Scope

This record documents the recurrence of the SJ01 remote meteorological
synchronization failure previously observed on 26 September 2026 and the
subsequent architectural mitigation implemented on the AtmosLink
controller.

The incident affected transfer of SJ01 observations to the central
AtmosLink database and therefore the freshness indicators presented by
the scientific dashboard.

The SJ01 local weather logger remained operational during the incident.
The 6 GHz radio link, CU01 meteorological acquisition, RF telemetry and
the active field campaign remained operational.

This record concerns the remote synchronization transport path. It does
not establish that every sensor acquisition interval was valid; serial
acquisition warnings observed independently at SJ01 are outside the
scope of this incident and require separate analysis.

---

### 2. Relation to the 26 September incident

On 26 September 2026, the same synchronization path stopped because
Tailscale SSH required an additional interactive authorization check.

After that authorization was completed, synchronization recovered
automatically and two successful unattended cycles were observed.

That intervention restored service, but it did not remove the dependency
of the unattended synchronizer on the periodic interactive Tailscale SSH
authorization mechanism.

The recurrence on 27 September demonstrated that the 26 September
recovery should be interpreted as operational restoration rather than
permanent elimination of the recurrence mechanism.

See:

`docs/INCIDENT_2026-09-26_SJ01_SYNC_RECOVERY.md`

---

### 3. Recurrence

On 27 September, the AtmosLink dashboard again reported stale SJ01 data
and an unhealthy SJ01 synchronization state.

The synchronization timer remained active and continued executing every
two minutes.

The central synchronization cursor remained at:

`44727`

Repeated unattended SSH checks to:

`ckoo@100.104.97.100`

using:

`BatchMode=yes`

timed out while Tailscale SSH required an additional interactive
authorization check.

The synchronization cycles therefore reported:

- received: 0;
- inserted: 0;
- ignored: 0;
- synchronization status: ERROR.

---

### 4. Verification of local scientific data preservation

Direct inspection of SJ01 established that:

- host: `rpi-cunacales`;
- Tailscale address: `100.104.97.100`;
- local Ethernet address: `192.168.1.4/24`;
- `weather-logger-sj01.service`: active;
- local SQLite database: accessible;
- SQLite integrity check: OK;
- observations continued to be stored locally during the central
  synchronization interruption.

Therefore, the failure remained isolated to the transport/authentication
layer between the controller and SJ01.

No database repair, logger restart or sensor service restart was
required.

---

### 5. Root-cause refinement

The recurrence confirmed that the unattended synchronization mechanism
depended on an SSH path subject to an interactive Tailscale SSH
authorization check.

This is incompatible with the operational requirement of a scheduled
scientific synchronization service executing unattended every two
minutes.

The failure was therefore not attributed to:

- RF link availability;
- IP reachability;
- the SJ01 weather logger;
- SQLite corruption;
- the systemd synchronization timer;
- the multi-station builder.

The recurring failure mechanism was the authentication dependency of the
unattended synchronization path.

---

### 6. Alternative transport-path validation

Network inspection identified a direct operational LAN path between the
central controller and SJ01:

- controller: `192.168.1.50`;
- SJ01: `192.168.1.4`.

ICMP testing to SJ01 produced:

- 3 packets transmitted;
- 3 packets received;
- 0% packet loss;
- average RTT approximately 2.3 ms.

SJ01 runs the standard OpenSSH server on TCP port 22 and contains an
authorized ED25519 public key for user `ckoo`.

A non-interactive test from the controller succeeded with:

`BatchMode=yes`

and returned:

- `LAN_SSH_OK`;
- hostname `rpi-cunacales`;
- return code `0`.

The remote weather logger service could also be queried successfully
through this path, and the remote SQLite database was readable without
interactive authentication.

---

### 7. Mitigation

The effective local configuration:

`Config/remote_stations.yaml`

was changed from:

`host: 100.104.97.100`

to:

`host: 192.168.1.4`

No application code, database schema, logger configuration, RF
configuration or systemd timer configuration was changed.

`Config/remote_stations.yaml` is intentionally excluded from Git by the
repository `.gitignore`; therefore, the operational address remains a
site-local configuration rather than a version-controlled environment
value.

The resulting architecture separates two functions:

**Remote administration**

Tailscale remains available for remote administrative access to SJ01.

**Scientific synchronization**

The controller synchronizes SJ01 observations over the operational LAN
using standard OpenSSH, ED25519 public-key authentication and
`BatchMode=yes`.

This removes the periodic interactive Tailscale SSH authorization check
from the unattended scientific synchronization path.

---

### 8. Backlog recovery

After completion of the Tailscale authorization check, the final cycle
using the previous Tailscale endpoint recovered the accumulated backlog.

The synchronization cursor advanced from:

`44727`

to:

`45890`

with:

- received: 1163;
- inserted: 1163;
- ignored: 0;
- synchronization status: OK.

This recovered the locally stored observations that were pending
central transfer.

The statement `ignored=0` refers specifically to the synchronization
recovery and must not be interpreted as proof that every possible
sensor acquisition interval contained a valid observation.

---

### 9. Validation of the new LAN synchronization path

Following the endpoint change, multiple consecutive unattended timer
cycles were observed.

First LAN cycle:

- previous cursor: 45890;
- received: 1;
- inserted: 1;
- ignored: 0;
- new cursor: 45891;
- status: OK.

Second LAN cycle:

- previous cursor: 45891;
- received: 2;
- inserted: 2;
- ignored: 0;
- new cursor: 45893;
- status: OK.

Third LAN cycle:

- previous cursor: 45893;
- received: 2;
- inserted: 2;
- ignored: 0;
- new cursor: 45895;
- status: OK.

Fourth LAN cycle:

- previous cursor: 45895;
- received: 1;
- inserted: 1;
- ignored: 0;
- new cursor: 45896;
- status: OK.

All observed LAN synchronization cycles reported:

`Status global: OK`

This demonstrates continued unattended operation rather than a
single successful manual transfer.

---

### 10. Downstream pipeline validation

The multi-station master builder continued to execute after
synchronization.

At approximately 18:00 -05:

- master rows: 165084;
- CU01 records: 119195;
- SJ01 records: 45889;
- CU01 latest: 2026-09-27 22:58 UTC;
- SJ01 latest: 2026-09-27 22:59 UTC;
- builder status: OK.

Subsequent master builds also completed successfully.

The scientific dashboard subsequently reported:

- Dashboard: HEALTHY;
- Logger CU01: HEALTHY;
- Sync SJ01: HEALTHY;
- Monitor RF: HEALTHY;
- Scheduler: nominal;
- SJ01 data: fresh.

The active RF configuration remained:

`6475 MHz / 40 MHz`

---

### 11. Final state

The incident is classified as:

**RESOLVED — corrective transport-path mitigation validated in production.**

At closure:

- SJ01 local acquisition: operational;
- SJ01 central synchronization: operational;
- synchronization timer: active and enabled;
- synchronization endpoint: `192.168.1.4`;
- authentication: non-interactive OpenSSH public key;
- consecutive automatic LAN cycles: successful;
- synchronization ignored records during recovery: 0;
- multi-station master: operational;
- dashboard freshness: restored;
- RF monitoring: operational;
- active 6 GHz field campaign: unaffected by the synchronization
  correction.

No logger restart, database repair, radio reconfiguration or campaign
restart was required.

---

### 12. Follow-up items outside this incident

Two observations identified during diagnosis are intentionally separated
from this root-cause record:

1. SJ01 serial acquisition occasionally reports non-UTF-8 frames.
   Their frequency, temporal pattern and possible effect on acquisition
   completeness require a separate data-quality analysis.

2. The multi-station master builder reached high transient memory usage,
   including an observed peak of approximately 1.3 GB. Memory scaling
   should be evaluated separately as the longitudinal dataset grows.

Neither observation was identified as the cause of the synchronization
failure documented here.
