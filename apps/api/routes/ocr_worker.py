"""
OCR Worker API 路由

提供 OCR Worker 注册、任务领取、结果汇报、心跳等接口
"""

import json
import logging
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional
import zipfile
import io

from fastapi import APIRouter, HTTPException, Header, Depends, status, Query
from fastapi.responses import StreamingResponse

from apps.api.orm.session import get_db_session
from packages.agents.equipment_import.models.pending import PendingEquipment
from apps.api.schemas.ocr_worker import (
    OCRWorkerRegister,
    OCRWorkerRegisterResponse,
    OCRTaskClaimRequest,
    OCRTaskClaimResponse,
    OCRTaskInfo,
    OCRTaskReport,
    OCRTaskReportResponse,
    OCRHeartbeatRequest,
    OCRHeartbeatResponse,
    OCRStats,
    OCRTaskItem,
    OCRTaskListResponse,
    # 管理员操作
    OCRTaskRetryResponse,
    OCRTaskBatchRetryRequest,
    OCRTaskBatchRetryResponse,
    OCRTaskSkipResponse,
    OCRTaskSetPriorityRequest,
    OCRTaskSetPriorityResponse,
    OCRTaskDeleteResponse,
)

from apps.api.auth.dependencies import require_permission, CurrentUser
from apps.api.auth.permissions import PermissionEnum
from apps.api.schemas.data_workflow import OCRProgressReport, WorkerLogSubmit
from apps.api.services.workflow_ws_manager import get_workflow_ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== Worker 认证 ==========

# Worker API Keys 存储（生产环境应使用 Redis 或数据库）
OCR_WORKER_API_KEYS = {}  # worker_id -> api_key


def verify_ocr_worker_token(x_worker_token: str = Header(None)) -> str:
    """验证 OCR Worker Token"""
    if not x_worker_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 X-Worker-Token 头"
        )

    if ":" not in x_worker_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Token 格式"
        )

    worker_id, secret = x_worker_token.split(":", 1)

    if worker_id in OCR_WORKER_API_KEYS:
        if OCR_WORKER_API_KEYS[worker_id] != secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token 验证失败"
            )

    return worker_id


# ========== API 端点 ==========

@router.post(
    "/register",
    response_model=OCRWorkerRegisterResponse,
    summary="注册 OCR Worker",
    description="OCR Worker 首次连接时注册，获取认证 Token"
)
async def register_ocr_worker(info: OCRWorkerRegister):
    """注册新的 OCR Worker"""
    api_key = secrets.token_urlsafe(32)
    OCR_WORKER_API_KEYS[info.worker_id] = api_key

    logger.info(
        f"OCR Worker 注册: id={info.worker_id}, name={info.worker_name}, "
        f"provider={info.ocr_provider}"
    )

    return OCRWorkerRegisterResponse(
        success=True,
        worker_id=info.worker_id,
        token=f"{info.worker_id}:{api_key}",
        message="注册成功"
    )


