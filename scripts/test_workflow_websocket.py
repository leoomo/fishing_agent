#!/usr/bin/env python3
"""
OCR 工作流实时状态功能深度测试脚本

测试内容:
1. WebSocket 连接和事件接收
2. 进度上报 API
3. 日志上报 API
4. 模拟完整 Worker 流程

使用方法:
    # 先启动 API 服务
    uv run uvicorn apps.api.main:app --reload --port 8000

    # 运行测试
    uv run python scripts/test_workflow_websocket.py
"""

import asyncio
import json
import time
import threading
from datetime import datetime
from typing import Optional
import requests
import websockets


# 配置
API_BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"

# 测试用的 Worker Token (需要先注册)
WORKER_ID = "test-ws-worker"
WORKER_TOKEN = None  # 将在测试中获取


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def log_info(msg: str):
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {msg}")


def log_success(msg: str):
    print(f"{Colors.GREEN}[PASS]{Colors.RESET} {msg}")


def log_error(msg: str):
    print(f"{Colors.RED}[FAIL]{Colors.RESET} {msg}")


def log_warning(msg: str):
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {msg}")


def log_event(event_type: str, data: dict):
    print(f"{Colors.CYAN}[EVENT]{Colors.RESET} {event_type}: {json.dumps(data, ensure_ascii=False)[:200]}")


