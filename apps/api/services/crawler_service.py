"""
爬虫服务 - 任务管理和执行逻辑
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
    """爬虫服务"""

    def trigger_crawler(
        self,
        task_type: str,
        keywords: Optional[List[str]] = None,
        shop_url: Optional[str] = None,
        max_pages: int = 5,
        proxy: Optional[str] = None
    ) -> Dict:
        """
        触发爬虫任务

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
                task_name=f"{task_type}爬虫 - {datetime.now().strftime('%Y%m%d%H%M%S')}",
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

            logger.info(f"爬虫任务已创建: task_id={task_id}, type={task_type}")

            # 异步启动爬虫（后台运行）
            self._start_crawler_process(task_id, task_type, config)

            # 在session内转换为dict返回，避免DetachedInstanceError
            return task.to_dict()

    def _start_crawler_process(
        self,
        task_id: int,
        task_type: str,
        config: Dict
    ):
        """
        启动爬虫进程（后台运行）

        Args:
            task_id: 任务ID
            task_type: 任务类型
            config: 任务配置

        Note:
            实际生产环境中，这里应该调用真实的爬虫脚本
            目前仅做演示，不启动真实进程
        """
        try:
            # 构造爬虫命令
            # cmd = [
            #     "uv", "run", "python",
            #     "scripts/run_crawler.py",
            #     "--type", task_type,
            #     "--task-id", str(task_id),
            #     "--keywords", ",".join(config.get("keywords", [])),
            #     "--max-pages", str(config.get("max_pages", 5))
            # ]
            #
            # if config.get("proxy"):
            #     cmd.extend(["--proxy", config["proxy"]])
            #
            # # 后台启动爬虫进程
            # subprocess.Popen(
            #     cmd,
            #     stdout=subprocess.DEVNULL,
            #     stderr=subprocess.DEVNULL,
            #     start_new_session=True  # 独立会话，不受父进程影响
            # )

            logger.info(
                f"爬虫进程待启动: task_id={task_id}, type={task_type}"
            )
            logger.info(
                "注意: 当前为演示模式，未实际启动爬虫进程。"
                "实际生产环境需要实现真实的爬虫逻辑。"
            )

            # 演示模式：直接标记任务为待处理
            # 真实环境中，任务状态由爬虫进程更新

        except Exception as e:
            logger.error(f"启动爬虫进程失败: {e}", exc_info=True)

            # 更新任务状态为失败
            db = get_crawler_db()
            with db.session_scope() as session:
                task = session.query(CrawlerTask).get(task_id)
                if task:
                    task.status = TaskStatus.FAILED
                    task.error_message = f"启动失败: {str(e)}"

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
