# CU01 dashboard query optimization — 2026-09-29

## Objective

Reduce CPU, latency and memory pressure in the AtmosLink dashboard without changing scientific values, raw observations, synchronization cadence or API response semantics.

The audit identified two hot paths on `master_observations_multistation`:

- station latest/history queries scanned the complete derived table because it had no indexes;
- the SJ01 scientific-hourly endpoint executed `SELECT *` across all valid SJ01 history, loaded the full wide table into pandas, and only afterwards retained the field-deployment interval and four scientific columns.

At the time of optimization the derived table contained about 170k rows and approximately 82 columns.

## Persistent indexes

Two partial indexes are now created by `build_multistation_master.py` every time the atomic output table is replaced:

- `idx_mom_station_minute_valid(station_id, bucket_minute DESC)`
- `idx_mom_station_hour_minute_valid(station_id, bucket_hour, bucket_minute)`

Both are restricted to rows where `local_temp_avg_c IS NOT NULL`, matching the dashboard predicates.

The indexes are created only after the previous atomic table has been dropped, because SQLite index names are database-global and would otherwise remain attached to the renamed previous table.

A natural scheduler rebuild at 18:35:42–18:36:12 created both indexes successfully on 169,847 derived rows. The rebuild duration remained about 29.4 s, comparable with pre-index rebuilds.

SQLite query plans then changed from full table scans plus temporary ordering to indexed searches.

Direct SQL timing after the indexed rebuild:

- SJ01 latest row: 0.0002 s.
- SJ01 history, 120 rows: 0.0017 s.
- SJ01 scientific-hourly source query, 27,438 rows / four columns: 0.0551 s.

## Scientific-hourly query narrowing

For SJ01 the endpoint now selects only:

- `bucket_hour`;
- the observed column for the requested variable;
- the ERA5 column for that variable;
- the NASA POWER column for that variable.

It also applies the field-deployment start `2026-08-31T21:00:00Z` in SQL instead of loading earlier laboratory history and filtering it only in pandas.

For the audited snapshot this reduced source rows loaded by the endpoint from 47,810 to about 27,435 while reducing the selected width from the full multistation schema to four columns.

The endpoint preserves the previous behavior for scientific columns that are not present in the physical table: missing mapped columns are projected as SQL `NULL` instead of causing an error.

## Scientific equivalence

A same-database old-query/new-query comparison was run for all six supported scientific variables:

- temperature
- humidity
- pressure
- dew point
- precipitation
- wind

For every variable, hourly bucket count, hour labels and all observed/ERA5/NASA numerical outputs were exactly equivalent under the existing aggregation rules. Equivalence failures: 0.

This check also covered current schema gaps such as station-adjusted pressure columns and the mapped local precipitation-hour column by preserving the historical null behavior.

## API latency

Before optimization, measured local endpoint latency was approximately:

- SJ01 scientific hourly temperature: 2.11 s.
- SJ01 history limit 120: 0.43 s.
- SJ01 latest: 0.24 s.

After the indexed rebuild and dashboard code reload, three repeated measurements were approximately:

- SJ01 scientific hourly temperature: 0.305–0.322 s.
- SJ01 history limit 120: 0.065–0.069 s.
- SJ01 latest: 0.055–0.060 s.

This corresponds to roughly 6.8x, 6.4x and 4.3x lower latency respectively for the tested paths.

All six scientific-hourly variables returned HTTP 200 after the change.

## Dashboard memory

Before the dashboard reload, the long-running Gunicorn cgroup was using about 1.16 GB current memory and about 250 MiB swap.

After the clean reload and an explicit stress pass of 66 representative dashboard requests, the cgroup reported about 182 MiB current memory, 183 MiB peak and zero swap.

The restart itself released accumulated Python heap state, so the entire memory reduction must not be attributed solely to the query rewrite. However, the new endpoint materially reduces each SJ01 scientific-hourly request from a wide 47.8k-row pandas load to a four-column field-period dataset, which removes the largest identified temporary allocation pattern.

No Gunicorn worker-count reduction was made because the optimized workload is currently operating with substantially lower memory pressure.

## Operational verification

The dashboard service restarted cleanly under its existing systemd `Restart=always` policy and returned HTTP 200 health.

The indexed table survived a natural multistation rebuild because index creation is now part of the builder itself.

No raw scientific record, historical CSV or source SQLite observation was deleted or altered. The indexes apply only to the derived multistation table and the endpoint change is read-only.

## Provenance

Before hashes:

- `weather_station/dashboard/multistation_api.py`: `a5f3de8b6e7780bbf581c449749155e0d794657a4fc39cfffe40592c3cc3c4da`
- `weather_station/sync/build_multistation_master.py`: `8697ae5f46f9c76d893725671926698f4c5c749f17933aac9457a6dd2a09ca15`

After hashes:

- `weather_station/dashboard/multistation_api.py`: `9025a6249a4d58c03140fcba676e56f0a8963360dfc1e7829811023df14d5910`
- `weather_station/sync/build_multistation_master.py`: `e872a4327d2ea4a09d354f91db0c9a58902e37cc0df36eb376c125a7641ee538`
