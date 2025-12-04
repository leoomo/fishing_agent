#!/usr/bin/env python3
"""
智能钓鱼助手调试脚本
支持多种运行模式和模型提供商切换
"""

import os
import sys
import time
import warnings
from typing import Optional

# 抑制警告
warnings.filterwarnings("ignore", message="LangSmith now uses UUID v7")

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")

    required_keys = {
        'DASHSCOPE_API_KEY': '通义千问 API',
        'CAIYUN_API_KEY': '彩云天气 API',
        'AMAP_API_KEY': '高德地图 API'
    }

    missing_keys = []
    for key, name in required_keys.items():
        if os.getenv(key):
            print(f"✅ {name}: 已配置")
        else:
            print(f"❌ {name}: 未配置")
            missing_keys.append(key)

    if missing_keys:
        print(f"\n⚠️  缺少必需的API密钥: {', '.join(missing_keys)}")
        print("请检查 .env 文件配置")
        return False

    print("✅ 环境配置检查通过")
    return True

def test_agent_creation(model_provider: str = "qwen") -> bool:
    """测试Agent创建"""
    print(f"\n🤖 测试 {model_provider} Agent 创建...")

    try:
        from packages.agent_fishing import create_agent, ModelFactory

        # 检查模型提供商可用性
        available_providers = ModelFactory.list_providers()
        print(f"📋 可用模型提供商: {list(available_providers.keys())}")

        if model_provider not in available_providers:
            print(f"❌ 不支持的模型提供商: {model_provider}")
            return False

        # 创建Agent
        agent = create_agent(
            model_provider=model_provider,
            enable_logging=True,
            timeout=60
        )

        print(f"✅ {model_provider} Agent 创建成功")
        print(f"🛠️  工具数量: {len(agent.tools)}")
        print(f"📊 模型: {agent.model_provider}")

        return True

    except Exception as e:
        print(f"❌ Agent 创建失败: {str(e)}")
        return False

def test_single_query(agent, query: str) -> bool:
    """测试单个查询"""
    print(f"\n📝 测试查询: {query}")
    print("🤔 正在思考...")

    try:
        start_time = time.time()
        response = agent.run(query)
        end_time = time.time()

        print(f"⏱️  响应时间: {end_time - start_time:.2f}秒")
        print(f"📄 响应长度: {len(response)}字符")
        print(f"\n🎯 回答:\n{response}")

        return True

    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")
        return False

def debug_weather_api_calls():
    """调试天气API调用和温度数据"""
    print("\n" + "="*60)
    print("🔍 调试天气API调用和温度数据")
    print("="*60)

    try:
        from packages.agent_fishing.tools.fishing.weather_api import get_weather_data as _get_weather_data
        from packages.agent_fishing.utils.coordinate import get_coordinates

        # 1. 测试地理编码
        print("📍 测试地理编码...")
        coords = get_coordinates("杭州")
        print(f"✅ 杭州坐标: {coords}")

        # 2. 测试天气数据获取
        print("\n🌤️ 测试天气数据获取...")
        from datetime import datetime
        target_date = datetime.now()
        weather_data = _get_weather_data("杭州", target_date)
        print(f"✅ 天气数据原始结构: {list(weather_data.keys())}")

        # 3. 检查温度字段
        print(f"\n🌡️ 检查温度相关字段:")
        temp_fields = {}
        for key, value in weather_data.items():
            if any(temp_keyword in key.lower() for temp_keyword in ['temp', 'temperature']):
                temp_fields[key] = value
                print(f"  {key}: {value} (类型: {type(value).__name__})")

        # 4. 检查小时温度数据
        hourly_temps = weather_data.get('hourly_temps', [])
        if hourly_temps:
            print(f"\n📊 小时温度数据: {len(hourly_temps)}个数据点")
            print(f"  温度范围: {min(hourly_temps):.1f}°C - {max(hourly_temps):.1f}°C")
            print(f"  平均温度: {sum(hourly_temps)/len(hourly_temps):.1f}°C")
        else:
            print(f"\n❌ 缺少小时温度数据")

        # 5. 检查数据质量
        data_quality = weather_data.get('data_quality', 'unknown')
        print(f"\n📈 数据质量: {data_quality}")

        return weather_data, coords

    except Exception as e:
        print(f"❌ 天气API调试失败: {str(e)}")
        import traceback
        print("\n📋 详细错误信息:")
        traceback.print_exc()
        return None, None

