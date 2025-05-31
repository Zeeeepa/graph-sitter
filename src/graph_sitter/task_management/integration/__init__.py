"""
Integration Layer for Task Management System

Provides seamless integration with external systems including:
- Codegen SDK for AI agent interactions
- Graph-Sitter for code analysis and manipulation
- Contexten for event-driven orchestration
"""

from .codegen_integration import CodegenIntegration, CodegenTaskHandler
from .graph_sitter_integration import GraphSitterIntegration, AnalysisTaskHandler
from .contexten_integration import ContextenIntegration, EventDrivenTaskHandler
from .base import IntegrationBase, IntegrationConfig, IntegrationStatus

__all__ = [
    "CodegenIntegration",
    "CodegenTaskHandler",
    "GraphSitterIntegration", 
    "AnalysisTaskHandler",
    "ContextenIntegration",
    "EventDrivenTaskHandler",
    "IntegrationBase",
    "IntegrationConfig",
    "IntegrationStatus",
]

