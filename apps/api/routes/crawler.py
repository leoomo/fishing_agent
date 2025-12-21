"""
数据采集管理路由 - 任务管理和实时监控
"""

from fastapi import APIRouter, HTTPException, Query, Depends, WebSocket, WebSocketDisconnect, status
import asyncio
import json
import logging
from typing import Optional, List
from datetime import datetime, timedelta

from packages.scraper.database import get_crawler_db
from packages.scraper.models import CrawlerTask, TaskStatus
from packages.agent_fishing.tools.lure.orm.repositories.crawler_repo import CrawlerRepository

from apps.api.schemas.crawler import (
    CrawlerTaskCreate,
    CrawlerTaskResponse,
    CrawlerTaskListResponse,
    CrawlerLogResponse,
    TriggerCrawlerRequest,
    SyncStatusResponse,
    # Workflow schemas
    WorkflowTemplateCreate,
    WorkflowTemplateUpdate,
    WorkflowTemplateResponse,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowStatusResponse,
    WorkflowTaskStatus,
    # Schedule schemas
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleJobStatus,
    SchedulePreviewRequest,
    SchedulePreviewResponse,
    CronExpressionRequest,
    CronExpressionResponse,
    ApiResponse,
    PaginatedResponse
)
from apps.api.auth.dependencies import require_permission, CurrentUser
from apps.api.auth.permissions import PermissionEnum
from apps.api.services.crawler_service import CrawlerService

# Workflow imports
from packages.agent_fishing.tools.lure.database import get_db
from packages.scraper.models import CrawlerWorkflowTemplate, CrawlerSchedule, CrawlerLog
from packages.scraper.workflow.manager import WorkflowManager
from packages.scraper.executor.task_queue import CrawlerTaskQueue, configure_database
from packages.scraper.scheduler.workflow_scheduler import WorkflowScheduler

# Scheduler imports
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from croniter import croniter
import uuid
import json

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== 数据采集任务管理 ==========

@router.get(
    "/tasks",
    response_model=CrawlerTaskListResponse,
    summary="查询数据采集任务列表",
    description="查询数据采集任务列表（支持分页和筛选）"
)
async def list_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    task_type: Optional[str] = Query(None, description="任务类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_READ))
):
    """
    查询数据采集任务列表（分页 + 筛选）

    Returns:
        CrawlerTaskListResponse: 任务列表
    """
    try:
        db = get_crawler_db()
        with db.session_scope() as session:
            query = session.query(CrawlerTask)

            if task_type:
                query = query.filter(CrawlerTask.task_type == task_type)
            if status:
                query = query.filter(CrawlerTask.status == status)

            total = query.count()
            tasks = query.order_by(CrawlerTask.created_at.desc()).offset(
                (page - 1) * page_size
            ).limit(page_size).all()

            return CrawlerTaskListResponse(
                total=total,
                page=page,
                page_size=page_size,
                tasks=[_build_task_response(task) for task in tasks]
            )

    except Exception as e:
        logger.error(f"查询数据采集任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get(
    "/tasks/{task_id}",
    response_model=CrawlerTaskResponse,
    summary="获取数据采集任务详情",
    description="获取指定数据采集任务的详细信息"
)
async def get_task(
    task_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_READ))
):
    """
    获取数据采集任务详情

    Args:
        task_id: 任务ID

    Returns:
        CrawlerTaskResponse: 任务详情

    Raises:
        HTTPException: 任务不存在
    """
    try:
        db = get_crawler_db()
        with db.session_scope() as session:
            task = session.query(CrawlerTask).get(task_id)

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