def direct_query_mode(agent, query: str):
    """直接查询模式 - 无需手动输入"""
    print("\n" + "="*60)
    print(f"🎣 智能钓鱼助手 - 直接查询模式")
    print("="*60)
    print(f"📝 查询内容: {query}")
    print("="*60)

    try:
        print("🤔 通义千问正在分析...")
        start_time = time.time()
        response = agent.run(query)
        end_time = time.time()

        print(f"\n⏱️  响应时间: {end_time - start_time:.2f}秒")
        print(f"📄 响应长度: {len(response)}字符")
        print(f"\n🎯 智能回答:\n{'='*60}")
        print(response)
        print(f"{'='*60}")

    except KeyboardInterrupt:
        print("\n\n⏹️  查询已取消")
    except Exception as e:
        print(f"\n❌ 处理请求时出错: {str(e)}")
        print("💡 请检查网络连接和API密钥配置")

def interactive_mode(agent):
    """交互模式"""
    print("\n" + "="*60)
    print("🎣 智能钓鱼助手 - 交互模式")
    print("="*60)
    print("💡 示例查询:")
    print("  - 明天杭州钓鱼怎么样？")
    print("  - 北京今天天气如何？")
    print("  - 推荐一些钓鱼装备")
    print("  - 现在几点了？")
    print("  - 今天白天上海钓鱼好吗？")
    print("\n输入 'quit', 'exit' 或 '退出' 结束对话")
    print("="*60)

    try:
        while True:
            user_input = input("\n🎣 请输入您的问题: ").strip()

            if user_input.lower() in ['quit', 'exit', '退出']:
                print("\n👋 感谢使用智能钓鱼助手！")
                break

            if not user_input:
                continue

            print(f"\n📝 您的问题: {user_input}")
            print("🤔 正在思考...")

            try:
                start_time = time.time()
                response = agent.run(user_input)
                end_time = time.time()

                print(f"\n🎯 回答 ({end_time - start_time:.2f}秒):")
                print(response)

            except KeyboardInterrupt:
                print("\n\n⏹️  查询已取消")
                continue
            except Exception as e:
                print(f"\n❌ 处理请求时出错: {str(e)}")
                print("💡 请检查网络连接和API密钥配置")

    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")

def batch_test_mode(agent):
    """批量测试模式"""
    print("\n" + "="*60)
    print("🧪 批量测试模式")
    print("="*60)

    test_queries = [
        "现在几点了？",
        "北京今天天气如何？",
        "明天杭州钓鱼怎么样？",
        "推荐一些钓鱼装备",
        "今天白天上海钓鱼好吗？",
        "这个周末适合钓鱼吗？"
    ]

    success_count = 0
    total_time = 0

    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 测试 {i}/{len(test_queries)}: {query}")

        try:
            start_time = time.time()
            response = agent.run(query)
            end_time = time.time()

            query_time = end_time - start_time
            total_time += query_time

            print(f"✅ 成功 ({query_time:.2f}秒, {len(response)}字符)")
            success_count += 1

            # 显示响应摘要
            response_preview = response[:100] + "..." if len(response) > 100 else response
            print(f"📄 摘要: {response_preview}")

        except Exception as e:
            print(f"❌ 失败: {str(e)}")

    print(f"\n📊 测试结果:")
    print(f"✅ 成功: {success_count}/{len(test_queries)}")
    print(f"⏱️  总耗时: {total_time:.2f}秒")
    print(f"📈 平均耗时: {total_time/len(test_queries):.2f}秒")
    print(f"🎯 成功率: {success_count/len(test_queries)*100:.1f}%")

def show_agent_stats(agent):
    """显示Agent统计信息"""
    print("\n📊 Agent 统计信息:")
    print("="*40)

    try:
        stats = agent.get_stats()
        llm_stats = agent.get_llm_stats()

        print(f"🤖 模型提供商: {stats.get('model_provider', 'Unknown')}")
        print(f"🛠️  工具数量: {stats.get('tools_count', 0)}")
        print(f"⏱️  超时设置: {stats.get('timeout', 0)}秒")
        print(f"🏗️  架构: {stats.get('architecture', 'Unknown')}")

        print(f"\n📈 LLM 调用统计:")
        print(f"  总调用次数: {llm_stats.get('total_model_calls', 0)}")
        print(f"  总错误次数: {llm_stats.get('total_errors', 0)}")
        print(f"  成功率: {llm_stats.get('success_rate', 0):.1f}%")
        print(f"  总Token数: {llm_stats.get('total_tokens', 0)}")

    except Exception as e:
        print(f"❌ 获取统计信息失败: {str(e)}")

