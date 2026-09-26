CREATE TABLE IF NOT EXISTS scientific_discoveries (
    discovery_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    detected_at_utc TEXT NOT NULL,
    dataset_sha256 TEXT NOT NULL,
    dataset_start_utc TEXT,
    dataset_end_utc TEXT,
    site_scope TEXT,
    frequency_mhz REAL,
    bandwidth_mhz REAL,
    direction TEXT,
    variables_json TEXT NOT NULL,
    derived_variables_json TEXT,
    algorithm TEXT NOT NULL,
    window_minutes REAL,
    lag_minutes REAL,
    number_of_occurrences INTEGER,
    effect_size REAL,
    stability_score REAL,
    pattern_description TEXT NOT NULL,
    generated_hypothesis TEXT,
    software_version TEXT,
    git_commit TEXT,
    status TEXT NOT NULL CHECK (
      status IN (
        'CANDIDATE','SCREENED_OUT','EVIDENCE_ACCUMULATING',
        'HUMAN_REVIEWED','HYPOTHESIS','FROZEN','VALIDATING','CONFIRMED',
        'REJECTED','INCONCLUSIVE'
      )
    ),
    human_review TEXT,
    validation_dataset_sha256 TEXT,
    validation_result_json TEXT,
    created_at_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scientific_discoveries_experiment
ON scientific_discoveries(experiment_id);

CREATE INDEX IF NOT EXISTS idx_scientific_discoveries_status
ON scientific_discoveries(status);
