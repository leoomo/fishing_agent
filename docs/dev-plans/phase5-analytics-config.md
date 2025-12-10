# Phase 5: 数据分析 + 配置管理开发详细方案

**目标**: 实现数据分析和配置管理功能
**周期**: 第 7 周（5 个工作日）
**优先级**: P1（核心功能）

---

## 目标概述

构建数据分析能力和系统配置管理，提供业务洞察和灵活的参数调整。

**核心功能**:
- 装备数据统计（数量趋势、价格分布、品牌占比）
- 用户行为分析（活跃度、查询热点、装备偏好）
- 业务报表生成（周报/月报）
- Agent 配置管理
- 推荐算法参数调整
- API 密钥管理（加密存储）

---

## Step 1: 数据分析 API（Day 1-3）

### 1.1 创建分析 Schema

**文件**: `apps/api/schemas/analytics.py`

**步骤**:
1. 定义分析相关 Schema:

```python
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
```

### 1.2 实现分析路由

**文件**: `apps/api/routes/analytics.py`

**步骤**:
1. 实现数据分析端点:

```python
from fastapi import APIRouter, HTTPException, Query, Depends
import logging
from typing import Optional
from datetime import datetime, timedelta

from apps.api.schemas.analytics import (
    EquipmentStatsResponse,
    EquipmentTrendResponse,
    UserBehaviorStatsResponse,
    BusinessReportRequest,
    BusinessReportResponse,
    ReportListResponse
)
from apps.api.auth.dependencies import require_permission, CurrentUser
from apps.api.auth.permissions import PermissionEnum
from apps.api.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== 装备数据分析 ==========

@router.get(
    "/equipment/stats",
    response_model=EquipmentStatsResponse,
    summary="装备数据统计总览",
    dependencies=[Depends(require_permission(PermissionEnum.ANALYTICS_READ))]
)
async def get_equipment_stats():
    """
    获取装备数据统计总览

    Returns:
        EquipmentStatsResponse: 装备统计数据
    """
    try:
        analytics_service = AnalyticsService()
        stats = analytics_service.get_equipment_stats()

        return EquipmentStatsResponse(**stats)

    except Exception as e:
        logger.error(f"获取装备统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get(
    "/equipment/trends",
    response_model=List[EquipmentTrendResponse],
    summary="装备数量趋势（按月）",
    dependencies=[Depends(require_permission(PermissionEnum.ANALYTICS_READ))]
)
async def get_equipment_trends(
    months: int = Query(12, ge=1, le=36, description="统计月数")
):
    """
    获取装备数量趋势（按月统计）

    Args:
        months: 统计月数（1-36）

    Returns:
        List[EquipmentTrendResponse]: 趋势数据
    """
    try:
        analytics_service = AnalyticsService()
        trends = analytics_service.get_equipment_trends(months=months)

        return [EquipmentTrendResponse(**trend) for trend in trends]

    except Exception as e:
        logger.error(f"获取装备趋势失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get(
    "/equipment/price-distribution",
    response_model=List[PriceDistributionResponse],
    summary="价格分布统计",
    dependencies=[Depends(require_permission(PermissionEnum.ANALYTICS_READ))]
)
async def get_price_distribution(
    category: Optional[str] = Query(None, description="类别过滤")
):
    """
    获取价格分布统计

    Args:
        category: 装备类别（可选）

    Returns:
        List[PriceDistributionResponse]: 价格分布数据
    """
    try:
        analytics_service = AnalyticsService()
        distribution = analytics_service.get_price_distribution(category=category)

        return [PriceDistributionResponse(**item) for item in distribution]

    except Exception as e:
        logger.error(f"获取价格分布失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get(
    "/equipment/brand-stats",
    response_model=List[BrandStatsResponse],
    summary="品牌统计排行",
    dependencies=[Depends(require_permission(PermissionEnum.ANALYTICS_READ))]
)
async def get_brand_stats(
    top_n: int = Query(10, ge=1, le=50, description="Top N 品牌")
):
    """
    获取品牌统计排行

    Args:
        top_n: 返回前 N 个品牌

    Returns:
        List[BrandStatsResponse]: 品牌统计数据
    """
    try:
        analytics_service = AnalyticsService()
        stats = analytics_service.get_brand_stats(top_n=top_n)

        return [BrandStatsResponse(**item) for item in stats]

    except Exception as e:
        logger.error(f"获取品牌统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


# ========== 用户行为分析 ==========

@router.get(
    "/users/activity",
    response_model=List[UserActivityResponse],
    summary="用户活跃度统计",
    dependencies=[Depends(require_permission(PermissionEnum.ANALYTICS_READ))]
)
async def get_user_activity(
    days: int = Query(30, ge=1, le=365, description="统计天数")
):
    """
    获取用户活跃度统计

    Args:
        days: 统计天数

    Returns:
        List[UserActivityResponse]: 活跃度数据
    """
    try:
        analytics_service = AnalyticsService()
        activity = analytics_service.get_user_activity(days=days)

        return [UserActivityResponse(**item) for item in activity]

    except Exception as e:
        logger.error(f"获取用户活跃度失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get(
    "/users/retention",
    response_model=Dict,
    summary="用户留存率分析",
    dependencies=[Depends(require_permission(PermissionEnum.ANALYTICS_READ))]
)
async def get_user_retention():
    """
    获取用户留存率分析

    Returns:
        dict: 留存率数据
    """
    try:
        analytics_service = AnalyticsService()
        retention = analytics_service.get_user_retention()

        return retention

    except Exception as e:
        logger.error(f"获取用户留存率失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get(
    "/queries/hotspots",
    response_model=List[QueryHotspotResponse],
    summary="查询热点分析",
    dependencies=[Depends(require_permission(PermissionEnum.ANALYTICS_READ))]
)
async def get_query_hotspots(
    top_n: int = Query(20, ge=1, le=100, description="Top N 热点")
):
    """
    获取查询热点分析

    Args:
        top_n: 返回前 N 个热点

    Returns:
        List[QueryHotspotResponse]: 热点数据
    """
    try:
        analytics_service = AnalyticsService()
        hotspots = analytics_service.get_query_hotspots(top_n=top_n)

        return [QueryHotspotResponse(**item) for item in hotspots]

    except Exception as e:
        logger.error(f"获取查询热点失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


# ========== 业务报表 ==========

@router.post(
    "/reports/generate",
    response_model=BusinessReportResponse,
    summary="生成业务报表",
    dependencies=[Depends(require_permission(PermissionEnum.ANALYTICS_READ))]
)
async def generate_report(
    request: BusinessReportRequest,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.ANALYTICS_READ))
):
    """
    生成业务报表

    Args:
        request: 报表生成请求

    Returns:
        BusinessReportResponse: 生成的报表
    """
    try:
        analytics_service = AnalyticsService()

        report = analytics_service.generate_report(
            report_type=request.report_type,
            start_date=request.start_date,
            end_date=request.end_date,
            generated_by=current_user.username
        )

        logger.info(
            f"报表生成成功: report_id={report['report_id']}, "
            f"type={request.report_type}, user={current_user.username}"
        )

        return BusinessReportResponse(**report)

    except Exception as e:
        logger.error(f"生成报表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get(
    "/reports/list",
    response_model=ReportListResponse,
    summary="查询报表列表",
    dependencies=[Depends(require_permission(PermissionEnum.ANALYTICS_READ))]
)
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    report_type: Optional[str] = Query(None)
):
    """
    查询报表列表

    Args:
        page: 页码
        page_size: 每页数量
        report_type: 报表类型过滤

    Returns:
        ReportListResponse: 报表列表
    """
    try:
        analytics_service = AnalyticsService()

        result = analytics_service.list_reports(
            page=page,
            page_size=page_size,
            report_type=report_type
        )

        return ReportListResponse(**result)

    except Exception as e:
        logger.error(f"查询报表列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
```

