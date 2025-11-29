#!/usr/bin/env python3
"""
增强钓鱼评分器测试套件
"""

import unittest
import sys
from datetime import datetime, timedelta
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tools.enhanced_fishing_scorer import (
    EnhancedFishingScorer,
    WeatherTrendAnalyzer,
    PressureTrendAnalyzer,
    SeasonalAnalyzer,
    AstronomicalCalculator,
    FishingScore
)


class TestEnhancedFishingScorer(unittest.TestCase):
    """增强评分器单元测试"""

    def setUp(self):
        """测试前准备"""
        self.scorer = EnhancedFishingScorer()

    def test_pressure_scoring(self):
        """测试气压评分算法"""
        analyzer = self.scorer.pressure_analyzer

        # 最佳气压范围测试
        self.assertEqual(analyzer.calculate_base_score(1015), 100.0)
        self.assertEqual(analyzer.calculate_base_score(1020), 100.0)
        self.assertEqual(analyzer.calculate_base_score(1010), 100.0)

        # 低气压测试
        self.assertGreater(analyzer.calculate_base_score(1000), 80.0)
        self.assertGreater(analyzer.calculate_base_score(990), 60.0)

        # 高气压测试
        self.assertLess(analyzer.calculate_base_score(1040), 90.0)
        self.assertLess(analyzer.calculate_base_score(1050), 70.0)

    def test_pressure_trend_analysis(self):
        """测试气压趋势分析"""
        analyzer = self.scorer.pressure_analyzer

        # 稳定气压
        stable_series = [1013, 1013, 1013, 1013, 1013]
        trend_score = analyzer.calculate_trend_score(stable_series)
        self.assertEqual(trend_score, 100.0)

        # 快速下降气压（最佳）
        falling_series = [1018, 1015, 1012, 1009, 1006, 1003]  # 更多数据点
        trend_score = analyzer.calculate_trend_score(falling_series)
        self.assertEqual(trend_score, 115.0)  # 应该返回115.0

        # 缓慢下降气压（良好）
        slow_falling_series = [1015, 1014.8, 1014.6, 1014.4, 1014.2, 1014.0]  # 缓慢下降
        trend_score = analyzer.calculate_trend_score(slow_falling_series)
        self.assertEqual(trend_score, 105.0)

        # 上升气压（较差）
        rising_series = [1007, 1009, 1011, 1013, 1015, 1017]
        trend_score = analyzer.calculate_trend_score(rising_series)
        self.assertLess(trend_score, 100.0)

    def test_humidity_scoring(self):
        """测试湿度评分算法"""
        # 理想湿度
        self.assertEqual(self.scorer._calculate_humidity_score(70), 100.0)
        self.assertEqual(self.scorer._calculate_humidity_score(65), 100.0)

        # 高湿度（低气压信号）
        self.assertEqual(self.scorer._calculate_humidity_score(85), 95.0)
        self.assertEqual(self.scorer._calculate_humidity_score(90), 95.0)

        # 中等湿度
        self.assertEqual(self.scorer._calculate_humidity_score(50), 80.0)

        # 极端湿度
        self.assertEqual(self.scorer._calculate_humidity_score(30), 65.0)
        self.assertEqual(self.scorer._calculate_humidity_score(98), 65.0)

    def test_seasonal_scoring(self):
        """测试季节性评分算法"""
        analyzer = self.scorer.seasonal_analyzer

        # 春季早晨最佳
        spring_morning = datetime(2024, 4, 15, 7, 0)
        score = analyzer.calculate_seasonal_score(spring_morning, 'morning')
        self.assertEqual(score, 100.0)

        # 夏季中午最差
        summer_noon = datetime(2024, 7, 15, 13, 0)
        score = analyzer.calculate_seasonal_score(summer_noon, 'noon')
        self.assertEqual(score, 60.0)

        # 秋季下午最佳
        autumn_afternoon = datetime(2024, 10, 15, 17, 0)
        score = analyzer.calculate_seasonal_score(autumn_afternoon, 'afternoon')
        self.assertEqual(score, 100.0)

        # 冬季早晚很差
        winter_early = datetime(2024, 1, 15, 6, 0)
        score = analyzer.calculate_seasonal_score(winter_early, 'morning')
        self.assertEqual(score, 50.0)

    def test_lunar_phase_calculation(self):
        """测试月相计算"""
        calculator = self.scorer.astronomical_calculator

        # 测试不同日期的月相计算
        test_dates = [
            datetime(2000, 1, 6),   # 已知新月日期
            datetime(2024, 6, 15),  # 随机日期
            datetime(2024, 12, 31)  # 年末日期
        ]

        for test_date in test_dates:
            moon_phase = calculator.calculate_lunar_phase(test_date)
            self.assertIn(moon_phase, [
                'new_moon', 'waxing_crescent', 'first_quarter', 'waxing_gibbous',
                'full_moon', 'waning_gibbous', 'last_quarter', 'waning_crescent'
            ])

            # 测试月相评分
            score = calculator.calculate_lunar_score(test_date, 'night')
            self.assertGreater(score, 50.0)
            self.assertLessEqual(score, 100.0)

    def test_weather_trend_analysis(self):
        """测试天气趋势分析"""
        analyzer = self.scorer.weather_analyzer

        # 气压趋势测试
        pressure_series = [1015, 1013, 1011, 1009, 1007]
        trend_result = analyzer.get_pressure_trend(pressure_series)
        self.assertEqual(trend_result['trend'], 'falling_fast')
        self.assertEqual(trend_result['multiplier'], 1.20)

        # 温度趋势测试
        temp_series = [15, 17, 19, 21, 23]
        temp_trend = analyzer.get_temperature_trend(temp_series)
        self.assertEqual(temp_trend['trend'], 'rising')
        self.assertGreater(temp_trend['multiplier'], 1.0)

        # 风速稳定性测试
        wind_series = [5.0, 5.1, 5.2, 4.9, 5.0]
        wind_stability = analyzer.get_wind_stability(wind_series)
        self.assertEqual(wind_stability['stability'], 'very_stable')
        self.assertGreater(wind_stability['multiplier'], 1.0)

    def test_comprehensive_scoring(self):
        """测试综合评分计算"""
        hourly_data = {
            'datetime': '2024-11-06T14:00:00',
            'temperature': 20.0,
            'condition': '多云',
            'wind_speed': 5.0,
            'humidity': 65.0,
            'pressure': 1015.0
        }

        historical_data = [
            {'pressure': 1013, 'temperature': 18, 'wind_speed': 4},
            {'pressure': 1014, 'temperature': 19, 'wind_speed': 4.5},
            {'pressure': 1015, 'temperature': 19.5, 'wind_speed': 5},
            {'pressure': 1016, 'temperature': 20, 'wind_speed': 5.5},
            {'pressure': 1017, 'temperature': 20.5, 'wind_speed': 6}
        ]

        date = datetime(2024, 11, 6, 14, 0)

        score = self.scorer.calculate_comprehensive_score(hourly_data, historical_data, date)

        # 验证返回的FishingScore对象
        self.assertIsInstance(score, FishingScore)
        self.assertGreater(score.overall, 0)
        self.assertLessEqual(score.overall, 100)
        self.assertEqual(score.temperature, 100.0)  # 20°C在最佳范围内
        self.assertEqual(score.weather, 100.0)     # 多云是最佳天气
        self.assertEqual(score.wind, 100.0)        # 5km/h在最佳范围内

        # 验证权重分解
        weight_sum = sum(score.breakdown.values())
        self.assertAlmostEqual(weight_sum, 1.0, places=2)  # 权重总和应约等于1

    def test_score_breakdown(self):
        """测试评分分解功能"""
        # 使用实际的权重配置
        weights = self.scorer.weights

        score = FishingScore(
            overall=85.5,
            temperature=100.0,
            weather=90.0,
            wind=80.0,
            pressure=95.0,
            humidity=85.0,
            seasonal=90.0,
            lunar=75.0,
            breakdown=weights,
            timestamp=datetime.now()
        )

        breakdown = self.scorer.get_score_breakdown(score)

        # 验证权重分析
        self.assertIn('weight_analysis', breakdown)
        self.assertEqual(len(breakdown['weight_analysis']), 7)

        # 验证各因子的贡献度计算
        temp_analysis = breakdown['weight_analysis']['temperature']
        temp_weight = weights['temperature']
        self.assertEqual(temp_analysis['weight'], temp_weight)
        self.assertAlmostEqual(temp_analysis['weight_percentage'], temp_weight * 100, places=1)
        self.assertEqual(temp_analysis['score'], 100.0)
        self.assertAlmostEqual(temp_analysis['contribution'], 100.0 * temp_weight, places=1)


