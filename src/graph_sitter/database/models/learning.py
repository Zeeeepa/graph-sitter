"""
Learning and OpenEvolve Models

Continuous learning system and OpenEvolve integration models
for system optimization and pattern recognition.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, UniqueConstraint, Index, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Session

from ..base import DatabaseModel, AuditedModel, DescriptionMixin, StatusMixin


class LearningPattern(AuditedModel, DescriptionMixin, StatusMixin):
    """
    Learned patterns and insights from system behavior.
    
    Stores patterns discovered through analysis of system behavior,
    code quality trends, and development workflows.
    """
    __tablename__ = 'learning_patterns'
    
    # Organization relationship
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    
    # Pattern identification
    pattern_type = Column(String(100), nullable=False)  # code_quality, workflow, performance, etc.
    category = Column(String(100), nullable=False, default='general')
    
    # Pattern data
    pattern_data = Column('pattern_data', DatabaseModel.metadata.type, nullable=False, default=dict)
    conditions = Column('conditions', DatabaseModel.metadata.type, nullable=False, default=dict)
    outcomes = Column('outcomes', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Pattern metrics
    confidence_score = Column(Numeric(5, 2), nullable=False, default=0.0)
    support_count = Column(Integer, nullable=False, default=1)
    accuracy_rate = Column(Numeric(5, 2), nullable=True)
    
    # Usage and validation
    times_applied = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    last_applied_at = Column('last_applied_at', DatabaseModel.created_at.type, nullable=True)
    
    # Pattern lifecycle
    discovered_at = Column('discovered_at', DatabaseModel.created_at.type, nullable=False)
    validated_at = Column('validated_at', DatabaseModel.created_at.type, nullable=True)
    
    # Relationships
    organization = relationship("Organization")
    optimizations = relationship("SystemOptimization", back_populates="learning_pattern")
    
    # Constraints
    __table_args__ = (
        Index('idx_learning_patterns_org', 'organization_id'),
        Index('idx_learning_patterns_type', 'pattern_type'),
        Index('idx_learning_patterns_category', 'category'),
        Index('idx_learning_patterns_confidence', 'confidence_score'),
        Index('idx_learning_patterns_support', 'support_count'),
        Index('idx_learning_patterns_accuracy', 'accuracy_rate'),
        Index('idx_learning_patterns_discovered', 'discovered_at'),
        Index('idx_learning_patterns_status', 'status'),
    )
    
    def __init__(self, organization_id: str, name: str, pattern_type: str, pattern_data: Dict[str, Any], **kwargs):
        """Initialize learning pattern with required fields."""
        super().__init__(
            organization_id=organization_id,
            name=name,
            pattern_type=pattern_type,
            pattern_data=pattern_data,
            discovered_at=datetime.utcnow(),
            **kwargs
        )
    
    def apply_pattern(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply pattern to given context and return recommendations."""
        self.times_applied += 1
        self.last_applied_at = datetime.utcnow()
        
        # Simple pattern matching logic
        recommendations = {
            'pattern_id': str(self.id),
            'pattern_name': self.name,
            'pattern_type': self.pattern_type,
            'confidence': float(self.confidence_score),
            'recommendations': self.outcomes.get('recommendations', []),
            'applied_at': datetime.utcnow().isoformat(),
        }
        
        return recommendations
    
    def record_success(self) -> None:
        """Record successful application of pattern."""
        self.success_count += 1
        self.accuracy_rate = Decimal(str((self.success_count / self.times_applied) * 100)) if self.times_applied > 0 else Decimal('0')
    
    def validate_pattern(self) -> None:
        """Mark pattern as validated."""
        self.validated_at = datetime.utcnow()
        self.status = 'active'
    
    def get_pattern_stats(self) -> Dict[str, Any]:
        """Get pattern statistics."""
        return {
            'id': str(self.id),
            'name': self.name,
            'pattern_type': self.pattern_type,
            'category': self.category,
            'status': self.status,
            'confidence_score': float(self.confidence_score),
            'support_count': self.support_count,
            'accuracy_rate': float(self.accuracy_rate) if self.accuracy_rate else None,
            'times_applied': self.times_applied,
            'success_count': self.success_count,
            'success_rate': (self.success_count / self.times_applied * 100) if self.times_applied > 0 else 0,
            'discovered_at': self.discovered_at.isoformat(),
            'validated_at': self.validated_at.isoformat() if self.validated_at else None,
            'last_applied_at': self.last_applied_at.isoformat() if self.last_applied_at else None,
        }


