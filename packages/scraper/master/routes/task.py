"""
Task Operation Routes

任务操作API路由 (Worker端使用)
"""

import json
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db_session
from ...models import CrawlerNode, CrawlerTask, TaskStatus, NodeTaskAssignment
from ..schemas.node import (
    TaskClaimRequest,
    TaskProgressRequest,
    TaskCompleteRequest,
    TaskFailRequest,
    TaskInfo,
    TaskListResponse,
)
from ..auth.node_auth import get_current_node

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/nodes", tags=["tasks"])


def _task_to_info(task: CrawlerTask) -> TaskInfo:
    """Convert CrawlerTask to TaskInfo schema"""
    config = None
    if task.config:
        try:
            config = json.loads(task.config) if isinstance(task.config, str) else task.config
        except (json.JSONDecodeError, TypeError):
            config = None

    return TaskInfo(
        id=task.id,
        task_type=task.task_type,
        platform=task.platform,
        shop_url=task.shop_url,
        status=task.status.value if hasattr(task.status, 'value') else str(task.status),
        priority=task.priority or 0,
        progress=task.progress or 0,
        timeout_seconds=task.timeout_seconds or 300,
        max_retries=task.max_retries or 3,
        retry_count=task.retry_count or 0,
        config=config,
        assigned_node_id=task.assigned_node_id,
        assigned_at=task.assigned_at,
        claimed_at=task.claimed_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("/{node_id}/tasks", response_model=TaskListResponse)
async def get_available_tasks(
    node_id: str,
    limit: int = 10,
    db: Session = Depends(get_db_session),
    current_node: CrawlerNode = Depends(get_current_node),
):
    """
    获取可用任务列表

    返回已分配给该节点但未认领的任务
    """
    # 验证node_id匹配
    if current_node.node_id != node_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Node ID mismatch",
        )

    # 查询已分配给该节点的待处理任务
    tasks = db.query(CrawlerTask).filter(
        CrawlerTask.assigned_node_id == current_node.id,
        CrawlerTask.status == TaskStatus.PENDING,
        CrawlerTask.claimed_at.is_(None),
    ).order_by(
        CrawlerTask.priority.desc(),
        CrawlerTask.created_at.asc(),
    ).limit(limit).all()

    return TaskListResponse(
        total=len(tasks),
        tasks=[_task_to_info(t) for t in tasks],
    )


@router.post("/{node_id}/tasks/{task_id}/claim", response_model=TaskInfo)
async def claim_task(
    node_id: str,
    task_id: int,
    db: Session = Depends(get_db_session),
    current_node: CrawlerNode = Depends(get_current_node),
):
    """
    认领任务

    Worker认领已分配的任务，开始执行
    """
    # 验证node_id匹配
    if current_node.node_id != node_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Node ID mismatch",
        )

    # 查找任务
    task = db.query(CrawlerTask).filter(
        CrawlerTask.id == task_id,
    ).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # 验证任务状态
    if task.status != TaskStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task is not pending, current status: {task.status}",
        )

    # 验证任务是否分配给该节点
    if task.assigned_node_id != current_node.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Task is not assigned to this node",
        )

    # 验证任务未被认领
    if task.claimed_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task already claimed",
        )

    # 认领任务
    now = datetime.utcnow()
    task.claimed_at = now
    task.started_at = now
    task.status = TaskStatus.RUNNING

    # 记录分配历史
    assignment = NodeTaskAssignment(
        task_id=task.id,
        node_id=current_node.id,
        action="claimed",
        action_at=now,
    )
    db.add(assignment)

    # 更新节点当前任务数
    current_node.current_tasks += 1

    db.commit()
    db.refresh(task)

    logger.info(f"Task {task_id} claimed by node {node_id}")

    return _task_to_info(task)


@router.put("/{node_id}/tasks/{task_id}/progress")
async def update_task_progress(
    node_id: str,
    task_id: int,
    request: TaskProgressRequest,
    db: Session = Depends(get_db_session),
    current_node: CrawlerNode = Depends(get_current_node),
):
    """
    上报任务进度
    """
    # 验证node_id匹配
    if current_node.node_id != node_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Node ID mismatch",
        )

    # 查找任务
    task = db.query(CrawlerTask).filter(
        CrawlerTask.id == task_id,
        CrawlerTask.assigned_node_id == current_node.id,
    ).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not assigned to this node",
        )

    # 验证任务状态
    if task.status != TaskStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task is not running, current status: {task.status}",
        )

    # 更新进度
    task.progress = request.progress

    # 更新进度消息到result_summary
    if request.message or request.current_items is not None:
        result_summary = json.loads(task.result_summary) if task.result_summary else {}
        if request.message:
            result_summary['progress_message'] = request.message
        if request.current_items is not None:
            result_summary['current_items'] = request.current_items
        if request.total_items is not None:
            result_summary['total_items'] = request.total_items
        task.result_summary = json.dumps(result_summary)

    db.commit()

    return {"message": "Progress updated", "progress": request.progress}


