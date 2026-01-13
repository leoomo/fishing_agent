"""
Crawler Worker

分布式Worker节点主进程

优化版本:
- 智能任务轮询 (指数退避算法)
- 任务取消机制
- 图片有序并发上传
- 移除冗余线程
"""

import asyncio
import json
import logging
import os
import signal
import sys
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any

import psutil

from .client import WorkerClient

logger = logging.getLogger(__name__)


class TaskCancelledException(Exception):
    """任务被取消异常"""
    pass


@dataclass
class TaskPoller:
    """
    智能任务轮询器 - 指数退避算法

    - 有任务时: 快速轮询 (min_interval)
    - 无任务时: 逐渐增加间隔，最大到 max_interval
    - 获取到任务后: 立即重置为 min_interval
    """
    min_interval: float = 1.0
    max_interval: float = 30.0
    backoff_factor: float = 1.5
    current_interval: float = field(init=False)
    consecutive_empty: int = field(init=False, default=0)

    def __post_init__(self):
        self.current_interval = self.min_interval

    def get_interval(self, has_tasks: bool) -> float:
        """
        获取下一次轮询间隔

        Args:
            has_tasks: 本次是否获取到任务

        Returns:
            下一次轮询间隔（秒）
        """
        if has_tasks:
            # 有任务，重置为最小间隔
            self.consecutive_empty = 0
            self.current_interval = self.min_interval
        else:
            # 无任务，指数增长
            self.consecutive_empty += 1
            self.current_interval = min(
                self.current_interval * self.backoff_factor,
                self.max_interval
            )
        return self.current_interval

    def reset(self):
        """重置轮询器状态"""
        self.current_interval = self.min_interval
        self.consecutive_empty = 0


