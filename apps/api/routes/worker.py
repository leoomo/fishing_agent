"""
分布式 Worker API 路由

提供远程 Worker 领取任务、汇报结果、心跳保活的接口

优化版本:
- Worker 状态持久化到数据库
- 动态心跳间隔
- 任务优先级队列
"""

import hashlib
import json
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Header, Depends, status, Form, File, UploadFile
from pydantic import BaseModel, Field

from packages.scraper.database import get_crawler_db
from packages.scraper.models import CrawlerTask, TaskStatus, CrawlerLog, LogLevel
from packages.scraper.models.node import CrawlerNode, NodeStatus, NodeTaskAssignment
from apps.api.schemas.crawler import (
    PendingEquipmentSubmit,
    PendingEquipmentSubmitResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== 工具函数 ==========

def hash_secret(secret: str) -> str:
    """哈希密钥"""
    return hashlib.sha256(secret.encode()).hexdigest()


def verify_secret(secret: str, secret_hash: str) -> bool:
    """验证密钥"""
    return hash_secret(secret) == secret_hash


def calculate_heartbeat_interval(worker_load: float, queue_length: int) -> int:
    """
    根据负载动态计算心跳间隔

    Args:
        worker_load: Worker 负载率 (0.0-1.0)
        queue_length: 任务队列长度

    Returns:
        心跳间隔（秒）
    """
    if queue_length > 100:
        return 10  # 队列积压，加快心跳以便快速分配任务
    elif queue_length > 50:
        return 15
    elif worker_load > 0.8:
        return 60  # 高负载，减少心跳以降低开销
    elif worker_load > 0.5:
        return 45
    else:
        return 30  # 正常


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
    next_heartbeat_seconds: int = Field(default=30, description="下次心跳间隔（秒）")


# ========== Worker 认证 ==========

# 内存缓存（可选，用于减少数据库查询）
_worker_cache: dict = {}
_cache_ttl = 300  # 缓存有效期（秒）


def verify_worker_token(x_worker_token: str = Header(None)) -> str:
    """
    验证 Worker Token - 使用数据库持久化验证

    Token 格式: node_id:secret
    """
    if not x_worker_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 X-Worker-Token 头"
        )

    # Token 格式: node_id:secret
    if ":" not in x_worker_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Token 格式"
        )

    node_id, secret = x_worker_token.split(":", 1)

    # 检查缓存
    cache_key = f"{node_id}:{hash_secret(secret)}"
    if cache_key in _worker_cache:
        cache_entry = _worker_cache[cache_key]
        if datetime.utcnow().timestamp() - cache_entry['time'] < _cache_ttl:
            return node_id

    # 从数据库验证
    db = get_crawler_db()
    try:
        with db.session_scope() as session:
            node = session.query(CrawlerNode).filter(
                CrawlerNode.node_id == node_id
            ).first()

            if not node:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Worker 未注册"
                )

            if not verify_secret(secret, node.node_secret_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token 验证失败"
                )

            # 更新缓存
            _worker_cache[cache_key] = {
                'time': datetime.utcnow().timestamp(),
                'node_id': node_id
            }

            return node_id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Worker token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="认证服务异常"
        )


# ========== API 端点 ==========

