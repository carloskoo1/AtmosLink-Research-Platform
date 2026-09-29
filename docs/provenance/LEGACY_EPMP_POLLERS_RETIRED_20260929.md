# Legacy ePMP pollers retired — 2026-09-29

## Decision

The legacy CU01 cron pollers `poll_epmp.sh` and `poll_epmp_agg.sh` no longer contribute useful data to the current AtmosLink workflow and were retired from active cron execution.

The scripts and historical raw CSV files were not deleted. They remain preserved for provenance and reproducibility.

## Change

Before retirement, each poller had one active every-minute cron entry. The validated replacement crontab comments both entries as retired and leaves all unrelated cron jobs unchanged.

Crontab SHA-256 before retirement:

`26bfffea59fd2ea1c6509c1fce67737fe9e79ef0b11f15faddee736360b9991f`

Crontab SHA-256 after retirement:

`93b60b1e690bed265fa684259f4ac6f37b0b84641999001cd6ffa7d755e96b7e`

Snapshots:
- `provenance/crontab_CU01_before_legacy_pollers_retired_20260929.txt`
- `provenance/crontab_CU01_after_legacy_pollers_retired_20260929.txt`

## Verification

After installation there were no active cron lines for either legacy poller. The 15:29 local cron cycle produced no `poll_epmp.sh` or `poll_epmp_agg.sh` invocation. The 15:28 invocation visible in the journal occurred before retirement took effect.

The unrelated five-minute jobs `alert_epmp.sh` and `auto_csv_pipeline.sh` were left unchanged.

## Data preservation

No historical `epmp_local_*.csv` or `epmp_agg_*.csv` file was altered, deleted, or deduplicated. The previously identified duplicate aggregate records remain preserved in the raw legacy dataset.
