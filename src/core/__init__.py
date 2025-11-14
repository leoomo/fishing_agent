"""
LangChain Learning - Core Module

核心模块提供了整个系统的基础设施，包括：
- 接口定义
- 工具注册机制  
- 基础类和抽象
- 配置管理
"""

from .interfaces import ITool, IAgent, IService
from .registry import ToolRegistry
from .base_tool import BaseTool
from .base_agent import BaseAgent
from .base_service import BaseService

__version__ = "1.0.0"
__all__ = [
    "ITool",
    "IAgent", 
    "IService",
    "ToolRegistry",
    "BaseTool",
    "BaseAgent",
    "BaseService",
]