"""
Calibration models for the AtmosLink propagation pipeline.

This module is intentionally independent from the physical propagation
models. The physical layer remains responsible for FSPL, gaseous
attenuation and rain attenuation.

The calibration layer accounts for systematic implementation losses and,
optionally, a deterministic slow-fading component.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import median
from typing import Iterable, Sequence


@dataclass(frozen=True)
class CalibrationParameters:
    """
    Parameters applied after the physical propagation model.

    Attributes
    ----------
    implementation_loss_db:
        Constant loss not represented by the basic physical budget.
        It may include effective antenna gain differences, connectors,
        equipment implementation losses, alignment and other systematic
        effects.

    slow_fading_amplitude_db:
        Amplitude of the deterministic sinusoidal slow-fading component.

    slow_fading_period_minutes:
        Period of the sinusoidal component in minutes.

    slow_fading_phase_rad:
        Initial phase of the sinusoidal component.

    model_version:
        Version identifier stored with the calibrated observations.
    """

    implementation_loss_db: float
    slow_fading_amplitude_db: float = 0.0
    slow_fading_period_minutes: float = 720.0
    slow_fading_phase_rad: float = 0.0
    model_version: str = "calibration-1.0.0"


@dataclass(frozen=True)
class CalibrationMetrics:
    sample_count: int
    bias_db: float
    mae_db: float
    rmse_db: float
    median_error_db: float
    max_absolute_error_db: float


def estimate_constant_loss_db(
    predicted_rssi_dbm: Sequence[float],
    observed_rssi_dbm: Sequence[float],
) -> float:
    """
    Estimate a robust constant implementation loss.

    The physical prediction is normally less negative than the observed
    RSSI. Therefore:

        implementation_loss =
            predicted_physical - observed

    The median is used instead of the mean to reduce sensitivity to
    transient fading and outliers.
    """

    if len(predicted_rssi_dbm) != len(observed_rssi_dbm):
        raise ValueError(
            "Predicted and observed sequences must have the same length."
        )

    if not predicted_rssi_dbm:
        raise ValueError(
            "At least one valid predicted/observed pair is required."
        )

    losses = [
        predicted - observed
        for predicted, observed in zip(
            predicted_rssi_dbm,
            observed_rssi_dbm,
        )
    ]

    return float(median(losses))


def slow_fading_loss_db(
    elapsed_minutes: float,
    parameters: CalibrationParameters,
) -> float:
    """
    Return a deterministic sinusoidal slow-fading loss.

    Positive values represent additional propagation loss.
    """

    amplitude = parameters.slow_fading_amplitude_db

    if amplitude == 0.0:
        return 0.0

    period = parameters.slow_fading_period_minutes

    if period <= 0.0:
        raise ValueError(
            "slow_fading_period_minutes must be greater than zero."
        )

    angular_position = (
        2.0
        * math.pi
        * elapsed_minutes
        / period
        + parameters.slow_fading_phase_rad
    )

    return amplitude * math.sin(angular_position)


def calibrated_rssi_dbm(
    physical_rssi_dbm: float,
    elapsed_minutes: float,
    parameters: CalibrationParameters,
) -> float:
    """
    Apply the AtmosLink calibration layer to a physical RSSI prediction.
    """

    fading_loss = slow_fading_loss_db(
        elapsed_minutes=elapsed_minutes,
        parameters=parameters,
    )

    return (
        physical_rssi_dbm
        - parameters.implementation_loss_db
        - fading_loss
    )


def calculate_metrics(
    predicted_rssi_dbm: Iterable[float],
    observed_rssi_dbm: Iterable[float],
) -> CalibrationMetrics:
    """
    Calculate residual metrics using:

        error = observed - predicted
    """

    predicted = list(predicted_rssi_dbm)
    observed = list(observed_rssi_dbm)

    if len(predicted) != len(observed):
        raise ValueError(
            "Predicted and observed sequences must have the same length."
        )

    if not predicted:
        raise ValueError(
            "At least one valid predicted/observed pair is required."
        )

    errors = [
        measured - estimated
        for estimated, measured in zip(predicted, observed)
    ]

    absolute_errors = [abs(value) for value in errors]
    squared_errors = [value * value for value in errors]

    count = len(errors)

    return CalibrationMetrics(
        sample_count=count,
        bias_db=sum(errors) / count,
        mae_db=sum(absolute_errors) / count,
        rmse_db=math.sqrt(sum(squared_errors) / count),
        median_error_db=float(median(errors)),
        max_absolute_error_db=max(absolute_errors),
    )
