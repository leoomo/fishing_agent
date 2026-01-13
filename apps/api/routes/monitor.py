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


# ========== Failure Analytics Endpoints ==========
# Import at the top of file when adding these imports:
# from apps.api.services.failure_analytics_service import FailureAnalyticsService


@router.get(
    "/failure-patterns",
    summary="Failure Pattern Detection",
    description="Detect failure patterns in the system using advanced analytics"
)
async def get_failure_patterns(
    time_range: str = Query("1h", description="Time range for analysis (e.g., '1h', '24h', '7d')"),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.MONITOR_READ))
):
    """
    Get detected failure patterns

    Args:
        time_range: Time range for pattern analysis

    Returns:
        List of detected failure patterns
    """
    try:
        from apps.api.services.failure_analytics_service import FailureAnalyticsService
        from apps.api.orm.session import get_db_session

        with get_db_session() as db:
            analytics_service = FailureAnalyticsService(db)
            patterns = await analytics_service.detect_failure_patterns(time_range)

            # Convert to response format
            pattern_data = []
            for pattern in patterns:
                pattern_data.append({
                    'pattern_id': pattern.pattern_id,
                    'pattern_type': pattern.pattern_type,
                    'description': pattern.description,
                    'severity': pattern.severity,
                    'frequency': pattern.frequency,
                    'affected_services': pattern.affected_services,
                    'confidence': pattern.confidence,
                    'detected_at': pattern.detected_at.isoformat(),
                    'metadata': pattern.metadata
                })

            return {
                'status': 'success',
                'patterns': pattern_data,
                'time_range': time_range,
                'total_patterns': len(pattern_data)
            }

    except Exception as e:
        logger.error(f"获取失败模式失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get(
    "/error-correlation/{correlation_id}",
    summary="Error Correlation Analysis",
    description="Get error correlation chain for a specific correlation ID"
)
async def get_error_correlation(
    correlation_id: str,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.MONITOR_READ))
):
    """
    Get error correlation chain

    Args:
        correlation_id: Correlation ID to analyze

    Returns:
        Error correlation chain with related errors
    """
    try:
        from apps.api.services.failure_analytics_service import FailureAnalyticsService
        from apps.api.orm.session import get_db_session

        with get_db_session() as db:
            analytics_service = FailureAnalyticsService(db)
            error_chain = await analytics_service.get_error_correlation(correlation_id)

            if not error_chain:
                raise HTTPException(status_code=404, detail="未找到相关错误链")

            return {
                'status': 'success',
                'correlation_id': error_chain.correlation_id,
                'errors': error_chain.errors,
                'root_cause': error_chain.root_cause,
                'impact_score': error_chain.impact_score,
                'total_errors': len(error_chain.errors)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取错误关联失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get(
    "/root-cause-analysis",
    summary="Root Cause Analysis",
    description="Perform automated root cause analysis on recent failures"
)
async def get_root_cause_analysis(
    time_range: str = Query("24h", description="Time range for analysis (e.g., '1h', '24h', '7d')"),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.MONITOR_READ))
):
    """
    Get root cause analysis

    Args:
        time_range: Time range for analysis

    Returns:
        List of potential root causes with confidence scores
    """
    try:
        from apps.api.services.failure_analytics_service import FailureAnalyticsService
        from apps.api.orm.session import get_db_session

        with get_db_session() as db:
            analytics_service = FailureAnalyticsService(db)
            root_causes = await analytics_service.get_root_cause_analysis(time_range)

            # Convert to response format
            cause_data = []
            for cause in root_causes:
                cause_data.append({
                    'cause_id': cause.cause_id,
                    'cause_type': cause.cause_type,
                    'description': cause.description,
                    'confidence': cause.confidence,
                    'evidence': cause.evidence,
                    'suggested_action': cause.suggested_action,
                    'generated_at': cause.generated_at.isoformat()
                })

            return {
                'status': 'success',
                'root_causes': cause_data,
                'time_range': time_range,
                'total_causes': len(cause_data)
            }

    except Exception as e:
        logger.error(f"获取根因分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get(
    "/failure-metrics",
    summary="Comprehensive Failure Metrics",
    description="Get comprehensive failure metrics and statistics"
)
async def get_failure_metrics(
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.MONITOR_READ))
):
    """
    Get comprehensive failure metrics

    Returns:
        Dictionary with failure statistics and metrics
    """
    try:
        from apps.api.services.failure_analytics_service import FailureAnalyticsService
        from apps.api.orm.session import get_db_session

        with get_db_session() as db:
            analytics_service = FailureAnalyticsService(db)
            metrics = await analytics_service.get_failure_metrics()

            return {
                'status': 'success',
                'metrics': metrics,
                'generated_at': datetime.utcnow().isoformat()
            }

    except Exception as e:
        logger.error(f"获取失败指标失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


# ========== 缓存监控端点 ==========

@router.get(
    "/cache-stats",
    summary="缓存统计",
    description="获取天气缓存统计信息（命中率、缓存项数等）"
)
async def get_cache_stats(
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.MONITOR_READ))
):
    """
    获取缓存统计信息

    Returns:
        缓存统计数据，包括命中率、缓存项数等
    """
    try:
        from packages.agents.fishing.utils.cache import cache

        stats = cache.get_stats()

        return {
            "status": "success",
            "weather_cache": stats,
            "summary": {
                "hit_rate": f"{stats['hit_rate']}%",
                "total_requests": stats['hits'] + stats['misses'],
                "cached_items": stats['valid_items']
            }
        }

    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post(
    "/cache-stats/reset",
    summary="重置缓存统计",
    description="重置缓存命中率统计计数"
)
async def reset_cache_stats(
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.MONITOR_READ))
):
    """
    重置缓存统计计数

    Returns:
        操作结果
    """
    try:
        from packages.agents.fishing.utils.cache import cache

        cache.reset_stats()

        return {
            "status": "success",
            "message": "缓存统计已重置"
        }

    except Exception as e:
        logger.error(f"重置缓存统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"重置失败: {str(e)}")