@router.put(
    "/tasks/{task_id}",
    response_model=CrawlerTaskResponse,
    summary="更新数据采集任务",
    description="更新指定数据采集任务的信息"
)
async def update_task(
    task_id: int,
    task_update: dict,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))
):
    """
    更新数据采集任务

    Args:
        task_id: 任务ID
        task_update: 更新数据

    Returns:
        CrawlerTaskResponse: 更新后的任务信息

    Raises:
        HTTPException: 任务不存在或更新失败
    """
    try:
        db = get_crawler_db()
        with db.session_scope() as session:
            task = session.query(CrawlerTask).get(task_id)

            if not task:
                raise HTTPException(
                    status_code=404,
                    detail=f"任务不存在: task_id={task_id}"
                )

            # 检查任务状态是否允许更新
            if task.status == TaskStatus.RUNNING:
                raise HTTPException(
                    status_code=400,
                    detail="运行中的任务不能更新"
                )

            # 更新允许的字段
            allowed_fields = [
                'task_name', 'priority', 'description', 'max_pages',
                'delay_range', 'timeout', 'retry_count', 'extract_images',
                'use_proxy', 'random_ua', 'config'
            ]

            updated = False
            for field, value in task_update.items():
                if field in allowed_fields and hasattr(task, field):
                    if field == 'config' and value:
                        # config字段需要JSON序列化
                        task.config = json.dumps(value, ensure_ascii=False)
                    else:
                        setattr(task, field, value)
                    updated = True

            if not updated:
                raise HTTPException(
                    status_code=400,
                    detail="没有有效的更新字段"
                )

            task.updated_at = datetime.now()
            session.commit()

            logger.info(f"任务更新成功: task_id={task_id}")
            return _build_task_response(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.post(
    "/tasks/trigger",
    response_model=CrawlerTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="手动触发数据采集任务",
    description="手动触发数据采集任务（支持自定义关键词和配置）"
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

        # 创建任务（返回dict）
        task_dict = crawler_service.trigger_crawler(
            task_type=request.task_type,
            keywords=request.keywords,
            shop_url=request.shop_url,
            max_pages=request.max_pages,
            proxy=request.proxy
        )

        logger.info(
            f"爬虫任务已触发: task_id={task_dict.get('id')}, "
            f"type={request.task_type}, user={current_user.user_id}"
        )

        return _build_task_response_from_dict(task_dict)

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
        with get_crawler_db().get_session() as session:
            repo = CrawlerRepository(session)
            task = repo.get(task_id)

            if not task:
                raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

            if task.status != TaskStatus.FAILED:
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


@router.post(
    "/tasks/{task_id}/start",
    response_model=CrawlerTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="启动数据采集任务",
    description="启动等待中的数据采集任务"
)
async def start_task(
    task_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_EXECUTE))
):
    """
    启动数据采集任务

    Args:
        task_id: 任务ID

    Returns:
        CrawlerTaskResponse: 更新后的任务信息

    Raises:
        HTTPException: 任务不存在或状态不允许启动
    """
    try:
        with get_crawler_db().get_session() as session:
            repo = CrawlerRepository(session)
            task = repo.get(task_id)

            if not task:
                raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

            if task.status not in [TaskStatus.PENDING, TaskStatus.FAILED]:
                raise HTTPException(
                    status_code=400,
                    detail=f"只能启动等待或失败的任务，当前状态: {task.status}"
                )

            # 启动任务
            crawler_service = CrawlerService()
            updated_task = crawler_service.start_task(task)

            logger.info(
                f"任务启动: task_id={task_id}, "
                f"user={current_user.user_id}"
            )

            return _build_task_response(updated_task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")


@router.post(
    "/tasks/{task_id}/rerun",
    response_model=CrawlerTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="重新运行任务",
    description="重新运行已完成或失败的任务（重置状态后启动）"
)
async def rerun_task(
    task_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_EXECUTE))
):
    """
    重新运行任务

    将任务状态重置为 PENDING，清空执行结果，然后重新启动。
    支持对成功、失败状态的任务重新运行。

    Args:
        task_id: 任务ID

    Returns:
        CrawlerTaskResponse: 更新后的任务信息

    Raises:
        HTTPException: 任务不存在或正在运行中
    """
    try:
        db = get_crawler_db()
        with db.session_scope() as session:
            task = session.query(CrawlerTask).get(task_id)

            if not task:
                raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

            if task.status == TaskStatus.RUNNING:
                raise HTTPException(
                    status_code=400,
                    detail="任务正在运行中，无法重新运行"
                )

            # 重置任务状态
            task.status = TaskStatus.PENDING
            task.start_time = None
            task.end_time = None
            task.success_items = 0
            task.failed_items = 0
            task.total_items = 0
            task.error_message = None
            task.result_summary = None
            task.retry_count = (task.retry_count or 0) + 1

            session.commit()

            logger.info(
                f"任务已重置: task_id={task_id}, user={current_user.user_id}"
            )

            # 启动任务
            crawler_service = CrawlerService()
            updated_task = crawler_service.start_task(task)

            logger.info(
                f"任务重新运行: task_id={task_id}, user={current_user.user_id}"
            )

            return _build_task_response(updated_task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新运行任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"重新运行失败: {str(e)}")


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
        db = get_crawler_db()
        with db.session_scope() as session:
            # 验证任务存在
            task = session.query(CrawlerTask).get(task_id)
            if not task:
                raise HTTPException(
                    status_code=404,
                    detail=f"任务不存在: task_id={task_id}"
                )

            # 查询日志
            query = session.query(CrawlerLog).filter(CrawlerLog.task_id == task_id)
            if level:
                query = query.filter(CrawlerLog.level == level)

            logs = query.order_by(CrawlerLog.created_at.desc()).limit(100).all()

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
        db = get_crawler_db()
        with db.session_scope() as session:
            task = session.query(CrawlerTask).get(task_id)

            if not task:
                raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

            if task.status == TaskStatus.RUNNING:
                raise HTTPException(
                    status_code=400,
                    detail="无法删除正在运行的任务"
                )

            session.delete(task)
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

    使用 WebSocketManager 管理连接，支持从执行器推送进度

    Args:
        websocket: WebSocket 连接
        task_id: 任务ID
    """
    from apps.api.services.websocket_manager import get_ws_manager

    ws_manager = get_ws_manager()

    try:
        await ws_manager.connect(websocket, task_id)
        logger.info(f"WebSocket 连接建立: task_id={task_id}")

        # 发送初始状态
        with get_crawler_db().get_session() as session:
            repo = CrawlerRepository(session)
            task = repo.get(task_id)

            if task:
                await websocket.send_json({
                    "type": "init",
                    "task_id": task_id,
                    "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                    "progress": 0,
                    "success_items": task.success_items,
                    "failed_items": task.failed_items,
                    "total_items": task.total_items,
                    "timestamp": datetime.utcnow().isoformat()
                })

        # 保持连接，等待客户端消息或断开
        while True:
            try:
                # 等待客户端消息（ping/pong 保活）
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )

                # 处理 ping
                if data == "ping":
                    await websocket.send_text("pong")

            except asyncio.TimeoutError:
                # 发送 ping 保持连接
                try:
                    await websocket.send_text("ping")
                except:
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket 客户端断开连接: task_id={task_id}")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}", exc_info=True)
    finally:
        await ws_manager.disconnect(websocket, task_id)


# ========== 工作流模板管理 ==========

@router.post(
    "/workflow/templates",
    response_model=WorkflowTemplateResponse,
    summary="创建工作流模板",
    description="创建新的工作流模板"
)
async def create_workflow_template(
    template: WorkflowTemplateCreate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_EXECUTE))
):
    """
    创建工作流模板

    Args:
        template: 工作流模板数据

    Returns:
        WorkflowTemplateResponse: 创建的模板
    """
    try:
        with get_crawler_db().get_session() as session:
            workflow_manager = WorkflowManager(session)

            # 转换为字典格式保存
            workflow_def = template.workflow_def.dict()

            template_id = workflow_manager.save_workflow_template(
                name=template.name,
                description=template.description,
                workflow_def=workflow_def,
                category=template.category
            )

            if not template_id:
                raise HTTPException(status_code=500, detail="创建工作流模板失败")

            # 获取创建的模板
            created_template = session.query(CrawlerWorkflowTemplate).filter(
                CrawlerWorkflowTemplate.id == template_id
            ).first()

        return _build_template_response(created_template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建工作流模板失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get(
    "/workflow/templates",
    response_model=PaginatedResponse,
    summary="查询工作流模板列表",
    description="查询工作流模板列表（支持分页和筛选）"
)
async def list_workflow_templates(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_READ))
):
    """
    查询工作流模板列表

    Returns:
        PaginatedResponse: 模板列表
    """
    try:
        with get_crawler_db().get_session() as session:
            query = session.query(CrawlerWorkflowTemplate)

            # 筛选条件
            if category:
                query = query.filter(CrawlerWorkflowTemplate.category == category)
            if is_active is not None:
                query = query.filter(CrawlerWorkflowTemplate.is_active == is_active)
            if search:
                query = query.filter(
                    CrawlerWorkflowTemplate.name.contains(search) |
                    CrawlerWorkflowTemplate.description.contains(search)
                )

            # 计算总数
            total = query.count()

            # 分页
            templates = query.order_by(CrawlerWorkflowTemplate.created_at.desc()).offset(
                (page - 1) * page_size
            ).limit(page_size).all()

            return PaginatedResponse(
                items=[_build_template_response(t) for t in templates],
                total=total,
                page=page,
                size=page_size,
                pages=(total + page_size - 1) // page_size
            )

    except Exception as e:
        logger.error(f"查询工作流模板失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get(
    "/workflow/templates/{template_id}",
    response_model=WorkflowTemplateResponse,
    summary="获取工作流模板详情",
    description="获取指定工作流模板的详细信息"
)
async def get_workflow_template(
    template_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_READ))
):
    """
    获取工作流模板详情

    Args:
        template_id: 模板ID

    Returns:
        WorkflowTemplateResponse: 模板详情
    """
    try:
        db = get_db()
        template = db.query(CrawlerWorkflowTemplate).filter(
            CrawlerWorkflowTemplate.id == template_id
        ).first()

        if not template:
            raise HTTPException(status_code=404, detail="工作流模板不存在")

        return _build_template_response(template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工作流模板失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.put(
    "/workflow/templates/{template_id}",
    response_model=WorkflowTemplateResponse,
    summary="更新工作流模板",
    description="更新指定工作流模板"
)
async def update_workflow_template(
    template_id: int,
    update_data: WorkflowTemplateUpdate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_EXECUTE))
):
    """
    更新工作流模板

    Args:
        template_id: 模板ID
        update_data: 更新数据

    Returns:
        WorkflowTemplateResponse: 更新后的模板
    """
    try:
        db = get_db()
        template = db.query(CrawlerWorkflowTemplate).filter(
            CrawlerWorkflowTemplate.id == template_id
        ).first()

        if not template:
            raise HTTPException(status_code=404, detail="工作流模板不存在")

        # 更新字段
        update_dict = update_data.dict(exclude_unset=True)
        if 'workflow_def' in update_dict:
            update_dict['template_json'] = json.dumps(update_dict.pop('workflow_def'))

        for field, value in update_dict.items():
            setattr(template, field, value)

        template.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(template)

        return _build_template_response(template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新工作流模板失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete(
    "/workflow/templates/{template_id}",
    response_model=ApiResponse,
    summary="删除工作流模板",
    description="删除指定的工作流模板"
)
async def delete_workflow_template(
    template_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_DELETE))
):
    """
    删除工作流模板

    Args:
        template_id: 模板ID

    Returns:
        ApiResponse: 删除结果
    """
    try:
        db = get_db()
        template = db.query(CrawlerWorkflowTemplate).filter(
            CrawlerWorkflowTemplate.id == template_id
        ).first()

        if not template:
            raise HTTPException(status_code=404, detail="工作流模板不存在")

        # 软删除 - 设置为非活跃状态
        template.is_active = False
        template.updated_at = datetime.utcnow()

        db.commit()

        return ApiResponse(message="工作流模板已删除")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除工作流模板失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


# ========== 工作流执行管理 ==========

@router.post(
    "/workflow/execute",
    response_model=WorkflowExecutionResponse,
    summary="执行工作流",
    description="基于模板创建并执行工作流实例"
)
async def execute_workflow(
    request: WorkflowExecutionRequest,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_EXECUTE))
):
    """
    执行工作流

    Args:
        request: 执行请求

    Returns:
        WorkflowExecutionResponse: 执行结果
    """
    try:
        db = get_db()
        workflow_manager = WorkflowManager(db)

        # 生成工作流实例ID
        workflow_id = str(uuid.uuid4())

        # 执行工作流
        success = workflow_manager.execute_workflow_from_template(
            template_id=request.template_id,
            workflow_id=workflow_id,
            params=request.params,
            priority=request.priority,
            max_retries=request.max_retries,
            timeout_seconds=request.timeout_seconds
        )

        if not success:
            raise HTTPException(status_code=500, detail="工作流执行失败")

        # 获取执行状态
        tasks = db.query(CrawlerTask).filter(
            CrawlerTask.workflow_id == workflow_id
        ).all()

        task_count = len(tasks)
        completed_count = len([t for t in tasks if t.status == TaskStatus.SUCCESS])
        failed_count = len([t for t in tasks if t.status == TaskStatus.FAILED])
        running_count = len([t for t in tasks if t.status == TaskStatus.RUNNING])
        pending_count = len([t for t in tasks if t.status == TaskStatus.PENDING])

        # 获取模板信息
        template = db.query(CrawlerWorkflowTemplate).filter(
            CrawlerWorkflowTemplate.id == request.template_id
        ).first()

        return WorkflowExecutionResponse(
            workflow_id=workflow_id,
            template_id=request.template_id,
            status=TaskStatus.RUNNING,
            created_at=datetime.utcnow(),
            task_count=task_count,
            completed_count=completed_count,
            failed_count=failed_count,
            running_count=running_count,
            pending_count=pending_count
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行工作流失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.get(
    "/workflow/{workflow_id}/status",
    response_model=WorkflowStatusResponse,
    summary="获取工作流状态",
    description="获取指定工作流实例的执行状态"
)
async def get_workflow_status(
    workflow_id: str,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_READ))
):
    """
    获取工作流状态

    Args:
        workflow_id: 工作流ID

    Returns:
        WorkflowStatusResponse: 工作流状态
    """
    try:
        db = get_db()

        # 获取工作流任务
        tasks = db.query(CrawlerTask).filter(
            CrawlerTask.workflow_id == workflow_id
        ).order_by(CrawlerTask.step_order).all()

        if not tasks:
            raise HTTPException(status_code=404, detail="工作流不存在")

        # 获取模板信息
        template_id = tasks[0].workflow_id
        template_name = tasks[0].workflow_name or "未知工作流"

        # 计算整体状态
        statuses = [t.status for t in tasks]
        if TaskStatus.FAILED in statuses:
            status = TaskStatus.FAILED
        elif TaskStatus.RUNNING in statuses:
            status = TaskStatus.RUNNING
        elif TaskStatus.PENDING in statuses:
            status = TaskStatus.RUNNING
        else:
            status = TaskStatus.SUCCESS

        # 构建任务状态列表
        task_statuses = []
        for task in tasks:
            step_config = json.loads(task.step_config) if task.step_config else {}
            task_statuses.append(WorkflowTaskStatus(
                task_id=task.id,
                step_id=step_config.get('step_id', f"step_{task.step_order}"),
                step_name=task.task_name,
                status=task.status,
                created_at=task.created_at,
                start_time=task.start_time,
                end_time=task.end_time,
                total_items=task.total_items,
                success_items=task.success_items,
                failed_items=task.failed_items,
                error_message=task.error_message
            ))

        # 计算进度
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status in [TaskStatus.SUCCESS, TaskStatus.FAILED]])
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return WorkflowStatusResponse(
            workflow_id=workflow_id,
            template_name=template_name,
            status=status,
            created_at=tasks[0].created_at,
            started_at=min(t.start_time for t in tasks if t.start_time),
            completed_at=max(t.end_time for t in tasks if t.end_time),
            tasks=task_statuses,
            progress_percentage=progress
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工作流状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post(
    "/workflow/{workflow_id}/pause",
    response_model=ApiResponse,
    summary="暂停工作流",
    description="暂停正在执行的工作流"
)
async def pause_workflow(
    workflow_id: str,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_EXECUTE))
):
    """暂停工作流"""
    # TODO: 实现工作流暂停逻辑
    return ApiResponse(message="工作流暂停功能开发中")


@router.post(
    "/workflow/{workflow_id}/resume",
    response_model=ApiResponse,
    summary="恢复工作流",
    description="恢复已暂停的工作流"
)
async def resume_workflow(
    workflow_id: str,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_EXECUTE))
):
    """恢复工作流"""
    # TODO: 实现工作流恢复逻辑
    return ApiResponse(message="工作流恢复功能开发中")


@router.post(
    "/workflow/{workflow_id}/cancel",
    response_model=ApiResponse,
    summary="取消工作流",
    description="取消正在执行的工作流"
)
async def cancel_workflow(
    workflow_id: str,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_DELETE))
):
    """取消工作流"""
    try:
        db = get_db()

        # 取消所有未开始的任务
        tasks = db.query(CrawlerTask).filter(
            CrawlerTask.workflow_id == workflow_id,
            CrawlerTask.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING])
        ).all()

        for task in tasks:
            task.status = TaskStatus.FAILED
            task.error_message = "用户取消"
            task.end_time = datetime.utcnow()

        db.commit()

        return ApiResponse(message="工作流已取消")

    except Exception as e:
        logger.error(f"取消工作流失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"取消失败: {str(e)}")


# ========== 定时工作流管理 ==========

@router.post(
    "/workflow/schedules",
    response_model=ScheduleResponse,
    summary="创建定时调度",
    description="创建工作流的定时调度"
)
async def create_schedule(
    schedule: ScheduleCreate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_EXECUTE))
):
    """
    创建定时调度

    Args:
        schedule: 调度配置

    Returns:
        ScheduleResponse: 创建的调度
    """
    try:
        db = get_db()

        # 验证模板是否存在
        template = db.query(CrawlerWorkflowTemplate).filter(
            CrawlerWorkflowTemplate.id == schedule.template_id
        ).first()

        if not template:
            raise HTTPException(status_code=404, detail="工作流模板不存在")

        # 创建调度记录
        db_schedule = CrawlerSchedule(
            name=schedule.name,
            template_id=schedule.template_id,
            cron_expression=schedule.cron_expression,
            timezone=schedule.timezone,
            params=json.dumps(schedule.params),
            is_enabled=schedule.is_enabled,
            max_instances=schedule.max_instances,
            timeout_seconds=schedule.timeout_seconds,
            created_by=current_user.user_id
        )

        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)

        # 如果启用，添加到调度器
        if schedule.is_enabled:
            await _add_schedule_to_scheduler(db_schedule, template)

        return _build_schedule_response(db_schedule)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建定时调度失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get(
    "/workflow/schedules",
    response_model=PaginatedResponse,
    summary="查询调度列表",
    description="查询定时调度列表"
)
async def list_schedules(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    template_id: Optional[int] = Query(None, description="模板ID筛选"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_READ))
):
    """
    查询调度列表

    Returns:
        PaginatedResponse: 调度列表
    """
    try:
        db = get_db()
        query = db.query(CrawlerSchedule)

        # 筛选条件
        if template_id:
            query = query.filter(CrawlerSchedule.template_id == template_id)
        if is_enabled is not None:
            query = query.filter(CrawlerSchedule.is_enabled == is_enabled)

        # 计算总数
        total = query.count()

        # 分页
        schedules = query.order_by(CrawlerSchedule.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return PaginatedResponse(
            items=[_build_schedule_response(s) for s in schedules],
            total=total,
            page=page,
            size=page_size,
            pages=(total + page_size - 1) // page_size
        )

    except Exception as e:
        logger.error(f"查询调度列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get(
    "/workflow/schedules/{schedule_id}",
    response_model=ScheduleResponse,
    summary="获取调度详情",
    description="获取指定调度的详细信息"
)
async def get_schedule(
    schedule_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_READ))
):
    """
    获取调度详情

    Args:
        schedule_id: 调度ID

    Returns:
        ScheduleResponse: 调度详情
    """
    try:
        db = get_db()
        schedule = db.query(CrawlerSchedule).filter(
            CrawlerSchedule.id == schedule_id
        ).first()

        if not schedule:
            raise HTTPException(status_code=404, detail="调度不存在")

        return _build_schedule_response(schedule)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取调度详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.put(
    "/workflow/schedules/{schedule_id}",
    response_model=ScheduleResponse,
    summary="更新调度",
    description="更新指定的定时调度"
)
async def update_schedule(
    schedule_id: int,
    update_data: ScheduleUpdate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_EXECUTE))
):
    """
    更新调度

    Args:
        schedule_id: 调度ID
        update_data: 更新数据

    Returns:
        ScheduleResponse: 更新后的调度
    """
    try:
        db = get_db()
        schedule = db.query(CrawlerSchedule).filter(
            CrawlerSchedule.id == schedule_id
        ).first()

        if not schedule:
            raise HTTPException(status_code=404, detail="调度不存在")

        # 先从调度器中移除旧任务
        await _remove_schedule_from_scheduler(schedule)

        # 更新字段
        update_dict = update_data.dict(exclude_unset=True)
        if 'params' in update_dict:
            update_dict['params'] = json.dumps(update_dict['params'])

        for field, value in update_dict.items():
            setattr(schedule, field, value)

        schedule.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(schedule)

        # 如果启用，重新添加到调度器
        if schedule.is_enabled:
            template = db.query(CrawlerWorkflowTemplate).filter(
                CrawlerWorkflowTemplate.id == schedule.template_id
            ).first()
            await _add_schedule_to_scheduler(schedule, template)

        return _build_schedule_response(schedule)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新调度失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete(
    "/workflow/schedules/{schedule_id}",
    response_model=ApiResponse,
    summary="删除调度",
    description="删除指定的定时调度"
)
async def delete_schedule(
    schedule_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_DELETE))
):
    """
    删除调度

    Args:
        schedule_id: 调度ID

    Returns:
        ApiResponse: 删除结果
    """
    try:
        db = get_db()
        schedule = db.query(CrawlerSchedule).filter(
            CrawlerSchedule.id == schedule_id
        ).first()

        if not schedule:
            raise HTTPException(status_code=404, detail="调度不存在")

        # 从调度器中移除
        await _remove_schedule_from_scheduler(schedule)

        # 删除记录
        db.delete(schedule)
        db.commit()

        return ApiResponse(message="调度已删除")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除调度失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post(
    "/workflow/schedules/{schedule_id}/enable",
    response_model=ApiResponse,
    summary="启用调度",
    description="启用指定的定时调度"
)
async def enable_schedule(
    schedule_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_EXECUTE))
):
    """启用调度"""
    try:
        db = get_db()
        schedule = db.query(CrawlerSchedule).filter(
            CrawlerSchedule.id == schedule_id
        ).first()

        if not schedule:
            raise HTTPException(status_code=404, detail="调度不存在")

        if not schedule.is_enabled:
            schedule.is_enabled = True
            schedule.updated_at = datetime.utcnow()
            db.commit()

            # 添加到调度器
            template = db.query(CrawlerWorkflowTemplate).filter(
                CrawlerWorkflowTemplate.id == schedule.template_id
            ).first()
            await _add_schedule_to_scheduler(schedule, template)

        return ApiResponse(message="调度已启用")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启用调度失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"启用失败: {str(e)}")


@router.post(
    "/workflow/schedules/{schedule_id}/disable",
    response_model=ApiResponse,
    summary="禁用调度",
    description="禁用指定的定时调度"
)
async def disable_schedule(
    schedule_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_EXECUTE))
):
    """禁用调度"""
    try:
        db = get_db()
        schedule = db.query(CrawlerSchedule).filter(
            CrawlerSchedule.id == schedule_id
        ).first()

        if not schedule:
            raise HTTPException(status_code=404, detail="调度不存在")

        if schedule.is_enabled:
            schedule.is_enabled = False
            schedule.updated_at = datetime.utcnow()
            db.commit()

            # 从调度器中移除
            await _remove_schedule_from_scheduler(schedule)

        return ApiResponse(message="调度已禁用")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"禁用调度失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"禁用失败: {str(e)}")


@router.post(
    "/workflow/schedules/preview",
    response_model=SchedulePreviewResponse,
    summary="预览调度时间",
    description="预览Cron表达式的执行时间"
)
async def preview_schedule(
    request: SchedulePreviewRequest,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_READ))
):
    """
    预览调度时间

    Args:
        request: 预览请求

    Returns:
        SchedulePreviewResponse: 预览结果
    """
    try:
        # 创建cron迭代器
        cron = croniter(request.cron_expression)

        # 设置预览范围
        start_time = request.start_time or datetime.utcnow()
        end_time = request.end_time or (start_time + timedelta(days=30))

        # 获取未来执行时间
        next_runs = []
        current_time = start_time
        while len(next_runs) < 10 and current_time < end_time:
            current_time = cron.get_next(datetime)
            if current_time < end_time:
                next_runs.append(current_time)

        return SchedulePreviewResponse(
            cron_expression=request.cron_expression,
            timezone=request.timezone,
            next_runs=next_runs,
            total_count=len(next_runs),
            preview_range={
                "start": start_time,
                "end": end_time
            }
        )

    except Exception as e:
        logger.error(f"预览调度失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")


@router.post(
    "/workflow/schedules/cron/generate",
    response_model=CronExpressionResponse,
    summary="生成Cron表达式",
    description="根据频率设置生成Cron表达式"
)
async def generate_cron_expression(
    request: CronExpressionRequest,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_READ))
):
    """
    生成Cron表达式

    Args:
        request: 生成请求

    Returns:
        CronExpressionResponse: 生成的表达式
    """
    try:
        # 根据频率生成Cron表达式
        if request.frequency == "minutely":
            cron_expr = f"*/{request.interval} * * * *"
            description = f"每{request.interval}分钟执行一次"
        elif request.frequency == "hourly":
            cron_expr = f"0 */{request.interval} * * *"
            description = f"每{request.interval}小时执行一次"
        elif request.frequency == "daily":
            if request.specific_times:
                minute = request.specific_times[0].split(":")[1] if ":" in request.specific_times[0] else "0"
                hour = request.specific_times[0].split(":")[0] if ":" in request.specific_times[0] else "0"
                cron_expr = f"{minute} {hour} */{request.interval} * *"
            else:
                cron_expr = f"0 0 */{request.interval} * *"
            description = f"每{request.interval}天执行一次"
        elif request.frequency == "weekly":
            if request.specific_times:
                minute = request.specific_times[0].split(":")[1] if ":" in request.specific_times[0] else "0"
                hour = request.specific_times[0].split(":")[0] if ":" in request.specific_times[0] else "0"
                day_of_week = request.days_of_week[0] if request.days_of_week else "1"
                cron_expr = f"{minute} {hour} * * {day_of_week}"
            else:
                cron_expr = f"0 0 * * 1"
            description = f"每周执行一次"
        elif request.frequency == "monthly":
            if request.specific_times:
                minute = request.specific_times[0].split(":")[1] if ":" in request.specific_times[0] else "0"
                hour = request.specific_times[0].split(":")[0] if ":" in request.specific_times[0] else "0"
                day_of_month = request.days_of_month[0] if request.days_of_month else "1"
                cron_expr = f"{minute} {hour} {day_of_month} */{request.interval} *"
            else:
                cron_expr = f"0 0 1 */{request.interval} *"
            description = f"每{request.interval}个月执行一次"
        else:
            cron_expr = "0 0 * * *"
            description = "自定义表达式"

        # 获取未来执行时间
        cron = croniter(cron_expr)
        next_runs = [cron.get_next(datetime) for _ in range(5)]

        return CronExpressionResponse(
            cron_expression=cron_expr,
            description=description,
            next_runs=next_runs,
            timezone=request.timezone
        )

    except Exception as e:
        logger.error(f"生成Cron表达式失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get(
    "/workflow/schedules/status",
    summary="获取调度器状态",
    description="获取工作流调度器的运行状态"
)
async def get_scheduler_status(
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_READ))
):
    """获取调度器状态"""
    try:
        from apps.api.main import workflow_scheduler

        if workflow_scheduler is None:
            raise HTTPException(status_code=503, detail="调度器未初始化")

        status = workflow_scheduler.get_schedule_status()
        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取调度器状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


# ========== 辅助函数 ==========

def _build_task_response(task: CrawlerTask) -> CrawlerTaskResponse:
    """构造任务响应对象"""
    return CrawlerTaskResponse(
        task_id=task.id,  # 前端期望 task_id 而不是 id
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


def _build_task_response_from_dict(task_dict: dict) -> CrawlerTaskResponse:
    """从字典构造任务响应对象"""
    return CrawlerTaskResponse(
        task_id=task_dict.get('task_id'),  # 使用 task_id（来自 to_dict()）
        task_type=task_dict.get('task_type'),
        task_name=task_dict.get('task_name'),
        status=task_dict.get('status'),
        start_time=task_dict.get('start_time'),
        end_time=task_dict.get('end_time'),
        total_items=task_dict.get('total_items', 0),
        success_items=task_dict.get('success_items', 0),
        failed_items=task_dict.get('failed_items', 0),
        error_message=task_dict.get('error_message'),
        config=task_dict.get('config'),
        result_summary=task_dict.get('result_summary'),
        created_at=task_dict.get('created_at'),
        updated_at=task_dict.get('updated_at')
    )


def _build_template_response(template: CrawlerWorkflowTemplate) -> WorkflowTemplateResponse:
    """构造模板响应对象"""
    workflow_def = json.loads(template.template_json) if template.template_json else {}
    return WorkflowTemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        category=template.category or 'custom',
        version=workflow_def.get('version', '1.0'),
        tags=workflow_def.get('tags', []),
        workflow_def=workflow_def,
        created_by=str(template.created_by) if template.created_by else None,
        created_at=template.created_at,
        updated_at=template.updated_at,
        is_active=not template.is_system,  # 非系统模板默认活跃
        usage_count=template.usage_count
    )


def _build_schedule_response(schedule: CrawlerSchedule) -> ScheduleResponse:
    """构造调度响应对象"""
    return ScheduleResponse(
        id=schedule.id,
        name=schedule.name,
        template_id=schedule.template_id,
        cron_expression=schedule.cron_expression,
        timezone=schedule.timezone,
        params=json.loads(schedule.params) if schedule.params else {},
        is_enabled=schedule.is_enabled,
        max_instances=schedule.max_instances,
        timeout_seconds=schedule.timeout_seconds,
        description=schedule.description,
        created_by=schedule.created_by,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
        last_run_at=schedule.last_run_at,
        next_run_at=schedule.next_run_at,
        run_count=schedule.run_count,
        success_count=schedule.success_count,
        failure_count=schedule.failure_count
    )


async def _add_schedule_to_scheduler(schedule: CrawlerSchedule, template: CrawlerWorkflowTemplate):
    """添加调度到APScheduler"""
    try:
        # 获取全局调度器实例
        from apps.api.main import scheduler

        if scheduler is None:
            logger.error("调度器未初始化")
            return

        job_id = f"workflow_schedule_{schedule.id}"

        # 定义任务函数
        async def run_scheduled_workflow():
            try:
                db = get_db()
                workflow_manager = WorkflowManager(db)

                # 生成工作流实例ID
                workflow_id = str(uuid.uuid4())

                # 获取调度参数
                params = json.loads(schedule.params) if schedule.params else {}

                # 执行工作流
                success = workflow_manager.execute_workflow_from_template(
                    template_id=schedule.template_id,
                    workflow_id=workflow_id,
                    params=params,
                    priority=0,  # 调度任务使用默认优先级
                    max_retries=3,
                    timeout_seconds=schedule.timeout_seconds
                )

                if success:
                    # 更新成功统计
                    schedule.run_count += 1
                    schedule.success_count += 1
                    logger.info(f"定时工作流执行成功: schedule_id={schedule.id}, workflow_id={workflow_id}")
                else:
                    # 更新失败统计
                    schedule.run_count += 1
                    schedule.failure_count += 1
                    logger.error(f"定时工作流执行失败: schedule_id={schedule.id}")

                # 更新最后运行时间
                schedule.last_run_at = datetime.utcnow()
                db.commit()

            except Exception as e:
                logger.error(f"定时工作流执行异常: schedule_id={schedule.id}, error={e}")
                # 更新失败统计
                db = get_db()
                schedule.run_count += 1
                schedule.failure_count += 1
                schedule.last_run_at = datetime.utcnow()
                db.commit()

        # 添加到调度器
        scheduler.add_job(
            run_scheduled_workflow,
            'cron',
            id=job_id,
            **_parse_cron_expression(schedule.cron_expression),
            timezone=schedule.timezone,
            max_instances=schedule.max_instances,
            misfire_grace_time=300  # 5分钟宽限期
        )

        logger.info(f"调度已添加到调度器: {job_id}, cron={schedule.cron_expression}")

    except Exception as e:
        logger.error(f"添加调度到调度器失败: {e}")


async def _remove_schedule_from_scheduler(schedule: CrawlerSchedule):
    """从调度器中移除调度"""
    try:
        # 获取全局调度器实例
        from apps.api.main import scheduler

        if scheduler is None:
            return

        job_id = f"workflow_schedule_{schedule.id}"

        # 移除任务
        scheduler.remove_job(job_id)

        logger.info(f"调度已从调度器移除: {job_id}")

    except Exception as e:
        logger.error(f"从调度器移除调度失败: {e}")


def _parse_cron_expression(cron_expr: str) -> dict:
    """解析Cron表达式为APScheduler参数"""
    parts = cron_expr.split()
    if len(parts) != 5:
        raise ValueError("无效的Cron表达式")

    minute, hour, day, month, day_of_week = parts

    return {
        'minute': minute,
        'hour': hour,
        'day': day,
        'month': month,
        'day_of_week': day_of_week
    }
