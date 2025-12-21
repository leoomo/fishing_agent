"""
分布式 Worker API 路由

提供远程 Worker 领取任务、汇报结果、心跳保活的接口
"""

import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Header, Depends, status
from pydantic import BaseModel, Field

from packages.scraper.database import get_crawler_db
from packages.scraper.models import CrawlerTask, TaskStatus, CrawlerLog, LogLevel

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== 数据模型 ==========

class WorkerInfo(BaseModel):
    """Worker 注册信息"""
    worker_id: str = Field(..., description="Worker 唯一标识")
    worker_name: Optional[str] = Field(None, description="Worker 名称")
    supported_types: List[str] = Field(default=["taobao", "jd", "forum"], description="支持的任务类型")
    max_concurrent: int = Field(default=1, description="最大并发任务数")
    ip_address: Optional[str] = Field(None, description="Worker IP 地址")


class TaskClaimRequest(BaseModel):
    """领取任务请求"""
    worker_id: str = Field(..., description="Worker 唯一标识")
    supported_types: List[str] = Field(default=["taobao", "jd", "forum"], description="支持的任务类型")
    max_tasks: int = Field(default=1, description="最多领取任务数")


class TaskClaimResponse(BaseModel):
    """领取任务响应"""
    success: bool
    tasks: List[dict] = Field(default_factory=list)
    message: str = ""


class TaskProgressReport(BaseModel):
    """任务进度汇报"""
    task_id: int = Field(..., description="任务ID")
    worker_id: str = Field(..., description="Worker ID")
    status: str = Field(..., description="任务状态: running/success/failed")
    progress: int = Field(default=0, description="进度百分比 0-100")
    message: Optional[str] = Field(None, description="进度消息")
    success_items: int = Field(default=0, description="成功数量")
    failed_items: int = Field(default=0, description="失败数量")
    total_items: int = Field(default=0, description="总数量")
    error_message: Optional[str] = Field(None, description="错误信息")
    result_data: Optional[dict] = Field(None, description="结果数据")


class TaskReportResponse(BaseModel):
    """汇报响应"""
    success: bool
    message: str = ""


class HeartbeatRequest(BaseModel):
    """心跳请求"""
    worker_id: str
    current_tasks: List[int] = Field(default_factory=list, description="当前正在执行的任务ID列表")
    cpu_usage: Optional[float] = Field(None, description="CPU 使用率")
    memory_usage: Optional[float] = Field(None, description="内存使用率")


class HeartbeatResponse(BaseModel):
    """心跳响应"""
    success: bool
    server_time: str
    commands: List[dict] = Field(default_factory=list, description="服务器下发的命令")


# ========== Worker 认证 ==========

# 简单的 API Key 认证（生产环境应使用更安全的方式）
WORKER_API_KEYS = {}  # worker_id -> api_key 映射，动态注册


def verify_worker_token(x_worker_token: str = Header(None)) -> str:
    """
    验证 Worker Token

    简化版：只检查 token 格式，生产环境应验证签名
    """
    if not x_worker_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 X-Worker-Token 头"
        )

    # Token 格式: worker_id:secret
    if ":" not in x_worker_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Token 格式"
        )

    worker_id, secret = x_worker_token.split(":", 1)

    # 验证 (简化版，生产环境应该查数据库或 Redis)
    if worker_id in WORKER_API_KEYS:
        if WORKER_API_KEYS[worker_id] != secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token 验证失败"
            )

    return worker_id


# ========== API 端点 ==========

@router.post(
    "/register",
    response_model=dict,
    summary="注册 Worker",
    description="Worker 首次连接时注册，获取认证 Token"
)
async def register_worker(info: WorkerInfo):
    """
    注册新的 Worker

    返回用于后续请求的认证 Token
    """
    # 生成 API Key
    api_key = secrets.token_urlsafe(32)
    WORKER_API_KEYS[info.worker_id] = api_key

    logger.info(
        f"Worker 注册: id={info.worker_id}, name={info.worker_name}, "
        f"types={info.supported_types}"
    )

    return {
        "success": True,
        "worker_id": info.worker_id,
        "token": f"{info.worker_id}:{api_key}",
        "message": "注册成功，请在后续请求中使用 X-Worker-Token 头"
    }


