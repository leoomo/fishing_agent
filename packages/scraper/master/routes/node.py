"""
Node Management Routes

节点管理API路由
"""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from ...database import get_db_session
from ...models import CrawlerNode, NodeStatus, CrawlerTask, TaskStatus, NodeTaskAssignment
from ..schemas.node import (
    NodeRegisterRequest,
    NodeRegisterResponse,
    NodeAuthRequest,
    NodeAuthResponse,
    HeartbeatRequest,
    HeartbeatResponse,
    NodeInfo,
    NodeListResponse,
    NodeUpdateRequest,
)
from ..auth.node_auth import (
    create_node_token,
    generate_node_secret,
    hash_node_secret,
    verify_node_secret,
    get_current_node,
    require_authenticated,
    NodeTokenPayload,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/nodes", tags=["nodes"])


# ========== 节点注册与认证 ==========

@router.post("/register", response_model=NodeRegisterResponse)
async def register_node(
    request: NodeRegisterRequest,
    req: Request,
    db: Session = Depends(get_db_session),
):
    """
    注册新的Worker节点

    Returns:
        NodeRegisterResponse: 包含node_id, node_secret(仅返回一次), token
    """
    import uuid

    # 生成唯一节点ID
    node_id = str(uuid.uuid4())

    # 生成节点密钥
    node_secret = generate_node_secret()
    secret_hash = hash_node_secret(node_secret)

    # 获取客户端IP
    client_ip = req.client.host if req.client else None

    # 创建节点记录
    node = CrawlerNode(
        node_id=node_id,
        node_name=request.node_name,
        node_secret_hash=secret_hash,
        ip_address=client_ip,
        location=request.location,
        capabilities=request.capabilities,
        max_concurrent_tasks=request.max_concurrent_tasks,
        worker_version=request.worker_version,
        status=NodeStatus.ONLINE,
        last_heartbeat=datetime.utcnow(),
    )

    db.add(node)
    db.commit()
    db.refresh(node)

    # 生成初始Token
    token, expires_at = create_node_token(node_id, request.capabilities)

    logger.info(f"Node registered: {node_id} ({request.node_name}) from {client_ip}")

    return NodeRegisterResponse(
        node_id=node_id,
        node_secret=node_secret,  # 仅返回一次
        token=token,
        expires_at=expires_at,
        heartbeat_interval=30,
    )


@router.post("/auth/token", response_model=NodeAuthResponse)
async def authenticate_node(
    request: NodeAuthRequest,
    db: Session = Depends(get_db_session),
):
    """
    节点认证获取Token

    使用node_id和node_secret换取访问Token
    """
    # 查找节点
    node = db.query(CrawlerNode).filter(
        CrawlerNode.node_id == request.node_id
    ).first()

    if node is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Node not found",
        )

    # 验证密钥
    if not verify_node_secret(request.node_secret, node.node_secret_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid node secret",
        )

    # 更新节点状态
    node.status = NodeStatus.ONLINE
    node.last_heartbeat = datetime.utcnow()
    db.commit()

    # 生成Token
    capabilities = node.capabilities if isinstance(node.capabilities, list) else ["all"]
    token, expires_at = create_node_token(node.node_id, capabilities)

    logger.info(f"Node authenticated: {node.node_id}")

    return NodeAuthResponse(
        token=token,
        expires_at=expires_at,
        heartbeat_interval=node.heartbeat_interval or 30,
    )


# ========== 心跳 ==========

