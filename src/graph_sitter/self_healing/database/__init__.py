"""
Database module for self-healing architecture.
"""

from .schema import create_tables, get_database_url
from .models import ErrorIncident, RecoveryProcedure, SystemHealthMetric

__all__ = [
    "create_tables",
    "get_database_url", 
    "ErrorIncident",
    "RecoveryProcedure",
    "SystemHealthMetric",
]

