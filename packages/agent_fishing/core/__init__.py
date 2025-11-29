"""
Agent 核心模块

导出:
- FishingAgent: 钓鱼助手 Agent 类
- create_agent: 工厂函数
- ModelFactory: LLM 模型工厂
- get_system_prompt: 系统提示词
- create_fishing_prompt: 创建钓鱼提示词
- FishingAgentCallback: 回调处理器
- select_prompt_by_query_type: 动态 prompt 中间件
"""
from .agent import FishingAgent
from .model_factory import ModelFactory
from .prompts import get_system_prompt, create_fishing_prompt
from .callbacks import FishingAgentCallback
from .middleware import select_prompt_by_query_type


def create_agent(**kwargs) -> FishingAgent:
    """创建钓鱼助手实例"""
    return FishingAgent(**kwargs)


__all__ = [
    "FishingAgent",
    "create_agent",
    "ModelFactory",
    "get_system_prompt",
    "create_fishing_prompt",
    "FishingAgentCallback",
    "select_prompt_by_query_type",
]
