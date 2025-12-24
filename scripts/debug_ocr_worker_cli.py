#!/usr/bin/env python3
"""
OCR Worker 调试脚本

用法:
    # 测试连接
    python scripts/debug_ocr_worker_cli.py --test-connection

    # 注册 Worker
    python scripts/debug_ocr_worker_cli.py --register

    # 领取任务
    python scripts/debug_ocr_worker_cli.py --claim

    # 查看统计
    python scripts/debug_ocr_worker_cli.py --stats

    # 重试任务
    python scripts/debug_ocr_worker_cli.py --retry <pending_id>

    # 完整测试流程
    python scripts/debug_ocr_worker_cli.py --full-test
"""

import os
import sys
import argparse
import requests
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("OCR_WORKER_SERVER_URL", "http://localhost:8000")
ADMIN_API = "http://localhost:8000/api/v1"


def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)


def test_connection():
    """测试 API 连接"""
    print_section("测试 API 连接")

    try:
        # 健康检查
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        print(f"Health Check: {resp.status_code} - {resp.json()}")

        # OCR 端点检查
        resp = requests.get(f"{API_BASE}/api/v1/ocr-worker/stats", timeout=5)
        print(f"OCR Stats: {resp.status_code}")
        if resp.status_code == 200:
            stats = resp.json()
            print(f"  总任务: {stats.get('total', 0)}")
            print(f"  待处理: {stats.get('pending', 0)}")
            print(f"  处理中: {stats.get('processing', 0)}")
            print(f"  已完成: {stats.get('completed', 0)}")
            print(f"  失败: {stats.get('failed', 0)}")

    except Exception as e:
        print(f"连接失败: {e}")


def register_worker(worker_id: str = "debug-worker", provider: str = "siliconflow"):
    """注册 Worker"""
    print_section(f"注册 Worker: {worker_id}")

    url = f"{API_BASE}/api/v1/ocr-worker/register"
    payload = {
        "worker_id": worker_id,
        "worker_name": f"Debug {provider} Worker",
        "ocr_provider": provider,
        "max_tasks": 3,
    }

    resp = requests.post(url, json=payload)
    print(f"Status: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

    if resp.status_code == 200:
        token = resp.json().get("token")
        print(f"\n保存 Token: {token[:30]}...")
        return token
    return None


def claim_tasks(worker_id: str, token: str, max_tasks: int = 1):
    """领取任务"""
    print_section(f"领取任务 (max={max_tasks})")

    url = f"{API_BASE}/api/v1/ocr-worker/claim"
    headers = {"X-Worker-Token": token}
    payload = {"max_tasks": max_tasks}

    resp = requests.post(url, json=payload, headers=headers)
    print(f"Status: {resp.status_code}")
    result = resp.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))

    tasks = result.get("tasks", [])
    if tasks:
        print(f"\n成功领取 {len(tasks)} 个任务:")
        for task in tasks:
            print(f"  - ID: {task['pending_id']}, 图片数: {len(task['images'])}")
    else:
        print("暂无可领取的任务")

    return tasks


def get_task_list(status: str = None, limit: int = 10):
    """获取任务列表"""
    print_section(f"任务列表 (status={status or '全部'}, limit={limit})")

    url = f"{API_BASE}/api/v1/ocr-worker/tasks"
    params = {"page": 1, "page_size": limit}
    if status:
        params["ocr_status"] = status

    resp = requests.get(url, params=params)
    print(f"Status: {resp.status_code}")

    if resp.status_code == 200:
        result = resp.json()
        tasks = result.get("tasks", [])
        print(f"\n共 {result.get('total', 0)} 条任务，显示前 {len(tasks)} 条:\n")

        for t in tasks:
            status_icon = {
                "pending": "⏳",
                "processing": "⚙️",
                "completed": "✅",
                "failed": "❌",
                "skipped": "⏭️",
            }.get(t["ocr_status"], "❓")

            print(f"{status_icon} [{t['pending_id']}] {t['ocr_status']} - {t['brand_name'] or '-'} / {t['product_name'] or '-'}")
            if t.get("ocr_error_message"):
                print(f"   错误: {t['ocr_error_message']}")


def retry_task(pending_id: int, token: str = None):
    """重试任务（需要管理员权限）"""
    print_section(f"重试任务 {pending_id}")

    # 使用 admin token
    admin_token = token or os.getenv("DEBUG_ADMIN_TOKEN", "")
    if not admin_token:
        # 先登录获取 token
        print("需要管理员权限，尝试登录...")
        login_url = f"{ADMIN_API}/auth/login"
        resp = requests.post(login_url, json={"username": "admin", "password": "admin"})
        if resp.status_code == 200:
            admin_token = resp.json().get("access_token")
        else:
            print("登录失败，请手动提供 token")
            return

    url = f"{ADMIN_API}/ocr-worker/admin/tasks/{pending_id}/retry"
    headers = {"Authorization": f"Bearer {admin_token}"}

    resp = requests.post(url, headers=headers)
    print(f"Status: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))


def run_full_test():
    """完整测试流程"""
    print_section("完整测试流程")

    # 1. 测试连接
    test_connection()

    # 2. 注册 Worker
    worker_id = "debug-test-worker"
    token = register_worker(worker_id, "siliconflow")
    if not token:
        print("注册失败，终止测试")
        return

    # 3. 查看任务列表
    get_task_list("pending", 5)

    # 4. 尝试领取任务
    tasks = claim_tasks(worker_id, token, 1)

    if tasks:
        print("\n注意: 任务已领取，需要手动处理或等待超时")
        print("可以使用 --retry <id> 重新将任务设为 pending")

    print_section("测试完成")


def main():
    parser = argparse.ArgumentParser(
        description="OCR Worker 调试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--test-connection", action="store_true", help="测试 API 连接")
    parser.add_argument("--register", action="store_true", help="注册 Worker")
    parser.add_argument("--claim", action="store_true", help="领取任务")
    parser.add_argument("--stats", action="store_true", help="查看任务统计")
    parser.add_argument("--list", action="store_true", help="查看任务列表")
    parser.add_argument("--status", help="按状态筛选任务 (pending/processing/completed/failed/skipped)")
    parser.add_argument("--retry", type=int, metavar="ID", help="重试指定任务")
    parser.add_argument("--full-test", action="store_true", help="运行完整测试流程")
    parser.add_argument("--worker-id", default="debug-worker", help="Worker ID")
    parser.add_argument("--provider", choices=["ollama", "siliconflow"], default="siliconflow", help="OCR 提供商")

    args = parser.parse_args()

    # 默认执行连接测试
    if not any([
        args.test_connection, args.register, args.claim,
        args.stats, args.list, args.retry is not None, args.full_test
    ]):
        args.test_connection = True
        args.stats = True
        args.list = True

    if args.test_connection or args.full_test:
        test_connection()

    if args.stats or args.full_test:
        test_connection()  # stats 在 test_connection 中

    if args.list or args.status or args.full_test:
        get_task_list(args.status)

    if args.register or args.full_test:
        register_worker(args.worker_id, args.provider)

    if args.claim or args.full_test:
        # 需要先有 token，这里简化处理
        print("请先使用 --register 获取 token")

    if args.retry is not None:
        retry_task(args.retry)

    if args.full_test:
        run_full_test()


if __name__ == "__main__":
    main()
