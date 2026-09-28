# Protocol — SJ01 FF64 Causal Isolation
## Passive ESP32 TX observation before intervention

### Objective

Localize the FF64 corruption boundary without altering the production
weather logger, SQLite database, radio configuration, firmware, or
scientific campaign.

### Current evidence

The malformed FF64 bytes are already present in the raw serial data returned
to the production logger by `ser.readline()`. Downstream parsing and SQLite
are therefore not candidate generators.

The unresolved boundary is:

`ESP32/UART TX -> CP2102 -> USB/cp210x/Linux -> pyserial raw read`

### Preferred test

Observe the ESP32 serial TX signal simultaneously with a second passive
RX-only receiver while the existing CP2102 production path continues
operating normally.

The passive receiver must observe the electrical TX signal before the
production CP2102/USB path.

### Hardware wiring

Use either:
- a 3.3 V logic-level USB-UART adapter with RX-only connection; or
- a logic analyzer capable of decoding 115200 baud UART.

Connections:
- ESP32 TX/TX0 -> passive adapter RX or analyzer channel;
- ESP32 GND -> passive adapter/analyzer GND.

Do **not** connect:
- passive adapter TX to the ESP32;
- VCC/5 V from the passive adapter to the ESP32;
- any second supply to the production board.

The exact ESP32 TX pin must be identified from the physical board
silkscreen/schematic. Do not assume a GPIO number solely from generic ESP32
documentation.

Serial parameters:
- 115200 baud;
- 8 data bits;
- no parity;
- 1 stop bit;
- no flow control.

### Safety gate before capture

On SJ01, after plugging in the second adapter:

```bash
ls -l /dev/serial/by-id/
udevadm info -q property -n /dev/ttyUSB2 | egrep 'ID_VENDOR|ID_MODEL|ID_SERIAL|ID_USB_DRIVER'
```

Use the actual newly created device path. The production weather CP2102 is
currently `/dev/ttyUSB1`; the wind CH340 is `/dev/ttyUSB0`.

The capture script intentionally refuses those known production paths.

### Capture

From the AtmosLink repository on SJ01:

```bash
python3 scripts/capture_sj01_passive_uart.py \
  --port /dev/serial/by-id/<NEW_PASSIVE_ADAPTER> \
  --duration-minutes 20
```

Twenty minutes should normally contain enough FF64 opportunities given the
currently observed approximately one-third FF64 rate. If no decisive FF64
coincidence appears, extend to 60 minutes.

The script writes a JSONL record for every passive UART frame and classifies
each frame as:
- `VALID17`;
- `FF64`;
- `OTHER`.

It does not access the production serial device or SQLite.

### Compare with production logger

After capture:

```bash
python3 scripts/compare_sj01_passive_vs_logger.py \
  Results/sj01_ff64_passive_capture/passive_uart_<TIMESTAMP>.jsonl
```

The comparison aligns passive and production logger observations by minute.

### Decision rule

Case A:

`passive TX = FF64` and `production logger = FF64`

Interpretation:
FF64 is already present at the ESP32 TX observation point. The causal
boundary moves upstream toward ESP32 firmware/runtime/UART behavior.

Case B:

`passive TX = VALID17` and `production logger = FF64`

Interpretation:
the ESP32 TX signal is clean while the production path receives FF64.
The causal boundary moves downstream toward CP2102, USB transport, Linux
serial reception, or the physical connection to that path.

Case C:

mixed A and B evidence

Interpretation:
do not declare a single root cause. Repeat with timing verification and
additional physical instrumentation.

Case D:

no FF64 coincidence captured

Interpretation:
increase capture duration; no causal conclusion.

### Scientific handling

Regardless of causal outcome:
- do not reconstruct historical FF64 observations;
- do not insert partial tails into SQLite;
- preserve FF64 slots as acquisition-QC failures;
- retain raw capture artifacts and comparison output;
- repeat the Missingness Bias Audit after any corrective intervention.

### Intervention rule

No firmware reflash, USB-adapter swap, cable replacement, service restart,
or parser change should occur before the passive comparison produces a
causal direction, unless required for site safety or loss of service.

### Success criterion

The experiment is successful when at least one production FF64 minute has
a simultaneous passive-TX classification sufficient to distinguish Case A
from Case B, preferably with multiple repeated coincidences.
