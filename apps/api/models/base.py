"""
Base models and mixins for SQLAlchemy ORM
"""

from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_base

# Create declarative base
Base = declarative_base()


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamp columns"""

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Record creation timestamp"
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Record last update timestamp"
    )

    def __repr__(self):
        """String representation including timestamps"""
        class_name = self.__class__.__name__
        if hasattr(self, 'id'):
            return f"<{class_name}(id={self.id}, created_at={self.created_at})>"
        return f"<{class_name}(created_at={self.created_at})>"