@router.post(
    "/claim",
    response_model=OCRTaskClaimResponse,
    summary="领取 OCR 任务",
    description="Worker 主动领取待处理的 OCR 任务"
)
async def claim_ocr_tasks(
    request: OCRTaskClaimRequest,
    worker_id: str = Depends(verify_ocr_worker_token)
):
    """领取待处理的 OCR 任务"""
    with get_db_session() as session:
        # 查询待处理的任务
        query = session.query(PendingEquipment).filter(
            PendingEquipment.ocr_status == "pending",
            PendingEquipment.images.isnot(None),
            PendingEquipment.images != "[]",
            PendingEquipment.images != "",
        ).order_by(
            PendingEquipment.created_at.asc()
        ).limit(request.max_tasks)

        pending_items = query.all()

        if not pending_items:
            return OCRTaskClaimResponse(
                success=True,
                tasks=[],
                message="暂无可领取的任务"
            )

        claimed_tasks = []
        now = datetime.utcnow()

        for item in pending_items:
            # 更新状态为处理中
            item.ocr_status = "processing"
            item.ocr_started_at = now
            item.ocr_worker_id = worker_id

            # 解析图片列表（兼容新旧格式）
            images = []
            if item.images:
                try:
                    data = json.loads(item.images)
                    # 新格式: {"paths": [...], "metadata": [...]}
                    if isinstance(data, dict) and "paths" in data:
                        images = data["paths"]
                    # 旧格式: ["path1", "path2", ...]
                    elif isinstance(data, list):
                        images = data
                except json.JSONDecodeError:
                    images = []

            claimed_tasks.append(OCRTaskInfo(
                pending_id=item.id,
                images=images,
                brand_name=item.brand_name,
                product_name=item.product_name,
                source_url=item.source_url,
            ))

        session.commit()

        logger.info(
            f"OCR Worker {worker_id} 领取了 {len(claimed_tasks)} 个任务: "
            f"{[t.pending_id for t in claimed_tasks]}"
        )

        # 广播任务领取事件
        ws_manager = get_workflow_ws_manager()
        for task in claimed_tasks:
            import asyncio
            asyncio.create_task(ws_manager.broadcast_task_event(
                task.pending_id,
                "task_claimed",
                {
                    "pending_id": task.pending_id,
                    "worker_id": worker_id,
                    "brand_name": task.brand_name,
                    "product_name": task.product_name,
                }
            ))

        # 广播统计更新
        from apps.api.routes.data_workflow import broadcast_stats_update
        import asyncio
        asyncio.create_task(broadcast_stats_update())

        return OCRTaskClaimResponse(
            success=True,
            tasks=claimed_tasks,
            message=f"成功领取 {len(claimed_tasks)} 个任务"
        )


@router.post(
    "/report",
    response_model=OCRTaskReportResponse,
    summary="汇报 OCR 结果",
    description="Worker 汇报 OCR 处理结果"
)
async def report_ocr_result(
    report: OCRTaskReport,
    worker_id: str = Depends(verify_ocr_worker_token)
):
    """汇报 OCR 处理结果"""
    with get_db_session() as session:
        item = session.query(PendingEquipment).filter(
            PendingEquipment.id == report.pending_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {report.pending_id} 不存在"
            )

        # 验证 Worker 是否是任务的分配者
        if item.ocr_worker_id and item.ocr_worker_id != worker_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"任务 {report.pending_id} 不属于当前 Worker"
            )

        now = datetime.utcnow()

        if report.status == "success":
            item.ocr_status = "completed"
            item.ocr_text = report.ocr_text
            item.ocr_completed_at = now
            item.ocr_processing_time_ms = report.processing_time_ms
            item.ocr_provider = report.provider
            message = "OCR 处理成功"

        else:  # failed
            item.ocr_retry_count += 1
            item.ocr_error_message = report.error_message
            item.ocr_provider = report.provider

            if item.ocr_retry_count < 3:
                # 重试次数未超限，重置为待处理
                item.ocr_status = "pending"
                item.ocr_started_at = None
                item.ocr_worker_id = None
                message = f"OCR 处理失败，将重试 (第 {item.ocr_retry_count} 次)"
            else:
                # 超过重试次数，标记为失败
                item.ocr_status = "failed"
                item.ocr_completed_at = now
                message = f"OCR 处理失败，已达最大重试次数"

        session.commit()

        logger.info(
            f"OCR Worker {worker_id} 汇报任务 {report.pending_id}: "
            f"status={report.status}, message={message}"
        )

        # 广播处理结果事件
        ws_manager = get_workflow_ws_manager()
        event_type = "ocr_completed" if report.status == "success" else "ocr_failed"
        import asyncio
        asyncio.create_task(ws_manager.broadcast_task_event(
            report.pending_id,
            event_type,
            {
                "pending_id": report.pending_id,
                "worker_id": worker_id,
                "status": report.status,
                "ocr_status": item.ocr_status,
                "processing_time_ms": report.processing_time_ms,
                "error_message": report.error_message if report.status == "failed" else None,
                "retry_count": item.ocr_retry_count,
            }
        ))

        # 广播统计更新
        from apps.api.routes.data_workflow import broadcast_stats_update
        asyncio.create_task(broadcast_stats_update())

        return OCRTaskReportResponse(success=True, message=message)


