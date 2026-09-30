# CU01 enrichment and quality-check optimization — 2026-09-29

## Objective

Reduce the recurring CPU cost of `enrich_master_dataset` and `master_quality_check` without changing their five-minute scheduler cadence, scientific formulas, QC rules, raw observations or output semantics.

At the time of optimization, `master_observations` contained approximately 122k rows.

## Enrichment bottleneck

The previous enrichment implementation iterated over every row with pandas `iterrows()`, converted each Series to a dictionary and invoked `derive_weather_metrics()` row by row.

A cProfile run on 122,295 rows required 72.810 s under profiler instrumentation. The dominant cumulative costs were pandas row iteration and Series-to-dictionary conversion.

The scientific formulas themselves were preserved, but rewritten as vectorized pandas/NumPy operations for:

- saturation vapor pressure;
- actual vapor pressure;
- dew point;
- vapor pressure deficit;
- heat index;
- wind chill;
- moist-air density.

The vectorized mathematical stage required approximately 0.04 s on the audited dataset. The complete job still includes reading the wide master table, rewriting the enriched SQLite table and exporting the approximately 83 MB CSV.

A normal scheduler run immediately before deployment took 35.087 s. The first scheduler run with the optimized implementation completed in 15.213 s, with zero task failures. This is about a 56.6% reduction in elapsed runtime for that observed production pair.

## Scientific equivalence

The vectorized implementation was compared against the previously generated enrichment on the same rows.

Validation snapshot:
- 122,302 common rows in the initial controlled comparison.
- Seven derived variables checked.
- Total mismatches: 0.
- Maximum absolute numerical difference for every checked derived variable: 0.0.

A later production verification after the scheduled run compared 122,308 common rows and again found zero mismatches across all seven derived variables.

The source/fallback column semantics, validity rules and output rounding were retained.

## Quality-check bottleneck

The previous QC implementation loaded the full approximately 81-column enriched table and iterated through all rows with `iterrows()`, although the QC rules use only eight columns.

The optimized implementation:
- selects only the eight required columns from SQLite;
- evaluates row-level QC predicates as vectorized boolean masks;
- iterates only over rows that actually generate an issue;
- preserves the historical row/rule ordering;
- preserves the existing jump checks and message formatting.

In a controlled same-snapshot comparison:
- previous QC runtime: 16.080 s;
- optimized QC runtime: 2.692 s;
- issue count: 3,760 in both runs;
- old/new QC CSVs were byte-identical;
- SHA-256 of both controlled CSVs:
  `3e16937051670ff8cac2b765117b694f3265c961adddecd3fc879662a7db2976`.

The first scheduled optimized QC run completed in 2.439 s with zero task failures.

## Operational verification

The five-minute cadence of both scheduler tasks was intentionally left unchanged.

Observed scheduled run:
- `enrich_master_dataset`: 23:08:37–23:08:52, 15.213 s, completed, failures=0.
- `master_quality_check`: 23:08:52–23:08:55, 2.439 s, completed, failures=0.

At 23:10 local time:
- `master_observations`: 122,309 rows.
- `master_observations_enriched`: 122,308 rows.
- `master_quality_report`: 3,760 rows.
- latest raw master minute: 23:09 local.
- latest enriched minute: 23:08 local.
- dashboard health: `healthy`, operational state `ONLINE`.

The one-minute raw/enriched difference is normal between scheduler cycles.

No raw scientific table or historical source observation was deleted or rewritten by this optimization. Only derived computation and QC evaluation code changed.

## Provenance

Pre-change source hashes:

- `enrich_master_dataset.py`:
  `6c5775428d8cb66cf5868ef6996b7b8eb74955eb6783ee985c1f72cb6ebdfd90`
- `master_quality_check.py`:
  `f1719a35ebb7dddcca53e9de18184e882e66fc2285e403d85b534c3b6397e24f`

Post-change source hashes:

- `enrich_master_dataset.py`:
  `bdea1adb935cffb8cf12eaa9041820ecc5f0756df08924137bc34b7353daf1ea`
- `master_quality_check.py`:
  `9b3b930663070ad60402702fda1ea4a2dca453cd67e814b4ca1916ca88a0ad6e`

The pre-change source files are preserved outside Git in the protected AtmosLink provenance backup directory.

Post-change source SHA-256:

- `enrich_master_dataset.py`: `bdea1adb935cffb8cf12eaa9041820ecc5f0756df08924137bc34b7353daf1ea`
- `master_quality_check.py`: `9b3b930663070ad60402702fda1ea4a2dca453cd67e814b4ca1916ca88a0ad6e`
