"""
数据采集服务 - 任务管理和执行逻辑
"""

import subprocess
import json
import logging
from typing import List, Optional, Dict
from datetime import datetime

from packages.scraper.database import get_crawler_db
from packages.scraper.models import CrawlerTask, CrawlerLog, TaskStatus

logger = logging.getLogger(__name__)


class CrawlerService:
    """数据采集服务"""

    def trigger_crawler(
        self,
        task_type: str,
        keywords: Optional[List[str]] = None,
        shop_url: Optional[str] = None,
        max_pages: int = 5,
        proxy: Optional[str] = None
    ) -> Dict:
        """
        触发数据采集任务

        Args:
            task_type: 任务类型（taobao/jd/pdd/forum）
            keywords: 搜索关键词
            shop_url: 店铺URL
            max_pages: 最大爬取页数
            proxy: 代理服务器

        Returns:
            CrawlerTask: 创建的任务对象
        """
        db = get_crawler_db()
        with db.session_scope() as session:
            # 构造任务配置
            config = {
                "keywords": keywords or [],
                "shop_url": shop_url,
                "max_pages": max_pages,
                "proxy": proxy
            }

            # 创建任务
            task = CrawlerTask(
                task_type=task_type,
                task_name=f"{task_type}数据采集 - {datetime.now().strftime('%Y%m%d%H%M%S')}",
                status=TaskStatus.PENDING,
                config=json.dumps(config, ensure_ascii=False),
                shop_url=shop_url,
                total_items=0,
                success_items=0,
                failed_items=0
            )

            session.add(task)
            session.commit()
            session.refresh(task)

            # 保存任务ID，用于后续操作
            task_id = task.id

            logger.info(f"数据采集任务已创建: task_id={task_id}, type={task_type}")

            # 注意：任务创建后状态为 PENDING，需要用户手动点击"启动"按钮
            # 启动后状态变为 QUEUED，等待 Worker 领取
            # 不再自动提交到内部队列执行

            # 在session内转换为dict返回，避免DetachedInstanceError
            return task.to_dict()

    def _start_crawler_process(
        self,
        task_id: int,
        task_type: str,
        config: Dict
    ):
        """
        提交任务到全局任务队列执行

        Args:
            task_id: 任务ID
            task_type: 任务类型
            config: 任务配置
        """
        try:
            # 延迟导入避免循环引用
            from packages.scraper.executor.task_queue import get_task_queue

            # 获取全局任务队列
            task_queue = get_task_queue()

            # 计算任务优先级
            priority = self._calculate_priority(task_type, config)

            # 提交任务到队列
            task_queue.submit(
                task_id=task_id,
                priority=priority,
                config=config
            )

            logger.info(
                f"任务已提交到队列: task_id={task_id}, "
                f"type={task_type}, priority={priority}"
            )

        except RuntimeError as e:
            # 任务队列未初始化
            logger.error(f"任务队列不可用: {e}")
            self._mark_task_failed(task_id, "任务队列未初始化")
            raise
        except Exception as e:
            logger.error(f"提交任务到队列失败: {e}", exc_info=True)
            self._mark_task_failed(task_id, str(e))
            raise

    def _calculate_priority(self, task_type: str, config: Dict) -> int:
        """
        计算任务优先级

        Args:
            task_type: 任务类型
            config: 任务配置

        Returns:
            int: 优先级（数字越大优先级越高）
        """
        priority = config.get("priority", 0)

        # 重试任务优先级更高
        if config.get("is_retry"):
            priority += 5

        # 根据任务类型调整优先级
        type_priorities = {
            "taobao": 1,
            "jd": 1,
            "forum": 0
        }
        priority += type_priorities.get(task_type, 0)

        return priority

    def _mark_task_failed(self, task_id: int, error_message: str):
        """
        标记任务为失败状态

        Args:
            task_id: 任务ID
            error_message: 错误信息
        """
        try:
            db = get_crawler_db()
            with db.session_scope() as session:
                task = session.query(CrawlerTask).get(task_id)
                if task:
                    task.status = TaskStatus.FAILED
                    task.error_message = f"启动失败: {error_message}"
        except Exception as e:
            logger.error(f"更新任务失败状态时出错: {e}")

    def retry_task(self, task: CrawlerTask) -> CrawlerTask:
        """
        重试失败任务

        Args:
            task: 失败的任务

        Returns:
            CrawlerTask: 新创建的任务
        """
        # 提取原任务配置
        config = json.loads(task.config) if task.config else {}

        # 创建新任务
        return self.trigger_crawler(
            task_type=task.task_type,
            keywords=config.get("keywords"),
            max_pages=config.get("max_pages", 5),
            proxy=config.get("proxy")
        )

    def start_task(self, task: CrawlerTask) -> Dict:
        """
        启动等待中的任务

        将任务状态改为 QUEUED（等待Worker领取），而不是直接运行。
        Worker 领取任务后会将状态改为 RUNNING。

        Args:
            task: 等待中的任务

        Returns:
            Dict: 更新后的任务字典
        """
        try:
            db = get_crawler_db()
            with db.session_scope() as session:
                # 重新获取任务以确保最新状态
                current_task = session.query(CrawlerTask).get(task.id)
                if not current_task:
                    raise ValueError(f"任务不存在: {task.id}")

                # 检查任务状态
                if current_task.status not in [TaskStatus.PENDING, TaskStatus.FAILED]:
                    raise ValueError(f"任务状态不允许启动: {current_task.status}")

                # 更新任务状态为 QUEUED（等待Worker领取）
                current_task.status = TaskStatus.QUEUED
                current_task.error_message = None

                logger.info(
                    f"任务已加入队列等待领取: task_id={current_task.id}, "
                    f"type={current_task.task_type}"
                )

                # 在session内转换为dict返回，避免DetachedInstanceError
                return current_task.to_dict()

        except Exception as e:
            logger.error(f"启动任务失败: {e}", exc_info=True)
            raise

    def get_sync_status(self) -> Dict:
        """
        获取数据同步状态

        Returns:
            dict: 同步状态统计
        """
        db = get_crawler_db()
        with db.session_scope() as session:
            # 统计最近成功任务
            recent_success_tasks = session.query(CrawlerTask).filter(
                CrawlerTask.status == TaskStatus.SUCCESS
            ).order_by(CrawlerTask.end_time.desc()).limit(10).all()

            last_sync_time = None
            if recent_success_tasks:
                task = recent_success_tasks[0]
                if task.end_time:
                    last_sync_time = task.end_time.isoformat()

            # 统计数据
            total_synced = sum(task.success_items for task in recent_success_tasks)
            sync_errors = sum(task.failed_items for task in recent_success_tasks)

            # TODO: 实现去重统计和待同步统计
            duplicate_removed = 0
            pending_sync = 0

            return {
                "last_sync_time": last_sync_time,
                "total_synced": total_synced,
                "pending_sync": pending_sync,
                "duplicate_removed": duplicate_removed,
                "sync_errors": sync_errors
            }
