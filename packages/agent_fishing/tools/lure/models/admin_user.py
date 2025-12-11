"""
Admin user model for backend management
"""

from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from .base import Base, TimestampMixin


class RoleEnum(str, enum.Enum):
    """Admin user role enumeration"""
    ADMIN = "admin"
    EDITOR = "editor"
    READONLY = "readonly"


class AdminUser(Base, TimestampMixin):
    """Administrator user model for backend management"""

    __tablename__ = 'admin_users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="Admin username")
    email = Column(String(100), unique=True, nullable=False, index=True, comment="Admin email")
    password_hash = Column(String(255), nullable=False, comment="Hashed password (bcrypt)")
    full_name = Column(String(100), comment="Full name")
    role = Column(
        SQLEnum(RoleEnum, native_enum=False),
        nullable=False,
        default=RoleEnum.READONLY,
        index=True,
        comment="User role"
    )
    is_active = Column(Boolean, default=True, nullable=False, index=True, comment="Whether user is active")
    last_login = Column(String(50), comment="Last login timestamp (ISO format)")

    # Relationships (lazy loading to avoid dependency issues)
    configs_modified = relationship("SystemConfig", back_populates="modifier", lazy='noload')
    reports_generated = relationship("AnalyticsReport", back_populates="generator", lazy='noload')
    created_workflow_templates = relationship("CrawlerWorkflowTemplate", back_populates="creator", lazy='noload')
    created_schedules = relationship("CrawlerSchedule", back_populates="creator", lazy='noload')

    def __repr__(self):
        return f"<AdminUser(id={self.id}, username='{self.username}', role='{self.role}')>"

    def to_dict(self, include_password=False):
        """Convert to dictionary representation"""
        result = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role.value if isinstance(self.role, enum.Enum) else self.role,
            'is_active': self.is_active,
            'last_login': self.last_login,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_password:
            result['password_hash'] = self.password_hash

        return result
