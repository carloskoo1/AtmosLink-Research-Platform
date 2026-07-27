# AtmosLink Design System

## Version 1.0

AtmosLink Design System defines the visual, semantic and interaction
standards for the AtmosLink Research Platform user interface.

## Design principles

1. Scientific clarity.
2. Operational readability.
3. Semantic consistency.
4. Reproducible presentation.
5. Accessibility.
6. Modular implementation.

## Theme

AtmosLink uses a single scientific light theme for operational monitoring,
technical documentation, presentations and scientific publications.

## Semantic states

| State | Meaning |
|---|---|
| HEALTHY / ACTIVE / FRESH / AVAILABLE | Normal operation |
| WARNING / WAITING / STALE / DELAYED | Attention required |
| ERROR / CRITICAL / FAILED / OFFLINE | Immediate action required |
| DISABLED / NOT INSTALLED / NOT ENABLED | Function unavailable by design |

## Main modules

- Executive Dashboard
- Scientific Observatory
- Meteorology
- Radio Link
- Scientific Analytics
- Timeline
- System
- Configuration

## Versioning

The user interface is developed independently from the scientific backend.
UI changes must not alter acquisition, synchronization, quality-control or
scientific-processing logic.
