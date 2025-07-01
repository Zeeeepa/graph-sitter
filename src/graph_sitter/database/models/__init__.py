"""
Database Models Package

Contains all SQLAlchemy models for the 7-module database schema:
1. Organizations & Users
2. Projects & Repositories  
3. Tasks & Workflows
4. Analytics & Codebase Analysis
5. Prompts & Templates
6. Events & Integrations
7. Learning & OpenEvolve
"""

# Import all models for easy access
from .organizations import Organization, User, OrganizationMembership
from .projects import Project, Repository, RepositoryBranch
from .tasks import Task, TaskDefinition, Workflow, TaskDependency
from .analytics import AnalysisRun, FileAnalysis, CodeElementAnalysis, Metric
from .prompts import PromptTemplate, PromptExecution, ContextSource
from .events import Event, EventAggregation, LinearEvent, GitHubEvent
from .learning import LearningPattern, SystemOptimization, OpenEvolveRun

__all__ = [
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

