# CU01 cron duplicate polling incident — 2026-09-29

## Finding

The CU01 user crontab contained two identical active entries for `poll_epmp.sh` and two identical active entries for `poll_epmp_agg.sh`, all scheduled every minute.

Before correction, the cron journal independently confirmed two launches of each script at the same minute.

## Data effect

For `epmp_local_2026-09-29.csv`, 1,838 data rows were examined at the audit point. There were zero duplicate timestamp/role groups and zero exact duplicate rows. `poll_epmp.sh` contains a non-blocking `flock`, so the duplicate cron launch was suppressed at the writer level.

For `epmp_agg_2026-09-29.csv`, 3,670 data rows were examined. There were 1,824 timestamp/role groups with multiplicity two and 1,824 exact excess duplicate rows. `poll_epmp_agg.sh` has no equivalent lock, so both cron invocations wrote the same AP and SM records.

No repository consumer reference to `epmp_local_*.csv` or `epmp_agg_*.csv` was found during this audit. These are legacy ePMP outputs, separate from the current AtmosLink SQLite telemetry path.

## Corrective action

The original crontab was preserved in:

`provenance/crontab_CU01_before_dedup_20260929.txt`

A validated replacement was generated with only the second occurrence of each identical polling line removed:

`provenance/crontab_CU01_after_dedup_20260929.txt`

No schedule, command, comment, or unrelated cron entry was changed.

Crontab SHA-256 before:
`b9c086dc8416774af7f0dbab83ee03c23a5e30443b4b5b1767e91d254965222f`

Crontab SHA-256 after:
`26bfffea59fd2ea1c6509c1fce67737fe9e79ef0b11f15faddee736360b9991f`

## Runtime verification

After installation, the 15:18 and 15:19 local cron cycles each launched exactly one `poll_epmp.sh` and one `poll_epmp_agg.sh`.

The aggregate CSV then contained exactly one AP row and one SM row for 15:18 and again for 15:19. The immediately preceding 15:17 minute still contains the historical duplicate pair because it was written before the corrected crontab took effect.

The historical raw CSV was not rewritten or deduplicated. Existing duplicate records remain preserved as acquired data; any future cleaned derivative must be generated separately and documented.
