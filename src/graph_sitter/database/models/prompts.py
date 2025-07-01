"""
Prompts and Templates Models

Dynamic prompt management and effectiveness tracking models
for AI-powered development workflows.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, UniqueConstraint, Index, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Session

from ..base import DatabaseModel, AuditedModel, DescriptionMixin, StatusMixin


class PromptTemplate(AuditedModel, DescriptionMixin, StatusMixin):
    """
    Reusable prompt templates with variable substitution.
    
    Manages prompt templates for AI interactions with variable substitution,
    effectiveness tracking, and A/B testing capabilities.
    """
    __tablename__ = 'prompt_templates'
    
    # Organization relationship
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    
    # Template identification
    category = Column(String(100), nullable=False, default='general')
    version = Column(String(20), nullable=False, default='1.0.0')
    
    # Template content
    template_content = Column(Text, nullable=False)
    variables = Column('variables', DatabaseModel.metadata.type, nullable=False, default=list)
    
    # Model configuration
    model_name = Column(String(100), nullable=True)
    model_parameters = Column('model_parameters', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Usage and effectiveness tracking
    usage_count = Column(Integer, nullable=False, default=0)
    success_rate = Column(Numeric(5, 2), nullable=True)
    average_response_time_ms = Column(Integer, nullable=True)
    average_cost = Column(Numeric(10, 4), nullable=True)
    
    # A/B testing
    is_variant = Column(Boolean, nullable=False, default=False)
    parent_template_id = Column(UUID(as_uuid=True), ForeignKey('prompt_templates.id', ondelete='CASCADE'), nullable=True)
    variant_weight = Column(Numeric(3, 2), nullable=False, default=1.0)
    
    # Relationships
    organization = relationship("Organization")
    parent_template = relationship("PromptTemplate", remote_side="PromptTemplate.id", back_populates="variants")
    variants = relationship("PromptTemplate", back_populates="parent_template", cascade="all, delete-orphan")
    executions = relationship("PromptExecution", back_populates="template", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'name', 'version', name='uq_prompt_template_org_name_version'),
        Index('idx_prompt_templates_org', 'organization_id'),
        Index('idx_prompt_templates_category', 'category'),
        Index('idx_prompt_templates_status', 'status'),
        Index('idx_prompt_templates_usage', 'usage_count'),
        Index('idx_prompt_templates_success_rate', 'success_rate'),
        Index('idx_prompt_templates_parent', 'parent_template_id'),
    )
    
    def __init__(self, organization_id: str, name: str, template_content: str, **kwargs):
        """Initialize prompt template with required fields."""
        super().__init__(
            organization_id=organization_id,
            name=name,
            template_content=template_content,
            **kwargs
        )
    
    def render_template(self, variables: Dict[str, Any]) -> str:
        """Render template with variable substitution."""
        content = self.template_content
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            content = content.replace(placeholder, str(var_value))
        return content
    
    def create_execution(self, session: Session, variables: Dict[str, Any], **kwargs) -> 'PromptExecution':
        """Create a new prompt execution."""
        rendered_prompt = self.render_template(variables)
        
        execution = PromptExecution(
            organization_id=self.organization_id,
            template=self,
            rendered_prompt=rendered_prompt,
            input_variables=variables,
            **kwargs
        )
        
        # Increment usage count
        self.usage_count += 1
        
        session.add(execution)
        session.add(self)
        return execution
    
    def get_template_stats(self) -> Dict[str, Any]:
        """Get template statistics."""
        return {
            'id': str(self.id),
            'name': self.name,
            'category': self.category,
            'version': self.version,
            'status': self.status,
            'usage_count': self.usage_count,
            'success_rate': float(self.success_rate) if self.success_rate else None,
            'average_response_time_ms': self.average_response_time_ms,
            'average_cost': float(self.average_cost) if self.average_cost else None,
            'is_variant': self.is_variant,
            'variant_count': len(self.variants) if hasattr(self, 'variants') else 0,
            'execution_count': len(self.executions) if hasattr(self, 'executions') else 0,
        }


class PromptExecution(DatabaseModel, AuditedModel):
    """
    Prompt execution tracking and results.
    
    Tracks individual prompt executions with performance metrics,
    cost tracking, and effectiveness scoring.
    """
    __tablename__ = 'prompt_executions'
    
    # Organization and template relationships
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey('prompt_templates.id', ondelete='CASCADE'), nullable=False)
    
    # Execution context
    context_source_id = Column(UUID(as_uuid=True), ForeignKey('context_sources.id', ondelete='SET NULL'), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Prompt content
    rendered_prompt = Column(Text, nullable=False)
    input_variables = Column('input_variables', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Model execution
    model_name = Column(String(100), nullable=True)
    model_parameters = Column('model_parameters', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Response and results
    response_content = Column(Text, nullable=True)
    response_metadata = Column('response_metadata', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Performance metrics
    execution_time_ms = Column(Integer, nullable=True)
    token_count_input = Column(Integer, nullable=True)
    token_count_output = Column(Integer, nullable=True)
    cost = Column(Numeric(10, 4), nullable=True)
    
    # Quality and effectiveness
    success = Column(Boolean, nullable=True)
    effectiveness_score = Column(Numeric(5, 2), nullable=True)
    user_feedback = Column('user_feedback', DatabaseModel.metadata.type, nullable=True)
    
    # Error handling
    error_details = Column('error_details', DatabaseModel.metadata.type, nullable=True)
    
    # Relationships
    organization = relationship("Organization")
    template = relationship("PromptTemplate", back_populates="executions")
    context_source = relationship("ContextSource")
    user = relationship("User")
    
    # Constraints
    __table_args__ = (
        Index('idx_prompt_executions_org', 'organization_id'),
        Index('idx_prompt_executions_template', 'template_id'),
        Index('idx_prompt_executions_context', 'context_source_id'),
        Index('idx_prompt_executions_user', 'user_id'),
        Index('idx_prompt_executions_success', 'success'),
        Index('idx_prompt_executions_effectiveness', 'effectiveness_score'),
        Index('idx_prompt_executions_created', 'created_at'),
    )
    
    def __init__(self, organization_id: str, template_id: str, rendered_prompt: str, **kwargs):
        """Initialize prompt execution with required fields."""
        super().__init__(
            organization_id=organization_id,
            template_id=template_id,
            rendered_prompt=rendered_prompt,
            **kwargs
        )
    
    def complete_execution(self, response_content: str, success: bool = True, **metrics) -> None:
        """Complete prompt execution with results."""
        self.response_content = response_content
        self.success = success
        
        # Update metrics
        self.execution_time_ms = metrics.get('execution_time_ms')
        self.token_count_input = metrics.get('token_count_input')
        self.token_count_output = metrics.get('token_count_output')
        self.cost = metrics.get('cost')
        self.effectiveness_score = metrics.get('effectiveness_score')
        self.response_metadata = metrics.get('response_metadata', {})
    
    def fail_execution(self, error_details: Dict[str, Any]) -> None:
        """Mark execution as failed."""
        self.success = False
        self.error_details = error_details
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary."""
        return {
            'id': str(self.id),
            'template_id': str(self.template_id),
            'template_name': self.template.name if self.template else None,
            'success': self.success,
            'execution_time_ms': self.execution_time_ms,
            'token_count_input': self.token_count_input,
            'token_count_output': self.token_count_output,
            'cost': float(self.cost) if self.cost else None,
            'effectiveness_score': float(self.effectiveness_score) if self.effectiveness_score else None,
            'created_at': self.created_at.isoformat(),
            'has_error': self.error_details is not None,
        }


