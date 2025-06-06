"""
Database management for the Dashboard extension.

This module handles database connections, schema management, and data persistence
for the dashboard system using PostgreSQL.
"""

import os
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import logging

try:
    import asyncpg
    import sqlalchemy as sa
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker, declarative_base
    from sqlalchemy.dialects.postgresql import UUID, JSONB
    ASYNC_DB_AVAILABLE = True
except ImportError:
    # Fallback for environments without async database support
    ASYNC_DB_AVAILABLE = False
    asyncpg = None
    sa = None
    AsyncSession = None
    sessionmaker = None
    declarative_base = None
    UUID = None
    JSONB = None

from .models import (
    Project, ProjectPin, ProjectSettings, WorkflowPlan, WorkflowTask,
    WorkflowExecution, QualityGate, PRInfo, EventLog,
    ProjectStatus, FlowStatus, WorkflowStatus, TaskStatus, QualityGateStatus, PRStatus
)

logger = logging.getLogger(__name__)

# Database schema SQL
DATABASE_SCHEMA = """
-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    url VARCHAR(500) NOT NULL,
    default_branch VARCHAR(100) DEFAULT 'main',
    language VARCHAR(50),
    status VARCHAR(20) DEFAULT 'inactive',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Project pins table
CREATE TABLE IF NOT EXISTS project_pins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    position INTEGER DEFAULT 0,
    flow_status VARCHAR(20) DEFAULT 'off',
    pinned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    settings JSONB DEFAULT '{}'
);

-- Project settings table
CREATE TABLE IF NOT EXISTS project_settings (
    project_id UUID PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
    github_enabled BOOLEAN DEFAULT true,
    linear_enabled BOOLEAN DEFAULT true,
    slack_enabled BOOLEAN DEFAULT true,
    codegen_enabled BOOLEAN DEFAULT true,
    auto_pr_creation BOOLEAN DEFAULT true,
    auto_issue_creation BOOLEAN DEFAULT true,
    quality_gates_enabled BOOLEAN DEFAULT true,
    notification_preferences JSONB DEFAULT '{}',
    custom_settings JSONB DEFAULT '{}'
);

-- Workflow plans table
CREATE TABLE IF NOT EXISTS workflow_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    requirements TEXT NOT NULL,
    generated_plan JSONB NOT NULL,
    tasks JSONB DEFAULT '[]',
    estimated_duration INTEGER,
    complexity_score FLOAT DEFAULT 0.0,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    metadata JSONB DEFAULT '{}'
);

-- Workflow tasks table
CREATE TABLE IF NOT EXISTS workflow_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES workflow_plans(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) NOT NULL,
    dependencies JSONB DEFAULT '[]',
    assignee VARCHAR(255),
    status VARCHAR(20) DEFAULT 'todo',
    priority INTEGER DEFAULT 1,
    estimated_hours FLOAT,
    actual_hours FLOAT,
    github_pr_url VARCHAR(500),
    linear_issue_id VARCHAR(100),
    codegen_task_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- Workflow executions table
CREATE TABLE IF NOT EXISTS workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES workflow_plans(id) ON DELETE CASCADE,
    execution_layer VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    progress_percentage FLOAT DEFAULT 0.0,
    current_task_id UUID REFERENCES workflow_tasks(id),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    execution_logs JSONB DEFAULT '[]',
    metrics JSONB DEFAULT '{}'
);

-- Quality gates table
CREATE TABLE IF NOT EXISTS quality_gates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES workflow_tasks(id) ON DELETE CASCADE,
    gate_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    score FLOAT,
    threshold FLOAT DEFAULT 0.8,
    issues_found JSONB DEFAULT '[]',
    auto_fix_applied BOOLEAN DEFAULT false,
    manual_review_required BOOLEAN DEFAULT false,
    executed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- PR info table
CREATE TABLE IF NOT EXISTS pr_info (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    task_id UUID REFERENCES workflow_tasks(id),
    pr_number INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'open',
    url VARCHAR(500) NOT NULL,
    branch_name VARCHAR(255) NOT NULL,
    base_branch VARCHAR(255) DEFAULT 'main',
    author VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    merged_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- Event logs table
CREATE TABLE IF NOT EXISTS event_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_source VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    user_id VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_projects_full_name ON projects(full_name);
CREATE INDEX IF NOT EXISTS idx_project_pins_user_id ON project_pins(user_id);
CREATE INDEX IF NOT EXISTS idx_workflow_plans_project_id ON workflow_plans(project_id);
CREATE INDEX IF NOT EXISTS idx_workflow_tasks_plan_id ON workflow_tasks(plan_id);
CREATE INDEX IF NOT EXISTS idx_workflow_tasks_status ON workflow_tasks(status);
CREATE INDEX IF NOT EXISTS idx_quality_gates_task_id ON quality_gates(task_id);
CREATE INDEX IF NOT EXISTS idx_pr_info_project_id ON pr_info(project_id);
CREATE INDEX IF NOT EXISTS idx_event_logs_project_id ON event_logs(project_id);
CREATE INDEX IF NOT EXISTS idx_event_logs_timestamp ON event_logs(timestamp);
"""


