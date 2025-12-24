#!/usr/bin/env python3
"""
OCR Worker CLI - 命令行启动 OCR Worker

用法:
    python -m packages.scraper.worker.ocr_cli --server http://localhost:8000
    python -m packages.scraper.worker.ocr_cli --provider siliconflow -v
"""

import argparse
import logging
import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def setup_logging(verbose: bool = False):
    """配置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="OCR Worker - 分布式 OCR 文本提取服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 使用默认配置启动
    python -m packages.scraper.worker.ocr_cli

    # 指定服务器和提供商
    python -m packages.scraper.worker.ocr_cli --server http://api.example.com --provider siliconflow

    # 详细日志模式
    python -m packages.scraper.worker.ocr_cli -v
        """,
    )

    parser.add_argument(
        "--server",
        type=str,
        default=os.getenv("OCR_WORKER_SERVER_URL", "http://localhost:8000"),
        help="API 服务器地址 (默认: http://localhost:8000)",
    )

    parser.add_argument(
        "--worker-id",
        type=str,
        default=None,
        help="Worker ID (默认: 自动生成)",
    )

    parser.add_argument(
        "--provider",
        type=str,
        choices=["ollama", "siliconflow"],
        default=os.getenv("OCR_PROVIDER", "ollama"),
        help="OCR 提供商 (默认: ollama)",
    )

    parser.add_argument(
        "--poll-interval",
        type=int,
        default=int(os.getenv("OCR_WORKER_POLL_INTERVAL", "5")),
        help="轮询间隔秒数 (默认: 5)",
    )

    parser.add_argument(
        "--heartbeat-interval",
        type=int,
        default=int(os.getenv("OCR_WORKER_HEARTBEAT_INTERVAL", "30")),
        help="心跳间隔秒数 (默认: 30)",
    )

    parser.add_argument(
        "--cache-dir",
        type=str,
        default="/tmp/ocr_worker_cache",
        help="图片缓存目录 (默认: /tmp/ocr_worker_cache)",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细日志输出",
    )

    args = parser.parse_args()

    # 配置日志
    setup_logging(args.verbose)

    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("OCR Worker 启动中...")
    logger.info(f"服务器: {args.server}")
    logger.info(f"OCR 提供商: {args.provider}")
    logger.info(f"轮询间隔: {args.poll_interval}s")
    logger.info(f"心跳间隔: {args.heartbeat_interval}s")
    logger.info("=" * 50)

    # 导入并启动 Worker
    from packages.scraper.worker.ocr_worker import OCRWorker

    worker = OCRWorker(
        server_url=args.server,
        worker_id=args.worker_id,
        ocr_provider=args.provider,
        poll_interval=args.poll_interval,
        heartbeat_interval=args.heartbeat_interval,
        cache_dir=args.cache_dir,
    )

    try:
        worker.run_forever()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在退出...")
    finally:
        worker.stop()
        logger.info("OCR Worker 已退出")


if __name__ == "__main__":
    main()
