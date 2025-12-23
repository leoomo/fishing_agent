"""
User-related models
"""

from sqlalchemy import Column, Integer, String, Text, Float, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from .base import Base, TimestampMixin


class ExperienceLevel(str, enum.Enum):
    """User fishing experience level"""
    BEGINNER = "新手"
    INTERMEDIATE = "进阶"
    ADVANCED = "高手"


class User(Base, TimestampMixin):
    """User model"""

    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="Username")
    nickname = Column(String(100), comment="Display nickname")
    email = Column(String(100), unique=True, index=True, comment="Email address")
    phone = Column(String(20), comment="Phone number")
    user_level = Column(
        String(20),
        index=True,
        comment="Fishing experience level"
    )
    fishing_experience_years = Column(Integer, comment="Years of fishing experience")
    preferred_fish = Column(String(200), comment="Preferred fish species (comma separated)")
    preferred_scenarios = Column(String(200), comment="Preferred fishing scenarios")
    # location 字段暂时保留，但数据库中不存在
    avatar_url = Column(String(500), comment="Avatar image URL")

    # Relationships
    equipment = relationship("UserEquipment", back_populates="user", cascade="all, delete-orphan")
    fishing_logs = relationship("FishingLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.user_id}, username='{self.username}', level='{self.user_level}')>"

    def to_dict(self, include_equipment=False, include_logs=False):
        """Convert to dictionary representation"""
        result = {
            'user_id': self.user_id,
            'username': self.username,
            'nickname': self.nickname,
            'email': self.email,
            'phone': self.phone,
            'user_level': self.user_level,
            'fishing_experience_years': self.fishing_experience_years,
            'preferred_fish': self.preferred_fish,
            'preferred_scenarios': self.preferred_scenarios,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_equipment:
            result['equipment'] = [eq.to_dict() for eq in self.equipment]

        if include_logs:
            result['fishing_logs'] = [log.to_dict() for log in self.fishing_logs]

        return result


class UserEquipment(Base, TimestampMixin):
    """User's equipment inventory"""

    __tablename__ = 'user_equipment'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    equipment_id = Column(Integer, ForeignKey('equipment.equipment_id', ondelete='CASCADE'), nullable=False, index=True)
    purchase_date = Column(Date, comment="Date of purchase")
    purchase_price = Column(Float, comment="Purchase price in CNY")
    condition = Column(String(20), comment="Equipment condition (new/good/fair/poor)")
    notes = Column(Text, comment="User notes about this equipment")
    is_favorite = Column(Integer, default=0, comment="Whether this is a favorite item (0/1)")

    # Relationships
    user = relationship("User", back_populates="equipment")
    equipment = relationship("Equipment", back_populates="user_equipment")

    def __repr__(self):
        return f"<UserEquipment(user_id={self.user_id}, equipment_id={self.equipment_id})>"

    def to_dict(self, include_equipment_details=True):
        """Convert to dictionary representation"""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'equipment_id': self.equipment_id,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'purchase_price': self.purchase_price,
            'condition': self.condition,
            'notes': self.notes,
            'is_favorite': bool(self.is_favorite),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_equipment_details and self.equipment:
            result['equipment'] = self.equipment.to_dict()

        return result


class FishingLog(Base, TimestampMixin):
    """User's fishing log/diary entries"""

    __tablename__ = 'fishing_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    location = Column(String(200), comment="Fishing location")
    date = Column(Date, nullable=False, index=True, comment="Fishing date")
    weather_condition = Column(String(100), comment="Weather conditions")
    temperature = Column(Float, comment="Temperature in Celsius")
    fish_caught = Column(String(200), comment="Fish species caught (comma separated)")
    total_count = Column(Integer, comment="Total number of fish caught")
    total_weight = Column(Float, comment="Total weight in kg")
    equipment_used = Column(Text, comment="Equipment used (JSON format)")
    notes = Column(Text, comment="Fishing notes and observations")
    images = Column(Text, comment="Image URLs (JSON array)")

    # Relationships
    user = relationship("User", back_populates="fishing_logs")

    def __repr__(self):
        return f"<FishingLog(id={self.id}, user_id={self.user_id}, date={self.date}, count={self.total_count})>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'location': self.location,
            'date': self.date.isoformat() if self.date else None,
            'weather_condition': self.weather_condition,
            'temperature': self.temperature,
            'fish_caught': self.fish_caught,
            'total_count': self.total_count,
            'total_weight': self.total_weight,
            'equipment_used': self.equipment_used,
            'notes': self.notes,
            'images': self.images,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
