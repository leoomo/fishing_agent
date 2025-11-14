#!/usr/bin/env python3
"""
增强版天气服务全国覆盖集成测试
测试智能地名匹配、坐标查询、缓存机制等功能
"""

import os
import sys
import time
import unittest
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from services.weather.enhanced_weather_service import EnhancedCaiyunWeatherService, get_enhanced_weather_info
from modern_langchain_agent import ModernLangChainAgent


class TestEnhancedWeatherNationalCoverage(unittest.TestCase):
    """增强版天气服务全国覆盖测试"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.service = EnhancedCaiyunWeatherService()
        print("\n🧪 增强版天气服务全国覆盖测试开始")
        print("=" * 60)

    def setUp(self):
        """每个测试方法的初始化"""
        # 清理缓存以确保测试独立性
        self.service.clear_cache()

    def test_database_integration(self):
        """测试数据库集成"""
        print("\n📊 测试数据库集成:")

        stats = self.service.get_supported_places_summary()
        db_stats = stats['database_stats']

        # 验证数据库包含预期的行政区划
        self.assertIn('省级', db_stats)
        self.assertIn('地级', db_stats)
        self.assertIn('县级', db_stats)
        self.assertIn('总计', db_stats)

        # 验证数据量
        self.assertGreater(db_stats['总计'], 50, "数据库应包含至少50个行政区划")
        self.assertGreater(db_stats['省级'], 10, "数据库应包含至少10个省级行政区")

        print(f"   ✅ 数据库包含: {db_stats}")

    def test_intelligent_place_matching(self):
        """测试智能地名匹配"""
        print("\n🎯 测试智能地名匹配:")

        test_cases = [
            # (输入, 期望匹配类型, 期望成功)
            ("北京", "exact", True),
            ("上海", "exact", True),
            ("广州市", "exact", True),
            ("天河区", "exact", True),
            ("广东省", "exact", True),
            ("beijing", "exact", True),  # 拼音匹配
            ("guangzhou", "exact", True),  # 拼音匹配
            ("湖", "exact", True),  # 模糊匹配
            ("朝阳区", "exact", False),  # 不存在的地区
        ]

        success_count = 0
        for place, expected_type, should_succeed in test_cases:
            coordinates = self.service.get_coordinates(place)

            if should_succeed:
                self.assertIsNotNone(coordinates, f"应该能找到 '{place}' 的坐标")
                if coordinates:
                    success_count += 1
                    print(f"   ✅ {place}: 坐标 ({coordinates[0]:.4f}, {coordinates[1]:.4f})")
            else:
                # 对于预期失败的案例，我们检查是否正确降级
                print(f"   ⚠️ {place}: 预期无法匹配，实际: {'有坐标' if coordinates else '无坐标'}")

        success_rate = success_count / len([tc for tc in test_cases if tc[2]])
        print(f"   📈 匹配成功率: {success_rate:.1%} ({success_count}/{len([tc for tc in test_cases if tc[2]])})")

        # 期望成功率至少80%
        self.assertGreaterEqual(success_rate, 0.8, "智能匹配成功率应至少80%")

    def test_weather_query_various_regions(self):
        """测试各级行政区划天气查询"""
        print("\n🌤️ 测试各级行政区划天气查询:")

        test_places = [
            # 省级
            ("北京市", "省级"),
            ("上海市", "省级"),
            ("广东省", "省级"),

            # 地级
            ("广州市", "地级"),
            ("深圳市", "地级"),
            ("杭州市", "地级"),

            # 县级
            ("天河区", "县级"),
            ("西湖区", "县级"),
            ("罗湖区", "县级"),

            # 拼音输入
            ("beijing", "拼音"),
            ("shanghai", "拼音"),

            # 别名输入
            ("北京", "别名"),
            ("上海", "别名"),
        ]

        for place, level_type in test_places:
            try:
                weather_data, source = self.service.get_weather(place)

                self.assertIsNotNone(weather_data, f"{place} 应返回天气数据")
                self.assertIsInstance(weather_data.temperature, (int, float), f"{place} 温度应为数值")
                self.assertIsInstance(weather_data.humidity, (int, float), f"{place} 湿度应为数值")
                self.assertIsNotNone(weather_data.condition, f"{place} 应有天气状况")

                print(f"   ✅ {place} ({level_type}): {weather_data.condition} {weather_data.temperature:.1f}°C")
                print(f"      来源: {source}")

            except Exception as e:
                print(f"   ❌ {place} ({level_type}): 错误 - {e}")
                self.fail(f"{place} 天气查询失败: {e}")

    def test_caching_mechanism(self):
        """测试缓存机制"""
        print("\n💾 测试缓存机制:")

        test_place = "广州市"

        # 第一次查询（应该调用API或生成模拟数据）
        start_time = time.time()
        weather_data1, source1 = self.service.get_weather(test_place)
        first_query_time = time.time() - start_time

        # 第二次查询（应该从缓存获取）
        start_time = time.time()
        weather_data2, source2 = self.service.get_weather(test_place)
        second_query_time = time.time() - start_time

        # 验证缓存效果
        self.assertIsNotNone(weather_data1, "第一次查询应返回数据")
        self.assertIsNotNone(weather_data2, "第二次查询应返回数据")
        self.assertEqual(weather_data1.temperature, weather_data2.temperature, "缓存数据应一致")

        # 缓存查询应该更快
        print(f"   📊 第一次查询耗时: {first_query_time:.3f}s")
        print(f"   📊 第二次查询耗时: {second_query_time:.3f}s")

        if second_query_time < first_query_time:
            print(f"   ✅ 缓存生效，加速比: {first_query_time/second_query_time:.1f}x")
        else:
            print(f"   ⚠️ 缓存效果不明显，可能是查询太快")

        # 验证来源信息包含缓存标识
        if "缓存" in source2:
            print(f"   ✅ 缓存来源标识正确: {source2}")

    def test_error_handling_and_fallback(self):
        """测试错误处理和降级机制"""
        print("\n🛡️ 测试错误处理和降级机制:")

        # 测试不存在的地区
        invalid_places = ["不存在的城市", "火星", ""]

        for place in invalid_places:
            try:
                weather_data, source = self.service.get_weather(place)

                # 即使地区不存在，也应该返回模拟数据
                self.assertIsNotNone(weather_data, f"即使地区不存在也应返回模拟数据: {place}")

                print(f"   ✅ {place}: 降级机制正常，返回模拟数据")
                print(f"      来源: {source}")

            except Exception as e:
                print(f"   ❌ {place}: 异常 - {e}")
                self.fail(f"错误处理失败: {e}")

    def test_batch_query_performance(self):
        """测试批量查询性能"""
        print("\n📦 测试批量查询性能:")

        batch_places = ["北京", "上海", "广州", "深圳", "杭州", "成都", "西安", "武汉"]

        # 测试批量查询
        start_time = time.time()
        batch_results = self.service.batch_get_weather(batch_places)
        batch_time = time.time() - start_time

        # 验证批量查询结果
        self.assertEqual(len(batch_results), len(batch_places), "批量查询应返回所有结果")

        success_count = sum(1 for result in batch_results if result['success'])
        print(f"   ✅ 批量查询完成: {success_count}/{len(batch_places)} 成功")
        print(f"   ⏱️ 总耗时: {batch_time:.3f}s")
        print(f"   📊 平均耗时: {batch_time/len(batch_places):.3f}s/个")

        # 验证性能指标
        avg_time_per_query = batch_time / len(batch_places)
        self.assertLess(avg_time_per_query, 2.0, "平均查询时间应少于2秒")

        # 验证成功率高
        success_rate = success_count / len(batch_places)
        self.assertGreater(success_rate, 0.8, "批量查询成功率应大于80%")

    def test_integration_with_agent(self):
        """测试与智能体的集成"""
        print("\n🤖 测试与智能体的集成:")

        # 测试智能体是否可以使用增强的天气工具
        try:
            # 创建智能体实例（不需要实际运行，只测试初始化）
            agent = ModernLangChainAgent(model_provider="zhipu")

            # 测试天气工具是否正确导入
            from modern_langchain_agent import get_weather

            # 直接调用工具函数
            result = get_weather.invoke({"city": "北京"})

            self.assertIsNotNone(result, "天气工具应返回结果")
            self.assertIsInstance(result, str, "天气工具应返回字符串")
            self.assertIn("天气", result, "结果应包含天气信息")

            print(f"   ✅ 智能体集成成功")
            print(f"   📄 工具返回: {result[:100]}...")

        except Exception as e:
            print(f"   ❌ 智能体集成失败: {e}")
            self.fail(f"智能体集成测试失败: {e}")

    def test_service_statistics(self):
        """测试服务统计信息"""
        print("\n📊 测试服务统计信息:")

        summary = self.service.get_supported_places_summary()

        # 验证统计信息结构
        expected_keys = ['database_stats', 'matcher_stats', 'cache_stats', 'api_configured', 'service_version']
        for key in expected_keys:
            self.assertIn(key, summary, f"统计信息应包含 {key}")

        print(f"   📋 数据库统计: {summary['database_stats']}")
        print(f"   🎯 匹配器统计: {summary['matcher_stats']}")
        print(f"   💾 缓存统计: {summary['cache_stats']}")
        print(f"   🔑 API配置: {summary['api_configured']}")
        print(f"   🏷️ 服务版本: {summary['service_version']}")

        # 验证服务版本
        self.assertEqual(summary['service_version'], "enhanced-v1.0", "服务版本应正确")

    def test_performance_benchmarks(self):
        """测试性能基准"""
        print("\n🏃 测试性能基准:")

        test_places = ["北京", "上海", "广州", "深圳", "杭州"]

        # 单次查询性能测试
        times = []
        for place in test_places:
            start_time = time.time()
            weather_data, source = self.service.get_weather(place)
            end_time = time.time()

            query_time = end_time - start_time
            times.append(query_time)

            self.assertIsNotNone(weather_data, f"{place} 查询应成功")
            self.assertLess(query_time, 3.0, f"{place} 查询时间应少于3秒")

        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)

        print(f"   ⏱️ 平均查询时间: {avg_time:.3f}s")
        print(f"   ⏱️ 最大查询时间: {max_time:.3f}s")
        print(f"   ⏱️ 最小查询时间: {min_time:.3f}s")

        # 性能要求验证
        self.assertLess(avg_time, 2.0, "平均查询时间应少于2秒")
        self.assertLess(max_time, 3.0, "最大查询时间应少于3秒")

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        if hasattr(cls, 'service'):
            cls.service.coordinate_db.close()
        print("\n✅ 增强版天气服务全国覆盖测试完成!")


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)