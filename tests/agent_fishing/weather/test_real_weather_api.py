#!/usr/bin/env python3
"""
彩云天气 API 真实场景测试
使用真实 API 密钥测试各种天气查询场景
"""

import os
import sys
import time
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.weather.weather_service import CaiyunWeatherService

# 加载环境变量
load_dotenv()

def test_real_api_calls():
    """测试真实 API 调用"""
    print("🌤️  彩云天气 API 真实场景测试")
    print("=" * 50)

    # 从环境变量获取 API 密钥
    api_key = os.getenv("CAIYUN_API_KEY")
    if not api_key:
        print("❌ 未设置彩云天气 API 密钥")
        print("请在 .env 文件中设置 CAIYUN_API_KEY")
        return

    service = CaiyunWeatherService(api_key=api_key)

    if not service.api_key:
        print("❌ API 密钥未设置")
        return

    print(f"✅ 已配置 API 密钥: {api_key[:8]}...")
    print()

    # 测试城市列表
    test_cities = [
        "北京", "上海", "广州", "深圳", "杭州", "成都", "西安",
        "武汉", "南京", "重庆", "天津", "苏州"
    ]

    print(f"测试 {len(test_cities)} 个城市的真实天气数据:")
    print("-" * 50)

    successful_calls = 0
    failed_calls = 0

    for i, city in enumerate(test_cities, 1):
        print(f"{i:2d}. {city}: ", end="")

        try:
            start_time = time.time()
            weather_data, source = service.get_weather(city)
            end_time = time.time()

            if "API" in source:
                successful_calls += 1
                print(f"✅ {weather_data.condition}, {weather_data.temperature}°C "
                      f"(湿度 {weather_data.humidity}%, 风速 {weather_data.wind_speed:.1f}km/h)")
                print(f"     响应时间: {(end_time - start_time)*1000:.0f}ms")
                print(f"     数据来源: {source}")
            else:
                failed_calls += 1
                print(f"❌ 使用模拟数据: {weather_data.condition}, {weather_data.temperature}°C")
                print(f"     原因: {source}")

        except Exception as e:
            failed_calls += 1
            print(f"❌ 调用失败: {str(e)}")

        print()

    print("=" * 50)
    print(f"测试统计:")
    print(f"✅ 成功调用: {successful_calls}/{len(test_cities)}")
    print(f"❌ 失败调用: {failed_calls}/{len(test_cities)}")
    print(f"📊 成功率: {successful_calls/len(test_cities)*100:.1f}%")

def test_detailed_weather_info():
    """测试详细天气信息"""
    print("\n🔍 详细天气信息测试")
    print("=" * 50)

    api_key = os.getenv("CAIYUN_API_KEY")
    if not api_key:
        print("❌ 未设置彩云天气 API 密钥")
        return

    service = CaiyunWeatherService(api_key=api_key)

    # 测试北京的详细天气信息
    city = "北京"
    print(f"获取 {city} 的详细天气信息:")

    weather_data, source = service.get_weather(city)

    print(f"🌡️  温度: {weather_data.temperature}°C")
    print(f"🤗 体感温度: {weather_data.apparent_temperature}°C")
    print(f"💧 湿度: {weather_data.humidity}%")
    print(f"🌫️  气压: {weather_data.pressure} hPa")
    print(f"💨 风速: {weather_data.wind_speed} km/h")
    print(f"🧭 风向: {weather_data.wind_direction}°")
    print(f"☁️  天气状况: {weather_data.condition}")
    print(f"📍 数据来源: {source}")

    # 显示完整的数据结构
    print(f"\n📋 完整数据结构:")
    print(f"   temperature: {weather_data.temperature}")
    print(f"   apparent_temperature: {weather_data.apparent_temperature}")
    print(f"   humidity: {weather_data.humidity}")
    print(f"   pressure: {weather_data.pressure}")
    print(f"   wind_speed: {weather_data.wind_speed}")
    print(f"   wind_direction: {weather_data.wind_direction}")
    print(f"   condition: {weather_data.condition}")
    print(f"   description: {weather_data.description}")

