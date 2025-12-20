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
    SystemHealthResponse,
    AgentStatsResponse,
    ToolStatsResponse,
    LatencyPercentilesResponse,
    CostReportResponse,
    AgentTrendsResponse
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


# ========== Agent 监控端点 ==========

@router.get(
    "/agent-stats",
    response_model=AgentStatsResponse,
    summary="Agent 执行统计",
    description="获取各 Agent 的执行统计（执行次数、Token、成本、成功率等）"
)
async def get_agent_stats(
    agent_type: Optional[str] = Query(None, description="过滤特定 Agent 类型"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.MONITOR_READ))
):
    """
    获取 Agent 执行统计

    Args:
        agent_type: 过滤特定 Agent 类型 (fishing/equipment_import)
        start_date: 开始日期（默认最近7天）
        end_date: 结束日期（默认今天）

    Returns:
        AgentStatsResponse: Agent 统计数据
    """
    try:
        monitor_service = MonitorService()

        stats = monitor_service.get_agent_stats(
            agent_type=agent_type,
            start_date=start_date,
            end_date=end_date
        )

        return AgentStatsResponse(**stats)

    except Exception as e:
        logger.error(f"获取 Agent 统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get(
    "/tool-stats",
    response_model=ToolStatsResponse,
    summary="工具使用统计",
    description="获取工具调用统计（调用次数、成功率、延时等）"
)
async def get_tool_stats(
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.MONITOR_READ))
):
    """
    获取工具使用统计

    Args:
        start_date: 开始日期（默认最近7天）
        end_date: 结束日期（默认今天）

    Returns:
        ToolStatsResponse: 工具统计数据
    """
    try:
        monitor_service = MonitorService()

        stats = monitor_service.get_tool_stats(
            start_date=start_date,
            end_date=end_date
        )

        return ToolStatsResponse(**stats)

    except Exception as e:
        logger.error(f"获取工具统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get(
    "/latency-percentiles",
    response_model=LatencyPercentilesResponse,
    summary="延时百分位",
    description="获取 Agent 执行延时百分位数据（P50/P90/P99）"
)
async def get_latency_percentiles(
    agent_type: Optional[str] = Query(None, description="过滤特定 Agent 类型"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.MONITOR_READ))
):
    """
    获取延时百分位数据

    Args:
        agent_type: 过滤特定 Agent 类型
        start_date: 开始日期（默认最近7天）

    Returns:
        LatencyPercentilesResponse: 延时百分位数据
    """
    try:
        monitor_service = MonitorService()

        stats = monitor_service.get_latency_percentiles(
            agent_type=agent_type,
            start_date=start_date
        )

        return LatencyPercentilesResponse(**stats)

    except Exception as e:
        logger.error(f"获取延时百分位失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get(
    "/cost-report",
    response_model=CostReportResponse,
    summary="成本报表",
    description="获取 Agent 成本报表（按日/Agent 类型分组）"
)
async def get_cost_report(
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    group_by: str = Query("day", description="分组方式 (day/week/month)"),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.MONITOR_READ))
):
    """
    获取成本报表

    Args:
        start_date: 开始日期（默认最近30天）
        end_date: 结束日期（默认今天）
        group_by: 分组方式

    Returns:
        CostReportResponse: 成本报表数据
    """
    try:
        monitor_service = MonitorService()

        stats = monitor_service.get_cost_report(
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )

        return CostReportResponse(**stats)

    except Exception as e:
        logger.error(f"获取成本报表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get(
    "/agent-trends",
    response_model=AgentTrendsResponse,
    summary="Agent 趋势",
    description="获取 Agent 执行趋势数据（按日统计）"
)
async def get_agent_trends(
    agent_type: Optional[str] = Query(None, description="过滤特定 Agent 类型"),
    days: int = Query(7, description="统计天数", ge=1, le=90),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.MONITOR_READ))
):
    """
    获取 Agent 趋势数据

    Args:
        agent_type: 过滤特定 Agent 类型
        days: 统计天数（默认7天）

    Returns:
        AgentTrendsResponse: 趋势数据
    """
    try:
        monitor_service = MonitorService()

        stats = monitor_service.get_agent_trends(
            agent_type=agent_type,
            days=days
        )

        return AgentTrendsResponse(**stats)

    except Exception as e:
        logger.error(f"获取 Agent 趋势失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")
