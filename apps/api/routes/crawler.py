"""
爬虫管理路由 - 任务管理和实时监控
"""

from fastapi import APIRouter, HTTPException, Query, Depends, WebSocket, WebSocketDisconnect, status
import asyncio
import logging
from typing import Optional, List
from datetime import datetime

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.orm.repositories.crawler_repo import CrawlerRepository
from packages.agent_fishing.tools.lure.models.system import CrawlerTask

from apps.api.schemas.crawler import (
    CrawlerTaskCreate,
    CrawlerTaskResponse,
    CrawlerTaskListResponse,
    CrawlerLogResponse,
    TriggerCrawlerRequest,
    SyncStatusResponse
)
from apps.api.auth.dependencies import require_permission, CurrentUser
from apps.api.auth.permissions import PermissionEnum
from apps.api.services.crawler_service import CrawlerService

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== 爬虫任务管理 ==========

@router.get(
    "/tasks",
    response_model=CrawlerTaskListResponse,
    summary="查询爬虫任务列表",
    description="查询爬虫任务列表（支持分页和筛选）"
)
async def list_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    task_type: Optional[str] = Query(None, description="任务类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_READ))
):
    """
    查询爬虫任务列表（分页 + 筛选）

    Returns:
        CrawlerTaskListResponse: 任务列表
    """
    try:
        with get_db_session() as session:
            repo = CrawlerRepository(session)

            filters = {}
            if task_type:
                filters['task_type'] = task_type
            if status:
                filters['status'] = status

            tasks = repo.get_all(
                filters=filters,
                limit=page_size,
                offset=(page - 1) * page_size,
                order_by='created_at DESC'
            )

            total = repo.count(filters=filters)

            return CrawlerTaskListResponse(
                total=total,
                page=page,
                page_size=page_size,
                tasks=[_build_task_response(task) for task in tasks]
            )

    except Exception as e:
        logger.error(f"查询爬虫任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get(
    "/tasks/{task_id}",
    response_model=CrawlerTaskResponse,
    summary="获取爬虫任务详情",
    description="获取指定爬虫任务的详细信息"
)
async def get_task(
    task_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_READ))
):
    """
    获取爬虫任务详情

    Args:
        task_id: 任务ID

    Returns:
        CrawlerTaskResponse: 任务详情

    Raises:
        HTTPException: 任务不存在
    """
    try:
        with get_db_session() as session:
            repo = CrawlerRepository(session)
            task = repo.get(task_id)

            if not task:
                raise HTTPException(
                    status_code=404,
                    detail=f"任务不存在: task_id={task_id}"
                )

            return _build_task_response(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post(
    "/tasks/trigger",
    response_model=CrawlerTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="手动触发爬虫任务",
    description="手动触发爬虫任务（支持自定义关键词和配置）"
)
async def trigger_crawler(
    request: TriggerCrawlerRequest,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_EXECUTE))
):
    """
    手动触发爬虫任务

    Args:
        request: 触发请求（包含任务类型、关键词、配置）

    Returns:
        CrawlerTaskResponse: 创建的任务信息
    """
    try:
        crawler_service = CrawlerService()

        # 创建任务
        task = crawler_service.trigger_crawler(
            task_type=request.task_type,
            keywords=request.keywords,
            max_pages=request.max_pages,
            proxy=request.proxy
        )

        logger.info(
            f"爬虫任务已触发: task_id={task.id}, "
            f"type={request.task_type}, user={current_user.user_id}"
        )

        return _build_task_response(task)

    except Exception as e:
        logger.error(f"触发爬虫任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"触发失败: {str(e)}")


@router.post(
    "/tasks/{task_id}/retry",
    response_model=CrawlerTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="重试失败任务",
    description="重试失败的爬虫任务"
)
async def retry_task(
    task_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_EXECUTE))
):
    """
    重试失败的爬虫任务

    Args:
        task_id: 任务ID

    Returns:
        CrawlerTaskResponse: 新任务信息

    Raises:
        HTTPException: 任务不存在或状态不是 failed
    """
    try:
        with get_db_session() as session:
            repo = CrawlerRepository(session)
            task = repo.get(task_id)

            if not task:
                raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

            if task.status != 'failed':
                raise HTTPException(
                    status_code=400,
                    detail=f"只能重试失败任务，当前状态: {task.status}"
                )

            # 重试任务
            crawler_service = CrawlerService()
            new_task = crawler_service.retry_task(task)

            logger.info(
                f"任务重试: 原task_id={task_id}, 新task_id={new_task.id}, "
                f"user={current_user.user_id}"
            )

            return _build_task_response(new_task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重试任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"重试失败: {str(e)}")


