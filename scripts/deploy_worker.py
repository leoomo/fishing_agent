#!/usr/bin/env python3
"""
Worker节点一键部署脚本

用法:
  # 注册并启动新节点
  python scripts/deploy_worker.py \\
    --master http://master-server:8100 \\
    --name "北京节点" \\
    --location "北京阿里云" \\
    --capabilities taobao,jd \\
    --max-tasks 2

  # 使用已有配置启动
  python scripts/deploy_worker.py --config worker_config.json

  # 仅注册节点（不启动）
  python scripts/deploy_worker.py \\
    --master http://master-server:8100 \\
    --name "上海节点" \\
    --register-only

启动Master服务:
  uv run uvicorn apps.crawler_master.main:app --host 0.0.0.0 --port 8100
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# 确保项目根目录在路径中
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def setup_logging(verbose: bool = False):
    """配置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def register_node(args) -> dict:
    """
    注册新节点

    Args:
        args: 命令行参数

    Returns:
        注册响应数据
    """
    import requests

    url = f'{args.master.rstrip("/")}/api/v1/nodes/register'

    capabilities = ['all']
    if args.capabilities:
        capabilities = [c.strip() for c in args.capabilities.split(',')]

    payload = {
        'node_name': args.name,
        'capabilities': capabilities,
        'max_concurrent_tasks': args.max_tasks,
        'worker_version': '1.0.0',
    }
    if args.location:
        payload['location'] = args.location

    print(f"\n正在注册节点...")
    print(f"  Master: {url}")
    print(f"  Name: {args.name}")
    print(f"  Capabilities: {capabilities}")
    print(f"  Max Tasks: {args.max_tasks}")

    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()

    data = response.json()

    print(f"\n✅ 节点注册成功!")
    print(f"  Node ID: {data['node_id']}")
    print(f"  Token Expires: {data['expires_at']}")
    print(f"\n⚠️  重要: 请妥善保存以下密钥，它只显示一次!")
    print(f"  Node Secret: {data['node_secret']}")

    return data


def save_config(config: dict, path: str):
    """保存配置到文件"""
    with open(path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"\n配置已保存到: {path}")


def load_config(path: str) -> dict:
    """加载配置文件"""
    with open(path) as f:
        return json.load(f)


def start_worker(config: dict):
    """启动Worker进程"""
    from packages.scraper.worker import CrawlerWorker, WorkerConfig

    worker_config = WorkerConfig.from_dict(config)
    worker = CrawlerWorker(worker_config)

    print(f"\n🚀 正在启动Worker...")
    print(f"  Master: {config['master_url']}")
    print(f"  Node ID: {config['node_id']}")
    print(f"  Max Tasks: {config.get('max_concurrent_tasks', 1)}")
    print("\n按 Ctrl+C 停止Worker")
    print("-" * 50)

    try:
        worker.start()
    except KeyboardInterrupt:
        print("\n\n正在停止Worker...")
        worker.stop()
        print("Worker已停止")


def main():
    parser = argparse.ArgumentParser(
        description='分布式爬虫Worker部署脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # 配置文件模式
    parser.add_argument(
        '--config', '-c',
        help='使用已有配置文件启动',
    )

    # 注册模式
    parser.add_argument(
        '--master', '-m',
        help='Master服务器地址 (例: http://localhost:8100)',
    )
    parser.add_argument(
        '--name', '-n',
        help='节点名称',
    )
    parser.add_argument(
        '--location', '-l',
        default='',
        help='节点位置 (例: 北京阿里云)',
    )
    parser.add_argument(
        '--capabilities', '-cap',
        default='all',
        help='能力标签，逗号分隔 (例: taobao,jd)',
    )
    parser.add_argument(
        '--max-tasks', '-t',
        type=int,
        default=1,
        help='最大并发任务数 (默认: 1)',
    )

    # 其他选项
    parser.add_argument(
        '--register-only',
        action='store_true',
        help='仅注册节点，不启动Worker',
    )
    parser.add_argument(
        '--output', '-o',
        default='worker_config.json',
        help='配置文件输出路径 (默认: worker_config.json)',
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细日志',
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    config_file = Path(args.config or args.output)

    # 模式1: 使用已有配置
    if args.config and config_file.exists():
        print(f"使用配置文件: {config_file}")
        config = load_config(str(config_file))

        if not config.get('node_id') or not config.get('node_secret'):
            print("❌ 配置文件缺少 node_id 或 node_secret")
            sys.exit(1)

        start_worker(config)
        return

    # 模式2: 注册新节点
    if args.master and args.name:
        # 注册节点
        try:
            data = register_node(args)
        except Exception as e:
            print(f"\n❌ 注册失败: {e}")
            sys.exit(1)

        # 构建配置
        config = {
            'master_url': args.master.rstrip('/'),
            'node_id': data['node_id'],
            'node_secret': data['node_secret'],
            'node_name': args.name,
            'capabilities': [c.strip() for c in args.capabilities.split(',')],
            'max_concurrent_tasks': args.max_tasks,
            'location': args.location,
            'worker_version': '1.0.0',
        }

        # 保存配置
        save_config(config, str(config_file))

        if args.register_only:
            print("\n节点注册完成（未启动Worker）")
            print(f"启动命令: python scripts/deploy_worker.py --config {config_file}")
            return

        # 启动Worker
        start_worker(config)
        return

    # 参数错误
    if args.config and not config_file.exists():
        print(f"❌ 配置文件不存在: {config_file}")
        sys.exit(1)

    parser.print_help()
    print("\n错误: 请提供 --master 和 --name 注册新节点，或使用 --config 加载已有配置")
    sys.exit(1)


if __name__ == '__main__':
    main()
