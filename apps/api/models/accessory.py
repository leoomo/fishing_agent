"""
Fishing accessory models - hooks, sinkers, swivels, leaders, floats, etc.
"""

from sqlalchemy import Column, Integer, String, Text, Float

from .base import Base, TimestampMixin


class Accessory(Base, TimestampMixin):
    """Fishing accessory model for hooks, sinkers, swivels, leaders, floats, etc."""

    __tablename__ = 'accessories'

    accessory_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True, comment="Accessory name")
    category = Column(String(50), nullable=False, index=True, comment="Category: hook/sinker/swivel/leader/float/snap/other")
    description = Column(Text, comment="Detailed description")
    features = Column(Text, comment="Key features")

    # Specifications
    size = Column(String(50), comment="Size/specification (e.g., #4, 3/0, 1.5g)")
    weight = Column(Float, comment="Weight in grams")
    material = Column(String(100), comment="Material (e.g., carbon steel, tungsten, fluorocarbon)")
    color = Column(String(100), comment="Color/pattern")
    quantity_per_pack = Column(Integer, comment="Quantity per package")

    # Application
    target_species = Column(String(200), comment="Target fish species")
    applicable_rigs = Column(String(200), comment="Applicable rig types (e.g., Texas, Carolina, drop shot)")
    best_conditions = Column(Text, comment="Best fishing conditions")

    # Commercial info
    brand = Column(String(100), comment="Brand name")
    price_min = Column(Float, comment="Minimum price in CNY")
    price_max = Column(Float, comment="Maximum price in CNY")
    user_level = Column(String(20), default="beginner", comment="Recommended level: beginner/intermediate/advanced")

    # Media
    image_url = Column(String(500), comment="Image URL")

    def __repr__(self):
        return f"<Accessory(id={self.accessory_id}, name='{self.name}', category='{self.category}')>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'accessory_id': self.accessory_id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'features': self.features,
            'size': self.size,
            'weight': self.weight,
            'material': self.material,
            'color': self.color,
            'quantity_per_pack': self.quantity_per_pack,
            'target_species': self.target_species,
            'applicable_rigs': self.applicable_rigs,
            'best_conditions': self.best_conditions,
            'brand': self.brand,
            'price_min': self.price_min,
            'price_max': self.price_max,
            'user_level': self.user_level,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
