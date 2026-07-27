"""
AtmosLink Campaign Engine.

Herramientas para inspección, sincronización y análisis reproducible
de campañas meteorológicas y de radioenlaces.
"""

from weather_station.campaign.inspection import (
    ColumnProfile,
    DatabaseProfile,
    TableProfile,
    inspect_sqlite_database,
    profile_to_dict,
)

__all__ = [
    "ColumnProfile",
    "DatabaseProfile",
    "TableProfile",
    "inspect_sqlite_database",
    "profile_to_dict",
]

__version__ = "1.0.0"