@router.post(
    "/heartbeat",
    response_model=OCRHeartbeatResponse,
    summary="Worker 心跳",
    description="Worker 定期发送心跳保持连接"
)
async def ocr_worker_heartbeat(
    request: OCRHeartbeatRequest,
    worker_id: str = Depends(verify_ocr_worker_token)
):
    """处理 Worker 心跳"""
    commands = []

    # 检查是否有需要取消的任务
    # TODO: 实现任务取消逻辑

    return OCRHeartbeatResponse(
        success=True,
        server_time=datetime.utcnow().isoformat(),
        commands=commands
    )


@router.get(
    "/images/{pending_id}",
    summary="下载待处理图片",
    description="Worker 下载待处理任务的图片"
)
async def download_images(
    pending_id: int,
    worker_id: str = Depends(verify_ocr_worker_token)
):
    """下载任务关联的图片"""
    with get_db_session() as session:
        item = session.query(PendingEquipment).filter(
            PendingEquipment.id == pending_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {pending_id} 不存在"
            )

        if not item.images:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {pending_id} 没有图片"
            )

        try:
            data = json.loads(item.images)
            # 兼容新旧格式
            if isinstance(data, dict) and "paths" in data:
                image_paths = data["paths"]
            elif isinstance(data, list):
                image_paths = data
            else:
                image_paths = []
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="图片路径解析失败"
            )

        if not image_paths:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {pending_id} 没有图片"
            )

        # 图片存储基础路径
        base_path = Path("shared/images")

        # 创建 ZIP 文件
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for img_path in image_paths:
                full_path = base_path / img_path
                if full_path.exists():
                    zip_file.write(full_path, img_path)
                else:
                    logger.warning(f"图片文件不存在: {full_path}")

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=images_{pending_id}.zip"
            }
        )


@router.get(
    "/stats",
    response_model=OCRStats,
    summary="OCR 任务统计",
    description="获取 OCR 任务各状态的统计数据"
)
async def get_ocr_stats():
    """获取 OCR 任务统计"""
    with get_db_session() as session:
        from sqlalchemy import func

        stats = session.query(
            PendingEquipment.ocr_status,
            func.count(PendingEquipment.id)
        ).group_by(PendingEquipment.ocr_status).all()

        result = OCRStats()
        for ocr_status, count in stats:
            result.total += count
            if ocr_status == "pending":
                result.pending = count
            elif ocr_status == "processing":
                result.processing = count
            elif ocr_status == "completed":
                result.completed = count
            elif ocr_status == "failed":
                result.failed = count
            elif ocr_status == "skipped":
                result.skipped = count

        return result


@router.get(
    "/tasks",
    response_model=OCRTaskListResponse,
    summary="OCR 任务列表",
    description="获取 OCR 任务列表，支持分页和状态筛选"
)
async def list_ocr_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    ocr_status: Optional[str] = Query(None, description="OCR 状态筛选"),
):
    """获取 OCR 任务列表"""
    with get_db_session() as session:
        query = session.query(PendingEquipment)

        if ocr_status:
            query = query.filter(PendingEquipment.ocr_status == ocr_status)

        # 获取总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        items = query.order_by(
            PendingEquipment.created_at.desc()
        ).offset(offset).limit(page_size).all()

        tasks = []
        for item in items:
            # 解析图片数量（兼容新旧格式）
            images_count = 0
            if item.images:
                try:
                    data = json.loads(item.images)
                    # 新格式: {"paths": [...], "metadata": [...]}
                    if isinstance(data, dict) and "paths" in data:
                        images_count = len(data["paths"])
                    # 旧格式: ["path1", "path2", ...]
                    elif isinstance(data, list):
                        images_count = len(data)
                except json.JSONDecodeError:
                    pass

            tasks.append(OCRTaskItem(
                pending_id=item.id,
                brand_name=item.brand_name,
                product_name=item.product_name,
                ocr_status=item.ocr_status,
                ocr_worker_id=item.ocr_worker_id,
                ocr_started_at=item.ocr_started_at,
                ocr_completed_at=item.ocr_completed_at,
                ocr_processing_time_ms=item.ocr_processing_time_ms,
                ocr_provider=item.ocr_provider,
                ocr_retry_count=item.ocr_retry_count,
                ocr_error_message=item.ocr_error_message,
                ocr_priority=item.ocr_priority,
                images_count=images_count,
                created_at=item.created_at,
            ))

        return OCRTaskListResponse(
            success=True,
            tasks=tasks,
            total=total,
            page=page,
            page_size=page_size,
        )


