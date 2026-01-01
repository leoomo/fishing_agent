"""
钓鱼配件 Schema 定义

定义钓鱼配件相关的请求/响应模型
包括钩子、铅坠、转环、前导线、浮漂、别针等
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AccessoryCategoryEnum(str, Enum):
    """配件分类枚举"""

    HOOK = "hook"  # 钩子
    SINKER = "sinker"  # 铅坠
    SWIVEL = "swivel"  # 转环/八字环
    LEADER = "leader"  # 前导线
    FLOAT = "float"  # 浮漂
    SNAP = "snap"  # 别针/快速连接器
    OTHER = "other"  # 其他


class UserLevelEnum(str, Enum):
    """用户等级枚举"""

    BEGINNER = "beginner"  # 新手
    INTERMEDIATE = "intermediate"  # 进阶
    ADVANCED = "advanced"  # 高级


# ========== Create/Update Schemas ==========


class AccessoryCreate(BaseModel):
    """创建配件请求"""

    name: str = Field(..., min_length=1, max_length=100, description="配件名称")
    category: AccessoryCategoryEnum = Field(..., description="配件分类")
    description: Optional[str] = Field(None, description="详细描述")
    features: Optional[str] = Field(None, description="主要特点")

    # 规格参数
    size: Optional[str] = Field(None, max_length=50, description="规格尺寸 (如 #4, 3/0, 1.5g)")
    weight: Optional[float] = Field(None, ge=0, description="重量(克)")
    material: Optional[str] = Field(None, max_length=100, description="材质")
    color: Optional[str] = Field(None, max_length=100, description="颜色/花纹")
    quantity_per_pack: Optional[int] = Field(None, ge=1, description="每包数量")

    # 应用场景
    target_species: Optional[str] = Field(None, max_length=200, description="目标鱼种")
    applicable_rigs: Optional[str] = Field(
        None, max_length=200, description="适用钓组 (如 Texas, Carolina, drop shot)"
    )
    best_conditions: Optional[str] = Field(None, description="最佳使用条件")

    # 商业信息
    brand: Optional[str] = Field(None, max_length=100, description="品牌")
    price_min: Optional[float] = Field(None, ge=0, description="最低价格(元)")
    price_max: Optional[float] = Field(None, ge=0, description="最高价格(元)")
    user_level: Optional[UserLevelEnum] = Field(
        UserLevelEnum.BEGINNER, description="推荐用户等级"
    )

    # 媒体
    image_url: Optional[str] = Field(None, max_length=500, description="图片URL")


class AccessoryUpdate(BaseModel):
    """更新配件请求"""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="配件名称")
    category: Optional[AccessoryCategoryEnum] = Field(None, description="配件分类")
    description: Optional[str] = Field(None, description="详细描述")
    features: Optional[str] = Field(None, description="主要特点")

    # 规格参数
    size: Optional[str] = Field(None, max_length=50, description="规格尺寸")
    weight: Optional[float] = Field(None, ge=0, description="重量(克)")
    material: Optional[str] = Field(None, max_length=100, description="材质")
    color: Optional[str] = Field(None, max_length=100, description="颜色/花纹")
    quantity_per_pack: Optional[int] = Field(None, ge=1, description="每包数量")

    # 应用场景
    target_species: Optional[str] = Field(None, max_length=200, description="目标鱼种")
    applicable_rigs: Optional[str] = Field(None, max_length=200, description="适用钓组")
    best_conditions: Optional[str] = Field(None, description="最佳使用条件")

    # 商业信息
    brand: Optional[str] = Field(None, max_length=100, description="品牌")
    price_min: Optional[float] = Field(None, ge=0, description="最低价格(元)")
    price_max: Optional[float] = Field(None, ge=0, description="最高价格(元)")
    user_level: Optional[UserLevelEnum] = Field(None, description="推荐用户等级")

    # 媒体
    image_url: Optional[str] = Field(None, max_length=500, description="图片URL")


# ========== Response Schemas ==========


class AccessoryResponse(BaseModel):
    """配件详情响应"""

    accessory_id: int
    name: str
    category: str
    description: Optional[str] = None
    features: Optional[str] = None

    # 规格参数
    size: Optional[str] = None
    weight: Optional[float] = None
    material: Optional[str] = None
    color: Optional[str] = None
    quantity_per_pack: Optional[int] = None

    # 应用场景
    target_species: Optional[str] = None
    applicable_rigs: Optional[str] = None
    best_conditions: Optional[str] = None

    # 商业信息
    brand: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    user_level: Optional[str] = None

    # 媒体
    image_url: Optional[str] = None

    # 时间戳
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AccessoryListItem(BaseModel):
    """配件列表项"""

    accessory_id: int
    name: str
    category: str
    size: Optional[str] = None
    material: Optional[str] = None
    brand: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    user_level: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AccessoryListResponse(BaseModel):
    """配件分页列表响应"""

    items: List[AccessoryListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ========== Category Stats ==========


class AccessoryCategoryStats(BaseModel):
    """分类统计"""

    category: str
    count: int
    label: str
    icon: str
    color: str


class AccessoryCategoryStatsResponse(BaseModel):
    """分类统计响应"""

    categories: List[AccessoryCategoryStats]
    total: int


# ========== Init Data Response ==========


class AccessoryInitDataResponse(BaseModel):
    """初始化数据响应"""

    created_count: int
    message: str


# ========== Options Response ==========


class AccessoryOptionsResponse(BaseModel):
    """配件表单选项响应"""

    categories: List[dict]  # category options with label, value, icon, color
    user_levels: List[dict]  # user level options
    materials: List[str]  # common materials
