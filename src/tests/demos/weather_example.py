#!/usr/bin/env python3
"""
彩云天气 API 使用示例
演示如何使用天气服务模块获取真实天气数据
"""

import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.weather.weather_service import CaiyunWeatherService, get_weather_info

def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===\n")

    # 测试多个城市的天气
    cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "西安"]

    for city in cities:
        weather_info = get_weather_info(city)
        print(weather_info)
        print("-" * 50)

def example_advanced_usage():
    """高级使用示例"""
    print("\n=== 高级使用示例 ===\n")

    # 创建天气服务实例
    service = CaiyunWeatherService()

    # 检查是否配置了 API 密钥
    if service.api_key:
        print(f"✅ 已配置彩云天气 API 密钥")

        # 获取北京天气的详细信息
        weather_data, source = service.get_weather("北京")

        print(f"城市: 北京")
        print(f"温度: {weather_data.temperature}°C")
        print(f"体感温度: {weather_data.apparent_temperature}°C")
        print(f"湿度: {weather_data.humidity}%")
        print(f"气压: {weather_data.pressure} hPa")
        print(f"风速: {weather_data.wind_speed} km/h")
        print(f"风向: {weather_data.wind_direction}°")
        print(f"天气状况: {weather_data.condition}")
        print(f"数据来源: {source}")

    else:
        print("❌ 未配置彩云天气 API 密钥")
        print("请在 .env 文件中设置 CAIYUN_API_KEY")
        print("或设置环境变量: export CAIYUN_API_KEY=your_api_key")

def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===\n")

    service = CaiyunWeatherService()

    # 测试不存在的城市
    print("测试不存在的城市:")
    weather_info = get_weather_info("不存在的城市")
    print(weather_info)

    # 测试空字符串
    print("\n测试空字符串:")
    weather_info = get_weather_info("")
    print(weather_info)

    # 测试特殊字符
    print("\n测试特殊字符:")
    weather_info = get_weather_info("城市@#$")
    print(weather_info)

def example_coordinate_lookup():
    """坐标查找示例"""
    print("\n=== 坐标查找示例 ===\n")

    service = CaiyunWeatherService()

    # 显示支持的城市及其坐标
    supported_cities = [
        "北京", "上海", "广州", "深圳", "杭州", "成都", "西安",
        "武汉", "南京", "重庆", "天津", "苏州", "青岛", "大连", "厦门"
    ]

    print("支持的城市及其坐标:")
    for city in supported_cities:
        coords = service.get_coordinates(city)
        if coords:
            lon, lat = coords
            print(f"{city}: 经度 {lon}, 纬度 {lat}")
        else:
            print(f"{city}: 未找到坐标")

def example_with_api_key():
    """使用真实 API 的示例（需要配置 API 密钥）"""
    print("\n=== 真实 API 调用示例 ===\n")

    # 从环境变量获取 API 密钥
    api_key = os.getenv("CAIYUN_API_KEY")

    if not api_key:
        print("⚠️  未配置彩云天气 API 密钥")
        print("要测试真实 API，请:")
        print("1. 在 https://www.caiyunapp.com/ 注册账号")
        print("2. 获取 API 密钥")
        print("3. 设置环境变量: export CAIYUN_API_KEY=your_api_key")
        print("4. 重新运行此示例")
        return

    # 使用真实 API 密钥创建服务
    service = CaiyunWeatherService(api_key=api_key)

    test_city = "北京"
    print(f"正在获取 {test_city} 的真实天气数据...")

    weather_data, source = service.get_weather(test_city)

    print(f"\n{test_city} 天气详情:")
    print(f"温度: {weather_data.temperature}°C")
    print(f"体感温度: {weather_data.apparent_temperature}°C")
    print(f"湿度: {weather_data.humidity}%")
    print(f"气压: {weather_data.pressure} hPa")
    print(f"风速: {weather_data.wind_speed} km/h")
    print(f"风向: {weather_data.wind_direction}°")
    print(f"天气状况: {weather_data.condition}")
    print(f"数据来源: {source}")

def performance_test():
    """性能测试示例"""
    print("\n=== 性能测试 ===\n")

    import time

    service = CaiyunWeatherService()
    test_cities = ["北京", "上海", "广州", "深圳", "杭州"]

    print(f"测试 {len(test_cities)} 个城市的查询性能:")

    start_time = time.time()

    for city in test_cities:
        weather_info = get_weather_info(city)
        print(f"✓ {city}: 查询完成")

    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / len(test_cities)

    print(f"\n性能统计:")
    print(f"总耗时: {total_time:.3f} 秒")
    print(f"平均每个城市: {avg_time:.3f} 秒")
    print(f"每秒可处理: {len(test_cities) / total_time:.1f} 个城市")

if __name__ == "__main__":
    print("🌤️  彩云天气 API 使用示例")
    print("=" * 50)

    # 运行各种示例
    example_basic_usage()
    example_advanced_usage()
    example_error_handling()
    example_coordinate_lookup()
    example_with_api_key()
    performance_test()

    print("\n📝 使用说明:")
    print("1. 复制 .env.example 为 .env")
    print("2. 在 .env 中配置 CAIYUN_API_KEY")
    print("3. 重新运行此程序以获取真实天气数据")
    print("4. 未配置 API 密钥时会使用模拟数据")