"""
数据处理工作流 API 路由

整合 OCR Worker 和待审核装备的统一管理界面
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy import func, and_, or_

from apps.api.orm.session import get_db_session
from packages.agents.equipment_import.models.pending import PendingEquipment
from apps.api.schemas.data_workflow import (
    WorkflowStats,
    WorkerInfo,
    WorkerListResponse,
    OCRTaskItem,
    OCRTaskListResponse,
    ReviewTaskItem,
    ReviewTaskListResponse,
    ReviewAction,
    OperationResponse,
)
from apps.api.auth.dependencies import require_permission, CurrentUser
from apps.api.auth.permissions import PermissionEnum

# 导入现有的 OCR Worker API Keys
from apps.api.routes.ocr_worker import OCR_WORKER_API_KEYS

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== 工作流统计 ==========

@router.get(
    "/stats",
    response_model=WorkflowStats,
    summary="工作流统计",
    description="获取数据处理工作流各阶段的统计数据",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_READ))]
)
async def get_workflow_stats():
    """获取工作流统计数据"""
    with get_db_session() as session:
        # OCR 状态统计
        ocr_stats = session.query(
            PendingEquipment.ocr_status,
            func.count(PendingEquipment.id)
        ).group_by(PendingEquipment.ocr_status).all()

        ocr_status_map = {status: count for status, count in ocr_stats}

        # 审核状态统计 (仅统计 OCR 已完成的)
        review_stats = session.query(
            PendingEquipment.status,
            func.count(PendingEquipment.id)
        ).filter(
            PendingEquipment.ocr_status == "completed"
        ).group_by(PendingEquipment.status).all()

        review_status_map = {status: count for status, count in review_stats}

        # 今日处理量
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_processed = session.query(func.count(PendingEquipment.id)).filter(
            PendingEquipment.ocr_completed_at >= today_start,
            PendingEquipment.ocr_status == "completed"
        ).scalar() or 0

        # 平均处理时间
        avg_time_result = session.query(
            func.avg(PendingEquipment.ocr_processing_time_ms)
        ).filter(
            PendingEquipment.ocr_status == "completed",
            PendingEquipment.ocr_processing_time_ms.isnot(None)
        ).scalar()
        avg_processing_time_ms = int(avg_time_result) if avg_time_result else 0

        # 成功率
        total_finished = (
            ocr_status_map.get("completed", 0) +
            ocr_status_map.get("failed", 0)
        )
        success_rate = (
            ocr_status_map.get("completed", 0) / total_finished
            if total_finished > 0 else 0.0
        )

        # 爬虫待处理 (根据 CrawlerTask 表，暂用占位)
        crawl_pending = 0  # TODO: 从 CrawlerTask 表获取

        return WorkflowStats(
            crawl_pending=crawl_pending,
            ocr_pending=ocr_status_map.get("pending", 0),
            ocr_processing=ocr_status_map.get("processing", 0),
            ocr_completed=ocr_status_map.get("completed", 0),
            ocr_failed=ocr_status_map.get("failed", 0),
            ocr_skipped=ocr_status_map.get("skipped", 0),
            review_pending=review_status_map.get("pending", 0),
            review_approved=review_status_map.get("approved", 0),
            review_rejected=review_status_map.get("rejected", 0),
            today_processed=today_processed,
            avg_processing_time_ms=avg_processing_time_ms,
            success_rate=round(success_rate, 3),
        )


# ========== Worker 监控 ==========

@router.get(
    "/workers",
    response_model=WorkerListResponse,
    summary="Worker 列表",
    description="获取已注册的 OCR Worker 状态列表",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_READ))]
)
async def get_workers():
    """获取 Worker 状态列表"""
    workers = []
    now = datetime.utcnow()
    active_threshold = now - timedelta(minutes=5)  # 5分钟内有活动视为活跃

    with get_db_session() as session:
        # 获取每个 Worker 的当前任务和统计
        for worker_id in OCR_WORKER_API_KEYS.keys():
            # 查询当前正在处理的任务
            current_task = session.query(PendingEquipment).filter(
                PendingEquipment.ocr_worker_id == worker_id,
                PendingEquipment.ocr_status == "processing"
            ).first()

            # 查询最近完成的任务以获取最后活动时间
            last_task = session.query(PendingEquipment).filter(
                PendingEquipment.ocr_worker_id == worker_id
            ).order_by(PendingEquipment.ocr_completed_at.desc()).first()

            # 统计已完成任务数
            tasks_completed = session.query(func.count(PendingEquipment.id)).filter(
                PendingEquipment.ocr_worker_id == worker_id,
                PendingEquipment.ocr_status == "completed"
            ).scalar() or 0

            # 判断是否活跃
            last_heartbeat = None
            if last_task and last_task.ocr_completed_at:
                last_heartbeat = last_task.ocr_completed_at
            elif current_task and current_task.ocr_started_at:
                last_heartbeat = current_task.ocr_started_at

            is_active = (
                current_task is not None or
                (last_heartbeat and last_heartbeat > active_threshold)
            )

            workers.append(WorkerInfo(
                id=worker_id,
                status="active" if is_active else "inactive",
                current_task=current_task.id if current_task else None,
                last_heartbeat=last_heartbeat,
                ocr_provider=last_task.ocr_provider if last_task else None,
                tasks_completed=tasks_completed,
            ))

    total_active = sum(1 for w in workers if w.status == "active")

    return WorkerListResponse(
        workers=workers,
        total_active=total_active,
    )


# ========== OCR 任务管理 ==========

@router.get(
    "/ocr/tasks",
    response_model=OCRTaskListResponse,
    summary="OCR 任务列表",
    description="获取 OCR 任务列表，支持分页和状态筛选",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_READ))]
)
async def list_ocr_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    ocr_status: Optional[str] = Query(None, description="OCR 状态筛选"),
    ocr_priority: Optional[int] = Query(None, description="优先级筛选"),
):
    """获取 OCR 任务列表"""
    with get_db_session() as session:
        query = session.query(PendingEquipment)

        if ocr_status:
            query = query.filter(PendingEquipment.ocr_status == ocr_status)

        if ocr_priority is not None:
            query = query.filter(PendingEquipment.ocr_priority == ocr_priority)

        # 获取总数
        total = query.count()

        # 分页，按优先级和创建时间排序
        offset = (page - 1) * page_size
        items = query.order_by(
            PendingEquipment.ocr_priority.desc(),
            PendingEquipment.created_at.desc()
        ).offset(offset).limit(page_size).all()

        tasks = []
        for item in items:
            # 解析图片数量
            images_count = 0
            if item.images:
                try:
                    data = json.loads(item.images)
                    if isinstance(data, dict) and "paths" in data:
                        images_count = len(data["paths"])
                    elif isinstance(data, list):
                        images_count = len(data)
                except json.JSONDecodeError:
                    pass

            tasks.append(OCRTaskItem(
                pending_id=item.id,
                brand_name=item.brand_name,
                product_name=item.product_name,
                images_count=images_count,
                ocr_status=item.ocr_status,
                ocr_priority=item.ocr_priority,
                ocr_worker_id=item.ocr_worker_id,
                ocr_started_at=item.ocr_started_at,
                ocr_processing_time_ms=item.ocr_processing_time_ms,
                ocr_retry_count=item.ocr_retry_count,
                ocr_error_message=item.ocr_error_message,
                ocr_provider=item.ocr_provider,
                created_at=item.created_at,
            ))

        return OCRTaskListResponse(
            items=tasks,
            total=total,
            page=page,
            page_size=page_size,
        )


@router.post(
    "/ocr/tasks/{pending_id}/retry",
    response_model=OperationResponse,
    summary="重试 OCR 任务",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))]
)
async def retry_ocr_task(
    pending_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))
):
    """重试失败的 OCR 任务"""
    with get_db_session() as session:
        item = session.query(PendingEquipment).filter(
            PendingEquipment.id == pending_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {pending_id} 不存在"
            )

        if item.ocr_status not in ["failed", "skipped", "completed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"只有失败、跳过或已完成的任务可以重试"
            )

        item.ocr_status = "pending"
        item.ocr_retry_count = 0
        item.ocr_error_message = None
        item.ocr_started_at = None
        item.ocr_completed_at = None
        item.ocr_worker_id = None

        session.commit()

        logger.info(f"管理员 {current_user.username} 重试任务 {pending_id}")

        return OperationResponse(
            success=True,
            message="任务已重新加入队列",
            affected_count=1,
        )


@router.post(
    "/ocr/tasks/batch-retry",
    response_model=OperationResponse,
    summary="批量重试 OCR 任务",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))]
)
async def batch_retry_ocr_tasks(
    pending_ids: list[int],
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))
):
    """批量重试 OCR 任务"""
    with get_db_session() as session:
        count = session.query(PendingEquipment).filter(
            PendingEquipment.id.in_(pending_ids),
            PendingEquipment.ocr_status.in_(["failed", "skipped", "completed"])
        ).update({
            "ocr_status": "pending",
            "ocr_retry_count": 0,
            "ocr_error_message": None,
            "ocr_started_at": None,
            "ocr_completed_at": None,
            "ocr_worker_id": None,
        }, synchronize_session=False)

        session.commit()

        logger.info(f"管理员 {current_user.username} 批量重试 {count} 个任务")

        return OperationResponse(
            success=True,
            message=f"成功重试 {count} 个任务",
            affected_count=count,
        )


@router.post(
    "/ocr/tasks/{pending_id}/skip",
    response_model=OperationResponse,
    summary="跳过 OCR 任务",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))]
)
async def skip_ocr_task(
    pending_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))
):
    """跳过 OCR 任务"""
    with get_db_session() as session:
        item = session.query(PendingEquipment).filter(
            PendingEquipment.id == pending_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {pending_id} 不存在"
            )

        item.ocr_status = "skipped"
        session.commit()

        logger.info(f"管理员 {current_user.username} 跳过任务 {pending_id}")

        return OperationResponse(
            success=True,
            message="任务已跳过",
            affected_count=1,
        )


@router.put(
    "/ocr/tasks/{pending_id}/priority",
    response_model=OperationResponse,
    summary="设置 OCR 任务优先级",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))]
)
async def set_ocr_task_priority(
    pending_id: int,
    priority: int = Query(..., ge=-10, le=10, description="优先级 (-10 到 10)"),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))
):
    """设置 OCR 任务优先级"""
    with get_db_session() as session:
        item = session.query(PendingEquipment).filter(
            PendingEquipment.id == pending_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {pending_id} 不存在"
            )

        item.ocr_priority = priority
        session.commit()

        logger.info(
            f"管理员 {current_user.username} 设置任务 {pending_id} 优先级为 {priority}"
        )

        return OperationResponse(
            success=True,
            message=f"优先级已更新为 {priority}",
            affected_count=1,
        )


@router.delete(
    "/ocr/tasks/{pending_id}",
    response_model=OperationResponse,
    summary="删除 OCR 任务",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_DELETE))]
)
async def delete_ocr_task(
    pending_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_DELETE))
):
    """删除 OCR 任务"""
    with get_db_session() as session:
        item = session.query(PendingEquipment).filter(
            PendingEquipment.id == pending_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {pending_id} 不存在"
            )

        if item.ocr_status == "processing":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法删除正在处理中的任务"
            )

        session.delete(item)
        session.commit()

        logger.info(f"管理员 {current_user.username} 删除任务 {pending_id}")

        return OperationResponse(
            success=True,
            message="任务已删除",
            affected_count=1,
        )


# ========== 审核任务管理 ==========

@router.get(
    "/review/tasks",
    response_model=ReviewTaskListResponse,
    summary="审核任务列表",
    description="获取待审核的装备数据列表",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_READ))]
)
async def list_review_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="审核状态筛选"),
    source_type: Optional[str] = Query(None, description="来源类型筛选"),
    equipment_type: Optional[str] = Query(None, description="装备类型筛选"),
):
    """获取审核任务列表"""
    with get_db_session() as session:
        # 仅查询 OCR 已完成的数据
        query = session.query(PendingEquipment).filter(
            PendingEquipment.ocr_status == "completed"
        )

        if status:
            query = query.filter(PendingEquipment.status == status)

        if source_type:
            query = query.filter(PendingEquipment.source_type == source_type)

        if equipment_type:
            query = query.filter(PendingEquipment.equipment_type == equipment_type)

        # 获取总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        items = query.order_by(
            PendingEquipment.created_at.desc()
        ).offset(offset).limit(page_size).all()

        tasks = []
        for item in items:
            # 解析图片数量
            images_count = 0
            if item.images:
                try:
                    data = json.loads(item.images)
                    if isinstance(data, dict) and "paths" in data:
                        images_count = len(data["paths"])
                    elif isinstance(data, list):
                        images_count = len(data)
                except json.JSONDecodeError:
                    pass

            # 解析提取的数据
            extracted_data = None
            if item.extracted_data:
                try:
                    extracted_data = json.loads(item.extracted_data)
                except json.JSONDecodeError:
                    pass

            tasks.append(ReviewTaskItem(
                id=item.id,
                status=item.status,
                source_type=item.source_type,
                equipment_type=item.equipment_type,
                brand_name=item.brand_name,
                product_name=item.product_name,
                confidence=item.confidence or 0.0,
                ocr_text=item.ocr_text,
                extracted_data=extracted_data,
                source_url=item.source_url,
                images_count=images_count,
                created_at=item.created_at,
                reviewed_at=item.reviewed_at,
                reviewed_by=item.reviewed_by,
                review_notes=item.review_notes,
            ))

        return ReviewTaskListResponse(
            items=tasks,
            total=total,
            page=page,
            page_size=page_size,
        )


@router.post(
    "/review/tasks/{task_id}/review",
    response_model=OperationResponse,
    summary="审核任务",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))]
)
async def review_task(
    task_id: int,
    action: ReviewAction,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))
):
    """审核任务（通过或拒绝）"""
    with get_db_session() as session:
        item = session.query(PendingEquipment).filter(
            PendingEquipment.id == task_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {task_id} 不存在"
            )

        if item.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"任务已被审核，当前状态: {item.status}"
            )

        if action.action not in ["approve", "reject"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="操作类型必须是 approve 或 reject"
            )

        item.status = "approved" if action.action == "approve" else "rejected"
        item.reviewed_at = datetime.utcnow()
        item.reviewed_by = current_user.id
        item.review_notes = action.review_notes

        session.commit()

        logger.info(
            f"管理员 {current_user.username} 审核任务 {task_id}: {action.action}"
        )

        return OperationResponse(
            success=True,
            message=f"任务已{'通过' if action.action == 'approve' else '拒绝'}",
            affected_count=1,
        )


@router.delete(
    "/review/tasks/{task_id}",
    response_model=OperationResponse,
    summary="删除审核任务",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_DELETE))]
)
async def delete_review_task(
    task_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_DELETE))
):
    """删除审核任务"""
    with get_db_session() as session:
        item = session.query(PendingEquipment).filter(
            PendingEquipment.id == task_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {task_id} 不存在"
            )

        session.delete(item)
        session.commit()

        logger.info(f"管理员 {current_user.username} 删除审核任务 {task_id}")

        return OperationResponse(
            success=True,
            message="任务已删除",
            affected_count=1,
        )
