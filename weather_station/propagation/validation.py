"""
Rain Event Cross Validation for AtmosLink.

Implements Leave-One-Rain-Event-Out validation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import median
from typing import Any, Mapping, Sequence

from weather_station.propagation.event_detection import (
    RainEvent,
    build_event_membership,
)
from weather_station.propagation.statistics import (
    ErrorMetrics,
    calculate_error_metrics,
)


@dataclass(frozen=True)
class RainEventFoldResult:
    fold_id: int
    validation_event_id: int

    validation_event_start_utc: str
    validation_event_end_utc: str
    validation_samples: int

    training_event_ids: tuple[int, ...]
    training_rain_samples: int
    dry_calibration_samples: int

    implementation_loss_db: float
    rain_scale_factor: float

    physical_metrics: ErrorMetrics
    calibrated_metrics: ErrorMetrics


@dataclass(frozen=True)
class RainEventCrossValidationResult:
    link_id: str
    model_version: str
    event_count: int
    fold_count: int
    implementation_loss_db: float
    folds: tuple[RainEventFoldResult, ...]


def estimate_implementation_loss_from_dry_rows(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[float, int]:
    """
    Estimate systematic implementation loss using dry observations.
    """

    dry_losses = [
        float(row["clear_sky_rssi_dbm"])
        - float(row["observed_rssi_dbm"])
        for row in rows
        if float(row["rain_rate_mm_h"] or 0.0)
        <= 0.0
    ]

    if not dry_losses:
        raise RuntimeError(
            "No dry observations are available for implementation-loss "
            "calibration."
        )

    return float(median(dry_losses)), len(
        dry_losses
    )


def estimate_rain_scale_from_training_events(
    training_rows: Sequence[Mapping[str, Any]],
    implementation_loss_db: float,
    minimum_attenuation_db: float = 0.001,
    minimum_scale: float = 0.0,
    maximum_scale: float = 2.0,
) -> float:
    """
    Estimate a robust rain scaling factor from rainy training rows.

    Model:

        observed =
            clear_sky
            - implementation_loss
            - alpha * physical_rain_attenuation
    """

    candidates: list[float] = []

    for row in training_rows:
        attenuation = float(
            row["rain_attenuation_db"]
            or 0.0
        )

        if attenuation < minimum_attenuation_db:
            continue

        clear_sky = float(
            row["clear_sky_rssi_dbm"]
        )

        observed = float(
            row["observed_rssi_dbm"]
        )

        alpha = (
            clear_sky
            - implementation_loss_db
            - observed
        ) / attenuation

        if math.isfinite(alpha):
            candidates.append(alpha)

    if not candidates:
        raise RuntimeError(
            "No valid rainy training observations are available."
        )

    rain_scale = float(median(candidates))

    return min(
        maximum_scale,
        max(minimum_scale, rain_scale),
    )


def physical_rain_prediction(
    row: Mapping[str, Any],
    implementation_loss_db: float,
) -> float:
    """
    Prediction using the complete uniform-path ITU attenuation.
    """

    return (
        float(row["clear_sky_rssi_dbm"])
        - implementation_loss_db
        - float(row["rain_attenuation_db"])
    )


def calibrated_rain_prediction(
    row: Mapping[str, Any],
    implementation_loss_db: float,
    rain_scale_factor: float,
) -> float:
    """
    Prediction using the calibrated rain attenuation.
    """

    return (
        float(row["clear_sky_rssi_dbm"])
        - implementation_loss_db
        - (
            rain_scale_factor
            * float(row["rain_attenuation_db"])
        )
    )


def run_leave_one_rain_event_out(
    rows: Sequence[Mapping[str, Any]],
    events: Sequence[RainEvent],
    link_id: str,
    model_version: str = "recv-1.0.0",
    minimum_training_events: int = 1,
) -> RainEventCrossValidationResult:
    """
    Run Leave-One-Rain-Event-Out validation.

    Each fold reserves one complete event for validation and estimates the
    rain scale using all remaining rain events.
    """

    if len(events) < 2:
        raise RuntimeError(
            "At least two independent rain events are required."
        )

    if minimum_training_events < 1:
        raise ValueError(
            "minimum_training_events must be at least one."
        )

    membership = build_event_membership(
        events
    )

    implementation_loss_db, dry_count = (
        estimate_implementation_loss_from_dry_rows(
            rows
        )
    )

    folds: list[RainEventFoldResult] = []

    all_event_ids = {
        event.event_id
        for event in events
    }

    for fold_id, validation_event in enumerate(
        events,
        start=1,
    ):
        training_event_ids = tuple(
            sorted(
                all_event_ids
                - {validation_event.event_id}
            )
        )

        if (
            len(training_event_ids)
            < minimum_training_events
        ):
            continue

        training_rows = [
            row
            for row in rows
            if membership.get(
                int(row["id"])
            )
            in training_event_ids
        ]

        validation_rows = [
            row
            for row in rows
            if membership.get(
                int(row["id"])
            )
            == validation_event.event_id
        ]

        if not validation_rows:
            raise RuntimeError(
                "Validation event contains no observations."
            )

        rain_scale_factor = (
            estimate_rain_scale_from_training_events(
                training_rows=training_rows,
                implementation_loss_db=(
                    implementation_loss_db
                ),
            )
        )

        observed = [
            float(row["observed_rssi_dbm"])
            for row in validation_rows
        ]

        physical_predictions = [
            physical_rain_prediction(
                row=row,
                implementation_loss_db=(
                    implementation_loss_db
                ),
            )
            for row in validation_rows
        ]

        calibrated_predictions = [
            calibrated_rain_prediction(
                row=row,
                implementation_loss_db=(
                    implementation_loss_db
                ),
                rain_scale_factor=(
                    rain_scale_factor
                ),
            )
            for row in validation_rows
        ]

        folds.append(
            RainEventFoldResult(
                fold_id=fold_id,
                validation_event_id=(
                    validation_event.event_id
                ),
                validation_event_start_utc=(
                    validation_event
                    .start_timestamp_utc
                ),
                validation_event_end_utc=(
                    validation_event
                    .end_timestamp_utc
                ),
                validation_samples=len(
                    validation_rows
                ),
                training_event_ids=(
                    training_event_ids
                ),
                training_rain_samples=len(
                    training_rows
                ),
                dry_calibration_samples=(
                    dry_count
                ),
                implementation_loss_db=(
                    implementation_loss_db
                ),
                rain_scale_factor=(
                    rain_scale_factor
                ),
                physical_metrics=(
                    calculate_error_metrics(
                        observed=observed,
                        predicted=(
                            physical_predictions
                        ),
                    )
                ),
                calibrated_metrics=(
                    calculate_error_metrics(
                        observed=observed,
                        predicted=(
                            calibrated_predictions
                        ),
                    )
                ),
            )
        )

    if not folds:
        raise RuntimeError(
            "No valid validation folds were generated."
        )

    return RainEventCrossValidationResult(
        link_id=link_id,
        model_version=model_version,
        event_count=len(events),
        fold_count=len(folds),
        implementation_loss_db=(
            implementation_loss_db
        ),
        folds=tuple(folds),
    )