def print_usage():
    """打印使用说明"""
    print("🎣 智能钓鱼助手调试脚本 v3.1.1")
    print("="*50)
    print("用法:")
    print("  python debug_agent.py [model_provider] [mode] [query]")
    print("")
    print("参数:")
    print("  model_provider  模型提供商 (qwen, zhipu, openai, doubao)")
    print("  mode           运行模式 (direct, interactive, test, batch, debug)")
    print("  query          查询内容 (direct模式时使用)")
    print("")
    print("示例:")
    print("  python debug_agent.py                    # 通义千问 + 直接查询(默认)")
    print("  python debug_agent.py qwen               # 通义千问 + 直接查询")
    print("  python debug_agent.py zhipu              # 智谱AI + 直接查询")
    print("  python debug_agent.py qwen interactive   # 通义千问 + 交互模式")
    print("  python debug_agent.py zhipu interactive  # 智谱AI + 交互模式")
    print("  python debug_agent.py qwen test           # 通义千问 + 测试模式")
    print("  python debug_agent.py qwen batch          # 通义千问 + 批量测试")
    print("  python debug_agent.py qwen debug          # 通义千问 + 调试模式(推荐)")
    print("  python debug_agent.py qwen direct \"今天白天北京钓鱼怎么样？\"  # 自定义查询")
    print("="*50)

def main():
    """主函数"""
    # 检查帮助参数
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['-h', '--help', 'help']:
        print_usage()
        return

    print("🎣 智能钓鱼助手调试脚本 v3.1.1")
    print("="*60)

    # 解析命令行参数
    model_provider = "qwen"  # 默认使用通义千问
    mode = "direct"         # 默认直接查询模式
    query = "今天去余杭区钓鱼，哪个时段比较合适？"  # 默认查询

    if len(sys.argv) > 1:
        model_provider = sys.argv[1]
    if len(sys.argv) > 2:
        mode = sys.argv[2]
    if len(sys.argv) > 3:
        query = sys.argv[3]

    print(f"🤖 使用模型: {model_provider}")
    print(f"🎮 运行模式: {mode}")
    if mode == "direct":
        print(f"📝 查询内容: {query}")
    elif mode == "debug":
        print(f"🔍 调试模式: 检查天气API和温度数据")
    elif mode == "interactive":
        print(f"💡 提示: 使用 'python debug_agent.py' 进入直接查询模式")

    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，程序退出")
        return

    # 测试Agent创建
    agent = None
    try:
        from packages.agent_fishing import create_agent
        agent = create_agent(
            model_provider=model_provider,
            enable_logging=True,
            timeout=60
        )
    except Exception as e:
        print(f"\n❌ Agent创建失败: {str(e)}")
        print("\n💡 可能的解决方案:")
        print("  1. 检查 .env 文件中的API密钥配置")
        print("  2. 确保网络连接正常")
        print("  3. 运行 'uv sync' 安装依赖")
        return

    # 根据模式运行
    if mode == "test":
        # 测试模式：运行几个示例查询
        test_queries = [
            "现在几点了？",
            "今天杭州钓鱼怎么样？"
        ]

        for query in test_queries:
            if not test_single_query(agent, query):
                print("⚠️  测试失败，但继续其他测试")

    elif mode == "batch":
        # 批量测试模式
        batch_test_mode(agent)

    elif mode == "debug":
        # 调试模式：检查天气API
        weather_data, coords = debug_weather_api_calls()
        if weather_data and coords:
            print(f"\n✅ API调试完成，现在测试完整查询...")
            direct_query_mode(agent, query)

    elif mode == "direct":
        # 直接查询模式
        direct_query_mode(agent, query)

    else:  # interactive or default
        # 交互模式
        interactive_mode(agent)

    # 显示统计信息
    if agent:
        show_agent_stats(agent)

if __name__ == "__main__":
    main()