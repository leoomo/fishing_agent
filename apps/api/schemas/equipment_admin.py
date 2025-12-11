"""
装备管理 Schema
"""

from typing import Optional, List, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# ========== 规格 Schema（Union 类型）==========

class RodSpecsBase(BaseModel):
    """鱼竿规格"""
    length: float = Field(..., ge=0.5, le=10.0, description="长度（米）")
    power: str = Field(..., pattern="^(UL|L|ML|M|MH|H|XH)$", description="调性")
    action: str = Field(..., pattern="^(Fast|Medium|Slow)$", description="动作")
    lure_weight_min: float = Field(..., ge=0, description="适用饵重最小值（克）")
    lure_weight_max: float = Field(..., ge=0, description="适用饵重最大值（克）")
    sections: Optional[int] = Field(None, ge=1, le=10, description="节数")
    closed_length: Optional[float] = Field(None, description="收缩长度（厘米）")
    weight: Optional[float] = Field(None, description="自重（克）")


class ReelSpecsBase(BaseModel):
    """渔轮规格"""
    gear_ratio: Optional[str] = Field(None, description="速比（如 5.2:1）")
    bearings: Optional[int] = Field(None, ge=0, description="轴承数")
    max_drag: Optional[float] = Field(None, description="最大拽力（千克）")
    line_capacity: Optional[str] = Field(None, description="线容量（如 0.2mm/100m）")
    weight: Optional[float] = Field(None, description="自重（克）")
    spool_type: Optional[str] = Field(None, description="线杯类型")


class LineSpecsBase(BaseModel):
    """鱼线规格"""
    line_type: str = Field(..., pattern="^(PE|尼龙|碳线|钢丝)$", description="线型")
    diameter: Optional[float] = Field(None, description="线径（毫米）")
    breaking_strength: Optional[float] = Field(None, description="拉力值（千克）")
    length: Optional[float] = Field(None, description="长度（米）")
    material: Optional[str] = Field(None, description="材质")


class LureSpecsBase(BaseModel):
    """拟饵规格"""
    lure_type: str = Field(..., description="拟饵类型")
    weight: Optional[float] = Field(None, description="重量（克）")
    length: Optional[float] = Field(None, description="长度（厘米）")
    diving_depth: Optional[str] = Field(None, description="潜深（如 0.5-1.5米）")
    action_type: Optional[str] = Field(None, description="动作类型")


# Union 类型（根据 category 动态选择）
SpecsUnion = Union[RodSpecsBase, ReelSpecsBase, LineSpecsBase, LureSpecsBase]


# ========== 装备 Schema ==========

class EquipmentCreate(BaseModel):
    """创建装备请求"""
    # 基础信息
    name: str = Field(..., min_length=1, max_length=200, description="装备名称")
    category: str = Field(
        ...,
        pattern="^(鱼竿|渔轮|鱼线|拟饵|套装)$",
        description="装备类别"
    )
    brand_id: int = Field(..., gt=0, description="品牌ID")
    model: Optional[str] = Field(None, max_length=100, description="型号")

    # 价格
    price_min: Optional[float] = Field(None, ge=0, description="最低价格")
    price_max: Optional[float] = Field(None, ge=0, description="最高价格")
    price_currency: str = Field(default="CNY", description="货币单位")

    # 详情
    description: Optional[str] = Field(None, max_length=2000, description="描述")
    features: Optional[str] = Field(None, max_length=1000, description="特点")
    user_level: str = Field(
        default="新手",
        pattern="^(新手|进阶|高手)$",
        description="适用水平"
    )

    # 状态
    is_active: bool = Field(default=True, description="是否启用")
    source: str = Field(default="manual", description="数据来源")
    source_url: Optional[str] = Field(None, description="来源链接")

    # 规格（嵌套对象）
    specs: Optional[SpecsUnion] = Field(None, description="装备规格")


class EquipmentUpdate(BaseModel):
    """更新装备请求（所有字段可选）"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = Field(None, pattern="^(鱼竿|渔轮|鱼线|拟饵|套装)$")
    brand_id: Optional[int] = Field(None, gt=0)
    model: Optional[str] = Field(None, max_length=100)
    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=2000)
    features: Optional[str] = Field(None, max_length=1000)
    user_level: Optional[str] = Field(None, pattern="^(入门|新手|进阶|高手)$")
    is_active: Optional[bool] = None
    specs: Optional[SpecsUnion] = None


class EquipmentResponse(BaseModel):
    """装备响应"""
    equipment_id: int
    name: str
    category: str
    brand_id: int
    brand_name: Optional[str] = None  # 品牌中文名（JOIN查询）
    model: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    price_currency: str
    description: Optional[str] = None
    features: Optional[str] = None
    user_level: Optional[str] = Field(None, pattern="^(入门|新手|进阶|高手)$", description="适用水平")
    is_active: bool
    source: str
    source_url: Optional[str] = None
    created_at: str
    updated_at: str

    # 规格（嵌套对象）
    specs: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class EquipmentListResponse(BaseModel):
    """装备列表响应（分页）"""
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    items: List[EquipmentResponse] = Field(..., description="装备列表")


# ========== 品牌 Schema ==========

class BrandCreate(BaseModel):
    """创建品牌请求"""
    name_cn: str = Field(..., min_length=1, max_length=100, description="中文名")
    name_en: Optional[str] = Field(None, max_length=100, description="英文名")
    country: Optional[str] = Field(None, max_length=50, description="国家")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    logo_url: Optional[str] = Field(None, description="Logo URL")


class BrandUpdate(BaseModel):
    """更新品牌请求"""
    name_cn: Optional[str] = Field(None, min_length=1, max_length=100)
    name_en: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None)


class BrandResponse(BaseModel):
    """品牌响应"""
    brand_id: int
    name_cn: str
    name_en: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    created_at: str
    updated_at: str
    equipment_count: Optional[int] = None  # 可选的装备数量

    model_config = ConfigDict(from_attributes=True)
