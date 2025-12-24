"""
OCR Worker - 分布式 OCR 文本提取 Worker

从服务端领取 OCR 任务，下载图片，执行 OCR 识别，返回结果。
"""

import io
import json
import logging
import os
import signal
import shutil
import sys
import threading
import time
import uuid
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class OCRWorkerClient:
    """OCR Worker HTTP 客户端"""

    def __init__(
        self,
        server_url: str,
        worker_id: str,
        ocr_provider: str = "ollama",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self.server_url = server_url.rstrip("/")
        self.worker_id = worker_id
        self.ocr_provider = ocr_provider
        self.timeout = timeout
        self.token: Optional[str] = None

        # HTTP Session
        self.session = self._create_session(max_retries)

    def _create_session(self, max_retries: int) -> requests.Session:
        """创建带重试机制的 HTTP Session"""
        session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
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

        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败 [{method} {endpoint}]: {e}")
            raise

    def register(self) -> bool:
        """注册 Worker"""
        try:
            response = self._request(
                "POST",
                "/register",
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
                    logger.info(f"注册成功: worker_id={self.worker_id}")
                    return True

            logger.error(f"注册失败: {response.text}")
            return False

        except Exception as e:
            logger.error(f"注册异常: {e}")
            return False

    def claim_tasks(self, max_tasks: int = 1) -> List[Dict]:
        """领取任务"""
        try:
            response = self._request(
                "POST",
                "/claim",
                json={
                    "worker_id": self.worker_id,
                    "max_tasks": max_tasks,
                },
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("tasks", [])

            logger.error(f"领取任务失败: {response.text}")
            return []

        except Exception as e:
            logger.error(f"领取任务异常: {e}")
            return []

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
                "POST",
                "/report",
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
                data = response.json()
                logger.info(f"汇报成功: pending_id={pending_id}, message={data.get('message')}")
                return data.get("success", False)

            logger.error(f"汇报失败: {response.text}")
            return False

        except Exception as e:
            logger.error(f"汇报异常: {e}")
            return False

    def heartbeat(self, current_tasks: List[int]) -> Dict:
        """发送心跳"""
        try:
            response = self._request(
                "POST",
                "/heartbeat",
                json={
                    "worker_id": self.worker_id,
                    "current_tasks": current_tasks,
                },
            )

            if response.status_code == 200:
                return response.json()

            return {"success": False}

        except Exception as e:
            logger.debug(f"心跳异常: {e}")
            return {"success": False}

    def download_images(self, pending_id: int, output_dir: Path) -> List[Path]:
        """下载图片"""
        try:
            # 下载 ZIP 文件
            response = self._request(
                "GET",
                f"/images/{pending_id}",
                timeout=60,
                headers={"Accept": "application/zip"},
            )

            if response.status_code != 200:
                logger.error(f"下载图片失败: {response.status_code}")
                return []

            # 解压到输出目录
            output_dir.mkdir(parents=True, exist_ok=True)

            zip_buffer = io.BytesIO(response.content)
            with zipfile.ZipFile(zip_buffer, "r") as zip_file:
                zip_file.extractall(output_dir)

            # 返回图片文件列表
            image_files = list(output_dir.rglob("*"))
            image_files = [f for f in image_files if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]

            logger.info(f"下载图片成功: pending_id={pending_id}, count={len(image_files)}")
            return image_files

        except Exception as e:
            logger.error(f"下载图片异常: {e}")
            return []


class OCRWorker:
    """
    分布式 OCR Worker

    功能:
    - 注册到服务端获取认证 Token
    - 定期轮询领取 OCR 任务
    - 下载图片并执行 OCR 识别
    - 汇报处理结果
    - 发送心跳保持连接
    """

    def __init__(
        self,
        server_url: str,
        worker_id: Optional[str] = None,
        ocr_provider: str = "ollama",
        poll_interval: int = 5,
        heartbeat_interval: int = 30,
        cache_dir: str = "/tmp/ocr_worker_cache",
    ):
        """
        初始化 OCR Worker

        Args:
            server_url: 服务器地址
            worker_id: Worker ID (自动生成)
            ocr_provider: OCR 提供商 (ollama/siliconflow)
            poll_interval: 轮询间隔 (秒)
            heartbeat_interval: 心跳间隔 (秒)
            cache_dir: 图片缓存目录
        """
        self.server_url = server_url.rstrip("/")
        self.worker_id = worker_id or f"ocr-{uuid.uuid4().hex[:8]}"
        self.ocr_provider = ocr_provider
        self.poll_interval = poll_interval
        self.heartbeat_interval = heartbeat_interval
        self.cache_dir = Path(cache_dir)

        # 运行状态
        self.running = False
        self.current_tasks: List[int] = []

        # HTTP 客户端
        self.client = OCRWorkerClient(
            server_url=server_url,
            worker_id=self.worker_id,
            ocr_provider=ocr_provider,
        )

        # OCR 提供商实例 (延迟初始化)
        self._ocr_provider = None

        # 线程
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._poll_thread: Optional[threading.Thread] = None

        # 信号处理
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        logger.info(
            f"OCR Worker 初始化: id={self.worker_id}, provider={self.ocr_provider}, "
            f"server={self.server_url}"
        )

    def _handle_signal(self, signum, _frame):
        """处理终止信号"""
        logger.info(f"收到信号 {signum}，准备退出...")
        self.stop()
        sys.exit(0)

    def _get_ocr_provider(self):
        """获取 OCR 提供商实例"""
        if self._ocr_provider is None:
            from apps.api.services.ocr.factory import OCRProviderFactory

            self._ocr_provider = OCRProviderFactory.create_provider(self.ocr_provider)
            logger.info(f"OCR 提供商初始化: {self.ocr_provider}")

        return self._ocr_provider

    def start(self) -> bool:
        """启动 Worker"""
        logger.info("正在启动 OCR Worker...")

        # 创建缓存目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 注册
        if not self.client.register():
            logger.error("注册失败，无法启动")
            return False

        self.running = True

        # 启动心跳线程
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name="ocr-heartbeat",
        )
        self._heartbeat_thread.start()

        # 启动轮询线程
        self._poll_thread = threading.Thread(
            target=self._poll_loop,
            daemon=True,
            name="ocr-poll",
        )
        self._poll_thread.start()

        logger.info(
            f"OCR Worker 已启动: poll_interval={self.poll_interval}s, "
            f"heartbeat_interval={self.heartbeat_interval}s"
        )

        return True

    def stop(self):
        """停止 Worker"""
        logger.info("正在停止 OCR Worker...")
        self.running = False

        # 等待线程结束
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=5)
        if self._poll_thread:
            self._poll_thread.join(timeout=5)

        # 清理缓存
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir, ignore_errors=True)

        logger.info("OCR Worker 已停止")

    def run_forever(self):
        """持续运行直到收到终止信号"""
        if not self.start():
            return

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            try:
                self.client.heartbeat(self.current_tasks)
            except Exception as e:
                logger.debug(f"心跳失败: {e}")

            time.sleep(self.heartbeat_interval)

    def _poll_loop(self):
        """轮询循环"""
        while self.running:
            try:
                # 领取任务
                tasks = self.client.claim_tasks(max_tasks=1)

                for task in tasks:
                    pending_id = task.get("pending_id")
                    if pending_id:
                        self.current_tasks.append(pending_id)

                        # 在新线程中执行任务
                        thread = threading.Thread(
                            target=self._execute_task,
                            args=(task,),
                            daemon=True,
                            name=f"ocr-task-{pending_id}",
                        )
                        thread.start()

            except Exception as e:
                logger.error(f"轮询失败: {e}")

            time.sleep(self.poll_interval)

    def _execute_task(self, task: Dict):
        """执行单个 OCR 任务"""
        pending_id = task.get("pending_id")
        start_time = time.time()

        try:
            logger.info(f"开始处理任务: pending_id={pending_id}")

            # 1. 下载图片
            task_cache_dir = self.cache_dir / str(pending_id)
            image_files = self.client.download_images(pending_id, task_cache_dir)

            if not image_files:
                raise Exception("无法下载图片或图片不存在")

            # 2. 执行 OCR
            ocr_provider = self._get_ocr_provider()
            image_paths = [str(f) for f in image_files]

            result = ocr_provider.recognize_table_from_paths(image_paths)

            if result.get("success"):
                ocr_text = result.get("markdown", "")
                processing_time_ms = int((time.time() - start_time) * 1000)

                # 3. 汇报成功
                self.client.report_result(
                    pending_id=pending_id,
                    status="success",
                    ocr_text=ocr_text,
                    processing_time_ms=processing_time_ms,
                )

                logger.info(
                    f"任务完成: pending_id={pending_id}, "
                    f"text_length={len(ocr_text)}, time={processing_time_ms}ms"
                )
            else:
                raise Exception(result.get("error", "OCR 识别失败"))

        except Exception as e:
            logger.error(f"任务失败: pending_id={pending_id}, error={e}")

            processing_time_ms = int((time.time() - start_time) * 1000)
            self.client.report_result(
                pending_id=pending_id,
                status="failed",
                error_message=str(e),
                processing_time_ms=processing_time_ms,
            )

        finally:
            # 清理任务缓存
            task_cache_dir = self.cache_dir / str(pending_id)
            if task_cache_dir.exists():
                shutil.rmtree(task_cache_dir, ignore_errors=True)

            # 从当前任务列表移除
            if pending_id in self.current_tasks:
                self.current_tasks.remove(pending_id)
