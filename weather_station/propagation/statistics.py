"""
Statistical utilities for AtmosLink propagation validation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean, median, stdev
from typing import Iterable, Sequence


@dataclass(frozen=True)
class ErrorMetrics:
    sample_count: int
    bias_db: float | None
    mae_db: float | None
    rmse_db: float | None
    median_error_db: float | None
    standard_deviation_db: float | None
    maximum_absolute_error_db: float | None
    r_squared: float | None


@dataclass(frozen=True)
class ConfidenceInterval:
    sample_count: int
    mean_value: float | None
    standard_deviation: float | None
    standard_error: float | None
    lower_95: float | None
    upper_95: float | None


def calculate_error_metrics(
    observed: Sequence[float],
    predicted: Sequence[float],
) -> ErrorMetrics:
    """
    Calculate prediction metrics using:

        residual = observed - predicted
    """

    if len(observed) != len(predicted):
        raise ValueError(
            "Observed and predicted sequences must have equal length."
        )

    if not observed:
        return ErrorMetrics(
            sample_count=0,
            bias_db=None,
            mae_db=None,
            rmse_db=None,
            median_error_db=None,
            standard_deviation_db=None,
            maximum_absolute_error_db=None,
            r_squared=None,
        )

    errors = [
        measured - estimated
        for measured, estimated in zip(
            observed,
            predicted,
        )
    ]

    absolute_errors = [
        abs(error)
        for error in errors
    ]

    squared_errors = [
        error * error
        for error in errors
    ]

    observed_mean = mean(observed)

    total_sum_of_squares = sum(
        (value - observed_mean) ** 2
        for value in observed
    )

    residual_sum_of_squares = sum(
        (
            measured - estimated
        ) ** 2
        for measured, estimated in zip(
            observed,
            predicted,
        )
    )

    r_squared = (
        None
        if total_sum_of_squares == 0.0
        else (
            1.0
            - residual_sum_of_squares
            / total_sum_of_squares
        )
    )

    return ErrorMetrics(
        sample_count=len(errors),
        bias_db=mean(errors),
        mae_db=mean(absolute_errors),
        rmse_db=math.sqrt(
            mean(squared_errors)
        ),
        median_error_db=float(
            median(errors)
        ),
        standard_deviation_db=(
            stdev(errors)
            if len(errors) > 1
            else 0.0
        ),
        maximum_absolute_error_db=max(
            absolute_errors
        ),
        r_squared=r_squared,
    )


def calculate_confidence_interval_95(
    values: Iterable[float],
) -> ConfidenceInterval:
    """
    Calculate an approximate 95% confidence interval for the mean.

    Uses the normal critical value 1.96. For very small samples this is
    descriptive and should not be presented as strong inferential evidence.
    """

    data = list(values)

    if not data:
        return ConfidenceInterval(
            sample_count=0,
            mean_value=None,
            standard_deviation=None,
            standard_error=None,
            lower_95=None,
            upper_95=None,
        )

    average = mean(data)

    if len(data) == 1:
        return ConfidenceInterval(
            sample_count=1,
            mean_value=average,
            standard_deviation=0.0,
            standard_error=0.0,
            lower_95=average,
            upper_95=average,
        )

    deviation = stdev(data)
    standard_error = deviation / math.sqrt(
        len(data)
    )

    margin = 1.96 * standard_error

    return ConfidenceInterval(
        sample_count=len(data),
        mean_value=average,
        standard_deviation=deviation,
        standard_error=standard_error,
        lower_95=average - margin,
        upper_95=average + margin,
    )
