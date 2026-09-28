# AtmosLink — SJ01 FF64 Structured Serial-Frame Corruption
## 27 September 2026

### 1. Scope

This record documents a persistent serial-acquisition anomaly at SJ01.
Nominal meteorological emissions are sometimes received by the Linux logger
as a block beginning with exactly 64 bytes of `0xFF`, followed by a partial
ASCII CSV tail.

This incident is separate from the SJ01 synchronization incident documented
in `INCIDENT_2026-09-27_SJ01_SYNC_RECURRENCE_AND_PERMANENT_MITIGATION.md`.
The synchronization incident concerned transfer from SJ01 to the controller;
this incident concerns acquisition integrity between the ESP32 weather
station and the SJ01 Raspberry Pi.

**Status: ROOT CAUSE OPEN — anomaly characterized; production unchanged.**

### 2. Acquisition path

Relevant path:

`ESP32 UART TX -> CP2102 USB-UART -> USB/cp210x -> /dev/ttyUSB1 -> pyserial -> logger`

Verified mapping:
- Main SJ01 weather interface: Silicon Labs CP2102, VID:PID `10c4:ea60`, `/dev/ttyUSB1`, 115200 baud.
- Wind/RS-485 interface: CH340, VID:PID `1a86:7523`, `/dev/ttyUSB0`, 9600 baud.
### 3. Nominal frame contract

The weather pipeline expects 17 comma-separated fields:
`t_s`, temperature avg/min/max, humidity avg/min/max, pressure avg,
dew point, vapor pressure, rain 1 min, rain 1 h, accumulated rain,
rain pulse delta, rain pulse total, BME validity, rain validity.

Valid production frames conform to the 17-field contract and terminate
with CRLF.

### 4. FF64 structure

Observed malformed frames have a stable signature:
- exactly 64 leading bytes equal to `0xFF`;
- a partial ASCII CSV tail;
- CRLF terminator preserved;
- meteorologically plausible tail values continuous with neighboring valid observations;
- fewer than the required 17 fields.

In a 12-hour journal analysis:
- FF64 frames: 248;
- valid frames: 472;
- total classified emissions: 720;
- FF64 fraction: 34.44%;
- leading FF count: exactly 64 in 248/248 malformed frames.

Malformed total lengths were 118, 121 or 122 bytes.
Post-FF tail lengths were 54, 57 or 58 bytes.
Predominant valid-frame lengths were 86, 89 and 90 bytes.
The modal relationships `86-54=32`, `89-57=32`, and `90-58=32`
are a structural clue, not proof of a mechanism.
### 5. Temporal-slot validation

A six-hour minute-level correlation produced:
- valid database observations: 238;
- FF64 warning events: 122;
- minutes containing both: 0;
- FF64-only minutes: 122;
- valid-only minutes: 238.

The counts sum to 360 nominal minute slots.

A separate `VALID -> FF -> VALID` test identified 121 isolated FF64 events.
For all 121 triplets, the surrounding valid frames differed by exactly
120 seconds in ESP32 `t_s`.

Therefore an isolated FF64 event occupies the nominal 60-second slot between
two valid observations. The affected minute is not simply absent from the
serial stream: an emission is received for that slot, but the frame is
malformed and rejected.

### 6. Daily persistence

Complete days analyzed:
- 2026-09-22: 950 valid, 490 FF64, 1440 total, 34.03%.
- 2026-09-23: 969 valid, 471 FF64, 1440 total, 32.71%.
- 2026-09-24: 965 valid, 475 FF64, 1440 total, 32.99%.
- 2026-09-25: 929 valid, 511 FF64, 1440 total, 35.49%.
- 2026-09-26: 948 valid, 492 FF64, 1440 total, 34.17%.

The first FF64 visible in the currently available journal is
`2026-09-21T19:07:10-05:00`. This must not be interpreted as the true
start time of the defect because earlier journal evidence is unavailable.
### 7. Logger behavior and scientific-data policy

The production logger uses `ser.readline()` followed by strict UTF-8
decoding. FF64 frames raise `UnicodeDecodeError` and are discarded before
parsing or database insertion. The logger also requires exactly 17 weather
fields before accepting a candidate observation.

Scientific treatment:
- valid 17-field frame -> accepted observation;
- FF64 malformed frame -> acquisition-QC failure / missing observation.

FF64 tails must not be reconstructed, stripped and inserted, or otherwise
promoted into the primary scientific dataset.

### 8. Historical logger evidence

Commit `588d5c6 — Improve ESP32 serial handling and validate 17-field weather frames`
changed decoding from:

`raw.decode("utf-8", errors="ignore")`

to strict decoding with explicit rejection on `UnicodeDecodeError`.
It also introduced `EXPECTED_WEATHER_FIELDS = 17`, structural validation,
ESP32 boot/control filtering, explicit serial settings, DTR/RTS deassertion
and input/output buffer reset at port opening.

