"""
Rain-event detection for the AtmosLink propagation platform.

A rain event is a sequence of rainy observations whose temporal
separation does not exceed a configurable maximum gap.

The module distinguishes between:

1. Event window duration:
   elapsed time between the first and last rainy observation, including
   one nominal sampling interval.

2. Effective rainy duration:
   number of rainy observations multiplied by the nominal sampling
   interval.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import median
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class RainEvent:
    event_id: int

    start_timestamp_utc: str
    end_timestamp_utc: str

    rainy_observation_count: int

    window_duration_minutes: float
    rainy_minutes_equivalent: float
    nominal_sampling_interval_minutes: float

    maximum_rain_rate_mm_h: float
    average_rain_rate_mm_h: float
    maximum_physical_attenuation_db: float

    row_ids: tuple[int, ...]


def parse_timestamp(timestamp: str) -> datetime:
    """
    Parse an ISO-8601 timestamp, including timestamps ending in Z.
    """

    return datetime.fromisoformat(
        timestamp.replace("Z", "+00:00")
    )


def estimate_nominal_sampling_interval_minutes(
    timestamps: list[datetime],
    default_interval_minutes: float = 1.0,
) -> float:
    """
    Estimate the nominal sampling interval using the median positive gap.

    The median is preferred over the minimum because isolated duplicate
    timestamps or irregular records should not redefine the nominal
    acquisition interval.
    """

    if default_interval_minutes <= 0:
        raise ValueError(
            "default_interval_minutes must be greater than zero."
        )

    if len(timestamps) < 2:
        return default_interval_minutes

    sorted_timestamps = sorted(timestamps)

    positive_intervals = [
        (
            sorted_timestamps[index]
            - sorted_timestamps[index - 1]
        ).total_seconds()
        / 60.0
        for index in range(
            1,
            len(sorted_timestamps),
        )
        if (
            sorted_timestamps[index]
            - sorted_timestamps[index - 1]
        ).total_seconds()
        > 0
    ]

    if not positive_intervals:
        return default_interval_minutes

    return float(median(positive_intervals))


def detect_rain_events(
    rows: Iterable[Mapping[str, Any]],
    gap_minutes: float = 10.0,
    rain_threshold_mm_h: float = 0.0,
    default_sampling_interval_minutes: float = 1.0,
) -> list[RainEvent]:
    """
    Detect independent rain events.

    Required row keys
    -----------------
    id
    source_timestamp_utc
    rain_rate_mm_h
    rain_uniform_path_attenuation_db

    Parameters
    ----------
    gap_minutes:
        Maximum temporal separation between consecutive rainy
        observations belonging to the same event.

    rain_threshold_mm_h:
        Minimum rain rate used to classify an observation as rainy.

    default_sampling_interval_minutes:
        Fallback sampling interval when an event contains only one
        observation or no positive timestamp difference can be estimated.
    """

    if gap_minutes <= 0:
        raise ValueError(
            "gap_minutes must be greater than zero."
        )

    if default_sampling_interval_minutes <= 0:
        raise ValueError(
            "default_sampling_interval_minutes must be greater than zero."
        )

    rainy_rows = [
        row
        for row in rows
        if float(
            row["rain_rate_mm_h"]
            or 0.0
        )
        > rain_threshold_mm_h
    ]

    rainy_rows.sort(
        key=lambda row: (
            parse_timestamp(
                str(
                    row[
                        "source_timestamp_utc"
                    ]
                )
            ),
            int(row["id"]),
        )
    )

    if not rainy_rows:
        return []

    maximum_gap_seconds = (
        gap_minutes
        * 60.0
    )

    grouped_rows: list[
        list[Mapping[str, Any]]
    ] = []

    current_group: list[
        Mapping[str, Any]
    ] = []

    previous_timestamp: (
        datetime | None
    ) = None

    for row in rainy_rows:
        current_timestamp = (
            parse_timestamp(
                str(
                    row[
                        "source_timestamp_utc"
                    ]
                )
            )
        )

        is_new_event = (
            previous_timestamp is None
            or (
                current_timestamp
                - previous_timestamp
            ).total_seconds()
            > maximum_gap_seconds
        )

        if (
            is_new_event
            and current_group
        ):
            grouped_rows.append(
                current_group
            )
            current_group = []

        current_group.append(row)
        previous_timestamp = (
            current_timestamp
        )

    if current_group:
        grouped_rows.append(
            current_group
        )

    events: list[RainEvent] = []

    for event_index, event_rows in enumerate(
        grouped_rows,
        start=1,
    ):
        timestamps = [
            parse_timestamp(
                str(
                    row[
                        "source_timestamp_utc"
                    ]
                )
            )
            for row in event_rows
        ]

        rain_rates = [
            float(
                row["rain_rate_mm_h"]
                or 0.0
            )
            for row in event_rows
        ]

        attenuations = [
            float(
                row[
                    "rain_uniform_path_attenuation_db"
                ]
                or 0.0
            )
            for row in event_rows
        ]

        start = min(timestamps)
        end = max(timestamps)

        nominal_interval = (
            estimate_nominal_sampling_interval_minutes(
                timestamps=timestamps,
                default_interval_minutes=(
                    default_sampling_interval_minutes
                ),
            )
        )

        elapsed_minutes = (
            end - start
        ).total_seconds() / 60.0

        window_duration_minutes = (
            elapsed_minutes
            + nominal_interval
        )

        rainy_observation_count = len(
            event_rows
        )

        rainy_minutes_equivalent = (
            rainy_observation_count
            * nominal_interval
        )

        events.append(
            RainEvent(
                event_id=event_index,

                start_timestamp_utc=(
                    start.isoformat()
                ),

                end_timestamp_utc=(
                    end.isoformat()
                ),

                rainy_observation_count=(
                    rainy_observation_count
                ),

                window_duration_minutes=(
                    window_duration_minutes
                ),

                rainy_minutes_equivalent=(
                    rainy_minutes_equivalent
                ),

                nominal_sampling_interval_minutes=(
                    nominal_interval
                ),

                maximum_rain_rate_mm_h=max(
                    rain_rates
                ),

                average_rain_rate_mm_h=(
                    sum(rain_rates)
                    / len(rain_rates)
                ),

                maximum_physical_attenuation_db=max(
                    attenuations
                ),

                row_ids=tuple(
                    int(row["id"])
                    for row in event_rows
                ),
            )
        )

    return events


def build_event_membership(
    events: Iterable[RainEvent],
) -> dict[int, int]:
    """
    Return a mapping from propagation-observation ID to event ID.
    """

    membership: dict[int, int] = {}

    for event in events:
        for row_id in event.row_ids:
            if row_id in membership:
                raise RuntimeError(
                    f"Row {row_id} belongs "
                    "to more than one event."
                )

            membership[row_id] = (
                event.event_id
            )

    return membership