@router.post(
    "/register",
    response_model=dict,
    summary="注册 Worker",
    description="Worker 首次连接时注册，获取认证 Token（持久化到数据库）"
)
async def register_worker(info: WorkerInfo):
    """
    注册新的 Worker - 持久化到数据库

    返回用于后续请求的认证 Token
    """
    db = get_crawler_db()

    try:
        with db.session_scope() as session:
            # 检查是否已注册
            existing = session.query(CrawlerNode).filter(
                CrawlerNode.node_id == info.worker_id
            ).first()

            if existing:
                # 已存在，更新信息并重新生成密钥
                node_secret = secrets.token_urlsafe(32)
                existing.node_name = info.worker_name or existing.node_name
                existing.capabilities = json.dumps(info.supported_types)
                existing.max_concurrent_tasks = info.max_concurrent
                existing.ip_address = info.ip_address
                existing.node_secret_hash = hash_secret(node_secret)
                existing.status = NodeStatus.ONLINE
                existing.last_heartbeat = datetime.utcnow()

                session.commit()

                logger.info(f"Worker 重新注册: id={info.worker_id}")

                return {
                    "success": True,
                    "worker_id": info.worker_id,
                    "token": f"{info.worker_id}:{node_secret}",
                    "message": "重新注册成功，已更新认证密钥"
                }

            # 新注册
            node_id = info.worker_id or str(uuid.uuid4())
            node_secret = secrets.token_urlsafe(32)

            node = CrawlerNode(
                node_id=node_id,
                node_name=info.worker_name or f"Worker-{node_id[:8]}",
                node_secret_hash=hash_secret(node_secret),
                capabilities=json.dumps(info.supported_types),
                max_concurrent_tasks=info.max_concurrent,
                ip_address=info.ip_address,
                status=NodeStatus.ONLINE,
                last_heartbeat=datetime.utcnow(),
            )

            session.add(node)
            session.commit()

            logger.info(
                f"Worker 注册: id={node_id}, name={info.worker_name}, "
                f"types={info.supported_types}"
            )

            return {
                "success": True,
                "worker_id": node_id,
                "token": f"{node_id}:{node_secret}",
                "message": "注册成功，请在后续请求中使用 X-Worker-Token 头"
            }

    except Exception as e:
        logger.error(f"Worker 注册失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/claim",
    response_model=TaskClaimResponse,
    summary="领取任务",
    description="Worker 主动领取待执行的任务（支持优先级队列）"
)
async def claim_tasks(
    request: TaskClaimRequest,
    worker_id: str = Depends(verify_worker_token)
):
    """
    领取待执行任务 - 支持优先级队列

    Worker 定期调用此接口获取新任务
    优先级高的任务优先被领取
    """
    db = get_crawler_db()

    try:
        with db.session_scope() as session:
            # 查找已启动等待领取的任务（QUEUED 状态）
            # 优先级队列: priority DESC, created_at ASC
            query = session.query(CrawlerTask).filter(
                CrawlerTask.status == TaskStatus.QUEUED,
                CrawlerTask.task_type.in_(request.supported_types)
            ).order_by(
                CrawlerTask.priority.desc(),  # 高优先级优先
                CrawlerTask.created_at.asc()  # 同优先级先进先出
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

            # 推送 WebSocket 更新，通知前端任务状态已变更
            try:
                from apps.api.services.websocket_manager import get_ws_manager
                import asyncio

                ws_manager = get_ws_manager()
                for claimed_task in claimed_tasks:
                    asyncio.create_task(
                        ws_manager.broadcast_progress(
                            task_id=claimed_task['task_id'],
                            status="RUNNING",
                            progress=0,
                            message=f"任务已被 Worker {worker_id} 领取，开始执行",
                            items_processed=0,
                            items_success=0,
                            items_failed=0
                        )
                    )
            except Exception as ws_error:
                logger.debug(f"WebSocket 推送失败: {ws_error}")

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
    description="Worker 定期发送心跳，汇报状态（支持动态心跳间隔）"
)
async def heartbeat(
    request: HeartbeatRequest,
    worker_id: str = Depends(verify_worker_token)
):
    """
    心跳接口 - 支持动态心跳间隔

    Worker 定期调用，服务器可以下发命令
    同时更新 Worker 状态到数据库
    """
    commands = []
    next_heartbeat_seconds = 30

    db = get_crawler_db()
    try:
        with db.session_scope() as session:
            # 更新 Worker 状态
            node = session.query(CrawlerNode).filter(
                CrawlerNode.node_id == worker_id
            ).first()

            if node:
                node.last_heartbeat = datetime.utcnow()
                node.current_tasks = len(request.current_tasks)
                node.running_task_ids = json.dumps(request.current_tasks)
                node.status = NodeStatus.ONLINE

                if request.cpu_usage is not None:
                    node.cpu_usage = request.cpu_usage
                if request.memory_usage is not None:
                    node.memory_usage = request.memory_usage

                # 计算 Worker 负载率
                worker_load = node.current_tasks / max(node.max_concurrent_tasks, 1)

                # 获取待处理任务队列长度
                queue_length = session.query(CrawlerTask).filter(
                    CrawlerTask.status == TaskStatus.QUEUED
                ).count()

                # 动态计算心跳间隔
                next_heartbeat_seconds = calculate_heartbeat_interval(
                    worker_load, queue_length
                )
                node.heartbeat_interval = next_heartbeat_seconds

            # 检查是否有需要取消的任务
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

            session.commit()

    except Exception as e:
        logger.error(f"心跳处理失败: {e}")

    return HeartbeatResponse(
        success=True,
        server_time=datetime.utcnow().isoformat(),
        commands=commands,
        next_heartbeat_seconds=next_heartbeat_seconds
    )