class SystemOptimization(AuditedModel, DescriptionMixin, StatusMixin):
    """
    System optimization recommendations and implementations.
    
    Tracks system optimization recommendations generated from
    learning patterns and their implementation results.
    """
    __tablename__ = 'system_optimizations'
    
    # Organization relationship
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    
    # Learning pattern relationship
    learning_pattern_id = Column(UUID(as_uuid=True), ForeignKey('learning_patterns.id', ondelete='SET NULL'), nullable=True)
    
    # Optimization details
    optimization_type = Column(String(100), nullable=False)  # performance, quality, workflow, etc.
    target_component = Column(String(255), nullable=False)  # database, analysis, workflow, etc.
    
    # Optimization data
    current_state = Column('current_state', DatabaseModel.metadata.type, nullable=False, default=dict)
    target_state = Column('target_state', DatabaseModel.metadata.type, nullable=False, default=dict)
    implementation_plan = Column('implementation_plan', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Metrics and impact
    expected_improvement = Column(Numeric(5, 2), nullable=True)
    actual_improvement = Column(Numeric(5, 2), nullable=True)
    impact_metrics = Column('impact_metrics', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Implementation tracking
    implemented_at = Column('implemented_at', DatabaseModel.created_at.type, nullable=True)
    validated_at = Column('validated_at', DatabaseModel.created_at.type, nullable=True)
    rollback_at = Column('rollback_at', DatabaseModel.created_at.type, nullable=True)
    
    # Priority and scheduling
    priority = Column(String(20), nullable=False, default='medium')
    scheduled_for = Column('scheduled_for', DatabaseModel.created_at.type, nullable=True)
    
    # Relationships
    organization = relationship("Organization")
    learning_pattern = relationship("LearningPattern", back_populates="optimizations")
    
    # Constraints
    __table_args__ = (
        Index('idx_system_optimizations_org', 'organization_id'),
        Index('idx_system_optimizations_pattern', 'learning_pattern_id'),
        Index('idx_system_optimizations_type', 'optimization_type'),
        Index('idx_system_optimizations_target', 'target_component'),
        Index('idx_system_optimizations_status', 'status'),
        Index('idx_system_optimizations_priority', 'priority'),
        Index('idx_system_optimizations_scheduled', 'scheduled_for'),
        Index('idx_system_optimizations_implemented', 'implemented_at'),
    )
    
    def __init__(self, organization_id: str, name: str, optimization_type: str, target_component: str, **kwargs):
        """Initialize system optimization with required fields."""
        super().__init__(
            organization_id=organization_id,
            name=name,
            optimization_type=optimization_type,
            target_component=target_component,
            **kwargs
        )
    
    def implement_optimization(self) -> None:
        """Mark optimization as implemented."""
        self.implemented_at = datetime.utcnow()
        self.status = 'implemented'
    
    def validate_optimization(self, actual_improvement: float, impact_metrics: Dict[str, Any]) -> None:
        """Validate optimization results."""
        self.validated_at = datetime.utcnow()
        self.actual_improvement = Decimal(str(actual_improvement))
        self.impact_metrics = impact_metrics
        self.status = 'validated'
    
    def rollback_optimization(self) -> None:
        """Rollback optimization."""
        self.rollback_at = datetime.utcnow()
        self.status = 'rolled_back'
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get optimization summary."""
        return {
            'id': str(self.id),
            'name': self.name,
            'optimization_type': self.optimization_type,
            'target_component': self.target_component,
            'status': self.status,
            'priority': self.priority,
            'expected_improvement': float(self.expected_improvement) if self.expected_improvement else None,
            'actual_improvement': float(self.actual_improvement) if self.actual_improvement else None,
            'learning_pattern_id': str(self.learning_pattern_id) if self.learning_pattern_id else None,
            'scheduled_for': self.scheduled_for.isoformat() if self.scheduled_for else None,
            'implemented_at': self.implemented_at.isoformat() if self.implemented_at else None,
            'validated_at': self.validated_at.isoformat() if self.validated_at else None,
            'rollback_at': self.rollback_at.isoformat() if self.rollback_at else None,
        }


class OpenEvolveRun(AuditedModel, StatusMixin):
    """
    OpenEvolve evaluation runs and results.
    
    Tracks OpenEvolve framework evaluation runs for continuous
    system improvement and optimization.
    """
    __tablename__ = 'openevolve_runs'
    
    # Organization relationship
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    
    # Run identification
    run_name = Column(String(255), nullable=False)
    run_type = Column(String(100), nullable=False, default='evaluation')
    
    # Evaluation configuration
    evaluation_config = Column('evaluation_config', DatabaseModel.metadata.type, nullable=False, default=dict)
    target_metrics = Column('target_metrics', DatabaseModel.metadata.type, nullable=False, default=list)
    
    # Population and generation tracking
    population_size = Column(Integer, nullable=False, default=50)
    max_generations = Column(Integer, nullable=False, default=100)
    current_generation = Column(Integer, nullable=False, default=0)
    
    # Execution tracking
    started_at = Column('started_at', DatabaseModel.created_at.type, nullable=False)
    completed_at = Column('completed_at', DatabaseModel.created_at.type, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Results and metrics
    best_fitness = Column(Numeric(10, 6), nullable=True)
    average_fitness = Column(Numeric(10, 6), nullable=True)
    convergence_generation = Column(Integer, nullable=True)
    
    # Evolution results
    evolution_results = Column('evolution_results', DatabaseModel.metadata.type, nullable=False, default=dict)
    best_solution = Column('best_solution', DatabaseModel.metadata.type, nullable=True)
    fitness_history = Column('fitness_history', DatabaseModel.metadata.type, nullable=False, default=list)
    
    # Error handling
    error_details = Column('error_details', DatabaseModel.metadata.type, nullable=True)
    
    # Relationships
    organization = relationship("Organization")
    
    # Constraints
    __table_args__ = (
        Index('idx_openevolve_runs_org', 'organization_id'),
        Index('idx_openevolve_runs_type', 'run_type'),
        Index('idx_openevolve_runs_status', 'status'),
        Index('idx_openevolve_runs_started', 'started_at'),
        Index('idx_openevolve_runs_completed', 'completed_at'),
        Index('idx_openevolve_runs_fitness', 'best_fitness'),
        Index('idx_openevolve_runs_generation', 'current_generation'),
    )
    
    def __init__(self, organization_id: str, run_name: str, **kwargs):
        """Initialize OpenEvolve run with required fields."""
        super().__init__(
            organization_id=organization_id,
            run_name=run_name,
            started_at=datetime.utcnow(),
            **kwargs
        )
    
    def update_generation(self, generation: int, best_fitness: float, average_fitness: float) -> None:
        """Update generation progress."""
        self.current_generation = generation
        self.best_fitness = Decimal(str(best_fitness))
        self.average_fitness = Decimal(str(average_fitness))
        
        # Add to fitness history
        if not self.fitness_history:
            self.fitness_history = []
        
        self.fitness_history.append({
            'generation': generation,
            'best_fitness': best_fitness,
            'average_fitness': average_fitness,
            'timestamp': datetime.utcnow().isoformat(),
        })
    
    def complete_run(self, best_solution: Dict[str, Any], convergence_generation: Optional[int] = None) -> None:
        """Complete OpenEvolve run."""
        self.completed_at = datetime.utcnow()
        self.duration_minutes = int((self.completed_at - self.started_at).total_seconds() / 60)
        self.status = 'completed'
        self.best_solution = best_solution
        self.convergence_generation = convergence_generation
    
    def fail_run(self, error_details: Dict[str, Any]) -> None:
        """Mark run as failed."""
        self.completed_at = datetime.utcnow()
        self.duration_minutes = int((self.completed_at - self.started_at).total_seconds() / 60)
        self.status = 'failed'
        self.error_details = error_details
    
    def get_run_summary(self) -> Dict[str, Any]:
        """Get run summary."""
        return {
            'id': str(self.id),
            'run_name': self.run_name,
            'run_type': self.run_type,
            'status': self.status,
            'population_size': self.population_size,
            'max_generations': self.max_generations,
            'current_generation': self.current_generation,
            'best_fitness': float(self.best_fitness) if self.best_fitness else None,
            'average_fitness': float(self.average_fitness) if self.average_fitness else None,
            'convergence_generation': self.convergence_generation,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_minutes': self.duration_minutes,
            'has_error': self.error_details is not None,
            'fitness_history_length': len(self.fitness_history) if self.fitness_history else 0,
        }

