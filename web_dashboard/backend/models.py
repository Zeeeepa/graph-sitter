"""
Database Models for Web-Eval-Agent Dashboard

SQLAlchemy ORM models and Pydantic models for API requests/responses.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import uuid

from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from typing import Any

# SQLAlchemy Base with proper typing
Base: DeclarativeMeta = declarative_base()


# SQLAlchemy ORM Models

class ProjectORM(Base):  # type: ignore[misc]
    """SQLAlchemy Project model."""
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    github_owner = Column(String(255), nullable=False)
    github_repo = Column(String(255), nullable=False)
    webhook_url = Column(String(500), nullable=True)
    webhook_id = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="active")
    user_id = Column(String(255), nullable=False)
    settings = Column(JSON, nullable=True, default={})
    last_activity = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agent_runs = relationship("AgentRunORM", back_populates="project")
    webhook_events = relationship("WebhookEventORM", back_populates="project")
    validation_results = relationship("ValidationResultORM", back_populates="project")


class AgentRunORM(Base):  # type: ignore[misc]
    """SQLAlchemy AgentRun model."""
    __tablename__ = "agent_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    target_text = Column(Text, nullable=False)
    auto_confirm_plan = Column(Boolean, nullable=False, default=False)
    status = Column(String(50), nullable=False, default="pending")
    session_id = Column(String(255), nullable=True)
    response_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("ProjectORM", back_populates="agent_runs")


class WebhookEventORM(Base):  # type: ignore[misc]
    """SQLAlchemy WebhookEvent model."""
    __tablename__ = "webhook_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    processed = Column(Boolean, nullable=False, default=False)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("ProjectORM", back_populates="webhook_events")


class ValidationResultORM(Base):  # type: ignore[misc]
    """SQLAlchemy ValidationResult model."""
    __tablename__ = "validation_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    pr_number = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    success = Column(Boolean, nullable=False, default=False)
    message = Column(Text, nullable=True)
    logs = Column(JSON, nullable=True, default=[])
    deployment_logs = Column(JSON, nullable=True, default=[])
    test_results = Column(JSON, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("ProjectORM", back_populates="validation_results")


class UserORM(Base):  # type: ignore[misc]
    """SQLAlchemy User model."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProjectStatus(str, Enum):
    """Project status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AgentRunStatus(str, Enum):
    """Agent run status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResponseType(str, Enum):
    """Agent response type enumeration."""
    REGULAR = "regular"
    PLAN = "plan"
    PR = "pr"


class ValidationStatus(str, Enum):
    """Validation status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Base Models

class BaseEntity(BaseModel):
    """Base entity with common fields."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Project Models

class ProjectSettings(BaseModel):
    """Project-specific settings."""
    repository_rules: Optional[str] = Field(None, description="Additional repository rules")
    setup_commands: Optional[str] = Field(None, description="Setup commands for deployment")
    planning_statement: Optional[str] = Field(None, description="Custom planning statement")
    auto_confirm_plan: bool = Field(default=False, description="Auto-confirm proposed plans")
    auto_merge_validated_pr: bool = Field(default=False, description="Auto-merge validated PRs")
    branch: Optional[str] = Field(default="main", description="Default branch to work with")
    secrets: Dict[str, str] = Field(default_factory=dict, description="Environment variables/secrets")


class ProjectBase(BaseModel):
    """Base project model."""
    name: str = Field(..., description="Project display name")
    description: Optional[str] = Field(None, description="Project description")
    github_owner: str = Field(..., description="GitHub repository owner")
    github_repo: str = Field(..., description="GitHub repository name")
    webhook_url: Optional[str] = Field(None, description="Webhook URL from Cloudflare")
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE)
    settings: ProjectSettings = Field(default_factory=ProjectSettings)


class ProjectCreate(ProjectBase):
    """Model for creating a new project."""
    pass