### 1.3 实现分析服务

**文件**: `apps/api/services/analytics_service.py`

**步骤**:
1. 实现数据分析逻辑:

```python
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import func

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.models.equipment import Equipment, Brand
from packages.agent_fishing.tools.lure.models.user import User, UserEquipment
from packages.agent_fishing.tools.lure.models.system import AnalyticsReport, APILog

logger = logging.getLogger(__name__)


class AnalyticsService:
    """数据分析服务"""

    def get_equipment_stats(self) -> Dict:
        """
        获取装备统计总览

        Returns:
            dict: 装备统计数据
        """
        with get_db_session() as session:
            # 总装备数
            total_equipment = session.query(Equipment).filter(
                Equipment.is_active == True
            ).count()

            # 总品牌数
            total_brands = session.query(Brand).count()

            # 平均价格
            avg_price = session.query(
                func.avg((Equipment.price_min + Equipment.price_max) / 2)
            ).filter(
                Equipment.is_active == True,
                Equipment.price_min.isnot(None),
                Equipment.price_max.isnot(None)
            ).scalar() or 0

            # 价格分布
            price_distribution = self.get_price_distribution()

            # Top 品牌
            top_brands = self.get_brand_stats(top_n=10)

            # 按类别统计
            by_category = {}
            categories = session.query(
                Equipment.category,
                func.count(Equipment.equipment_id)
            ).filter(
                Equipment.is_active == True
            ).group_by(
                Equipment.category
            ).all()

            for category, count in categories:
                by_category[category] = count

            return {
                "total_equipment": total_equipment,
                "total_brands": total_brands,
                "avg_price": round(avg_price, 2),
                "price_distribution": price_distribution,
                "top_brands": top_brands,
                "by_category": by_category
            }

    def get_equipment_trends(self, months: int = 12) -> List[Dict]:
        """
        获取装备数量趋势（按月）

        Args:
            months: 统计月数

        Returns:
            list: 趋势数据
        """
        with get_db_session() as session:
            # 计算起始月份
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)

            # 按月统计
            trends = session.query(
                func.strftime('%Y-%m', Equipment.created_at).label('month'),
                func.count(Equipment.equipment_id).label('count'),
                Equipment.category
            ).filter(
                Equipment.created_at >= start_date,
                Equipment.is_active == True
            ).group_by(
                'month',
                Equipment.category
            ).order_by(
                'month'
            ).all()

            # 组织数据
            result = {}
            for month, count, category in trends:
                if month not in result:
                    result[month] = {
                        'date': month,
                        'total_count': 0,
                        'by_category': {}
                    }

                result[month]['total_count'] += count
                result[month]['by_category'][category] = count

            return list(result.values())

    def get_price_distribution(self, category: Optional[str] = None) -> List[Dict]:
        """
        获取价格分布统计

        Args:
            category: 装备类别（可选）

        Returns:
            list: 价格分布数据
        """
        with get_db_session() as session:
            query = session.query(Equipment).filter(
                Equipment.is_active == True,
                Equipment.price_min.isnot(None),
                Equipment.price_max.isnot(None)
            )

            if category:
                query = query.filter(Equipment.category == category)

            equipment_list = query.all()

            # 定义价格区间
            price_ranges = [
                (0, 100),
                (100, 300),
                (300, 500),
                (500, 1000),
                (1000, 2000),
                (2000, 5000),
                (5000, float('inf'))
            ]

            distribution = []
            total_count = len(equipment_list)

            for min_price, max_price in price_ranges:
                count = sum(
                    1 for eq in equipment_list
                    if min_price <= ((eq.price_min + eq.price_max) / 2) < max_price
                )

                if count > 0:
                    range_label = f"{min_price}-{max_price}" if max_price != float('inf') else f"{min_price}+"

                    distribution.append({
                        "price_range": range_label,
                        "count": count,
                        "percentage": round(count / total_count * 100, 2) if total_count > 0 else 0
                    })

            return distribution

    def get_brand_stats(self, top_n: int = 10) -> List[Dict]:
        """
        获取品牌统计排行

        Args:
            top_n: 返回前 N 个品牌

        Returns:
            list: 品牌统计数据
        """
        with get_db_session() as session:
            # 统计每个品牌的装备数量和平均价格
            brand_stats = session.query(
                Brand.brand_id,
                Brand.name_cn,
                func.count(Equipment.equipment_id).label('equipment_count'),
                func.avg((Equipment.price_min + Equipment.price_max) / 2).label('avg_price'),
                func.sum((Equipment.price_min + Equipment.price_max) / 2).label('total_value')
            ).join(
                Equipment,
                Equipment.brand_id == Brand.brand_id
            ).filter(
                Equipment.is_active == True
            ).group_by(
                Brand.brand_id,
                Brand.name_cn
            ).order_by(
                func.count(Equipment.equipment_id).desc()
            ).limit(top_n).all()

            # 计算总装备数（用于计算百分比）
            total_equipment = session.query(Equipment).filter(
                Equipment.is_active == True
            ).count()

            result = []
            for brand_id, name_cn, count, avg_price, total_value in brand_stats:
                result.append({
                    "brand_id": brand_id,
                    "brand_name": name_cn,
                    "equipment_count": count,
                    "avg_price": round(avg_price or 0, 2),
                    "total_value": round(total_value or 0, 2),
                    "percentage": round(count / total_equipment * 100, 2) if total_equipment > 0 else 0
                })

            return result

    def get_user_activity(self, days: int = 30) -> List[Dict]:
        """
        获取用户活跃度统计

        Args:
            days: 统计天数

        Returns:
            list: 活跃度数据
        """
        with get_db_session() as session:
            # TODO: 实现基于 API 日志的活跃度统计
            # 需要从 api_logs 表中提取用户活跃数据

            # 占位符实现
            result = []
            for i in range(days):
                date = (datetime.now() - timedelta(days=days-i-1)).date()
                result.append({
                    "date": date.isoformat(),
                    "dau": 0,  # 日活跃用户数
                    "new_users": 0,  # 新增用户数
                    "active_rate": 0.0  # 活跃率
                })

            return result

    def get_user_retention(self) -> Dict:
        """
        获取用户留存率分析

        Returns:
            dict: 留存率数据
        """
        # TODO: 实现用户留存率计算
        # 次日留存、7日留存、30日留存

        return {
            "retention_1d": 0.0,
            "retention_7d": 0.0,
            "retention_30d": 0.0
        }

    def get_query_hotspots(self, top_n: int = 20) -> List[Dict]:
        """
        获取查询热点分析

        Args:
            top_n: 返回前 N 个热点

        Returns:
            list: 热点数据
        """
        # TODO: 实现基于 LLM 日志或 API 日志的查询热点分析
        # 需要提取用户查询关键词

        return []

    def generate_report(
        self,
        report_type: str,
        start_date: str,
        end_date: str,
        generated_by: str
    ) -> Dict:
        """
        生成业务报表

        Args:
            report_type: 报表类型（weekly/monthly/custom）
            start_date: 开始日期
            end_date: 结束日期
            generated_by: 生成人

        Returns:
            dict: 报表数据
        """
        with get_db_session() as session:
            # 收集报表数据
            report_data = {
                "equipment": {
                    "new_count": 0,  # 新增装备数
                    "total_count": 0,  # 总装备数
                    "avg_price": 0.0  # 平均价格
                },
                "users": {
                    "new_count": 0,  # 新增用户数
                    "active_count": 0,  # 活跃用户数
                    "retention_rate": 0.0  # 留存率
                },
                "api": {
                    "total_calls": 0,  # 总调用量
                    "avg_response_time": 0.0,  # 平均响应时间
                    "error_rate": 0.0  # 错误率
                },
                "llm": {
                    "total_calls": 0,  # 总调用量
                    "total_tokens": 0,  # 总 Token 数
                    "total_cost": 0.0  # 总成本
                }
            }

            # 创建报表记录
            report = AnalyticsReport(
                report_type=report_type,
                start_date=datetime.fromisoformat(start_date).date(),
                end_date=datetime.fromisoformat(end_date).date(),
                report_data=str(report_data),  # JSON 字符串
                generated_by=None,  # TODO: 关联 admin_user_id
                is_published=True
            )

            session.add(report)
            session.commit()
            session.refresh(report)

            return {
                "report_id": report.id,
                "report_type": report.report_type,
                "start_date": report.start_date.isoformat(),
                "end_date": report.end_date.isoformat(),
                "report_data": report_data,
                "generated_at": report.created_at.isoformat(),
                "generated_by": generated_by
            }

    def list_reports(
        self,
        page: int = 1,
        page_size: int = 20,
        report_type: Optional[str] = None
    ) -> Dict:
        """
        查询报表列表

        Args:
            page: 页码
            page_size: 每页数量
            report_type: 报表类型过滤

        Returns:
            dict: 报表列表
        """
        with get_db_session() as session:
            query = session.query(AnalyticsReport)

            if report_type:
                query = query.filter(AnalyticsReport.report_type == report_type)

            total = query.count()

            reports = query.order_by(
                AnalyticsReport.created_at.desc()
            ).limit(page_size).offset((page - 1) * page_size).all()

            return {
                "total": total,
                "reports": [
                    {
                        "report_id": r.id,
                        "report_type": r.report_type,
                        "start_date": r.start_date.isoformat(),
                        "end_date": r.end_date.isoformat(),
                        "report_data": eval(r.report_data),  # 转换回 dict
                        "generated_at": r.created_at.isoformat(),
                        "generated_by": "admin"  # TODO: 从关联表获取
                    }
                    for r in reports
                ]
            }
```

