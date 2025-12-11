"""
工作流管理器

负责工作流的创建、调度和管理
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from packages.agent_fishing.tools.lure.models.system import (
    CrawlerTask, CrawlerWorkflowTemplate, CrawlerSchedule
)
from packages.agent_fishing.tools.crawler.workflow.engine import WorkflowEngine, Workflow
from packages.agent_fishing.tools.crawler.executor.task_queue import CrawlerTaskQueue

logger = logging.getLogger(__name__)


class WorkflowManager:
    """
    工作流管理器

    管理工作流的生命周期
    """

    def __init__(self, db_session, task_queue: Optional[CrawlerTaskQueue] = None):
        """
        初始化工作流管理器

        Args:
            db_session: 数据库会话
            task_queue: 任务队列
        """
        self.db = db_session
        self.task_queue = task_queue
        self.engine = WorkflowEngine(db_session, task_queue)

    def create_workflow_from_template(self, template_id: int, params: Dict[str, Any]) -> Optional[Workflow]:
        """
        从模板创建工作流

        Args:
            template_id: 模板ID
            params: 执行参数

        Returns:
            工作流实例
        """
        # 获取模板
        template = self.db.query(CrawlerWorkflowTemplate).filter(
            CrawlerWorkflowTemplate.id == template_id
        ).first()

        if not template:
            logger.error(f"工作流模板不存在: {template_id}")
            return None

        try:
            # 解析模板定义
            workflow_def = json.loads(template.template_json)

            # 创建工作流
            workflow = self.engine.create_workflow(workflow_def, params)

            logger.info(f"从模板创建工作流: {template.name} -> {workflow.name}")
            return workflow

        except Exception as e:
            logger.error(f"创建工作流失败: {e}", exc_info=True)
            return None

    def execute_workflow_from_template(self, template_id: int, params: Dict[str, Any]) -> Optional[str]:
        """
        从模板执行工作流

        Args:
            template_id: 模板ID
            params: 执行参数

        Returns:
            工作流ID
        """
        workflow = self.create_workflow_from_template(template_id, params)
        if not workflow:
            return None

        # 更新模板使用次数
        self.db.query(CrawlerWorkflowTemplate).filter(
            CrawlerWorkflowTemplate.id == template_id
        ).update({"usage_count": CrawlerWorkflowTemplate.usage_count + 1})
        self.db.commit()

        # 执行工作流
        success = self.engine.execute_workflow(workflow)
        if success:
            return workflow.id
        else:
            return None

    def execute_custom_workflow(self, workflow_def: Dict[str, Any], params: Dict[str, Any]) -> Optional[str]:
        """
        执行自定义工作流

        Args:
            workflow_def: 工作流定义
            params: 执行参数

        Returns:
            工作流ID
        """
        workflow = self.engine.create_workflow(workflow_def, params)
        if not workflow:
            return None

        success = self.engine.execute_workflow(workflow)
        if success:
            return workflow.id
        else:
            return None

    def save_workflow_template(self, name: str, description: str, workflow_def: Dict[str, Any],
                              category: str = None, is_system: bool = False) -> Optional[int]:
        """
        保存工作流模板

        Args:
            name: 模板名称
            description: 描述
            workflow_def: 工作流定义
            category: 分类
            is_system: 是否系统模板

        Returns:
            模板ID
        """
        try:
            template = CrawlerWorkflowTemplate(
                name=name,
                description=description,
                template_json=json.dumps(workflow_def, ensure_ascii=False),
                category=category,
                is_system=is_system
            )

            self.db.add(template)
            self.db.commit()

            logger.info(f"保存工作流模板: {name} (ID: {template.id})")
            return template.id

        except Exception as e:
            logger.error(f"保存工作流模板失败: {e}", exc_info=True)
            return None

    def get_workflow_templates(self, category: str = None) -> List[Dict[str, Any]]:
        """
        获取工作流模板列表

        Args:
            category: 分类过滤

        Returns:
            模板列表
        """
        query = self.db.query(CrawlerWorkflowTemplate)

        if category:
            query = query.filter(CrawlerWorkflowTemplate.category == category)

        templates = query.all()
        return [template.to_dict() for template in templates]

    def get_workflow_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """
        获取工作流模板详情

        Args:
            template_id: 模板ID

        Returns:
            模板详情
        """
        template = self.db.query(CrawlerWorkflowTemplate).filter(
            CrawlerWorkflowTemplate.id == template_id
        ).first()

        return template.to_dict() if template else None

    def delete_workflow_template(self, template_id: int) -> bool:
        """
        删除工作流模板

        Args:
            template_id: 模板ID

        Returns:
            是否成功删除
        """
        try:
            template = self.db.query(CrawlerWorkflowTemplate).filter(
                CrawlerWorkflowTemplate.id == template_id
            ).first()

            if not template:
                return False

            if template.is_system:
                logger.warning(f"不能删除系统模板: {template.name}")
                return False

            self.db.delete(template)
            self.db.commit()

            logger.info(f"删除工作流模板: {template.name}")
            return True

        except Exception as e:
            logger.error(f"删除工作流模板失败: {e}")
            return False

    def create_schedule(self, name: str, template_id: int, cron_expression: str,
                       params: Dict[str, Any], timezone: str = "Asia/Shanghai",
                       is_enabled: bool = True) -> Optional[int]:
        """
        创建定时调度

        Args:
            name: 调度名称
            template_id: 模板ID
            cron_expression: Cron表达式
            params: 执行参数
            timezone: 时区
            is_enabled: 是否启用

        Returns:
            调度ID
        """
        try:
            schedule = CrawlerSchedule(
                name=name,
                template_id=template_id,
                cron_expression=cron_expression,
                timezone=timezone,
                config=json.dumps(params, ensure_ascii=False),
                is_enabled=is_enabled
            )

            self.db.add(schedule)
            self.db.commit()

            logger.info(f"创建定时调度: {name} (ID: {schedule.id})")
            return schedule.id

        except Exception as e:
            logger.error(f"创建定时调度失败: {e}", exc_info=True)
            return None

    def get_schedules(self, template_id: int = None, is_enabled: bool = None) -> List[Dict[str, Any]]:
        """
        获取定时调度列表

        Args:
            template_id: 模板ID过滤
            is_enabled: 启用状态过滤

        Returns:
            调度列表
        """
        query = self.db.query(CrawlerSchedule)

        if template_id:
            query = query.filter(CrawlerSchedule.template_id == template_id)

        if is_enabled is not None:
            query = query.filter(CrawlerSchedule.is_enabled == is_enabled)

        schedules = query.all()
        return [schedule.to_dict() for schedule in schedules]

    def update_schedule(self, schedule_id: int, **kwargs) -> bool:
        """
        更新定时调度

        Args:
            schedule_id: 调度ID
            **kwargs: 更新字段

        Returns:
            是否成功更新
        """
        try:
            schedule = self.db.query(CrawlerSchedule).filter(
                CrawlerSchedule.id == schedule_id
            ).first()

            if not schedule:
                return False

            # 更新字段
            for key, value in kwargs.items():
                if hasattr(schedule, key):
                    if key == "config" and isinstance(value, dict):
                        value = json.dumps(value, ensure_ascii=False)
                    setattr(schedule, key, value)

            self.db.commit()
            logger.info(f"更新定时调度: {schedule.name}")
            return True

        except Exception as e:
            logger.error(f"更新定时调度失败: {e}")
            return False

    def delete_schedule(self, schedule_id: int) -> bool:
        """
        删除定时调度

        Args:
            schedule_id: 调度ID

        Returns:
            是否成功删除
        """
        try:
            schedule = self.db.query(CrawlerSchedule).filter(
                CrawlerSchedule.id == schedule_id
            ).first()

            if not schedule:
                return False

            self.db.delete(schedule)
            self.db.commit()

            logger.info(f"删除定时调度: {schedule.name}")
            return True

        except Exception as e:
            logger.error(f"删除定时调度失败: {e}")
            return False

    def get_running_workflows(self) -> List[Dict[str, Any]]:
        """
        获取正在运行的工作流列表

        Returns:
            工作流列表
        """
        workflows = []
        for workflow_id, workflow in self.engine.active_workflows.items():
            status = self.engine.get_workflow_status(workflow_id)
            if status and status["status"] == "running":
                workflows.append(status)

        return workflows

    def get_workflow_history(self, workflow_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取工作流历史记录

        Args:
            workflow_id: 工作流ID过滤
            limit: 限制数量

        Returns:
            历史记录列表
        """
        # 查询数据库中的工作流任务
        query = self.db.query(CrawlerTask).filter(
            CrawlerTask.workflow_id.isnot(None)
        )

        if workflow_id:
            query = query.filter(CrawlerTask.workflow_id == workflow_id)

        # 按创建时间倒序
        tasks = query.order_by(CrawlerTask.created_at.desc()).limit(limit).all()

        # 按工作流分组
        workflows = {}
        for task in tasks:
            wf_id = task.workflow_id
            if wf_id not in workflows:
                workflows[wf_id] = {
                    "id": wf_id,
                    "name": task.workflow_name or wf_id,
                    "created_at": task.created_at.isoformat(),
                    "status": "unknown",
                    "steps": []
                }

            workflows[wf_id]["steps"].append({
                "id": task.id,
                "name": task.task_name,
                "step_order": task.step_order,
                "status": task.status,
                "created_at": task.created_at.isoformat(),
                "start_time": task.start_time.isoformat() if task.start_time else None,
                "end_time": task.end_time.isoformat() if task.end_time else None
            })

        # 判断工作流状态
        for wf_id, wf in workflows.items():
            if all(s["status"] == "success" for s in wf["steps"]):
                wf["status"] = "completed"
            elif any(s["status"] in ["running", "pending"] for s in wf["steps"]):
                wf["status"] = "running"
            elif any(s["status"] == "failed" for s in wf["steps"]):
                wf["status"] = "failed"

        return list(workflows.values())