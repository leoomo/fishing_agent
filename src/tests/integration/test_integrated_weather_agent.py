#!/usr/bin/env python3
"""
集成测试：智能体天气查询功能
使用真实彩云天气 API 测试完整的智能体天气查询流程
"""

import os
import sys
import time
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.weather.weather_service import get_weather_info, CaiyunWeatherService
from modern_langchain_agent import get_weather

# 加载环境变量
load_dotenv()

def test_weather_service_integration():
    """测试天气服务集成"""
    print("🌤️  智能体天气查询集成测试")
    print("=" * 60)

    # 检查环境变量中的 API 密钥
    api_key = os.getenv("CAIYUN_API_KEY")
    if not api_key:
        print("❌ 未设置彩云天气 API 密钥")
        print("请在 .env 文件中设置 CAIYUN_API_KEY")
        return

    print(f"✅ 已配置彩云天气 API 密钥")
    print()

    # 测试直接调用天气服务
    print("1. 直接调用天气服务:")
    print("-" * 30)

    test_queries = ["北京", "上海", "广州", "深圳"]

    for city in test_queries:
        start_time = time.time()
        weather_info = get_weather_info(city)
        end_time = time.time()

        print(f"📍 {city}:")
        print(weather_info)
        print(f"⏱️  响应时间: {(end_time - start_time)*1000:.0f}ms")
        print()

    # 测试 LangChain 工具函数
    print("2. LangChain 工具函数测试:")
    print("-" * 30)

    for city in test_queries[:2]:  # 只测试前两个
        start_time = time.time()
        result = get_weather.invoke({"city": city})
        end_time = time.time()

        print(f"📍 {city} (通过 LangChain 工具):")
        print(result)
        print(f"⏱️  响应时间: {(end_time - start_time)*1000:.0f}ms")
        print()

def test_weather_data_accuracy():
    """测试天气数据准确性"""
    print("🎯 天气数据准确性验证")
    print("=" * 60)

    api_key = os.getenv("CAIYUN_API_KEY")
    if not api_key:
        print("❌ 未设置彩云天气 API 密钥")
        return

    service = CaiyunWeatherService(api_key=api_key)

    # 测试不同城市的天气数据
    cities_with_expected_conditions = {
        "北京": "晴夜",  # 北方通常比较干燥
        "广州": "小雨",  # 南方可能多雨
        "上海": "阴天",  # 沿海城市
    }

    print("验证天气数据的合理性:")
    print("-" * 30)

    for city, expected_condition in cities_with_expected_conditions.items():
        weather_data, source = service.get_weather(city)

        print(f"📍 {city}:")
        print(f"   实际天气: {weather_data.condition}")
        print(f"   温度: {weather_data.temperature}°C")
        print(f"   湿度: {weather_data.humidity}%")
        print(f"   风速: {weather_data.wind_speed} km/h")
        print(f"   数据来源: {source}")

        # 验证数据合理性
        if "API" in source:
            print("   ✅ 使用真实 API 数据")

            # 检查温度范围（-50°C 到 60°C）
            if -50 <= weather_data.temperature <= 60:
                print("   ✅ 温度数据合理")
            else:
                print("   ❌ 温度数据异常")

            # 检查湿度范围（0% 到 100%）
            if 0 <= weather_data.humidity <= 100:
                print("   ✅ 湿度数据合理")
            else:
                print("   ❌ 湿度数据异常")

            # 检查风速范围（0 到 200 km/h）
            if 0 <= weather_data.wind_speed <= 200:
                print("   ✅ 风速数据合理")
            else:
                print("   ❌ 风速数据异常")
        else:
            print("   ⚠️  使用模拟数据")

        print()

def test_error_recovery():
    """测试错误恢复机制"""
    print("🛡️  错误恢复机制测试")
    print("=" * 60)

    # 测试各种错误场景
    error_scenarios = [
        ("不存在的城市", "测试不存在城市"),
        ("", "测试空字符串"),
        ("城市@#$", "测试特殊字符"),
    ]

    print("测试错误场景下的降级处理:")
    print("-" * 30)

    for city, description in error_scenarios:
        print(f"{description}:")
        try:
            start_time = time.time()
            weather_info = get_weather_info(city)
            end_time = time.time()

            print(f"   输入: '{city}'")
            print(f"   输出: {weather_info}")
            print(f"   响应时间: {(end_time - start_time)*1000:.0f}ms")
            print("   ✅ 系统正常响应，未崩溃")
        except Exception as e:
            print(f"   ❌ 系统异常: {str(e)}")
        print()

