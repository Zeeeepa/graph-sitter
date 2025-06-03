"""
Organizations and Users Models

Multi-tenant foundation models providing organization-based isolation
and user management with role-based access control.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import Column, String, Boolean, ForeignKey, UniqueConstraint, Index, Text
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship, Session

from ..base import DatabaseModel, AuditedModel, DescriptionMixin, StatusMixin


# Define enums
USER_ROLE_ENUM = ENUM(
    'owner', 'admin', 'member', 'viewer',
    name='user_role',
    create_type=False  # Type already created in extensions.sql
)

STATUS_TYPE_ENUM = ENUM(
    'active', 'inactive', 'pending', 'suspended', 'deleted',
    name='status_type', 
    create_type=False
)


class Organization(AuditedModel, DescriptionMixin, StatusMixin):
    """
    Organization model for multi-tenant architecture.
    
    Provides top-level tenant isolation with settings and configuration
    management. All other entities are scoped to an organization.
    """
    __tablename__ = 'organizations'
    
    # Basic information
    slug = Column(String(100), unique=True, nullable=False, index=True)
    
    # Configuration
    settings = Column('settings', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Subscription and limits
    subscription_tier = Column(String(50), nullable=False, default='free')
    max_users = Column('max_users', DatabaseModel.metadata.type, nullable=False, default=10)
    max_repositories = Column('max_repositories', DatabaseModel.metadata.type, nullable=False, default=5)
    
    # Relationships
    memberships = relationship("OrganizationMembership", back_populates="organization", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="organization", cascade="all, delete-orphan")
    repositories = relationship("Repository", back_populates="organization", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        Index('idx_organizations_slug', 'slug'),
        Index('idx_organizations_status', 'status'),
        Index('idx_organizations_subscription', 'subscription_tier'),
    )
    
    def __init__(self, name: str, slug: str, **kwargs):
        """Initialize organization with required fields."""
        super().__init__(name=name, slug=slug, **kwargs)
    
    @property
    def active_users(self) -> List['User']:
        """Get all active users in the organization."""
        return [m.user for m in self.memberships if m.user.status == 'active']
    
    @property
    def admin_users(self) -> List['User']:
        """Get all admin users in the organization."""
        return [m.user for m in self.memberships if m.role in ['owner', 'admin']]
    
    def get_user_role(self, user_id: str) -> Optional[str]:
        """Get the role of a user in this organization."""
        for membership in self.memberships:
            if str(membership.user_id) == user_id:
                return membership.role
        return None
    
    def has_user_permission(self, user_id: str, required_role: str) -> bool:
        """Check if a user has the required permission level."""
        user_role = self.get_user_role(user_id)
        if not user_role:
            return False
        
        role_hierarchy = {'viewer': 1, 'member': 2, 'admin': 3, 'owner': 4}
        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)
    
    def add_user(self, session: Session, user: 'User', role: str = 'member', 
                 invited_by: Optional['User'] = None) -> 'OrganizationMembership':
        """Add a user to the organization."""
        membership = OrganizationMembership(
            organization=self,
            user=user,
            role=role,
            invited_by=invited_by
        )
        session.add(membership)
        return membership
    
    def remove_user(self, session: Session, user: 'User') -> bool:
        """Remove a user from the organization."""
        membership = session.query(OrganizationMembership).filter_by(
            organization_id=self.id,
            user_id=user.id
        ).first()
        
        if membership:
            session.delete(membership)
            return True
        return False
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get organization usage statistics."""
        return {
            'total_users': len(self.memberships),
            'active_users': len(self.active_users),
            'total_projects': len(self.projects) if hasattr(self, 'projects') else 0,
            'total_repositories': len(self.repositories) if hasattr(self, 'repositories') else 0,
            'subscription_tier': self.subscription_tier,
            'max_users': self.max_users,
            'max_repositories': self.max_repositories,
        }


