# CU01 scientific campaign export optimization — 2026-09-29

## Objective

Reduce the hourly CPU, memory and disk-processing cost of `scientific_campaign_export` without changing campaign classification rules, field/laboratory boundaries, RF-weather matching tolerance, public table schemas, CSV semantics or downstream scientific products.

## Baseline

The production scheduler run immediately before this optimization started at 23:18:39 local time and completed at 23:19:34:

- elapsed scheduler duration: 55.087 s;
- failures: 0.

A read-only stage profile of the historical implementation showed:

- full multistation master loaded into pandas: 170,324 rows, about 371 MiB;
- classified in-memory copy: about 440 MiB;
- RF telemetry in memory: about 88 MiB;
- integrated RF-weather product in memory: about 104 MiB;
- read/classify/integrate profile peak RSS: 1,187,796 KiB, before the SQLite and CSV publication steps.

The two published CSV files together are roughly 258 MB, so materializing extra wide pandas copies every hour was unnecessary overhead.

## Optimization

Three changes were applied.

### 1. Campaign classification moved into SQLite

`scientific_campaign_observations` is a deterministic classification of `master_observations_multistation`.

The optimized exporter performs the classification directly with one SQL `INSERT ... SELECT` transaction while preserving the stable destination-table object. This eliminates the Python round trip of approximately 170k rows x 82 source columns and the additional classified pandas copy.

The classification rules are unchanged:

- CU01 before 2026-08-31 16:00 -05:00: `FIELD_BASELINE_CU01`;
- SJ01 before that cutoff: `LABORATORY_TEST`;
- CU01/SJ01 at or after the cutoff: `FIELD_OPERATION`;
- only field-operation rows receive `field_analysis_valid=1`.

A pre-deployment equivalence test over all rows present in the previous campaign table found zero classification mismatches.

### 2. RF-weather integration reads only required weather data

The historical exporter loaded the complete multistation table before selecting CU01 and SJ01 weather fields.

The optimized path reads only the weather columns used by the RF integration and only from two minutes before the field-campaign cutoff onward. The two-minute lead preserves the existing nearest-match tolerance.

Benchmark:

- historical full master pandas load: about 371 MiB;
- narrowed weather input: 67,185 rows, about 58 MiB.

The raw RF telemetry remains wide because its JSON/raw fields are part of the established integrated-product schema.

A pre-deployment comparison over 7,916 common integrated RF records found the same historical result for all established rows except one most-recent row whose weather fields had been filled in the current master after the previous hourly export. That difference was source freshness, not a matching-rule difference.

### 3. CSV publication is streamed from stable SQLite tables

The previous implementation built additional pandas-backed CSV writes.

The optimized exporter streams SQLite rows directly to an atomic temporary CSV and renames the file only after successful completion.

Before deployment, the streaming writer was applied to both existing stable products. It produced byte-identical files:

- observations CSV SHA-256: `8f83a36eb08e8addd27895aebc67e80aa369f6b7c08d54dbc4a1c27be72f606d`;
- integrated CSV SHA-256: `78ebd666ab82a70f5a7196e3d6005e1339fb7dc50c912562ebe971a7ebb528e9`.

Thus the writer optimization did not alter CSV serialization for the tested snapshot.

## Observed production-equivalent result

A complete manual production execution of the optimized command at 23:34:56 local time completed successfully at 23:35:20:

- elapsed: 24.12 s;
- user CPU: 18.07 s;
- system CPU: 2.84 s;
- peak RSS: 392,472 KiB;
- classified rows: 170,342;
- integrated 6 GHz rows: 7,920;
- field rows: 67,190;
- SJ01 laboratory rows: 20,375;
- both weather stations matched: 7,733;
- UL link-rate available: 0.

Relative to the immediately preceding scheduler run, elapsed time fell from 55.087 s to 24.12 s:

- speedup: about 2.28x;
- elapsed reduction: about 56.2%.

The optimized full run also used substantially less memory than the historical read/classify/integrate stage alone: approximately 383 MiB peak versus approximately 1.13 GiB in the historical read-only stage profile.

## Database and downstream verification

After publication:

- SQLite `PRAGMA quick_check`: `ok`;
- `scientific_campaign_observations`: 170,342 rows / 88 columns;
- `scientific_campaign_6g_integrated`: 7,920 rows / 145 columns;
- dependent view `scientific_campaign_6g_analysis_qc`: valid, 7,920 rows;
- dashboard health: `healthy`;
- operational state: `ONLINE`.

The stable table names and schemas were preserved. No source observation, RF telemetry row, weather row or historical raw dataset was deleted by the optimization.

The next normal scheduler invocation will import the optimized module automatically; no scheduler or dashboard restart is required.

## Provenance

Pre-change source SHA-256:

`6baf3977f2039da8eff0504131bd3b9aa8522b8b9419d92a59132c8e848fe178`

Post-change source SHA-256:

`ea39052a83561ea13ecdbd1a3c27ef5658d3f6f1dc50e5dc0cc90b623fee399a`

Protected pre-change source and pre-change output hashes are stored outside Git under:

`/home/carlos/.config/atmoslink/provenance_backups/20260929_campaign_export_optimization/`
