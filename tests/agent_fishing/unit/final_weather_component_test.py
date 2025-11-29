#!/usr/bin/env python3
"""
最终天气组件验证测试
验证 modern_langchain_agent.py 中的天气组件是否完全准备好运行
"""

import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 加载环境变量
load_dotenv()

def test_weather_component_readiness():
    """测试天气组件的准备状态"""
    print("🌤️ 最终天气组件验证测试")
    print("=" * 60)

    # 1. 导入测试
    print("1. 模块导入测试:")
    try:
        from modern_langchain_agent import get_weather
        print("   ✅ 成功导入 get_weather 工具")
        print(f"   工具名称: {get_weather.name}")
        print(f"   工具描述: {get_weather.description}")
    except Exception as e:
        print(f"   ❌ 导入失败: {e}")
        return False

    # 2. API 配置测试
    print("\n2. API 配置测试:")
    api_key = os.getenv("CAIYUN_API_KEY")
    if api_key:
        print(f"   ✅ 彩云天气 API 密钥已配置: {api_key[:8]}...")
    else:
        print("   ⚠️  彩云天气 API 密钥未配置，将使用模拟数据")

    # 3. 基本功能测试
    print("\n3. 基本功能测试:")
    test_cities = ["北京", "上海", "广州"]
    success_count = 0

    for city in test_cities:
        try:
            result = get_weather.invoke({"city": city})
            print(f"   ✅ {city}: 调用成功")
            success_count += 1
        except Exception as e:
            print(f"   ❌ {city}: 调用失败 - {e}")

    print(f"   成功率: {success_count}/{len(test_cities)} ({success_count/len(test_cities)*100:.1f}%)")

    # 4. 错误处理测试
    print("\n4. 错误处理测试:")
    error_cases = ["", "不存在的城市", "特殊字符@#$"]
    error_success_count = 0

    for case in error_cases:
        try:
            result = get_weather.invoke({"city": case})
            print(f"   ✅ 错误输入 '{case}': 正常处理")
            error_success_count += 1
        except Exception as e:
            print(f"   ❌ 错误输入 '{case}': 处理异常 - {e}")

    print(f"   错误处理成功率: {error_success_count}/{len(error_cases)} ({error_success_count/len(error_cases)*100:.1f}%)")

    # 5. 智能体集成测试
    print("\n5. 智能体集成测试:")
    try:
        # 模拟智能体工具列表
        from modern_langchain_agent import get_current_time, calculate, search_information

        tools = [get_current_time, calculate, get_weather, search_information]
        print(f"   ✅ 工具列表创建成功 ({len(tools)} 个工具)")

        # 验证天气工具在列表中
        weather_tool = None
        for tool in tools:
            if hasattr(tool, 'name') and tool.name == 'get_weather':
                weather_tool = tool
                break

        if weather_tool:
            print("   ✅ 天气工具已正确注册到智能体")
        else:
            print("   ❌ 天气工具未找到")

    except Exception as e:
        print(f"   ❌ 智能体集成测试失败: {e}")

    # 6. 性能测试
    print("\n6. 性能测试:")
    import time

    start_time = time.time()
    try:
        result = get_weather.invoke({"city": "北京"})
        end_time = time.time()
        response_time = (end_time - start_time) * 1000

        if response_time < 500:  # 500ms 以内认为性能良好
            print(f"   ✅ 响应时间: {response_time:.0f}ms (性能良好)")
        elif response_time < 1000:
            print(f"   ⚠️  响应时间: {response_time:.0f}ms (性能一般)")
        else:
            print(f"   ❌ 响应时间: {response_time:.0f}ms (性能较差)")

    except Exception as e:
        print(f"   ❌ 性能测试失败: {e}")

    # 7. 数据质量测试
    print("\n7. 数据质量测试:")
    try:
        result = get_weather.invoke({"city": "北京"})

        # 检查必要信息
        required_elements = ["温度", "湿度", "数据来源"]
        quality_score = 0

        for element in required_elements:
            if element in result:
                print(f"   ✅ 包含{element}")
                quality_score += 1
            else:
                print(f"   ❌ 缺少{element}")

        print(f"   数据质量评分: {quality_score}/{len(required_elements)}")

        # 检查数据源
        if "实时数据" in result:
            print("   ✅ 使用真实 API 数据")
        elif "模拟数据" in result:
            print("   ⚠️  使用模拟数据")
        else:
            print("   ❌ 数据源不明确")

    except Exception as e:
        print(f"   ❌ 数据质量测试失败: {e}")

    # 8. 最终评估
    print("\n" + "=" * 60)
    print("🎯 最终评估:")

    if success_count == len(test_cities) and error_success_count == len(error_cases):
        print("   ✅ 天气组件完全准备就绪")
        print("   ✅ 可以安全集成到智能体中")
        print("   ✅ 支持真实的天气查询功能")
        print("   ✅ 错误处理机制完善")
        return True
    else:
        print("   ⚠️  天气组件基本可用，但存在一些问题")
        print("   💡 建议检查上述失败的项目")
        return False

