#!/usr/bin/env python3
"""
OCR Worker CLI - 命令行启动 OCR Worker

用法:
    python -m packages.scraper.worker.ocr_cli --server http://localhost:8000
    python -m packages.scraper.worker.ocr_cli --provider siliconflow -v
    python -m packages.scraper.worker.ocr_cli --log-file /var/log/ocr_worker.log
"""

import argparse
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from typing import Optional

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def setup_logging(verbose: bool = False, log_file: Optional[str] = None):
    """
    配置日志

    Args:
        verbose: 是否启用详细日志 (DEBUG 级别)
        log_file: 可选的日志文件路径
    """
    level = logging.DEBUG if verbose else logging.INFO

    # 更详细的格式（包含毫秒）
    fmt = "%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    # 创建处理器列表
    handlers = [logging.StreamHandler()]

    # 可选文件日志（带轮转）
    if log_file:
        try:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setFormatter(logging.Formatter(fmt, datefmt))
            handlers.append(file_handler)
        except Exception as e:
            print(f"警告: 无法创建日志文件 {log_file}: {e}", file=sys.stderr)

    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt=datefmt,
        handlers=handlers,
    )

    # 降低第三方库日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


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
        help="详细日志输出 (DEBUG 级别)",
    )

    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="日志文件路径 (可选，支持自动轮转)",
    )

    args = parser.parse_args()

    # 配置日志
    setup_logging(args.verbose, args.log_file)

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
