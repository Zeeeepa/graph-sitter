"""
Task Management API Layer

Provides RESTful API endpoints and interfaces for the task management system,
enabling external access and integration with web interfaces and other systems.
"""

from .rest_api import TaskManagementAPI, APIConfig
from .endpoints import TaskEndpoints, WorkflowEndpoints, MetricsEndpoints
from .models import TaskRequest, TaskResponse, WorkflowRequest, WorkflowResponse
from .auth import APIAuthentication, APIAuthorization
from .middleware import RequestLogging, RateLimiting, ErrorHandling

__all__ = [
    "TaskManagementAPI",
    "APIConfig",
    "TaskEndpoints",
    "WorkflowEndpoints", 
    "MetricsEndpoints",
    "TaskRequest",
    "TaskResponse",
    "WorkflowRequest",
    "WorkflowResponse",
    "APIAuthentication",
    "APIAuthorization",
    "RequestLogging",
    "RateLimiting",
    "ErrorHandling",
]

