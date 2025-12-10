"""
系统监控路由 - 统计和健康检查
"""

from fastapi import APIRouter, HTTPException, Query, Depends, WebSocket, WebSocketDisconnect
import asyncio
import logging
from typing import Optional
from datetime import datetime

from apps.api.schemas.monitor import (
    APIStatsResponse,
    LLMStatsResponse,
    DBPerformanceResponse,
    SystemHealthResponse
)
from apps.api.auth.dependencies import require_permission, CurrentUser
from apps.api.auth.permissions import PermissionEnum
from apps.api.services.monitor_service import MonitorService

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== 监控统计端点 ==========

@router.get(
    "/api-stats",
    response_model=APIStatsResponse,
    summary="API 调用统计",
    description="获取 API 调用统计数据（支持日期范围过滤）"
)
async def get_api_stats(
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.MONITOR_READ))
):
    """
    获取 API 调用统计

    Args:
        start_date: 开始日期（默认最近7天）
        end_date: 结束日期（默认今天）

    Returns:
        APIStatsResponse: API 统计数据
    """
    try:
        monitor_service = MonitorService()

        stats = monitor_service.get_api_stats(
            start_date=start_date,
            end_date=end_date
        )

        return APIStatsResponse(**stats)

    except Exception as e:
        logger.error(f"获取 API 统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get(
    "/llm-stats",
    response_model=LLMStatsResponse,
    summary="LLM 使用统计",
    description="获取 LLM 使用统计（Token、成本、成功率等）"
)
async def get_llm_stats(
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.MONITOR_READ))
):
    """
    获取 LLM 使用统计

    Args:
        start_date: 开始日期（默认最近7天）
        end_date: 结束日期（默认今天）

    Returns:
        LLMStatsResponse: LLM 统计数据
    """
    try:
        monitor_service = MonitorService()

        stats = monitor_service.get_llm_stats(
            start_date=start_date,
            end_date=end_date
        )

        return LLMStatsResponse(**stats)

    except Exception as e:
        logger.error(f"获取 LLM 统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get(
    "/db-performance",
    response_model=DBPerformanceResponse,
    summary="数据库性能监控",
    description="获取数据库性能指标（查询时间、连接池、表大小等）"
)
async def get_db_performance(
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.MONITOR_READ))
):
    """
    获取数据库性能指标

    Returns:
        DBPerformanceResponse: 数据库性能数据
    """
    try:
        monitor_service = MonitorService()
        performance = monitor_service.get_db_performance()

        return DBPerformanceResponse(**performance)

    except Exception as e:
        logger.error(f"获取数据库性能失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get(
    "/health-check",
    response_model=SystemHealthResponse,
    summary="系统健康检查",
    description="系统健康检查（无需认证）"
)
async def health_check():
    """
    系统健康检查（无需认证）

    Returns:
        SystemHealthResponse: 健康状态
    """
    try:
        monitor_service = MonitorService()
        health = monitor_service.check_system_health()

        return SystemHealthResponse(**health)

    except Exception as e:
        logger.error(f"健康检查失败: {e}", exc_info=True)
        return SystemHealthResponse(
            status="unhealthy",
            api_status="unknown",
            db_status="unknown",
            llm_status="unknown",
            uptime_seconds=0
        )


# ========== WebSocket 实时监控 ==========

@router.websocket("/ws/realtime-stats")
async def websocket_realtime_stats(websocket: WebSocket):
    """
    WebSocket 实时统计推送

    推送数据:
    - API 调用量（每分钟）
    - LLM Token 使用（每分钟）
    - 错误率

    Note:
        连接后每5秒推送一次最新统计数据
    """
    await websocket.accept()

    try:
        logger.info("实时监控 WebSocket 连接建立")

        monitor_service = MonitorService()

        while True:
            # 获取实时统计
            stats = monitor_service.get_realtime_stats()

            # 推送数据
            await websocket.send_json({
                "timestamp": datetime.utcnow().isoformat(),
                **stats
            })

            # 每5秒推送一次
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        logger.info("实时监控 WebSocket 客户端断开")
    except Exception as e:
        logger.error(f"实时监控 WebSocket 错误: {e}", exc_info=True)
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