@router.post("/{node_id}/heartbeat", response_model=HeartbeatResponse)
async def node_heartbeat(
    node_id: str,
    request: HeartbeatRequest,
    db: Session = Depends(get_db_session),
    current_node: CrawlerNode = Depends(get_current_node),
):
    """
    节点心跳

    定期上报状态，获取新分配的任务
    """
    # 验证node_id匹配
    if current_node.node_id != node_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Node ID mismatch",
        )

    # 更新节点状态
    current_node.last_heartbeat = datetime.utcnow()
    current_node.current_tasks = request.current_tasks

    if request.worker_version:
        current_node.worker_version = request.worker_version

    # 更新资源使用率（存储在tags JSON中）
    import json
    tags = json.loads(current_node.tags) if current_node.tags else {}
    if request.cpu_usage is not None:
        tags['cpu_usage'] = request.cpu_usage
    if request.memory_usage is not None:
        tags['memory_usage'] = request.memory_usage
    if request.disk_usage is not None:
        tags['disk_usage'] = request.disk_usage
    current_node.tags = json.dumps(tags)

    # 检查是否需要排空
    response_status = "ok"
    message = None

    if current_node.status == NodeStatus.DRAINING:
        response_status = "drain"
        message = "Node is draining, please finish current tasks"
    elif current_node.status == NodeStatus.MAINTENANCE:
        response_status = "shutdown"
        message = "Node is in maintenance mode"

    # 查找新分配的任务（已分配但未认领）
    assigned_tasks = db.query(CrawlerTask).filter(
        CrawlerTask.assigned_node_id == current_node.id,
        CrawlerTask.status == TaskStatus.PENDING,
        CrawlerTask.claimed_at.is_(None),
    ).all()

    assigned_task_ids = [t.id for t in assigned_tasks]

    # 查找需要取消的任务（被重新分配到其他节点的）
    cancel_task_ids = []
    if request.running_task_ids:
        for task_id in request.running_task_ids:
            task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
            if task and task.assigned_node_id != current_node.id:
                cancel_task_ids.append(task_id)

    db.commit()

    return HeartbeatResponse(
        status=response_status,
        next_heartbeat_seconds=current_node.heartbeat_interval or 30,
        assigned_tasks=assigned_task_ids,
        cancel_tasks=cancel_task_ids,
        message=message,
    )


# ========== 节点管理 ==========

@router.get("", response_model=NodeListResponse)
async def list_nodes(
    status: Optional[str] = None,
    capability: Optional[str] = None,
    db: Session = Depends(get_db_session),
    _: NodeTokenPayload = Depends(require_authenticated),
):
    """
    获取节点列表
    """
    query = db.query(CrawlerNode)

    if status:
        try:
            node_status = NodeStatus(status)
            query = query.filter(CrawlerNode.status == node_status)
        except ValueError:
            pass

    if capability:
        # 简单的JSON包含查询
        query = query.filter(CrawlerNode.capabilities.contains(capability))

    nodes = query.order_by(CrawlerNode.created_at.desc()).all()

    node_infos = []
    for node in nodes:
        # 计算成功率
        total = node.total_completed + node.total_failed
        success_rate = (node.total_completed / total * 100) if total > 0 else 100.0

        node_infos.append(NodeInfo(
            id=node.id,
            node_id=node.node_id,
            node_name=node.node_name,
            status=node.status.value,
            ip_address=node.ip_address,
            location=node.location,
            capabilities=node.capabilities if isinstance(node.capabilities, list) else [],
            max_concurrent_tasks=node.max_concurrent_tasks,
            current_tasks=node.current_tasks,
            total_completed=node.total_completed,
            total_failed=node.total_failed,
            success_rate=success_rate,
            avg_task_duration=node.avg_task_duration,
            worker_version=node.worker_version,
            last_heartbeat=node.last_heartbeat,
            created_at=node.created_at,
            updated_at=node.updated_at,
        ))

    return NodeListResponse(total=len(node_infos), nodes=node_infos)