---

## Step 2: 配置管理 API（Day 4-5）

### 2.1 创建配置 Schema

**文件**: `apps/api/schemas/config.py`

**步骤**:
1. 定义配置相关 Schema:

```python
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ConfigCreate(BaseModel):
    """创建配置请求"""
    config_key: str = Field(..., min_length=1, max_length=100, description="配置键")
    config_value: str = Field(..., description="配置值（JSON字符串）")
    config_type: str = Field(
        ...,
        pattern="^(agent|algorithm|api|system)$",
        description="配置类型"
    )
    description: Optional[str] = Field(None, description="描述")
    is_encrypted: bool = Field(default=False, description="是否加密")


class ConfigUpdate(BaseModel):
    """更新配置请求"""
    config_value: str = Field(..., description="配置值（JSON字符串）")
    description: Optional[str] = None


class ConfigResponse(BaseModel):
    """配置响应"""
    id: int
    config_key: str
    config_value: Any  # 已解析的 JSON
    config_type: str
    description: Optional[str] = None
    is_encrypted: bool
    created_at: str
    updated_at: str


class TestAPIKeyRequest(BaseModel):
    """测试 API 密钥请求"""
    api_provider: str = Field(
        ...,
        pattern="^(dashscope|caiyun|amap)$",
        description="API 提供商"
    )
    api_key: str = Field(..., description="API 密钥")


class TestAPIKeyResponse(BaseModel):
    """测试 API 密钥响应"""
    valid: bool
    message: str
```

