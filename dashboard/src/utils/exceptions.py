"""
Custom Exception Classes

Defines custom exceptions for better error handling and user feedback.
"""


class DashboardError(Exception):
    """Base exception for dashboard-related errors."""
    pass


class APIError(DashboardError):
    """Exception raised for API-related errors."""
    pass


class NetworkError(DashboardError):
    """Exception raised for network-related errors."""
    pass


class ValidationError(DashboardError):
    """Exception raised for validation errors."""
    pass


class AnalysisError(DashboardError):
    """Exception raised for analysis-related errors."""
    pass


class ConfigurationError(DashboardError):
    """Exception raised for configuration-related errors."""
    pass

