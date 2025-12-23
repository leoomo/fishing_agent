"""
Lure type and rod-lure fitness models
"""

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class LureType(Base, TimestampMixin):
    """Lure type classification"""

    __tablename__ = 'lure_types'

    lure_type_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True, comment="Lure type name")
    category = Column(String(50), index=True, comment="Lure category (hard/soft)")
    description = Column(Text, comment="Lure type description")
    action_description = Column(Text, comment="How the lure moves/acts")
    best_conditions = Column(Text, comment="Best fishing conditions")
    target_species = Column(String(200), comment="Target fish species")
    typical_weight_min = Column(Float, comment="Typical minimum weight in grams")
    typical_weight_max = Column(Float, comment="Typical maximum weight in grams")
    image_url = Column(String(500), comment="Lure type image URL")

    # Relationships
    rod_fitness = relationship("RodLureFitness", back_populates="lure_type", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LureType(id={self.lure_type_id}, name='{self.name}', category='{self.category}')>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'lure_type_id': self.lure_type_id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'action_description': self.action_description,
            'best_conditions': self.best_conditions,
            'target_species': self.target_species,
            'typical_weight_min': self.typical_weight_min,
            'typical_weight_max': self.typical_weight_max,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class RodLureFitness(Base, TimestampMixin):
    """Rod and lure type compatibility matrix"""

    __tablename__ = 'rod_lure_fitness'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rod_power = Column(String(20), nullable=False, index=True, comment="Rod power (UL/L/ML/M/MH/H/XH)")
    lure_type_id = Column(Integer, ForeignKey('lure_types.lure_type_id', ondelete='CASCADE'), nullable=False, index=True)
    fitness_score = Column(Float, nullable=False, comment="Compatibility score (0-100)")
    weight_range_min = Column(Float, comment="Recommended minimum lure weight in grams")
    weight_range_max = Column(Float, comment="Recommended maximum lure weight in grams")
    notes = Column(Text, comment="Compatibility notes")

    # Relationships
    lure_type = relationship("LureType", back_populates="rod_fitness")

    def __repr__(self):
        return f"<RodLureFitness(rod_power='{self.rod_power}', lure_type_id={self.lure_type_id}, score={self.fitness_score})>"

    def to_dict(self, include_lure_type=False):
        """Convert to dictionary representation"""
        result = {
            'id': self.id,
            'rod_power': self.rod_power,
            'lure_type_id': self.lure_type_id,
            'fitness_score': self.fitness_score,
            'weight_range_min': self.weight_range_min,
            'weight_range_max': self.weight_range_max,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_lure_type and self.lure_type:
            result['lure_type'] = self.lure_type.to_dict()

        return result
