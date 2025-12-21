#!/usr/bin/env python3
"""
分布式爬虫 Worker 客户端

在远程服务器上运行此脚本，连接到主服务器领取并执行爬虫任务。

使用方法:
    python remote_worker.py --server http://your-server:8000 --name "Worker-1"

环境变量:
    WORKER_SERVER_URL: 主服务器地址 (默认: http://localhost:8000)
    WORKER_NAME: Worker 名称 (默认: 自动生成)
    WORKER_ID: Worker ID (默认: 自动生成)
    POLL_INTERVAL: 轮询间隔秒数 (默认: 5)
    HEARTBEAT_INTERVAL: 心跳间隔秒数 (默认: 30)
"""

import os
import sys
import time
import json
import uuid
import signal
import logging
import argparse
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RemoteWorker")


class RemoteWorker:
    """
    远程爬虫 Worker 客户端

    功能:
    - 注册到主服务器获取认证 Token
    - 定期轮询领取待执行任务
    - 执行任务并汇报进度/结果
    - 发送心跳保持连接
    """

    def __init__(
        self,
        server_url: str,
        worker_id: Optional[str] = None,
        worker_name: Optional[str] = None,
        supported_types: List[str] = None,
        max_concurrent: int = 1,
        poll_interval: int = 5,
        heartbeat_interval: int = 30
    ):
        """
        初始化 Worker

        Args:
            server_url: 主服务器地址
            worker_id: Worker ID (自动生成)
            worker_name: Worker 名称
            supported_types: 支持的任务类型
            max_concurrent: 最大并发任务数
            poll_interval: 轮询间隔 (秒)
            heartbeat_interval: 心跳间隔 (秒)
        """
        self.server_url = server_url.rstrip("/")
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.worker_name = worker_name or f"RemoteWorker-{self.worker_id[-8:]}"
        self.supported_types = supported_types or ["taobao", "jd", "forum"]
        self.max_concurrent = max_concurrent
        self.poll_interval = poll_interval
        self.heartbeat_interval = heartbeat_interval

        # 认证 Token
        self.token: Optional[str] = None

        # 运行状态
        self.running = False
        self.current_tasks: List[int] = []

        # HTTP Session (带重试)
        self.session = self._create_session()

        # 线程
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._poll_thread: Optional[threading.Thread] = None

        logger.info(
            f"Worker 初始化: id={self.worker_id}, name={self.worker_name}, "
            f"server={self.server_url}"
        )

    def _create_session(self) -> requests.Session:
        """创建带重试机制的 HTTP Session"""
        session = requests.Session()

        retry_strategy = Retry(
            total=3,
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

    def register(self) -> bool:
        """注册到主服务器"""
        url = f"{self.server_url}/api/v1/worker/register"

        payload = {
            "worker_id": self.worker_id,
            "worker_name": self.worker_name,
            "supported_types": self.supported_types,
            "max_concurrent": self.max_concurrent
        }

        try:
            response = self.session.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                logger.info(f"注册成功: {data.get('message')}")
                return True
            else:
                logger.error(f"注册失败: {response.status_code} - {response.text}")
                return False

        except requests.RequestException as e:
            logger.error(f"注册请求失败: {e}")
            return False

    def claim_tasks(self) -> List[Dict]:
        """领取任务"""
        url = f"{self.server_url}/api/v1/worker/claim"

        payload = {
            "worker_id": self.worker_id,
            "supported_types": self.supported_types,
            "max_tasks": self.max_concurrent - len(self.current_tasks)
        }

        try:
            response = self.session.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                tasks = data.get("tasks", [])
                if tasks:
                    logger.info(f"领取到 {len(tasks)} 个任务: {[t['task_id'] for t in tasks]}")
                return tasks
            elif response.status_code == 401:
                logger.warning("认证失败，尝试重新注册")
                self.register()
                return []
            else:
                logger.debug(f"领取任务失败: {response.status_code}")
                return []

        except requests.RequestException as e:
            logger.error(f"领取任务请求失败: {e}")
            return []

    def report_progress(
        self,
        task_id: int,
        status: str,
        progress: int = 0,
        message: str = "",
        success_items: int = 0,
        failed_items: int = 0,
        total_items: int = 0,
        error_message: str = None,
        result_data: Dict = None
    ) -> bool:
        """汇报任务进度"""
        url = f"{self.server_url}/api/v1/worker/report"

        payload = {
            "task_id": task_id,
            "worker_id": self.worker_id,
            "status": status,
            "progress": progress,
            "message": message,
            "success_items": success_items,
            "failed_items": failed_items,
            "total_items": total_items,
            "error_message": error_message,
            "result_data": result_data
        }

        try:
            response = self.session.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                logger.debug(f"任务 {task_id} 进度已汇报: {status} ({progress}%)")
                return True
            else:
                logger.error(f"汇报失败: {response.status_code} - {response.text}")
                return False

        except requests.RequestException as e:
            logger.error(f"汇报请求失败: {e}")
            return False

    def heartbeat(self) -> Dict:
        """发送心跳"""
        url = f"{self.server_url}/api/v1/worker/heartbeat"

        payload = {
            "worker_id": self.worker_id,
            "current_tasks": self.current_tasks
        }

        try:
            response = self.session.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                commands = data.get("commands", [])
                if commands:
                    self._handle_commands(commands)
                return data
            else:
                logger.warning(f"心跳失败: {response.status_code}")
                return {}

        except requests.RequestException as e:
            logger.error(f"心跳请求失败: {e}")
            return {}

    def _handle_commands(self, commands: List[Dict]):
        """处理服务器下发的命令"""
        for cmd in commands:
            cmd_type = cmd.get("type")
            if cmd_type == "cancel_task":
                task_id = cmd.get("task_id")
                logger.info(f"收到取消任务命令: {task_id}")
                # TODO: 实现任务取消逻辑

    def execute_task(self, task_info: Dict) -> bool:
        """
        执行任务

        这是一个模板方法，需要根据实际爬虫逻辑实现

        Args:
            task_info: 任务信息

        Returns:
            是否成功
        """
        task_id = task_info["task_id"]
        task_type = task_info["task_type"]
        config = task_info.get("config", {})

        logger.info(f"开始执行任务 {task_id}: type={task_type}")

        try:
            # 汇报开始
            self.report_progress(task_id, "running", 10, "任务开始执行")

            # TODO: 根据 task_type 调用对应的爬虫逻辑
            # 这里是演示逻辑
            if task_type == "taobao":
                result = self._execute_taobao_task(task_id, config)
            elif task_type == "jd":
                result = self._execute_jd_task(task_id, config)
            elif task_type == "forum":
                result = self._execute_forum_task(task_id, config)
            else:
                logger.warning(f"未知任务类型: {task_type}")
                result = self._execute_generic_task(task_id, config)

            # 汇报完成
            if result.get("success"):
                self.report_progress(
                    task_id, "success", 100, "任务执行完成",
                    success_items=result.get("success_items", 0),
                    total_items=result.get("total_items", 0),
                    result_data=result.get("data")
                )
                return True
            else:
                self.report_progress(
                    task_id, "failed", 0, "任务执行失败",
                    error_message=result.get("error", "未知错误"),
                    failed_items=result.get("failed_items", 0)
                )
                return False

        except Exception as e:
            logger.error(f"任务 {task_id} 执行异常: {e}")
            self.report_progress(
                task_id, "failed", 0, f"执行异常: {str(e)}",
                error_message=str(e)
            )
            return False

    def _execute_taobao_task(self, task_id: int, config: Dict) -> Dict:
        """执行淘宝爬虫任务 (示例)"""
        logger.info(f"执行淘宝任务 {task_id}")

        # 模拟执行过程
        self.report_progress(task_id, "running", 30, "正在登录淘宝...")
        time.sleep(1)

        self.report_progress(task_id, "running", 60, "正在采集商品数据...")
        time.sleep(1)

        self.report_progress(task_id, "running", 90, "正在保存数据...")
        time.sleep(0.5)

        return {
            "success": True,
            "success_items": 10,
            "total_items": 10,
            "data": {"products": ["示例商品1", "示例商品2"]}
        }

    def _execute_jd_task(self, task_id: int, config: Dict) -> Dict:
        """执行京东爬虫任务 (示例)"""
        logger.info(f"执行京东任务 {task_id}")

        self.report_progress(task_id, "running", 50, "正在采集京东数据...")
        time.sleep(2)

        return {
            "success": True,
            "success_items": 5,
            "total_items": 5,
            "data": {"products": ["JD商品1"]}
        }

    def _execute_forum_task(self, task_id: int, config: Dict) -> Dict:
        """执行论坛爬虫任务 (示例)"""
        logger.info(f"执行论坛任务 {task_id}")

        self.report_progress(task_id, "running", 50, "正在爬取论坛帖子...")
        time.sleep(1)

        return {
            "success": True,
            "success_items": 20,
            "total_items": 20,
            "data": {"posts": ["帖子1", "帖子2"]}
        }

    def _execute_generic_task(self, task_id: int, config: Dict) -> Dict:
        """执行通用任务 (示例)"""
        logger.info(f"执行通用任务 {task_id}")
        time.sleep(1)
        return {"success": True, "success_items": 1, "total_items": 1}

    def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            self.heartbeat()
            time.sleep(self.heartbeat_interval)

    def _poll_loop(self):
        """任务轮询循环"""
        while self.running:
            # 检查是否还有空闲槽位
            if len(self.current_tasks) < self.max_concurrent:
                tasks = self.claim_tasks()

                for task_info in tasks:
                    task_id = task_info["task_id"]
                    self.current_tasks.append(task_id)

                    # 在线程中执行任务
                    thread = threading.Thread(
                        target=self._task_wrapper,
                        args=(task_info,),
                        daemon=True
                    )
                    thread.start()

            time.sleep(self.poll_interval)

    def _task_wrapper(self, task_info: Dict):
        """任务执行包装器"""
        task_id = task_info["task_id"]
        try:
            self.execute_task(task_info)
        finally:
            # 任务完成，从当前任务列表移除
            if task_id in self.current_tasks:
                self.current_tasks.remove(task_id)

    def start(self):
        """启动 Worker"""
        logger.info("正在启动 Worker...")

        # 注册
        if not self.register():
            logger.error("注册失败，无法启动")
            return False

        self.running = True

        # 启动心跳线程
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name="heartbeat"
        )
        self._heartbeat_thread.start()

        # 启动轮询线程
        self._poll_thread = threading.Thread(
            target=self._poll_loop,
            daemon=True,
            name="poll"
        )
        self._poll_thread.start()

        logger.info(
            f"Worker 已启动: poll_interval={self.poll_interval}s, "
            f"heartbeat_interval={self.heartbeat_interval}s"
        )

        return True

    def stop(self):
        """停止 Worker"""
        logger.info("正在停止 Worker...")
        self.running = False

        # 等待线程结束
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=5)
        if self._poll_thread:
            self._poll_thread.join(timeout=5)

        logger.info("Worker 已停止")

    def run_forever(self):
        """持续运行直到收到终止信号"""
        if not self.start():
            return

        # 信号处理
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，准备退出...")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        logger.info("Worker 正在运行，按 Ctrl+C 退出")

        # 主线程保持运行
        while self.running:
            time.sleep(1)


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="分布式爬虫 Worker 客户端",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python remote_worker.py --server http://api.example.com:8000
    python remote_worker.py --server http://localhost:8000 --name Worker-1 --types taobao,jd

