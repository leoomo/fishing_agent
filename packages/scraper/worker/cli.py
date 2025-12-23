#!/usr/bin/env python3
"""
分布式爬虫 Worker 启动脚本

使用方法:
    python -m packages.scraper.worker --server http://localhost:8000
    python -m packages.scraper.worker --server http://localhost:8000 --name "Worker-1" --types taobao,jd
"""

import argparse
import logging
import os
import sys

from . import TaobaoWorker

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Worker")


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='分布式爬虫 Worker 客户端',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
    python -m packages.scraper.worker --server http://localhost:8000
    python -m packages.scraper.worker --server http://localhost:8000 --name Worker-1 --types taobao,jd

环境变量:
    WORKER_SERVER_URL  主服务器地址
    WORKER_NAME        Worker 名称
    WORKER_ID          Worker ID
    POLL_INTERVAL      轮询间隔 (秒)
    HEARTBEAT_INTERVAL 心跳间隔 (秒)
        '''
    )

    parser.add_argument(
        '--server', '-s',
        default=os.getenv('WORKER_SERVER_URL', 'http://localhost:8000'),
        help='主服务器地址'
    )
    parser.add_argument(
        '--name', '-n',
        default=os.getenv('WORKER_NAME'),
        help='Worker 名称'
    )
    parser.add_argument(
        '--id',
        default=os.getenv('WORKER_ID'),
        help='Worker ID'
    )
    parser.add_argument(
        '--types', '-t',
        default='taobao,jd,forum',
        help='支持的任务类型 (逗号分隔)'
    )
    parser.add_argument(
        '--concurrent', '-c',
        type=int,
        default=1,
        help='最大并发任务数'
    )
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=int(os.getenv('POLL_INTERVAL', '5')),
        help='轮询间隔 (秒)'
    )
    parser.add_argument(
        '--heartbeat-interval',
        type=int,
        default=int(os.getenv('HEARTBEAT_INTERVAL', '30')),
        help='心跳间隔 (秒)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 解析任务类型
    supported_types = [t.strip() for t in args.types.split(',')]

    # 创建并运行 Worker
    worker = TaobaoWorker(
        server_url=args.server,
        worker_id=args.id,
        worker_name=args.name,
        supported_types=supported_types,
        max_concurrent=args.concurrent,
        poll_interval=args.poll_interval,
        heartbeat_interval=args.heartbeat_interval
    )

    worker.run_forever()


if __name__ == '__main__':
    main()
