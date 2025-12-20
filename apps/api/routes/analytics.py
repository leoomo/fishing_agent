from fastapi import APIRouter, HTTPException, Query, Depends
import logging
from typing import Optional, List

from apps.api.schemas.analytics import (
    EquipmentStatsResponse,
    EquipmentTrendResponse,
    PriceDistributionResponse,
    BrandStatsResponse,
    UserActivityResponse,
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
    summary="装备数据统计总览"
    # dependencies=[Depends(require_permission(PermissionEnum.ANALYTICS_READ))]  # 临时移除权限检查
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
    summary="装备数量趋势（按月）"
    # dependencies=[Depends(require_permission(PermissionEnum.ANALYTICS_READ))]  # 临时移除权限检查
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
    summary="价格分布统计"
    # dependencies=[Depends(require_permission(PermissionEnum.ANALYTICS_READ))]  # 临时移除权限检查
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
    summary="品牌统计排行"
    # dependencies=[Depends(require_permission(PermissionEnum.ANALYTICS_READ))]  # 临时移除权限检查
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
