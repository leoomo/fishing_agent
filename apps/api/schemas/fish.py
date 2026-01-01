"""
鱼百科 Schema 定义

定义鱼种、知识库、季节活动相关的请求/响应模型
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class FishCategoryEnum(str, Enum):
    """鱼类分类枚举"""

    FRESHWATER = "freshwater"  # 淡水鱼
    SALTWATER = "saltwater"  # 海水鱼
    BRACKISH = "brackish"  # 广盐鱼


class SeasonEnum(str, Enum):
    """季节枚举"""

    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"


class ActivityLevelEnum(str, Enum):
    """活跃度枚举"""

    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"


# ========== FishKnowledge Schemas ==========


class FishKnowledgeBase(BaseModel):
    """知识库基础字段"""

    topic: str = Field(..., min_length=1, max_length=100, description="知识主题")
    content: str = Field(..., min_length=1, description="知识内容")
    source: Optional[str] = Field(None, max_length=200, description="信息来源")
    tags: Optional[str] = Field(None, max_length=200, description="标签(逗号分隔)")


class FishKnowledgeCreate(FishKnowledgeBase):
    """创建知识条目请求"""

    pass


class FishKnowledgeUpdate(BaseModel):
    """更新知识条目请求"""

    topic: Optional[str] = Field(None, min_length=1, max_length=100, description="知识主题")
    content: Optional[str] = Field(None, min_length=1, description="知识内容")
    source: Optional[str] = Field(None, max_length=200, description="信息来源")
    tags: Optional[str] = Field(None, max_length=200, description="标签(逗号分隔)")


class FishKnowledgeResponse(FishKnowledgeBase):
    """知识条目响应"""

    id: int
    species_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ========== FishSeasonActivity Schemas ==========


class FishSeasonActivityBase(BaseModel):
    """季节活动基础字段"""

    season: SeasonEnum = Field(..., description="季节")
    activity_level: ActivityLevelEnum = Field(..., description="活跃度")
    best_time: Optional[str] = Field(None, max_length=100, description="最佳钓鱼时间")
    recommended_lures: Optional[str] = Field(None, description="推荐拟饵(逗号分隔)")
    fishing_tips: Optional[str] = Field(None, description="钓鱼技巧")


class FishSeasonActivityCreate(FishSeasonActivityBase):
    """创建季节活动请求"""

    pass


class FishSeasonActivityUpdate(BaseModel):
    """更新季节活动请求"""

    season: Optional[SeasonEnum] = Field(None, description="季节")
    activity_level: Optional[ActivityLevelEnum] = Field(None, description="活跃度")
    best_time: Optional[str] = Field(None, max_length=100, description="最佳钓鱼时间")
    recommended_lures: Optional[str] = Field(None, description="推荐拟饵(逗号分隔)")
    fishing_tips: Optional[str] = Field(None, description="钓鱼技巧")


class FishSeasonActivityResponse(BaseModel):
    """季节活动响应"""

    id: int
    species_id: int
    season: str
    activity_level: str
    best_time: Optional[str] = None
    recommended_lures: Optional[str] = None
    fishing_tips: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ========== FishSpecies Schemas ==========


class FishSpeciesBase(BaseModel):
    """鱼种基础字段"""

    name_cn: str = Field(..., min_length=1, max_length=100, description="中文名")
    name_en: Optional[str] = Field(None, max_length=100, description="英文名")
    scientific_name: Optional[str] = Field(None, max_length=100, description="学名")
    category: FishCategoryEnum = Field(..., description="鱼类分类")
    habitat: Optional[str] = Field(None, max_length=200, description="栖息环境")
    description: Optional[str] = Field(None, description="物种描述")
    image_url: Optional[str] = Field(None, max_length=500, description="图片URL")
    min_weight: Optional[float] = Field(None, ge=0, description="最小体重(kg)")
    max_weight: Optional[float] = Field(None, ge=0, description="最大体重(kg)")
    min_length: Optional[float] = Field(None, ge=0, description="最小体长(cm)")
    max_length: Optional[float] = Field(None, ge=0, description="最大体长(cm)")


class FishSpeciesCreate(FishSpeciesBase):
    """创建鱼种请求"""

    pass


class FishSpeciesUpdate(BaseModel):
    """更新鱼种请求"""

    name_cn: Optional[str] = Field(None, min_length=1, max_length=100, description="中文名")
    name_en: Optional[str] = Field(None, max_length=100, description="英文名")
    scientific_name: Optional[str] = Field(None, max_length=100, description="学名")
    category: Optional[FishCategoryEnum] = Field(None, description="鱼类分类")
    habitat: Optional[str] = Field(None, max_length=200, description="栖息环境")
    description: Optional[str] = Field(None, description="物种描述")
    image_url: Optional[str] = Field(None, max_length=500, description="图片URL")
    min_weight: Optional[float] = Field(None, ge=0, description="最小体重(kg)")
    max_weight: Optional[float] = Field(None, ge=0, description="最大体重(kg)")
    min_length: Optional[float] = Field(None, ge=0, description="最小体长(cm)")
    max_length: Optional[float] = Field(None, ge=0, description="最大体长(cm)")


class FishSpeciesResponse(FishSpeciesBase):
    """鱼种详情响应(含关联数据)"""

    species_id: int
    category: str  # Override to return string instead of enum
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    knowledge: List[FishKnowledgeResponse] = []
    season_activity: List[FishSeasonActivityResponse] = []

    model_config = ConfigDict(from_attributes=True)


class FishSpeciesListItem(BaseModel):
    """鱼种列表项"""

    species_id: int
    name_cn: str
    name_en: Optional[str] = None
    category: str
    habitat: Optional[str] = None
    knowledge_count: int = 0
    season_count: int = 0
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class FishSpeciesListResponse(BaseModel):
    """鱼种分页列表响应"""

    items: List[FishSpeciesListItem]
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


# ========== Equipment Recommendation (Read-only) ==========


class EquipmentRecommendation(BaseModel):
    """装备推荐(只读)"""

    recommended_lures: Optional[List[str]] = Field(None, description="推荐拟饵")
    recommended_rigs: Optional[List[str]] = Field(None, description="推荐钓组")
    recommended_rod_power: Optional[List[str]] = Field(None, description="推荐竿力")
    recommended_line_lb_min: Optional[int] = Field(None, description="推荐鱼线最小拉力")
    recommended_line_lb_max: Optional[int] = Field(None, description="推荐鱼线最大拉力")
    lure_difficulty: Optional[str] = Field(None, description="路亚难度")
    fight_intensity: Optional[str] = Field(None, description="搏斗强度")


# ========== Init Data Response ==========


class InitDataResponse(BaseModel):
    """初始化数据响应"""

    created_count: int
    message: str