### 2.2 实现配置路由

**文件**: `apps/api/routes/config.py`

**步骤**:
1. 实现配置管理端点:

```python
from fastapi import APIRouter, HTTPException, Query, Depends
import logging
from typing import Optional, List

from apps.api.schemas.config import (
    ConfigCreate,
    ConfigUpdate,
    ConfigResponse,
    TestAPIKeyRequest,
    TestAPIKeyResponse
)
from apps.api.auth.dependencies import require_permission, CurrentUser
from apps.api.auth.permissions import PermissionEnum
from apps.api.services.config_service import ConfigService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/configs",
    response_model=List[ConfigResponse],
    summary="查询配置列表",
    dependencies=[Depends(require_permission(PermissionEnum.CONFIG_READ))]
)
async def list_configs(
    config_type: Optional[str] = Query(None, description="配置类型过滤")
):
    """
    查询配置列表

    Args:
        config_type: 配置类型（agent/algorithm/api/system）

    Returns:
        List[ConfigResponse]: 配置列表
    """
    try:
        config_service = ConfigService()
        configs = config_service.list_configs(config_type=config_type)

        return [ConfigResponse(**config) for config in configs]

    except Exception as e:
        logger.error(f"查询配置列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get(
    "/configs/{config_key}",
    response_model=ConfigResponse,
    summary="获取配置",
    dependencies=[Depends(require_permission(PermissionEnum.CONFIG_READ))]
)
async def get_config(config_key: str):
    """
    获取配置

    Args:
        config_key: 配置键

    Returns:
        ConfigResponse: 配置信息

    Raises:
        HTTPException: 配置不存在
    """
    try:
        config_service = ConfigService()
        config = config_service.get_config(config_key)

        if not config:
            raise HTTPException(status_code=404, detail=f"配置不存在: {config_key}")

        return ConfigResponse(**config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post(
    "/configs",
    response_model=ConfigResponse,
    summary="创建配置",
    dependencies=[Depends(require_permission(PermissionEnum.CONFIG_CREATE))]
)
async def create_config(
    config_data: ConfigCreate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONFIG_CREATE))
):
    """
    创建配置

    Args:
        config_data: 配置数据

    Returns:
        ConfigResponse: 创建的配置

    Raises:
        HTTPException: 配置键已存在
    """
    try:
        config_service = ConfigService()

        config = config_service.create_config(
            config_key=config_data.config_key,
            config_value=config_data.config_value,
            config_type=config_data.config_type,
            description=config_data.description,
            is_encrypted=config_data.is_encrypted
        )

        logger.info(
            f"配置创建成功: key={config_data.config_key}, "
            f"user={current_user.username}"
        )

        return ConfigResponse(**config)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.put(
    "/configs/{config_key}",
    response_model=ConfigResponse,
    summary="更新配置",
    dependencies=[Depends(require_permission(PermissionEnum.CONFIG_UPDATE))]
)
async def update_config(
    config_key: str,
    config_data: ConfigUpdate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONFIG_UPDATE))
):
    """
    更新配置

    Args:
        config_key: 配置键
        config_data: 更新数据

    Returns:
        ConfigResponse: 更新后的配置

    Raises:
        HTTPException: 配置不存在
    """
    try:
        config_service = ConfigService()

        config = config_service.update_config(
            config_key=config_key,
            config_value=config_data.config_value,
            description=config_data.description
        )

        if not config:
            raise HTTPException(status_code=404, detail=f"配置不存在: {config_key}")

        logger.info(f"配置更新成功: key={config_key}, user={current_user.username}")

        return ConfigResponse(**config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete(
    "/configs/{config_key}",
    status_code=204,
    summary="删除配置",
    dependencies=[Depends(require_permission(PermissionEnum.CONFIG_DELETE))]
)
async def delete_config(
    config_key: str,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONFIG_DELETE))
):
    """
    删除配置

    Args:
        config_key: 配置键

    Raises:
        HTTPException: 配置不存在
    """
    try:
        config_service = ConfigService()

        success = config_service.delete_config(config_key)

        if not success:
            raise HTTPException(status_code=404, detail=f"配置不存在: {config_key}")

        logger.info(f"配置删除成功: key={config_key}, user={current_user.username}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post(
    "/configs/test-api-key",
    response_model=TestAPIKeyResponse,
    summary="测试 API 密钥",
    dependencies=[Depends(require_permission(PermissionEnum.CONFIG_TEST))]
)
async def test_api_key(request: TestAPIKeyRequest):
    """
    测试 API 密钥有效性

    Args:
        request: 测试请求

    Returns:
        TestAPIKeyResponse: 测试结果
    """
    try:
        config_service = ConfigService()

        result = config_service.test_api_key(
            api_provider=request.api_provider,
            api_key=request.api_key
        )

        return TestAPIKeyResponse(**result)

    except Exception as e:
        logger.error(f"测试 API 密钥失败: {e}", exc_info=True)
        return TestAPIKeyResponse(
            valid=False,
            message=f"测试失败: {str(e)}"
        )
```