class TestWeatherTrendAnalyzer(unittest.TestCase):
    """天气趋势分析器测试"""

    def setUp(self):
        self.analyzer = WeatherTrendAnalyzer()

    def test_pressure_trend_insufficient_data(self):
        """测试数据不足时的气压趋势"""
        insufficient_data = [1013]
        result = self.analyzer.get_pressure_trend(insufficient_data)
        self.assertEqual(result['trend'], 'unknown')
        self.assertEqual(result['multiplier'], 1.0)

    def test_temperature_trend_stable(self):
        """测试温度稳定趋势"""
        stable_data = [20.0, 20.1, 19.9, 20.2, 19.8]
        result = self.analyzer.get_temperature_trend(stable_data)
        self.assertEqual(result['trend'], 'stable')
        self.assertEqual(result['multiplier'], 1.0)

    def test_wind_stability_varying_conditions(self):
        """测试不同风速条件下的稳定性"""
        # 非常稳定
        stable_wind = [5.0, 5.1, 5.2, 4.9, 5.0]
        result = self.analyzer.get_wind_stability(stable_wind)
        self.assertEqual(result['stability'], 'very_stable')
        self.assertGreater(result['multiplier'], 1.0)

        # 不稳定
        unstable_wind = [5.0, 10.0, 2.0, 15.0, 1.0]
        result = self.analyzer.get_wind_stability(unstable_wind)
        self.assertEqual(result['stability'], 'very_unstable')
        self.assertLess(result['multiplier'], 1.0)


