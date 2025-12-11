"""
工作流调度器

基于APScheduler的工作流定时调度系统
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from packages.agent_fishing.tools.lure.database import get_db
from packages.agent_fishing.tools.lure.models.system import CrawlerSchedule, CrawlerWorkflowTemplate

logger = logging.getLogger(__name__)


class WorkflowScheduler:
    """
    工作流调度器

    负责管理定时工作流的调度和执行
    """

    def __init__(self, scheduler):
        """
        初始化调度器

        Args:
            scheduler: APScheduler实例
        """
        self.scheduler = scheduler
        self._loaded_schedules = set()

    def load_schedules_from_db(self):
        """从数据库加载所有启用的调度"""
        try:
            db = get_db()

            # 查询所有启用的调度
            schedules = db.query(CrawlerSchedule).filter(
                CrawlerSchedule.is_enabled == True
            ).all()

            logger.info(f"开始加载定时调度，共 {len(schedules)} 个")

            for schedule in schedules:
                try:
                    # 获取关联的模板
                    template = db.query(CrawlerWorkflowTemplate).filter(
                        CrawlerWorkflowTemplate.id == schedule.template_id,
                        CrawlerWorkflowTemplate.is_active == True
                    ).first()

                    if not template:
                        logger.warning(f"跳过调度 {schedule.name}: 模板不存在或未启用")
                        continue

                    # 添加到调度器
                    self._add_schedule(schedule, template)
                    self._loaded_schedules.add(schedule.id)

                except Exception as e:
                    logger.error(f"加载调度失败 {schedule.name}: {e}")

            logger.info(f"成功加载 {len(self._loaded_schedules)} 个定时调度")

        except Exception as e:
            logger.error(f"从数据库加载调度失败: {e}")

    def reload_schedule(self, schedule_id: int):
        """
        重新加载指定的调度

        Args:
            schedule_id: 调度ID
        """
        try:
            db = get_db()

            # 先移除旧调度
            self.remove_schedule(schedule_id)

            # 查询新调度
            schedule = db.query(CrawlerSchedule).filter(
                CrawlerSchedule.id == schedule_id,
                CrawlerSchedule.is_enabled == True
            ).first()

            if schedule:
                # 获取关联的模板
                template = db.query(CrawlerWorkflowTemplate).filter(
                    CrawlerWorkflowTemplate.id == schedule.template_id,
                    CrawlerWorkflowTemplate.is_active == True
                ).first()

                if template:
                    # 添加到调度器
                    self._add_schedule(schedule, template)
                    self._loaded_schedules.add(schedule_id)
                    logger.info(f"重新加载调度成功: {schedule.name}")
                else:
                    logger.warning(f"跳过调度 {schedule.name}: 模板不存在或未启用")
            else:
                logger.info(f"调度 {schedule_id} 未启用或不存在，跳过重新加载")

        except Exception as e:
            logger.error(f"重新加载调度失败 {schedule_id}: {e}")

    def remove_schedule(self, schedule_id: int):
        """
        移除指定的调度

        Args:
            schedule_id: 调度ID
        """
        try:
            job_id = f"workflow_schedule_{schedule_id}"

            # 从调度器中移除
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"从调度器移除任务: {job_id}")

            # 从已加载集合中移除
            self._loaded_schedules.discard(schedule_id)

        except Exception as e:
            logger.error(f"移除调度失败 {schedule_id}: {e}")

    def _add_schedule(self, schedule: CrawlerSchedule, template: CrawlerWorkflowTemplate):
        """添加调度到APScheduler"""
        import json
        import uuid

        job_id = f"workflow_schedule_{schedule.id}"

        # 检查是否已存在
        if self.scheduler.get_job(job_id):
            logger.warning(f"调度任务已存在: {job_id}")
            return

        # 定义任务函数
        async def run_scheduled_workflow():
            from packages.agent_fishing.tools.crawler.workflow.manager import WorkflowManager

            try:
                db = get_db()
                workflow_manager = WorkflowManager(db)

                # 生成工作流实例ID
                workflow_id = str(uuid.uuid4())

                # 获取调度参数
                params = {}
                if schedule.params:
                    try:
                        params = json.loads(schedule.params)
                    except json.JSONDecodeError:
                        logger.error(f"调度参数解析失败: {schedule.params}")
                        params = {}

                # 执行工作流
                success = workflow_manager.execute_workflow_from_template(
                    template_id=schedule.template_id,
                    workflow_id=workflow_id,
                    params=params,
                    priority=0,  # 调度任务使用默认优先级
                    max_retries=3,
                    timeout_seconds=schedule.timeout_seconds
                )

                # 更新统计信息
                self._update_schedule_stats(schedule.id, success)

                if success:
                    logger.info(f"定时工作流执行成功: schedule_id={schedule.id}, workflow_id={workflow_id}")
                else:
                    logger.error(f"定时工作流执行失败: schedule_id={schedule.id}")

            except Exception as e:
                logger.error(f"定时工作流执行异常: schedule_id={schedule.id}, error={e}", exc_info=True)
                # 更新失败统计
                self._update_schedule_stats(schedule.id, False)

        # 解析Cron表达式
        cron_parts = self._parse_cron_expression(schedule.cron_expression)

        # 添加到调度器
        self.scheduler.add_job(
            run_scheduled_workflow,
            'cron',
            id=job_id,
            **cron_parts,
            timezone=schedule.timezone,
            max_instances=schedule.max_instances,
            misfire_grace_time=300,  # 5分钟宽限期
            coalesce=True,  # 合并错过的任务
            jitter=60  # 随机延迟0-60秒，避免同时执行
        )

        logger.info(f"调度已添加到调度器: {job_id}, cron={schedule.cron_expression}, timezone={schedule.timezone}")

    def _parse_cron_expression(self, cron_expr: str) -> Dict[str, str]:
        """解析Cron表达式为APScheduler参数"""
        parts = cron_expr.split()
        if len(parts) != 5:
            raise ValueError(f"无效的Cron表达式: {cron_expr}")

        minute, hour, day, month, day_of_week = parts

        return {
            'minute': minute,
            'hour': hour,
            'day': day,
            'month': month,
            'day_of_week': day_of_week
        }

    def _update_schedule_stats(self, schedule_id: int, success: bool):
        """更新调度统计信息"""
        try:
            db = get_db()
            schedule = db.query(CrawlerSchedule).filter(
                CrawlerSchedule.id == schedule_id
            ).first()

            if schedule:
                schedule.run_count += 1
                if success:
                    schedule.success_count += 1
                else:
                    schedule.failure_count += 1
                schedule.last_run_at = datetime.utcnow()
                db.commit()

        except Exception as e:
            logger.error(f"更新调度统计失败: {e}")

    def get_schedule_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        jobs = self.scheduler.get_jobs()
        schedule_jobs = [job for job in jobs if job.id.startswith('workflow_schedule_')]

        return {
            'total_jobs': len(jobs),
            'schedule_jobs': len(schedule_jobs),
            'loaded_schedules': len(self._loaded_schedules),
            'scheduler_state': self.scheduler.state,
            'active_schedule_jobs': [
                {
                    'id': job.id,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                }
                for job in schedule_jobs
            ]
        }

    def pause_schedule(self, schedule_id: int):
        """暂停调度"""
        try:
            job_id = f"workflow_schedule_{schedule_id}"
            self.scheduler.pause_job(job_id)
            logger.info(f"调度已暂停: {job_id}")
        except Exception as e:
            logger.error(f"暂停调度失败 {schedule_id}: {e}")

    def resume_schedule(self, schedule_id: int):
        """恢复调度"""
        try:
            job_id = f"workflow_schedule_{schedule_id}"
            self.scheduler.resume_job(job_id)
            logger.info(f"调度已恢复: {job_id}")
        except Exception as e:
            logger.error(f"恢复调度失败 {schedule_id}: {e}")