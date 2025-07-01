"""
Contexten - Enhanced CI/CD Orchestrator

This module provides the main Contexten orchestrator with comprehensive
CI/CD capabilities, continuous learning, and platform integrations.
"""

from .core import ContextenOrchestrator, SystemConfig, SystemStatus
from .client import ContextenClient, ClientConfig, AnalysisRequest, WorkflowRequest, BatchRequest
from .integrations import UnifiedAPI, APIRequest, APIResponse, DatabaseConfig
from .learning import (
    PatternRecognitionEngine, PerformanceTracker, AdaptationEngine,
    Pattern, PatternType, DataPoint, MetricPoint, MetricType
)

__version__ = "1.0.0"
__all__ = [
    # Core Orchestrator
    "ContextenOrchestrator",
    "SystemConfig", 
    "SystemStatus",
    
    # Client Interface
    "ContextenClient",
    "ClientConfig",
    "AnalysisRequest",
    "WorkflowRequest", 
    "BatchRequest",
    
    # Unified API
    "UnifiedAPI",
    "APIRequest",
    "APIResponse",
    "DatabaseConfig",
    
    # Learning System
    "PatternRecognitionEngine",
    "PerformanceTracker", 
    "AdaptationEngine",
    "Pattern",
    "PatternType",
    "DataPoint",
    "MetricPoint",
    "MetricType"
]

