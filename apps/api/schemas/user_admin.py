"""
用户管理 Schema
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# ========== 用户 Schema ==========

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
