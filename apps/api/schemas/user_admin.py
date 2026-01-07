"""
用户管理 Schema
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# ========== 用户水平常量 ==========
USER_LEVELS = ["新手", "进阶", "高手"]

# ========== 钓法常量 ==========
FISHING_METHODS = ["路亚", "台钓", "矶钓", "筏钓", "海钓", "飞蝇"]


# ========== 用户请求 Schema ==========

class UserUpdateRequest(BaseModel):
    """用户更新请求"""
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机")
    user_level: Optional[str] = Field(None, description="用户水平")
    fishing_experience_years: Optional[int] = Field(None, ge=0, le=100, description="钓龄（年）")
    preferred_fish: Optional[str] = Field(None, description="喜欢鱼种")
    preferred_scenarios: Optional[str] = Field(None, description="偏好钓法")
    nickname: Optional[str] = Field(None, description="昵称")


class BatchUpdateRequest(BaseModel):
    """批量更新请求"""
    user_ids: List[int] = Field(..., min_length=1, description="用户ID列表")
    user_level: Optional[str] = Field(None, description="批量修改用户水平")


# ========== 用户响应 Schema ==========

class UserResponse(BaseModel):
    """用户响应"""
    user_id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    user_level: str
    fishing_experience_years: Optional[int] = None
    favorite_fish_species: Optional[str] = None
    preferred_fishing_method: Optional[str] = None
    location: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """用户列表响应（分页）"""
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    users: List[UserResponse] = Field(..., description="用户列表")


class UserEquipmentResponse(BaseModel):
    """用户装备响应"""
    user_equipment_id: int
    user_id: int
    equipment_id: int
    equipment_name: Optional[str] = None
    category: Optional[str] = None
    brand_name: Optional[str] = None
    purchase_date: Optional[str] = None
    purchase_price: Optional[float] = None
    condition: Optional[str] = None
    notes: Optional[str] = None
    is_favorite: bool = False
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class FishingLogResponse(BaseModel):
    """钓鱼记录响应"""
    id: int  # 使用 id 而非 log_id
    user_id: int
    date: str  # 使用 date 而非 fishing_date
    location: Optional[str] = None
    weather_condition: Optional[str] = None
    temperature: Optional[float] = None
    fish_caught: Optional[str] = None  # 使用 fish_caught 而非 fish_species
    total_count: Optional[int] = None  # 使用 total_count 而非 fish_count
    total_weight: Optional[float] = None  # 使用 total_weight 而非 fish_total_weight
    equipment_used: Optional[str] = None
    notes: Optional[str] = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class UserStatsResponse(BaseModel):
    """用户统计响应"""
    equipment_count: int = Field(0, description="装备总数")
    favorite_count: int = Field(0, description="收藏装备数")
    equipment_total_cost: float = Field(0, description="装备总花费")
    fishing_logs_count: int = Field(0, description="钓鱼记录数")
    total_fish_caught: int = Field(0, description="总钓鱼数量")
    total_weight: float = Field(0, description="总钓获重量(kg)")


class BatchUpdateResponse(BaseModel):
    """批量更新响应"""
    success: bool = Field(..., description="是否成功")
    updated_count: int = Field(..., description="更新的用户数量")
    message: str = Field(..., description="结果消息")
