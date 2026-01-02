#!/usr/bin/env python3
"""
OCR Worker Debug 脚本 - 用于 IDE 调试运行

使用方法:
    在 IDE 中直接运行此文件，或使用:
    PYTHONPATH=. uv run python scripts/debug_ocr_worker_simple.py
"""

import sys
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加项目根目录到 path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from packages.scraper.worker.ocr_worker import OCRWorker

# ========== 调试配置 ==========
# 可以根据需要修改这些参数

SERVER_URL = "http://localhost:8000"
WORKER_ID = "debug-ocr-worker"
OCR_PROVIDER = "ollama"  # ollama, siliconflow, baidu
POLL_INTERVAL = 5  # 轮询间隔 (秒)
HEARTBEAT_EVERY = 6  # 每 N 次轮询发送心跳 (6*5=30秒)
CACHE_DIR = "/tmp/ocr_worker_cache"


def main():
    """调试入口"""
    print("=" * 50)
    print("  OCR Worker Debug 模式 (单线程同步)")
    print("=" * 50)
    print(f"  服务器: {SERVER_URL}")
    print(f"  Worker ID: {WORKER_ID}")
    print(f"  OCR 提供商: {OCR_PROVIDER}")
    print(f"  轮询间隔: {POLL_INTERVAL}s")
    print(f"  心跳: 每 {HEARTBEAT_EVERY} 次轮询")
    print("=" * 50)
    print()

    # 创建 Worker 实例
    worker = OCRWorker(
        server_url=SERVER_URL,
        worker_id=WORKER_ID,
        ocr_provider=OCR_PROVIDER,
        poll_interval=POLL_INTERVAL,
        heartbeat_every=HEARTBEAT_EVERY,
        cache_dir=CACHE_DIR,
    )

    # 启动 Worker
    worker.run_forever()


if __name__ == "__main__":
    main()
