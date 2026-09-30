# CU01 post-optimization runtime profile — 2026-09-29

## Scope

A five-minute observational profile was run after the multistation cadence, dashboard, enrichment/QC and scientific-campaign export optimizations.

Profile window:

- first sample: 2026-09-29 23:48:15 -05:00
- last sample: 2026-09-29 23:53:11 -05:00
- samples: 60
- sampling interval: approximately 5 s
- duration: 301.35 s

No production service was restarted or reconfigured during this profile.

## Whole-machine CPU and load

The host has four logical CPUs.

Across the five-minute window:

- total system CPU busy: mean 14.38%, median 10.09%, maximum 38.81%;
- 1-minute load average: mean 0.76, maximum 1.39.

Therefore CU01 was not CPU-saturated during the observed window. Even the maximum 1-minute load remained well below the four available logical CPUs.

The median machine utilization is now modest, but periodic scientific/derived-data jobs still create short CPU bursts.

## Memory and swap

Available memory during the profile:

- mean: 6,363 MiB;
- median: 6,569 MiB;
- minimum: 5,126 MiB.

Swap usage remained exactly 496.1 MiB throughout all 60 samples. There was no observed swap growth during the profile.

This indicates that the current workload has substantial RAM headroom. Existing swap pages are historical/stable rather than evidence of active memory pressure during this five-minute window.

## Persistent AtmosLink service load

Mean CPU utilization is expressed as a percentage of one logical CPU core.

### Scheduler cgroup

- mean CPU: 14.19%;
- median CPU: 0.05%;
- maximum CPU: 100.33%;
- mean memory.current: 592 MiB;
- maximum memory.current: 1,132 MiB;
- mean write rate: 1.14 MiB/s;
- peak sampled write rate: 27.15 MiB/s.

The very low median and high maximum confirm a bursty workload rather than a continuously busy scheduler.

After the profile, the scheduler cgroup contained only about 8 MiB anonymous memory but about 539 MiB file cache. Therefore the persistent cgroup `memory.current` value must not be interpreted as equivalent to live Python RSS.

### Dashboard

- mean CPU: 3.82% of one core;
- median CPU: 0.04%;
- maximum CPU: 46.09%;
- memory: stable at about 169 MiB;
- swap: 0.

The dashboard remains materially improved compared with its pre-index state and is no longer a dominant memory consumer.

### Weather logger

- mean CPU: 0.29%;
- memory: about 20 MiB;
- swap: stable at about 14.7 MiB.

The acquisition logger is not a current CPU bottleneck.

### Radio-config collector and event monitor

Both persistent services were negligible in CPU consumption during the profile. The radio-config collector generated periodic disk-write bursts but low CPU.

## Largest observed burst: multistation full rebuild

During the profile, an `atmoslink-remote-sync.service` invocation transferred one new SJ01 row and then became eligible for a full multistation rebuild.

That invocation consumed:

- 28.048 s of CPU time;
- approximately one full CPU core while the builder was active;
- observed builder RSS around 1.27 GiB;
- resulting master size: 170,373 rows.

The adjacent remote-sync cycles, which skipped the fresh derived master, consumed only about 1.3 s CPU each.

This confirms that throttling eliminated repeated two-minute full rebuilds, but the remaining full rebuild itself is now the largest AtmosLink burst.

## Scheduler work observed in the same window

A natural scheduler cycle included:

- `enrich_master_dataset`: 25.088 s;
- `master_quality_check`: 2.767 s;
- `build_station_observations`: 6.977 s;
- `scientific_comparison`: 4.222 s;
- `health_monitor`: about 1.3 s;
- other five-minute scientific/QC tasks: sub-second to low-single-digit duration.

The enrichment task remained much faster than its historical scalar implementation, although this particular cycle was slower than the earlier 15.2 s post-optimization run. Its runtime is now dominated by wide SQLite/CSV I/O rather than the removed row-by-row metric calculation.

The scheduler registry still reports the old 55.087 s value for `scientific_campaign_export` because its next hourly scheduler invocation has not yet occurred since the exporter optimization. Separate verified post-optimization full executions completed in 22.35–24.12 s.

## Secondary non-scheduler spike

At approximately 23:50:05, system CPU busy reached 36.41% while the scheduler and dashboard cgroups were nearly idle.

This coincided with the five-minute legacy/current ePMP monitoring cron pipeline starting at 23:50:01:

- `alert_epmp.sh`
- `auto_csv_pipeline.sh`

The timing is consistent with that pipeline contributing to the burst, but this five-minute profile did not attribute per-process CPU inside the cron job, so it is recorded as a correlation rather than a definitive process-level measurement.

The long-running `capture_agg_ap.sh` remains active and is not classified as obsolete because it still belongs to the current RF-monitoring path.

## Interpretation

The system is currently healthy and has considerable CPU/RAM headroom. The optimization work removed sustained excess load; the remaining load is predominantly periodic.

The most important remaining AtmosLink hotspot is no longer the dashboard, QC or hourly campaign exporter. It is the complete `build_multistation_master` reconstruction itself.

The next high-value optimization is therefore to make the multistation builder incremental or append/upsert-oriented, so that a normal 1–2-row SJ01 synchronization does not require rebuilding approximately 170k derived rows and rewriting the full multistation CSV.

Any such change must preserve:

- existing CU01/SJ01 scientific mapping;
- exact derived-table schema;
- atmospheric association semantics;
- existing indexes;
- stable table identity/atomic publication guarantees;
- raw source data;
- reproducible equivalence with the current full builder.

## Raw evidence

The 60-sample profile is stored in:

`provenance/performance_profile_CU01_5min_20260929.csv`

The measurement was read-only with respect to scientific source data.

## Measurement caveat

The raw profile contains exploratory `project_cpu_pct` and `project_rss_mib` aggregate columns built from a changing set of matching PIDs. Because processes start and exit during a sample interval, the aggregate CPU-delta field can become negative and is not used in the conclusions above. Whole-system `/proc/stat`, systemd cgroup deltas and explicit service logs are the authoritative CPU evidence for this audit.
