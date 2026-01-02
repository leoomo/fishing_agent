"""
Brand model for equipment manufacturers
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship

from .base import Base


class Brand(Base):
    """Equipment brand/manufacturer model"""

    __tablename__ = 'brands'

    brand_id = Column('id', Integer, primary_key=True, autoincrement=True)  # Maps to 'id' in database
    name_cn = Column(String(100), nullable=False, unique=True, index=True, comment="Brand name in Chinese")
    name_en = Column(String(100), index=True, comment="Brand name in English")
    logo_url = Column(String(500), comment="Brand logo URL")
    website = Column(String(500), comment="Brand website URL")
    country = Column(String(50), comment="Country of origin")
    tier = Column(String(20), comment="Brand tier")
    description = Column(Text, comment="Brand description")
    is_active = Column(Boolean, default=True, comment="Brand active status")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Record creation timestamp")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Record update timestamp")

    # Relationships
    equipment = relationship("Equipment", back_populates="brand", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Brand(id={self.brand_id}, name_cn='{self.name_cn}', country='{self.country}')>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'brand_id': self.brand_id,
            'name_cn': self.name_cn,
            'name_en': self.name_en,
            'logo_url': self.logo_url,
            'website': self.website,
            'country': self.country,
            'tier': self.tier,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