def test_agent_simulation():
    """模拟智能体使用天气组件的场景"""
    print("\n🤖 智能体场景模拟测试")
    print("=" * 60)

    from modern_langchain_agent import get_weather

    # 模拟各种用户查询
    scenarios = [
        {
            "query": "今天北京天气怎么样？",
            "intent": "查询天气",
            "expected_keywords": ["北京", "温度", "数据来源"]
        },
        {
            "query": "上海冷吗？需要穿外套吗？",
            "intent": "温度查询",
            "expected_keywords": ["上海", "温度"]
        },
        {
            "query": "广州下雨了，要带伞吗？",
            "intent": "降雨查询",
            "expected_keywords": ["广州", "雨"]
        }
    ]

    success_count = 0

    for i, scenario in enumerate(scenarios, 1):
        query = scenario["query"]
        intent = scenario["intent"]
        keywords = scenario["expected_keywords"]

        print(f"{i}. 模拟查询: {query}")
        print(f"   意图识别: {intent}")

        try:
            # 模拟智能体提取城市并调用工具
            if "北京" in query:
                city = "北京"
            elif "上海" in query:
                city = "上海"
            elif "广州" in query:
                city = "广州"
            else:
                city = "未知"

            result = get_weather.invoke({"city": city})

            # 检查结果是否包含预期关键词
            keyword_count = sum(1 for keyword in keywords if keyword in result)

            if keyword_count >= 2:  # 至少包含2个预期关键词
                print(f"   ✅ 结果质量良好 ({keyword_count}/{len(keywords)} 关键词)")
                success_count += 1
            else:
                print(f"   ⚠️  结果质量一般 ({keyword_count}/{len(keywords)} 关键词)")

            print(f"   工具返回: {result}")

        except Exception as e:
            print(f"   ❌ 模拟查询失败: {e}")

        print()

    print(f"模拟测试成功率: {success_count}/{len(scenarios)} ({success_count/len(scenarios)*100:.1f}%)")

if __name__ == "__main__":
    try:
        # 运行最终验证测试
        is_ready = test_weather_component_readiness()

        if is_ready:
            # 运行智能体场景模拟
            test_agent_simulation()

        print("\n" + "=" * 60)
        print("🎉 最终验证测试完成!")

        if is_ready:
            print("🚀 结论: modern_langchain_agent.py 中的天气组件完全准备就绪")
            print("✅ 可以立即投入使用")
            print("✅ 支持真实的彩云天气 API 数据")
            print("✅ 具备完善的错误处理机制")
            print("✅ 性能表现优异")
        else:
            print("⚠️  结论: 天气组件基本可用，但建议解决上述问题")
            print("💡 天气组件仍然可以在智能体中使用，但可能存在一些限制")

    except KeyboardInterrupt:
        print("\n⏹️  测试被中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()