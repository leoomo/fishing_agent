"""
Equipment models including Equipment and various Spec models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, Enum as SQLEnum, DateTime, Index
from sqlalchemy.orm import relationship
import enum

from .base import Base, TimestampMixin


class EquipmentCategory(str, enum.Enum):
    """Equipment category enumeration"""
    ROD = "鱼竿"
    REEL = "渔轮"
    LINE = "鱼线"
    LURE = "拟饵"
    KIT = "套装"


class UserLevel(str, enum.Enum):
    """User skill level enumeration"""
    BEGINNER = "新手"
    INTERMEDIATE = "进阶"
    ADVANCED = "高手"


class Equipment(Base):
    """Main equipment model"""

    __tablename__ = 'equipment'

    # 复合索引用于常见查询优化
    __table_args__ = (
        # 按类别和激活状态筛选（最常见查询）
        Index('ix_equipment_category_active', 'category', 'is_active'),
        # 按品牌和激活状态筛选
        Index('ix_equipment_brand_active', 'brand_id', 'is_active'),
        # 按价格范围搜索优化
        Index('ix_equipment_price_range', 'price_min', 'price_max'),
        # 按类别和用户级别筛选
        Index('ix_equipment_category_level', 'category', 'user_level'),
    )

    equipment_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True, comment="Equipment name")
    category = Column(String(20), nullable=False, index=True, comment="Equipment category")
    brand_id = Column(Integer, ForeignKey('brands.id', ondelete='CASCADE'), index=True)
    model = Column(String(100), index=True, comment="Model number")
    price_min = Column(Float, comment="Minimum price (CNY)")
    price_max = Column(Float, comment="Maximum price (CNY)")
    description = Column(Text, comment="Equipment description")
    features = Column(Text, comment="Key features (newline separated)")
    target_fish = Column(Text, comment="Target fish species")
    user_level = Column(String(20), index=True, comment="Recommended user skill level")
    is_active = Column(Integer, default=1, nullable=False, index=True, comment="Whether equipment is active")
    is_vectorized = Column(Integer, default=0, comment="Whether equipment has been vectorized")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    source = Column(String(50), default='manual', index=True, comment="Data source")
    source_url = Column(String(500), comment="Source URL")
    crawled_at = Column(DateTime, comment="Crawl timestamp")
    last_synced_at = Column(DateTime, comment="Last sync timestamp")

    # Relationships
    brand = relationship("Brand", back_populates="equipment")
    rod_spec = relationship("RodSpec", back_populates="equipment", uselist=False, cascade="all, delete-orphan")
    reel_spec = relationship("ReelSpec", back_populates="equipment", uselist=False, cascade="all, delete-orphan")
    line_spec = relationship("LineSpec", back_populates="equipment", uselist=False, cascade="all, delete-orphan")
    lure_spec = relationship("LureSpec", back_populates="equipment", uselist=False, cascade="all, delete-orphan")
    user_equipment = relationship("UserEquipment", back_populates="equipment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Equipment(id={self.equipment_id}, name='{self.name}', category='{self.category}')>"

    def to_dict(self, include_brand=True, include_specs=True):
        """Convert to dictionary representation"""
        result = {
            'equipment_id': self.equipment_id,
            'name': self.name,
            'category': self.category,
            'brand_id': self.brand_id,
            'model': self.model,
            'price_min': self.price_min,
            'price_max': self.price_max,
            'description': self.description,
            'features': self.features,
            'target_fish': self.target_fish,
            'user_level': self.user_level,
            'is_active': bool(self.is_active),
            'is_vectorized': bool(self.is_vectorized),
            'source': self.source,
            'source_url': self.source_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'crawled_at': self.crawled_at.isoformat() if self.crawled_at else None,
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None,
        }

        if include_brand and self.brand:
            result['brand'] = self.brand.to_dict()

        if include_specs:
            if self.rod_spec:
                result['specs'] = self.rod_spec.to_dict()
            elif self.reel_spec:
                result['specs'] = self.reel_spec.to_dict()
            elif self.line_spec:
                result['specs'] = self.line_spec.to_dict()
            elif self.lure_spec:
                result['specs'] = self.lure_spec.to_dict()

        return result


class RodSpec(Base):
    """Fishing rod specifications"""

    __tablename__ = 'rod_specs'

    spec_id = Column('id', Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(Integer, ForeignKey('equipment.equipment_id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    # Rod specifications
    length = Column(Float, comment="Rod length in meters")
    power = Column(String(20), index=True, comment="Rod power (UL/L/ML/M/MH/H/XH)")
    action = Column(String(20), comment="Rod action (Fast/Moderate/Slow)")
    sections = Column(Integer, comment="Number of rod sections")
    weight = Column(Float, comment="Rod weight in grams")
    lure_weight_min = Column(Float, comment="Minimum lure weight in grams")
    lure_weight_max = Column(Float, comment="Maximum lure weight in grams")
    line_weight_min = Column(Float, comment="Minimum line weight (lb)")
    line_weight_max = Column(Float, comment="Maximum line weight (lb)")
    guide_type = Column(String(50), comment="Guide type")
    handle_type = Column(String(50), comment="Handle type")
    tip_diameter = Column(Float, comment="Tip diameter in mm")
    butt_diameter = Column(Float, comment="Butt diameter in mm")
    handle_length = Column(Float, comment="Handle length in cm")
    craft_description = Column(Text, comment="Craft and build description")

    # Relationships
    equipment = relationship("Equipment", back_populates="rod_spec")

    def __repr__(self):
        return f"<RodSpec(equipment_id={self.equipment_id}, length={self.length}m, power='{self.power}')>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'spec_id': self.spec_id,
            'equipment_id': self.equipment_id,
            'length': self.length,
            'sections': self.sections,
            'closed_length': self.closed_length,
            'weight': self.weight,
            'power': self.power,
            'action': self.action,
            'lure_weight_min': self.lure_weight_min,
            'lure_weight_max': self.lure_weight_max,
            'line_weight_min': self.line_weight_min,
            'line_weight_max': self.line_weight_max,
            'material': self.material,
            'handle_length': self.handle_length,
            'grip_material': self.grip_material,
        }


class ReelSpec(Base):
    """Fishing reel specifications"""

    __tablename__ = 'reel_specs'

    spec_id = Column('id', Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(Integer, ForeignKey('equipment.equipment_id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    # Reel specifications
    reel_type = Column(String(20), index=True, comment="Reel type (spinning/baitcasting/fly)")
    gear_ratio = Column(String(20), comment="Gear ratio (e.g., 5.2:1)")
    bearings = Column(String(20), comment="Number of ball bearings")
    weight = Column(Float, comment="Reel weight in grams")
    line_capacity = Column(String(100), comment="Line capacity (e.g., 0.2mm/200m)")
    max_drag = Column(Float, comment="Maximum drag in kg")
    retrieve_per_turn = Column(Float, comment="Retrieve per turn in cm")

    # Relationships
    equipment = relationship("Equipment", back_populates="reel_spec")

    def __repr__(self):
        return f"<ReelSpec(equipment_id={self.equipment_id}, type='{self.reel_type}', ratio='{self.gear_ratio}')>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'spec_id': self.spec_id,
            'equipment_id': self.equipment_id,
            'reel_type': self.reel_type,
            'gear_ratio': self.gear_ratio,
            'bearings': self.bearings,
            'weight': self.weight,
            'line_capacity': self.line_capacity,
            'max_drag': self.max_drag,
            'retrieve_per_turn': self.retrieve_per_turn,
        }


class LineSpec(Base):
    """Fishing line specifications"""

    __tablename__ = 'line_specs'

    spec_id = Column('id', Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(Integer, ForeignKey('equipment.equipment_id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    # Line specifications
    line_type = Column(String(20), index=True, comment="Line type (monofilament/braided/fluorocarbon)")
    diameter = Column(Float, comment="Line diameter in mm")
    strength_lb = Column(Float, comment="Breaking strength in lb")
    length_m = Column(Float, comment="Line length in meters")
    color = Column(String(50), comment="Line color")
    material = Column(String(50), comment="Line material")

    # Relationships
    equipment = relationship("Equipment", back_populates="line_spec")

    def __repr__(self):
        return f"<LineSpec(equipment_id={self.equipment_id}, type='{self.line_type}', strength={self.strength_lb}lb)>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'spec_id': self.spec_id,
            'equipment_id': self.equipment_id,
            'line_type': self.line_type,
            'diameter': self.diameter,
            'strength_lb': self.strength_lb,
            'length_m': self.length_m,
            'color': self.color,
            'material': self.material,
        }


class LureSpec(Base):
    """Fishing lure specifications"""

    __tablename__ = 'lure_specs'

    spec_id = Column('id', Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(Integer, ForeignKey('equipment.equipment_id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    # Lure specifications
    lure_type = Column(String(50), index=True, comment="Lure type (crankbait/jerkbait/topwater/soft plastic/etc)")
    lure_category = Column(String(50), comment="Lure category")
    length = Column(Float, comment="Lure length in cm")
    weight = Column(Float, comment="Lure weight in grams")
    diving_depth_min = Column(Float, comment="Minimum diving depth in meters")
    diving_depth_max = Column(Float, comment="Maximum diving depth in meters")
    color = Column(String(100), comment="Color/pattern")
    action_type = Column(String(50), comment="Action type (fast/slow/suspending)")

    # Relationships
    equipment = relationship("Equipment", back_populates="lure_spec")

    def __repr__(self):
        return f"<LureSpec(equipment_id={self.equipment_id}, type='{self.lure_type}', weight={self.weight}g)>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'spec_id': self.spec_id,
            'equipment_id': self.equipment_id,
            'lure_type': self.lure_type,
            'lure_category': self.lure_category,
            'length': self.length,
            'weight': self.weight,
            'diving_depth_min': self.diving_depth_min,
            'diving_depth_max': self.diving_depth_max,
            'color': self.color,
            'action_type': self.action_type,
        }