环境变量:
    WORKER_SERVER_URL  主服务器地址
    WORKER_NAME        Worker 名称
    WORKER_ID          Worker ID
    POLL_INTERVAL      轮询间隔 (秒)
    HEARTBEAT_INTERVAL 心跳间隔 (秒)
        """
    )

    parser.add_argument(
        "--server", "-s",
        default=os.getenv("WORKER_SERVER_URL", "http://localhost:8000"),
        help="主服务器地址"
    )
    parser.add_argument(
        "--name", "-n",
        default=os.getenv("WORKER_NAME"),
        help="Worker 名称"
    )
    parser.add_argument(
        "--id",
        default=os.getenv("WORKER_ID"),
        help="Worker ID"
    )
    parser.add_argument(
        "--types", "-t",
        default="taobao,jd,forum",
        help="支持的任务类型 (逗号分隔)"
    )
    parser.add_argument(
        "--concurrent", "-c",
        type=int,
        default=1,
        help="最大并发任务数"
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=int(os.getenv("POLL_INTERVAL", "5")),
        help="轮询间隔 (秒)"
    )
    parser.add_argument(
        "--heartbeat-interval",
        type=int,
        default=int(os.getenv("HEARTBEAT_INTERVAL", "30")),
        help="心跳间隔 (秒)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 解析任务类型
    supported_types = [t.strip() for t in args.types.split(",")]

    # 创建并运行 Worker
    worker = RemoteWorker(
        server_url=args.server,
        worker_id=args.id,
        worker_name=args.name,
        supported_types=supported_types,
        max_concurrent=args.concurrent,
        poll_interval=args.poll_interval,
        heartbeat_interval=args.heartbeat_interval
    )

    worker.run_forever()


if __name__ == "__main__":
    main()
