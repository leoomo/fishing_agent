#!/usr/bin/env python3
"""
Worker Debug 脚本 - 用于 IDE 调试运行

使用方法:
    在 IDE 中直接运行此文件，或使用:
    uv run python scripts/debug_worker.py
"""

import sys
import os

# 添加项目根目录到 path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from packages.scraper.worker import TaobaoWorker

# ========== 调试配置 ==========
# 可以根据需要修改这些参数

SERVER_URL = "http://localhost:8000"
WORKER_NAME = "Debug-Worker-1"
WORKER_ID = "debug-worker-001"
SUPPORTED_TYPES = ["taobao", "jd", "forum"]
MAX_CONCURRENT = 1
POLL_INTERVAL = 5  # 轮询间隔 (秒)
HEARTBEAT_INTERVAL = 30  # 心跳间隔 (秒)


def main():
    """调试入口"""
    print("=" * 50)
    print("  Worker Debug 模式")
    print("=" * 50)
    print(f"  服务器: {SERVER_URL}")
    print(f"  Worker名称: {WORKER_NAME}")
    print(f"  Worker ID: {WORKER_ID}")
    print(f"  支持类型: {SUPPORTED_TYPES}")
    print(f"  最大并发: {MAX_CONCURRENT}")
    print(f"  轮询间隔: {POLL_INTERVAL}s")
    print(f"  心跳间隔: {HEARTBEAT_INTERVAL}s")
    print("=" * 50)
    print()

    # 创建 Worker 实例
    worker = TaobaoWorker(
        server_url=SERVER_URL,
        worker_id=WORKER_ID,
        worker_name=WORKER_NAME,
        supported_types=SUPPORTED_TYPES,
        max_concurrent=MAX_CONCURRENT,
        poll_interval=POLL_INTERVAL,
        heartbeat_interval=HEARTBEAT_INTERVAL
    )

    # 启动 Worker
    worker.run_forever()


if __name__ == "__main__":
    main()
