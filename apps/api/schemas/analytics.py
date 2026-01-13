from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import date


# ========== 装备数据分析 ==========

class EquipmentTrendResponse(BaseModel):
    """装备数量趋势响应"""
    date: str  # YYYY-MM
    total_count: int
    by_category: Dict[str, int]  # {category: count}


class PriceDistributionResponse(BaseModel):
    """价格分布响应"""
    price_range: str  # "0-100", "100-300", etc.
    count: int
    percentage: float


class BrandStatsResponse(BaseModel):
    """品牌统计响应"""
    brand_id: int
    brand_name: str
    equipment_count: int
    avg_price: float
    total_value: float
    percentage: float


class EquipmentStatsResponse(BaseModel):
    """装备统计总览"""
    total_equipment: int
    total_brands: int
    avg_price: float
    price_distribution: List[PriceDistributionResponse]
    top_brands: List[BrandStatsResponse]
    by_category: Dict[str, int]


# ========== 用户行为分析 ==========

class UserActivityResponse(BaseModel):
    """用户活跃度响应"""
    date: str
    dau: int  # 日活跃用户数
    new_users: int  # 新增用户数
    active_rate: float  # 活跃率


class QueryHotspotResponse(BaseModel):
    """查询热点响应"""
    keyword: str
    count: int
    category: Optional[str] = None


class UserRetentionResponse(BaseModel):
    """用户留存率响应"""
    retention_1d: float  # 次日留存率 (%)
    retention_7d: float  # 7日留存率 (%)
    retention_30d: float  # 30日留存率 (%)
    new_users_count: int  # 新用户数
    analysis_period_days: int  # 分析周期


class UserPreferenceResponse(BaseModel):
    """用户偏好响应"""
    category: str
    user_count: int
    avg_equipment_count: float


class UserBehaviorStatsResponse(BaseModel):
    """用户行为统计"""
    total_users: int
    active_users_7d: int
    active_users_30d: int
    retention_rate_7d: float
    retention_rate_30d: float
    query_hotspots: List[QueryHotspotResponse]
    category_preferences: List[UserPreferenceResponse]


# ========== 业务报表 ==========

class BusinessReportRequest(BaseModel):
    """业务报表生成请求"""
    report_type: str = Field(..., pattern="^(weekly|monthly|custom)$")
    start_date: str = Field(..., description="开始日期（YYYY-MM-DD）")
    end_date: str = Field(..., description="结束日期（YYYY-MM-DD）")


class BusinessReportResponse(BaseModel):
    """业务报表响应"""
    report_id: int
    report_type: str
    start_date: str
    end_date: str
    report_data: Dict  # 报表数据（JSON）
    generated_at: str
    generated_by: str


class ReportListResponse(BaseModel):
    """报表列表响应"""
    total: int
    reports: List[BusinessReportResponse]
