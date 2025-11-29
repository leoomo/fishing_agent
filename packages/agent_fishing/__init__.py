"""
Fishing Agent - 智能钓鱼助手（完全自包含）

公共 API:
- FishingAgent: 钓鱼助手 Agent
- create_agent: 工厂函数
- agent: LangGraph 兼容的 agent 实例
- get_all_tools: 获取所有工具
"""
from .core import FishingAgent, create_agent, ModelFactory
from .tools import get_all_tools

# LangGraph 兼容: 模块级 agent 实例
_default_agent = None


def _get_default_agent():
    global _default_agent
    if _default_agent is None:
        _default_agent = create_agent(model_provider="zhipu", enable_logging=True)
    return _default_agent


# 供 LangGraph 使用的 agent 对象
def get_agent():
    return _get_default_agent().agent


# 导出 agent 属性供 LangGraph 使用
agent = property(lambda self: _get_default_agent().agent)

__all__ = [
    "FishingAgent",
    "create_agent",
    "ModelFactory",
    "get_all_tools",
    "get_agent",
]