### 2.3 实现配置服务

**文件**: `apps/api/services/config_service.py`

**步骤**:
1. 实现配置管理逻辑:

```python
import json
import logging
from typing import Dict, Optional, List

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.models.system import SystemConfig
from apps.api.utils.encryption import encrypt_value, decrypt_value

logger = logging.getLogger(__name__)


class ConfigService:
    """配置管理服务"""

    def list_configs(self, config_type: Optional[str] = None) -> List[Dict]:
        """
        查询配置列表

        Args:
            config_type: 配置类型过滤

        Returns:
            list: 配置列表
        """
        with get_db_session() as session:
            query = session.query(SystemConfig)

            if config_type:
                query = query.filter(SystemConfig.config_type == config_type)

            configs = query.all()

            result = []
            for config in configs:
                # 解密配置值（如果加密）
                config_value = config.config_value
                if config.is_encrypted:
                    try:
                        config_value = decrypt_value(config_value)
                    except:
                        config_value = "***加密内容***"

                # 解析 JSON
                try:
                    config_value = json.loads(config_value)
                except:
                    pass  # 保持字符串

                result.append({
                    "id": config.id,
                    "config_key": config.config_key,
                    "config_value": config_value,
                    "config_type": config.config_type,
                    "description": config.description,
                    "is_encrypted": config.is_encrypted,
                    "created_at": config.created_at.isoformat(),
                    "updated_at": config.updated_at.isoformat()
                })

            return result

    def get_config(self, config_key: str) -> Optional[Dict]:
        """
        获取配置

        Args:
            config_key: 配置键

        Returns:
            dict: 配置信息
        """
        configs = self.list_configs()
        return next((c for c in configs if c["config_key"] == config_key), None)

    def create_config(
        self,
        config_key: str,
        config_value: str,
        config_type: str,
        description: Optional[str] = None,
        is_encrypted: bool = False
    ) -> Dict:
        """
        创建配置

        Args:
            config_key: 配置键
            config_value: 配置值（JSON字符串）
            config_type: 配置类型
            description: 描述
            is_encrypted: 是否加密

        Returns:
            dict: 创建的配置

        Raises:
            ValueError: 配置键已存在
        """
        with get_db_session() as session:
            # 检查是否存在
            existing = session.query(SystemConfig).filter_by(
                config_key=config_key
            ).first()

            if existing:
                raise ValueError(f"配置键已存在: {config_key}")

            # 加密配置值（如果需要）
            stored_value = config_value
            if is_encrypted:
                stored_value = encrypt_value(config_value)

            # 创建配置
            config = SystemConfig(
                config_key=config_key,
                config_value=stored_value,
                config_type=config_type,
                description=description,
                is_encrypted=is_encrypted
            )

            session.add(config)
            session.commit()
            session.refresh(config)

            # 返回解密后的值
            return self.get_config(config_key)

    def update_config(
        self,
        config_key: str,
        config_value: str,
        description: Optional[str] = None
    ) -> Optional[Dict]:
        """
        更新配置

        Args:
            config_key: 配置键
            config_value: 配置值
            description: 描述

        Returns:
            dict: 更新后的配置
        """
        with get_db_session() as session:
            config = session.query(SystemConfig).filter_by(
                config_key=config_key
            ).first()

            if not config:
                return None

            # 加密配置值（如果需要）
            stored_value = config_value
            if config.is_encrypted:
                stored_value = encrypt_value(config_value)

            # 更新
            config.config_value = stored_value
            if description is not None:
                config.description = description

            session.commit()

            return self.get_config(config_key)

    def delete_config(self, config_key: str) -> bool:
        """
        删除配置

        Args:
            config_key: 配置键

        Returns:
            bool: 是否成功
        """
        with get_db_session() as session:
            config = session.query(SystemConfig).filter_by(
                config_key=config_key
            ).first()

            if not config:
                return False

            session.delete(config)
            session.commit()

            return True

    def test_api_key(self, api_provider: str, api_key: str) -> Dict:
        """
        测试 API 密钥有效性

        Args:
            api_provider: API 提供商
            api_key: API 密钥

        Returns:
            dict: 测试结果
        """
        try:
            if api_provider == "dashscope":
                # 测试通义千问 API
                import requests
                response = requests.get(
                    "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=5
                )
                valid = response.status_code != 401

            elif api_provider == "caiyun":
                # 测试彩云天气 API
                import requests
                response = requests.get(
                    f"https://api.caiyunapp.com/v2.6/{api_key}/120.0,30.0/realtime",
                    timeout=5
                )
                valid = response.status_code == 200

            elif api_provider == "amap":
                # 测试高德地图 API
                import requests
                response = requests.get(
                    f"https://restapi.amap.com/v3/geocode/geo?key={api_key}&address=北京",
                    timeout=5
                )
                valid = response.status_code == 200 and response.json().get("status") == "1"

            else:
                return {"valid": False, "message": f"不支持的 API 提供商: {api_provider}"}

            return {
                "valid": valid,
                "message": "API 密钥有效" if valid else "API 密钥无效"
            }

        except Exception as e:
            return {
                "valid": False,
                "message": f"测试失败: {str(e)}"
            }
```

