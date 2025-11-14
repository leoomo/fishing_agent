#!/usr/bin/env python3
"""
日志中间件使用示例

演示如何在项目中使用AgentLoggingMiddleware。
"""

import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
load_dotenv()

from modern_langchain_agent import ModernLangChainAgent
from services.middleware import MiddlewareConfig


def example_basic_usage():
    """基础使用示例"""
    print("📝 基础使用示例")
    print("=" * 40)

    # 创建启用日志的智能体（使用默认配置）
    agent = ModernLangChainAgent(
        model_provider="anthropic",
        enable_logging=True  # 启用日志中间件
    )

    # 正常使用智能体
    response = agent.run("现在几点了？")
    print(f"回答: {response}")

    # 获取执行统计
    summary = agent.get_execution_summary()
    if summary:
        print(f"📊 会话统计: {summary['metrics']['model_calls_count']} 次模型调用")


def example_custom_config():
    """自定义配置示例"""
    print("\n⚙️  自定义配置示例")
    print("=" * 40)

    # 创建自定义配置
    config = MiddlewareConfig(
        log_level="DEBUG",                           # 详细日志
        log_to_console=True,                         # 控制台输出
        log_to_file=True,                            # 同时输出到文件
        log_file_path="logs/agent_detailed.log",     # 日志文件路径
        enable_performance_monitoring=True,          # 启用性能监控
        enable_tool_tracking=True,                   # 启用工具追踪
        max_log_length=1000,                         # 最大日志长度
    )

    # 使用自定义配置
    agent = ModernLangChainAgent(
        model_provider="anthropic",
        enable_logging=True,
        middleware_config=config
    )

    # 执行一些复杂查询
    queries = [
        "明天杭州适合钓鱼吗？",
        "计算 25 * 8 + 100",
        "介绍一下LangChain框架"
    ]

    for query in queries:
        print(f"\n🔍 查询: {query}")
        response = agent.run(query)
        print(f"🤖 回答: {response[:100]}...")

    # 显示详细统计
    summary = agent.get_execution_summary()
    if summary:
        print(f"\n📈 详细统计:")
        print(f"   会话ID: {summary['session_id']}")
        print(f"   总耗时: {summary['metrics']['total_duration_ms']:.2f}ms")
        print(f"   模型调用: {summary['metrics']['model_calls_count']} 次")
        print(f"   工具调用: {summary['metrics']['tool_calls_count']} 次")
        print(f"   Token使用: {summary['metrics']['token_usage']}")
        print(f"   错误次数: {summary['metrics']['errors_count']}")


def example_environment_config():
    """环境变量配置示例"""
    print("\n🌍 环境变量配置示例")
    print("=" * 40)

    # 在.env文件中设置以下环境变量:
    # AGENT_LOG_LEVEL=DEBUG
    # AGENT_LOG_CONSOLE=true
    # AGENT_LOG_FILE=true
    # AGENT_LOG_FILE_PATH=logs/agent_from_env.log
    # AGENT_PERF_MONITOR=true
    # AGENT_TOOL_TRACKING=true
    # AGENT_SENSITIVE_FILTER=true

    print("请确保在.env文件中设置了以下环境变量:")
    print("- AGENT_LOG_LEVEL=DEBUG")
    print("- AGENT_LOG_CONSOLE=true")
    print("- AGENT_LOG_FILE=true")
    print("- AGENT_LOG_FILE_PATH=logs/agent_from_env.log")

    # 创建智能体（自动从环境变量读取配置）
    agent = ModernLangChainAgent(
        model_provider="anthropic",
        enable_logging=True  # 配置将从环境变量自动加载
    )

    response = agent.run("环境配置测试：计算 100 * 5")
    print(f"回答: {response}")


def example_no_logging():
    """禁用日志示例"""
    print("\n🔇 禁用日志示例")
    print("=" * 40)

    # 创建禁用日志的智能体
    agent = ModernLangChainAgent(
        model_provider="anthropic",
        enable_logging=False  # 禁用日志中间件
    )

    response = agent.run("无日志模式测试：现在几点了？")
    print(f"回答: {response}")

    # 检查统计数据
    summary = agent.get_execution_summary()
    print(f"统计数据: {summary}")  # 应该返回 None


def example_performance_comparison():
    """性能对比示例"""
    print("\n⚡ 性能对比示例")
    print("=" * 40)

    import time

    # 测试启用日志的性能
    start_time = time.time()
    agent_with_logging = ModernLangChainAgent(enable_logging=True)
    response1 = agent_with_logging.run("性能测试：计算 50 + 30")
    time_with_logging = (time.time() - start_time) * 1000

    # 测试禁用日志的性能
    start_time = time.time()
    agent_without_logging = ModernLangChainAgent(enable_logging=False)
    response2 = agent_without_logging.run("性能测试：计算 50 + 30")
    time_without_logging = (time.time() - start_time) * 1000

    print(f"启用日志耗时: {time_with_logging:.2f}ms")
    print(f"禁用日志耗时: {time_without_logging:.2f}ms")
    print(f"日志开销: {time_with_logging - time_without_logging:.2f}ms")


def main():
    """主函数"""
    print("🚀 AgentLoggingMiddleware 使用示例")
    print("=" * 50)

    try:
        example_basic_usage()
        example_custom_config()
        example_environment_config()
        example_no_logging()
        example_performance_comparison()

        print("\n✅ 所有示例执行完成!")
        print("\n💡 提示:")
        print("- 查看生成的日志文件: logs/")
        print("- 在实际项目中，建议设置 AGENT_LOG_FILE=true 来持久化日志")
        print("- 生产环境中可以设置 AGENT_LOG_LEVEL=INFO 来减少日志量")

    except Exception as e:
        print(f"❌ 示例执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()