@router.get(
    "/status",
    summary="获取 Worker 状态",
    description="获取所有注册的 Worker 状态（从数据库读取）"
)
async def get_workers_status():
    """
    获取所有 Worker 的状态（管理接口）- 从数据库读取
    """
    db = get_crawler_db()

    try:
        with db.session_scope() as session:
            # 获取所有 Worker
            nodes = session.query(CrawlerNode).all()

            # 检查在线状态（超过 5 分钟未心跳视为离线）
            now = datetime.utcnow()
            offline_threshold = now - timedelta(minutes=5)

            workers = []
            online_count = 0
            total_tasks = 0

            for node in nodes:
                is_online = (
                    node.last_heartbeat and
                    node.last_heartbeat > offline_threshold and
                    node.status == NodeStatus.ONLINE
                )

                if is_online:
                    online_count += 1
                    total_tasks += node.current_tasks

                workers.append({
                    'id': node.node_id,
                    'name': node.node_name,
                    'status': 'active' if is_online else 'inactive',
                    'current_task': node.running_task_ids,
                    'tasks_completed': node.total_completed,
                    'cpu_usage': node.cpu_usage,
                    'memory_usage': node.memory_usage,
                    'disk_usage': node.disk_usage,
                    'last_heartbeat': node.last_heartbeat.isoformat() if node.last_heartbeat else None,
                    'worker_version': node.worker_version,
                })

            return {
                "workers": workers,
                "total_count": len(nodes),
                "online_count": online_count,
                "total_running_tasks": total_tasks
            }

    except Exception as e:
        logger.error(f"获取 Worker 状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/submit-pending",
    response_model=PendingEquipmentSubmitResponse,
    summary="提交待审核装备数据",
    description="Worker 提交 OCR 识别结果，服务端提取结构化数据并存入待审核表"
)
async def submit_pending_equipment(
    request: PendingEquipmentSubmit,
    worker_id: str = Depends(verify_worker_token)
):
    """
    Worker 提交待审核装备数据

    处理流程：
    1. 验证 Worker 权限
    2. 调用 EquipmentImportAgent 提取结构化数据
    3. 存入 pending_equipment 表
    4. 更新任务统计信息

    Args:
        request: 包含 OCR 文本和来源信息
        worker_id: 从 Token 验证获取的 Worker ID

    Returns:
        PendingEquipmentSubmitResponse: 包含待审核记录 ID
    """
    try:
        # 验证请求中的 worker_id 与 token 中的一致
        if request.worker_id != worker_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Worker ID 不匹配 (请求: {request.worker_id}, Token: {worker_id})"
            )

        # 验证任务存在
        db = get_crawler_db()
        with db.session_scope() as session:
            task = session.query(CrawlerTask).filter(
                CrawlerTask.id == request.task_id
            ).first()

            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"任务不存在: {request.task_id}"
                )

            # 验证任务是否分配给该 Worker
            config = json.loads(task.config) if task.config else {}
            assigned_worker = config.get("_assigned_worker")
            if assigned_worker and assigned_worker != worker_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"任务不属于该 Worker (分配给: {assigned_worker})"
                )

        # 调用 EquipmentImportAgent 提取结构化数据
        from packages.agents.equipment_import import EquipmentImportAgent

        agent = EquipmentImportAgent(
            model_provider="zhipu",
            enable_logging=True,
            enable_compression=True,
            enable_monitoring=True  # 启用监控记录
        )

        # 使用 extract_and_save 提取并保存
        result = agent.extract_and_save(
            text=request.ocr_text,
            source_type=request.source_type,
            source_url=request.source_url
        )

        if result.success:
            logger.info(
                f"Worker {worker_id} 提交待审核数据成功: "
                f"task_id={request.task_id}, pending_id={result.pending_id}"
            )

            # 记录日志
            with db.session_scope() as session:
                log = CrawlerLog(
                    task_id=request.task_id,
                    level=LogLevel.INFO,
                    message=f"Worker 提交待审核装备数据，pending_id={result.pending_id}",
                    details=json.dumps({
                        "worker_id": worker_id,
                        "pending_id": result.pending_id,
                        "equipment_type": result.extracted.equipment_type if result.extracted else None,
                        "brand_name": result.extracted.brand_name if result.extracted else None,
                    }, ensure_ascii=False)
                )
                session.add(log)

            return PendingEquipmentSubmitResponse(
                success=True,
                pending_id=result.pending_id,
                message=result.message,
                extracted_data=result.extracted.to_dict() if result.extracted else None
            )
        else:
            logger.warning(
                f"Worker {worker_id} 提交待审核数据失败: "
                f"task_id={request.task_id}, error={result.message}"
            )

            return PendingEquipmentSubmitResponse(
                success=False,
                pending_id=None,
                message=result.message,
                extracted_data=result.extracted.to_dict() if result.extracted else None
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交待审核数据失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/submit-pending-batch",
    response_model=dict,
    summary="批量提交待审核装备数据",
    description="Worker 批量提交 OCR 识别结果（从一张图片识别出多个装备）"
)
async def submit_pending_equipment_batch(
    request: PendingEquipmentSubmit,
    worker_id: str = Depends(verify_worker_token)
):
    """
    Worker 批量提交待审核装备数据

    用于一张截图中包含多个商品的情况。

    Returns:
        dict: 包含成功和失败的结果列表
    """
    try:
        # 验证请求中的 worker_id 与 token 中的一致
        if request.worker_id != worker_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Worker ID 不匹配"
            )

        # 验证任务存在
        db = get_crawler_db()
        with db.session_scope() as session:
            task = session.query(CrawlerTask).filter(
                CrawlerTask.id == request.task_id
            ).first()

            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"任务不存在: {request.task_id}"
                )

        # 调用 EquipmentImportAgent 批量提取
        from packages.agents.equipment_import import EquipmentImportAgent

        agent = EquipmentImportAgent(
            model_provider="zhipu",
            enable_logging=True,
            enable_compression=True,
            enable_monitoring=True
        )

        # 使用 batch_extract_and_save 批量提取并保存
        results = agent.batch_extract_and_save(
            text=request.ocr_text,
            source_type=request.source_type,
            source_url=request.source_url
        )

        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count

        logger.info(
            f"Worker {worker_id} 批量提交待审核数据: "
            f"task_id={request.task_id}, success={success_count}, failed={failed_count}"
        )

        # 记录日志
        with db.session_scope() as session:
            log = CrawlerLog(
                task_id=request.task_id,
                level=LogLevel.INFO,
                message=f"Worker 批量提交待审核数据，成功 {success_count} 条，失败 {failed_count} 条",
                details=json.dumps({
                    "worker_id": worker_id,
                    "success_count": success_count,
                    "failed_count": failed_count,
                }, ensure_ascii=False)
            )
            session.add(log)

        return {
            "success": True,
            "total": len(results),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": [
                {
                    "success": r.success,
                    "pending_id": r.pending_id,
                    "message": r.message,
                    "equipment_type": r.extracted.equipment_type if r.extracted else None,
                    "model": r.extracted.model if r.extracted else None,
                }
                for r in results
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量提交待审核数据失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========== Worker 图片上传 ==========

@router.post(
    "/upload-images",
    response_model=dict,
    summary="Worker 上传爬虫图片",
    description="Worker 批量上传爬虫任务图片（使用 Worker Token 认证）"
)
async def worker_upload_images(
    task_id: int = Form(..., description="任务ID"),
    products: str = Form(..., description="产品列表JSON字符串"),
    files: List[UploadFile] = File(..., description="图片文件列表"),
    worker_id: str = Depends(verify_worker_token)
):
    """
    Worker 批量上传爬虫图片

    - 使用 X-Worker-Token 认证（不需要 JWT）
    - 复用 CrawlerUploadService 处理上传逻辑

    文件名格式: {product_index}_{image_index}.{ext}
    """
    try:
        from apps.api.services.crawler_upload_service import CrawlerUploadService
        from apps.api.schemas.crawler import CrawlerProductUpload, CrawlerUploadResponse

        # 解析产品 JSON
        try:
            products_data = json.loads(products)
            product_list = [CrawlerProductUpload(**p) for p in products_data]
        except (json.JSONDecodeError, Exception) as e:
            raise HTTPException(
                status_code=400,
                detail=f"products JSON 解析失败: {str(e)}"
            )

        # 验证任务存在且属于该 Worker
        db = get_crawler_db()
        with db.session_scope() as session:
            task = session.query(CrawlerTask).filter(
                CrawlerTask.id == task_id
            ).first()

            if not task:
                raise HTTPException(
                    status_code=404,
                    detail=f"任务不存在: task_id={task_id}"
                )

            # 验证任务分配给该 Worker
            config = json.loads(task.config) if task.config else {}
            assigned_worker = config.get("_assigned_worker")
            if assigned_worker and assigned_worker != worker_id:
                raise HTTPException(
                    status_code=403,
                    detail=f"任务不属于该 Worker (分配给: {assigned_worker})"
                )

        # 调用上传服务
        service = CrawlerUploadService()
        result = service.upload_products(
            task_id=task_id,
            products=product_list,
            files=files
        )

        logger.info(
            f"Worker {worker_id} 上传图片完成: task_id={task_id}, "
            f"uploaded={result.uploaded_count}, skipped={result.skipped_count}"
        )

        return {
            "success": result.success,
            "task_id": result.task_id,
            "uploaded_count": result.uploaded_count,
            "skipped_count": result.skipped_count,
            "failed_count": result.failed_count,
            "pending_ids": result.pending_ids,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Worker 上传图片失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"上传失败: {str(e)}"
        )