# ========== 管理员操作端点 ==========


@router.post(
    "/admin/tasks/{pending_id}/retry",
    response_model=OCRTaskRetryResponse,
    summary="手动重试OCR任务",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))]
)
async def retry_ocr_task(
    pending_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))
):
    """
    将失败/跳过的任务重新设为pending状态
    - 重置 retry_count 为 0
    - 清空 error_message
    """
    with get_db_session() as session:
        item = session.query(PendingEquipment).filter(
            PendingEquipment.id == pending_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {pending_id} 不存在"
            )

        # 允许 failed/skipped/completed 状态重试
        if item.ocr_status not in ["failed", "skipped", "completed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"只有失败、跳过或已完成的任务可以重试，当前状态: {item.ocr_status}"
            )

        previous_status = item.ocr_status

        # 重置状态为 pending
        item.ocr_status = "pending"
        item.ocr_retry_count = 0
        item.ocr_error_message = None
        item.ocr_started_at = None
        item.ocr_completed_at = None
        item.ocr_worker_id = None

        session.commit()

        logger.info(
            f"管理员 {current_user.username} 重试任务 {pending_id}, "
            f"原状态: {previous_status}"
        )

        return OCRTaskRetryResponse(
            success=True,
            message="任务已重新加入队列（重试次数已重置）",
            pending_id=pending_id,
            previous_status=previous_status
        )


@router.post(
    "/admin/tasks/retry-batch",
    response_model=OCRTaskBatchRetryResponse,
    summary="批量重试OCR任务",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))]
)
async def retry_ocr_tasks_batch(
    request: OCRTaskBatchRetryRequest,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))
):
    """批量重试失败/跳过的任务，全部重置重试次数"""
    with get_db_session() as session:
        query = session.query(PendingEquipment).filter(
            PendingEquipment.ocr_status == request.ocr_status
        )

        # 如果指定了任务ID，只重试这些任务
        if request.pending_ids:
            query = query.filter(PendingEquipment.id.in_(request.pending_ids))

        items = query.all()

        if not items:
            return OCRTaskBatchRetryResponse(
                success=True,
                message="没有找到需要重试的任务",
                retried_count=0,
                skipped_count=0,
                pending_ids=[]
            )

        retried_ids = []
        now = datetime.utcnow()

        for item in items:
            # 重置状态
            item.ocr_status = "pending"
            item.ocr_retry_count = 0
            item.ocr_error_message = None
            item.ocr_started_at = None
            item.ocr_completed_at = None
            item.ocr_worker_id = None
            retried_ids.append(item.id)

        session.commit()

        logger.info(
            f"管理员 {current_user.username} 批量重试了 {len(retried_ids)} 个任务: {retried_ids}"
        )

        return OCRTaskBatchRetryResponse(
            success=True,
            message=f"成功重试 {len(retried_ids)} 个任务",
            retried_count=len(retried_ids),
            skipped_count=0,
            pending_ids=retried_ids
        )