@router.post("/{node_id}/tasks/{task_id}/complete")
async def complete_task(
    node_id: str,
    task_id: int,
    request: TaskCompleteRequest,
    db: Session = Depends(get_db_session),
    current_node: CrawlerNode = Depends(get_current_node),
):
    """
    上报任务完成
    """
    # 验证node_id匹配
    if current_node.node_id != node_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Node ID mismatch",
        )

    # 查找任务
    task = db.query(CrawlerTask).filter(
        CrawlerTask.id == task_id,
        CrawlerTask.assigned_node_id == current_node.id,
    ).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not assigned to this node",
        )

    # 验证任务状态
    if task.status not in [TaskStatus.RUNNING, TaskStatus.PENDING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task cannot be completed, current status: {task.status}",
        )

    now = datetime.utcnow()

    # 更新任务状态
    task.status = TaskStatus.COMPLETED
    task.completed_at = now
    task.progress = 100
    task.success_count = request.success_items
    task.fail_count = request.failed_items
    task.total_count = request.total_items
    task.duplicate_count = request.duplicate_items

    # 保存结果摘要
    result_summary = request.result_summary or {}
    if request.image_stats:
        result_summary['image_stats'] = request.image_stats
    task.result_summary = json.dumps(result_summary)

    # 保存结果数据
    if request.result_data:
        task.result_data = json.dumps(request.result_data)

    # 计算任务执行时长
    if task.started_at:
        duration = (now - task.started_at).total_seconds()
    else:
        duration = 0

    # 记录分配历史
    assignment = NodeTaskAssignment(
        task_id=task.id,
        node_id=current_node.id,
        action="completed",
        action_at=now,
        action_reason=f"success:{request.success_items}, failed:{request.failed_items}",
    )
    db.add(assignment)

    # 更新节点统计
    current_node.current_tasks = max(0, current_node.current_tasks - 1)
    current_node.total_completed += 1

    # 更新平均任务时长
    total_tasks = current_node.total_completed + current_node.total_failed
    if total_tasks > 0:
        old_avg = current_node.avg_task_duration or 0
        current_node.avg_task_duration = (old_avg * (total_tasks - 1) + duration) / total_tasks

    # 更新成功率
    if total_tasks > 0:
        current_node.success_rate = (current_node.total_completed / total_tasks) * 100

    db.commit()

    logger.info(f"Task {task_id} completed by node {node_id}: "
                f"success={request.success_items}, failed={request.failed_items}")

    return {
        "message": "Task completed",
        "task_id": task_id,
        "duration_seconds": duration,
    }


@router.post("/{node_id}/tasks/{task_id}/fail")
async def fail_task(
    node_id: str,
    task_id: int,
    request: TaskFailRequest,
    db: Session = Depends(get_db_session),
    current_node: CrawlerNode = Depends(get_current_node),
):
    """
    上报任务失败
    """
    # 验证node_id匹配
    if current_node.node_id != node_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Node ID mismatch",
        )

    # 查找任务
    task = db.query(CrawlerTask).filter(
        CrawlerTask.id == task_id,
        CrawlerTask.assigned_node_id == current_node.id,
    ).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not assigned to this node",
        )

    now = datetime.utcnow()

    # 记录错误信息
    task.error_message = request.error_message
    if request.error_details:
        error_details = json.loads(task.error_details) if task.error_details else {}
        error_details.update(request.error_details)
        task.error_details = json.dumps(error_details)

    # 检查是否应该重试
    should_retry = request.should_retry and task.retry_count < task.max_retries

    if should_retry:
        # 重试: 重置状态为pending，等待重新分配
        task.status = TaskStatus.PENDING
        task.retry_count += 1
        task.claimed_at = None
        task.started_at = None
        task.assigned_node_id = None  # 清除分配，等待重新调度
        task.assigned_at = None

        action = "retry"
        message = f"Task will be retried (attempt {task.retry_count}/{task.max_retries})"
    else:
        # 标记为失败
        task.status = TaskStatus.FAILED
        task.completed_at = now

        action = "failed"
        message = "Task failed permanently"

    # 记录分配历史
    assignment = NodeTaskAssignment(
        task_id=task.id,
        node_id=current_node.id,
        action=action,
        action_at=now,
        action_reason=request.error_message[:500] if request.error_message else None,
    )
    db.add(assignment)

    # 更新节点统计
    current_node.current_tasks = max(0, current_node.current_tasks - 1)
    if not should_retry:
        current_node.total_failed += 1

        # 更新成功率
        total_tasks = current_node.total_completed + current_node.total_failed
        if total_tasks > 0:
            current_node.success_rate = (current_node.total_completed / total_tasks) * 100

    db.commit()

    logger.warning(f"Task {task_id} failed on node {node_id}: {request.error_message}")

    return {
        "message": message,
        "task_id": task_id,
        "will_retry": should_retry,
        "retry_count": task.retry_count if should_retry else None,
    }
