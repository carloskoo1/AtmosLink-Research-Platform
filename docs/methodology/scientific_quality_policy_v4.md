# AtmosLink Scientific Quality Policy

## Scope

This document defines the operational scientific-quality criteria used by
AtmosLink V4 for comparison of local meteorological observations with
ERA5-Land and NASA POWER.

These thresholds are internal methodological rules of AtmosLink. They are
not intended to represent universal statistical standards.

---

## 1. Scientific validity of local observations

For SJ01 (Cerro San José), observations are considered valid field
observations from:

- 2026-08-31 16:00 local time (UTC-5)
- 2026-08-31 21:00 UTC

Observations prior to this boundary must not be included in scientific
field comparisons for SJ01.

CU01 uses its validated historical scientific dataset.

---

## 2. Strict temporal comparison

A Local–ERA5 or Local–NASA pair is considered comparable only when:

1. a valid local hourly observation exists;
2. the corresponding external reference value exists for the same hourly
   bucket;
3. neither value is interpolated or extrapolated.

AtmosLink does not create synthetic values to fill external-source gaps.

---

## 3. Sample maturity

Sample maturity is classified from the number of valid comparable pairs N.

| Comparable pairs N | AtmosLink classification |
|---:|---|
| N < 10 | INSUFICIENTE |
| 10 <= N < 30 | PRELIMINAR |
| 30 <= N < 100 | MODERADA |
| N >= 100 | ROBUSTA DESCRIPTIVAMENTE |

For N < 10, association/agreement indicators such as r² and NSE are not
presented as interpretable indicators.

This classification describes sample availability only. It does not prove
physical agreement between sources.

---

## 4. External-source coverage

Coverage is calculated as:

coverage (%) =
valid comparable pairs / valid local hourly observations × 100

| Coverage | AtmosLink classification |
|---:|---|
| < 10 % | LIMITADA |
| 10–49.9 % | PARCIAL |
| 50–89.9 % | SUSTANCIAL |
| >= 90 % | ALTA |

Coverage describes temporal coincidence availability. It does not measure
model accuracy.

---

## 5. Local temporal completeness

Expected hours are defined as the inclusive hourly interval between the
first and last valid local observation of the evaluated variable.

Local completeness is calculated as:

completeness (%) =
available local hours / expected local hours × 100

| Completeness | AtmosLink classification |
|---:|---|
| >= 95 % | ALTA |
| 80–94.9 % | ACEPTABLE |
| 50–79.9 % | PARCIAL |
| < 50 % | FRAGMENTADA |

AtmosLink also reports:

- missing local hours;
- maximum local temporal gap;
- longest continuous local run;
- ERA5 reference lag;
- NASA POWER reference lag.

Reference lag is the difference between the latest valid local observation
and the latest available comparable external-reference observation. It
must not automatically be interpreted as provider operational latency.

---

## 6. Operational scientific-quality decision

AtmosLink V4.6 combines local completeness, external-source coverage, and
sample size.

### APTA

A source-variable comparison is classified as APTA when all of the
following are satisfied:

- local completeness >= 95 %;
- comparable N >= 30;
- external-source coverage >= 50 %.

### PRELIMINAR

A comparison is classified as PRELIMINAR when all of the following are
satisfied:

- local completeness >= 80 %;
- comparable N >= 10;
- external-source coverage >= 10 %.

### NO APTA

A comparison is classified as NO APTA when it does not satisfy the
requirements above.

This decision is an operational data-readiness classification. It does not
replace variable-specific physical validation, uncertainty analysis, or
formal inferential statistics.

---

## 6.1 Multi-source scientific readiness

AtmosLink V4.7 adds a higher-level readiness summary derived exclusively
from the V4.6 operational scientific-quality decisions.

No new numerical thresholds are introduced.

Two aggregation concepts are reported.

### MULTI-SOURCE READINESS

This indicator represents the current ability to perform a simultaneous
scientific comparison using:

- local observations;
- ERA5-Land;
- NASA POWER.

The station-level state is obtained conservatively from the worst
operational quality state among the evaluated external sources.

Conceptually:

multi-source readiness =
minimum(ERA5 readiness, NASA POWER readiness)

where the ordering is:

