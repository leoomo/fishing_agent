"""
Base models and mixins for SQLAlchemy ORM

独立的基类定义，不依赖 agent_fishing
"""

from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_base

# Create declarative base for scraper models
Base = declarative_base()


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamp columns"""

    created_at = Column(
        DateTime,
        default=datetime.now,
        nullable=False,
        comment="Record creation timestamp (local time)"
    )

    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
        comment="Record last update timestamp (local time)"
    )

    def __repr__(self):
        """String representation including timestamps"""
        class_name = self.__class__.__name__
        if hasattr(self, 'id'):
            return f"<{class_name}(id={self.id}, created_at={self.created_at})>"
        return f"<{class_name}(created_at={self.created_at})>"
