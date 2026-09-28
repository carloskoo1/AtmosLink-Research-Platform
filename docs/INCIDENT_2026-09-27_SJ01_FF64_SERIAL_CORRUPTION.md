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


---

### 17. Two-phase periodicity discovered remotely

A follow-up read-only analysis of 8,643 classified minute slots revealed a
strong deterministic temporal structure that was not captured by the
hour-of-day aggregation used in Missingness Bias Audit v1.

Results:

- even local minutes: 0 FF64 of 4,322 slots (0.00%);
- odd local minutes: 2,934 FF64 of 4,321 slots (67.90%);
- every FF64 run length observed: exactly 1 minute;
- FF64 -> FF64 transitions: 0;
- lag-1 FF64 autocorrelation: approximately -0.514;
- lag-2 FF64 autocorrelation: approximately +0.508.

Using the first valid observation as a slot-phase anchor and a nominal
60-second emission interval, the two alternating 120-second phases contain:

- phase A: 4,322 valid, 0 FF64;
- phase B: 1,387 valid, 2,934 FF64.

Thus FF64 is confined to one of the two alternating emission phases in the
retained window. Missingness must therefore not be described as MCAR or as
unstructured random loss.

This does not contradict the v1 result that no strong association was found
with day, hour-of-day, represented RF scenario, CU01 weather, available NASA
POWER covariates, or matched RF metrics. It refines that interpretation:
the loss is strongly acquisition-phase selective, while no weather- or
RF-selective mechanism has been demonstrated.

Hourly coverage remains dense despite the phase-selective loss. Across 143
complete analyzed hours, valid minute observations per hour were:

- minimum: 33;
- median: 40;
- maximum: 49.

No complete analyzed hour contained fewer than 30 valid SJ01 observations.

The only local systemd timer with a nominal two-minute cadence is
`atmoslink-weather-watchdog-sj01.timer`. Its execution phase drifts across
even and odd wall-clock minutes. Direct comparison over the retained journal
gave FF64 rates of approximately 34.30% in minutes without a watchdog
execution and 33.55% in minutes with one; chi-square p approximately 0.477.
The watchdog is therefore not supported as the explanation for the
alternating FF64 phase.

The deterministic two-phase structure materially strengthens the hypothesis
of a stateful acquisition/transport mechanism (for example a buffer/bank
cycle), but does not identify a specific component. Physical root cause
remains open.


---

### 18. A/B frame-forensics refinement

A deeper read-only reconstruction of the complete retained logger journal
was performed after the two-phase periodicity finding.

The analyzed journal contained 8,680 classified emissions:

- 5,733 valid 17-field frames;
- 2,947 FF64 frames.

Every one of the 2,947 FF64 frames had exactly 12 comma-separated ASCII
fields after the 64-byte FF prefix.

For all 2,947 FF64 tails:

- the third surviving token was pressure-like and within the expected
  high-Andean pressure range used by the station;
- the final BME/rain validity flags were structurally valid;
- rain pulse fields were structurally valid.

This confirms that the surviving ASCII region is a stable suffix of the
meteorological record, not arbitrary printable noise.

#### 18.1 Exact 32-byte prefix clue

Inspection of valid 17-field frames shows that byte offset 32 always lands
inside field 5 (`hum_min_pct`) over the retained window.

The observed FF64 tail begins in the same semantic position: a truncated
humidity-minimum token, followed by complete humidity-maximum, pressure,
dew-point, vapor-pressure, rainfall, pulse and validity fields.

For isolated FF64 frames, comparison of malformed total length with the
immediately adjacent valid frame gave:

- FF64 length minus previous valid length = +32 bytes in 2,853 of 2,947
  cases;
- FF64 length minus next valid length = +32 bytes in 2,824 of 2,947 cases.

The remaining differences were within a few bytes and are compatible with
normal changes in printed numeric field widths between adjacent minutes.

The observed structure is therefore strongly consistent with:

1. loss/replacement of approximately the first 32 bytes of the nominal
   ASCII weather record; and
2. insertion/presence of exactly 64 bytes of `0xFF`;
3. preservation of the record suffix and CRLF terminator.

This explains why malformed frames are approximately 32 bytes longer than
neighboring valid records despite containing a 64-byte FF prefix.

This is a structural reconstruction, not permission to reconstruct missing
scientific fields.

#### 18.2 Alternating phase remains exact

In sequential emission order:

- phase A: 4,340 valid, 0 FF64;
- phase B: 1,393 valid, 2,947 FF64.

No FF64-to-FF64 consecutive transition was observed.

For adjacent valid frames, ESP32 `t_s` increments were 60 s in 2,781
cases and 61 s in 4 cases.

For `VALID -> FF64 -> VALID` triplets, surrounding `t_s` increments were
120 s in 2,934 cases and 121 s in 13 cases.

The one-second deviations are consistent with long-run scheduling drift;
the two-phase emission structure remains intact.

#### 18.3 Central two-minute synchronization ruled out as phase driver

Because the controller remote-sync service also runs approximately every
two minutes, its timing was tested explicitly against FF64 occurrence.

Across the retained overlap:

- FF64 rate in minutes without a same-minute remote-sync start: 34.214%;
- FF64 rate in minutes with a same-minute remote-sync start: 33.670%;
- chi-square p = 0.609.

Remote-sync starts were nearly evenly distributed across wall-clock minute
parity:

- even minute starts: 2,160;
- odd minute starts: 2,126.

The emission-to-sync-start timing distribution was also essentially the
same for valid and FF64 observations.

The controller remote synchronization timer is therefore not supported as
the source of the deterministic A/B FF64 phase.

The local SJ01 freshness watchdog had previously also shown no significant
association with FF64 occurrence.

#### 18.4 Linux TTY error-marker mechanism not supported

Read-only inspection of the active `/dev/ttyUSB1` termios state showed:

- 115200 baud;
- 8 data bits;
- no parity;
- one stop bit;
- `PARMRK` disabled;
- `INPCK` disabled;
- software and hardware flow control disabled.

The Linux TTY is therefore not configured to synthesize parity/framing
error marker sequences into the received stream. This further narrows the
fault boundary toward the ESP32/UART/CP2102/USB transfer path rather than
a terminal-line-discipline transformation.

#### 18.5 Current causal interpretation

The strongest current signature is now:

`nominal prefix ~32 bytes -> replaced/absent + 64 FF bytes -> intact suffix`

combined with a deterministic two-phase emission dependency.

The exact 64-byte FF block remains notable because the production CP2102
USB bulk endpoint reports a 64-byte maximum packet size. However, packet
size equality alone is not causal proof, and the 32-byte nominal-prefix
displacement prevents a simple claim that a normal 64-byte USB packet is
merely being replaced one-for-one.

Root cause therefore remains open, but the search space is substantially
narrower than before.
