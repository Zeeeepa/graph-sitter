"""
Base SQLAlchemy Models and Mixins

Provides base model classes, common mixins, and utilities for the
graph-sitter database system with consistent patterns across all modules.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import Session
from sqlalchemy.sql import func


class BaseModel:
    """Base model class with common functionality."""
    
    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name."""
        # Convert CamelCase to snake_case
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    def to_dict(self, exclude: Optional[list] = None) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        exclude = exclude or []
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                
                # Handle special types
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif isinstance(value, uuid.UUID):
                    value = str(value)
                
                result[column.name] = value
        
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude: Optional[list] = None) -> None:
        """Update model instance from dictionary."""
        exclude = exclude or ['id', 'created_at']
        
        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def create(cls, session: Session, **kwargs) -> 'BaseModel':
        """Create and save a new instance."""
        instance = cls(**kwargs)
        session.add(instance)
        session.flush()  # Get the ID without committing
        return instance
    
    def save(self, session: Session) -> 'BaseModel':
        """Save the instance to database."""
        session.add(self)
        session.flush()
        return self
    
    def delete(self, session: Session) -> None:
        """Delete the instance from database."""
        session.delete(self)
        session.flush()
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


class TimestampMixin:
    """Mixin for automatic timestamp management."""
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        server_onupdate=func.now()
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    def soft_delete(self, session: Session) -> None:
        """Soft delete the instance."""
        self.deleted_at = datetime.now(timezone.utc)
        self.is_deleted = True
        session.add(self)
        session.flush()
    
    def restore(self, session: Session) -> None:
        """Restore a soft-deleted instance."""
        self.deleted_at = None
        self.is_deleted = False
        session.add(self)
        session.flush()
    
    @classmethod
    def active_only(cls):
        """Query filter for non-deleted records."""
        return cls.is_deleted.is_(False)


class MetadataMixin:
    """Mixin for flexible metadata storage."""
    
    metadata = Column(JSON, nullable=False, default=dict)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set a metadata value."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata value."""
        if self.metadata is None:
            return default
        return self.metadata.get(key, default)
    
    def update_metadata(self, data: Dict[str, Any]) -> None:
        """Update multiple metadata values."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata.update(data)


class AuditMixin:
    """Mixin for audit trail functionality."""
    
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    def set_audit_info(self, user_id: str, is_update: bool = False) -> None:
        """Set audit information."""
        if is_update:
            self.updated_by = user_id
        else:
            self.created_by = user_id


class DescriptionMixin:
    """Mixin for models that have name and description."""
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    def __str__(self) -> str:
        """String representation using name."""
        return self.name


class StatusMixin:
    """Mixin for models with status tracking."""
    
    status = Column(String(50), nullable=False, default='active')
    
    def is_active(self) -> bool:
        """Check if the instance is active."""
        return self.status == 'active'
    
    def activate(self) -> None:
        """Activate the instance."""
        self.status = 'active'
    
    def deactivate(self) -> None:
        """Deactivate the instance."""
        self.status = 'inactive'


# Create the declarative base
Base = declarative_base(cls=BaseModel)


class DatabaseModel(Base, TimestampMixin, MetadataMixin):
    """
    Enhanced base model with all common functionality.
    
    This is the recommended base class for all database models
    as it includes timestamps and metadata support by default.
    """
    __abstract__ = True


class AuditedModel(DatabaseModel, AuditMixin, SoftDeleteMixin):
    """
    Fully audited model with soft delete support.
    
    Use this for models that require full audit trails
    and soft delete functionality.
    """
    __abstract__ = True


# Utility functions for model operations
def get_or_create(session: Session, model_class, defaults: Optional[Dict] = None, **kwargs):
    """Get an existing instance or create a new one."""
    instance = session.query(model_class).filter_by(**kwargs).first()
    
    if instance:
        return instance, False
    else:
        params = kwargs.copy()
        if defaults:
            params.update(defaults)
        instance = model_class(**params)
        session.add(instance)
        session.flush()
        return instance, True


def bulk_create(session: Session, model_class, data_list: list) -> list:
    """Create multiple instances efficiently."""
    instances = [model_class(**data) for data in data_list]
    session.add_all(instances)
    session.flush()
    return instances


def paginate_query(query, page: int = 1, per_page: int = 50):
    """Add pagination to a query."""
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 1000:
        per_page = 50
    
    offset = (page - 1) * per_page
    total = query.count()
    items = query.offset(offset).limit(per_page).all()
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
        'has_prev': page > 1,
        'has_next': page * per_page < total,
    }


def apply_filters(query, model_class, filters: Dict[str, Any]):
    """Apply filters to a query dynamically."""
    for field, value in filters.items():
        if hasattr(model_class, field):
            column = getattr(model_class, field)
            
            if isinstance(value, dict):
                # Handle complex filters like {'gt': 10}, {'in': [1, 2, 3]}
                for op, op_value in value.items():
                    if op == 'gt':
                        query = query.filter(column > op_value)
                    elif op == 'gte':
                        query = query.filter(column >= op_value)
                    elif op == 'lt':
                        query = query.filter(column < op_value)
                    elif op == 'lte':
                        query = query.filter(column <= op_value)
                    elif op == 'in':
                        query = query.filter(column.in_(op_value))
                    elif op == 'not_in':
                        query = query.filter(~column.in_(op_value))
                    elif op == 'like':
                        query = query.filter(column.like(f"%{op_value}%"))
                    elif op == 'ilike':
                        query = query.filter(column.ilike(f"%{op_value}%"))
            else:
                # Simple equality filter
                query = query.filter(column == value)
    
    return query

