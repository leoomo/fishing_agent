"""
Fishing rig models
"""

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class RigType(Base, TimestampMixin):
    """Fishing rig type/configuration"""

    __tablename__ = 'rig_types'

    rig_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True, comment="Rig name")
    category = Column(String(50), index=True, comment="Rig category")
    description = Column(Text, comment="Rig description")
    diagram_url = Column(String(500), comment="Rig diagram image URL")
    difficulty = Column(String(20), comment="Setup difficulty (easy/medium/hard)")
    target_species = Column(String(200), comment="Target fish species")
    best_conditions = Column(Text, comment="Best fishing conditions")

    # Relationships
    specs = relationship("RigSpec", back_populates="rig_type", cascade="all, delete-orphan")
    components = relationship("RigComponent", back_populates="rig_type", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RigType(id={self.rig_id}, name='{self.name}', category='{self.category}')>"

    def to_dict(self, include_specs=False, include_components=False):
        """Convert to dictionary representation"""
        result = {
            'rig_id': self.rig_id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'diagram_url': self.diagram_url,
            'difficulty': self.difficulty,
            'target_species': self.target_species,
            'best_conditions': self.best_conditions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_specs:
            result['specs'] = [spec.to_dict() for spec in self.specs]

        if include_components:
            result['components'] = [comp.to_dict() for comp in self.components]

        return result


class RigSpec(Base, TimestampMixin):
    """Rig specifications"""

    __tablename__ = 'rig_specs'

    spec_id = Column(Integer, primary_key=True, autoincrement=True)
    rig_id = Column(Integer, ForeignKey('rig_types.rig_id', ondelete='CASCADE'), nullable=False, index=True)
    spec_name = Column(String(100), nullable=False, comment="Specification name")
    spec_value = Column(String(200), comment="Specification value")
    unit = Column(String(20), comment="Unit of measurement")
    notes = Column(Text, comment="Additional notes")

    # Relationships
    rig_type = relationship("RigType", back_populates="specs")

    def __repr__(self):
        return f"<RigSpec(rig_id={self.rig_id}, name='{self.spec_name}', value='{self.spec_value}')>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'spec_id': self.spec_id,
            'rig_id': self.rig_id,
            'spec_name': self.spec_name,
            'spec_value': self.spec_value,
            'unit': self.unit,
            'notes': self.notes,
        }


class RigComponent(Base, TimestampMixin):
    """Rig components/parts"""

    __tablename__ = 'rig_components'

    component_id = Column(Integer, primary_key=True, autoincrement=True)
    rig_id = Column(Integer, ForeignKey('rig_types.rig_id', ondelete='CASCADE'), nullable=False, index=True)
    component_name = Column(String(100), nullable=False, comment="Component name")
    component_type = Column(String(50), index=True, comment="Component type (hook/sinker/swivel/etc)")
    quantity = Column(Integer, comment="Quantity needed")
    size = Column(String(50), comment="Component size")
    position = Column(Integer, comment="Position in rig assembly")
    notes = Column(Text, comment="Assembly notes")

    # Relationships
    rig_type = relationship("RigType", back_populates="components")

    def __repr__(self):
        return f"<RigComponent(rig_id={self.rig_id}, name='{self.component_name}', type='{self.component_type}')>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'component_id': self.component_id,
            'rig_id': self.rig_id,
            'component_name': self.component_name,
            'component_type': self.component_type,
            'quantity': self.quantity,
            'size': self.size,
            'position': self.position,
            'notes': self.notes,
        }
