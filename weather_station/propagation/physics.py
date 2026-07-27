"""
Deterministic propagation calculations used by the scientific pipeline.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class LinkBudget:
    frequency_ghz: float
    path_distance_km: float
    tx_power_dbm: float
    ap_antenna_gain_dbi: float
    sm_antenna_gain_dbi: float
    ap_feeder_loss_db: float = 0.0
    sm_feeder_loss_db: float = 0.0


def _positive(value: float, name: str) -> float:
    value = float(value)

    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and greater than zero")

    return value


def _finite(value: float, name: str) -> float:
    value = float(value)

    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")

    return value


def free_space_path_loss_db(
    frequency_ghz: float,
    path_distance_km: float,
) -> float:
    frequency_ghz = _positive(frequency_ghz, "frequency_ghz")
    path_distance_km = _positive(
        path_distance_km,
        "path_distance_km",
    )

    return (
        92.45
        + 20.0 * math.log10(frequency_ghz)
        + 20.0 * math.log10(path_distance_km)
    )


def predicted_rssi_dbm(
    link: LinkBudget,
    additional_attenuation_db: float = 0.0,
) -> float:
    additional_attenuation_db = _finite(
        additional_attenuation_db,
        "additional_attenuation_db",
    )

    fspl = free_space_path_loss_db(
        link.frequency_ghz,
        link.path_distance_km,
    )

    total_feeder_loss = (
        link.ap_feeder_loss_db
        + link.sm_feeder_loss_db
    )

    return (
        link.tx_power_dbm
        + link.ap_antenna_gain_dbi
        + link.sm_antenna_gain_dbi
        - total_feeder_loss
        - fspl
        - additional_attenuation_db
    )


def residual_db(
    observed_rssi_dbm: float,
    predicted_rssi_dbm_value: float,
) -> float:
    return (
        _finite(observed_rssi_dbm, "observed_rssi_dbm")
        - _finite(
            predicted_rssi_dbm_value,
            "predicted_rssi_dbm",
        )
    )
