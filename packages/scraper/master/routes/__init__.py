"""
Master Service Routes

API路由模块
"""

from .node import router as node_router
from .task import router as task_router
from .image import router as image_router

__all__ = ["node_router", "task_router", "image_router"]