APTA > PRELIMINAR > NO APTA

The corresponding dashboard labels are:

| V4.6 quality state | V4.7 readiness label |
|---|---|
| APTA | READY |
| PRELIMINAR | PARTIAL |
| NO APTA | LIMITED |

A LIMITED multi-source readiness state does not mean that the local
station is scientifically invalid. It means that simultaneous analysis
with all external sources is currently constrained by at least one source.

For example, a station may have highly complete local observations and a
usable ERA5-Land comparison while NASA POWER still has insufficient
temporal coverage.

### BEST AVAILABLE COMPARISON

This indicator identifies the strongest currently available external
comparison.

Conceptually:

best available comparison =
maximum(ERA5 readiness, NASA POWER readiness)

using the same ordering:

APTA > PRELIMINAR > NO APTA

This indicator is intended to distinguish between:

1. readiness for simultaneous Local + ERA5-Land + NASA POWER analysis; and
2. readiness for the best external comparison currently available.

This prevents the absence or limited maturity of one external source from
being incorrectly interpreted as invalidating all scientific comparison
possibilities for the station.

### Local data readiness

Local readiness is summarized from the temporal-completeness states
defined in Section 5.

The dashboard maps them operationally as follows:

| Local completeness state | Readiness label |
|---|---|
| ALTA | READY |
| ACEPTABLE | PARTIAL |
| PARCIAL | PARTIAL |
| FRAGMENTADA | LIMITED |
| SIN DATOS | LIMITED |

Station-level local readiness uses the most conservative completeness
state among the evaluated variables.

### Aggregation principle

The readiness layer is intentionally conservative.

For each source, the station-level state corresponds to the worst state
among the evaluated meteorological variables.

Therefore:

- one variable classified as NO APTA makes that source LIMITED at station
  level;
- one variable classified as PRELIMINAR prevents that source from being
  reported as READY;
- all evaluated variables must be APTA for a source to be READY.

This aggregation rule is a transparency and data-readiness mechanism. It
does not replace interpretation of individual variables, physical
validation, uncertainty analysis, or formal statistical inference.

---


## 7. Quantitative comparison metrics

For valid paired observations AtmosLink reports:

- Bias = mean(reference - local)
- MAE = mean(abs(reference - local))
- RMSE = sqrt(mean((reference - local)^2))
- r² = squared Pearson linear correlation
- NSE = Nash-Sutcliffe efficiency

A high r² does not imply good absolute agreement.

A source may reproduce temporal variability while presenting systematic
offset or poor absolute agreement. Bias, MAE, RMSE, r² and NSE must
therefore be interpreted jointly.

---

## 8. Precipitation handling for SJ01

The field `local_rain_1h_mm` is a retrospective moving-window quantity and
is not used directly as calendar-hour precipitation for scientific source
comparison.

SJ01 hourly precipitation is reconstructed from successive increments of
the cumulative counter `local_rain_total_mm`.

For two consecutive valid samples:

delta_rain = total_current - total_previous

If:

- delta_rain > 0: the increment is accumulated;
- delta_rain = 0: no new precipitation is added;
- delta_rain < 0: the event is treated as a counter reset and the negative
  jump is not accumulated as precipitation.

Hourly precipitation is the sum of valid positive increments assigned to
that hourly bucket.

This method is intended to prevent artificial rainfall caused by counter
resets and to avoid contamination from the retrospective one-hour moving
window.

---

## 9. Missing-data policy

AtmosLink:

- does not interpolate missing ERA5-Land values;
- does not interpolate missing NASA POWER values;
- does not extend external series beyond their latest available value;
- preserves gaps as real missing-data intervals;
- calculates metrics only from actually available Local–Reference pairs.

---

## 10. Interpretation principle

The dashboard separates four different concepts:

1. local data continuity;
2. external-source temporal coverage;
3. statistical sample maturity;
4. numerical agreement between local observation and reference.

These concepts must not be treated as interchangeable.

A dataset can have:

- high local completeness but low external coverage;
- high r² but high bias;
- a large N but poor NSE;
- low current source coverage without any local acquisition failure.

The purpose of the AtmosLink scientific-quality layer is to make these
differences explicit and auditable.