class User(AuditedModel, StatusMixin):
    """
    User model with external platform integration.
    
    Supports integration with GitHub, Linear, Slack and other platforms
    through external_ids JSONB field.
    """
    __tablename__ = 'users'
    
    # Basic information
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    avatar_url = Column(Text, nullable=True)
    
    # Settings and preferences
    settings = Column('settings', DatabaseModel.metadata.type, nullable=False, default=dict)
    preferences = Column('preferences', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # External platform integration
    external_ids = Column('external_ids', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Activity tracking
    last_active_at = Column('last_active_at', DatabaseModel.created_at.type, nullable=True)
    
    # Relationships
    memberships = relationship("OrganizationMembership", back_populates="user", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_status', 'status'),
        Index('idx_users_last_active', 'last_active_at'),
        Index('idx_users_external_ids_gin', 'external_ids', postgresql_using='gin'),
    )
    
    def __init__(self, email: str, name: str, **kwargs):
        """Initialize user with required fields."""
        super().__init__(email=email, name=name, **kwargs)
    
    @property
    def organizations(self) -> List[Organization]:
        """Get all organizations the user belongs to."""
        return [m.organization for m in self.memberships]
    
    def get_organization_role(self, organization_id: str) -> Optional[str]:
        """Get the user's role in a specific organization."""
        for membership in self.memberships:
            if str(membership.organization_id) == organization_id:
                return membership.role
        return None
    
    def is_member_of(self, organization: Organization) -> bool:
        """Check if user is a member of the organization."""
        return any(m.organization_id == organization.id for m in self.memberships)
    
    def has_permission_in_org(self, organization: Organization, required_role: str) -> bool:
        """Check if user has required permission in organization."""
        return organization.has_user_permission(str(self.id), required_role)
    
    def set_external_id(self, platform: str, external_id: str) -> None:
        """Set external ID for a platform."""
        if self.external_ids is None:
            self.external_ids = {}
        self.external_ids[platform] = external_id
    
    def get_external_id(self, platform: str) -> Optional[str]:
        """Get external ID for a platform."""
        if self.external_ids is None:
            return None
        return self.external_ids.get(platform)
    
    def update_last_active(self) -> None:
        """Update the last active timestamp."""
        self.last_active_at = datetime.utcnow()
    
    def get_profile_data(self) -> Dict[str, Any]:
        """Get user profile data."""
        return {
            'id': str(self.id),
            'email': self.email,
            'name': self.name,
            'avatar_url': self.avatar_url,
            'status': self.status,
            'last_active_at': self.last_active_at.isoformat() if self.last_active_at else None,
            'organizations': [
                {
                    'id': str(m.organization.id),
                    'name': m.organization.name,
                    'role': m.role
                }
                for m in self.memberships
            ]
        }


class OrganizationMembership(DatabaseModel, AuditedModel):
    """
    Organization membership model with role-based access control.
    
    Manages the many-to-many relationship between users and organizations
    with role assignment and invitation tracking.
    """
    __tablename__ = 'organization_memberships'
    
    # Foreign keys
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Role and permissions
    role = Column(USER_ROLE_ENUM, nullable=False, default='member')
    permissions = Column('permissions', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Invitation tracking
    invited_by_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    invited_at = Column('invited_at', DatabaseModel.created_at.type, nullable=True)
    joined_at = Column('joined_at', DatabaseModel.created_at.type, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="memberships")
    user = relationship("User", back_populates="memberships", foreign_keys=[user_id])
    invited_by = relationship("User", foreign_keys=[invited_by_id])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'user_id', name='uq_org_user_membership'),
        Index('idx_memberships_org', 'organization_id'),
        Index('idx_memberships_user', 'user_id'),
        Index('idx_memberships_role', 'role'),
        Index('idx_memberships_invited_by', 'invited_by_id'),
    )
    
    def __init__(self, organization: Organization, user: User, role: str = 'member', 
                 invited_by: Optional[User] = None, **kwargs):
        """Initialize membership with required relationships."""
        super().__init__(
            organization=organization,
            user=user,
            role=role,
            invited_by=invited_by,
            invited_at=datetime.utcnow() if invited_by else None,
            joined_at=datetime.utcnow(),
            **kwargs
        )
    
    def has_permission(self, permission: str) -> bool:
        """Check if the membership has a specific permission."""
        if self.permissions is None:
            return False
        return self.permissions.get(permission, False)
    
    def grant_permission(self, permission: str) -> None:
        """Grant a specific permission."""
        if self.permissions is None:
            self.permissions = {}
        self.permissions[permission] = True
    
    def revoke_permission(self, permission: str) -> None:
        """Revoke a specific permission."""
        if self.permissions is None:
            self.permissions = {}
        self.permissions[permission] = False
    
    def can_manage_users(self) -> bool:
        """Check if the user can manage other users."""
        return self.role in ['owner', 'admin']
    
    def can_manage_projects(self) -> bool:
        """Check if the user can manage projects."""
        return self.role in ['owner', 'admin', 'member']
    
    def can_view_analytics(self) -> bool:
        """Check if the user can view analytics."""
        return self.role in ['owner', 'admin', 'member']
    
    def get_membership_info(self) -> Dict[str, Any]:
        """Get membership information."""
        return {
            'organization_id': str(self.organization_id),
            'organization_name': self.organization.name,
            'user_id': str(self.user_id),
            'user_name': self.user.name,
            'role': self.role,
            'permissions': self.permissions or {},
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'invited_by': self.invited_by.name if self.invited_by else None,
        }