@dataclass
class WorkerConfig:
    """Worker配置"""
    master_url: str
    node_id: Optional[str] = None
    node_secret: Optional[str] = None
    node_name: str = "Worker Node"
    capabilities: List[str] = None
    max_concurrent_tasks: int = 1
    heartbeat_interval: int = 30
    headless: bool = True
    location: Optional[str] = None
    worker_version: str = "1.0.0"

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = ["all"]

    @classmethod
    def from_dict(cls, data: Dict) -> "WorkerConfig":
        return cls(
            master_url=data['master_url'],
            node_id=data.get('node_id'),
            node_secret=data.get('node_secret'),
            node_name=data.get('node_name', 'Worker Node'),
            capabilities=data.get('capabilities', ['all']),
            max_concurrent_tasks=data.get('max_concurrent_tasks', 1),
            heartbeat_interval=data.get('heartbeat_interval', 30),
            headless=data.get('headless', True),
            location=data.get('location'),
            worker_version=data.get('worker_version', '1.0.0'),
        )

    @classmethod
    def from_file(cls, path: str) -> "WorkerConfig":
        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> Dict:
        return {
            'master_url': self.master_url,
            'node_id': self.node_id,
            'node_secret': self.node_secret,
            'node_name': self.node_name,
            'capabilities': self.capabilities,
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'heartbeat_interval': self.heartbeat_interval,
            'headless': self.headless,
            'location': self.location,
            'worker_version': self.worker_version,
        }

    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class CrawlerWorker:
    """
    分布式Worker节点主进程 (RPA模式)

    核心职责:
    - 定时心跳
    - 任务获取与认领 (智能轮询)
    - 复用现有RPA执行任务 (TaobaoRPA, TaobaoShopRPA等)
    - 结果实时上报
    - 图片下载与有序并发上传
    - 任务取消支持

    注意: RPA需要图形界面环境，建议:
    - Linux: 使用Xvfb虚拟显示
    - Docker: 需要headless模式
    """

    def __init__(self, config: WorkerConfig):
        """
        初始化Worker

        Args:
            config: Worker配置
        """
        self.config = config
        self.client: Optional[WorkerClient] = None
        self.running = False
        self.draining = False

        # 任务管理 - 存储 Future 而非 Thread
        self.current_tasks: Dict[int, Future] = {}
        self.task_executor = ThreadPoolExecutor(max_workers=config.max_concurrent_tasks)

        # 任务取消事件
        self.cancel_events: Dict[int, threading.Event] = {}

        # 智能轮询器
        self.task_poller = TaskPoller(
            min_interval=1.0,
            max_interval=30.0,
            backoff_factor=1.5
        )

        # 图片上传线程池
        self.image_upload_executor = ThreadPoolExecutor(max_workers=4)

        # 平台注册器（延迟导入）
        self._platform_registry = None

        # 信号处理
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    @property
    def platform_registry(self):
        """延迟加载平台注册器"""
        if self._platform_registry is None:
            try:
                from ..platform.registry import platform_registry
                self._platform_registry = platform_registry
            except ImportError as e:
                logger.warning(f"Platform registry not available: {e}")
                self._platform_registry = None
        return self._platform_registry

    def _handle_signal(self, signum, frame):
        """处理终止信号"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

    def start(self):
        """
        启动Worker

        流程:
        1. 认证（如果没有node_id则注册）
        2. 启动心跳线程
        3. 启动任务获取循环
        """
        logger.info(f"Starting Crawler Worker...")
        logger.info(f"  Master URL: {self.config.master_url}")
        logger.info(f"  Node Name: {self.config.node_name}")
        logger.info(f"  Capabilities: {self.config.capabilities}")
        logger.info(f"  Max Concurrent Tasks: {self.config.max_concurrent_tasks}")

        # 初始化客户端
        if not self.config.node_id or not self.config.node_secret:
            # 需要注册
            if not self._register():
                raise RuntimeError("Failed to register node")
        else:
            # 已有凭证，直接创建客户端
            self.client = WorkerClient(
                master_url=self.config.master_url,
                node_id=self.config.node_id,
                node_secret=self.config.node_secret,
            )

        # 认证
        if not self.client.authenticate():
            raise RuntimeError("Failed to authenticate")

        self.running = True

        # 启动心跳线程
        heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name="heartbeat",
        )
        heartbeat_thread.start()

        # 主循环: 获取并执行任务
        logger.info("Worker started, entering task loop...")
        self._task_loop()

    def stop(self):
        """停止Worker"""
        logger.info("Stopping Worker...")
        self.running = False
        self.draining = True

        # 等待当前任务完成
        if self.current_tasks:
            logger.info(f"Waiting for {len(self.current_tasks)} tasks to complete...")
            for task_id, future in list(self.current_tasks.items()):
                try:
                    future.result(timeout=60)
                except Exception as e:
                    logger.warning(f"Task {task_id} did not complete properly: {e}")

        self.task_executor.shutdown(wait=True)
        self.image_upload_executor.shutdown(wait=True)
        logger.info("Worker stopped")

    def cancel_task(self, task_id: int) -> bool:
        """
        取消指定任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功发送取消信号
        """
        if task_id in self.cancel_events:
            self.cancel_events[task_id].set()
            logger.info(f"Cancel signal sent to task {task_id}")
            return True
        else:
            logger.warning(f"Task {task_id} not found in cancel_events")
            return False

    def _check_cancelled(self, task_id: int):
        """
        检查任务是否被取消

        Args:
            task_id: 任务ID

        Raises:
            TaskCancelledException: 如果任务被取消
        """
        if task_id in self.cancel_events and self.cancel_events[task_id].is_set():
            raise TaskCancelledException(f"Task {task_id} was cancelled")

    def _register(self) -> bool:
        """注册新节点"""
        import requests

        try:
            url = f"{self.config.master_url}/api/v1/nodes/register"
            response = requests.post(url, json={
                'node_name': self.config.node_name,
                'capabilities': self.config.capabilities,
                'max_concurrent_tasks': self.config.max_concurrent_tasks,
                'worker_version': self.config.worker_version,
                'location': self.config.location,
            }, timeout=30)
            response.raise_for_status()

            data = response.json()
            self.config.node_id = data['node_id']
            self.config.node_secret = data['node_secret']

            # 创建客户端
            self.client = WorkerClient(
                master_url=self.config.master_url,
                node_id=self.config.node_id,
                node_secret=self.config.node_secret,
            )
            self.client.token = data['token']

            logger.info(f"Node registered: {self.config.node_id}")
            logger.warning("IMPORTANT: Save the node_secret, it will not be shown again!")

            return True

        except Exception as e:
            logger.error(f"Failed to register: {e}")
            return False

    def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            try:
                # 收集系统指标
                cpu_usage = psutil.cpu_percent()
                memory_usage = psutil.virtual_memory().percent
                disk_usage = psutil.disk_usage('/').percent

                # 发送心跳
                response = self.client.heartbeat(
                    current_tasks=len(self.current_tasks),
                    running_task_ids=list(self.current_tasks.keys()),
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    disk_usage=disk_usage,
                    worker_version=self.config.worker_version,
                )

                if response:
                    # 处理心跳响应
                    status = response.get('status', 'ok')
                    if status == 'drain':
                        logger.info("Received drain signal, stopping task acquisition")
                        self.draining = True
                    elif status == 'shutdown':
                        logger.info("Received shutdown signal")
                        self.stop()
                        return

                    # 处理需要取消的任务
                    cancel_tasks = response.get('cancel_tasks', [])
                    for task_id in cancel_tasks:
                        if self.cancel_task(task_id):
                            logger.info(f"Task {task_id} cancellation requested by server")

                    # 更新心跳间隔
                    interval = response.get('next_heartbeat_seconds', self.config.heartbeat_interval)
                else:
                    interval = self.config.heartbeat_interval

            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                interval = self.config.heartbeat_interval

            time.sleep(interval)

    def _task_loop(self):
        """任务获取循环 - 使用智能轮询"""
        while self.running:
            try:
                # 清理已完成的任务
                self._cleanup_completed_tasks()

                # 检查是否可以接受新任务
                if self.draining:
                    time.sleep(5)
                    continue

                if len(self.current_tasks) >= self.config.max_concurrent_tasks:
                    time.sleep(2)
                    continue

                # 获取可用任务
                tasks = self.client.get_tasks(limit=1)
                has_tasks = bool(tasks)

                if not tasks:
                    # 使用智能轮询间隔
                    interval = self.task_poller.get_interval(has_tasks=False)
                    logger.debug(f"No tasks available, waiting {interval:.1f}s")
                    time.sleep(interval)
                    continue

                # 有任务，重置轮询间隔
                self.task_poller.get_interval(has_tasks=True)

                # 认领并执行第一个任务
                task = tasks[0]
                task_id = task['id']

                # 认领任务
                claimed = self.client.claim_task(task_id)
                if not claimed:
                    logger.warning(f"Failed to claim task {task_id}")
                    continue

                logger.info(f"Claimed task {task_id}: {task.get('task_type')}")

                # 创建取消事件
                self.cancel_events[task_id] = threading.Event()

                # 直接使用线程池执行任务（移除冗余的 Thread 包装）
                future = self.task_executor.submit(self._execute_task, claimed)
                self.current_tasks[task_id] = future

            except Exception as e:
                logger.error(f"Task loop error: {e}")
                time.sleep(5)

    def _cleanup_completed_tasks(self):
        """清理已完成的任务"""
        completed = []
        for task_id, future in list(self.current_tasks.items()):
            if future.done():
                completed.append(task_id)
                # 清理取消事件
                if task_id in self.cancel_events:
                    del self.cancel_events[task_id]

        for task_id in completed:
            del self.current_tasks[task_id]
            logger.debug(f"Cleaned up completed task {task_id}")

    def _execute_task(self, task_data: Dict):
        """
        执行任务 - 复用现有RPA平台

        Args:
            task_data: 任务数据
        """
        task_id = task_data['id']
        task_type = task_data.get('task_type', 'unknown')

        logger.info(f"Executing task {task_id} ({task_type})")

        try:
            # 检查是否已被取消
            self._check_cancelled(task_id)

            # 解析任务配置
            config = task_data.get('config', {})
            if isinstance(config, str):
                config = json.loads(config)

            # 创建临时目录用于图片
            with tempfile.TemporaryDirectory(prefix=f'crawler_{task_id}_') as tmp_dir:
                tmp_path = Path(tmp_dir)

                # 检查是否已被取消
                self._check_cancelled(task_id)

                # 根据任务类型执行
                if self.platform_registry:
                    result = self._execute_with_platform(task_id, task_data, config, tmp_path)
                else:
                    # 平台注册器不可用时，拒绝执行并报告错误
                    raise RuntimeError(
                        "Platform registry not available - cannot execute task. "
                        "Please ensure the platform module is properly installed."
                    )

                # 检查是否已被取消
                self._check_cancelled(task_id)

                # 上报完成
                self.client.complete_task(
                    task_id,
                    success_items=result.get('success_items', 0),
                    failed_items=result.get('failed_items', 0),
                    total_items=result.get('total_items', 0),
                    duplicate_items=result.get('duplicate_items', 0),
                    result_summary=result.get('summary'),
                    result_data=result.get('data'),
                    image_stats=result.get('image_stats'),
                )

        except TaskCancelledException:
            logger.info(f"Task {task_id} was cancelled")
            self.client.fail_task(
                task_id,
                error_message="Task cancelled by user",
                error_details={'cancelled': True},
                should_retry=False,
            )

        except Exception as e:
            logger.exception(f"Task {task_id} failed: {e}")
            self.client.fail_task(
                task_id,
                error_message=str(e),
                error_details={'traceback': str(e)},
                should_retry=True,
            )

        finally:
            # 清理取消事件
            if task_id in self.cancel_events:
                del self.cancel_events[task_id]

    def _execute_with_platform(
        self,
        task_id: int,
        task_data: Dict,
        config: Dict,
        tmp_path: Path,
    ) -> Dict:
        """
        使用平台注册器执行任务

        Args:
            task_id: 任务ID
            task_data: 任务数据
            config: 任务配置
            tmp_path: 临时目录

        Returns:
            执行结果
        """
        from ..platform.base_platform import TaskConfig, TaskType

        # 构建TaskConfig
        task_config = TaskConfig(
            task_type=TaskType(config.get('task_type', 'keyword_search')),
            keywords=config.get('keywords'),
            shop_url=task_data.get('shop_url'),
            max_pages=config.get('max_pages', 5),
            timeout=task_data.get('timeout_seconds', 300),
        )

        # 获取平台
        platform = self.platform_registry.get_platform_for_config(task_config)

        if not platform:
            raise ValueError(f"No platform found for task type: {config.get('task_type')}")

        # 检查是否已被取消
        self._check_cancelled(task_id)

        # 进度回调（带取消检查）
        def on_progress(msg: str, percent: int):
            self._check_cancelled(task_id)
            self.client.report_progress(task_id, percent, msg)

        # 异步执行RPA爬虫
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(platform.crawl(task_config, on_progress))
        finally:
            loop.close()

        # 检查是否已被取消
        self._check_cancelled(task_id)

        # 收集所有需要处理的图片（保持顺序）
        all_images = []
        for item in result.items:
            images = item.get('images', [])
            equipment_name = item.get('name', 'unknown')

            for idx, img_info in enumerate(images):
                img_url = img_info.get('url')
                img_type = img_info.get('type', 'detail')

                if img_url:
                    all_images.append({
                        'index': len(all_images),  # 全局索引，保证顺序
                        'url': img_url,
                        'type': img_type,
                        'equipment_name': equipment_name,
                    })

        # 有序并发处理图片
        image_stats = self._process_images_ordered(task_id, all_images, tmp_path)

        return {
            'success_items': len(result.items),
            'failed_items': 0,
            'total_items': result.total_count,
            'duplicate_items': 0,
            'summary': {'platform': platform.name},
            'data': result.items,
            'image_stats': image_stats,
        }

    def _process_images_ordered(
        self,
        task_id: int,
        images: List[Dict],
        tmp_path: Path,
    ) -> Dict[str, int]:
        """
        有序并发处理图片 - 使用 executor.map() 保证顺序

        Args:
            task_id: 任务ID
            images: 图片信息列表（已按顺序排列）
            tmp_path: 临时目录

        Returns:
            图片处理统计
        """
        image_stats = {'downloaded': 0, 'uploaded': 0, 'duplicates': 0, 'errors': 0}

        if not images:
            return image_stats

        def process_single_image(img_info: Dict) -> Dict:
            """处理单张图片"""
            result = {
                'index': img_info['index'],
                'status': 'error',
                'downloaded': False,
                'uploaded': False,
            }

            try:
                # 检查是否已被取消
                self._check_cancelled(task_id)

                # 下载图片
                img_path = self._download_image(img_info['url'], tmp_path)
                if not img_path:
                    return result

                result['downloaded'] = True

                # 上传到Master
                upload_result = self.client.upload_image(
                    task_id,
                    img_path,
                    img_info['type'],
                    img_info['url'],
                    img_info['equipment_name']
                )

                if upload_result:
                    result['status'] = upload_result.get('status', 'error')
                    if result['status'] == 'saved':
                        result['uploaded'] = True

            except TaskCancelledException:
                result['status'] = 'cancelled'
                raise
            except Exception as e:
                logger.error(f"Image processing error for {img_info['url']}: {e}")
                result['status'] = 'error'

            return result

        try:
            # 使用 executor.map() 保证结果顺序与输入顺序一致
            # map() 内部并发执行，但按顺序返回结果
            results = list(self.image_upload_executor.map(process_single_image, images))

            # 按顺序统计结果（results 顺序与 images 完全一致）
            for result in results:
                if result['downloaded']:
                    image_stats['downloaded'] += 1
                if result['uploaded']:
                    image_stats['uploaded'] += 1
                elif result['status'] == 'duplicate':
                    image_stats['duplicates'] += 1
                elif result['status'] == 'error':
                    image_stats['errors'] += 1

        except TaskCancelledException:
            raise
        except Exception as e:
            logger.error(f"Batch image processing error: {e}")

        return image_stats

    def _download_image(self, url: str, save_dir: Path) -> Optional[Path]:
        """
        下载图片

        Args:
            url: 图片URL
            save_dir: 保存目录

        Returns:
            本地路径或None
        """
        import hashlib
        import requests

        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()

            # 确定扩展名
            content_type = response.headers.get('Content-Type', '')
            ext = '.jpg'
            if 'png' in content_type:
                ext = '.png'
            elif 'gif' in content_type:
                ext = '.gif'
            elif 'webp' in content_type:
                ext = '.webp'

            # 使用URL哈希作为文件名
            url_hash = hashlib.md5(url.encode()).hexdigest()
            file_path = save_dir / f'{url_hash}{ext}'

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return file_path

        except Exception as e:
            logger.error(f"Failed to download image {url}: {e}")
            return None
