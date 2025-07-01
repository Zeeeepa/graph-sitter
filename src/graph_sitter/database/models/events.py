"""
Events and Integrations Models

Event tracking and processing models for Linear, GitHub, Slack,
and deployment integrations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, UniqueConstraint, Index, Text
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship, Session

from ..base import DatabaseModel, AuditedModel, StatusMixin


# Define enums (already created in extensions.sql)
EVENT_SOURCE_ENUM = ENUM(
    'linear', 'slack', 'github', 'deployment', 'system', 'openevolve',
    'analytics', 'task_engine', 'workflow', 'custom',
    name='event_source',
    create_type=False
)

EVENT_TYPE_ENUM = ENUM(
    'issue_created', 'issue_updated', 'issue_closed', 'comment_added',
    'pr_opened', 'pr_merged', 'pr_closed', 'commit_pushed',
    'deployment_started', 'deployment_completed', 'deployment_failed',
    'task_created', 'task_started', 'task_completed', 'task_failed',
    'evaluation_started', 'evaluation_completed', 'workflow_triggered',
    'system_alert', 'custom_event',
    name='event_type',
    create_type=False
)


class Event(DatabaseModel, AuditedModel, StatusMixin):
    """
    Universal event storage for all integration sources.
    
    Stores events from various sources (Linear, GitHub, Slack, etc.)
    with flexible payload storage and processing tracking.
    """
    __tablename__ = 'events'
    
    # Organization relationship
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    
    # Event identification
    source = Column(EVENT_SOURCE_ENUM, nullable=False)
    type = Column(EVENT_TYPE_ENUM, nullable=False)
    
    # Event associations
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='SET NULL'), nullable=True)
    repository_id = Column(UUID(as_uuid=True), ForeignKey('repositories.id', ondelete='SET NULL'), nullable=True)
    
    # External references
    external_id = Column(String(255), nullable=True, index=True)
    external_url = Column(Text, nullable=True)
    
    # Event content
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    event_data = Column('event_data', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Actor information
    actor_id = Column(String(255), nullable=True, index=True)
    actor_name = Column(String(255), nullable=True)
    actor_email = Column(String(255), nullable=True)
    
    # Timing and processing
    occurred_at = Column('occurred_at', DatabaseModel.created_at.type, nullable=False)
    processed_at = Column('processed_at', DatabaseModel.created_at.type, nullable=True)
    
    # Event metadata and tags
    tags = Column('tags', DatabaseModel.metadata.type, nullable=False, default=list)
    
    # Relationships
    organization = relationship("Organization")
    project = relationship("Project")
    repository = relationship("Repository")
    
    # Constraints
    __table_args__ = (
        Index('idx_events_org', 'organization_id'),
        Index('idx_events_source_type', 'source', 'type'),
        Index('idx_events_project', 'project_id'),
        Index('idx_events_repository', 'repository_id'),
        Index('idx_events_external_id', 'external_id'),
        Index('idx_events_actor', 'actor_id'),
        Index('idx_events_occurred_at', 'occurred_at'),
        Index('idx_events_processed_at', 'processed_at'),
        Index('idx_events_status', 'status'),
        Index('idx_events_event_data_gin', 'event_data', postgresql_using='gin'),
        Index('idx_events_tags_gin', 'tags', postgresql_using='gin'),
    )
    
    def __init__(self, organization_id: str, source: str, type: str, **kwargs):
        """Initialize event with required fields."""
        super().__init__(
            organization_id=organization_id,
            source=source,
            type=type,
            occurred_at=kwargs.pop('occurred_at', datetime.utcnow()),
            **kwargs
        )
    
    def mark_processed(self) -> None:
        """Mark event as processed."""
        self.processed_at = datetime.utcnow()
        self.status = 'completed'
    
    def get_event_summary(self) -> Dict[str, Any]:
        """Get event summary information."""
        return {
            'id': str(self.id),
            'source': self.source,
            'type': self.type,
            'title': self.title,
            'external_id': self.external_id,
            'external_url': self.external_url,
            'actor_name': self.actor_name,
            'actor_email': self.actor_email,
            'project_id': str(self.project_id) if self.project_id else None,
            'repository_id': str(self.repository_id) if self.repository_id else None,
            'occurred_at': self.occurred_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'status': self.status,
            'tags': self.tags,
        }


class EventAggregation(DatabaseModel, AuditedModel):
    """
    Event aggregations for analytics and reporting.
    
    Stores pre-computed event aggregations for performance
    and analytics dashboard support.
    """
    __tablename__ = 'event_aggregations'
    
    # Organization relationship
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    
    # Aggregation scope
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=True)
    repository_id = Column(UUID(as_uuid=True), ForeignKey('repositories.id', ondelete='CASCADE'), nullable=True)
    
    # Aggregation metadata
    aggregation_type = Column(String(100), nullable=False)  # daily, weekly, monthly
    period_start = Column('period_start', DatabaseModel.created_at.type, nullable=False)
    period_end = Column('period_end', DatabaseModel.created_at.type, nullable=False)
    
    # Aggregated data
    event_counts = Column('event_counts', DatabaseModel.metadata.type, nullable=False, default=dict)
    metrics = Column('metrics', DatabaseModel.metadata.type, nullable=False, default=dict)
    summary = Column('summary', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Relationships
    organization = relationship("Organization")
    project = relationship("Project")
    repository = relationship("Repository")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'project_id', 'repository_id', 'aggregation_type', 'period_start', 
                        name='uq_event_aggregation'),
        Index('idx_event_aggregations_org', 'organization_id'),
        Index('idx_event_aggregations_project', 'project_id'),
        Index('idx_event_aggregations_repository', 'repository_id'),
        Index('idx_event_aggregations_type', 'aggregation_type'),
        Index('idx_event_aggregations_period', 'period_start', 'period_end'),
    )
    
    def __init__(self, organization_id: str, aggregation_type: str, period_start: datetime, period_end: datetime, **kwargs):
        """Initialize event aggregation with required fields."""
        super().__init__(
            organization_id=organization_id,
            aggregation_type=aggregation_type,
            period_start=period_start,
            period_end=period_end,
            **kwargs
        )


class LinearEvent(DatabaseModel, AuditedModel):
    """
    Linear-specific event data and processing.
    
    Stores Linear-specific event data with issue and project
    context for enhanced Linear integration.
    """
    __tablename__ = 'linear_events'
    
    # Event relationship
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    
    # Linear-specific data
    linear_issue_id = Column(String(255), nullable=True, index=True)
    linear_project_id = Column(String(255), nullable=True, index=True)
    linear_team_id = Column(String(255), nullable=True, index=True)
    linear_user_id = Column(String(255), nullable=True, index=True)
    
    # Issue details
    issue_number = Column(Integer, nullable=True)
    issue_title = Column(String(500), nullable=True)
    issue_state = Column(String(100), nullable=True)
    issue_priority = Column(Integer, nullable=True)
    
    # Linear-specific metadata
    linear_data = Column('linear_data', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Relationships
    event = relationship("Event")
    
    # Constraints
    __table_args__ = (
        Index('idx_linear_events_event', 'event_id'),
        Index('idx_linear_events_issue', 'linear_issue_id'),
        Index('idx_linear_events_project', 'linear_project_id'),
        Index('idx_linear_events_team', 'linear_team_id'),
        Index('idx_linear_events_user', 'linear_user_id'),
        Index('idx_linear_events_issue_number', 'issue_number'),
    )
    
    def __init__(self, event_id: str, **kwargs):
        """Initialize Linear event with required fields."""
        super().__init__(event_id=event_id, **kwargs)


class GitHubEvent(DatabaseModel, AuditedModel):
    """
    GitHub-specific event data and processing.
    
    Stores GitHub-specific event data with repository and PR
    context for enhanced GitHub integration.
    """
    __tablename__ = 'github_events'
    
    # Event relationship
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    
    # GitHub-specific data
    github_repo_id = Column(Integer, nullable=True, index=True)
    github_user_id = Column(Integer, nullable=True, index=True)
    github_pr_number = Column(Integer, nullable=True, index=True)
    github_issue_number = Column(Integer, nullable=True, index=True)
    
    # Repository details
    repo_full_name = Column(String(255), nullable=True)
    repo_owner = Column(String(255), nullable=True)
    repo_name = Column(String(255), nullable=True)
    
    # PR/Issue details
    pr_title = Column(String(500), nullable=True)
    pr_state = Column(String(100), nullable=True)
    pr_merged = Column(Boolean, nullable=True)
    
    # Commit details
    commit_sha = Column(String(40), nullable=True, index=True)
    commit_message = Column(Text, nullable=True)
    
    # GitHub-specific metadata
    github_data = Column('github_data', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Relationships
    event = relationship("Event")
    
    # Constraints
    __table_args__ = (
        Index('idx_github_events_event', 'event_id'),
        Index('idx_github_events_repo', 'github_repo_id'),
        Index('idx_github_events_user', 'github_user_id'),
        Index('idx_github_events_pr', 'github_pr_number'),
        Index('idx_github_events_issue', 'github_issue_number'),
        Index('idx_github_events_commit', 'commit_sha'),
        Index('idx_github_events_repo_name', 'repo_full_name'),
    )
    
    def __init__(self, event_id: str, **kwargs):
        """Initialize GitHub event with required fields."""
        super().__init__(event_id=event_id, **kwargs)

