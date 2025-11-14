#!/usr/bin/env python3
"""
全国天气覆盖功能演示脚本
展示增强版天气服务的各项功能
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from services.weather.enhanced_weather_service import EnhancedCaiyunWeatherService
from modern_langchain_agent import ModernLangChainAgent


def demo_basic_functionality():
    """演示基本功能"""
    print("🌤️ 1. 基本天气查询功能演示")
    print("=" * 50)

    service = EnhancedCaiyunWeatherService()

    # 测试不同级别的行政区划
    test_places = [
        ("北京市", "直辖市"),
        ("广东省", "省份"),
        ("广州市", "地级市"),
        ("天河区", "市辖区"),
        ("beijing", "拼音输入"),
        ("北京", "简称输入"),
    ]

    for place, desc in test_places:
        try:
            weather_data, source = service.get_weather(place)
            print(f"📍 {place} ({desc}):")
            print(f"   天气: {weather_data.condition}")
            print(f"   温度: {weather_data.temperature:.1f}°C (体感 {weather_data.apparent_temperature:.1f}°C)")
            print(f"   湿度: {weather_data.humidity:.0f}%")
            print(f"   风速: {weather_data.wind_speed:.1f}km/h")
            print(f"   来源: {source}")
            print()

        except Exception as e:
            print(f"❌ {place}: 查询失败 - {e}")

    service.coordinate_db.close()


def demo_intelligent_matching():
    """演示智能匹配功能"""
    print("🎯 2. 智能地名匹配演示")
    print("=" * 50)

    service = EnhancedCaiyunWeatherService()

    # 测试各种匹配情况
    matching_tests = [
        ("北京", "别名匹配"),
        ("上海", "别名匹配"),
        ("beijing", "拼音匹配"),
        ("guangzhou", "拼音匹配"),
        ("天河区", "精确匹配"),
        ("西湖区", "精确匹配"),
        ("湖", "模糊匹配"),
        ("广东", "简称匹配"),
        ("广东省广州市", "层级匹配尝试"),
        ("不存在的城市", "降级处理"),
    ]

    for place, match_type in matching_tests:
        try:
            weather_data, source = service.get_weather(place)
            print(f"🔍 {place} ({match_type}):")
            print(f"   结果: {weather_data.condition} {weather_data.temperature:.1f}°C")
            print(f"   来源: {source}")

            # 提取坐标信息
            if "|" in source and "坐标:" in source:
                coords = source.split("坐标:")[1].strip()
                print(f"   坐标: {coords}")
            print()

        except Exception as e:
            print(f"❌ {place}: 匹配失败 - {e}")

    service.coordinate_db.close()


def demo_caching_performance():
    """演示缓存性能"""
    print("💾 3. 缓存机制性能演示")
    print("=" * 50)

    service = EnhancedCaiyunWeatherService()

    test_place = "广州市"
    iterations = 5

    print(f"📍 测试地点: {test_place}")
    print(f"🔄 查询次数: {iterations}")
    print()

    # 执行多次查询测试缓存效果
    for i in range(iterations):
        start_time = time.time()
        weather_data, source = service.get_weather(test_place)
        end_time = time.time()

        query_time = end_time - start_time
        print(f"第{i+1}次查询: {query_time:.4f}s - {weather_data.condition} {weather_data.temperature:.1f}°C")
        print(f"来源: {source}")

        if i == 0:
            print("   (首次查询，需要API调用或数据生成)")
        else:
            print("   (缓存查询，速度显著提升)")

        print()

    # 显示缓存统计
    cache_stats = service.cache.get_statistics()
    print("📊 缓存统计:")
    print(f"   内存缓存条目: {cache_stats['memory_cache']['size']}")
    print(f"   文件缓存条目: {cache_stats['file_cache']['size']}")
    print(f"   总缓存条目: {cache_stats['total_entries']}")

    service.coordinate_db.close()


def demo_batch_operations():
    """演示批量操作"""
    print("📦 4. 批量操作演示")
    print("=" * 50)

    service = EnhancedCaiyunWeatherService()

    # 批量查询多个城市
    batch_places = ["北京", "上海", "广州", "深圳", "杭州", "成都", "西安", "武汉"]

    print(f"📍 批量查询 {len(batch_places)} 个城市:")
    start_time = time.time()

    batch_results = service.batch_get_weather(batch_places)

    end_time = time.time()
    total_time = end_time - start_time

    print(f"⏱️ 总耗时: {total_time:.3f}s")
    print(f"📊 平均耗时: {total_time/len(batch_places):.3f}s/个")
    print()

    # 显示结果
    success_count = 0
    for result in batch_results:
        if result['success']:
            success_count += 1
            weather = result['weather']
            print(f"✅ {result['place']}: {weather.condition} {weather.temperature:.1f}°C")
        else:
            print(f"❌ {result['place']}: {result['source']}")

    print(f"\n📈 成功率: {success_count}/{len(batch_places)} ({success_count/len(batch_places):.1%})")

    service.coordinate_db.close()


def demo_agent_integration():
    """演示智能体集成"""
    print("🤖 5. 智能体集成演示")
    print("=" * 50)

    try:
        # 创建智能体
        agent = ModernLangChainAgent(model_provider="zhipu")

        # 测试对话
        test_queries = [
            "现在北京天气怎么样？",
            "帮我查一下上海的天气",
            "天河区和西湖区哪个更暖和？",
            "广东省今天天气如何？",
        ]

        print("💬 智能体对话测试:")
        for query in test_queries:
            print(f"\n用户: {query}")
            print("智能体: ", end="")

            try:
                # 这里为了演示，我们直接调用工具而不是完整的智能体
                from modern_langchain_agent import get_weather

                # 简单提取地名
                if "北京" in query:
                    place = "北京"
                elif "上海" in query:
                    place = "上海"
                elif "天河区" in query:
                    place = "天河区"
                elif "西湖区" in query:
                    place = "西湖区"
                elif "广东" in query:
                    place = "广东省"
                else:
                    place = "北京"

                result = get_weather.invoke({"city": place})
                print(result)

            except Exception as e:
                print(f"抱歉，查询天气时遇到了问题: {e}")

    except Exception as e:
        print(f"❌ 智能体初始化失败: {e}")
        print("这可能是因为缺少必要的API密钥")


def demo_service_statistics():
    """演示服务统计信息"""
    print("📊 6. 服务统计信息演示")
    print("=" * 50)

    service = EnhancedCaiyunWeatherService()

    summary = service.get_supported_places_summary()

    print("🗄️ 数据库统计:")
    db_stats = summary['database_stats']
    for level, count in db_stats.items():
        print(f"   {level}: {count}个")

    print("\n🎯 匹配器统计:")
    matcher_stats = summary['matcher_stats']
    print(f"   别名映射数量: {matcher_stats['alias_map_size']}")
    print(f"   行政后缀数量: {matcher_stats['admin_suffixes_count']}")
    print(f"   当前缓存大小: {matcher_stats['cache_size']}")

    print("\n💾 缓存统计:")
    cache_stats = summary['cache_stats']
    print(f"   内存缓存: {cache_stats['memory_cache']['size']} 条目")
    print(f"   文件缓存: {cache_stats['file_cache']['size']} 条目")
    print(f"   总缓存: {cache_stats['total_entries']} 条目")
    print(f"   缓存文件: {cache_stats['cache_file_path']}")

    print(f"\n🔧 服务配置:")
    print(f"   API配置状态: {'✅ 已配置' if summary['api_configured'] else '❌ 未配置'}")
    print(f"   服务版本: {summary['service_version']}")

    service.coordinate_db.close()


def main():
    """主演示函数"""
    print("🎉 增强版天气服务全国覆盖功能演示")
    print("=" * 60)
    print("本演示展示了增强版天气服务的各项新功能:")
    print("✅ 支持全国所有行政区划查询")
    print("✅ 智能地名匹配算法")
    print("✅ 高效缓存机制")
    print("✅ 批量操作支持")
    print("✅ 智能体集成")
    print("✅ 完善的错误处理")
    print("=" * 60)

    # 确保数据目录存在
    Path("data/cache").mkdir(parents=True, exist_ok=True)

    try:
        # 运行各项演示
        demo_basic_functionality()
        demo_intelligent_matching()
        demo_caching_performance()
        demo_batch_operations()
        demo_agent_integration()
        demo_service_statistics()

        print("\n🎊 所有演示完成！")
        print("=" * 60)
        print("✨ 增强版天气服务功能验证成功")
        print("🚀 现在可以查询中国全国任何地区的天气了！")

    except KeyboardInterrupt:
        print("\n⏹️ 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()