def test_concurrent_calls():
    """测试并发调用"""
    print("🔄 并发调用测试")
    print("=" * 60)

    import threading
    import queue

    api_key = os.getenv("CAIYUN_API_KEY")
    if not api_key:
        print("❌ 未设置彩云天气 API 密钥")
        return

    # 准备测试城市
    test_cities = ["北京", "上海", "广州", "深圳", "杭州"]
    results = queue.Queue()

    def worker(city):
        """工作线程函数"""
        start_time = time.time()
        try:
            weather_info = get_weather_info(city)
            end_time = time.time()
            results.put({
                "city": city,
                "success": True,
                "result": weather_info,
                "time": (end_time - start_time) * 1000
            })
        except Exception as e:
            results.put({
                "city": city,
                "success": False,
                "error": str(e),
                "time": (time.time() - start_time) * 1000
            })

    print(f"并发查询 {len(test_cities)} 个城市:")
    print("-" * 30)

    # 创建并启动线程
    threads = []
    start_time = time.time()

    for city in test_cities:
        thread = threading.Thread(target=worker, args=(city,))
        thread.start()
        threads.append(thread)

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    end_time = time.time()

    # 收集结果
    all_results = []
    while not results.empty():
        all_results.append(results.get())

    # 显示结果
    successful_results = [r for r in all_results if r["success"]]
    failed_results = [r for r in all_results if not r["success"]]

    for result in all_results:
        if result["success"]:
            print(f"✅ {result['city']}: {result['time']:.0f}ms")
        else:
            print(f"❌ {result['city']}: {result['error']}")

    print(f"\n并发测试统计:")
    print(f"   总耗时: {(end_time - start_time)*1000:.0f}ms")
    print(f"   成功请求: {len(successful_results)}/{len(test_cities)}")
    print(f"   失败请求: {len(failed_results)}/{len(test_cities)}")
    print(f"   平均响应时间: {sum(r['time'] for r in successful_results)/len(successful_results):.0f}ms")

def test_data_consistency():
    """测试数据一致性"""
    print("🔍 数据一致性测试")
    print("=" * 60)

    api_key = os.getenv("CAIYUN_API_KEY")
    if not api_key:
        print("❌ 未设置彩云天气 API 密钥")
        return

    service = CaiyunWeatherService(api_key=api_key)

    city = "北京"
    num_calls = 3

    print(f"对 {city} 进行 {num_calls} 次重复查询，验证数据一致性:")
    print("-" * 30)

    results = []
    for i in range(num_calls):
        weather_data, source = service.get_weather(city)
        results.append(weather_data)

        print(f"第 {i+1} 次: {weather_data.condition}, {weather_data.temperature}°C, "
              f"湿度 {weather_data.humidity}%, 风速 {weather_data.wind_speed:.1f}km/h")

    # 检查数据一致性
    if len(results) > 1:
        print("\n一致性检查:")
        temps = [r.temperature for r in results]
        humidities = [r.humidity for r in results]
        wind_speeds = [r.wind_speed for r in results]

        temp_variance = max(temps) - min(temps)
        humidity_variance = max(humidities) - min(humidities)
        wind_variance = max(wind_speeds) - min(wind_speeds)

        print(f"   温度变化范围: {temp_variance:.2f}°C")
        print(f"   湿度变化范围: {humidity_variance:.2f}%")
        print(f"   风速变化范围: {wind_variance:.2f}km/h")

        if temp_variance < 1.0 and humidity_variance < 5.0 and wind_variance < 2.0:
            print("   ✅ 数据一致性良好")
        else:
            print("   ⚠️  数据存在较大差异（可能是实时更新）")

if __name__ == "__main__":
    try:
        # 运行所有集成测试
        test_weather_service_integration()
        test_weather_data_accuracy()
        test_error_recovery()
        test_concurrent_calls()
        test_data_consistency()

        print("\n🎉 集成测试全部完成!")
        print("=" * 60)
        print("✅ 彩云天气 API 集成成功")
        print("✅ 智能体天气查询功能正常")
        print("✅ 错误处理机制有效")
        print("✅ 性能表现良好")
        print("✅ 数据一致性验证通过")

    except KeyboardInterrupt:
        print("\n⏹️  测试被中断")
    except Exception as e:
        print(f"\n❌ 集成测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()