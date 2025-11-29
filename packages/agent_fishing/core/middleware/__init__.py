"""
Agent 中间件模块

提供各种 LangChain Agent 中间件功能：
- 动态 Prompt 选择
- 日志记录（未来）
- 缓存（未来）
- 监控（未来）
"""
from .dynamic_prompt import select_prompt_by_query_type

__all__ = [
    "select_prompt_by_query_type",
]