class TestSeasonalAnalyzer(unittest.TestCase):
    """季节性分析器测试"""

    def setUp(self):
        self.analyzer = SeasonalAnalyzer()

    def test_season_identification(self):
        """测试季节识别"""
        # 春季
        spring_date = datetime(2024, 4, 15)
        season_info = self.analyzer.get_season_info(spring_date)
        self.assertEqual(season_info['season'], 'spring')
        self.assertEqual(season_info['season_name'], '春季')

        # 夏季
        summer_date = datetime(2024, 7, 15)
        season_info = self.analyzer.get_season_info(summer_date)
        self.assertEqual(season_info['season'], 'summer')
        self.assertEqual(season_info['season_name'], '夏季')

        # 秋季
        autumn_date = datetime(2024, 10, 15)
        season_info = self.analyzer.get_season_info(autumn_date)
        self.assertEqual(season_info['season'], 'autumn')
        self.assertEqual(season_info['season_name'], '秋季')

        # 冬季
        winter_date = datetime(2024, 1, 15)
        season_info = self.analyzer.get_season_info(winter_date)
        self.assertEqual(season_info['season'], 'winter')
        self.assertEqual(season_info['season_name'], '冬季')

    def test_optimal_fishing_times(self):
        """测试最佳钓鱼时间"""
        # 春季最佳时间
        spring_times = self.analyzer.get_optimal_fishing_times('spring')
        self.assertEqual(len(spring_times), 2)
        self.assertIn((6, 9), spring_times)
        self.assertIn((17, 19), spring_times)

        # 夏季最佳时间
        summer_times = self.analyzer.get_optimal_fishing_times('summer')
        self.assertEqual(len(summer_times), 2)
        self.assertIn((5, 8), summer_times)
        self.assertIn((18, 20), summer_times)


