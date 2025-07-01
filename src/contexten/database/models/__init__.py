"""
Database models for the comprehensive CI/CD system.

This module contains SQLAlchemy models for the 7-module database system:
1. Task DB - Store all task context and execution data
2. Projects DB - Store all project context and repository management  
3. Prompts DB - Store conditional prompt templates
4. Codebase DB - Store comprehensive codebase analysis and metadata
5. Analytics DB - OpenEvolve mechanics to analyze each system step
6. Events DB - Store Linear/Slack/GitHub and deployment events
7. Learning DB - Store patterns and continuous improvement data
"""

from .task import TaskModel, TaskExecutionModel, TaskDependencyModel
from .project import ProjectModel, RepositoryModel, ProjectConfigModel
from .prompt import PromptModel, PromptTemplateModel, PromptConditionModel
from .codebase import CodebaseModel, CodebaseAnalysisModel, CodebaseMetadataModel
from .analytics import AnalyticsModel, AnalyticsEventModel, AnalyticsMetricModel
from .event import EventModel, EventPayloadModel, EventHandlerModel
from .learning import LearningModel, LearningPatternModel, LearningFeedbackModel

# Import base classes for external use
from .base import BaseModel, TimestampMixin, UUIDMixin, MetadataMixin

__all__ = [
    # Base classes
    "BaseModel",
    "TimestampMixin", 
    "UUIDMixin",
    "MetadataMixin",
    
    # Task models
    "TaskModel",
    "TaskExecutionModel", 
    "TaskDependencyModel",
    
    # Project models
    "ProjectModel",
    "RepositoryModel",
    "ProjectConfigModel",
    
    # Prompt models
    "PromptModel",
    "PromptTemplateModel",
    "PromptConditionModel",
    
    # Codebase models
    "CodebaseModel",
    "CodebaseAnalysisModel",
    "CodebaseMetadataModel",
    
    # Analytics models
    "AnalyticsModel",
    "AnalyticsEventModel",
    "AnalyticsMetricModel",
    
    # Event models
    "EventModel",
    "EventPayloadModel",
    "EventHandlerModel",
    
    # Learning models
    "LearningModel",
    "LearningPatternModel",
    "LearningFeedbackModel",
]

