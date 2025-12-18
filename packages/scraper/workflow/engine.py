"""
工作流引擎

负责执行工作流，管理DAG依赖关系和参数替换
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field

from packages.scraper.models import CrawlerTask
from packages.scraper.executor.crawler_executor import CrawlerExecutor
from packages.scraper.executor.task_queue import CrawlerTaskQueue

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """工作流步骤"""
    id: str
    name: str
    task_type: str
    order: int
    config: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)
    max_retries: int = 3
    timeout: int = 3600
    status: str = "pending"  # pending, ready, running, success, failed, skipped
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    task_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class Workflow:
    """工作流定义"""
    id: str
    name: str
    description: str
    steps: List[WorkflowStep] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    status: str = "created"  # created, running, completed, failed, cancelled
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)  # 用于存储步骤间的共享数据


class WorkflowEngine:
    """
    工作流引擎

    负责执行工作流，管理DAG依赖关系
    """

    def __init__(self, db_session, task_queue: Optional[CrawlerTaskQueue] = None):
        """
        初始化工作流引擎

        Args:
            db_session: 数据库会话
            task_queue: 任务队列（可选）
        """
        self.db = db_session
        self.task_queue = task_queue
        self.active_workflows: Dict[str, Workflow] = {}

    def create_workflow(self, workflow_def: Dict[str, Any], params: Dict[str, Any] = None) -> Workflow:
        """
        创建工作流实例

        Args:
            workflow_def: 工作流定义（JSON）
            params: 执行参数

        Returns:
            工作流实例
        """
        # 生成唯一ID
        workflow_id = str(uuid.uuid4())

        # 解析步骤
        steps = []
        for step_def in workflow_def.get("steps", []):
            step = WorkflowStep(
                id=step_def["id"],
                name=step_def["name"],
                task_type=step_def["task_type"],
                order=step_def["order"],
                config=step_def.get("config", {}),
                depends_on=step_def.get("depends_on", []),
                max_retries=step_def.get("max_retries", 3),
                timeout=step_def.get("timeout", 3600)
            )
            steps.append(step)

        # 创建工作流
        workflow = Workflow(
            id=workflow_id,
            name=workflow_def.get("name", "未命名工作流"),
            description=workflow_def.get("description", ""),
            steps=steps,
            params=params or {},
            context={}
        )

        # 初始化上下文，包含参数
        workflow.context.update(params or {})

        logger.info(f"创建工作流: {workflow.name} (ID: {workflow_id})")
        return workflow

    def execute_workflow(self, workflow: Workflow) -> bool:
        """
        执行工作流

        Args:
            workflow: 工作流实例

        Returns:
            是否执行成功
        """
        logger.info(f"开始执行工作流: {workflow.name} (ID: {workflow.id})")
        workflow.status = "running"
        workflow.started_at = datetime.utcnow()
        self.active_workflows[workflow.id] = workflow

        try:
            # 排序步骤
            sorted_steps = sorted(workflow.steps, key=lambda x: x.order)

            # 执行循环，直到所有步骤完成或失败
            max_iterations = len(workflow.steps) * 2  # 防止死循环
            iteration = 0

            while iteration < max_iterations:
                iteration += 1
                progress_made = False

                for step in sorted_steps:
                    if step.status == "pending":
                        # 检查依赖是否满足
                        if self._check_dependencies(workflow, step):
                            # 准备执行步骤
                            step.status = "ready"
                            self._prepare_step(workflow, step)
                            progress_made = True

                    elif step.status == "ready":
                        # 执行步骤
                        logger.info(f"执行步骤: {step.name} (ID: {step.id})")
                        success = self._execute_step(workflow, step)
                        progress_made = True

                        if success:
                            step.status = "success"
                            step.end_time = datetime.utcnow()
                            logger.info(f"步骤完成: {step.name}")
                        else:
                            step.status = "failed"
                            step.end_time = datetime.utcnow()
                            logger.error(f"步骤失败: {step.name} - {step.error}")

                # 检查是否所有步骤都已完成
                if all(s.status in ["success", "failed", "skipped"] for s in workflow.steps):
                    break

            # 检查执行结果
            completed_steps = [s for s in workflow.steps if s.status == "success"]
            failed_steps = [s for s in workflow.steps if s.status == "failed"]

            if not failed_steps:
                workflow.status = "completed"
                workflow.completed_at = datetime.utcnow()
                logger.info(f"工作流执行成功: {workflow.name} - {len(completed_steps)} 个步骤完成")
                return True
            else:
                workflow.status = "failed"
                workflow.completed_at = datetime.utcnow()
                logger.error(f"工作流执行失败: {workflow.name} - {len(failed_steps)} 个步骤失败")
                return False

        except Exception as e:
            logger.error(f"工作流执行异常: {e}", exc_info=True)
            workflow.status = "failed"
            workflow.completed_at = datetime.utcnow()
            return False

        finally:
            # 清理活动工作流
            if workflow.id in self.active_workflows:
                del self.active_workflows[workflow.id]

    def _check_dependencies(self, workflow: Workflow, step: WorkflowStep) -> bool:
        """
        检查步骤的依赖是否满足

        Args:
            workflow: 工作流实例
            step: 要检查的步骤

        Returns:
            依赖是否满足
        """
        for dep_id in step.depends_on:
            # 查找依赖的步骤
            dep_step = next((s for s in workflow.steps if s.id == dep_id), None)
            if not dep_step:
                logger.error(f"步骤 {step.id} 依赖的步骤 {dep_id} 不存在")
                return False

            if dep_step.status != "success":
                logger.debug(f"步骤 {step.id} 等待依赖 {dep_id} 完成 (当前状态: {dep_step.status})")
                return False

        return True

    def _prepare_step(self, workflow: Workflow, step: WorkflowStep):
        """
        准备执行步骤，进行参数替换

        Args:
            workflow: 工作流实例
            step: 要准备的步骤
        """
        # 合并工作流参数和步骤配置
        merged_config = {}
        merged_config.update(workflow.params)
        merged_config.update(step.config)

        # 参数替换
        replaced_config = self._replace_parameters(merged_config, workflow.context)

        # 更新步骤配置
        step.config = replaced_config

        # 设置平台信息
        if "platform" not in step.config:
            step.config["platform"] = step.task_type

    def _replace_parameters(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        替换配置中的参数占位符

        Args:
            config: 原始配置
            context: 上下文数据

        Returns:
            替换后的配置
        """
        # 转换为JSON字符串进行替换
        config_str = json.dumps(config, ensure_ascii=False)

        # 替换占位符
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                placeholder = f"{{{{{key}}}}}"
                config_str = config_str.replace(placeholder, str(value))
            elif isinstance(value, (list, dict)):
                placeholder = f"{{{{{key}}}}}"
                config_str = config_str.replace(placeholder, json.dumps(value, ensure_ascii=False))

        # 转换回字典
        return json.loads(config_str)

    def _execute_step(self, workflow: Workflow, step: WorkflowStep) -> bool:
        """
        执行单个步骤

        Args:
            workflow: 工作流实例
            step: 要执行的步骤

        Returns:
            是否执行成功
        """
        step.status = "running"
        step.start_time = datetime.utcnow()

        try:
            # 创建数据库任务记录
            task = CrawlerTask(
                task_type=step.task_type,
                task_name=f"[工作流 {workflow.name}] {step.name}",
                status="pending",
                config=json.dumps(step.config, ensure_ascii=False),
                workflow_id=workflow.id,
                workflow_name=workflow.name,
                step_order=step.order,
                step_config=json.dumps({
                    "depends_on": step.depends_on
                }, ensure_ascii=False),
                platform=step.config.get("platform"),
                shop_url=step.config.get("shop_url"),
                max_retries=step.max_retries,
                timeout_seconds=step.timeout
            )

            self.db.add(task)
            self.db.commit()
            step.task_id = task.id

            # 执行任务
            executor = CrawlerExecutor(self.db)
            success = executor.execute(task.id)

            if success:
                # 读取结果
                result_summary = json.loads(task.result_summary or "{}")
                step.result = {
                    "total_items": task.total_items,
                    "success_items": task.success_items,
                    "failed_items": task.failed_items,
                    "duplicate_items": task.duplicate_items,
                    "summary": result_summary
                }

                # 将结果存入上下文，供后续步骤使用
                workflow.context[f"step_{step.id}_result"] = step.result
                workflow.context[f"step_{step.order}_result"] = step.result

            return success

        except Exception as e:
            logger.error(f"步骤执行异常 {step.id}: {e}", exc_info=True)
            step.error = str(e)
            return False

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流状态

        Args:
            workflow_id: 工作流ID

        Returns:
            工作流状态信息
        """
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return None

        return {
            "id": workflow.id,
            "name": workflow.name,
            "status": workflow.status,
            "created_at": workflow.created_at.isoformat(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "steps": [
                {
                    "id": s.id,
                    "name": s.name,
                    "status": s.status,
                    "order": s.order,
                    "task_id": s.task_id,
                    "error": s.error
                }
                for s in workflow.steps
            ]
        }

    def cancel_workflow(self, workflow_id: str) -> bool:
        """
        取消工作流

        Args:
            workflow_id: 工作流ID

        Returns:
            是否成功取消
        """
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return False

        workflow.status = "cancelled"
        workflow.completed_at = datetime.utcnow()

        # 取消所有未开始的步骤
        for step in workflow.steps:
            if step.status in ["pending", "ready"]:
                step.status = "skipped"

        logger.info(f"工作流已取消: {workflow.name} (ID: {workflow_id})")
        return True