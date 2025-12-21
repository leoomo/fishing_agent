"""
任务队列实现

支持subprocess和线程两种执行模式
"""

import logging
import threading
import queue
import json
import time
from typing import Optional, Callable, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from ..database import get_crawler_db
from ..models import CrawlerTask, TaskStatus

logger = logging.getLogger(__name__)

# 全局数据库获取函数（通过 configure_database 设置）
_get_db_func = None


def configure_database(get_db_func):
    """
    配置数据库获取函数

    Args:
        get_db_func: 返回数据库会话的函数
    """
    global _get_db_func
    _get_db_func = get_db_func


def _get_db():
    """获取数据库会话"""
    if _get_db_func is None:
        raise RuntimeError(
            "Database not configured. Call configure_database() first or "
            "pass get_db function to CrawlerTaskQueue constructor."
        )
    return _get_db_func()


class CrawlerTaskQueue:
    """
    爬虫任务队列（支持进程和线程两种模式）

    特性：
    - 支持subprocess模式（与现有系统兼容）
    - 支持线程池模式（轻量级任务）
    - 任务优先级管理
    - 失败重试机制
    - 实时状态更新
    """

    def __init__(self, mode="subprocess", max_workers=3, get_db_func=None):
        """
        初始化任务队列

        Args:
            mode: 执行模式 ("subprocess" 或 "thread")
            max_workers: 最大工作线程/进程数
            get_db_func: 获取数据库会话的函数（可选，也可通过 configure_database 全局配置）
        """
        self.mode = mode
        self.max_workers = max_workers

        # 设置数据库获取函数
        if get_db_func is not None:
            configure_database(get_db_func)

        # 任务队列
        self.task_queue = queue.PriorityQueue()

        # 状态追踪
        self.running_tasks = set()
        self.completed_tasks = set()
        self.failed_tasks = set()

        # 统计信息
        self.stats = {
            "total_submitted": 0,
            "total_completed": 0,
            "total_failed": 0,
            "queue_depth": 0,
            "active_workers": 0
        }

        # 线程安全锁
        self._lock = threading.Lock()

        # 工作线程池
        self.executor = None
        self._shutdown_event = threading.Event()

        # 启动工作线程
        self._start_workers()
        logger.info(f"任务队列初始化完成，模式={mode}，最大工作数={max_workers}")

    def _start_workers(self):
        """启动工作线程池"""
        if self.mode == "subprocess":
            # 使用进程池执行（适合重型爬虫任务）
            self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
        else:
            # 使用线程池执行（适合轻量级任务）
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

        logger.info(f"启动{self.mode}执行器，工作器数量: {self.max_workers}")

    def submit(self, task_id: int, priority: int = 0, config: Optional[Dict] = None):
        """
        提交任务到队列

        Args:
            task_id: 任务ID
            priority: 任务优先级（数字越大优先级越高）
            config: 任务配置（可选）
        """
        # 包装任务信息
        task_info = {
            "task_id": task_id,
            "priority": priority,
            "config": config or {},
            "submitted_at": datetime.utcnow().isoformat()
        }

        # 使用负优先级，因为PriorityQueue是低优先级先
        self.task_queue.put((-priority, task_info))

        # 更新统计
        with self._lock:
            self.stats["total_submitted"] += 1
            self.stats["queue_depth"] = self.task_queue.qsize()

        logger.info(f"任务已提交: {task_id} (优先级={priority}, 队列深度={self.task_queue.qsize()})")

    def execute_next_task(self):
        """执行下一个可用任务"""
        try:
            # 从队列获取任务（阻塞1秒）
            priority, task_info = self.task_queue.get(timeout=1)

            task_id = task_info["task_id"]
            config = task_info["config"]

            logger.info(f"开始执行任务: {task_id}")

            # 标记为运行中
            with self._lock:
                self.running_tasks.add(task_id)
                self.stats["active_workers"] = len(self.running_tasks)

            # 根据模式执行任务
            if self.mode == "subprocess":
                success = self._execute_via_subprocess(task_id, config)
            else:
                success = self._execute_via_thread(task_id, config)

            # 更新状态
            with self._lock:
                self.running_tasks.discard(task_id)
                self.stats["active_workers"] = len(self.running_tasks)
                self.stats["queue_depth"] = self.task_queue.qsize()

                if success:
                    self.completed_tasks.add(task_id)
                    self.stats["total_completed"] += 1
                else:
                    self.failed_tasks.add(task_id)
                    self.stats["total_failed"] += 1

            return success

        except queue.Empty:
            # 队列为空
            return True
        except Exception as e:
            logger.error(f"任务执行异常: {e}", exc_info=True)
            return False

    def _execute_via_subprocess(self, task_id: int, config: Dict) -> bool:
        """
        通过subprocess执行任务

        注意：subprocess 模式目前使用线程模式作为回退
        """
        # 暂时使用线程模式执行
        # TODO: 实现真正的subprocess执行（需要独立的执行脚本）
        logger.info(f"任务 {task_id} 使用线程模式执行（subprocess模式暂未实现）")
        return self._execute_via_thread(task_id, config)

    def _execute_via_thread(self, task_id: int, config: Dict) -> bool:
        """
        通过线程执行任务

        使用独立的数据库会话确保线程安全
        """
        db = get_crawler_db()
        session = None

        try:
            # 获取独立的数据库会话
            session = db.get_session()

            # 获取任务
            task = session.query(CrawlerTask).filter(
                CrawlerTask.id == task_id
            ).first()

            if not task:
                logger.error(f"任务 {task_id} 不存在")
                return False

            # 更新任务状态为运行中
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.utcnow()
            session.commit()

            logger.info(f"[Thread] 开始执行任务 {task_id}, 类型: {task.task_type}")

            # 推送进度：开始执行
            self._push_ws_progress(task_id, "RUNNING", 10, "任务开始执行")

            # 模拟任务执行（实际环境中这里调用真实的爬虫逻辑）
            # TODO: 集成真实的爬虫执行器
            time.sleep(1)
            self._push_ws_progress(task_id, "RUNNING", 50, "正在处理数据...")
            time.sleep(1)
            self._push_ws_progress(task_id, "RUNNING", 90, "即将完成...")

            # 更新任务完成状态
            task.status = TaskStatus.SUCCESS
            task.end_time = datetime.utcnow()
            task.success_items = 3
            task.total_items = 3
            session.commit()

            # 推送进度：完成
            self._push_ws_progress(
                task_id, "SUCCESS", 100, "任务执行完成",
                items_success=3, items_processed=3
            )

            # 触发工作流后续任务
            self._trigger_workflow_next_tasks(task, session)

            logger.info(f"任务 {task_id} 执行成功")
            return True

        except Exception as e:
            logger.error(f"任务 {task_id} 执行异常: {e}", exc_info=True)

            # 更新任务状态为失败
            try:
                if session:
                    task = session.query(CrawlerTask).filter(
                        CrawlerTask.id == task_id
                    ).first()
                    if task:
                        task.status = TaskStatus.FAILED
                        task.error_message = str(e)
                        task.end_time = datetime.utcnow()
                        session.commit()

                # 推送进度：失败
                self._push_ws_progress(task_id, "FAILED", 0, f"执行失败: {str(e)}")

            except Exception as db_error:
                logger.error(f"更新任务失败状态时出错: {db_error}")
                if session:
                    session.rollback()

            return False

        finally:
            if session:
                session.close()

    def _push_ws_progress(
        self,
        task_id: int,
        status: str,
        progress: int,
        message: str,
        items_processed: int = 0,
        items_success: int = 0,
        items_failed: int = 0
    ):
        """
        推送 WebSocket 进度更新（线程安全）

        Args:
            task_id: 任务ID
            status: 任务状态
            progress: 进度百分比
            message: 进度消息
        """
        try:
            import asyncio
            from apps.api.services.websocket_manager import get_ws_manager

            ws_manager = get_ws_manager()

            # 创建协程
            coro = ws_manager.broadcast_progress(
                task_id=task_id,
                status=status,
                progress=progress,
                message=message,
                items_processed=items_processed,
                items_success=items_success,
                items_failed=items_failed
            )

            # 尝试获取运行中的事件循环
            try:
                loop = asyncio.get_running_loop()
                # 在已有事件循环中调度
                asyncio.run_coroutine_threadsafe(coro, loop)
            except RuntimeError:
                # 没有运行中的事件循环，创建新的
                asyncio.run(coro)

        except Exception as e:
            # WebSocket 推送失败不应影响任务执行
            logger.debug(f"WebSocket 进度推送失败: {e}")

    def _trigger_workflow_next_tasks(self, task: CrawlerTask, session):
        """
        触发工作流的后续任务

        Args:
            task: 已完成的任务
            session: 数据库会话
        """
        if not task.workflow_id:
            return

        try:
            from ..workflow.task_chain import TaskChainManager

            chain_manager = TaskChainManager(session)
            chain_manager.on_task_complete(task)

        except Exception as e:
            logger.error(f"触发工作流后续任务失败: {e}", exc_info=True)

    def start_worker_loop(self):
        """启动工作循环"""
        logger.info("任务队列工作循环已启动")

        while not self._shutdown_event.is_set():
            # 执行下一个任务
            self.execute_next_task()

            # 短暂休眠，避免CPU占用过高
            time.sleep(0.1)

    def shutdown(self, wait=True, timeout=30):
        """
        关闭任务队列

        Args:
            wait: 是否等待队列中的任务完成
            timeout: 等待超时时间（秒）
        """
        logger.info(f"关闭任务队列中... (wait={wait}, timeout={timeout}s)")

        if wait:
            logger.info("等待队列中的任务完成...")

            # 等待队列清空或超时
            start_time = time.time()
            while not self.task_queue.empty() and (time.time() - start_time < timeout):
                logger.info(f"队列中还有 {self.task_queue.qsize()} 个任务")
                time.sleep(1)

        # 设置关闭标志
        self._shutdown_event.set()

        # 关闭执行器
        if self.executor:
            logger.info("关闭执行器...")
            self.executor.shutdown(wait=True)

        logger.info("任务队列已关闭")

    def get_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        with self._lock:
            return {
                "mode": self.mode,
                "max_workers": self.max_workers,
                "queue_depth": self.task_queue.qsize(),
                "running_tasks": len(self.running_tasks),
                "completed_tasks": len(self.completed_tasks),
                "failed_tasks": len(self.failed_tasks),
                "active_workers": self.stats["active_workers"],
                "total_submitted": self.stats["total_submitted"],
                "total_completed": self.stats["total_completed"],
                "total_failed": self.stats["total_failed"],
            }

    def get_task_status(self, task_id: int) -> Optional[str]:
        """获取任务状态"""
        try:
            db = get_crawler_db()
            with db.session_scope() as session:
                task = session.query(CrawlerTask).filter(
                    CrawlerTask.id == task_id
                ).first()

                if task:
                    return task.status.value if hasattr(task.status, 'value') else str(task.status)
                return None
        except Exception as e:
            logger.error(f"获取任务状态失败: {e}")
            return None

    def cancel_task(self, task_id: int) -> bool:
        """取消任务（仅适用于未开始的任务）"""
        try:
            db = get_crawler_db()
            with db.session_scope() as session:
                task = session.query(CrawlerTask).filter(
                    CrawlerTask.id == task_id
                ).first()

                if not task:
                    logger.error(f"任务 {task_id} 不存在")
                    return False

                if task.status != TaskStatus.PENDING:
                    logger.warning(f"任务 {task_id} 状态为 {task.status}，无法取消")
                    return False

                # 标记为已取消
                task.status = TaskStatus.FAILED
                task.error_message = "用户取消"
                logger.info(f"任务 {task_id} 已取消")

            return True

        except Exception as e:
            logger.error(f"取消任务 {task_id} 失败: {e}")
            return False

    def retry_task(self, task_id: int) -> bool:
        """重试失败的任务"""
        try:
            db = get_crawler_db()
            with db.session_scope() as session:
                task = session.query(CrawlerTask).filter(
                    CrawlerTask.id == task_id
                ).first()

                if not task:
                    logger.error(f"找不到任务 {task_id}")
                    return False

                if task.status != TaskStatus.FAILED:
                    logger.warning(f"任务 {task_id} 状态为 {task.status}，无法重试")
                    return False

                # 获取配置
                config = json.loads(task.config) if task.config else {}
                config["is_retry"] = True

                # 增加重试次数
                current_retry = task.retry_count or 0
                task.retry_count = current_retry + 1
                task.status = TaskStatus.PENDING
                task.error_message = None

            # 重新提交到队列
            priority = 5  # 重试任务优先级较高
            self.submit(task_id, priority, config)

            logger.info(f"任务 {task_id} 已重新提交，当前重试次数: {current_retry + 1}")
            return True

        except Exception as e:
            logger.error(f"重试任务 {task_id} 失败: {e}")
            return False


# 全局任务队列实例（将在应用启动时初始化）
task_queue: Optional[CrawlerTaskQueue] = None


def initialize_task_queue(mode="subprocess", max_workers=3):
    """初始化全局任务队列"""
    global task_queue
    task_queue = CrawlerTaskQueue(mode=mode, max_workers=max_workers)
    return task_queue


def get_task_queue() -> CrawlerTaskQueue:
    """获取全局任务队列实例"""
    if task_queue is None:
        raise RuntimeError("任务队列未初始化，请先调用 initialize_task_queue()")
    return task_queue


def shutdown_task_queue(wait=True, timeout=30):
    """关闭全局任务队列"""
    global task_queue
    if task_queue:
        task_queue.shutdown(wait=wait, timeout=timeout)
        task_queue = None