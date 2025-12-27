"""
数据工作流 WebSocket 管理器

支持：
1. 全局广播（stats, workers 更新推送给所有连接）
2. 任务订阅（按 pending_id 订阅单任务进度）
3. 日志流（推送 Worker 处理日志）
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Optional
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WorkflowWSManager:
    """工作流 WebSocket 连接管理器"""

    def __init__(self):
        # 全局状态订阅者（接收 stats, workers, tasks 更新）
        self.global_subscribers: set[WebSocket] = set()
        # 单任务进度订阅者（按 pending_id）
        self.task_subscribers: dict[int, set[WebSocket]] = {}
        # 日志流订阅者
        self.log_subscribers: set[WebSocket] = set()
        # 异步锁
        self._lock = asyncio.Lock()

    async def connect_global(self, websocket: WebSocket) -> None:
        """添加全局状态订阅"""
        await websocket.accept()
        async with self._lock:
            self.global_subscribers.add(websocket)
        logger.info(f"全局订阅者连接，当前数量: {len(self.global_subscribers)}")

    async def disconnect_global(self, websocket: WebSocket) -> None:
        """移除全局状态订阅"""
        async with self._lock:
            self.global_subscribers.discard(websocket)
        logger.info(f"全局订阅者断开，当前数量: {len(self.global_subscribers)}")

    async def subscribe_task(self, websocket: WebSocket, pending_id: int) -> None:
        """订阅单任务进度"""
        async with self._lock:
            if pending_id not in self.task_subscribers:
                self.task_subscribers[pending_id] = set()
            self.task_subscribers[pending_id].add(websocket)
        logger.debug(f"任务 {pending_id} 新增订阅者")

    async def unsubscribe_task(self, websocket: WebSocket, pending_id: int) -> None:
        """取消订阅单任务进度"""
        async with self._lock:
            if pending_id in self.task_subscribers:
                self.task_subscribers[pending_id].discard(websocket)
                if not self.task_subscribers[pending_id]:
                    del self.task_subscribers[pending_id]

    async def connect_logs(self, websocket: WebSocket) -> None:
        """订阅日志流"""
        await websocket.accept()
        async with self._lock:
            self.log_subscribers.add(websocket)
        logger.info(f"日志订阅者连接，当前数量: {len(self.log_subscribers)}")

    async def disconnect_logs(self, websocket: WebSocket) -> None:
        """取消日志流订阅"""
        async with self._lock:
            self.log_subscribers.discard(websocket)
        logger.info(f"日志订阅者断开，当前数量: {len(self.log_subscribers)}")

    async def _send_json(self, websocket: WebSocket, data: dict[str, Any]) -> bool:
        """安全发送 JSON 数据"""
        try:
            await websocket.send_json(data)
            return True
        except Exception as e:
            logger.warning(f"WebSocket 发送失败: {e}")
            return False

    async def _broadcast_to_set(
        self, subscribers: set[WebSocket], data: dict[str, Any]
    ) -> None:
        """向订阅者集合广播消息"""
        if not subscribers:
            return

        disconnected = set()
        for ws in subscribers.copy():
            success = await self._send_json(ws, data)
            if not success:
                disconnected.add(ws)

        # 清理断开的连接
        if disconnected:
            async with self._lock:
                subscribers -= disconnected

    async def broadcast_stats(self, stats: dict[str, Any]) -> None:
        """广播统计数据更新"""
        event = {
            "type": "stats_update",
            "data": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self._broadcast_to_set(self.global_subscribers, event)
        logger.debug(f"广播统计更新到 {len(self.global_subscribers)} 个订阅者")

    async def broadcast_workers(self, workers: list[dict[str, Any]]) -> None:
        """广播 Worker 状态更新"""
        event = {
            "type": "worker_update",
            "data": workers,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self._broadcast_to_set(self.global_subscribers, event)
        logger.debug(f"广播 Worker 更新到 {len(self.global_subscribers)} 个订阅者")

    async def broadcast_task_event(
        self,
        pending_id: int,
        event_type: str,
        data: dict[str, Any],
    ) -> None:
        """
        广播任务事件

        event_type: task_claimed, ocr_started, ocr_progress, ocr_completed, ocr_failed
        """
        event = {
            "type": event_type,
            "pending_id": pending_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # 广播到全局订阅者
        await self._broadcast_to_set(self.global_subscribers, event)

        # 广播到任务专属订阅者
        if pending_id in self.task_subscribers:
            await self._broadcast_to_set(self.task_subscribers[pending_id], event)

        logger.debug(f"广播任务事件 {event_type} (pending_id={pending_id})")

    async def broadcast_log(
        self,
        worker_id: str,
        level: str,
        message: str,
        pending_id: Optional[int] = None,
    ) -> None:
        """广播 Worker 日志"""
        event = {
            "type": "worker_log",
            "data": {
                "worker_id": worker_id,
                "level": level,
                "message": message,
                "pending_id": pending_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
        await self._broadcast_to_set(self.log_subscribers, event)
        # 同时发送给全局订阅者
        await self._broadcast_to_set(self.global_subscribers, event)

    async def send_init_state(
        self,
        websocket: WebSocket,
        stats: Optional[dict[str, Any]] = None,
        workers: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        """发送初始状态给新连接的客户端"""
        event = {
            "type": "init",
            "data": {
                "stats": stats,
                "workers": workers,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self._send_json(websocket, event)

    def get_connection_count(self) -> dict[str, int]:
        """获取连接统计"""
        return {
            "global": len(self.global_subscribers),
            "logs": len(self.log_subscribers),
            "tasks": sum(len(subs) for subs in self.task_subscribers.values()),
        }


# 全局单例
_workflow_ws_manager: Optional[WorkflowWSManager] = None


def get_workflow_ws_manager() -> WorkflowWSManager:
    """获取工作流 WebSocket 管理器单例"""
    global _workflow_ws_manager
    if _workflow_ws_manager is None:
        _workflow_ws_manager = WorkflowWSManager()
    return _workflow_ws_manager
