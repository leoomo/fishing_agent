"""
爬虫执行器

负责执行单个爬虫任务，包括：
- 状态管理
- 进度回调
- 错误处理
- 结果持久化
"""

import json
import logging
import traceback
import time
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List
from packages.agent_fishing.tools.lure.models.system import CrawlerTask, CrawlerLog
from packages.agent_fishing.tools.crawler.data_persister import DataPersister
from packages.agent_fishing.tools.lure.database import get_db
from packages.agent_fishing.tools.crawler.platform.registry import platform_registry
from packages.agent_fishing.tools.crawler.platform.base_platform import TaskConfig, TaskType

logger = logging.getLogger(__name__)


class CrawlerExecutor:
    """
    爬虫执行器

    职责：
    1. 根据task_type调用对应平台爬虫
    2. 实时更新任务状态和进度
    3. 捕获异常并记录日志
    4. 触发重试逻辑
    5. 触发工作流后续任务
    """

    def __init__(self, db_session, worker_id: int = 0):
        """
        初始化爬虫执行器

        Args:
            db_session: 数据库会话
            worker_id: 工作器ID（用于日志追踪）
        """
        self.db = db_session
        self.worker_id = worker_id
        self.platform_registry = platform_registry

    def execute(self, task_id: int):
        """
        执行单个爬虫任务

        Args:
            task_id: CrawlerTask的ID
        """
        task = self.db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
        if not task:
            logger.error(f"任务 {task_id} 不存在")
            return False

        logger.info(f"[Worker-{self.worker_id}] 开始执行任务 {task_id} (type={task.task_type}, name={task.task_name})")

        # 1. 更新状态为RUNNING
        task.status = 'running'
        task.start_time = datetime.utcnow()
        self.db.commit()

        # 2. 记录任务开始事件到监控系统
        try:
            from packages.agent_fishing.tools.crawler.monitoring import get_monitoring_service
            monitor = get_monitoring_service()
            if monitor:
                monitor.record_task_event("start", task_id, task_type=task.task_type)
        except Exception as e:
            logger.warning(f"记录任务开始事件失败: {e}")

        # 3. 记录开始日志
        self._log(task, 'info', '任务开始执行', {
            'worker_id': self.worker_id,
            'task_type': task.task_type,
            'config': task.config
        })

        try:
            # 3. 解析任务配置
            config = json.loads(task.config) if task.config else {}

            # 4. 构建任务配置对象
            task_config = self._build_task_config(task, config)

            # 5. 获取平台爬虫实例
            platform = platform_registry.get_platform_for_config(task_config)

            # 6. 执行爬虫（带进度回调）
            logger.info(f"调用平台 {platform.platform_name} 的爬虫，配置: {config}")

            # 使用异步执行（因为平台爬虫是异步的）
            import asyncio
            try:
                # 获取或创建事件循环
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # 如果没有事件循环，创建新的
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # 执行爬虫
            async def _crawl():
                return await platform.crawl(
                    task_config,
                    lambda msg, progress: self._on_progress(task, msg, progress)
                )

            # 在新线程中运行异步函数
            crawl_result = asyncio.run_coroutine_threadsafe(_crawl(), loop).result()

            # 提取结果
            results = crawl_result.items if crawl_result else []

            logger.info(f"爬虫执行完成，获得 {len(results)} 条数据")

            # 7. 持久化结果
            if results:
                persister = DataPersister(self.db, None, None, None)
                stats = persister.save_equipment_data_batch(results)

                logger.info(f"数据持久化完成: 成功{stats['success']}条, 失败{stats['failed']}条, 去重{stats['duplicates']}条")
            else:
                stats = {'success': 0, 'failed': 0, 'duplicates': 0}
                logger.warning("没有获得数据，跳过持久化")

            # 6. 更新任务状态为SUCCESS
            task.status = 'success'
            task.end_time = datetime.utcnow()
            task.success_items = stats['success']
            task.failed_items = stats['failed']
            task.duplicate_items = stats['duplicates']
            task.total_items = len(results)
            task.result_summary = json.dumps({
                "total_items": len(results),
                "success_count": stats['success'],
                "failed_count": stats['failed'],
                "duplicate_count": stats['duplicates']
            })
            self.db.commit()

            # 7. 记录成功日志
            self._log(task, 'info', '任务执行成功', {
                'total_items': task.total_items,
                'success_items': task.success_items,
                'failed_items': task.failed_items,
                'duration_seconds': (task.end_time - task.start_time).total_seconds() if task.start_time and task.end_time else 0
            })

            # 8. 记录任务完成事件到监控系统
            try:
                from packages.agent_fishing.tools.crawler.monitoring import get_monitoring_service
                monitor = get_monitoring_service()
                if monitor:
                    monitor.record_task_event(
                        "complete",
                        task_id,
                        status="success",
                        items_processed=task.total_items,
                        items_success=task.success_items,
                        items_failed=task.failed_items
                    )
            except Exception as e:
                logger.warning(f"记录任务完成事件失败: {e}")

            # 9. 触发工作流后续任务
            self._trigger_workflow_next_tasks(task)

            return True

        except Exception as e:
            # 错误处理
            logger.error(f"任务 {task_id} 执行失败: {e}", exc_info=True)

            task.status = 'failed'
            task.error_message = str(e)
            task.end_time = datetime.utcnow()
            self.db.commit()

            # 记录任务失败事件到监控系统
            try:
                from packages.agent_fishing.tools.crawler.monitoring import get_monitoring_service
                monitor = get_monitoring_service()
                if monitor:
                    monitor.record_task_event(
                        "complete",
                        task_id,
                        status="failed",
                        items_processed=task.total_items,
                        items_success=task.success_items,
                        items_failed=task.failed_items,
                        error_message=str(e)
                    )
            except Exception as me:
                logger.warning(f"记录任务失败事件失败: {me}")

            # 记录错误日志
            self._log(task, 'error', f'任务执行失败: {e}', {
                'traceback': traceback.format_exc()
            })

            # 触发重试逻辑
            self._handle_retry(task)

            return False

    def _build_task_config(self, task: CrawlerTask, config: Dict) -> TaskConfig:
        """
        构建任务配置对象

        Args:
            task: 任务对象
            config: 配置字典

        Returns:
            任务配置对象
        """
        # 根据task_type确定TaskType
        task_type_map = {
            'taobao': TaskType.KEYWORD_SEARCH,
            'jd': TaskType.KEYWORD_SEARCH,
            'shop_crawl': TaskType.SHOP_CRAWL,
            'shop_analyze': TaskType.SHOP_ANALYZE,
            'product_detail': TaskType.PRODUCT_DETAIL,
            'category_crawl': TaskType.CATEGORY_CRAWL
        }

        task_type = task_type_map.get(task.task_type, TaskType.KEYWORD_SEARCH)

        # 构建TaskConfig对象
        task_config = TaskConfig(
            task_type=task_type,
            keywords=config.get('keywords', []),
            shop_url=task.shop_url or config.get('shop_url'),
            category_url=config.get('category_url'),
            product_urls=config.get('product_urls', []),
            max_pages=config.get('max_pages', task.max_retries),
            max_items_per_page=config.get('max_items_per_page', 100),
            delay=config.get('delay', 1.0),
            timeout=task.timeout_seconds or config.get('timeout', 300),
            proxy=config.get('proxy'),
            custom_params=config.get('custom_params', {})
        )

        # 如果有步骤配置，也添加到自定义参数中
        if task.step_config:
            step_config = json.loads(task.step_config) if isinstance(task.step_config, str) else task.step_config
            if step_config:
                task_config.custom_params.update(step_config)

        return task_config

    def _simulate_crawl(self, task: CrawlerTask, config: Dict) -> List[Dict]:
        """模拟爬虫执行（用于测试）"""
        from packages.agent_fishing.tools.crawler.data_persister import EquipmentData

        # 模拟数据
        mock_items = [
            EquipmentData(
                name=f"测试商品 - {task.task_name}",
                category="装备",
                brand_name="测试品牌",
                model=f"型号-{task.task_type}",
                price_min=100.0,
                price_max=200.0,
                description=f"通过爬虫获取的{task.task_type}数据",
                source_url=f"https://example.com/item/{task.id}"
            )
            for _ in range(3)  # 模拟3条数据
        ]

        # 模拟处理时间
        time.sleep(1)

        # 返回字典格式数据
        return [
            {
                'name': item.name,
                'category': item.category,
                'brand_name': item.brand_name,
                'model': item.model,
                'price_min': item.price_min,
                'price_max': item.price_max,
                'description': item.description,
                'source_url': item.source_url
            }
            for item in mock_items
        ]

    def _on_progress(self, task: CrawlerTask, message: str, progress_percent: int):
        """
        进度回调

        Args:
            task: 任务对象
            message: 进度消息
            progress_percent: 进度百分比（0-100）
        """
        logger.info(f"任务 {task.id} 进度: {progress_percent}% - {message}")

        # 更新进度（将进度存储在config中）
        config = json.loads(task.config) if task.config else {}
        config['_progress'] = {
            'percent': progress_percent,
            'message': message,
            'updated_at': datetime.utcnow().isoformat()
        }
        task.config = json.dumps(config)
        self.db.commit()

        # 推送WebSocket进度更新（如果需要）
        # self._push_ws_update(task, message, progress_percent)

    def _log(self, task: CrawlerTask, level: str, message: str, details: dict = None):
        """
        记录任务日志

        Args:
            task: 任务对象
            level: 日志级别（info/warning/error）
            message: 日志消息
            details: 详细信息（JSON）
        """
        log = CrawlerLog(
            task_id=task.id,
            level=level,
            message=message,
            details=json.dumps(details) if details else None
        )
        self.db.add(log)
        self.db.commit()

    def _handle_retry(self, task: CrawlerTask):
        """
        处理任务重试

        Args:
            task: 失败的任务对象
        """
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = 'pending'  # 重置为PENDING
            self.db.commit()

            # 指数退避延迟
            delay = 2 ** task.retry_count
            logger.info(f"任务 {task.id} 将在 {delay} 秒后重试 (第{task.retry_count}/{task.max_retries}次)")

            # 记录重试日志
            self._log(task, 'warning', f'任务重试: 第{task.retry_count}次', {
                'delay_seconds': delay
            })

            # 延迟后重新提交（这里只是记录，实际提交需要外部调用）
            logger.info(f"任务 {task.id} 准备重试（需要外部系统重新提交）")

        else:
            logger.error(f"任务 {task.id} 已达最大重试次数({task.max_retries})，放弃重试")
            self._log(task, 'error', '任务达到最大重试次数，执行失败', {
                'max_retries': task.max_retries
            })

    def _trigger_workflow_next_tasks(self, task: CrawlerTask):
        """
        触发工作流的后续任务

        Args:
            task: 已完成的任务对象
        """
        if not task.workflow_id:
            return  # 非工作流任务，直接返回

        logger.info(f"检查工作流 {task.workflow_id} 的后续任务...")

        # 查找同一工作流的所有任务
        workflow_tasks = self.db.query(CrawlerTask).filter(
            CrawlerTask.workflow_id == task.workflow_id
        ).all()

        # 解析步骤定义，找到依赖当前任务的步骤
        for t in workflow_tasks:
            if t.status != 'pending':
                continue  # 只处理PENDING状态的任务

            step_config = json.loads(t.step_config) if t.step_config else {}
            depends_on = step_config.get('depends_on', [])

            # 检查是否依赖当前任务
            if task.id in depends_on or f"step_{task.step_order}" in depends_on:
                # 检查所有依赖是否都已完成
                all_deps_done = all(
                    self.db.query(CrawlerTask).filter(
                        CrawlerTask.workflow_id == task.workflow_id,
                        CrawlerTask.step_order == dep_order,
                        CrawlerTask.status == 'success'
                    ).first() is not None
                    for dep_order in [int(dep.split('_')[1]) for dep in depends_on if dep.startswith('step_')]
                )

                if all_deps_done:
                    logger.info(f"任务 {t.id} 的所有依赖已完成，准备执行")
                    # 这里只是记录，实际执行需要外部系统调用
                    logger.info(f"建议调用: submit_task_to_queue({t.id})")

    def get_task_metrics(self, task_id: int) -> Optional[Dict]:
        """获取任务执行指标"""
        try:
            task = self.db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
            if not task:
                return None

            metrics = {
                'task_id': task_id,
                'task_name': task.task_name,
                'task_type': task.task_type,
                'status': task.status,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'start_time': task.start_time.isoformat() if task.start_time else None,
                'end_time': task.end_time.isoformat() if task.end_time else None,
                'total_items': task.total_items,
                'success_items': task.success_items,
                'failed_items': task.failed_items,
                'retry_count': task.retry_count,
                'max_retries': task.max_retries,
                'worker_id': self.worker_id
            }

            # 计算持续时间
            if task.start_time and task.end_time:
                metrics['duration_seconds'] = (task.end_time - task.start_time).total_seconds()

            # 获取日志数量
            logs = self.db.execute(
                "SELECT level, COUNT(*) as count FROM crawler_logs WHERE task_id = ? GROUP BY level",
                (task_id,)
            )
            metrics['log_counts'] = {row['level']: row['count'] for row in logs}

            return metrics

        except Exception as e:
            logger.error(f"获取任务指标失败: {e}")
            return None