def test_error_scenarios():
    """测试错误场景"""
    print("\n⚠️  错误场景测试")
    print("=" * 50)

    api_key = os.getenv("CAIYUN_API_KEY")
    if not api_key:
        print("❌ 未设置彩云天气 API 密钥")
        return

    service = CaiyunWeatherService(api_key=api_key)

    # 测试无效 API 密钥
    print("1. 测试无效 API 密钥:")
    invalid_service = CaiyunWeatherService(api_key="invalid_key")
    weather_data, source = invalid_service.get_weather("北京")
    print(f"   结果: {source}")

    # 测试不存在的城市
    print("\n2. 测试不存在的城市:")
    weather_data, source = service.get_weather("不存在的城市")
    print(f"   结果: {source}")

    # 测试特殊字符
    print("\n3. 测试特殊字符城市名:")
    weather_data, source = service.get_weather("城市@#$")
    print(f"   结果: {source}")

    # 测试空字符串
    print("\n4. 测试空字符串:")
    weather_data, source = service.get_weather("")
    print(f"   结果: {source}")

def test_performance():
    """性能测试"""
    print("\n⚡ 性能测试")
    print("=" * 50)

    api_key = os.getenv("CAIYUN_API_KEY")
    if not api_key:
        print("❌ 未设置彩云天气 API 密钥")
        return

    service = CaiyunWeatherService(api_key=api_key)

    test_cities = ["北京", "上海", "广州", "深圳", "杭州"]
    num_tests = 3

    print(f"对 {len(test_cities)} 个城市进行 {num_tests} 轮性能测试:")

    all_times = []

    for round_num in range(num_tests):
        print(f"\n第 {round_num + 1} 轮测试:")
        round_times = []

        for city in test_cities:
            start_time = time.time()
            weather_data, source = service.get_weather(city)
            end_time = time.time()

            response_time = (end_time - start_time) * 1000
            round_times.append(response_time)

            status = "✅" if "API" in source else "❌"
            print(f"  {city}: {status} {response_time:.0f}ms")

        avg_time = sum(round_times) / len(round_times)
        print(f"  平均响应时间: {avg_time:.0f}ms")
        all_times.extend(round_times)

    overall_avg = sum(all_times) / len(all_times)
    min_time = min(all_times)
    max_time = max(all_times)

    print(f"\n📊 性能统计:")
    print(f"   总请求数: {len(all_times)}")
    print(f"   平均响应时间: {overall_avg:.0f}ms")
    print(f"   最快响应时间: {min_time:.0f}ms")
    print(f"   最慢响应时间: {max_time:.0f}ms")
    print(f"   每秒可处理: {1000/overall_avg:.1f} 个请求")

def test_raw_api_call():
    """测试原始 API 调用"""
    print("\n🔧 原始 API 调用测试")
    print("=" * 50)

    api_key = os.getenv("CAIYUN_API_KEY")
    if not api_key:
        print("❌ 未设置彩云天气 API 密钥")
        return

    service = CaiyunWeatherService(api_key=api_key)

    # 直接调用 API 方法
    print("直接调用彩云天气 API:")

    # 北京坐标
    longitude, latitude = 116.4074, 39.9042

    try:
        raw_data = service.call_weather_api(longitude, latitude)

        if raw_data:
            print("✅ API 调用成功")
            print(f"   状态: {raw_data.get('status')}")
            print(f"   API 版本: {raw_data.get('api_version')}")
            print(f"   更新时间: {raw_data.get('server_time')}")

            # 显示原始响应结构
            result = raw_data.get('result', {})
            realtime = result.get('realtime', {})

            print(f"\n📡 原始响应数据结构:")
            print(f"   温度: {realtime.get('temperature')}°C")
            print(f"   湿度: {realtime.get('humidity')}%")
            print(f"   气压: {realtime.get('pressure')} hPa")
            print(f"   天气代码: {realtime.get('skycon')}")
            print(f"   风速: {realtime.get('wind', {}).get('speed')} km/h")
            print(f"   风向: {realtime.get('wind', {}).get('direction')}°")
        else:
            print("❌ API 调用失败")

    except Exception as e:
        print(f"❌ API 调用异常: {str(e)}")

if __name__ == "__main__":
    try:
        # 运行所有测试
        test_real_api_calls()
        test_detailed_weather_info()
        test_error_scenarios()
        test_performance()
        test_raw_api_call()

        print("\n🎉 所有测试完成!")

    except KeyboardInterrupt:
        print("\n⏹️  测试被中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")