@router.get(
    "/tasks/{task_id}/logs",
    response_model=List[CrawlerLogResponse],
    summary="获取任务日志",
    description="获取指定任务的运行日志"
)
async def get_task_logs(
    task_id: int,
    level: Optional[str] = Query(None, description="日志级别过滤（info/warning/error）"),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_READ))
):
    """
    获取爬虫任务日志

    Args:
        task_id: 任务ID
        level: 日志级别（info/warning/error）

    Returns:
        List[CrawlerLogResponse]: 日志列表
    """
    try:
        with get_db_session() as session:
            repo = CrawlerRepository(session)

            # 验证任务存在
            task = repo.get(task_id)
            if not task:
                raise HTTPException(
                    status_code=404,
                    detail=f"任务不存在: task_id={task_id}"
                )

            logs = repo.get_task_logs(task_id, level=level)

            return [
                CrawlerLogResponse(
                    id=log.id,
                    task_id=log.task_id,
                    level=log.level,
                    message=log.message,
                    details=log.details,
                    created_at=log.created_at.isoformat()
                )
                for log in logs
            ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务日志失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除任务记录",
    description="删除爬虫任务记录（无法删除正在运行的任务）"
)
async def delete_task(
    task_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_DELETE))
):
    """
    删除爬虫任务记录

    Args:
        task_id: 任务ID

    Raises:
        HTTPException: 任务不存在或正在运行
    """
    try:
        with get_db_session() as session:
            repo = CrawlerRepository(session)
            task = repo.get(task_id)

            if not task:
                raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

            if task.status == 'running':
                raise HTTPException(
                    status_code=400,
                    detail="无法删除正在运行的任务"
                )

            repo.delete(task_id)

            logger.info(f"任务记录已删除: task_id={task_id}, user={current_user.user_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get(
    "/sync-status",
    response_model=SyncStatusResponse,
    summary="获取数据同步状态",
    description="获取数据同步状态统计"
)
async def get_sync_status(
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_READ))
):
    """
    获取数据同步状态

    Returns:
        SyncStatusResponse: 同步状态统计
    """
    try:
        crawler_service = CrawlerService()
        status_data = crawler_service.get_sync_status()

        return SyncStatusResponse(**status_data)

    except Exception as e:
        logger.error(f"获取同步状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


# ========== WebSocket 实时监控 ==========

@router.websocket("/ws/crawler/{task_id}")
async def websocket_crawler_progress(websocket: WebSocket, task_id: int):
    """
    WebSocket 实时推送爬虫任务进度

    Args:
        websocket: WebSocket 连接
        task_id: 任务ID
    """
    await websocket.accept()

    try:
        logger.info(f"WebSocket 连接建立: task_id={task_id}")

        while True:
            # 查询任务状态
            with get_db_session() as session:
                repo = CrawlerRepository(session)
                task = repo.get(task_id)

                if not task:
                    await websocket.send_json({
                        "error": f"任务不存在: {task_id}"
                    })
                    break

                # 推送进度
                await websocket.send_json({
                    "task_id": task_id,
                    "status": task.status,
                    "progress": f"{task.success_items}/{task.total_items}",
                    "success_items": task.success_items,
                    "failed_items": task.failed_items,
                    "timestamp": datetime.utcnow().isoformat()
                })

                # 任务结束时断开连接
                if task.status in ['success', 'failed']:
                    logger.info(
                        f"任务已完成，关闭 WebSocket: task_id={task_id}, "
                        f"status={task.status}"
                    )
                    break

            # 每秒推送一次
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info(f"WebSocket 客户端断开连接: task_id={task_id}")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}", exc_info=True)
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


# ========== 辅助函数 ==========

def _build_task_response(task: CrawlerTask) -> CrawlerTaskResponse:
    """构造任务响应对象"""
    return CrawlerTaskResponse(
        id=task.id,
        task_type=task.task_type,
        task_name=task.task_name,
        status=task.status,
        start_time=task.start_time.isoformat() if task.start_time else None,
        end_time=task.end_time.isoformat() if task.end_time else None,
        total_items=task.total_items,
        success_items=task.success_items,
        failed_items=task.failed_items,
        error_message=task.error_message,
        config=task.config,
        result_summary=task.result_summary,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat()
    )
