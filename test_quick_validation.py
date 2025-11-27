#!/usr/bin/env python3
"""快速验证工具选择优化效果"""

import sys
import os
from pathlib import Path

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agent import create_optimized_fishing_agent

def test_core_scenario():
    """测试核心问题场景：钓鱼+天气混合查询"""
    print("🧪 快速验证：工具选择优化")
    print("=" * 60)

    # 创建agent（使用通义千问）
    print("\n📝 创建智能代理（使用通义千问）...")
    agent = create_optimized_fishing_agent(model_provider="qwen", enable_logging=True)

    # 测试用例：核心问题场景
    test_input = "今天杭州余杭区钓鱼天气如何？"
    print(f"\n❓ 测试查询: {test_input}")
    print("-" * 60)

    # 重置callback统计
    agent.callback.reset()

    try:
        print("\n🤔 正在执行查询...")
        response = agent.run(test_input)
        print(f"\n📝 Agent响应:\n{response[:200]}...")  # 显示前200字符

        # 检查工具调用（从callback获取）
        tool_calls = agent.callback.stats.get('tool_calls', {})
        total_tool_calls = sum(tool_calls.values())

        print(f"\n📊 工具调用统计:")
        print(f"  调用的工具: {list(tool_calls.keys())}")
        print(f"  总调用次数: {total_tool_calls}")

        # 判断结果
        print(f"\n✅ 验证结果:")
        if total_tool_calls > 1:
            print(f"  ❌ 失败: 调用了 {total_tool_calls} 个工具（期望1个）")
            print(f"  ⚠️  工具调用详情: {tool_calls}")
            return False
        elif 'query_fishing_recommendation' not in tool_calls:
            print(f"  ❌ 失败: 未调用期望工具 query_fishing_recommendation")
            print(f"  ⚠️  实际调用: {list(tool_calls.keys())}")
            return False
        else:
            print(f"  ✅ 成功: 仅调用了 query_fishing_recommendation")
            print(f"  ✅ 优化生效！")
            return True

    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎯 工具选择优化 - 快速验证")
    print("="*60)

    success = test_core_scenario()

    print("\n" + "="*60)
    if success:
        print("✅ 验证通过！工具选择优化成功")
    else:
        print("❌ 验证失败！需要进一步调整")
    print("="*60 + "\n")

    sys.exit(0 if success else 1)
