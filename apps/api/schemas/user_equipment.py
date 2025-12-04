"""
用户装备管理 API Schema

定义用户装备管理相关的请求和响应模型
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ========== 用户相关 Schema ==========


class UserCreate(BaseModel):
    """创建用户请求"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名（唯一）")
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    user_level: str = Field(
        default="新手",
        pattern="^(新手|进阶|高手)$",
        description="用户水平：新手/进阶/高手",
    )
    fishing_experience_years: Optional[int] = Field(
        None, ge=0, le=100, description="钓龄（年）"
    )
    preferred_fish: Optional[str] = Field(None, max_length=200, description="偏好鱼种")


class UserResponse(BaseModel):
    """用户信息响应"""

    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    nickname: Optional[str] = Field(None, description="昵称")
    email: Optional[str] = Field(None, description="邮箱")
    user_level: str = Field(..., description="用户水平")
    fishing_experience_years: Optional[int] = Field(None, description="钓龄")
    preferred_fish: Optional[str] = Field(None, description="偏好鱼种")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)


# ========== 装备相关 Schema ==========


class AddEquipmentRequest(BaseModel):
    """添加装备到用户库请求"""

    equipment_id: int = Field(..., gt=0, description="装备ID")
    purchase_price: Optional[float] = Field(None, ge=0, description="购买价格")
    purchase_date: Optional[str] = Field(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="购买日期（格式：YYYY-MM-DD）",
    )
    purchase_source: Optional[str] = Field(None, max_length=200, description="购买渠道")
    notes: Optional[str] = Field(None, max_length=500, description="备注")
    tags: Optional[List[str]] = Field(None, max_items=10, description="标签列表")


class UserEquipmentResponse(BaseModel):
    """用户装备响应"""

    id: int = Field(..., description="记录ID")
    user_id: int = Field(..., description="用户ID")
    equipment_id: int = Field(..., description="装备ID")
    equipment_name: str = Field(..., description="装备名称")
    category: str = Field(..., description="装备类别")
    brand_name: Optional[str] = Field(None, description="品牌名称")
    model: Optional[str] = Field(None, description="型号")
    purchase_date: Optional[str] = Field(None, description="购买日期")
    purchase_price: Optional[float] = Field(None, description="购买价格")
    purchase_source: Optional[str] = Field(None, description="购买渠道")
    condition: str = Field(..., description="装备状态")
    usage_frequency: Optional[str] = Field(None, description="使用频率")
    notes: Optional[str] = Field(None, description="备注")
    is_favorite: bool = Field(..., description="是否收藏")
    tags: Optional[str] = Field(None, description="标签（JSON字符串）")
    created_at: str = Field(..., description="添加时间")

    model_config = ConfigDict(from_attributes=True)


class UserEquipmentListResponse(BaseModel):
    """用户装备列表响应"""

    total: int = Field(..., description="装备总数")
    equipment_list: List[UserEquipmentResponse] = Field(..., description="装备列表")


# ========== 推荐相关 Schema ==========


class RecommendRequest(BaseModel):
    """基于用户装备推荐请求"""

    need_type: str = Field(
        ...,
        pattern="^(upgrade|complete|match)$",
        description="推荐类型：upgrade（升级）/complete（完善）/match（搭配）",
    )


class RecommendResponse(BaseModel):
    """推荐响应"""

    recommendation: str = Field(..., description="Markdown格式的推荐报告")
    need_type: str = Field(..., description="推荐类型")


# ========== 统计相关 Schema ==========


class CategoryStatistics(BaseModel):
    """类别统计"""

    category: str = Field(..., description="装备类别")
    count: int = Field(..., description="数量")
    avg_price: Optional[float] = Field(None, description="平均价格")
    total_price: Optional[float] = Field(None, description="总价格")


class UserStatisticsResponse(BaseModel):
    """用户装备统计响应"""

    user_id: int = Field(..., description="用户ID")
    total_count: int = Field(..., description="装备总数")
    total_spent: float = Field(..., description="总花费")
    favorite_count: int = Field(..., description="收藏数")
    by_category: List[CategoryStatistics] = Field(..., description="按类别统计")


# ========== 通用响应 Schema ==========


class SuccessResponse(BaseModel):
    """通用成功响应"""

    success: bool = Field(True, description="操作是否成功")
    message: str = Field(..., description="消息")
    data: Optional[Any] = Field(None, description="返回数据")


class ErrorResponse(BaseModel):
    """通用错误响应"""

    success: bool = Field(False, description="操作是否成功")
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细错误信息")