class DatabaseManager:
    """Database manager for the dashboard system."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager.
        
        Args:
            database_url: PostgreSQL connection URL. If None, uses environment variable.
        """
        self.database_url = database_url or os.getenv(
            "POSTGRESQL_URL", 
            "postgresql://localhost:5432/contexten_dashboard"
        )
        self.engine = None
        self.session_factory = None
        
        if ASYNC_DB_AVAILABLE:
            self._setup_async_engine()
        else:
            logger.warning("Async database support not available. Install asyncpg and sqlalchemy[asyncio]")
    
    def _setup_async_engine(self):
        """Setup async database engine."""
        if not ASYNC_DB_AVAILABLE:
            return
            
        try:
            # Convert postgresql:// to postgresql+asyncpg://
            async_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
            self.engine = create_async_engine(async_url, echo=False)
            self.session_factory = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            logger.info("Database engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to setup database engine: {e}")
            self.engine = None
            self.session_factory = None
    
    async def initialize_schema(self):
        """Initialize database schema."""
        if not self.engine:
            logger.error("Database engine not available")
            return False
            
        try:
            async with self.engine.begin() as conn:
                await conn.execute(sa.text(DATABASE_SCHEMA))
            logger.info("Database schema initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            return False
    
    async def get_session(self) -> Optional[AsyncSession]:
        """Get database session."""
        if not self.session_factory:
            return None
        return self.session_factory()
    
    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()


class ProjectRepository:
    """Repository for project data operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_project(self, project: Project) -> Optional[str]:
        """Create a new project."""
        if not self.db_manager.engine:
            return None
            
        try:
            async with self.db_manager.get_session() as session:
                query = sa.text("""
                    INSERT INTO projects (name, full_name, description, url, default_branch, language, status, metadata)
                    VALUES (:name, :full_name, :description, :url, :default_branch, :language, :status, :metadata)
                    RETURNING id
                """)
                result = await session.execute(query, {
                    "name": project.name,
                    "full_name": project.full_name,
                    "description": project.description,
                    "url": project.url,
                    "default_branch": project.default_branch,
                    "language": project.language,
                    "status": project.status.value,
                    "metadata": json.dumps(project.metadata)
                })
                project_id = result.scalar()
                await session.commit()
                return str(project_id)
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return None
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        if not self.db_manager.engine:
            return None
            
        try:
            async with self.db_manager.get_session() as session:
                query = sa.text("SELECT * FROM projects WHERE id = :project_id")
                result = await session.execute(query, {"project_id": project_id})
                row = result.fetchone()
                
                if row:
                    return Project(
                        id=str(row.id),
                        name=row.name,
                        full_name=row.full_name,
                        description=row.description,
                        url=row.url,
                        default_branch=row.default_branch,
                        language=row.language,
                        status=ProjectStatus(row.status),
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                        metadata=row.metadata or {}
                    )
                return None
        except Exception as e:
            logger.error(f"Failed to get project: {e}")
            return None
    
    async def get_projects_by_user(self, user_id: str) -> List[Project]:
        """Get all projects pinned by a user."""
        if not self.db_manager.engine:
            return []
            
        try:
            async with self.db_manager.get_session() as session:
                query = sa.text("""
                    SELECT p.* FROM projects p
                    JOIN project_pins pp ON p.id = pp.project_id
                    WHERE pp.user_id = :user_id
                    ORDER BY pp.position
                """)
                result = await session.execute(query, {"user_id": user_id})
                
                projects = []
                for row in result.fetchall():
                    projects.append(Project(
                        id=str(row.id),
                        name=row.name,
                        full_name=row.full_name,
                        description=row.description,
                        url=row.url,
                        default_branch=row.default_branch,
                        language=row.language,
                        status=ProjectStatus(row.status),
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                        metadata=row.metadata or {}
                    ))
                return projects
        except Exception as e:
            logger.error(f"Failed to get user projects: {e}")
            return []
    
    async def pin_project(self, project_pin: ProjectPin) -> bool:
        """Pin a project for a user."""
        if not self.db_manager.engine:
            return False
            
        try:
            async with self.db_manager.get_session() as session:
                query = sa.text("""
                    INSERT INTO project_pins (project_id, user_id, position, flow_status, settings)
                    VALUES (:project_id, :user_id, :position, :flow_status, :settings)
                    ON CONFLICT (project_id, user_id) DO UPDATE SET
                        position = EXCLUDED.position,
                        flow_status = EXCLUDED.flow_status,
                        settings = EXCLUDED.settings
                """)
                await session.execute(query, {
                    "project_id": project_pin.project_id,
                    "user_id": project_pin.user_id,
                    "position": project_pin.position,
                    "flow_status": project_pin.flow_status.value,
                    "settings": json.dumps(project_pin.settings)
                })
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to pin project: {e}")
            return False


class WorkflowRepository:
    """Repository for workflow data operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_plan(self, plan: WorkflowPlan) -> Optional[str]:
        """Create a new workflow plan."""
        if not self.db_manager.engine:
            return None
            
        try:
            async with self.db_manager.get_session() as session:
                query = sa.text("""
                    INSERT INTO workflow_plans (
                        project_id, title, description, requirements, generated_plan,
                        tasks, estimated_duration, complexity_score, created_by, metadata
                    )
                    VALUES (
                        :project_id, :title, :description, :requirements, :generated_plan,
                        :tasks, :estimated_duration, :complexity_score, :created_by, :metadata
                    )
                    RETURNING id
                """)
                result = await session.execute(query, {
                    "project_id": plan.project_id,
                    "title": plan.title,
                    "description": plan.description,
                    "requirements": plan.requirements,
                    "generated_plan": json.dumps(plan.generated_plan),
                    "tasks": json.dumps(plan.tasks),
                    "estimated_duration": plan.estimated_duration,
                    "complexity_score": plan.complexity_score,
                    "created_by": plan.created_by,
                    "metadata": json.dumps(plan.metadata)
                })
                plan_id = result.scalar()
                await session.commit()
                return str(plan_id)
        except Exception as e:
            logger.error(f"Failed to create workflow plan: {e}")
            return None
    
    async def get_plans_by_project(self, project_id: str) -> List[WorkflowPlan]:
        """Get all workflow plans for a project."""
        if not self.db_manager.engine:
            return []
            
        try:
            async with self.db_manager.get_session() as session:
                query = sa.text("""
                    SELECT * FROM workflow_plans 
                    WHERE project_id = :project_id 
                    ORDER BY created_at DESC
                """)
                result = await session.execute(query, {"project_id": project_id})
                
                plans = []
                for row in result.fetchall():
                    plans.append(WorkflowPlan(
                        id=str(row.id),
                        project_id=str(row.project_id),
                        title=row.title,
                        description=row.description,
                        requirements=row.requirements,
                        generated_plan=row.generated_plan or {},
                        tasks=row.tasks or [],
                        estimated_duration=row.estimated_duration,
                        complexity_score=row.complexity_score,
                        status=WorkflowStatus(row.status),
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                        created_by=row.created_by,
                        metadata=row.metadata or {}
                    ))
                return plans
        except Exception as e:
            logger.error(f"Failed to get workflow plans: {e}")
            return []


# Initialize global database manager
db_manager = DatabaseManager()


async def initialize_database():
    """Initialize the database schema."""
    return await db_manager.initialize_schema()


async def get_project_repository() -> ProjectRepository:
    """Get project repository instance."""
    return ProjectRepository(db_manager)


async def get_workflow_repository() -> WorkflowRepository:
    """Get workflow repository instance."""
    return WorkflowRepository(db_manager)

