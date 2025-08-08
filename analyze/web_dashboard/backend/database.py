"""
Database Layer for Web-Eval-Agent Dashboard

SQLAlchemy database models and operations.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

import asyncpg
from sqlalchemy import (
    Column, String, DateTime, Boolean, Integer, Text, JSON,
    ForeignKey, Index, UniqueConstraint, create_engine
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.sql import select, update, delete
from sqlalchemy.dialects.postgresql import UUID
import uuid

from models import (
    Project as ProjectModel, ProjectCreate, ProjectUpdate,
    AgentRun as AgentRunModel, AgentRunCreate, AgentRunUpdate,
    WebhookEvent as WebhookEventModel, WebhookEventCreate,
    ValidationResult as ValidationResultModel, ValidationResultCreate,
    User as UserModel, UserCreate,
    ProjectStatus, AgentRunStatus, ValidationStatus
)

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()


# Database Tables

class User(Base):
    """User table."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    """Project table."""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    github_owner = Column(String, nullable=False)
    github_repo = Column(String, nullable=False)
    webhook_url = Column(String)
    webhook_id = Column(String)
    status = Column(String, default=ProjectStatus.ACTIVE.value)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    agent_runs = relationship("AgentRun", back_populates="project", cascade="all, delete-orphan")
    webhook_events = relationship("WebhookEvent", back_populates="project", cascade="all, delete-orphan")
    validation_results = relationship("ValidationResult", back_populates="project", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("ix_projects_user_id", "user_id"),
        Index("ix_projects_github", "github_owner", "github_repo"),
        UniqueConstraint("user_id", "github_owner", "github_repo", name="uq_user_repo"),
    )


class AgentRun(Base):
    """Agent run table."""
    __tablename__ = "agent_runs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    target_text = Column(Text, nullable=False)
    auto_confirm_plan = Column(Boolean, default=False)
    status = Column(String, default=AgentRunStatus.PENDING.value)
    session_id = Column(String)
    response_data = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    project = relationship("Project", back_populates="agent_runs")
    
    # Indexes
    __table_args__ = (
        Index("ix_agent_runs_project_id", "project_id"),
        Index("ix_agent_runs_status", "status"),
        Index("ix_agent_runs_session_id", "session_id"),
    )


class WebhookEvent(Base):
    """Webhook event table."""
    __tablename__ = "webhook_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="webhook_events")
    
    # Indexes
    __table_args__ = (
        Index("ix_webhook_events_project_id", "project_id"),
        Index("ix_webhook_events_type", "event_type"),
        Index("ix_webhook_events_processed", "processed"),
    )


class ValidationResult(Base):
    """Validation result table."""
    __tablename__ = "validation_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    pr_number = Column(Integer, nullable=False)
    status = Column(String, default=ValidationStatus.PENDING.value)
    success = Column(Boolean, default=False)
    message = Column(Text)
    logs = Column(JSON, default=list)
    deployment_logs = Column(JSON, default=list)
    test_results = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    project = relationship("Project", back_populates="validation_results")
    
    # Indexes
    __table_args__ = (
        Index("ix_validation_results_project_id", "project_id"),
        Index("ix_validation_results_pr", "project_id", "pr_number"),
        Index("ix_validation_results_status", "status"),
    )


# Database Class

class Database:
    """Database manager class."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager."""
        self.database_url = database_url or "postgresql+asyncpg://user:password@localhost/webeval"
        self.engine = None
        self.session_factory = None
        
    async def initialize(self):
        """Initialize database connection and create tables."""
        try:
            # Create async engine
            self.engine = create_async_engine(
                self.database_url,
                echo=False,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
    
    async def get_session(self) -> AsyncSession:
        """Get database session."""
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        return self.session_factory()
    
    # User operations
    
    async def create_user(self, user_data: UserCreate) -> UserModel:
        """Create a new user."""
        async with self.get_session() as session:
            db_user = User(
                email=user_data.email,
                name=user_data.name,
                hashed_password=user_data.password,  # Should be hashed before calling this
                is_active=user_data.is_active
            )
            session.add(db_user)
            await session.commit()
            await session.refresh(db_user)
            
            return UserModel.from_orm(db_user)
    
    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """Get user by email."""
        async with self.get_session() as session:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            db_user = result.scalar_one_or_none()
            
            if db_user:
                return UserModel.from_orm(db_user)
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        """Get user by ID."""
        async with self.get_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            db_user = result.scalar_one_or_none()
            
            if db_user:
                return UserModel.from_orm(db_user)
            return None
    
    # Project operations
    
    async def create_project(self, user_id: str, project_data: ProjectCreate) -> ProjectModel:
        """Create a new project."""
        async with self.get_session() as session:
            db_project = Project(
                user_id=user_id,
                name=project_data.name,
                description=project_data.description,
                github_owner=project_data.github_owner,
                github_repo=project_data.github_repo,
                webhook_url=project_data.webhook_url,
                status=project_data.status.value,
                settings=project_data.settings.dict()
            )
            session.add(db_project)
            await session.commit()
            await session.refresh(db_project)
            
            return ProjectModel.from_orm(db_project)
    
    async def get_user_projects(self, user_id: str) -> List[ProjectModel]:
        """Get all projects for a user."""
        async with self.get_session() as session:
            result = await session.execute(
                select(Project)
                .where(Project.user_id == user_id)
                .order_by(Project.updated_at.desc())
            )
            db_projects = result.scalars().all()
            
            return [ProjectModel.from_orm(p) for p in db_projects]
    
    async def get_project(self, project_id: str, user_id: str) -> Optional[ProjectModel]:
        """Get a specific project."""
        async with self.get_session() as session:
            result = await session.execute(
                select(Project)
                .where(Project.id == project_id, Project.user_id == user_id)
            )
            db_project = result.scalar_one_or_none()
            
            if db_project:
                return ProjectModel.from_orm(db_project)
            return None
    
    async def get_project_by_id(self, project_id: str) -> Optional[ProjectModel]:
        """Get project by ID (without user check)."""
        async with self.get_session() as session:
            result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            db_project = result.scalar_one_or_none()
            
            if db_project:
                return ProjectModel.from_orm(db_project)
            return None
    
    async def update_project(self, project_id: str, update_data: Dict[str, Any]) -> Optional[ProjectModel]:
        """Update a project."""
        async with self.get_session() as session:
            # Update the project
            await session.execute(
                update(Project)
                .where(Project.id == project_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )
            await session.commit()
            
            # Fetch updated project
            result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            db_project = result.scalar_one_or_none()
            
            if db_project:
                return ProjectModel.from_orm(db_project)
            return None
    
    async def delete_project(self, project_id: str):
        """Delete a project."""
        async with self.get_session() as session:
            await session.execute(
                delete(Project).where(Project.id == project_id)
            )
            await session.commit()
    
    # Agent run operations
    
    async def create_agent_run(
        self, 
        project_id: str, 
        target_text: str, 
        auto_confirm_plan: bool = False
    ) -> AgentRunModel:
        """Create a new agent run."""
        async with self.get_session() as session:
            db_run = AgentRun(
                project_id=project_id,
                target_text=target_text,
                auto_confirm_plan=auto_confirm_plan
            )
            session.add(db_run)
            await session.commit()
            await session.refresh(db_run)
            
            return AgentRunModel.from_orm(db_run)
    
    async def get_agent_run(self, run_id: str, project_id: str) -> Optional[AgentRunModel]:
        """Get an agent run."""
        async with self.get_session() as session:
            result = await session.execute(
                select(AgentRun)
                .where(AgentRun.id == run_id, AgentRun.project_id == project_id)
            )
            db_run = result.scalar_one_or_none()
            
            if db_run:
                return AgentRunModel.from_orm(db_run)
            return None
    
    async def update_agent_run(self, run_id: str, update_data: Dict[str, Any]) -> Optional[AgentRunModel]:
        """Update an agent run."""
        async with self.get_session() as session:
            await session.execute(
                update(AgentRun)
                .where(AgentRun.id == run_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )
            await session.commit()
            
            result = await session.execute(
                select(AgentRun).where(AgentRun.id == run_id)
            )
            db_run = result.scalar_one_or_none()
            
            if db_run:
                return AgentRunModel.from_orm(db_run)
            return None
    
    async def get_project_agent_runs(self, project_id: str) -> List[AgentRunModel]:
        """Get all agent runs for a project."""
        async with self.get_session() as session:
            result = await session.execute(
                select(AgentRun)
                .where(AgentRun.project_id == project_id)
                .order_by(AgentRun.created_at.desc())
            )
            db_runs = result.scalars().all()
            
            return [AgentRunModel.from_orm(r) for r in db_runs]
    
    # Webhook event operations
    
    async def create_webhook_event(self, event_data: WebhookEventCreate) -> WebhookEventModel:
        """Create a webhook event."""
        async with self.get_session() as session:
            db_event = WebhookEvent(
                project_id=event_data.project_id,
                event_type=event_data.event_type,
                payload=event_data.payload,
                processed=event_data.processed
            )
            session.add(db_event)
            await session.commit()
            await session.refresh(db_event)
            
            return WebhookEventModel.from_orm(db_event)
    
    async def get_unprocessed_webhook_events(self) -> List[WebhookEventModel]:
        """Get unprocessed webhook events."""
        async with self.get_session() as session:
            result = await session.execute(
                select(WebhookEvent)
                .where(WebhookEvent.processed == False)
                .order_by(WebhookEvent.created_at.asc())
            )
            db_events = result.scalars().all()
            
            return [WebhookEventModel.from_orm(e) for e in db_events]
    
    async def mark_webhook_event_processed(self, event_id: str, error_message: Optional[str] = None):
        """Mark webhook event as processed."""
        async with self.get_session() as session:
            await session.execute(
                update(WebhookEvent)
                .where(WebhookEvent.id == event_id)
                .values(
                    processed=True,
                    processed_at=datetime.utcnow(),
                    error_message=error_message,
                    updated_at=datetime.utcnow()
                )
            )
            await session.commit()
    
    # Validation result operations
    
    async def create_validation_result(self, result_data: ValidationResultCreate) -> ValidationResultModel:
        """Create a validation result."""
        async with self.get_session() as session:
            db_result = ValidationResult(
                project_id=result_data.project_id,
                pr_number=result_data.pr_number,
                status=result_data.status.value,
                success=result_data.success,
                message=result_data.message,
                logs=result_data.logs,
                deployment_logs=result_data.deployment_logs,
                test_results=result_data.test_results
            )
            session.add(db_result)
            await session.commit()
            await session.refresh(db_result)
            
            return ValidationResultModel.from_orm(db_result)
    
    async def update_validation_result(self, result_id: str, update_data: Dict[str, Any]) -> Optional[ValidationResultModel]:
        """Update a validation result."""
        async with self.get_session() as session:
            await session.execute(
                update(ValidationResult)
                .where(ValidationResult.id == result_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )
            await session.commit()
            
            result = await session.execute(
                select(ValidationResult).where(ValidationResult.id == result_id)
            )
            db_result = result.scalar_one_or_none()
            
            if db_result:
                return ValidationResultModel.from_orm(db_result)
            return None
    
    async def get_project_validation_results(self, project_id: str) -> List[ValidationResultModel]:
        """Get validation results for a project."""
        async with self.get_session() as session:
            result = await session.execute(
                select(ValidationResult)
                .where(ValidationResult.project_id == project_id)
                .order_by(ValidationResult.created_at.desc())
            )
            db_results = result.scalars().all()
            
            return [ValidationResultModel.from_orm(r) for r in db_results]


# Dependency injection

_database_instance: Optional[Database] = None

async def get_database() -> Database:
    """Get database instance for dependency injection."""
    global _database_instance
    if _database_instance is None:
        _database_instance = Database()
        await _database_instance.initialize()
    return _database_instance

async def close_database():
    """Close database connections."""
    global _database_instance
    if _database_instance:
        await _database_instance.close()
        _database_instance = None
