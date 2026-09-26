#!/usr/bin/env python3
"""Post-audit diagnostic of the complete v23 circular-shift orbit; development only."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd
from scipy.stats import binom

ROOT = Path("/home/carlos/Proyectos/EstacionMeteorologica")
sys.path.insert(0, str(ROOT))
from scientific_discovery.synthetic_benchmark import (
    RF_FEATURES, robust_z, robust_reference,
    rf_drop_threshold_from_array, detect_drop_indices_fixed_threshold,
)

SOURCE = ROOT / "Results/scientific_discovery/DISCOVERY-001/prevalidation_7000_20.csv"
OUT = ROOT / "Results/scientific_discovery/DISCOVERY-001/reviewer_a_shift_orbit.json"
SOURCE_SHA = "eed7df2621f6952b9ea2eaa7524f735a706b69494d3d272fd2dd828b52a97387"
DRIVERS = {
    "cu01_local_temp_avg_c__rise": (1.5308007671599377, 23),
    "sj01_local_temp_avg_c__fall": (1.2876641771825945, 28),
    "sj01_local_hum_avg_pct__fall": (1.6365945597866016, 28),
    "sj01_local_press_hpa__rise": (0.8993210126363124, 28),
}
BOUNDS = [
    ("2026-09-01T18:30:52Z", "2026-09-04T08:02:17Z"),
    ("2026-09-04T08:12:19Z", "2026-09-07T05:14:26Z"),
    ("2026-09-07T05:19:27Z", "2026-09-09T18:41:57Z"),
    ("2026-09-09T18:46:58Z", "2026-09-13T03:29:49Z"),
]
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
df = pd.read_csv(SOURCE)
df["t"] = pd.to_datetime(df.rf_timestamp_utc, utc=True)
vars_ = sorted({name.rsplit("__", 1)[0] for name in DRIVERS})
X = df.set_index("t")[vars_ + RF_FEATURES].resample("5min").median()
driver_idx = {}
for name, (threshold, expected) in DRIVERS.items():
    col, direction = name.rsplit("__", 1)
    z = robust_z(X[col].diff(3))
    score = z if direction == "rise" else -z
    events, last = [], None
    for t, value in score.dropna().items():
        if value < threshold or value < score.loc[t-pd.Timedelta("10min"):t+pd.Timedelta("10min")].max():
            continue
        if last is None or t-last >= pd.Timedelta("360min"):
            events.append(t)
            last = t
    assert len(events) == expected, (name, len(events))
    driver_idx[name] = np.array([X.index.get_loc(t) for t in events], dtype=int)
med, scale = robust_reference(X)
base = X[RF_FEATURES].to_numpy(float)
threshold = rf_drop_threshold_from_array(base, med.to_numpy(float), scale.to_numpy(float), quantile=.075)
assert abs(threshold - (-0.5620817932460992)) < 1e-12
rf = detect_drop_indices_fixed_threshold(base, med.to_numpy(float), scale.to_numpy(float), threshold)
bounds = [(int(X.index.searchsorted(pd.Timestamp(a))),
           int(X.index.searchsorted(pd.Timestamp(b), side="right")-1)) for a, b in BOUNDS]

def directional(driver, horizon):
    left = np.searchsorted(rf, driver-horizon, side="left")
    mid = np.searchsorted(rf, driver, side="left")
    right = np.searchsorted(rf, driver+horizon, side="right")
    pre = mid > left
    post = right > np.searchsorted(rf, driver, side="right")
    post_only = int(np.sum(post & ~pre))
    pre_only = int(np.sum(pre & ~post))
    discordant = post_only + pre_only
    p = float(binom.sf(post_only-1, discordant, .5)) if discordant else 1.0
    return p, discordant, post_only, pre_only

counts = dict.fromkeys(("M0", "M1", "M2", "M3"), 0)
discordant_shifts = 0
n = len(X)
for shift in range(72, n-72):
    selected = [set() for _ in range(4)]
    for name, indices in driver_idx.items():
        driver = np.sort((indices + shift) % n)
        for horizon in (6, 12, 24):
            p, support, _, _ = directional(driver, horizon)
            positive = sum(directional(driver[(driver >= a) & (driver <= b)], horizon)[2] >
                           directional(driver[(driver >= a) & (driver <= b)], horizon)[3]
                           for a, b in bounds)
            checks = (p < .05, p < .05/12,
                      p < .05/12 and support >= 8,
                      p < .05/12 and support >= 8 and positive >= 3)
            for j, passed in enumerate(checks):
                if passed:
                    selected[j].add(name)
    for j, method in enumerate(counts):
        counts[method] += bool(selected[j])
    discordant_shifts += int(not (selected[1] == selected[2] == selected[3]))
result = {
    "status": "PASS" if counts == {"M0":649, "M1":50, "M2":50, "M3":50} and discordant_shifts == 0 else "REVIEW",
    "scope": "post-hoc exhaustive diagnostic of the v23 circular-shift orbit on one fixed development background",
    "source_sha256": SOURCE_SHA,
    "grid_bins": n,
    "complete_bins": int(X[vars_ + RF_FEATURES].notna().all(axis=1).sum()),
    "rf_events": len(rf),
    "admissible_offsets": n-144,
    "selected_offsets": counts,
    "selection_rates": {k: v/(n-144) for k, v in counts.items()},
    "m1_m2_m3_discordant_offsets": discordant_shifts,
    "warning": "This checks finite-orbit Monte Carlo stability, not null exchangeability, physical replication, or field-wide FWER."
}
OUT.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
