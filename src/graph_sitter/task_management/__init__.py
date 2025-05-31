"""
Advanced Task Management System for Graph-Sitter Integration

This module provides comprehensive task management capabilities with advanced workflow
orchestration, integrating with Codegen SDK, Graph-Sitter, and Contexten.

Core Components:
- Task System Architecture: Advanced task creation, scheduling, and execution
- Workflow Management: Sophisticated workflow orchestration and dependencies
- Integration Layer: Seamless integration with external systems
- Performance Optimization: High-performance task execution and monitoring
- Evaluation System: Effectiveness tracking and analytics
"""

from .core import TaskManager, Task, TaskStatus, TaskPriority
from .workflow import WorkflowOrchestrator, WorkflowEngine, Workflow
from .integration import CodegenIntegration, GraphSitterIntegration, ContextenIntegration
from .performance import PerformanceMonitor, ResourceOptimizer, MetricsCollector
from .evaluation import EvaluationSystem, EffectivenessTracker, AnalyticsEngine

__all__ = [
    # Core Task Management
    "TaskManager",
    "Task", 
    "TaskStatus",
    "TaskPriority",
    
    # Workflow Management
    "WorkflowOrchestrator",
    "WorkflowEngine", 
    "Workflow",
    
    # Integration Layer
    "CodegenIntegration",
    "GraphSitterIntegration",
    "ContextenIntegration",
    
    # Performance Optimization
    "PerformanceMonitor",
    "ResourceOptimizer",
    "MetricsCollector",
    
    # Evaluation System
    "EvaluationSystem",
    "EffectivenessTracker",
    "AnalyticsEngine",
]

__version__ = "1.0.0"

