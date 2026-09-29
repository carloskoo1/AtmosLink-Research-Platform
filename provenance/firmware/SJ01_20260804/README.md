# SJ01 firmware provenance — build 20260804

This directory records the provenance of the recovered SJ01 production firmware build.

- Firmware identity: WeatherStation v3.5.2 / build 20260804 / station SJ01.
- Historical source SHA-256: CA2481711145E0E7042DA381DC4B69FDBD0D47B76545648FA6EEB8F90D6C4533.
- Historical application binary SHA-256: 7887428D764C22E87D9B961B156A0274ABD2C5B481D3F0D348BE716D5E482901.
- Historical merged 4 MiB image SHA-256: CF0C13EB1DD178D1C31659DFE311AE56371DEEB82CB7BF7AA8E17E42979CD0E1.
- Arduino-ESP32 core recorded in historical build.options.json: 3.3.11.
- Historical flash offsets: bootloader 0x1000; partitions 0x8000; boot_app0 0xe000; application 0x10000.
- Flash arguments recorded: DIO, 80 MHz, 4 MB.
- The historical .ino.bin and .ino_flashed.bin were verified byte-identical.

Large binary/ELF/MAP artifacts are intentionally not stored in normal Git history. Their hashes are fixed in SHA256SUMS.txt; the preserved archive must be stored as an immutable external release/archive artifact.
