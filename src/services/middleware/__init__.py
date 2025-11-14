"""
LangChain 中间件模块

提供自定义中间件实现，用于扩展和增强 LangChain 智能体功能。
"""

from .logging_middleware import AgentLoggingMiddleware
from .config import MiddlewareConfig

__all__ = [
    'AgentLoggingMiddleware',
    'MiddlewareConfig'
]

__version__ = "1.0.0"