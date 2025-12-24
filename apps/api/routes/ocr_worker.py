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
)

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

            # 解析图片列表
            images = []
            if item.images:
                try:
                    images = json.loads(item.images)
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
            image_paths = json.loads(item.images)
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
            # 解析图片数量
            images_count = 0
            if item.images:
                try:
                    images_count = len(json.loads(item.images))
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