### 2.4 实现加密工具

**文件**: `apps/api/utils/encryption.py`

**步骤**:
1. 实现配置加密功能:

```python
import os
from cryptography.fernet import Fernet

# 从环境变量读取加密密钥（如果不存在则生成）
ENCRYPTION_KEY = os.getenv('CONFIG_ENCRYPTION_KEY')

if not ENCRYPTION_KEY:
    # 生成新密钥（仅用于开发环境）
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print(f"⚠️  警告: 未设置 CONFIG_ENCRYPTION_KEY，使用临时密钥: {ENCRYPTION_KEY}")
    print("   生产环境请设置环境变量: export CONFIG_ENCRYPTION_KEY=<your_key>")

cipher = Fernet(ENCRYPTION_KEY.encode())


def encrypt_value(value: str) -> str:
    """
    加密配置值

    Args:
        value: 明文字符串

    Returns:
        str: 加密后的字符串
    """
    return cipher.encrypt(value.encode()).decode()


def decrypt_value(encrypted_value: str) -> str:
    """
    解密配置值

    Args:
        encrypted_value: 加密字符串

    Returns:
        str: 明文字符串
    """
    return cipher.decrypt(encrypted_value.encode()).decode()
```

---

## 测试用例

### 分析测试

```bash
# 测试装备统计
curl "http://localhost:8000/api/v1/admin/analytics/equipment/stats" \
  -H "Authorization: Bearer $TOKEN"

# 测试价格分布
curl "http://localhost:8000/api/v1/admin/analytics/equipment/price-distribution?category=鱼竿" \
  -H "Authorization: Bearer $TOKEN"

# 测试报表生成
curl -X POST "http://localhost:8000/api/v1/admin/analytics/reports/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "weekly",
    "start_date": "2025-01-01",
    "end_date": "2025-01-07"
  }'
```

