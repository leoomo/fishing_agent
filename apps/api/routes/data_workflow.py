"""
数据处理工作流 API 路由

整合 OCR Worker 和待审核装备的统一管理界面
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query, status, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import FileResponse, Response
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
    ExtractResponse,
    ExtractedEquipmentItem,
    ExtractedDataUpdate,
    ImageInfo,
    TaskImagesResponse,
    OCRProgressReport,
    WorkerLogSubmit,
    ImportPreviewRow,
    ImportPreviewResponse,
    ImportResponse,
    ImportError,
    ImportTemplateInfo,
    ImportTemplateListResponse,
)
from apps.api.services.workflow_ws_manager import get_workflow_ws_manager

# 图片存储基础路径
IMAGES_BASE_PATH = Path(__file__).parents[3] / "shared" / "images"
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

            # 解析审核历史
            review_history = None
            if item.review_history:
                try:
                    review_history = json.loads(item.review_history)
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
                review_history=review_history,
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
    description="审核任务（通过或拒绝），支持重新审核已审核的任务",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))]
)
async def review_task(
    task_id: int,
    action: ReviewAction,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))
):
    """审核任务（通过或拒绝），支持重新审核"""
    with get_db_session() as session:
        item = session.query(PendingEquipment).filter(
            PendingEquipment.id == task_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {task_id} 不存在"
            )

        if action.action not in ["approve", "reject"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="操作类型必须是 approve 或 reject"
            )

        # 保存旧状态用于历史记录
        previous_status = item.status
        is_re_review = previous_status != "pending"

        # 构建历史记录条目
        history_entry = {
            "reviewed_by": current_user.user_id,
            "reviewed_at": datetime.utcnow().isoformat(),
            "action": action.action,
            "review_notes": action.review_notes,
            "previous_status": previous_status
        }

        # 追加到历史记录
        existing_history = []
        if item.review_history:
            try:
                existing_history = json.loads(item.review_history)
            except (json.JSONDecodeError, TypeError):
                existing_history = []
        existing_history.append(history_entry)
        item.review_history = json.dumps(existing_history, ensure_ascii=False)

        # 更新当前状态
        item.status = "approved" if action.action == "approve" else "rejected"
        item.reviewed_at = datetime.utcnow()
        item.reviewed_by = current_user.user_id
        item.review_notes = action.review_notes

        session.commit()

        action_text = "通过" if action.action == "approve" else "拒绝"
        if is_re_review:
            logger.info(
                f"管理员 {current_user.username} 重新审核任务 {task_id}: "
                f"{previous_status} -> {action.action}"
            )
            message = f"任务已重新审核: {action_text}"
        else:
            logger.info(
                f"管理员 {current_user.username} 审核任务 {task_id}: {action.action}"
            )
            message = f"任务已{action_text}"

        return OperationResponse(
            success=True,
            message=message,
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


# ========== 装备提取功能 ==========

@router.post(
    "/review/tasks/{task_id}/extract",
    response_model=ExtractResponse,
    summary="一键提取装备信息",
    description="从 OCR 识别的文本中提取装备详细信息",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))]
)
async def extract_equipment(
    task_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))
):
    """
    一键提取装备信息

    从 PendingEquipment 的 ocr_text 中提取装备详细信息，
    并保存到 extracted_data 字段。
    """
    with get_db_session() as session:
        item = session.query(PendingEquipment).filter(
            PendingEquipment.id == task_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {task_id} 不存在"
            )

        if not item.ocr_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该任务没有 OCR 识别文本"
            )

        try:
            # 导入并调用装备提取 Agent
            from packages.agents.equipment_import import EquipmentImportAgent

            agent = EquipmentImportAgent(
                model_provider="zhipu",
                enable_logging=True,
                enable_monitoring=False  # 不需要监控
            )

            # 使用批量提取（不保存）
            extracted_list = agent.batch_extract_only(
                text=item.ocr_text,
                source_type=item.source_type or "unknown"
            )

            if not extracted_list:
                return ExtractResponse(
                    success=False,
                    message="无法从文本中提取装备信息",
                    extracted_count=0,
                    items=[]
                )

            # 转换为响应格式
            items = []
            for extracted in extracted_list:
                items.append(ExtractedEquipmentItem(
                    equipment_type=extracted.equipment_type,
                    brand_name=extracted.brand_name,
                    model=extracted.model,
                    name=extracted.name,
                    price_min=extracted.price_min,
                    price_max=extracted.price_max,
                    description=extracted.description,
                    features=extracted.features,
                    target_fish=extracted.target_fish,
                    user_level=extracted.user_level,
                    specs=extracted.specs,
                    confidence=extracted.confidence,
                    extraction_notes=extracted.extraction_notes,
                ))

            # 保存提取结果到数据库
            extracted_data = [item.model_dump() for item in items]
            item.extracted_data = json.dumps(extracted_data, ensure_ascii=False)
            session.commit()

            logger.info(
                f"管理员 {current_user.username} 提取任务 {task_id} 的装备信息，"
                f"提取到 {len(items)} 个型号"
            )

            return ExtractResponse(
                success=True,
                message=f"成功提取 {len(items)} 个装备型号",
                extracted_count=len(items),
                items=items
            )

        except Exception as e:
            logger.error(f"提取装备信息失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"提取失败: {str(e)}"
            )


@router.put(
    "/review/tasks/{task_id}/extracted-data",
    response_model=OperationResponse,
    summary="保存编辑后的装备数据",
    description="保存人工编辑修正后的装备信息",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))]
)
async def save_extracted_data(
    task_id: int,
    data: ExtractedDataUpdate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))
):
    """
    保存编辑后的装备数据

    将人工修正后的装备信息保存到 extracted_data 字段。
    """
    with get_db_session() as session:
        item = session.query(PendingEquipment).filter(
            PendingEquipment.id == task_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {task_id} 不存在"
            )

        try:
            # 转换为 JSON 格式保存
            extracted_data = [item_data.model_dump() for item_data in data.items]
            item.extracted_data = json.dumps(extracted_data, ensure_ascii=False)
            session.commit()

            logger.info(
                f"管理员 {current_user.username} 保存任务 {task_id} 的装备数据，"
                f"共 {len(data.items)} 个型号"
            )

            return OperationResponse(
                success=True,
                message=f"成功保存 {len(data.items)} 个装备型号",
                affected_count=len(data.items)
            )

        except Exception as e:
            logger.error(f"保存装备数据失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"保存失败: {str(e)}"
            )


# ========== 图片访问功能 ==========

@router.get(
    "/review/tasks/{task_id}/images",
    response_model=TaskImagesResponse,
    summary="获取任务图片列表",
    description="获取审核任务关联的所有图片信息",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_READ))]
)
async def get_task_images(
    task_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_READ))
):
    """获取任务的图片列表"""
    with get_db_session() as session:
        item = session.query(PendingEquipment).filter(
            PendingEquipment.id == task_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {task_id} 不存在"
            )

        images: List[ImageInfo] = []

        if item.images:
            try:
                data = json.loads(item.images)

                # 新格式: {"paths": [...], "metadata": [...]}
                if isinstance(data, dict) and "paths" in data:
                    paths = data.get("paths", [])
                    metadata = data.get("metadata", [])

                    for idx, path in enumerate(paths):
                        filename = Path(path).name
                        meta = metadata[idx] if idx < len(metadata) else {}

                        images.append(ImageInfo(
                            filename=filename,
                            url=f"/api/v1/admin/workflow/images/{path}",
                            order=meta.get("order", idx + 1),
                            original_name=meta.get("original_name")
                        ))

                # 旧格式: [...]
                elif isinstance(data, list):
                    for idx, path in enumerate(data):
                        filename = Path(path).name
                        images.append(ImageInfo(
                            filename=filename,
                            url=f"/api/v1/admin/workflow/images/{path}",
                            order=idx + 1,
                            original_name=None
                        ))

            except json.JSONDecodeError:
                logger.warning(f"任务 {task_id} 的 images 字段解析失败")

        return TaskImagesResponse(
            task_id=task_id,
            images=images,
            total=len(images)
        )


@router.get(
    "/images/{path:path}",
    summary="获取图片文件",
    description="根据路径获取图片文件（支持通过 token 查询参数认证）",
)
async def get_image(
    path: str,
    token: str = Query(None, description="JWT token（用于 img 标签认证）")
):
    """
    获取图片文件

    由于浏览器的 <img> 标签无法携带 Authorization header，
    支持通过 query parameter 传递 token 进行认证。
    """
    # 验证 token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要提供 token 参数"
        )

    from ..auth.dependencies import verify_token
    try:
        verify_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Token 验证失败: {str(e)}"
        )
    # 安全检查：防止路径遍历攻击
    if ".." in path or path.startswith("/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的图片路径"
        )

    image_path = IMAGES_BASE_PATH / path

    if not image_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"图片不存在: {path}"
        )

    if not image_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="路径不是有效的文件"
        )

    # 检查文件扩展名
    suffix = image_path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }

    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(
        path=str(image_path),
        media_type=media_type,
        filename=image_path.name
    )


# ========== WebSocket 实时更新 ==========

async def get_current_stats() -> dict:
    """获取当前工作流统计数据（用于 WebSocket 初始状态）"""
    with get_db_session() as session:
        # OCR 状态统计
        ocr_stats = session.query(
            PendingEquipment.ocr_status,
            func.count(PendingEquipment.id)
        ).group_by(PendingEquipment.ocr_status).all()

        ocr_status_map = {status: count for status, count in ocr_stats}

        # 审核状态统计
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

        return {
            "crawl_pending": 0,
            "ocr_pending": ocr_status_map.get("pending", 0),
            "ocr_processing": ocr_status_map.get("processing", 0),
            "ocr_completed": ocr_status_map.get("completed", 0),
            "ocr_failed": ocr_status_map.get("failed", 0),
            "ocr_skipped": ocr_status_map.get("skipped", 0),
            "review_pending": review_status_map.get("pending", 0),
            "review_approved": review_status_map.get("approved", 0),
            "review_rejected": review_status_map.get("rejected", 0),
            "today_processed": today_processed,
            "avg_processing_time_ms": avg_processing_time_ms,
            "success_rate": round(success_rate, 3),
        }


async def get_current_workers() -> list[dict]:
    """获取当前 Worker 状态（用于 WebSocket 初始状态）"""
    workers = []
    now = datetime.utcnow()
    active_threshold = now - timedelta(minutes=5)

    with get_db_session() as session:
        for worker_id in OCR_WORKER_API_KEYS.keys():
            # 查询当前正在处理的任务
            current_task = session.query(PendingEquipment).filter(
                PendingEquipment.ocr_worker_id == worker_id,
                PendingEquipment.ocr_status == "processing"
            ).first()

            # 查询最近完成的任务
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

            workers.append({
                "id": worker_id,
                "status": "active" if is_active else "inactive",
                "current_task": current_task.id if current_task else None,
                "last_heartbeat": last_heartbeat.isoformat() if last_heartbeat else None,
                "ocr_provider": last_task.ocr_provider if last_task else None,
                "tasks_completed": tasks_completed,
            })

    return workers


@router.websocket("/ws/workflow")
async def websocket_workflow_status(websocket: WebSocket):
    """
    工作流全局状态 WebSocket

    功能：
    - 连接时发送初始状态（stats, workers）
    - 实时推送 stats/workers/tasks 更新

    客户端消息：
    - {"type": "ping"} -> 心跳响应
    - {"type": "subscribe_task", "pending_id": 123} -> 订阅单任务进度
    - {"type": "unsubscribe_task", "pending_id": 123} -> 取消订阅
    - {"type": "subscribe_logs"} -> 订阅日志流
    """
    ws_manager = get_workflow_ws_manager()

    try:
        await ws_manager.connect_global(websocket)

        # 发送初始状态
        stats = await get_current_stats()
        workers = await get_current_workers()
        await ws_manager.send_init_state(websocket, stats=stats, workers=workers)

        # 处理客户端消息
        subscribed_tasks: set[int] = set()
        subscribed_logs = False

        while True:
            try:
                data = await websocket.receive_json()
                msg_type = data.get("type")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

                elif msg_type == "subscribe_task":
                    pending_id = data.get("pending_id")
                    if pending_id:
                        await ws_manager.subscribe_task(websocket, pending_id)
                        subscribed_tasks.add(pending_id)
                        await websocket.send_json({
                            "type": "subscribed",
                            "pending_id": pending_id
                        })

                elif msg_type == "unsubscribe_task":
                    pending_id = data.get("pending_id")
                    if pending_id:
                        await ws_manager.unsubscribe_task(websocket, pending_id)
                        subscribed_tasks.discard(pending_id)

                elif msg_type == "subscribe_logs":
                    if not subscribed_logs:
                        await ws_manager.log_subscribers.add(websocket)
                        subscribed_logs = True
                        await websocket.send_json({"type": "logs_subscribed"})

            except Exception as e:
                logger.warning(f"处理 WebSocket 消息时出错: {e}")
                break

    except WebSocketDisconnect:
        logger.info("WebSocket 客户端断开连接")
    except Exception as e:
        logger.error(f"WebSocket 连接错误: {e}")
    finally:
        # 清理订阅
        await ws_manager.disconnect_global(websocket)
        for task_id in subscribed_tasks:
            await ws_manager.unsubscribe_task(websocket, task_id)
        if subscribed_logs:
            ws_manager.log_subscribers.discard(websocket)


@router.websocket("/ws/workflow/task/{pending_id}")
async def websocket_task_progress(websocket: WebSocket, pending_id: int):
    """
    单任务 OCR 进度 WebSocket

    专门用于监听单个任务的处理进度
    """
    ws_manager = get_workflow_ws_manager()

    try:
        await websocket.accept()
        await ws_manager.subscribe_task(websocket, pending_id)

        logger.info(f"客户端订阅任务 {pending_id} 进度")

        while True:
            try:
                data = await websocket.receive_json()
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except Exception:
                break

    except WebSocketDisconnect:
        logger.info(f"任务 {pending_id} 进度订阅断开")
    except Exception as e:
        logger.error(f"任务进度 WebSocket 错误: {e}")
    finally:
        await ws_manager.unsubscribe_task(websocket, pending_id)


@router.websocket("/ws/workflow/logs")
async def websocket_worker_logs(websocket: WebSocket):
    """
    Worker 日志流 WebSocket

    实时推送 Worker 处理日志
    """
    ws_manager = get_workflow_ws_manager()

    try:
        await ws_manager.connect_logs(websocket)

        logger.info("客户端订阅日志流")

        while True:
            try:
                data = await websocket.receive_json()
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except Exception:
                break

    except WebSocketDisconnect:
        logger.info("日志流订阅断开")
    except Exception as e:
        logger.error(f"日志流 WebSocket 错误: {e}")
    finally:
        await ws_manager.disconnect_logs(websocket)


# ========== 广播辅助函数（供其他模块调用）==========

async def broadcast_stats_update():
    """广播统计数据更新"""
    ws_manager = get_workflow_ws_manager()
    stats = await get_current_stats()
    await ws_manager.broadcast_stats(stats)


async def broadcast_workers_update():
    """广播 Worker 状态更新"""
    ws_manager = get_workflow_ws_manager()
    workers = await get_current_workers()
    await ws_manager.broadcast_workers(workers)


# ========== Excel 导入功能 ==========

# 装备类型映射
EQUIPMENT_TYPES = {
    "rod": "鱼竿",
    "reel": "渔轮",
    "line": "鱼线",
    "lure": "拟饵",
}


@router.get(
    "/import/templates",
    response_model=ImportTemplateListResponse,
    summary="获取导入模板列表",
    description="获取所有装备类型的导入模板信息",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_READ))]
)
async def get_import_templates():
    """获取导入模板列表"""
    templates = []
    for key, label in EQUIPMENT_TYPES.items():
        templates.append(ImportTemplateInfo(
            equipment_type=key,
            equipment_type_label=label,
            download_url=f"/api/v1/admin/workflow/import/template/{key}"
        ))
    return ImportTemplateListResponse(templates=templates)


@router.get(
    "/import/template/{equipment_type}",
    summary="下载导入模板",
    description="下载指定装备类型的 Excel 导入模板（支持通过 token 查询参数认证）",
)
async def download_import_template(
    equipment_type: str,
    token: str = Query(None, description="JWT token（用于浏览器下载认证）")
):
    """
    下载导入模板

    由于浏览器直接打开 URL 无法携带 Authorization header，
    支持通过 query parameter 传递 token 进行认证。
    """
    # 验证 token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要提供 token 参数"
        )

    from ..auth.dependencies import verify_token
    try:
        verify_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Token 验证失败: {str(e)}"
        )

    if equipment_type not in EQUIPMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的装备类型: {equipment_type}"
        )

    from apps.api.services.excel_import_service import get_excel_import_service
    service = get_excel_import_service()

    try:
        content = service.generate_template(equipment_type)
        filename = f"{EQUIPMENT_TYPES[equipment_type]}导入模板.xlsx"
        # 使用 RFC 5987 编码中文文件名
        from urllib.parse import quote
        filename_encoded = quote(filename)

        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"
            }
        )
    except Exception as e:
        logger.error(f"生成模板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成模板失败: {str(e)}"
        )


@router.post(
    "/import/preview",
    response_model=ImportPreviewResponse,
    summary="预览导入数据",
    description="上传 Excel 文件并预览导入数据，不实际导入",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))]
)
async def preview_import(
    file: UploadFile = File(...),
    equipment_type: str = Query(..., description="装备类型: rod/reel/line/lure"),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))
):
    """预览导入数据"""
    if equipment_type not in EQUIPMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的装备类型: {equipment_type}"
        )

    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持 .xlsx 或 .xls 格式的 Excel 文件"
        )

    from apps.api.services.excel_import_service import get_excel_import_service
    service = get_excel_import_service()

    try:
        content = await file.read()
        preview_rows = service.parse_excel(content, equipment_type)

        # 转换为响应格式
        preview_data = []
        for row in preview_rows:
            preview_data.append(ImportPreviewRow(
                row_number=row.row_number,
                data=row.data,
                is_valid=row.is_valid,
                errors=row.errors
            ))

        valid_count = sum(1 for r in preview_rows if r.is_valid)
        invalid_count = len(preview_rows) - valid_count

        return ImportPreviewResponse(
            success=True,
            message=f"解析成功，共 {len(preview_rows)} 条数据",
            equipment_type=equipment_type,
            total_rows=len(preview_rows),
            valid_rows=valid_count,
            invalid_rows=invalid_count,
            preview_data=preview_data
        )

    except Exception as e:
        logger.error(f"预览导入失败: {e}")
        return ImportPreviewResponse(
            success=False,
            message=f"解析失败: {str(e)}",
            equipment_type=equipment_type,
            total_rows=0,
            valid_rows=0,
            invalid_rows=0,
            preview_data=[]
        )


@router.post(
    "/import/execute",
    response_model=ImportResponse,
    summary="执行导入",
    description="上传 Excel 文件并执行导入到待审核队列",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))]
)
async def execute_import(
    file: UploadFile = File(...),
    equipment_type: str = Query(..., description="装备类型: rod/reel/line/lure"),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))
):
    """执行导入"""
    if equipment_type not in EQUIPMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的装备类型: {equipment_type}"
        )

    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持 .xlsx 或 .xls 格式的 Excel 文件"
        )

    from apps.api.services.excel_import_service import get_excel_import_service
    service = get_excel_import_service()

    try:
        content = await file.read()
        result = service.import_to_pending(
            file_content=content,
            equipment_type=equipment_type,
            admin_user_id=current_user.user_id
        )

        # 转换错误格式
        errors = []
        for err in result.errors:
            errors.append(ImportError(
                row=err["row"],
                errors=err["errors"],
                data=err.get("data", {})
            ))

        logger.info(
            f"管理员 {current_user.username} 导入 {EQUIPMENT_TYPES[equipment_type]}: "
            f"成功 {result.imported_count} 条, 失败 {result.failed_count} 条"
        )

        return ImportResponse(
            success=result.success,
            message=result.message,
            total_rows=result.total_rows,
            imported_count=result.imported_count,
            failed_count=result.failed_count,
            pending_ids=result.pending_ids,
            errors=errors
        )

    except Exception as e:
        logger.error(f"执行导入失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )
