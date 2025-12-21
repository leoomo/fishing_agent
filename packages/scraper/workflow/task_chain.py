"""
任务链管理器

管理工作流任务依赖和后续任务触发
"""

import json
import logging
from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Session

from ..models import CrawlerTask, TaskStatus

logger = logging.getLogger(__name__)


class TaskChainManager:
    """
    任务链管理器

    管理工作流中任务的依赖关系和自动触发
    """

    def __init__(self, db_session: Session):
        """
        初始化任务链管理器

        Args:
            db_session: 数据库会话
        """
        self.db = db_session

    def on_task_complete(self, task: CrawlerTask):
        """
        任务完成时的回调 - 触发依赖此任务的后续任务

        Args:
            task: 已完成的任务
        """
        if not task.workflow_id:
            logger.debug(f"任务 {task.id} 不属于工作流，跳过后续任务触发")
            return

        logger.info(
            f"任务 {task.id} 完成 (workflow={task.workflow_id}, step={task.step_order})，"
            f"检查后续任务..."
        )

        # 查找依赖此任务的待执行任务
        pending_tasks = self._find_dependent_tasks(task)

        for pending_task in pending_tasks:
            if self._all_dependencies_satisfied(pending_task):
                self._submit_task(pending_task)

    def _find_dependent_tasks(self, completed_task: CrawlerTask) -> List[CrawlerTask]:
        """
        查找依赖已完成任务的待执行任务

        Args:
            completed_task: 已完成的任务

        Returns:
            依赖此任务的待执行任务列表
        """
        # 获取同一工作流中的所有待执行任务
        workflow_tasks = self.db.query(CrawlerTask).filter(
            CrawlerTask.workflow_id == completed_task.workflow_id,
            CrawlerTask.status == TaskStatus.PENDING
        ).all()

        dependent_tasks = []

        for task in workflow_tasks:
            # 检查 step_config 中的依赖关系
            if task.step_config:
                try:
                    step_config = json.loads(task.step_config)
                    depends_on = step_config.get('depends_on', [])

                    # 检查是否依赖已完成的任务
                    completed_ref = f"step_{completed_task.step_order}"
                    if completed_task.id in depends_on or completed_ref in depends_on:
                        dependent_tasks.append(task)

                except json.JSONDecodeError:
                    logger.warning(f"任务 {task.id} 的 step_config 解析失败")
                    continue
            else:
                # 没有显式依赖配置，使用简单的顺序依赖
                if task.step_order == completed_task.step_order + 1:
                    dependent_tasks.append(task)

        logger.debug(
            f"找到 {len(dependent_tasks)} 个依赖任务 {completed_task.id} 的待执行任务"
        )

        return dependent_tasks

    def _all_dependencies_satisfied(self, task: CrawlerTask) -> bool:
        """
        检查任务的所有依赖是否都已满足

        Args:
            task: 要检查的任务

        Returns:
            True 如果所有依赖都已满足
        """
        if not task.step_config:
            # 没有显式依赖，检查前一步骤是否完成
            if task.step_order > 0:
                prev_task = self.db.query(CrawlerTask).filter(
                    CrawlerTask.workflow_id == task.workflow_id,
                    CrawlerTask.step_order == task.step_order - 1
                ).first()

                if prev_task and prev_task.status != TaskStatus.SUCCESS:
                    return False

            return True

        try:
            step_config = json.loads(task.step_config)
            depends_on = step_config.get('depends_on', [])

            if not depends_on:
                return True

            for dep in depends_on:
                # 解析依赖引用
                if isinstance(dep, str) and dep.startswith('step_'):
                    dep_order = int(dep.split('_')[1])
                    dep_task = self.db.query(CrawlerTask).filter(
                        CrawlerTask.workflow_id == task.workflow_id,
                        CrawlerTask.step_order == dep_order
                    ).first()
                else:
                    # 直接使用任务 ID
                    dep_task = self.db.query(CrawlerTask).filter(
                        CrawlerTask.id == dep
                    ).first()

                if not dep_task or dep_task.status != TaskStatus.SUCCESS:
                    logger.debug(f"任务 {task.id} 的依赖 {dep} 未满足")
                    return False

            return True

        except (json.JSONDecodeError, ValueError, IndexError) as e:
            logger.warning(f"解析任务 {task.id} 的依赖配置失败: {e}")
            return False

    def _submit_task(self, task: CrawlerTask):
        """
        提交任务到执行队列

        Args:
            task: 要提交的任务
        """
        try:
            # 延迟导入避免循环引用
            from packages.scraper.executor.task_queue import get_task_queue

            task_queue = get_task_queue()

            # 获取任务配置
            config = json.loads(task.config) if task.config else {}

            # 标记任务为运行中
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.utcnow()
            self.db.commit()

            # 提交到队列（工作流任务优先级较高）
            task_queue.submit(
                task_id=task.id,
                priority=2,
                config=config
            )

            logger.info(f"工作流后续任务已提交: task_id={task.id}")

        except Exception as e:
            logger.error(f"提交工作流任务 {task.id} 失败: {e}")
            # 重置任务状态
            task.status = TaskStatus.PENDING
            self.db.commit()

    def get_workflow_status(self, workflow_id: str) -> dict:
        """
        获取工作流的整体状态

        Args:
            workflow_id: 工作流 ID

        Returns:
            工作流状态摘要
        """
        tasks = self.db.query(CrawlerTask).filter(
            CrawlerTask.workflow_id == workflow_id
        ).order_by(CrawlerTask.step_order).all()

        if not tasks:
            return {"error": "工作流不存在"}

        status_counts = {
            "pending": 0,
            "running": 0,
            "success": 0,
            "failed": 0
        }

        for task in tasks:
            status_key = task.status.value.lower() if hasattr(task.status, 'value') else str(task.status).lower()
            if status_key in status_counts:
                status_counts[status_key] += 1

        # 确定整体状态
        if status_counts["failed"] > 0:
            overall_status = "failed"
        elif status_counts["running"] > 0:
            overall_status = "running"
        elif status_counts["pending"] > 0:
            overall_status = "pending"
        else:
            overall_status = "completed"

        return {
            "workflow_id": workflow_id,
            "workflow_name": tasks[0].workflow_name if tasks else None,
            "total_tasks": len(tasks),
            "status": overall_status,
            "status_counts": status_counts,
            "tasks": [
                {
                    "id": t.id,
                    "step_order": t.step_order,
                    "task_type": t.task_type,
                    "status": t.status.value if hasattr(t.status, 'value') else str(t.status)
                }
                for t in tasks
            ]
        }