### 配置测试

```bash
# 测试创建配置
curl -X POST "http://localhost:8000/api/v1/admin/config/configs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "config_key": "agent.model",
    "config_value": "{\"provider\": \"qwen\", \"model\": \"qwen-max\"}",
    "config_type": "agent",
    "description": "Agent 模型配置"
  }'

# 测试 API 密钥
curl -X POST "http://localhost:8000/api/v1/admin/config/configs/test-api-key" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "api_provider": "dashscope",
    "api_key": "sk-xxx..."
  }'
```

---

## 注意事项

### 1. 配置加密安全

⚠️ **生产环境必须设置加密密钥**:
```bash
# 生成加密密钥
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 设置环境变量
export CONFIG_ENCRYPTION_KEY=<生成的密钥>
```

### 2. 配置热加载

🚀 **配置更新后自动生效**:
```python
# 可选：实现配置缓存 + 定时刷新
# 或使用 Redis Pub/Sub 推送配置更新
```

### 3. 统计查询优化

🚀 **使用数据库索引**:
```sql
-- 添加统计常用的索引
CREATE INDEX idx_equipment_created_at ON equipment(created_at);
CREATE INDEX idx_api_logs_timestamp ON api_logs(timestamp);
CREATE INDEX idx_llm_logs_timestamp ON llm_logs(timestamp);
```

---

## 验收标准

### 必须完成

- ✅ 装备统计端点（总览、趋势、分布、品牌）
- ✅ 用户行为统计端点（活跃度、留存率、热点）
- ✅ 报表生成和列表端点
- ✅ 配置 CRUD 端点
- ✅ API 密钥测试端点
- ✅ 配置加密功能

### 可选优化

- 🔧 配置版本管理
- 🔧 配置回滚功能
- 🔧 配置变更审计日志
- 🔧 实时数据看板（Dashboard）

---

## 下一步

完成 Phase 5 后，进入 **Phase 6-8: 前端开发**（Week 8-10）
