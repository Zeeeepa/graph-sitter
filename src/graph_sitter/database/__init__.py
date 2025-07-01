"""
Graph-Sitter Database Module

Comprehensive database integration for the graph-sitter codebase analysis system.
Provides SQLAlchemy models, connection management, and integration adapters for
the 7-module database schema supporting:

1. Organizations & Users - Multi-tenant foundation
2. Projects & Repositories - Project management and repository tracking  
3. Tasks & Workflows - Task lifecycle and workflow orchestration
4. Analytics & Codebase Analysis - Analysis results and metrics storage
5. Prompts & Templates - Dynamic prompt management
6. Events & Integrations - Event tracking for Linear, GitHub, Slack
7. Learning & OpenEvolve - Continuous learning and system improvement

This module integrates seamlessly with existing graph_sitter.codebase.codebase_analysis
functionality while providing enhanced database persistence and analytics capabilities.
"""

from .config import DatabaseConfig, get_database_config
from .connection import DatabaseConnection, get_database_session
from .base import BaseModel, TimestampMixin, SoftDeleteMixin

# Import all models for easy access
from .models.organizations import Organization, User, OrganizationMembership
from .models.projects import Project, Repository, RepositoryBranch
from .models.tasks import Task, TaskDefinition, Workflow, TaskDependency
from .models.analytics import AnalysisRun, FileAnalysis, CodeElementAnalysis, Metric
from .models.prompts import PromptTemplate, PromptExecution, ContextSource
from .models.events import Event, EventAggregation, LinearEvent, GitHubEvent
from .models.learning import LearningPattern, SystemOptimization, OpenEvolveRun

__version__ = "1.0.0"

__all__ = [
    # Configuration and connection
    "DatabaseConfig",
    "get_database_config", 
    "DatabaseConnection",
    "get_database_session",
    
    # Base classes
    "BaseModel",
    "TimestampMixin", 
    "SoftDeleteMixin",
    
    # Organizations & Users
    "Organization",
    "User",
    "OrganizationMembership",
    
    # Projects & Repositories
    "Project",
    "Repository", 
    "RepositoryBranch",
    
    # Tasks & Workflows
    "Task",
    "TaskDefinition",
    "Workflow",
    "TaskDependency",
    
    # Analytics & Codebase Analysis
    "AnalysisRun",
    "FileAnalysis",
    "CodeElementAnalysis", 
    "Metric",
    
    # Prompts & Templates
    "PromptTemplate",
    "PromptExecution",
    "ContextSource",
    
    # Events & Integrations
    "Event",
    "EventAggregation",
    "LinearEvent",
    "GitHubEvent",
    
    # Learning & OpenEvolve
    "LearningPattern",
    "SystemOptimization",
    "OpenEvolveRun",
]

