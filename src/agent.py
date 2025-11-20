#!/usr/bin/env python3
"""
Fishing Agent - Backward Compatibility Shim

This file maintains backward compatibility with existing code
that imports from src.agent. All functionality has been moved
to the src.agent module for better organization.

For new code, prefer:
    from src.agent import create_fishing_agent, FishingAgent
"""

import logging
from fishing_agent import (
    FishingAgent as OptimizedFishingAgent,
    create_fishing_agent,
    create_optimized_fishing_agent,
    ModelFactory,
    FishingAgentCallback,
    get_system_prompt
)
from middleware import HealthCheck

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = [
    "OptimizedFishingAgent",
    "FishingAgent",
    "create_fishing_agent",
    "create_optimized_fishing_agent",
    "agent",
    "main",
    "demonstrate_agent"
]

# Alias for backward compatibility
FishingAgent = OptimizedFishingAgent


def demonstrate_agent():
    """
    Demonstrate fishing agent functionality
    (Moved from original implementation)
    """
    import os
    from datetime import datetime

    print("🎯 智能钓鱼助手演示")
    print("=" * 60)

    # Check API keys
    required_keys = {
        "DASHSCOPE_API_KEY": "阿里云通义千问",
        "ANTHROPIC_AUTH_TOKEN": "智谱AI GLM",
        "ARK_API_KEY": "豆包大模型"
    }

    available_models = []
    for key, name in required_keys.items():
        if os.getenv(key):
            available_models.append((key, name))

    if not available_models:
        print("❌ 错误: 请配置至少一个API密钥")
        for key, name in required_keys.items():
            print(f"   {key}: {name}")
        return

    # Select model
    if os.getenv("DASHSCOPE_API_KEY"):
        model_provider = "qwen"
        model_name = "通义千问"
    elif os.getenv("ANTHROPIC_AUTH_TOKEN"):
        model_provider = "zhipu"
        model_name = "智谱AI GLM"
    else:
        model_provider = "doubao"
        model_name = "豆包"

    print(f"✅ 使用模型: {model_name}")

    try:
        # Create agent
        fishing_agent = create_optimized_fishing_agent(
            model_provider=model_provider,
            enable_logging=True
        )

        # Health check
        health_checker = HealthCheck(fishing_agent)
        health = health_checker.check()
        print(f"🏥 系统状态: {health['status']}")
        for check, status in health['checks'].items():
            print(f"   {check}: {status}")

        # Test cases
        test_cases = [
            "后天杭州市钓鱼怎么样？",
        ]

        print(f"\n🧪 测试 {len(test_cases)} 个用例:")

        for i, test_input in enumerate(test_cases, 1):
            print(f"\n📝 测试 {i}: {test_input}")
            print("-" * 40)

            try:
                response = fishing_agent.run(test_input)
                print(f"🤖 回复:\n{response}")

            except Exception as e:
                print(f"❌ 失败: {e}")

        # Display statistics
        print(f"\n📊 系统统计:")
        fishing_agent.print_stats()

        stats = fishing_agent.get_stats()
        for key, value in stats.items():
            if key not in ["tool_calls"]:
                print(f"   {key}: {value}")

    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


# Create module-level agent instance for backward compatibility
# This replicates the behavior from the original agent.py
agent = create_optimized_fishing_agent(
    model_provider="zhipu",
    enable_logging=True
).agent


def main():
    """
    Main function - Simplified architecture version
    """
    print("🎯 智能钓鱼助手")
    print("基于 LangChain 1.0+ 和简化架构设计")
    print("🚀 架构优势: 85%+ 代码减少，无过度抽象，直接工具调用")
    print()

    demonstrate_agent()


if __name__ == "__main__":
    main()