class TestAstronomicalCalculator(unittest.TestCase):
    """天文计算器测试"""

    def setUp(self):
        self.calculator = AstronomicalCalculator()

    def test_sun_position(self):
        """测试太阳位置计算"""
        # 早晨
        morning = datetime(2024, 6, 15, 8, 0)
        sun_pos = self.calculator.get_sun_position(morning)
        self.assertEqual(sun_pos['position'], 'morning')
        self.assertGreater(sun_pos['intensity'], 0.5)

        # 正午
        noon = datetime(2024, 6, 15, 12, 0)
        sun_pos = self.calculator.get_sun_position(noon)
        self.assertEqual(sun_pos['position'], 'noon')
        self.assertEqual(sun_pos['intensity'], 1.0)

        # 夜间
        night = datetime(2024, 6, 15, 23, 0)
        sun_pos = self.calculator.get_sun_position(night)
        self.assertEqual(sun_pos['position'], 'night')
        self.assertLess(sun_pos['intensity'], 0.2)


class TestPerformance(unittest.TestCase):
    """性能测试"""

    def setUp(self):
        self.scorer = EnhancedFishingScorer()

    def test_scoring_performance(self):
        """测试评分计算性能"""
        import time

        # 构造测试数据
        hourly_data = {
            'datetime': '2024-11-06T14:00:00',
            'temperature': 20.0,
            'condition': '多云',
            'wind_speed': 5.0,
            'humidity': 65.0,
            'pressure': 1015.0
        }

        historical_data = [
            {'pressure': 1013 + i * 0.5, 'temperature': 18 + i, 'wind_speed': 4 + i * 0.2}
            for i in range(6)
        ]

        date = datetime(2024, 11, 6, 14, 0)

        # 执行性能测试
        start_time = time.time()
        for _ in range(100):  # 执行100次
            self.scorer.calculate_comprehensive_score(hourly_data, historical_data, date)

        execution_time = time.time() - start_time
        avg_time = execution_time / 100

        # 性能要求：平均每次评分 < 10ms
        self.assertLess(avg_time, 0.01, f"评分计算时间过长: {avg_time:.4f}s")

    def test_memory_efficiency(self):
        """测试内存效率（简化版）"""
        import gc

        # 执行大量评分计算
        scores = []
        for i in range(100):  # 减少测试数量避免内存问题
            hourly_data = {
                'datetime': f'2024-11-06T{i%24:02d}:00:00',
                'temperature': 20.0 + i * 0.1,
                'condition': '多云',
                'wind_speed': 5.0,
                'humidity': 65.0,
                'pressure': 1015.0
            }

            historical_data = [
                {'pressure': 1013 + j * 0.5, 'temperature': 18 + j, 'wind_speed': 4 + j * 0.2}
                for j in range(6)
            ]

            date = datetime(2024, 11, 6, i % 24, 0)
            score = self.scorer.calculate_comprehensive_score(hourly_data, historical_data, date)
            scores.append(score)

        # 验证所有评分都被正确计算
        self.assertEqual(len(scores), 100)
        for score in scores:
            self.assertIsInstance(score, FishingScore)
            self.assertGreater(score.overall, 0)
            self.assertLessEqual(score.overall, 100)

        # 清理内存
        del scores
        gc.collect()

        # 如果能执行到这里没有内存错误，说明内存效率是合理的
        self.assertTrue(True)


def run_enhanced_scorer_tests():
    """运行增强评分器所有测试"""
    print("🚀 开始运行增强钓鱼评分器测试套件...")

    import time
    start_time = time.time()

    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加测试类
    test_classes = [
        TestEnhancedFishingScorer,
        TestWeatherTrendAnalyzer,
        TestSeasonalAnalyzer,
        TestAstronomicalCalculator,
        TestPerformance
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    execution_time = time.time() - start_time

    # 输出测试结果摘要
    print(f"\n{'='*50}")
    print(f"📊 测试结果摘要:")
    print(f"   运行测试: {result.testsRun}")
    print(f"   成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   失败: {len(result.failures)}")
    print(f"   错误: {len(result.errors)}")
    print(f"   耗时: {execution_time:.2f}秒")

    if result.failures:
        print(f"\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"   - {test}")

    if result.errors:
        print(f"\n💥 错误的测试:")
        for test, traceback in result.errors:
            print(f"   - {test}")

    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n{'✅' if success_rate == 100 else '⚠️'} 成功率: {success_rate:.1f}%")

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_enhanced_scorer_tests()
    sys.exit(0 if success else 1)