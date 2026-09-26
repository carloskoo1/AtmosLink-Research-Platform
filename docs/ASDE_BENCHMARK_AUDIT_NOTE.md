# ASDE Benchmark Audit Note

The synthetic benchmark was developed adaptively in stages v7-v10.

- v7 established a first recovery/false-positive benchmark.
- v8 mapped detection sensitivity across analysis horizons.
- v9 demonstrated the identifiability effect of atmospheric-event spacing and includes a safeguard ablation.
- v10 repeated the revised design with additional seeds, but occurred before the benchmark protocol and implementation were committed as an immutable Git checkpoint.

Therefore v7-v10 are treated as benchmark development/calibration evidence, not as the final audit-grade confirmatory simulation.

The protocol in ASDE_SYNTHETIC_BENCHMARK_PROTOCOL.md and the implementation are frozen at the next Git checkpoint. A subsequent run using previously unused simulation and null seeds will be designated the audit-grade confirmatory synthetic benchmark.

This distinction does not affect D_validation, which remains unopened throughout all synthetic benchmark development.

A legacy ablation generated from the adaptive-threshold v8/v10 path is preserved under v11_legacy_recomputed_threshold_ablation for provenance. It is not part of the frozen final benchmark and must not be cited as the audit-grade result.

The final benchmark freezes the RF-drop threshold learned from the unmodified development background and uses 180-minute atmospheric-event spacing.
