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
        logger.info(f"正在注册 Worker: id={self.worker_id}, provider={self.ocr_provider}")
        start_time = time.time()

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

            elapsed = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.token = data.get("token")
                    logger.info(f"注册成功: worker_id={self.worker_id}, token已获取, 耗时={elapsed}ms")
                    return True

            logger.error(f"注册失败: status={response.status_code}, response={response.text}, 耗时={elapsed}ms")
            return False

        except Exception as e:
            elapsed = int((time.time() - start_time) * 1000)
            logger.error(f"注册异常: {e}, 耗时={elapsed}ms")
            return False

    def claim_tasks(self, max_tasks: int = 1) -> List[Dict]:
        """领取任务"""
        logger.debug(f"尝试领取任务: max_tasks={max_tasks}")
        start_time = time.time()

        try:
            response = self._request(
                "POST",
                "/claim",
                json={
                    "worker_id": self.worker_id,
                    "max_tasks": max_tasks,
                },
            )

            elapsed = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                data = response.json()
                tasks = data.get("tasks", [])
                if tasks:
                    task_ids = [t.get("pending_id") for t in tasks]
                    logger.info(f"领取任务成功: 数量={len(tasks)}, pending_ids={task_ids}, 耗时={elapsed}ms")
                else:
                    logger.debug(f"无可用任务, 耗时={elapsed}ms")
                return tasks

            logger.error(f"领取任务失败: status={response.status_code}, response={response.text}, 耗时={elapsed}ms")
            return []

        except Exception as e:
            elapsed = int((time.time() - start_time) * 1000)
            logger.error(f"领取任务异常: {e}, 耗时={elapsed}ms")
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
        text_length = len(ocr_text) if ocr_text else 0
        logger.debug(
            f"[任务 {pending_id}] 汇报结果: status={status}, "
            f"text_length={text_length}, processing_time={processing_time_ms}ms"
        )
        start_time = time.time()

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

            elapsed = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                data = response.json()
                logger.info(
                    f"[任务 {pending_id}] 汇报成功: status={status}, "
                    f"message={data.get('message')}, 耗时={elapsed}ms"
                )
                return data.get("success", False)

            logger.error(
                f"[任务 {pending_id}] 汇报失败: http_status={response.status_code}, "
                f"response={response.text}, 耗时={elapsed}ms"
            )
            return False

        except Exception as e:
            elapsed = int((time.time() - start_time) * 1000)
            logger.error(f"[任务 {pending_id}] 汇报异常: {e}, 耗时={elapsed}ms")
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
                data = response.json()
                task_info = f", 当前任务={current_tasks}" if current_tasks else ""
                logger.debug(f"心跳成功: worker_id={self.worker_id}{task_info}")
                return data

            logger.warning(f"心跳响应异常: status={response.status_code}")
            return {"success": False}

        except Exception as e:
            logger.warning(f"心跳失败: {e}")
            return {"success": False}

    def download_images(self, pending_id: int, output_dir: Path) -> List[Path]:
        """下载图片"""
        logger.debug(f"[任务 {pending_id}] 开始下载图片...")
        start_time = time.time()

        try:
            # 下载 ZIP 文件
            response = self._request(
                "GET",
                f"/images/{pending_id}",
                timeout=60,
                headers={"Accept": "application/zip"},
            )

            elapsed = int((time.time() - start_time) * 1000)

            if response.status_code != 200:
                logger.error(f"[任务 {pending_id}] 下载图片失败: status={response.status_code}, 耗时={elapsed}ms")
                return []

            # 记录 ZIP 文件大小
            zip_size = len(response.content)
            logger.debug(f"[任务 {pending_id}] ZIP 下载完成: 大小={zip_size/1024:.1f}KB, 耗时={elapsed}ms")

            # 解压到输出目录
            output_dir.mkdir(parents=True, exist_ok=True)

            zip_buffer = io.BytesIO(response.content)
            with zipfile.ZipFile(zip_buffer, "r") as zip_file:
                zip_file.extractall(output_dir)

            # 返回图片文件列表
            image_files = list(output_dir.rglob("*"))
            image_files = [f for f in image_files if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]

            # 计算总大小
            total_size = sum(f.stat().st_size for f in image_files) / 1024 / 1024

            logger.info(
                f"[任务 {pending_id}] 图片下载完成: 数量={len(image_files)}, "
                f"大小={total_size:.2f}MB, 耗时={elapsed}ms"
            )
            return image_files

        except Exception as e:
            elapsed = int((time.time() - start_time) * 1000)
            logger.error(f"[任务 {pending_id}] 下载图片异常: {e}, 耗时={elapsed}ms")
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
        self._stats_thread: Optional[threading.Thread] = None

        # 统计数据
        self._stats = {
            "start_time": None,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_processing_time_ms": 0,
            "total_download_time_ms": 0,
            "total_ocr_time_ms": 0,
        }
        self._stats_lock = threading.Lock()

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

    def _update_stats(
        self,
        success: bool,
        processing_time_ms: int = 0,
        download_time_ms: int = 0,
        ocr_time_ms: int = 0,
    ):
        """更新统计数据"""
        with self._stats_lock:
            if success:
                self._stats["tasks_completed"] += 1
            else:
                self._stats["tasks_failed"] += 1
            self._stats["total_processing_time_ms"] += processing_time_ms
            self._stats["total_download_time_ms"] += download_time_ms
            self._stats["total_ocr_time_ms"] += ocr_time_ms

    @staticmethod
    def _format_size(bytes_size: int) -> str:
        """格式化文件大小"""
        if bytes_size < 1024:
            return f"{bytes_size}B"
        elif bytes_size < 1024 * 1024:
            return f"{bytes_size / 1024:.1f}KB"
        else:
            return f"{bytes_size / 1024 / 1024:.2f}MB"

    def _log_stats(self):
        """记录统计信息"""
        with self._stats_lock:
            start_time = self._stats["start_time"]
            if not start_time:
                return

            uptime = time.time() - start_time
            completed = self._stats["tasks_completed"]
            failed = self._stats["tasks_failed"]
            total = completed + failed

            if total == 0:
                logger.info(
                    f"Worker 统计: 运行时间={uptime/60:.1f}分钟, "
                    f"尚未处理任务"
                )
                return

            success_rate = (completed / total * 100) if total > 0 else 0
            avg_time = self._stats["total_processing_time_ms"] / total
            avg_download = self._stats["total_download_time_ms"] / total
            avg_ocr = self._stats["total_ocr_time_ms"] / total

            logger.info(
                f"Worker 统计: 运行时间={uptime/60:.1f}分钟, "
                f"完成={completed}, 失败={failed}, 成功率={success_rate:.1f}%, "
                f"平均耗时={avg_time:.0f}ms (下载={avg_download:.0f}ms, OCR={avg_ocr:.0f}ms)"
            )

    def _stats_loop(self):
        """统计日志循环 (每 5 分钟输出一次)"""
        stats_interval = 300  # 5 分钟
        while self.running:
            time.sleep(stats_interval)
            if self.running:
                self._log_stats()

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
        self._stats["start_time"] = time.time()

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

        # 启动统计线程
        self._stats_thread = threading.Thread(
            target=self._stats_loop,
            daemon=True,
            name="ocr-stats",
        )
        self._stats_thread.start()

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
        if self._stats_thread:
            self._stats_thread.join(timeout=5)

        # 输出最终统计
        self._log_stats()

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
        poll_count = 0
        while self.running:
            poll_count += 1
            try:
                # 领取任务
                tasks = self.client.claim_tasks(max_tasks=1)

                for task in tasks:
                    pending_id = task.get("pending_id")
                    if pending_id:
                        self.current_tasks.append(pending_id)
                        logger.debug(
                            f"启动任务线程: pending_id={pending_id}, "
                            f"当前任务数={len(self.current_tasks)}"
                        )

                        # 在新线程中执行任务
                        thread = threading.Thread(
                            target=self._execute_task,
                            args=(task,),
                            daemon=True,
                            name=f"ocr-task-{pending_id}",
                        )
                        thread.start()

            except Exception as e:
                logger.error(f"轮询失败: {e}", exc_info=True)

            # 每 60 次轮询输出一次状态（约 5 分钟，取决于 poll_interval）
            if poll_count % 60 == 0:
                logger.debug(
                    f"轮询状态: 已轮询{poll_count}次, "
                    f"当前任务数={len(self.current_tasks)}"
                )

            time.sleep(self.poll_interval)

    def _execute_task(self, task: Dict):
        """执行单个 OCR 任务"""
        pending_id = task.get("pending_id")
        brand_name = task.get("brand_name", "未知")
        images_count = task.get("images_count", 0)
        start_time = time.time()

        # 分阶段耗时统计
        download_time_ms = 0
        ocr_time_ms = 0
        report_time_ms = 0

        try:
            logger.info(
                f"[任务 {pending_id}] 开始处理: brand={brand_name}, "
                f"images={images_count}, provider={self.ocr_provider}"
            )

            # 1. 下载图片
            download_start = time.time()
            task_cache_dir = self.cache_dir / str(pending_id)
            image_files = self.client.download_images(pending_id, task_cache_dir)
            download_time_ms = int((time.time() - download_start) * 1000)

            if not image_files:
                raise Exception("无法下载图片或图片不存在")

            # 计算文件大小并输出
            total_size = sum(f.stat().st_size for f in image_files)
            logger.info(
                f"[任务 {pending_id}] 下载完成: "
                f"{len(image_files)} 张图片, "
                f"总大小={self._format_size(total_size)}, "
                f"耗时={download_time_ms}ms"
            )

            # 2. 执行 OCR
            logger.info(
                f"[任务 {pending_id}] 开始 OCR: provider={self.ocr_provider}, "
                f"images={len(image_files)}"
            )
            ocr_start = time.time()
            ocr_provider = self._get_ocr_provider()
            image_paths = [str(f) for f in image_files]

            result = ocr_provider.recognize_table_from_paths(image_paths)
            ocr_time_ms = int((time.time() - ocr_start) * 1000)

            if result.get("success"):
                ocr_text = result.get("markdown", "")

                # 从 metadata 提取处理统计
                metadata = result.get("metadata", {})
                output_files_count = metadata.get("output_files_count", 1)

                logger.info(
                    f"[任务 {pending_id}] OCR 完成: "
                    f"合并后={output_files_count} 个文件, "
                    f"文本长度={len(ocr_text)} 字符, "
                    f"耗时={ocr_time_ms}ms"
                )

                # 3. 汇报成功
                report_start = time.time()
                self.client.report_result(
                    pending_id=pending_id,
                    status="success",
                    ocr_text=ocr_text,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                )
                report_time_ms = int((time.time() - report_start) * 1000)

                total_time_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    f"[任务 {pending_id}] 处理完成: 总耗时={total_time_ms}ms "
                    f"(下载={download_time_ms}ms, OCR={ocr_time_ms}ms, 汇报={report_time_ms}ms)"
                )
                logger.info(
                    f"[任务 {pending_id}] 统计: "
                    f"原始图片={len(image_files)}, "
                    f"合并后={output_files_count}, "
                    f"文本={len(ocr_text)}字符"
                )

                # 更新统计
                self._update_stats(
                    success=True,
                    processing_time_ms=total_time_ms,
                    download_time_ms=download_time_ms,
                    ocr_time_ms=ocr_time_ms,
                )
            else:
                error_msg = result.get("error", "OCR 识别失败")
                error_code = result.get("error_code", "UNKNOWN")
                logger.warning(
                    f"[任务 {pending_id}] OCR 失败: error={error_msg}, "
                    f"error_code={error_code}, 耗时={ocr_time_ms}ms"
                )
                raise Exception(error_msg)

        except Exception as e:
            total_time_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[任务 {pending_id}] 处理失败: error={e}, 总耗时={total_time_ms}ms"
            )
            logger.debug(f"[任务 {pending_id}] 错误堆栈:", exc_info=True)

            self.client.report_result(
                pending_id=pending_id,
                status="failed",
                error_message=str(e),
                processing_time_ms=total_time_ms,
            )

            # 更新统计
            self._update_stats(
                success=False,
                processing_time_ms=total_time_ms,
                download_time_ms=download_time_ms,
                ocr_time_ms=ocr_time_ms,
            )

        finally:
            # 清理任务缓存
            task_cache_dir = self.cache_dir / str(pending_id)
            if task_cache_dir.exists():
                shutil.rmtree(task_cache_dir, ignore_errors=True)
                logger.debug(f"[任务 {pending_id}] 缓存已清理: {task_cache_dir}")

            # 从当前任务列表移除
            if pending_id in self.current_tasks:
                self.current_tasks.remove(pending_id)
