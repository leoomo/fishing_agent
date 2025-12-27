"""
OCR Worker - 简化版分布式 OCR 文本提取 Worker

单线程同步模式：注册 -> 轮询领取任务 -> 处理 -> 汇报 -> 循环
"""

import io
import logging
import os
import shutil
import time
import uuid
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class OCRWorker:
    """
    简化版 OCR Worker - 单线程同步执行

    功能:
    - 注册到服务端获取认证 Token
    - 轮询领取 OCR 任务
    - 下载图片并执行 OCR 识别
    - 汇报处理结果
    - 定期发送心跳
    """

    def __init__(
        self,
        server_url: str,
        worker_id: Optional[str] = None,
        ocr_provider: str = "ollama",
        poll_interval: int = 5,
        heartbeat_every: int = 6,
        cache_dir: str = "/tmp/ocr_worker_cache",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        初始化 OCR Worker

        Args:
            server_url: 服务器地址
            worker_id: Worker ID (自动生成)
            ocr_provider: OCR 提供商 (ollama/siliconflow/baidu)
            poll_interval: 轮询间隔 (秒)
            heartbeat_every: 每 N 次轮询发送一次心跳
            cache_dir: 图片缓存目录
            timeout: HTTP 请求超时 (秒)
            max_retries: HTTP 重试次数
        """
        self.server_url = server_url.rstrip("/")
        self.worker_id = worker_id or f"ocr-{uuid.uuid4().hex[:8]}"
        self.ocr_provider = ocr_provider
        self.poll_interval = poll_interval
        self.heartbeat_every = heartbeat_every
        self.cache_dir = Path(cache_dir)
        self.timeout = timeout

        # HTTP Session
        self.session = self._create_session(max_retries)
        self.token: Optional[str] = None

        # 运行状态
        self.running = False

        # OCR 提供商 (延迟初始化)
        self._ocr_provider_instance = None

        # 统计数据
        self.stats = {
            "start_time": None,
            "completed": 0,
            "failed": 0,
            "total_time_ms": 0,
        }

        logger.info(
            f"OCR Worker 初始化: id={self.worker_id}, provider={self.ocr_provider}, "
            f"server={self.server_url}"
        )

    def _create_session(self, max_retries: int) -> requests.Session:
        """创建带重试机制的 HTTP Session"""
        session = requests.Session()
        retry = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["X-Worker-Token"] = self.token
        return headers

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """发送 HTTP 请求"""
        url = f"{self.server_url}/api/v1/ocr-worker{endpoint}"

        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"].update(self._get_headers())

        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout

        return self.session.request(method, url, **kwargs)

    def _get_ocr_provider(self):
        """获取 OCR 提供商实例 (延迟初始化)"""
        if self._ocr_provider_instance is None:
            from apps.api.services.ocr.factory import OCRProviderFactory
            self._ocr_provider_instance = OCRProviderFactory.create_provider(self.ocr_provider)
            logger.info(f"OCR 提供商初始化: {self.ocr_provider}")
        return self._ocr_provider_instance

    # ==================== API 方法 ====================

    def register(self) -> bool:
        """注册 Worker 并获取 Token"""
        logger.info(f"正在注册 Worker: id={self.worker_id}, provider={self.ocr_provider}")

        try:
            response = self._request(
                "POST", "/register",
                json={
                    "worker_id": self.worker_id,
                    "worker_name": f"OCR-{self.worker_id[:8]}",
                    "ocr_provider": self.ocr_provider,
                    "max_concurrent": 1,
                },
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.token = data.get("token")
                    logger.info(f"注册成功: token 已获取")
                    return True

            logger.error(f"注册失败: {response.status_code} - {response.text}")
            return False

        except Exception as e:
            logger.error(f"注册异常: {e}")
            return False

    def claim_task(self) -> Optional[Dict]:
        """领取一个任务"""
        try:
            response = self._request(
                "POST", "/claim",
                json={"worker_id": self.worker_id, "max_tasks": 1},
            )

            if response.status_code == 200:
                data = response.json()
                tasks = data.get("tasks", [])
                if tasks:
                    task = tasks[0]
                    logger.info(f"领取任务: pending_id={task.get('pending_id')}")
                    return task
            return None

        except Exception as e:
            logger.error(f"领取任务失败: {e}")
            return None

    def report_result(
        self,
        pending_id: int,
        status: str,
        ocr_text: Optional[str] = None,
        error_message: Optional[str] = None,
        processing_time_ms: int = 0,
    ) -> bool:
        """汇报结果"""
        try:
            response = self._request(
                "POST", "/report",
                json={
                    "pending_id": pending_id,
                    "worker_id": self.worker_id,
                    "status": status,
                    "ocr_text": ocr_text,
                    "error_message": error_message,
                    "processing_time_ms": processing_time_ms,
                    "provider": self.ocr_provider,
                },
            )

            if response.status_code == 200:
                logger.info(f"[任务 {pending_id}] 汇报成功: status={status}")
                return True

            logger.error(f"[任务 {pending_id}] 汇报失败: {response.status_code}")
            return False

        except Exception as e:
            logger.error(f"[任务 {pending_id}] 汇报异常: {e}")
            return False

    def heartbeat(self) -> bool:
        """发送心跳"""
        try:
            response = self._request(
                "POST", "/heartbeat",
                json={"worker_id": self.worker_id, "current_tasks": []},
            )
            if response.status_code == 200:
                logger.debug("心跳成功")
                return True
            return False
        except Exception as e:
            logger.debug(f"心跳失败: {e}")
            return False

    def download_images(self, pending_id: int, output_dir: Path) -> List[Path]:
        """下载任务图片"""
        import re

        try:
            response = self._request(
                "GET", f"/images/{pending_id}",
                timeout=60,
                headers={"Accept": "application/zip"},
            )

            if response.status_code != 200:
                logger.error(f"[任务 {pending_id}] 下载失败: {response.status_code}")
                return []

            # 解压 ZIP
            output_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(io.BytesIO(response.content), "r") as zf:
                zf.extractall(output_dir)

            # 获取图片列表
            image_files = [
                f for f in output_dir.rglob("*")
                if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
            ]

            # 自然排序（确保 image_2 在 image_10 之前）
            def natural_sort_key(path: Path) -> tuple:
                numbers = re.findall(r'\d+', path.stem)
                if numbers:
                    # 使用最后一个数字作为排序键
                    return (path.suffix.lower(), int(numbers[-1]))
                return (path.suffix.lower(), path.name)

            image_files.sort(key=natural_sort_key)

            total_size = sum(f.stat().st_size for f in image_files) / 1024 / 1024
            logger.info(f"[任务 {pending_id}] 下载完成: {len(image_files)}张, {total_size:.2f}MB")

            return image_files

        except Exception as e:
            logger.error(f"[任务 {pending_id}] 下载异常: {e}")
            return []

    # ==================== 任务处理 ====================

    def process_task(self, task: Dict) -> bool:
        """处理单个任务"""
        pending_id = task.get("pending_id")
        brand_name = task.get("brand_name", "未知")
        images_count = task.get("images_count", 0)
        start_time = time.time()

        logger.info(f"[任务 {pending_id}] 开始处理: brand={brand_name}, images={images_count}")

        task_cache_dir = self.cache_dir / str(pending_id)

        try:
            # 1. 下载图片
            image_files = self.download_images(pending_id, task_cache_dir)
            if not image_files:
                raise Exception("下载图片失败")

            # 2. OCR 识别
            logger.info(f"[任务 {pending_id}] 开始 OCR...")
            ocr_start = time.time()
            provider = self._get_ocr_provider()
            result = provider.recognize_table_from_paths([str(f) for f in image_files])
            ocr_time = int((time.time() - ocr_start) * 1000)

            if not result.get("success"):
                raise Exception(result.get("error", "OCR 失败"))

            ocr_text = result.get("markdown", "")
            total_time = int((time.time() - start_time) * 1000)

            logger.info(
                f"[任务 {pending_id}] OCR 完成: {len(ocr_text)}字符, "
                f"耗时={total_time}ms (OCR={ocr_time}ms)"
            )

            # 3. 汇报成功
            self.report_result(
                pending_id=pending_id,
                status="success",
                ocr_text=ocr_text,
                processing_time_ms=total_time,
            )

            # 更新统计
            self.stats["completed"] += 1
            self.stats["total_time_ms"] += total_time
            return True

        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            logger.error(f"[任务 {pending_id}] 处理失败: {e}")

            self.report_result(
                pending_id=pending_id,
                status="failed",
                error_message=str(e),
                processing_time_ms=total_time,
            )

            self.stats["failed"] += 1
            return False

        finally:
            # 清理缓存
            if task_cache_dir.exists():
                shutil.rmtree(task_cache_dir, ignore_errors=True)

    # ==================== 运行控制 ====================

    def _log_stats(self):
        """输出统计信息"""
        start_time = self.stats.get("start_time")
        if not start_time:
            return

        uptime = time.time() - start_time
        completed = self.stats["completed"]
        failed = self.stats["failed"]
        total = completed + failed

        if total == 0:
            logger.info(f"Worker 统计: 运行{uptime/60:.1f}分钟, 尚未处理任务")
            return

        avg_time = self.stats["total_time_ms"] / total
        success_rate = completed / total * 100

        logger.info(
            f"Worker 统计: 运行{uptime/60:.1f}分钟, "
            f"完成={completed}, 失败={failed}, 成功率={success_rate:.0f}%, "
            f"平均耗时={avg_time:.0f}ms"
        )

    def run_forever(self):
        """持续运行 (主循环)"""
        # 创建缓存目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 注册
        if not self.register():
            logger.error("注册失败，退出")
            return

        self.running = True
        self.stats["start_time"] = time.time()
        poll_count = 0

        logger.info(f"Worker 已启动: poll_interval={self.poll_interval}s")

        try:
            while self.running:
                poll_count += 1

                # 心跳 (每 heartbeat_every 次轮询)
                if poll_count % self.heartbeat_every == 0:
                    self.heartbeat()

                # 领取并处理任务
                task = self.claim_task()
                if task:
                    self.process_task(task)

                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            logger.info("收到中断信号，退出...")
        finally:
            self.running = False
            self._log_stats()
            # 清理缓存
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir, ignore_errors=True)
            logger.info("Worker 已停止")

    def run_once(self):
        """处理一个任务后退出 (用于调试)"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if not self.register():
            logger.error("注册失败")
            return False

        task = self.claim_task()
        if task:
            result = self.process_task(task)
            return result
        else:
            logger.info("无可用任务")
            return False
