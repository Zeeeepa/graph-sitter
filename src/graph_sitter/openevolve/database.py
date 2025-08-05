"""Database models and schema for OpenEvolve integration."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, Float, Integer, JSON, String, Text, 
    Index, ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

from .models import EvaluationStatus, EvaluationTrigger

Base = declarative_base()


class OpenEvolveEvaluation(Base):
    """Database model for OpenEvolve evaluations."""
    
    __tablename__ = "openevolve_evaluations"
    
    # Primary key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # OpenEvolve evaluation ID
    evaluation_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Status and timing
    status = Column(String(50), nullable=False, default=EvaluationStatus.PENDING.value, index=True)
    trigger_event = Column(String(100), nullable=False, index=True)
    priority = Column(Integer, nullable=False, default=5)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Data
    context = Column(JSON, nullable=False, default=dict)
    metadata = Column(JSON, nullable=False, default=dict)
    results = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Configuration
    timeout = Column(Integer, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    
    # Relationships
    improvements = relationship("SystemImprovement", back_populates="evaluation", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_openevolve_evaluations_status_created", "status", "created_at"),
        Index("idx_openevolve_evaluations_trigger_created", "trigger_event", "created_at"),
        Index("idx_openevolve_evaluations_completed_at", "completed_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "evaluation_id": self.evaluation_id,
            "status": self.status,
            "trigger_event": self.trigger_event,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "context": self.context,
            "metadata": self.metadata,
            "results": self.results,
            "metrics": self.metrics,
            "error_message": self.error_message,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }


class SystemImprovement(Base):
    """Database model for system improvements from OpenEvolve."""
    
    __tablename__ = "system_improvements"
    
    # Primary key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to evaluation
    evaluation_id = Column(PostgresUUID(as_uuid=True), ForeignKey("openevolve_evaluations.id"), nullable=False, index=True)
    
    # Improvement details
    improvement_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    priority = Column(Integer, nullable=False, default=5)
    estimated_impact = Column(Float, nullable=True)
    implementation_complexity = Column(String(50), nullable=True)
    
    # Application status
    applied = Column(Boolean, nullable=False, default=False, index=True)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    results = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    evaluation = relationship("OpenEvolveEvaluation", back_populates="improvements")
    
    # Indexes
    __table_args__ = (
        Index("idx_system_improvements_type_priority", "improvement_type", "priority"),
        Index("idx_system_improvements_applied_created", "applied", "created_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "evaluation_id": str(self.evaluation_id),
            "improvement_type": self.improvement_type,
            "description": self.description,
            "priority": self.priority,
            "estimated_impact": self.estimated_impact,
            "implementation_complexity": self.implementation_complexity,
            "applied": self.applied,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "results": self.results,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EvaluationMetrics(Base):
    """Database model for detailed evaluation metrics."""
    
    __tablename__ = "evaluation_metrics"
    
    # Primary key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to evaluation
    evaluation_id = Column(PostgresUUID(as_uuid=True), ForeignKey("openevolve_evaluations.id"), nullable=False, index=True)
    
    # Metrics
    accuracy = Column(Float, nullable=True)
    performance_score = Column(Float, nullable=True)
    improvement_score = Column(Float, nullable=True)
    execution_time = Column(Float, nullable=True)
    resource_usage = Column(JSON, nullable=True)
    custom_metrics = Column(JSON, nullable=True)
    
    # Timestamps
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("evaluation_id", name="uq_evaluation_metrics_evaluation_id"),
        Index("idx_evaluation_metrics_recorded_at", "recorded_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "evaluation_id": str(self.evaluation_id),
            "accuracy": self.accuracy,
            "performance_score": self.performance_score,
            "improvement_score": self.improvement_score,
            "execution_time": self.execution_time,
            "resource_usage": self.resource_usage,
            "custom_metrics": self.custom_metrics,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }


class EvaluationRepository:
    """Repository for managing OpenEvolve evaluations in the database."""
    
    def __init__(self, session: Session):
        """Initialize the repository.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def create_evaluation(self, evaluation_data: Dict[str, Any]) -> OpenEvolveEvaluation:
        """Create a new evaluation record.
        
        Args:
            evaluation_data: Evaluation data
            
        Returns:
            Created evaluation record
        """
        evaluation = OpenEvolveEvaluation(**evaluation_data)
        self.session.add(evaluation)
        self.session.commit()
        self.session.refresh(evaluation)
        return evaluation
    
    def get_evaluation(self, evaluation_id: UUID) -> Optional[OpenEvolveEvaluation]:
        """Get an evaluation by ID.
        
        Args:
            evaluation_id: Evaluation ID
            
        Returns:
            Evaluation record or None
        """
        return self.session.query(OpenEvolveEvaluation).filter(
            OpenEvolveEvaluation.id == evaluation_id
        ).first()
    
    def get_evaluation_by_openevolve_id(self, openevolve_id: str) -> Optional[OpenEvolveEvaluation]:
        """Get an evaluation by OpenEvolve ID.
        
        Args:
            openevolve_id: OpenEvolve evaluation ID
            
        Returns:
            Evaluation record or None
        """
        return self.session.query(OpenEvolveEvaluation).filter(
            OpenEvolveEvaluation.evaluation_id == openevolve_id
        ).first()
    
    def update_evaluation_status(
        self, 
        evaluation_id: UUID, 
        status: EvaluationStatus,
        **kwargs
    ) -> Optional[OpenEvolveEvaluation]:
        """Update evaluation status and optional fields.
        
        Args:
            evaluation_id: Evaluation ID
            status: New status
            **kwargs: Additional fields to update
            
        Returns:
            Updated evaluation record or None
        """
        evaluation = self.get_evaluation(evaluation_id)
        if evaluation:
            evaluation.status = status.value
            for key, value in kwargs.items():
                if hasattr(evaluation, key):
                    setattr(evaluation, key, value)
            self.session.commit()
            self.session.refresh(evaluation)
        return evaluation
    
    def list_evaluations(
        self,
        status: Optional[EvaluationStatus] = None,
        trigger_event: Optional[EvaluationTrigger] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[OpenEvolveEvaluation]:
        """List evaluations with optional filtering.
        
        Args:
            status: Filter by status
            trigger_event: Filter by trigger event
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of evaluation records
        """
        query = self.session.query(OpenEvolveEvaluation)
        
        if status:
            query = query.filter(OpenEvolveEvaluation.status == status.value)
        
        if trigger_event:
            query = query.filter(OpenEvolveEvaluation.trigger_event == trigger_event.value)
        
        return query.order_by(OpenEvolveEvaluation.created_at.desc()).offset(offset).limit(limit).all()
    
    def get_pending_evaluations(self) -> List[OpenEvolveEvaluation]:
        """Get all pending evaluations.
        
        Returns:
            List of pending evaluation records
        """
        return self.session.query(OpenEvolveEvaluation).filter(
            OpenEvolveEvaluation.status == EvaluationStatus.PENDING.value
        ).order_by(OpenEvolveEvaluation.priority.asc(), OpenEvolveEvaluation.created_at.asc()).all()
    
    def create_improvement(self, improvement_data: Dict[str, Any]) -> SystemImprovement:
        """Create a new system improvement record.
        
        Args:
            improvement_data: Improvement data
            
        Returns:
            Created improvement record
        """
        improvement = SystemImprovement(**improvement_data)
        self.session.add(improvement)
        self.session.commit()
        self.session.refresh(improvement)
        return improvement
    
    def get_improvements_for_evaluation(self, evaluation_id: UUID) -> List[SystemImprovement]:
        """Get all improvements for an evaluation.
        
        Args:
            evaluation_id: Evaluation ID
            
        Returns:
            List of improvement records
        """
        return self.session.query(SystemImprovement).filter(
            SystemImprovement.evaluation_id == evaluation_id
        ).order_by(SystemImprovement.priority.asc()).all()
    
    def mark_improvement_applied(self, improvement_id: UUID, results: Optional[Dict] = None) -> Optional[SystemImprovement]:
        """Mark an improvement as applied.
        
        Args:
            improvement_id: Improvement ID
            results: Optional results data
            
        Returns:
            Updated improvement record or None
        """
        improvement = self.session.query(SystemImprovement).filter(
            SystemImprovement.id == improvement_id
        ).first()
        
        if improvement:
            improvement.applied = True
            improvement.applied_at = func.now()
            if results:
                improvement.results = results
            self.session.commit()
            self.session.refresh(improvement)
        
        return improvement

