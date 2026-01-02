"""
Rig configuration API schemas
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


class RigCategoryEnum(str, Enum):
    """Rig category classification"""
    BOTTOM = "bottom"       # 底钓钓组
    FLOAT = "float"         # 浮漂钓组
    LURE = "lure"           # 路亚钓组
    FLY = "fly"             # 飞蝇钓组
    SURF = "surf"           # 海钓钓组


class RigDifficultyEnum(str, Enum):
    """Rig difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# ========== Component Schemas ==========

class RigComponentBase(BaseModel):
    """Base rig component schema"""
    component_name: str = Field(..., min_length=1, max_length=100, description="组件名称")
    component_type: str = Field(..., max_length=50, description="组件类型")
    quantity: int = Field(default=1, ge=1, description="数量")
    size: Optional[str] = Field(None, max_length=50, description="尺寸规格")
    position: Optional[int] = Field(None, ge=0, description="组装位置")
    notes: Optional[str] = Field(None, max_length=500, description="组装说明")


class RigComponentCreate(RigComponentBase):
    """Create rig component"""
    pass


class RigComponentUpdate(BaseModel):
    """Update rig component"""
    component_name: Optional[str] = Field(None, min_length=1, max_length=100)
    component_type: Optional[str] = Field(None, max_length=50)
    quantity: Optional[int] = Field(None, ge=1)
    size: Optional[str] = Field(None, max_length=50)
    position: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=500)


class RigComponentResponse(RigComponentBase):
    """Rig component response"""
    component_id: int
    rig_id: int

    model_config = ConfigDict(from_attributes=True)


# ========== Spec Schemas ==========

class RigSpecBase(BaseModel):
    """Base rig specification schema"""
    spec_name: str = Field(..., min_length=1, max_length=100, description="规格名称")
    spec_value: str = Field(..., max_length=200, description="规格值")
    unit: Optional[str] = Field(None, max_length=20, description="单位")
    notes: Optional[str] = Field(None, max_length=500, description="备注")


class RigSpecCreate(RigSpecBase):
    """Create rig specification"""
    pass


class RigSpecUpdate(BaseModel):
    """Update rig specification"""
    spec_name: Optional[str] = Field(None, min_length=1, max_length=100)
    spec_value: Optional[str] = Field(None, max_length=200)
    unit: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=500)


class RigSpecResponse(RigSpecBase):
    """Rig specification response"""
    spec_id: int
    rig_id: int

    model_config = ConfigDict(from_attributes=True)


# ========== Rig Schemas ==========

class RigBase(BaseModel):
    """Base rig schema"""
    name: str = Field(..., min_length=1, max_length=100, description="钓组名称")
    category: str = Field(..., description="钓组分类")
    description: Optional[str] = Field(None, max_length=2000, description="详细描述")
    diagram_url: Optional[str] = Field(None, max_length=500, description="示意图URL")
    difficulty: str = Field(default="medium", description="难度等级")
    target_species: Optional[str] = Field(None, max_length=200, description="目标鱼种")
    best_conditions: Optional[str] = Field(None, max_length=1000, description="最佳钓鱼条件")


class RigCreate(RigBase):
    """Create rig - with optional nested specs and components"""
    specs: Optional[List[RigSpecCreate]] = Field(default=None, description="规格参数列表")
    components: Optional[List[RigComponentCreate]] = Field(default=None, description="组件配件列表")


class RigUpdate(BaseModel):
    """Update rig - All fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = None
    description: Optional[str] = Field(None, max_length=2000)
    diagram_url: Optional[str] = Field(None, max_length=500)
    difficulty: Optional[str] = None
    target_species: Optional[str] = Field(None, max_length=200)
    best_conditions: Optional[str] = Field(None, max_length=1000)


class RigResponse(RigBase):
    """Rig detail response with nested specs and components"""
    rig_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    specs: List[RigSpecResponse] = []
    components: List[RigComponentResponse] = []

    model_config = ConfigDict(from_attributes=True)


class RigListItem(BaseModel):
    """Rig list item - simplified without nested details"""
    rig_id: int
    name: str
    category: str
    difficulty: str
    target_species: Optional[str] = None
    diagram_url: Optional[str] = None
    component_count: int = 0
    spec_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RigListResponse(BaseModel):
    """Paginated rig list response"""
    total: int
    page: int
    page_size: int
    items: List[RigListItem]


# ========== Lure Type Association ==========

class LureTypeSimple(BaseModel):
    """Simplified lure type for associations"""
    lure_type_id: int
    name: str
    category: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RigLureAssociationRequest(BaseModel):
    """Request to associate lure types with a rig"""
    lure_type_ids: List[int] = Field(..., min_length=0, description="拟饵类型ID列表")


# ========== Option Response ==========

class OptionItem(BaseModel):
    """Generic option item"""
    value: str
    label: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class RigOptionsResponse(BaseModel):
    """Rig form options"""
    categories: List[OptionItem]
    difficulties: List[OptionItem]
    component_types: List[OptionItem]