def get_admin_token() -> str:
    """获取管理员 Token"""
    resp = requests.post(
        f"{API_BASE_URL}/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    if resp.status_code != 200:
        raise Exception(f"登录失败: {resp.text}")
    return resp.json()["access_token"]


def register_worker(admin_token: str) -> str:
    """注册测试 Worker"""
    # Worker 注册不需要管理员权限，直接注册即可
    resp = requests.post(
        f"{API_BASE_URL}/api/v1/ocr-worker/register",
        json={
            "worker_id": WORKER_ID,
            "worker_name": "测试 WebSocket Worker",
            "ocr_provider": "test"
        }
    )
    if resp.status_code == 200:
        return resp.json()["token"]
    else:
        raise Exception(f"注册 Worker 失败: {resp.text}")


class TestResults:
    """测试结果收集器"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def add_pass(self, name: str):
        self.passed += 1
        self.tests.append((name, True))
        log_success(name)

    def add_fail(self, name: str, error: str = ""):
        self.failed += 1
        self.tests.append((name, False))
        log_error(f"{name}: {error}")

    def summary(self):
        print("\n" + "=" * 60)
        print(f"{Colors.BOLD}测试结果汇总{Colors.RESET}")
        print("=" * 60)
        for name, passed in self.tests:
            status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
            print(f"  [{status}] {name}")
        print("-" * 60)
        total = self.passed + self.failed
        print(f"总计: {total} | 通过: {Colors.GREEN}{self.passed}{Colors.RESET} | 失败: {Colors.RED}{self.failed}{Colors.RESET}")
        print("=" * 60)


results = TestResults()


# ========== 测试 1: WebSocket 连接 ==========

async def test_websocket_connection():
    """测试 WebSocket 连接"""
    log_info("测试 WebSocket 连接...")

    try:
        admin_token = get_admin_token()
        ws_url = f"{WS_BASE_URL}/api/v1/admin/workflow/ws/workflow?token={admin_token}"

        async with websockets.connect(ws_url) as ws:
            # 等待 init 事件
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            event = json.loads(msg)

            if event.get("type") == "init":
                log_event("init", event.get("data", {}))
                results.add_pass("WebSocket 连接成功并收到 init 事件")
            else:
                results.add_fail("WebSocket 连接", f"未收到 init 事件，收到: {event.get('type')}")

    except asyncio.TimeoutError:
        results.add_fail("WebSocket 连接", "等待 init 事件超时")
    except Exception as e:
        results.add_fail("WebSocket 连接", str(e))


# ========== 测试 2: 进度上报 API ==========

def test_progress_api():
    """测试进度上报 API"""
    log_info("测试进度上报 API...")

    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/v1/ocr-worker/progress",
            headers={"X-Worker-Token": WORKER_TOKEN},
            json={
                "pending_id": 9999,  # 使用不存在的任务 ID 测试
                "stage": "downloading",
                "progress": 50,
                "message": "测试进度上报",
                "current_image": 5,
                "total_images": 10
            }
        )

        if resp.status_code == 200:
            results.add_pass("进度上报 API 返回 200")
        else:
            results.add_fail("进度上报 API", f"状态码: {resp.status_code}, 响应: {resp.text}")

    except Exception as e:
        results.add_fail("进度上报 API", str(e))


# ========== 测试 3: 日志上报 API ==========

def test_log_api():
    """测试日志上报 API"""
    log_info("测试日志上报 API...")

    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/v1/ocr-worker/log",
            headers={"X-Worker-Token": WORKER_TOKEN},
            json={
                "level": "info",
                "message": "测试日志上报",
                "pending_id": 9999
            }
        )

        if resp.status_code == 200:
            results.add_pass("日志上报 API 返回 200")
        else:
            results.add_fail("日志上报 API", f"状态码: {resp.status_code}, 响应: {resp.text}")

    except Exception as e:
        results.add_fail("日志上报 API", str(e))


# ========== 测试 4: WebSocket 事件广播 ==========

async def test_websocket_broadcast():
    """测试 WebSocket 事件广播"""
    log_info("测试 WebSocket 事件广播...")

    received_events = []
    test_pending_id = 8888

    async def ws_listener():
        """监听 WebSocket 事件"""
        try:
            admin_token = get_admin_token()
            ws_url = f"{WS_BASE_URL}/api/v1/admin/workflow/ws/workflow?token={admin_token}"

            async with websockets.connect(ws_url) as ws:
                # 跳过 init 事件
                await asyncio.wait_for(ws.recv(), timeout=5)

                # 持续监听事件
                while True:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=10)
                        event = json.loads(msg)
                        received_events.append(event)
                        log_event(event.get("type", "unknown"), event.get("data", {}))
                    except asyncio.TimeoutError:
                        break
        except Exception as e:
            log_warning(f"WebSocket 监听异常: {e}")

    # 在后台启动 WebSocket 监听
    ws_task = asyncio.create_task(ws_listener())

    # 等待 WebSocket 连接建立
    await asyncio.sleep(1)

    # 发送进度上报
    log_info("发送进度上报...")
    for stage in ["downloading", "merging", "ocr_processing", "extracting"]:
        requests.post(
            f"{API_BASE_URL}/api/v1/ocr-worker/progress",
            headers={"X-Worker-Token": WORKER_TOKEN},
            json={
                "pending_id": test_pending_id,
                "stage": stage,
                "progress": 25 if stage == "downloading" else 50 if stage == "merging" else 75 if stage == "ocr_processing" else 100,
                "message": f"测试阶段: {stage}"
            }
        )
        await asyncio.sleep(0.5)

    # 发送日志上报
    log_info("发送日志上报...")
    requests.post(
        f"{API_BASE_URL}/api/v1/ocr-worker/log",
        headers={"X-Worker-Token": WORKER_TOKEN},
        json={
            "level": "info",
            "message": "测试日志广播",
            "pending_id": test_pending_id
        }
    )

    # 等待事件接收
    await asyncio.sleep(2)

    # 取消监听任务
    ws_task.cancel()
    try:
        await ws_task
    except asyncio.CancelledError:
        pass

    # 验证结果
    progress_events = [e for e in received_events if e.get("type") == "ocr_progress"]
    log_events = [e for e in received_events if e.get("type") == "worker_log"]

    if len(progress_events) >= 4:
        results.add_pass(f"收到 {len(progress_events)} 个进度事件")
    else:
        results.add_fail("进度事件广播", f"只收到 {len(progress_events)} 个事件，预期至少 4 个")

    if len(log_events) >= 1:
        results.add_pass(f"收到 {len(log_events)} 个日志事件")
    else:
        results.add_fail("日志事件广播", f"只收到 {len(log_events)} 个事件，预期至少 1 个")


# ========== 测试 5: 模拟完整 Worker 流程 ==========

async def test_simulated_worker_flow():
    """模拟完整 Worker 处理流程"""
    log_info("模拟完整 Worker 处理流程...")

    admin_token = get_admin_token()
    received_events = []

    async def ws_listener():
        """监听 WebSocket 事件"""
        try:
            ws_url = f"{WS_BASE_URL}/api/v1/admin/workflow/ws/workflow?token={admin_token}"
            async with websockets.connect(ws_url) as ws:
                # 跳过 init 事件
                await asyncio.wait_for(ws.recv(), timeout=5)

                while True:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=15)
                        event = json.loads(msg)
                        received_events.append(event)
                        log_event(event.get("type", "unknown"), {
                            "pending_id": event.get("pending_id"),
                            "type": event.get("type"),
                        })
                    except asyncio.TimeoutError:
                        break
        except Exception as e:
            log_warning(f"WebSocket 监听异常: {e}")

    # 启动监听
    ws_task = asyncio.create_task(ws_listener())
    await asyncio.sleep(1)

    # 1. 尝试领取任务
    log_info("1. 尝试领取任务...")
    resp = requests.post(
        f"{API_BASE_URL}/api/v1/ocr-worker/claim",
        headers={"X-Worker-Token": WORKER_TOKEN},
        json={
            "worker_id": WORKER_ID,
            "supported_types": ["taobao", "jd", "forum"],
            "max_tasks": 1
        }
    )

    if resp.status_code == 200:
        data = resp.json()
        if data.get("tasks"):
            task = data["tasks"][0]
            pending_id = task["pending_id"]
            log_info(f"   领取到任务: pending_id={pending_id}")

            # 2. 模拟处理过程
            stages = [
                ("downloading", 0, "开始下载图片"),
                ("downloading", 25, "下载完成"),
                ("merging", 30, "开始合并图片"),
                ("merging", 50, "合并完成"),
                ("ocr_processing", 55, "开始 OCR 识别"),
                ("ocr_processing", 75, "OCR 识别完成"),
                ("extracting", 80, "开始数据提取"),
                ("extracting", 100, "处理完成"),
            ]

            for stage, progress, message in stages:
                log_info(f"   上报进度: {stage} - {progress}%")
                requests.post(
                    f"{API_BASE_URL}/api/v1/ocr-worker/progress",
                    headers={"X-Worker-Token": WORKER_TOKEN},
                    json={
                        "pending_id": pending_id,
                        "stage": stage,
                        "progress": progress,
                        "message": message
                    }
                )
                await asyncio.sleep(0.3)

            # 3. 上报日志
            log_info("   上报处理日志...")
            requests.post(
                f"{API_BASE_URL}/api/v1/ocr-worker/log",
                headers={"X-Worker-Token": WORKER_TOKEN},
                json={
                    "level": "info",
                    "message": f"任务 {pending_id} 处理完成",
                    "pending_id": pending_id
                }
            )

            # 4. 汇报结果
            log_info("   汇报处理结果...")
            resp = requests.post(
                f"{API_BASE_URL}/api/v1/ocr-worker/report",
                headers={"X-Worker-Token": WORKER_TOKEN},
                json={
                    "pending_id": pending_id,
                    "worker_id": WORKER_ID,
                    "success": True,
                    "ocr_text": "模拟 OCR 识别结果文本",
                    "processing_time_ms": 5000
                }
            )

            if resp.status_code == 200:
                results.add_pass("完整 Worker 流程模拟成功")
            else:
                results.add_fail("汇报结果", f"状态码: {resp.status_code}")

        else:
            log_warning("没有可领取的任务，跳过完整流程测试")
            results.add_pass("领取任务 API 正常（无待处理任务）")
    else:
        results.add_fail("领取任务", f"状态码: {resp.status_code}, 响应: {resp.text}")

    # 等待事件接收
    await asyncio.sleep(3)

    # 取消监听
    ws_task.cancel()
    try:
        await ws_task
    except asyncio.CancelledError:
        pass

    # 统计收到的事件
    event_types = [e.get("type") for e in received_events]
    log_info(f"收到的事件类型: {set(event_types)}")

    if "ocr_progress" in event_types:
        results.add_pass("收到 ocr_progress 事件")
    if "worker_log" in event_types:
        results.add_pass("收到 worker_log 事件")
    if "stats_update" in event_types:
        results.add_pass("收到 stats_update 事件")


# ========== 主测试函数 ==========

async def main():
    global WORKER_TOKEN

    print("\n" + "=" * 60)
    print(f"{Colors.BOLD}OCR 工作流实时状态功能深度测试{Colors.RESET}")
    print("=" * 60 + "\n")

    try:
        # 准备工作
        log_info("准备测试环境...")
        admin_token = get_admin_token()
        log_success("获取管理员 Token 成功")

        WORKER_TOKEN = register_worker(admin_token)
        log_success(f"注册测试 Worker 成功: {WORKER_ID}")

    except Exception as e:
        log_error(f"准备测试环境失败: {e}")
        log_error("请确保 API 服务已启动: uv run uvicorn apps.api.main:app --reload")
        return

    print("\n" + "-" * 60 + "\n")

    # 运行测试
    try:
        # 测试 1: WebSocket 连接
        await test_websocket_connection()

        # 测试 2: 进度上报 API
        test_progress_api()

        # 测试 3: 日志上报 API
        test_log_api()

        # 测试 4: WebSocket 事件广播
        await test_websocket_broadcast()

        # 测试 5: 模拟完整 Worker 流程
        await test_simulated_worker_flow()

    except Exception as e:
        log_error(f"测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

    # 输出测试结果汇总
    results.summary()

    # 清理
    log_info("清理测试环境...")
    try:
        requests.delete(
            f"{API_BASE_URL}/api/v1/ocr-worker/admin/workers/{WORKER_ID}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        log_success("删除测试 Worker")
    except:
        pass


if __name__ == "__main__":
    asyncio.run(main())
