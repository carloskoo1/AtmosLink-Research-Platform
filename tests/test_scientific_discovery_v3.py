import numpy as np
import pandas as pd

from scientific_discovery.event_sequence_engine import (
    robust_location_scale,
    multivariate_transition_score,
    exact_direction_stats,
)

def test_robust_scale_falls_back_when_mad_is_zero():
    df = pd.DataFrame({
        "constant_mostly": [1, 1, 1, 1, 1, 5],
        "varying": [1, 2, 3, 4, 5, 6],
    })
    _, scale = robust_location_scale(df)
    assert np.isfinite(scale).all()
    assert (scale > 0).all()

def test_multivariate_transition_requires_multiple_active_features():
    z = pd.DataFrame({
        "a": [2.0, 2.0],
        "b": [0.0, 2.0],
        "c": [0.0, 0.0],
    })
    score = multivariate_transition_score(z, min_active=2, active_z=1.5)
    assert pd.isna(score.iloc[0])
    assert np.isfinite(score.iloc[1])

def test_exact_direction_rejects_more_past_than_future_events():
    atm = [
        pd.Timestamp("2026-09-01T12:00:00Z"),
        pd.Timestamp("2026-09-01T14:00:00Z"),
    ]
    rf = [
        pd.Timestamp("2026-09-01T11:30:00Z"),
        pd.Timestamp("2026-09-01T13:30:00Z"),
        pd.Timestamp("2026-09-01T14:30:00Z"),
    ]
    result = exact_direction_stats(atm, rf, 60)
    assert result["past_events"] == 2
    assert result["future_events"] == 1
    assert result["direction_pass"] is False
