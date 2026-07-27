"""
Motor de métricas científicas de AtmosLink.

Este módulo implementa métricas uniformes para comparar:

- estación local frente a ERA5-Land;
- estación local frente a NASA POWER;
- RSSI observado frente a RSSI predicho;
- atenuación observada frente a atenuación física estimada.

Las funciones no dependen de pandas ni de scipy. Esto permite que el
núcleo matemático pueda ejecutarse incluso en dispositivos con recursos
limitados, como una Raspberry Pi.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from statistics import NormalDist
from typing import Any, Iterable, Sequence


Number = int | float


@dataclass(frozen=True, slots=True)
class ComparisonMetrics:
    """
    Resultado consolidado de una comparación entre referencia y estimación.

    Convención:

    - ``reference`` representa el valor observado o considerado verdadero.
    - ``estimated`` representa el valor modelado, satelital o predicho.
    - El sesgo se calcula como ``estimated - reference``.
    """

    n_total: int
    n_valid: int
    n_missing: int
    missing_percentage: float

    mae: float | None
    rmse: float | None
    mbe: float | None
    mape: float | None

    r_squared: float | None
    pearson_r: float | None
    spearman_rho: float | None

    residual_mean: float | None
    residual_std: float | None
    residual_ci95_low: float | None
    residual_ci95_high: float | None

    reference_mean: float | None
    estimated_mean: float | None
    reference_std: float | None
    estimated_std: float | None

    def to_dict(self) -> dict[str, Any]:
        """Convierte el resultado a un diccionario serializable."""
        return asdict(self)


def _safe_float(value: Any) -> float | None:
    """
    Convierte un valor en ``float`` si es numérico y finito.

    Se consideran inválidos:

    - ``None``;
    - cadenas vacías;
    - NaN;
    - infinito positivo o negativo;
    - valores que no puedan convertirse a número.
    """

    if value is None:
        return None

    if isinstance(value, str) and not value.strip():
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None

    return number


def clean_paired_values(
    reference: Iterable[Any],
    estimated: Iterable[Any],
) -> tuple[list[float], list[float], int]:
    """
    Filtra pares inválidos y conserva únicamente observaciones completas.

    Ambos iterables deben tener la misma cantidad de elementos.

    Returns
    -------
    tuple
        ``(reference_clean, estimated_clean, n_total)``.
    """

    reference_values = list(reference)
    estimated_values = list(estimated)

    if len(reference_values) != len(estimated_values):
        raise ValueError(
            "reference y estimated deben tener la misma longitud: "
            f"{len(reference_values)} != {len(estimated_values)}"
        )

    reference_clean: list[float] = []
    estimated_clean: list[float] = []

    for reference_value, estimated_value in zip(
        reference_values,
        estimated_values,
        strict=True,
    ):
        reference_number = _safe_float(reference_value)
        estimated_number = _safe_float(estimated_value)

        if reference_number is None or estimated_number is None:
            continue

        reference_clean.append(reference_number)
        estimated_clean.append(estimated_number)

    return reference_clean, estimated_clean, len(reference_values)


def calculate_missing_percentage(
    n_total: int,
    n_valid: int,
) -> float:
    """Calcula el porcentaje de pares no válidos."""

    if n_total < 0 or n_valid < 0:
        raise ValueError("n_total y n_valid no pueden ser negativos")

    if n_valid > n_total:
        raise ValueError("n_valid no puede ser mayor que n_total")

    if n_total == 0:
        return 0.0

    return ((n_total - n_valid) / n_total) * 100.0


def _mean(values: Sequence[float]) -> float | None:
    if not values:
        return None

    return sum(values) / len(values)


def _sample_std(values: Sequence[float]) -> float | None:
    """
    Calcula la desviación estándar muestral.

    Requiere al menos dos observaciones.
    """

    if len(values) < 2:
        return None

    mean_value = sum(values) / len(values)
    variance = sum(
        (value - mean_value) ** 2
        for value in values
    ) / (len(values) - 1)

    return math.sqrt(variance)


def _pearson(
    first: Sequence[float],
    second: Sequence[float],
) -> float | None:
    """Calcula el coeficiente de correlación de Pearson."""

    if len(first) != len(second):
        raise ValueError("Las series deben tener la misma longitud")

    if len(first) < 2:
        return None

    first_mean = sum(first) / len(first)
    second_mean = sum(second) / len(second)

    numerator = sum(
        (first_value - first_mean)
        * (second_value - second_mean)
        for first_value, second_value in zip(first, second, strict=True)
    )

    first_sum_squares = sum(
        (value - first_mean) ** 2
        for value in first
    )
    second_sum_squares = sum(
        (value - second_mean) ** 2
        for value in second
    )

    denominator = math.sqrt(
        first_sum_squares * second_sum_squares
    )

    if denominator == 0.0:
        return None

    return numerator / denominator


def _average_ranks(values: Sequence[float]) -> list[float]:
    """
    Calcula rangos promedio, incluyendo tratamiento de empates.
    """

    sorted_pairs = sorted(
        enumerate(values),
        key=lambda pair: pair[1],
    )

    ranks = [0.0] * len(values)
    position = 0

    while position < len(sorted_pairs):
        end = position + 1
        current_value = sorted_pairs[position][1]

        while (
            end < len(sorted_pairs)
            and sorted_pairs[end][1] == current_value
        ):
            end += 1

        average_rank = (
            (position + 1) + end
        ) / 2.0

        for rank_position in range(position, end):
            original_index = sorted_pairs[rank_position][0]
            ranks[original_index] = average_rank

        position = end

    return ranks


def _spearman(
    first: Sequence[float],
    second: Sequence[float],
) -> float | None:
    """Calcula Spearman como Pearson aplicado a los rangos."""

    if len(first) != len(second):
        raise ValueError("Las series deben tener la misma longitud")

    if len(first) < 2:
        return None

    return _pearson(
        _average_ranks(first),
        _average_ranks(second),
    )


def _r_squared(
    reference: Sequence[float],
    estimated: Sequence[float],
) -> float | None:
    """
    Calcula el coeficiente de determinación mediante SSE y SST.

    R² puede ser negativo cuando el modelo es peor que utilizar la media
    de la referencia.
    """

    if len(reference) != len(estimated):
        raise ValueError("Las series deben tener la misma longitud")

    if len(reference) < 2:
        return None

    reference_mean = sum(reference) / len(reference)

    sum_squared_error = sum(
        (reference_value - estimated_value) ** 2
        for reference_value, estimated_value in zip(
            reference,
            estimated,
            strict=True,
        )
    )

    total_sum_squares = sum(
        (reference_value - reference_mean) ** 2
        for reference_value in reference
    )

    if total_sum_squares == 0.0:
        return None

    return 1.0 - (
        sum_squared_error / total_sum_squares
    )


def _mape(
    reference: Sequence[float],
    estimated: Sequence[float],
) -> float | None:
    """
    Calcula MAPE omitiendo referencias iguales a cero.

    Esta métrica debe interpretarse con cautela en variables que puedan
    tomar valores cercanos a cero, como lluvia o atenuación residual.
    """

    percentage_errors: list[float] = []

    for reference_value, estimated_value in zip(
        reference,
        estimated,
        strict=True,
    ):
        if reference_value == 0.0:
            continue

        percentage_errors.append(
            abs(
                (
                    estimated_value - reference_value
                ) / reference_value
            )
        )

    if not percentage_errors:
        return None

    return (
        sum(percentage_errors)
        / len(percentage_errors)
        * 100.0
    )


def _confidence_interval_mean(
    values: Sequence[float],
    confidence: float = 0.95,
) -> tuple[float | None, float | None]:
    """
    Calcula un intervalo bilateral normal para la media.

    Se usa una aproximación normal. Para muestras pequeñas, una versión
    posterior podrá emplear la distribución t de Student mediante scipy.
    """

    if not 0.0 < confidence < 1.0:
        raise ValueError(
            "confidence debe estar entre 0 y 1"
        )

    if len(values) < 2:
        return None, None

    mean_value = _mean(values)
    standard_deviation = _sample_std(values)

    if mean_value is None or standard_deviation is None:
        return None, None

    alpha = 1.0 - confidence
    critical_value = NormalDist().inv_cdf(
        1.0 - alpha / 2.0
    )

    standard_error = (
        standard_deviation / math.sqrt(len(values))
    )

    margin = critical_value * standard_error

    return mean_value - margin, mean_value + margin


def calculate_comparison_metrics(
    reference: Iterable[Any],
    estimated: Iterable[Any],
) -> ComparisonMetrics:
    """
    Calcula un conjunto uniforme de métricas de comparación.

    Parameters
    ----------
    reference:
        Serie observada o de referencia.

    estimated:
        Serie estimada, modelada o satelital.

    Returns
    -------
    ComparisonMetrics
        Resultado consolidado y serializable.
    """

    reference_clean, estimated_clean, n_total = (
        clean_paired_values(reference, estimated)
    )

    n_valid = len(reference_clean)
    n_missing = n_total - n_valid

    missing_percentage = calculate_missing_percentage(
        n_total,
        n_valid,
    )

    if n_valid == 0:
        return ComparisonMetrics(
            n_total=n_total,
            n_valid=0,
            n_missing=n_missing,
            missing_percentage=missing_percentage,
            mae=None,
            rmse=None,
            mbe=None,
            mape=None,
            r_squared=None,
            pearson_r=None,
            spearman_rho=None,
            residual_mean=None,
            residual_std=None,
            residual_ci95_low=None,
            residual_ci95_high=None,
            reference_mean=None,
            estimated_mean=None,
            reference_std=None,
            estimated_std=None,
        )

    residuals = [
        estimated_value - reference_value
        for reference_value, estimated_value in zip(
            reference_clean,
            estimated_clean,
            strict=True,
        )
    ]

    absolute_errors = [
        abs(residual)
        for residual in residuals
    ]

    squared_errors = [
        residual**2
        for residual in residuals
    ]

    mae = sum(absolute_errors) / n_valid
    rmse = math.sqrt(sum(squared_errors) / n_valid)
    mbe = sum(residuals) / n_valid

    residual_ci95_low, residual_ci95_high = (
        _confidence_interval_mean(residuals)
    )

    return ComparisonMetrics(
        n_total=n_total,
        n_valid=n_valid,
        n_missing=n_missing,
        missing_percentage=missing_percentage,
        mae=mae,
        rmse=rmse,
        mbe=mbe,
        mape=_mape(
            reference_clean,
            estimated_clean,
        ),
        r_squared=_r_squared(
            reference_clean,
            estimated_clean,
        ),
        pearson_r=_pearson(
            reference_clean,
            estimated_clean,
        ),
        spearman_rho=_spearman(
            reference_clean,
            estimated_clean,
        ),
        residual_mean=_mean(residuals),
        residual_std=_sample_std(residuals),
        residual_ci95_low=residual_ci95_low,
        residual_ci95_high=residual_ci95_high,
        reference_mean=_mean(reference_clean),
        estimated_mean=_mean(estimated_clean),
        reference_std=_sample_std(reference_clean),
        estimated_std=_sample_std(estimated_clean),
    )
