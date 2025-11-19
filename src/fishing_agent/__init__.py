#!/usr/bin/env python3
"""
Agent Module - Simplified fishing assistant

Main exports:
- FishingAgent: Core agent class
- create_fishing_agent: Factory function
- create_optimized_fishing_agent: Alias for backward compatibility
"""

from .core import FishingAgent
from .model_factory import ModelFactory
from .prompts import get_system_prompt, create_fishing_prompt
from .callbacks import FishingAgentCallback

# Backward compatibility alias
OptimizedFishingAgent = FishingAgent

# Export core components
__all__ = [
    "FishingAgent",
    "OptimizedFishingAgent",
    "create_fishing_agent",
    "create_optimized_fishing_agent",
    "ModelFactory",
    "FishingAgentCallback",
    "get_system_prompt",
    "create_fishing_prompt"
]


def create_fishing_agent(**kwargs) -> FishingAgent:
    """
    Create a fishing agent instance

    Args:
        model_provider: LLM provider ("zhipu", "qwen", "doubao", "openai")
        timeout: Request timeout in seconds (default: 60)
        enable_logging: Enable logging output (default: True)
        verbose_callbacks: Enable verbose callback logging (default: False)

    Returns:
        FishingAgent instance

    Example:
        >>> agent = create_fishing_agent(model_provider="zhipu")
        >>> response = agent.run("明天杭州钓鱼怎么样？")
    """
    return FishingAgent(**kwargs)


def create_optimized_fishing_agent(**kwargs) -> FishingAgent:
    """
    Create optimized fishing agent (backward compatibility alias)

    This is an alias for create_fishing_agent() to maintain
    backward compatibility with existing code.

    Args:
        **kwargs: Same as create_fishing_agent()

    Returns:
        FishingAgent instance
    """
    return create_fishing_agent(**kwargs)
