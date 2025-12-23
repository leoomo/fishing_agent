#!/usr/bin/env python3
"""工具选择优化验证测试"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from packages.agents.fishing import create_agent as create_optimized_fishing_agent
import logging

logging.basicConfig(level=logging.WARNING)  # 减少日志噪音

# 测试用例
TEST_CASES = [
    {
        "name": "钓鱼+天气混合查询（核心问题场景）",
        "input": "今天杭州余杭区钓鱼天气如何？",
        "expected_tool": "query_fishing_recommendation",
        "max_tools": 1,
        "description": "同时包含'钓鱼'和'天气'关键词，应只调用钓鱼工具"
    },
    {
        "name": "纯天气查询",
        "input": "杭州余杭区明天天气怎么样？",
        "expected_tool": "get_weather",
        "max_tools": 1,
        "description": "只有'天气'关键词，应调用天气工具"
    },
    {
        "name": "纯钓鱼查询",
        "input": "明天杭州钓鱼怎么样？",
        "expected_tool": "query_fishing_recommendation",
        "max_tools": 1,
        "description": "只有'钓鱼'关键词，应调用钓鱼工具"
    },
    {
        "name": "天气在前钓鱼在后",
        "input": "杭州天气适合钓鱼吗？",
        "expected_tool": "query_fishing_recommendation",
        "max_tools": 1,
        "description": "关键词顺序不影响判断"
    },
    {
        "name": "多天气词+钓鱼",
        "input": "杭州今天钓鱼天气如何，气温多少，会下雨吗？",
        "expected_tool": "query_fishing_recommendation",
        "max_tools": 1,
        "description": "多个天气关键词，但包含'钓鱼'，应只调用钓鱼工具"
    },
]

def run_tests():
    """运行测试用例"""
    print("\n" + "=" * 80)
    print("🧪 工具选择优化验证测试")
    print("=" * 80)

    # 创建agent（使用通义千问）
    print("\n📝 创建智能代理（使用通义千问）...")
    agent = create_optimized_fishing_agent(model_provider="qwen", enable_logging=False)

    passed = 0
    failed = 0
    failed_cases = []

    for i, test in enumerate(TEST_CASES, 1):
        print(f"\n{'='*80}")
        print(f"测试 {i}/{len(TEST_CASES)}: {test['name']}")
        print(f"{'='*80}")
        print(f"📝 说明: {test['description']}")
        print(f"❓ 输入: {test['input']}")
        print(f"🎯 期望工具: {test['expected_tool']}")
        print(f"📊 最大工具数: {test['max_tools']}")
        print("-" * 80)

        # 重置callback统计
        agent.callback.reset()

        try:
            print(f"🤔 正在执行查询...")
            response = agent.run(test['input'])

            # 检查工具调用
            tool_calls = agent.callback.stats.get('tool_calls', {})
            total_tool_calls = sum(tool_calls.values())

            print(f"\n📊 实际结果:")
            print(f"   调用的工具: {list(tool_calls.keys())}")
            print(f"   总调用次数: {total_tool_calls}")
            print(f"   响应长度: {len(response)} 字符")

            # 验证
            success = True
            failure_reasons = []

            if total_tool_calls > test['max_tools']:
                success = False
                failure_reasons.append(
                    f"调用了 {total_tool_calls} 个工具（期望最多 {test['max_tools']} 个）"
                )

            if test['expected_tool'] not in tool_calls:
                success = False
                failure_reasons.append(
                    f"未调用期望工具 '{test['expected_tool']}'"
                )

            if success:
                print(f"\n✅ 测试通过")
                passed += 1
            else:
                print(f"\n❌ 测试失败:")
                for reason in failure_reasons:
                    print(f"   - {reason}")
                failed += 1
                failed_cases.append({
                    "name": test['name'],
                    "reasons": failure_reasons,
                    "tool_calls": tool_calls
                })

        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            failed += 1
            failed_cases.append({
                "name": test['name'],
                "reasons": [f"异常: {str(e)}"],
                "tool_calls": {}
            })

    # 总结
    print(f"\n{'='*80}")
    print(f"📊 测试总结")
    print(f"{'='*80}")
    print(f"总测试数: {len(TEST_CASES)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"成功率: {passed/len(TEST_CASES)*100:.1f}%")

    if failed_cases:
        print(f"\n失败用例详情:")
        for case in failed_cases:
            print(f"\n  - {case['name']}")
            for reason in case['reasons']:
                print(f"    {reason}")
            if case['tool_calls']:
                print(f"    实际调用: {case['tool_calls']}")

    print("=" * 80 + "\n")

    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
