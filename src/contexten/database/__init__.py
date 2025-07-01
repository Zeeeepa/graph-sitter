"""
Database module for the comprehensive CI/CD system.

This module provides database connectivity and ORM models for the 7-module database system:
1. Task DB - Store all task context and execution data
2. Projects DB - Store all project context and repository management
3. Prompts DB - Store conditional prompt templates
4. Codebase DB - Store comprehensive codebase analysis and metadata
5. Analytics DB - OpenEvolve mechanics to analyze each system step
6. Events DB - Store Linear/Slack/GitHub and deployment events
7. Learning DB - Store patterns and continuous improvement data
"""

from .connection import DatabaseManager, get_database_manager
from .models import (
    TaskModel,
    ProjectModel,
    PromptModel,
    CodebaseModel,
    AnalyticsModel,
    EventModel,
    LearningModel,
)

__all__ = [
    "DatabaseManager",
    "get_database_manager",
    "TaskModel",
    "ProjectModel", 
    "PromptModel",
    "CodebaseModel",
    "AnalyticsModel",
    "EventModel",
    "LearningModel",
]