Before this commit, invalid bytes such as `0xFF` could be silently removed.
Historical absence of explicit FF64 warnings before strict decoding is
therefore not evidence that the underlying anomaly did not exist.
Commit `4811300 — Integrate production SJ01 multisensor station` established:
- ESP32 CP2102 by-id device at 115200 baud;
- wind CH340 by-id device at 9600 baud;
- declared firmware metadata `3.5.2`, build `20260804`,
  device `ESP32-SJ01-001`.

That metadata identifies the intended production firmware, but does not by
itself prove the exact binary currently flashed. Exact firmware provenance
remains unresolved.

### 9. Linux/USB observations

Inspection of kernel logs found no reported USB disconnect/reconnect,
CP2102 reset, ttyUSB reset, driver-reported overrun, overflow, or gross
enumeration failure in the inspected window.

This does not exclude byte corruption; it only means no gross USB/driver
fault was reported by the kernel.

### 10. Components not identified as the source

Current evidence does not support SQLite, central synchronization, parser
field mapping, database insertion, master-data builder, dashboard, or the
UTF-8 decoder itself as generators of the FF64 block.

The malformed bytes are already present in the raw serial data returned by
`ser.readline()`. The parser and strict decoder are acting as QC barriers.
### 11. Root-cause boundary

The unresolved causal boundary is upstream of Python parsing and SQLite:

`ESP32 / UART TX -> CP2102 -> USB/cp210x/Linux -> pyserial raw read`

Evidence does not yet distinguish among ESP32 firmware/runtime output,
UART transmission, electrical/physical UART path, CP2102 behavior,
USB transport, or lower-level host serial reception.

### 12. Next discriminating experiment

Preferred experiment: simultaneously observe ESP32 TX with a passive
RX-only receiver or logic analyzer while leaving the production CP2102 path
connected.

Interpretation:
- FF64 present directly on ESP32 TX -> fault boundary moves toward
  ESP32 firmware/runtime/UART.
- ESP32 TX clean while CP2102/Linux records FF64 -> fault boundary moves
  toward CP2102/USB/host reception.

### 13. Operational constraints

Until that experiment:
- do not reconstruct FF64 observations;
- do not insert partial tails into SQLite;
- do not relax the 17-field contract or strict UTF-8 rejection;
- do not restart or reflash solely to suppress the symptom;
- preserve raw FF64 evidence in logs.

### 14. Current state

SJ01 logger remains operational and valid observations continue.
The FF64 signature is persistent and reproducible, with isolated-slot
placement verified in 121/121 triplets and approximately 33–35% FF64 on
complete analyzed days. Database corruption was not observed. Central
synchronization was resolved separately. FF64 root cause remains open.


---

### 15. Missingness Bias Audit v1

A reproducible read-only audit was executed with:

`scripts/audit_sj01_ff64_missingness_v1.py`

Outputs are stored in:

`Results/sj01_ff64_missingness_v1/`

The audit classified 8,643 exclusive minute events from the retained
journal window, with 5,709 valid observations and 2,934 FF64 events
(33.95%). No ambiguous minutes were found.

For the five complete days 22–26 September, the FF64 fraction remained
between 32.71% and 35.49%. Association with complete day was weak
(Cramer's V = 0.0208; chi-square p = 0.538), and association with
hour-of-day was also weak (Cramer's V = 0.0367; p = 0.976).

The retained journal window includes three RF scenarios:
`6475/20`, `6655/40`, and `6475/40`. Their FF64 rates differed by
only 1.53 percentage points overall; the scenario association was weak
(Cramer's V = 0.0114; p = 0.570).

Matched independent covariates included CU01 local weather, NASA POWER
conditions for `SM_SAN_JOSE`, and RF telemetry. Across the tested
continuous covariates, the maximum absolute standardized mean difference
between valid and FF64 minutes was 0.0304.

Within this observable window there is therefore no evidence of a strong
differential FF64 association with day, hour, the three represented RF
scenarios, observed CU01 weather, available NASA POWER SJ01-area
conditions, or matched RF metrics.

This result supports treating FF64 primarily as loss of eligible SJ01
observations rather than demonstrated weather- or RF-selective missingness
in the observed window. It does not prove Missing Completely At Random,
does not cover unrepresented 3x2 scenarios, and does not resolve the
physical root cause. FF64 observations remain ineligible for scientific
reconstruction.


---

### 16. CP2102 USB packet-size observation

A read-only USB descriptor inspection on SJ01 identified the production
CP2102 bulk endpoints as:

- endpoint `0x81`: EP 1 IN;
- endpoint `0x01`: EP 1 OUT;
- `wMaxPacketSize = 0x0040 = 64 bytes` for both endpoints.

The exact FF64 prefix length therefore equals the CP2102 USB bulk endpoint
maximum packet size.

This alignment is technically significant as a localization clue, but is
not causal proof. A 64-byte FF block could still be generated upstream or
through another mechanism. The observation strengthens the value of the
planned passive ESP32-TX capture because that experiment samples the signal
before the CP2102/USB packetization boundary.
