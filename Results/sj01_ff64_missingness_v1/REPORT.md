# SJ01 FF64 Missingness Bias Audit v1

Read-only audit. No production database, service, firmware, or station configuration was modified.

## Coverage

- Exclusive minute events: 8643
- Valid: 5709
- FF64: 2934
- Overall FF64 fraction: 33.95%
- Ambiguous minutes excluded: 0

## Complete-day rates

```text
date_local  valid  ff64  total  ff64_pct
2026-09-22    950   490   1440 34.027778
2026-09-23    969   471   1440 32.708333
2026-09-24    965   475   1440 32.986111
2026-09-25    929   511   1440 35.486111
2026-09-26    948   492   1440 34.166667
```

## RF-scenario rates

```text
scenario  valid  ff64  total  ff64_pct
 6475/20   2112  1055   3167 33.312283
 6475/40    718   384   1102 34.845735
 6655/40   2841  1479   4320 34.236111
 UNKNOWN     38    16     54 29.629630
```

## Categorical association

- Day: Cramer's V=0.0208, p=0.538
- Hour: Cramer's V=0.0367, p=0.976
- RF scenario: Cramer's V=0.0114, p=0.57

## Continuous covariates

```text
          variable  n_valid  n_ff64  mean_valid  mean_ff64  median_valid  median_ff64  smd_ff64_minus_valid  mannwhitney_p
 nasa_sj_precip_mm     3833    1929    0.020701   0.020007       0.01375     0.012917             -0.030447       0.636876
            mcs_ul     5702    2930  139.976324 141.142662     102.00000   102.000000              0.023742       0.326601
            ul_mcs     5671    2918  139.959090 140.832419     102.00000   102.000000              0.017823       0.621799
            dl_mcs     5671    2918  157.956092 158.771076     201.00000   201.000000              0.016536       0.581115
    nasa_sj_rh_pct     3833    1929   78.132382  77.884914      86.88000    86.880000             -0.014808       0.928837
            mcs_dl     5702    2930  159.411961 160.121160     201.00000   201.000000              0.014442       0.541522
       sta_dl_rssi     5702    2930  -77.562960 -77.527645     -77.00000   -77.000000              0.014081       0.882702
    nasa_sj_temp_c     3833    1929   17.105828  17.151208      15.56000    15.750000              0.013834       0.906913
        temp_avg_C     5600    2869   19.531043  19.577267      18.60000    18.660000              0.012390       0.672363
           dl_rate     5702    2930  111.487724 112.237201     103.00000   103.000000              0.011834       0.418625
nasa_sj_dewpoint_c     3833    1929   12.845591  12.838647      13.14000    13.100000             -0.009235       0.360079
            snr_ul     5702    2930   15.487724  15.425256      18.00000    18.000000             -0.008974       0.925292
      pres_avg_hPa     5600    2869  741.298384 741.309599     741.49000   741.500000              0.008700       0.654506
            snr_dl     5702    2930   21.916345  21.932082      22.00000    22.000000              0.007646       0.782040
       dl_rssi_dbm     5671    2918  -77.567272 -77.581220     -77.00000   -77.000000             -0.007523       0.802624
    tx_quality_pct     5671    2918   99.400458  99.451679     100.00000   100.000000              0.006732       0.767629
nasa_sj_wind10m_ms     3833    1929    1.461124   1.467926       1.10000     1.100000              0.006438       0.950384
         dl_snr_db     5671    2918   21.931582  21.920151      22.00000    22.000000             -0.005774       0.806123
       hum_avg_pct     5600    2869   57.944089  57.877009      61.10000    61.010000             -0.005677       0.776862
   tx_capacity_pct     5671    2918   19.780462  19.807745      20.00000    20.000000              0.003530       0.841672
 nasa_sj_press_hpa     3833    1929  767.433029 767.434318     767.40000   767.500000              0.001270       0.962527
      rain_1min_mm     5600    2869    0.000000   0.000000       0.00000     0.000000                   NaN       1.000000
        rain_1h_mm     5600    2869    0.000000   0.000000       0.00000     0.000000                   NaN       1.000000
```

## Scientific interpretation

- Maximum absolute standardized mean difference across matched observed covariates: 0.0304.
- Hour-of-day FF64 rate spread: 5.56 percentage points.
- Known RF-scenario FF64 rate spread: 1.53 percentage points.
- In the currently observable window, there is no evidence of a strong differential FF64 association with complete day, hour of day, the three represented RF scenarios, CU01 weather, NASA POWER conditions at SM_SAN_JOSE, or the matched RF metrics.
- This supports treating FF64 primarily as loss of eligible SJ01 observations rather than demonstrated weather- or RF-selective missingness in this window.
- This is not proof of MCAR, and the physical failure mechanism remains unresolved.

## Scope limitations

- The journal window begins on 2026-09-21 local time; it cannot establish behavior before the retained logs.
- RF scenarios represented in this audit are 6475/20, 6655/40, and 6475/40; conclusions must not be generalized automatically to unrepresented 3x2 scenarios.
- NASA POWER provides independent SJ01-area atmospheric covariates for part of the audit window; ERA5-Land has no overlap with the retained FF64 journal window at the current watermark.
- CU01 rain was constant at zero in the matched window and therefore cannot test rain dependence by itself; NASA POWER precipitation provides limited independent variation.

## Interpretation guardrail

This audit evaluates whether FF64 occurrence is associated with observed time, weather, RF, or configuration covariates.
It does not prove Missing Completely At Random (MCAR), and it does not identify the physical root cause.
FF64 records remain ineligible for scientific observation reconstruction.