@router.post(
    "/admin/tasks/{pending_id}/skip",
    response_model=OCRTaskSkipResponse,
    summary="跳过/取消OCR任务",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))]
)
async def skip_ocr_task(
    pending_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))
):
    """将任务标记为跳过状态（支持取消处理中的任务）"""
    with get_db_session() as session:
        item = session.query(PendingEquipment).filter(
            PendingEquipment.id == pending_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {pending_id} 不存在"
            )

        # 允许 pending/failed/processing 状态跳过/取消
        if item.ocr_status not in ["pending", "failed", "processing"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"只有待处理、失败或处理中的任务可以跳过，当前状态: {item.ocr_status}"
            )

        previous_status = item.ocr_status
        item.ocr_status = "skipped"
        item.ocr_completed_at = datetime.utcnow()
        session.commit()

        action = "取消" if previous_status == "processing" else "跳过"
        logger.info(
            f"管理员 {current_user.username} {action}任务 {pending_id}, 原状态: {previous_status}"
        )

        return OCRTaskSkipResponse(
            success=True,
            message=f"任务已{action}",
            pending_id=pending_id
        )


@router.put(
    "/admin/tasks/{pending_id}/priority",
    response_model=OCRTaskSetPriorityResponse,
    summary="设置OCR任务优先级",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))]
)
async def set_task_priority(
    pending_id: int,
    request: OCRTaskSetPriorityRequest,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_UPDATE))
):
    """设置任务优先级，高优先级任务先被Worker领取"""
    with get_db_session() as session:
        item = session.query(PendingEquipment).filter(
            PendingEquipment.id == pending_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {pending_id} 不存在"
            )

        old_priority = item.ocr_priority
        item.ocr_priority = request.priority
        session.commit()

        logger.info(
            f"管理员 {current_user.username} 设置任务 {pending_id} 优先级: {old_priority} -> {request.priority}"
        )

        return OCRTaskSetPriorityResponse(
            success=True,
            message="优先级已更新",
            pending_id=pending_id,
            old_priority=old_priority,
            new_priority=request.priority
        )


@router.delete(
    "/admin/tasks/{pending_id}",
    response_model=OCRTaskDeleteResponse,
    summary="删除OCR任务",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_DELETE))]
)
async def delete_ocr_task(
    pending_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_DELETE))
):
    """删除任务记录（仅pending/failed/skipped状态可删除）"""
    with get_db_session() as session:
        item = session.query(PendingEquipment).filter(
            PendingEquipment.id == pending_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {pending_id} 不存在"
            )

        # processing 和 completed 状态不可删除
        if item.ocr_status in ["processing", "completed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"处理中或已完成的任务不可删除，当前状态: {item.ocr_status}"
            )

        session.delete(item)
        session.commit()

        logger.info(
            f"管理员 {current_user.username} 删除任务 {pending_id}"
        )

        return OCRTaskDeleteResponse(
            success=True,
            message="任务已删除",
            pending_id=pending_id
        )


# ========== 实时进度和日志上报 ==========

@router.post(
    "/progress",
    summary="上报 OCR 处理进度",
    description="Worker 上报当前任务的处理进度（阶段和百分比）"
)
async def report_ocr_progress(
    progress: OCRProgressReport,
    worker_id: str = Depends(verify_ocr_worker_token)
):
    """
    Worker 上报 OCR 处理进度

    阶段说明：
    - downloading: 下载图片
    - merging: 合并图片
    - ocr_processing: OCR 识别
    - extracting: 提取数据
    """
    ws_manager = get_workflow_ws_manager()

    # 广播进度事件
    await ws_manager.broadcast_task_event(
        progress.pending_id,
        "ocr_progress",
        {
            "pending_id": progress.pending_id,
            "worker_id": worker_id,
            "stage": progress.stage,
            "progress": progress.progress,
            "message": progress.message,
            "current_image": progress.current_image,
            "total_images": progress.total_images,
        }
    )

    return {"success": True, "message": "进度已更新"}


@router.post(
    "/log",
    summary="提交 Worker 日志",
    description="Worker 提交处理过程中的日志信息"
)
async def submit_worker_log(
    log: WorkerLogSubmit,
    worker_id: str = Depends(verify_ocr_worker_token)
):
    """Worker 提交处理日志"""
    ws_manager = get_workflow_ws_manager()

    # 广播日志事件
    await ws_manager.broadcast_log(
        worker_id=worker_id,
        level=log.level,
        message=log.message,
        pending_id=log.pending_id,
    )

    return {"success": True, "message": "日志已提交"}