class ContextSource(AuditedModel, DescriptionMixin, StatusMixin):
    """
    Context data source management.
    
    Manages dynamic context data sources for prompt enrichment
    with caching and expiration policies.
    """
    __tablename__ = 'context_sources'
    
    # Organization relationship
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    
    # Source configuration
    source_type = Column(String(100), nullable=False)  # codebase, repository, file, api, static
    source_config = Column('source_config', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Caching configuration
    cache_ttl_seconds = Column(Integer, nullable=False, default=3600)
    auto_refresh = Column(Boolean, nullable=False, default=True)
    
    # Usage tracking
    usage_count = Column(Integer, nullable=False, default=0)
    last_accessed_at = Column('last_accessed_at', DatabaseModel.created_at.type, nullable=True)
    
    # Relationships
    organization = relationship("Organization")
    executions = relationship("PromptExecution", back_populates="context_source")
    
    # Constraints
    __table_args__ = (
        Index('idx_context_sources_org', 'organization_id'),
        Index('idx_context_sources_type', 'source_type'),
        Index('idx_context_sources_status', 'status'),
        Index('idx_context_sources_usage', 'usage_count'),
        Index('idx_context_sources_accessed', 'last_accessed_at'),
    )
    
    def __init__(self, organization_id: str, name: str, source_type: str, **kwargs):
        """Initialize context source with required fields."""
        super().__init__(
            organization_id=organization_id,
            name=name,
            source_type=source_type,
            **kwargs
        )
    
    def get_context_data(self) -> Dict[str, Any]:
        """Get context data from source."""
        # Update usage tracking
        self.usage_count += 1
        self.last_accessed_at = datetime.utcnow()
        
        # This would be implemented based on source_type
        # For now, return configuration as context
        return {
            'source_name': self.name,
            'source_type': self.source_type,
            'config': self.source_config,
            'last_updated': self.updated_at.isoformat(),
        }
    
    def get_source_stats(self) -> Dict[str, Any]:
        """Get context source statistics."""
        return {
            'id': str(self.id),
            'name': self.name,
            'source_type': self.source_type,
            'status': self.status,
            'usage_count': self.usage_count,
            'cache_ttl_seconds': self.cache_ttl_seconds,
            'auto_refresh': self.auto_refresh,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            'execution_count': len(self.executions) if hasattr(self, 'executions') else 0,
        }

