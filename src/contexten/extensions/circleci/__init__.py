"""
CircleCI Extension for Contexten

Comprehensive CircleCI integration providing:
- Real-time build monitoring via webhooks
- Intelligent failure analysis and root cause detection
- Automatic fix generation using Codegen SDK
- Seamless GitHub integration for PR updates
- Workflow automation and task orchestration

This extension follows the established contexten extension patterns
and integrates deeply with graph-sitter for code analysis.
"""

from .config import CircleCIIntegrationConfig
from .types import (
    CircleCIBuild,
    CircleCIWorkflow,
    CircleCIJob,
    CircleCIEvent,
    CircleCIEventType,
    BuildStatus,
    FailureAnalysis,
    CircleCIIntegrationMetrics,
)
from .client import CircleCIClient
from .webhook_processor import WebhookProcessor
from .workflow_automation import WorkflowAutomation
from .integration_agent import CircleCIIntegrationAgent
from .failure_analyzer import FailureAnalyzer
from .auto_fix_generator import AutoFixGenerator
from .circleci import CircleCI

__version__ = "1.0.0"
__author__ = "Contexten Team"

__all__ = [
    "CircleCI",  # Add main integration class
    "CircleCIIntegrationConfig",
    
    # API and processing
    "CircleCIClient",
    "WebhookProcessor",
    "WorkflowAutomation",
    "FailureAnalyzer",
    "AutoFixGenerator",
    
    # Data models
    "CircleCIBuild",
    "CircleCIWorkflow",
    "CircleCIJob",
    "CircleCIEvent",
    "CircleCIEventType",
    "BuildStatus",
    "FailureAnalysis",
    "CircleCIIntegrationMetrics",
]
