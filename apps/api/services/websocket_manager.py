"""
WebSocket 连接管理器

用于爬虫任务进度的实时推送
"""

import asyncio
import logging
from typing import Dict, Set, Optional
from datetime import datetime
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    WebSocket 连接管理器

    管理爬虫任务的实时进度推送连接
    """

    def __init__(self):
        # task_id -> set of websockets
        self.connections: Dict[int, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, task_id: int):
        """
        注册新的 WebSocket 连接

        Args:
            websocket: WebSocket 连接
            task_id: 任务ID
        """
        await websocket.accept()

        async with self._lock:
            if task_id not in self.connections:
                self.connections[task_id] = set()
            self.connections[task_id].add(websocket)

        logger.info(f"WebSocket 连接已建立: task_id={task_id}")

    async def disconnect(self, websocket: WebSocket, task_id: int):
        """
        移除 WebSocket 连接

        Args:
            websocket: WebSocket 连接
            task_id: 任务ID
        """
        async with self._lock:
            if task_id in self.connections:
                self.connections[task_id].discard(websocket)
                if not self.connections[task_id]:
                    del self.connections[task_id]

        logger.info(f"WebSocket 连接已断开: task_id={task_id}")

    async def broadcast_progress(
        self,
        task_id: int,
        status: str,
        progress: int,
        message: str,
        items_processed: int = 0,
        items_success: int = 0,
        items_failed: int = 0
    ):
        """
        向所有连接的客户端广播进度更新

        Args:
            task_id: 任务ID
            status: 任务状态
            progress: 进度百分比 (0-100)
            message: 进度消息
            items_processed: 已处理数量
            items_success: 成功数量
            items_failed: 失败数量
        """
        if task_id not in self.connections:
            return

        payload = {
            "type": "progress",
            "task_id": task_id,
            "status": status,
            "progress": progress,
            "message": message,
            "items_processed": items_processed,
            "items_success": items_success,
            "items_failed": items_failed,
            "timestamp": datetime.utcnow().isoformat()
        }

        # 复制集合避免迭代时修改
        websockets = list(self.connections.get(task_id, []))

        for websocket in websockets:
            try:
                await websocket.send_json(payload)
            except Exception as e:
                logger.warning(f"WebSocket 发送失败: {e}")
                await self.disconnect(websocket, task_id)

    async def broadcast_completion(
        self,
        task_id: int,
        status: str,
        message: str,
        result_summary: Optional[Dict] = None
    ):
        """
        广播任务完成通知

        Args:
            task_id: 任务ID
            status: 最终状态 (SUCCESS/FAILED)
            message: 完成消息
            result_summary: 结果摘要
        """
        if task_id not in self.connections:
            return

        payload = {
            "type": "completion",
            "task_id": task_id,
            "status": status,
            "message": message,
            "result_summary": result_summary,
            "timestamp": datetime.utcnow().isoformat()
        }

        websockets = list(self.connections.get(task_id, []))

        for websocket in websockets:
            try:
                await websocket.send_json(payload)
            except Exception as e:
                logger.warning(f"WebSocket 发送失败: {e}")
                await self.disconnect(websocket, task_id)

    def get_connection_count(self, task_id: Optional[int] = None) -> int:
        """
        获取连接数量

        Args:
            task_id: 指定任务ID，为空则返回所有连接数

        Returns:
            连接数量
        """
        if task_id is not None:
            return len(self.connections.get(task_id, set()))

        total = 0
        for connections in self.connections.values():
            total += len(connections)
        return total


# 全局单例
ws_manager = WebSocketManager()


def get_ws_manager() -> WebSocketManager:
    """获取全局 WebSocket 管理器"""
    return ws_manager
