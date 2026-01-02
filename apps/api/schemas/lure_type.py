"""
拟饵类型 Schema 定义

定义拟饵类型相关的请求/响应模型
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class LureCategoryEnum(str, Enum):
    """拟饵分类枚举"""

    HARD = "hard"  # 硬饵
    SOFT = "soft"  # 软饵
    METAL = "metal"  # 金属饵
    FLY = "fly"  # 飞蝇
    OTHER = "other"  # 其他


# ========== Create/Update Schemas ==========


class LureTypeCreate(BaseModel):
    """创建拟饵类型请求"""

    name: str = Field(..., min_length=1, max_length=100, description="拟饵名称")
    category: LureCategoryEnum = Field(..., description="拟饵分类")
    description: Optional[str] = Field(None, description="详细描述")
    action_description: Optional[str] = Field(None, description="动作描述")
    best_conditions: Optional[str] = Field(None, description="最佳使用条件")
    target_species: Optional[str] = Field(None, max_length=200, description="目标鱼种")
    typical_weight_min: Optional[float] = Field(
        None, ge=0, description="典型最小重量(克)"
    )
    typical_weight_max: Optional[float] = Field(
        None, ge=0, description="典型最大重量(克)"
    )
    image_url: Optional[str] = Field(None, max_length=500, description="图片URL")


class LureTypeUpdate(BaseModel):
    """更新拟饵类型请求"""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="拟饵名称")
    category: Optional[LureCategoryEnum] = Field(None, description="拟饵分类")
    description: Optional[str] = Field(None, description="详细描述")
    action_description: Optional[str] = Field(None, description="动作描述")
    best_conditions: Optional[str] = Field(None, description="最佳使用条件")
    target_species: Optional[str] = Field(None, max_length=200, description="目标鱼种")
    typical_weight_min: Optional[float] = Field(
        None, ge=0, description="典型最小重量(克)"
    )
    typical_weight_max: Optional[float] = Field(
        None, ge=0, description="典型最大重量(克)"
    )
    image_url: Optional[str] = Field(None, max_length=500, description="图片URL")


# ========== Response Schemas ==========


class LureTypeResponse(BaseModel):
    """拟饵类型详情响应"""

    lure_type_id: int
    name: str
    category: str
    description: Optional[str] = None
    action_description: Optional[str] = None
    best_conditions: Optional[str] = None
    target_species: Optional[str] = None
    typical_weight_min: Optional[float] = None
    typical_weight_max: Optional[float] = None
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LureTypeListItem(BaseModel):
    """拟饵类型列表项"""

    lure_type_id: int
    name: str
    category: str
    target_species: Optional[str] = None
    typical_weight_min: Optional[float] = None
    typical_weight_max: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class LureTypeListResponse(BaseModel):
    """拟饵类型分页列表响应"""

    items: List[LureTypeListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ========== Category Stats ==========


class CategoryStats(BaseModel):
    """分类统计"""

    category: str
    count: int
    label: str
    icon: str
    color: str


class CategoryStatsResponse(BaseModel):
    """分类统计响应"""

    categories: List[CategoryStats]
    total: int


# ========== Init Data Response ==========


class InitDataResponse(BaseModel):
    """初始化数据响应"""

    created_count: int
    message: str
