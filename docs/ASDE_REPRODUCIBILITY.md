# ASDE Reproducibility Record

## Scope
This record covers the audit-grade DISCOVERY-001 artifacts used for the IEEE Methods manuscript. It verifies analytical provenance and published benchmark outputs; it does not claim that every historical exploratory run can be reconstructed from a single command.

## Recorded environment
- Python 3.12.3
- NumPy 1.26.4
- pandas 2.1.4
- SciPy 1.11.4
- Matplotlib 3.6.3
- Linux 6.14.0-37-generic x86_64, glibc 2.39

Exact package pins are stored in `scientific_discovery/requirements-discovery.txt`. Machine-readable environment and artifact hashes are stored in `scientific_discovery/environment_manifest.json`.

## Verification command
From the repository root:

```bash
python3 scripts/verify_asde_publication_artifacts.py
```

A successful run must end with `STATUS=PASS`.

The verifier checks:
1. SHA-256 of the D_development snapshot.
2. SHA-256 of the frozen v21 protocol.
3. SHA-256 of v21 trials, metrics and summary artifacts.
4. Recorded package versions.
5. Reconstruction of headline v21 metrics from raw trial rows.
6. Analytical isolation audit for D_validation across active v7-v21 scripts.

## Important CSV parsing note
The v21 trial table uses the literal label `null` in its `mode` column. pandas treats the string `null` as missing data under default CSV parsing. Reproducibility scripts therefore read the trial CSV with `keep_default_na=False`. This is a parsing issue only; it does not change the stored audit results.

## Publication archive still required
Before manuscript submission, create a DOI-bearing immutable release (e.g. Zenodo or an institutional repository) containing the tagged code, protocols, machine-readable audit outputs and permitted data artifacts. The DOI release should reference the exact Git commit used for the submitted manuscript.