class ProjectUpdate(BaseModel):
    """Model for updating a project."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    settings: Optional[ProjectSettings] = None


class Project(BaseEntity, ProjectBase):
    """Complete project model."""
    user_id: str = Field(..., description="Owner user ID")
    webhook_id: Optional[str] = Field(None, description="GitHub webhook ID")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    
    class Config:
        from_attributes = True


# Agent Run Models

class AgentRunBase(BaseModel):
    """Base agent run model."""
    target_text: str = Field(..., description="Target goal for the agent run")
    auto_confirm_plan: bool = Field(default=False, description="Auto-confirm proposed plans")
    status: AgentRunStatus = Field(default=AgentRunStatus.PENDING)


class AgentRunCreate(AgentRunBase):
    """Model for creating a new agent run."""
    project_id: str = Field(..., description="Associated project ID")


class AgentRunUpdate(BaseModel):
    """Model for updating an agent run."""
    status: Optional[AgentRunStatus] = None
    session_id: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class AgentRun(BaseEntity, AgentRunBase):
    """Complete agent run model."""
    project_id: str = Field(..., description="Associated project ID")
    session_id: Optional[str] = Field(None, description="Codegen API session ID")
    response_data: Optional[Dict[str, Any]] = Field(None, description="Latest response data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    class Config:
        from_attributes = True


# Agent Response Models

class AgentResponse(BaseModel):
    """Agent response model."""
    type: ResponseType
    content: str
    plan: Optional[Dict[str, Any]] = None
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Webhook Models

class WebhookEventBase(BaseModel):
    """Base webhook event model."""
    event_type: str = Field(..., description="GitHub event type")
    payload: Dict[str, Any] = Field(..., description="Event payload")
    processed: bool = Field(default=False)


class WebhookEventCreate(WebhookEventBase):
    """Model for creating a webhook event."""
    project_id: str = Field(..., description="Associated project ID")


class WebhookEvent(BaseEntity, WebhookEventBase):
    """Complete webhook event model."""
    project_id: str = Field(..., description="Associated project ID")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    
    class Config:
        from_attributes = True


# Validation Models

class ValidationResultBase(BaseModel):
    """Base validation result model."""
    pr_number: int = Field(..., description="Pull request number")
    status: ValidationStatus = Field(default=ValidationStatus.PENDING)
    success: bool = Field(default=False)
    message: Optional[str] = Field(None, description="Validation message")
    logs: List[str] = Field(default_factory=list, description="Validation logs")
    deployment_logs: List[str] = Field(default_factory=list, description="Deployment logs")
    test_results: Optional[Dict[str, Any]] = Field(None, description="Test execution results")


class ValidationResultCreate(ValidationResultBase):
    """Model for creating a validation result."""
    project_id: str = Field(..., description="Associated project ID")


class ValidationResult(BaseEntity, ValidationResultBase):
    """Complete validation result model."""
    project_id: str = Field(..., description="Associated project ID")
    started_at: Optional[datetime] = Field(None, description="Validation start time")
    completed_at: Optional[datetime] = Field(None, description="Validation completion time")
    
    class Config:
        from_attributes = True


# User Models

class UserBase(BaseModel):
    """Base user model."""
    email: str = Field(..., description="User email address")
    name: Optional[str] = Field(None, description="User display name")
    is_active: bool = Field(default=True)


class UserCreate(UserBase):
    """Model for creating a new user."""
    password: str = Field(..., description="User password")


class User(BaseEntity, UserBase):
    """Complete user model."""
    hashed_password: str = Field(..., description="Hashed password")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class Config:
        from_attributes = True


# API Response Models

class ProjectListResponse(BaseModel):
    """Response model for project list."""
    projects: List[Project]
    total: int


class AgentRunListResponse(BaseModel):
    """Response model for agent run list."""
    runs: List[AgentRun]
    total: int


class ValidationResultListResponse(BaseModel):
    """Response model for validation result list."""
    results: List[ValidationResult]
    total: int


# WebSocket Message Models

class WebSocketMessage(BaseModel):
    """Base WebSocket message model."""
    type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)


class ProjectUpdateMessage(WebSocketMessage):
    """Project update WebSocket message."""
    type: str = "project_updated"
    project: Project


class AgentRunStatusMessage(WebSocketMessage):
    """Agent run status WebSocket message."""
    type: str = "agent_run_status"
    run_id: str
    status: AgentRunStatus
    message: Optional[str] = None


class AgentRunResponseMessage(WebSocketMessage):
    """Agent run response WebSocket message."""
    type: str = "agent_run_response"
    run_id: str
    response_type: ResponseType
    content: str
    can_continue: bool = False
    can_confirm: bool = False
    can_modify: bool = False
    can_validate: bool = False
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None


class ValidationStatusMessage(WebSocketMessage):
    """Validation status WebSocket message."""
    type: str = "validation_status"
    project_id: str
    pr_number: int
    status: ValidationStatus
    message: Optional[str] = None
    success: Optional[bool] = None


# Configuration Models

class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = Field(..., description="Database connection URL")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max pool overflow")
    echo: bool = Field(default=False, description="Echo SQL queries")


class GitHubConfig(BaseModel):
    """GitHub integration configuration."""
    token: str = Field(..., description="GitHub personal access token")
    webhook_secret: str = Field(..., description="Webhook secret for signature verification")
    app_id: Optional[str] = Field(None, description="GitHub App ID if using app authentication")
    private_key: Optional[str] = Field(None, description="GitHub App private key")


class CodegenConfig(BaseModel):
    """Codegen API configuration."""
    api_key: str = Field(..., description="Codegen API key")
    org_id: str = Field(..., description="Codegen organization ID")
    base_url: str = Field(default="https://api.codegen.com", description="API base URL")
    timeout: int = Field(default=300, description="Request timeout in seconds")


class ValidationConfig(BaseModel):
    """Validation pipeline configuration."""
    docker_image: str = Field(default="node:18-alpine", description="Base Docker image for validation")
    timeout: int = Field(default=1800, description="Validation timeout in seconds")
    max_concurrent: int = Field(default=3, description="Max concurrent validations")
    cleanup_after: int = Field(default=3600, description="Cleanup containers after seconds")


class AppConfig(BaseModel):
    """Application configuration."""
    debug: bool = Field(default=False)
    secret_key: str = Field(..., description="Application secret key")
    webhook_base_url: str = Field(..., description="Base URL for webhooks")
    cors_origins: List[str] = Field(default_factory=list, description="CORS allowed origins")
    
    database: DatabaseConfig
    github: GitHubConfig
    codegen: CodegenConfig
    validation: ValidationConfig


# Tree Structure Models (for project file tree)

class FileNode(BaseModel):
    """File tree node model."""
    name: str = Field(..., description="File/directory name")
    path: str = Field(..., description="Full path")
    type: str = Field(..., description="Type: file or directory")
    size: Optional[int] = Field(None, description="File size in bytes")
    children: Optional[List['FileNode']] = Field(None, description="Child nodes for directories")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Code errors/issues")
    has_errors: bool = Field(default=False, description="Whether this node has errors")


# Update forward references
FileNode.model_rebuild()


# Error Models

class CodeError(BaseModel):
    """Code error/issue model."""
    file_path: str = Field(..., description="File path where error occurs")
    line: int = Field(..., description="Line number")
    column: int = Field(..., description="Column number")
    severity: str = Field(..., description="Error severity: error, warning, info")
    message: str = Field(..., description="Error message")
    rule: Optional[str] = Field(None, description="Rule or check that triggered the error")
    source: str = Field(..., description="Source of the error: linter, type-checker, etc.")


class ProjectAnalysis(BaseModel):
    """Project analysis result model."""
    project_id: str = Field(..., description="Associated project ID")
    total_files: int = Field(..., description="Total number of files analyzed")
    files_with_errors: int = Field(..., description="Number of files with errors")
    total_errors: int = Field(..., description="Total number of errors")
    errors_by_severity: Dict[str, int] = Field(default_factory=dict, description="Error count by severity")
    errors_by_type: Dict[str, int] = Field(default_factory=dict, description="Error count by type")
    file_tree: FileNode = Field(..., description="File tree with error annotations")
    analysis_duration: float = Field(..., description="Analysis duration in seconds")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
