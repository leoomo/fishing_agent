"""
装备批量添加 Schema

支持模板 + 变体模式，用于批量添加同系列装备
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


# ========== 枚举定义 ==========

class RodPower(str, Enum):
    """鱼竿调性"""
    UL = "UL"
    L = "L"
    ML = "ML"
    M = "M"
    MH = "MH"
    H = "H"
    XH = "XH"


class RodAction(str, Enum):
    """鱼竿动作"""
    Fast = "Fast"
    Medium = "Medium"
    Slow = "Slow"


class EquipmentCategory(str, Enum):
    """装备类别"""
    ROD = "鱼竿"
    REEL = "渔轮"
    LINE = "鱼线"
    LURE = "拟饵"


class UserLevel(str, Enum):
    """适用水平"""
    BEGINNER = "新手"
    INTERMEDIATE = "进阶"
    ADVANCED = "高手"


# ========== 模板 Schema ==========

class BatchRodTemplate(BaseModel):
    """鱼竿批量添加模板（共享字段）"""

    # 必填共享字段
    brand_id: int = Field(..., gt=0, description="品牌ID")
    product_line: str = Field(..., min_length=1, max_length=100, description="产品线名称")

    # 可选共享字段
    sections: Optional[int] = Field(None, ge=1, le=10, description="节数")
    guide_type: Optional[str] = Field(None, max_length=100, description="导环类型")
    handle_type: Optional[str] = Field(None, max_length=100, description="握把类型")
    material: Optional[str] = Field(None, max_length=100, description="材质")

    # 默认价格范围（可被变体覆盖）
    price_min: Optional[float] = Field(None, ge=0, description="默认最低价格")
    price_max: Optional[float] = Field(None, ge=0, description="默认最高价格")

    # 其他共享字段
    user_level: UserLevel = Field(default=UserLevel.INTERMEDIATE, description="适用水平")
    description: Optional[str] = Field(None, max_length=2000, description="描述")
    features: Optional[str] = Field(None, max_length=1000, description="特点")

    @field_validator('price_max')
    @classmethod
    def validate_price_range(cls, v, info):
        if v is not None and info.data.get('price_min') is not None:
            if v < info.data['price_min']:
                raise ValueError('price_max 必须大于等于 price_min')
        return v


class BatchReelTemplate(BaseModel):
    """渔轮批量添加模板（共享字段）"""

    brand_id: int = Field(..., gt=0, description="品牌ID")
    product_line: str = Field(..., min_length=1, max_length=100, description="产品线名称")

    # 渔轮共享字段
    reel_type: Optional[str] = Field(None, description="类型（纺车/水滴/鼓轮）")
    spool_type: Optional[str] = Field(None, description="线杯类型")
    material: Optional[str] = Field(None, max_length=100, description="材质")

    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)
    user_level: UserLevel = Field(default=UserLevel.INTERMEDIATE)
    description: Optional[str] = Field(None, max_length=2000)
    features: Optional[str] = Field(None, max_length=1000)


class BatchLineTemplate(BaseModel):
    """鱼线批量添加模板（共享字段）"""

    brand_id: int = Field(..., gt=0, description="品牌ID")
    product_line: str = Field(..., min_length=1, max_length=100, description="产品线名称")

    # 鱼线共享字段
    line_type: str = Field(..., description="线型（PE/尼龙/碳线/钢丝）")
    material: Optional[str] = Field(None, max_length=100, description="材质")

    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)
    user_level: UserLevel = Field(default=UserLevel.INTERMEDIATE)
    description: Optional[str] = Field(None, max_length=2000)
    features: Optional[str] = Field(None, max_length=1000)


class BatchLureTemplate(BaseModel):
    """拟饵批量添加模板（共享字段）"""

    brand_id: int = Field(..., gt=0, description="品牌ID")
    product_line: str = Field(..., min_length=1, max_length=100, description="产品线名称")

    # 拟饵共享字段
    lure_type: str = Field(..., description="拟饵类型")
    action_type: Optional[str] = Field(None, description="动作类型")

    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)
    user_level: UserLevel = Field(default=UserLevel.INTERMEDIATE)
    description: Optional[str] = Field(None, max_length=2000)
    features: Optional[str] = Field(None, max_length=1000)


# ========== 变体 Schema ==========

class RodVariantSpec(BaseModel):
    """鱼竿变体规格（每个型号不同的字段）"""

    # 必填字段
    model: str = Field(..., min_length=1, max_length=100, description="型号（如 264MH）")
    length: float = Field(..., ge=0.5, le=10.0, description="长度（米）")
    power: RodPower = Field(..., description="调性")

    # 可选字段
    action: Optional[RodAction] = Field(None, description="动作")
    weight: Optional[float] = Field(None, ge=0, description="自重（克）")
    lure_weight_min: Optional[float] = Field(None, ge=0, description="适用饵重最小值（克）")
    lure_weight_max: Optional[float] = Field(None, ge=0, description="适用饵重最大值（克）")
    line_weight_min: Optional[float] = Field(None, ge=0, description="适用线重最小值（磅）")
    line_weight_max: Optional[float] = Field(None, ge=0, description="适用线重最大值（磅）")
    closed_length: Optional[float] = Field(None, ge=0, description="收缩长度（厘米）")

    # 覆盖模板价格（可选）
    price_min: Optional[float] = Field(None, ge=0, description="覆盖最低价格")
    price_max: Optional[float] = Field(None, ge=0, description="覆盖最高价格")

    @model_validator(mode='after')
    def validate_weight_ranges(self):
        if self.lure_weight_min is not None and self.lure_weight_max is not None:
            if self.lure_weight_max < self.lure_weight_min:
                raise ValueError('lure_weight_max 必须大于等于 lure_weight_min')
        if self.line_weight_min is not None and self.line_weight_max is not None:
            if self.line_weight_max < self.line_weight_min:
                raise ValueError('line_weight_max 必须大于等于 line_weight_min')
        return self


class ReelVariantSpec(BaseModel):
    """渔轮变体规格"""

    model: str = Field(..., min_length=1, max_length=100, description="型号")
    size: Optional[str] = Field(None, description="规格（如 2500, 3000）")
    gear_ratio: Optional[str] = Field(None, description="速比（如 5.2:1）")
    bearings: Optional[int] = Field(None, ge=0, description="轴承数")
    max_drag: Optional[float] = Field(None, ge=0, description="最大拽力（千克）")
    line_capacity: Optional[str] = Field(None, description="线容量")
    weight: Optional[float] = Field(None, ge=0, description="自重（克）")

    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)


class LineVariantSpec(BaseModel):
    """鱼线变体规格"""

    model: str = Field(..., min_length=1, max_length=100, description="型号")
    diameter: Optional[float] = Field(None, ge=0, description="线径（毫米）")
    breaking_strength: Optional[float] = Field(None, ge=0, description="拉力值（千克）")
    length: Optional[float] = Field(None, ge=0, description="长度（米）")
    pe_number: Optional[str] = Field(None, description="PE号数（如 0.8, 1.0）")

    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)


class LureVariantSpec(BaseModel):
    """拟饵变体规格"""

    model: str = Field(..., min_length=1, max_length=100, description="型号/色号")
    weight: Optional[float] = Field(None, ge=0, description="重量（克）")
    length: Optional[float] = Field(None, ge=0, description="长度（厘米）")
    diving_depth: Optional[str] = Field(None, description="潜深范围")
    color: Optional[str] = Field(None, description="颜色")

    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)


# ========== 请求/响应 Schema ==========

class BatchEquipmentCreateRequest(BaseModel):
    """批量创建装备请求"""

    category: EquipmentCategory = Field(..., description="装备类别")
    template: dict = Field(..., description="共享模板字段")
    variants: List[dict] = Field(..., min_length=1, max_length=100, description="变体列表")
    skip_duplicates: bool = Field(default=True, description="跳过重复项（同品牌同型号）")

    @field_validator('variants')
    @classmethod
    def validate_variants(cls, v):
        if len(v) == 0:
            raise ValueError('至少需要一个变体')
        if len(v) > 100:
            raise ValueError('单次最多添加100个变体')
        return v


class BatchRodCreateRequest(BaseModel):
    """批量创建鱼竿请求（强类型版本）"""

    template: BatchRodTemplate
    variants: List[RodVariantSpec] = Field(..., min_length=1, max_length=100)
    skip_duplicates: bool = Field(default=True)


class BatchReelCreateRequest(BaseModel):
    """批量创建渔轮请求"""

    template: BatchReelTemplate
    variants: List[ReelVariantSpec] = Field(..., min_length=1, max_length=100)
    skip_duplicates: bool = Field(default=True)


class BatchLineCreateRequest(BaseModel):
    """批量创建鱼线请求"""

    template: BatchLineTemplate
    variants: List[LineVariantSpec] = Field(..., min_length=1, max_length=100)
    skip_duplicates: bool = Field(default=True)


class BatchLureCreateRequest(BaseModel):
    """批量创建拟饵请求"""

    template: BatchLureTemplate
    variants: List[LureVariantSpec] = Field(..., min_length=1, max_length=100)
    skip_duplicates: bool = Field(default=True)


class BatchEquipmentCreateResponse(BaseModel):
    """批量创建装备响应"""

    success_count: int = Field(..., description="成功创建数量")
    skip_count: int = Field(..., description="跳过数量（重复）")
    error_count: int = Field(..., description="失败数量")
    created_ids: List[int] = Field(default_factory=list, description="创建的装备ID列表")
    skipped_models: List[str] = Field(default_factory=list, description="跳过的型号列表")
    errors: List[dict] = Field(default_factory=list, description="错误详情")


# ========== 文本解析 Schema ==========

class TextParseRequest(BaseModel):
    """文本解析请求"""

    text: str = Field(..., min_length=10, max_length=50000, description="规格表文本")
    category: EquipmentCategory = Field(..., description="装备类别")
    delimiter: Optional[str] = Field(None, description="分隔符（自动检测）")


class TextParseResponse(BaseModel):
    """文本解析响应"""

    success: bool = Field(..., description="是否解析成功")
    template: dict = Field(default_factory=dict, description="识别的模板字段")
    variants: List[dict] = Field(default_factory=list, description="识别的变体列表")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    raw_headers: List[str] = Field(default_factory=list, description="原始表头")
    row_count: int = Field(default=0, description="识别的行数")