@router.get("/{node_id}", response_model=NodeInfo)
async def get_node(
    node_id: str,
    db: Session = Depends(get_db_session),
    _: NodeTokenPayload = Depends(require_authenticated),
):
    """
    获取节点详情
    """
    node = db.query(CrawlerNode).filter(
        CrawlerNode.node_id == node_id
    ).first()

    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )

    total = node.total_completed + node.total_failed
    success_rate = (node.total_completed / total * 100) if total > 0 else 100.0

    return NodeInfo(
        id=node.id,
        node_id=node.node_id,
        node_name=node.node_name,
        status=node.status.value,
        ip_address=node.ip_address,
        location=node.location,
        capabilities=node.capabilities if isinstance(node.capabilities, list) else [],
        max_concurrent_tasks=node.max_concurrent_tasks,
        current_tasks=node.current_tasks,
        total_completed=node.total_completed,
        total_failed=node.total_failed,
        success_rate=success_rate,
        avg_task_duration=node.avg_task_duration,
        worker_version=node.worker_version,
        last_heartbeat=node.last_heartbeat,
        created_at=node.created_at,
        updated_at=node.updated_at,
    )


@router.put("/{node_id}", response_model=NodeInfo)
async def update_node(
    node_id: str,
    request: NodeUpdateRequest,
    db: Session = Depends(get_db_session),
    _: NodeTokenPayload = Depends(require_authenticated),
):
    """
    更新节点配置
    """
    node = db.query(CrawlerNode).filter(
        CrawlerNode.node_id == node_id
    ).first()

    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )

    # 更新字段
    if request.node_name is not None:
        node.node_name = request.node_name
    if request.capabilities is not None:
        node.capabilities = request.capabilities
    if request.max_concurrent_tasks is not None:
        node.max_concurrent_tasks = request.max_concurrent_tasks
    if request.location is not None:
        node.location = request.location
    if request.tags is not None:
        import json
        node.tags = json.dumps(request.tags)
    if request.config is not None:
        import json
        node.config = json.dumps(request.config)

    db.commit()
    db.refresh(node)

    total = node.total_completed + node.total_failed
    success_rate = (node.total_completed / total * 100) if total > 0 else 100.0

    return NodeInfo(
        id=node.id,
        node_id=node.node_id,
        node_name=node.node_name,
        status=node.status.value,
        ip_address=node.ip_address,
        location=node.location,
        capabilities=node.capabilities if isinstance(node.capabilities, list) else [],
        max_concurrent_tasks=node.max_concurrent_tasks,
        current_tasks=node.current_tasks,
        total_completed=node.total_completed,
        total_failed=node.total_failed,
        success_rate=success_rate,
        avg_task_duration=node.avg_task_duration,
        worker_version=node.worker_version,
        last_heartbeat=node.last_heartbeat,
        created_at=node.created_at,
        updated_at=node.updated_at,
    )


@router.delete("/{node_id}")
async def delete_node(
    node_id: str,
    db: Session = Depends(get_db_session),
    _: NodeTokenPayload = Depends(require_authenticated),
):
    """
    删除节点
    """
    node = db.query(CrawlerNode).filter(
        CrawlerNode.node_id == node_id
    ).first()

    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )

    # 检查是否有正在执行的任务
    running_tasks = db.query(CrawlerTask).filter(
        CrawlerTask.assigned_node_id == node.id,
        CrawlerTask.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING]),
    ).count()

    if running_tasks > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Node has {running_tasks} running tasks, please drain first",
        )

    db.delete(node)
    db.commit()

    logger.info(f"Node deleted: {node_id}")

    return {"message": "Node deleted successfully"}


@router.post("/{node_id}/drain")
async def drain_node(
    node_id: str,
    db: Session = Depends(get_db_session),
    _: NodeTokenPayload = Depends(require_authenticated),
):
    """
    排空节点

    设置节点为排空状态，不再分配新任务，等待当前任务完成
    """
    node = db.query(CrawlerNode).filter(
        CrawlerNode.node_id == node_id
    ).first()

    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )

    node.status = NodeStatus.DRAINING
    db.commit()

    logger.info(f"Node draining: {node_id}")

    return {"message": "Node is now draining", "status": "draining"}
