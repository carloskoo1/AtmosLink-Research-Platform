"""
AtmosLink Scientific Engine.

Herramientas para análisis estadístico, validación científica,
evaluación de modelos y generación de productos reproducibles.
"""

from weather_station.analysis.metrics import (
    ComparisonMetrics,
    calculate_comparison_metrics,
    calculate_missing_percentage,
    clean_paired_values,
)

__all__ = [
    "ComparisonMetrics",
    "calculate_comparison_metrics",
    "calculate_missing_percentage",
    "clean_paired_values",
]

__version__ = "1.0.0"
