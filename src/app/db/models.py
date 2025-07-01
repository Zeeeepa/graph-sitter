"""
Database models for the application.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship, Mapped
from .base import Base

class User(Base):
    """User model."""
    __tablename__ = "users"

    id: Mapped[int] = Column(Integer, primary_key=True)
    github_id: Mapped[str] = Column(String(100), unique=True, index=True)
    email: Mapped[str] = Column(String(100), unique=True, index=True)
    username: Mapped[str] = Column(String(100), unique=True, index=True)
    is_active: Mapped[bool] = Column(Boolean, default=True)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    repositories: Mapped[List["Repository"]] = relationship("Repository", back_populates="user")
    secrets: Mapped[List["Secret"]] = relationship("Secret", back_populates="user")

class Repository(Base):
    """Repository model."""
    __tablename__ = "repositories"

    id: Mapped[int] = Column(Integer, primary_key=True)
    github_id: Mapped[int] = Column(Integer, unique=True, index=True)
    name: Mapped[str] = Column(String(200))
    full_name: Mapped[str] = Column(String(200), unique=True, index=True)
    is_private: Mapped[bool] = Column(Boolean, default=False)
    is_pinned: Mapped[bool] = Column(Boolean, default=False)
    webhook_id: Mapped[Optional[int]] = Column(Integer, nullable=True)
    webhook_secret: Mapped[Optional[str]] = Column(String(100), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    user_id: Mapped[int] = Column(Integer, ForeignKey("users.id"))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="repositories")
    validation_workflows: Mapped[List["ValidationWorkflow"]] = relationship("ValidationWorkflow", back_populates="repository")
    sandboxes: Mapped[List["Sandbox"]] = relationship("Sandbox", back_populates="repository")

class ValidationWorkflow(Base):
    """Validation workflow model."""
    __tablename__ = "validation_workflows"

    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String(200))
    is_active: Mapped[bool] = Column(Boolean, default=True)
    setup_commands: Mapped[str] = Column(Text)  # Commands separated by newlines
    rules: Mapped[dict] = Column(JSON)  # Repository-specific rules
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    repository_id: Mapped[int] = Column(Integer, ForeignKey("repositories.id"))

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="validation_workflows")
    sandboxes: Mapped[List["Sandbox"]] = relationship("Sandbox", back_populates="validation_workflow")

class Sandbox(Base):
    """Sandbox environment model."""
    __tablename__ = "sandboxes"

    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String(200))
    status: Mapped[str] = Column(String(50))  # active, completed, failed
    environment_vars: Mapped[dict] = Column(JSON)
    results: Mapped[Optional[dict]] = Column(JSON, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    repository_id: Mapped[int] = Column(Integer, ForeignKey("repositories.id"))
    validation_workflow_id: Mapped[int] = Column(Integer, ForeignKey("validation_workflows.id"))

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="sandboxes")
    validation_workflow: Mapped["ValidationWorkflow"] = relationship("ValidationWorkflow", back_populates="sandboxes")

class Secret(Base):
    """Encrypted secrets model."""
    __tablename__ = "secrets"

    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String(200))
    encrypted_value: Mapped[str] = Column(Text)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    user_id: Mapped[int] = Column(Integer, ForeignKey("users.id"))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="secrets")

