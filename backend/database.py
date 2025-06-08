"""
Database configuration and models for the AI-Powered CI/CD Platform
"""
import asyncio
from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
import asyncpg

from backend.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG,
    future=True
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()


class Project(Base):
    """Project model for storing GitHub repository information"""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    github_url = Column(String, nullable=False)
    github_token = Column(String, nullable=False)  # Encrypted in production
    owner = Column(String, nullable=False)
    repo_name = Column(String, nullable=False)
    default_branch = Column(String, default="main")
    is_pinned = Column(Boolean, default=False)
    requirements = Column(Text)
    plan = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    workflows = relationship("WorkflowExecution", back_populates="project")
    agent_tasks = relationship("AgentTask", back_populates="project")
    analysis_results = relationship("AnalysisResult", back_populates="project")


class WorkflowExecution(Base):
    """Workflow execution tracking"""
    __tablename__ = "workflow_executions"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed, cancelled
    plan = Column(Text)
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, default=0)
    progress_percentage = Column(Integer, default=0)
    error_message = Column(Text)
    metadata = Column(JSON)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="workflows")
    workflow_steps = relationship("WorkflowStep", back_populates="workflow")
    agent_tasks = relationship("AgentTask", back_populates="workflow")


class WorkflowStep(Base):
    """Individual workflow step tracking"""
    __tablename__ = "workflow_steps"
    
    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflow_executions.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="pending")  # pending, running, completed, failed, skipped
    step_type = Column(String)  # analysis, pr_creation, deployment, validation
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    workflow = relationship("WorkflowExecution", back_populates="workflow_steps")


class AgentTask(Base):
    """Codegen agent task tracking with enhanced monitoring"""
    __tablename__ = "agent_tasks"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    workflow_id = Column(String, ForeignKey("workflow_executions.id"), nullable=True)
    codegen_task_id = Column(String)  # ID from Codegen SDK
    original_prompt = Column(Text, nullable=False)
    enhanced_prompt = Column(Text)
    prompt_enhancement_techniques = Column(JSON)
    status = Column(String, default="pending")  # pending, running, completed, failed
    result = Column(Text)
    web_url = Column(String)
    error_message = Column(Text)
    execution_time_seconds = Column(Integer)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="agent_tasks")
    workflow = relationship("WorkflowExecution", back_populates="agent_tasks")
    status_updates = relationship("AgentStatusUpdate", back_populates="agent_task")


class AgentStatusUpdate(Base):
    """Real-time agent status updates for dashboard monitoring"""
    __tablename__ = "agent_status_updates"
    
    id = Column(String, primary_key=True)
    agent_task_id = Column(String, ForeignKey("agent_tasks.id"), nullable=False)
    status = Column(String, nullable=False)
    message = Column(Text)
    progress_percentage = Column(Integer, default=0)
    current_action = Column(String)
    metadata = Column(JSON)
    timestamp = Column(DateTime, default=func.now())
    
    # Relationships
    agent_task = relationship("AgentTask", back_populates="status_updates")


class AnalysisResult(Base):
    """Graph-sitter code analysis results"""
    __tablename__ = "analysis_results"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    commit_sha = Column(String)
    branch = Column(String)
    analysis_type = Column(String)  # dead_code, unused_params, security, quality
    file_path = Column(String)
    line_number = Column(Integer)
    issue_type = Column(String)
    severity = Column(String)  # low, medium, high, critical
    message = Column(Text)
    suggestion = Column(Text)
    metadata = Column(JSON)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="analysis_results")


class Deployment(Base):
    """Modal deployment tracking"""
    __tablename__ = "deployments"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    workflow_id = Column(String, ForeignKey("workflow_executions.id"), nullable=True)
    environment = Column(String, nullable=False)  # staging, production
    status = Column(String, default="pending")  # pending, deploying, deployed, failed, rolled_back
    deployment_url = Column(String)
    commit_sha = Column(String)
    branch = Column(String)
    modal_app_id = Column(String)
    health_check_url = Column(String)
    error_message = Column(Text)
    metadata = Column(JSON)
    deployed_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())


# Database dependency
async def get_db() -> AsyncSession:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Database utilities
class DatabaseManager:
    """Database operations manager"""
    
    @staticmethod
    async def create_project(project_data: dict) -> Project:
        """Create a new project"""
        async with AsyncSessionLocal() as session:
            project = Project(**project_data)
            session.add(project)
            await session.commit()
            await session.refresh(project)
            return project
    
    @staticmethod
    async def get_project(project_id: str) -> Optional[Project]:
        """Get project by ID"""
        async with AsyncSessionLocal() as session:
            result = await session.get(Project, project_id)
            return result
    
    @staticmethod
    async def get_pinned_projects() -> List[Project]:
        """Get all pinned projects"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                "SELECT * FROM projects WHERE is_pinned = true ORDER BY updated_at DESC"
            )
            return result.fetchall()
    
    @staticmethod
    async def create_workflow(workflow_data: dict) -> WorkflowExecution:
        """Create a new workflow execution"""
        async with AsyncSessionLocal() as session:
            workflow = WorkflowExecution(**workflow_data)
            session.add(workflow)
            await session.commit()
            await session.refresh(workflow)
            return workflow
    
    @staticmethod
    async def update_agent_status(task_id: str, status: str, message: str = None):
        """Update agent task status with real-time tracking"""
        async with AsyncSessionLocal() as session:
            # Update main task
            task = await session.get(AgentTask, task_id)
            if task:
                task.status = status
                task.updated_at = func.now()
                
                # Create status update record
                status_update = AgentStatusUpdate(
                    id=f"{task_id}_{datetime.now().timestamp()}",
                    agent_task_id=task_id,
                    status=status,
                    message=message,
                    timestamp=func.now()
                )
                session.add(status_update)
                await session.commit()
                
                return task
            return None

