"""
Fish species and knowledge models
"""

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from .base import Base, TimestampMixin


class ActivityLevel(str, enum.Enum):
    """Fish activity level"""
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"


class FishSpecies(Base, TimestampMixin):
    """Fish species information"""

    __tablename__ = 'fish_species'

    species_id = Column(Integer, primary_key=True, autoincrement=True)
    name_cn = Column(String(100), nullable=False, unique=True, index=True, comment="Chinese name")
    name_en = Column(String(100), index=True, comment="English name")
    scientific_name = Column(String(100), comment="Scientific name")
    category = Column(String(50), index=True, comment="Fish category")
    habitat = Column(String(200), comment="Natural habitat")
    description = Column(Text, comment="Species description")
    image_url = Column(String(500), comment="Species image URL")
    min_weight = Column(Float, comment="Typical minimum weight in kg")
    max_weight = Column(Float, comment="Typical maximum weight in kg")
    min_length = Column(Float, comment="Typical minimum length in cm")
    max_length = Column(Float, comment="Typical maximum length in cm")

    # Relationships
    knowledge = relationship("FishKnowledge", back_populates="species", cascade="all, delete-orphan")
    season_activity = relationship("FishSeasonActivity", back_populates="species", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FishSpecies(id={self.species_id}, name_cn='{self.name_cn}')>"

    def to_dict(self, include_knowledge=False, include_seasons=False):
        """Convert to dictionary representation"""
        result = {
            'species_id': self.species_id,
            'name_cn': self.name_cn,
            'name_en': self.name_en,
            'scientific_name': self.scientific_name,
            'category': self.category,
            'habitat': self.habitat,
            'description': self.description,
            'image_url': self.image_url,
            'min_weight': self.min_weight,
            'max_weight': self.max_weight,
            'min_length': self.min_length,
            'max_length': self.max_length,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_knowledge:
            result['knowledge'] = [k.to_dict() for k in self.knowledge]

        if include_seasons:
            result['season_activity'] = [s.to_dict() for s in self.season_activity]

        return result


class FishKnowledge(Base, TimestampMixin):
    """Fish species knowledge base"""

    __tablename__ = 'fish_knowledge'

    id = Column(Integer, primary_key=True, autoincrement=True)
    species_id = Column(Integer, ForeignKey('fish_species.species_id', ondelete='CASCADE'), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True, comment="Knowledge topic")
    content = Column(Text, nullable=False, comment="Knowledge content")
    source = Column(String(200), comment="Information source")
    tags = Column(String(200), comment="Tags (comma separated)")

    # Relationships
    species = relationship("FishSpecies", back_populates="knowledge")

    def __repr__(self):
        return f"<FishKnowledge(id={self.id}, species_id={self.species_id}, topic='{self.topic}')>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'species_id': self.species_id,
            'topic': self.topic,
            'content': self.content,
            'source': self.source,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class FishSeasonActivity(Base, TimestampMixin):
    """Fish activity by season"""

    __tablename__ = 'fish_season_activity'

    id = Column(Integer, primary_key=True, autoincrement=True)
    species_id = Column(Integer, ForeignKey('fish_species.species_id', ondelete='CASCADE'), nullable=False, index=True)
    season = Column(String(20), nullable=False, index=True, comment="Season (spring/summer/fall/winter)")
    activity_level = Column(
        SQLEnum(ActivityLevel, native_enum=False),
        nullable=False,
        comment="Activity level"
    )
    best_time = Column(String(100), comment="Best fishing time")
    recommended_lures = Column(Text, comment="Recommended lures (comma separated)")
    fishing_tips = Column(Text, comment="Fishing tips for this season")

    # Relationships
    species = relationship("FishSpecies", back_populates="season_activity")

    def __repr__(self):
        return f"<FishSeasonActivity(species_id={self.species_id}, season='{self.season}', level='{self.activity_level}')>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'species_id': self.species_id,
            'season': self.season,
            'activity_level': self.activity_level.value if isinstance(self.activity_level, enum.Enum) else self.activity_level,
            'best_time': self.best_time,
            'recommended_lures': self.recommended_lures,
            'fishing_tips': self.fishing_tips,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