@router.post(
    "/claim",
    response_model=TaskClaimResponse,
    summary="领取任务",
    description="Worker 主动领取待执行的任务"
)
async def claim_tasks(
    request: TaskClaimRequest,
    worker_id: str = Depends(verify_worker_token)
):
    """
    领取待执行任务

    Worker 定期调用此接口获取新任务
    """
    db = get_crawler_db()

    try:
        with db.session_scope() as session:
            # 查找已启动等待领取的任务（QUEUED 状态）
            query = session.query(CrawlerTask).filter(
                CrawlerTask.status == TaskStatus.QUEUED,
                CrawlerTask.task_type.in_(request.supported_types)
            ).order_by(
                CrawlerTask.created_at.asc()  # 先进先出
            ).limit(request.max_tasks)

            tasks = query.all()

            if not tasks:
                return TaskClaimResponse(
                    success=True,
                    tasks=[],
                    message="暂无可领取的任务"
                )

            claimed_tasks = []

            for task in tasks:
                # 标记任务为运行中，分配给 Worker
                task.status = TaskStatus.RUNNING
                task.start_time = datetime.utcnow()
                task.assigned_node_id = None  # 可以扩展为 Worker ID

                # 在 config 中记录分配信息
                config = json.loads(task.config) if task.config else {}
                config["_assigned_worker"] = worker_id
                config["_assigned_at"] = datetime.utcnow().isoformat()
                task.config = json.dumps(config, ensure_ascii=False)

                claimed_tasks.append({
                    "task_id": task.id,
                    "task_type": task.task_type,
                    "task_name": task.task_name,
                    "config": config,
                    "timeout_seconds": task.timeout_seconds or 3600,
                    "max_retries": task.max_retries or 3,
                    "shop_url": task.shop_url,
                })

            session.commit()

            logger.info(
                f"Worker {worker_id} 领取了 {len(claimed_tasks)} 个任务: "
                f"{[t['task_id'] for t in claimed_tasks]}"
            )

            return TaskClaimResponse(
                success=True,
                tasks=claimed_tasks,
                message=f"成功领取 {len(claimed_tasks)} 个任务"
            )

    except Exception as e:
        logger.error(f"领取任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/report",
    response_model=TaskReportResponse,
    summary="汇报任务进度/结果",
    description="Worker 汇报任务执行进度或最终结果"
)
async def report_progress(
    report: TaskProgressReport,
    worker_id: str = Depends(verify_worker_token)
):
    """
    汇报任务进度或结果

    Worker 在执行过程中和完成后调用
    """
    db = get_crawler_db()

    try:
        with db.session_scope() as session:
            task = session.query(CrawlerTask).filter(
                CrawlerTask.id == report.task_id
            ).first()

            if not task:
                raise HTTPException(status_code=404, detail="任务不存在")

            # 验证是否是分配给该 Worker 的任务
            config = json.loads(task.config) if task.config else {}
            assigned_worker = config.get("_assigned_worker")
            if assigned_worker and assigned_worker != worker_id:
                raise HTTPException(
                    status_code=403,
                    detail=f"任务不属于该 Worker (分配给: {assigned_worker})"
                )

            # 更新任务状态
            if report.status == "running":
                task.status = TaskStatus.RUNNING
            elif report.status == "success":
                task.status = TaskStatus.SUCCESS
                task.end_time = datetime.utcnow()
            elif report.status == "failed":
                task.status = TaskStatus.FAILED
                task.end_time = datetime.utcnow()
                task.error_message = report.error_message

            # 更新统计数据
            task.success_items = report.success_items
            task.failed_items = report.failed_items
            task.total_items = report.total_items

            # 保存结果数据
            if report.result_data:
                task.result_summary = json.dumps(report.result_data, ensure_ascii=False)

            # 记录日志
            log_level = LogLevel.INFO if report.status != "failed" else LogLevel.ERROR
            log = CrawlerLog(
                task_id=task.id,
                level=log_level,
                message=report.message or f"Worker {worker_id} 汇报: {report.status}",
                details=json.dumps({
                    "worker_id": worker_id,
                    "progress": report.progress,
                    "success_items": report.success_items,
                    "failed_items": report.failed_items,
                }, ensure_ascii=False)
            )
            session.add(log)

            session.commit()

            logger.info(
                f"Worker {worker_id} 汇报任务 {report.task_id}: "
                f"status={report.status}, progress={report.progress}%"
            )

            # 推送 WebSocket 更新
            try:
                from apps.api.services.websocket_manager import get_ws_manager
                import asyncio

                ws_manager = get_ws_manager()
                asyncio.create_task(
                    ws_manager.broadcast_progress(
                        task_id=report.task_id,
                        status=report.status.upper(),
                        progress=report.progress,
                        message=report.message or "",
                        items_processed=report.total_items,
                        items_success=report.success_items,
                        items_failed=report.failed_items
                    )
                )
            except Exception as ws_error:
                logger.debug(f"WebSocket 推送失败: {ws_error}")

            return TaskReportResponse(
                success=True,
                message="汇报成功"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"汇报任务进度失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/heartbeat",
    response_model=HeartbeatResponse,
    summary="心跳保活",
    description="Worker 定期发送心跳，汇报状态"
)
async def heartbeat(
    request: HeartbeatRequest,
    worker_id: str = Depends(verify_worker_token)
):
    """
    心跳接口

    Worker 定期调用，服务器可以下发命令
    """
    commands = []

    # 检查是否有需要取消的任务
    db = get_crawler_db()
    try:
        with db.session_scope() as session:
            for task_id in request.current_tasks:
                task = session.query(CrawlerTask).filter(
                    CrawlerTask.id == task_id
                ).first()

                if task:
                    # 检查任务是否已被取消
                    config = json.loads(task.config) if task.config else {}
                    if config.get("_cancelled"):
                        commands.append({
                            "type": "cancel_task",
                            "task_id": task_id,
                            "reason": "任务已被用户取消"
                        })
    except Exception as e:
        logger.error(f"心跳处理失败: {e}")

    return HeartbeatResponse(
        success=True,
        server_time=datetime.utcnow().isoformat(),
        commands=commands
    )


@router.get(
    "/status",
    summary="获取 Worker 状态",
    description="获取所有注册的 Worker 状态"
)
async def get_workers_status():
    """
    获取所有 Worker 的状态（管理接口）
    """
    return {
        "registered_workers": list(WORKER_API_KEYS.keys()),
        "total_count": len(WORKER_API_KEYS)
    }
