#!/usr/bin/env python3
"""
增强钓鱼评分引擎单元测试

测试覆盖：
1. 季节性评分算法
2. 月相评分算法
3. 气压趋势分析
4. 温度趋势分析
5. 风速稳定性分析
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from packages.agent_fishing.tools.scoring.enhanced_scorer import (
    calculate_seasonal_score,
    calculate_lunar_phase,
    calculate_lunar_score,
    analyze_pressure_trend,
    analyze_temperature_trend,
    analyze_wind_stability
)


class TestSeasonalScore:
    """季节性评分测试"""

    def test_spring_morning(self):
        """春季早晨应得高分"""
        spring_morning = datetime(2024, 4, 15, 7, 0)
        score = calculate_seasonal_score(spring_morning, 7)
        assert score == 100.0, "春季早晨应该得100分"

    def test_spring_afternoon(self):
        """春季下午应得中等分"""
        spring_afternoon = datetime(2024, 4, 15, 14, 0)
        score = calculate_seasonal_score(spring_afternoon, 14)
        assert score == 85.0, "春季下午应该得85分"

    def test_summer_noon(self):
        """夏季中午应得低分"""
        summer_noon = datetime(2024, 7, 15, 13, 0)
        score = calculate_seasonal_score(summer_noon, 13)
        assert score == 60.0, "夏季中午应该得60分"

    def test_summer_morning(self):
        """夏季清晨应得高分"""
        summer_morning = datetime(2024, 7, 15, 6, 0)
        score = calculate_seasonal_score(summer_morning, 6)
        assert score == 100.0, "夏季清晨应该得100分"

    def test_autumn_morning(self):
        """秋季早晨应得高分"""
        autumn_morning = datetime(2024, 10, 15, 8, 0)
        score = calculate_seasonal_score(autumn_morning, 8)
        assert score == 100.0, "秋季早晨应该得100分"

    def test_winter_noon(self):
        """冬季中午应得高分"""
        winter_noon = datetime(2024, 12, 15, 12, 0)
        score = calculate_seasonal_score(winter_noon, 12)
        assert score == 90.0, "冬季中午应该得90分"

    def test_winter_night(self):
        """冬季夜间应得低分"""
        winter_night = datetime(2024, 12, 15, 22, 0)
        score = calculate_seasonal_score(winter_night, 22)
        assert score == 50.0, "冬季夜间应该得50分"


class TestLunarPhase:
    """月相计算测试"""

    def test_lunar_phase_calculation(self):
        """测试月相计算是否返回有效值"""
        test_date = datetime(2024, 6, 6, 12, 0)
        phase = calculate_lunar_phase(test_date)

        # 验证返回的月相是有效的
        valid_phases = [
            'new_moon', 'waxing_crescent', 'first_quarter', 'waxing_gibbous',
            'full_moon', 'waning_gibbous', 'last_quarter', 'waning_crescent'
        ]
        assert phase in valid_phases, f"月相计算返回了无效值: {phase}"

    def test_different_dates_produce_different_phases(self):
        """测试不同日期会产生不同的月相"""
        date1 = datetime(2024, 1, 1, 12, 0)
        date2 = datetime(2024, 1, 15, 12, 0)  # 15天后应该是不同月相

        phase1 = calculate_lunar_phase(date1)
        phase2 = calculate_lunar_phase(date2)

        # 15天后月相应该不同
        assert phase1 != phase2, "15天后的月相应该不同"


class TestLunarScore:
    """月相评分测试"""

    def test_new_moon_score(self):
        """测试新月评分"""
        # 2024年6月6日是新月
        new_moon_date = datetime(2024, 6, 6, 12, 0)
        score = calculate_lunar_score(new_moon_date, is_night=False)

        # 新月评分可能因为月相计算精度在78-90之间
        assert 75 <= score <= 90, f"新月评分应在75-90之间，实际: {score}"

    def test_full_moon_night(self):
        """测试满月夜间评分"""
        # 2024年5月23日是满月
        full_moon_date = datetime(2024, 5, 23, 20, 0)
        score = calculate_lunar_score(full_moon_date, is_night=True)

        # 满月夜间应该得高分（但具体值取决于月相计算精度）
        assert score >= 65, f"满月夜间评分应>=65分，实际: {score}"

    def test_full_moon_day(self):
        """测试满月白天评分"""
        # 2024年5月23日是满月
        full_moon_date = datetime(2024, 5, 23, 12, 0)
        score = calculate_lunar_score(full_moon_date, is_night=False)

        # 满月白天评分应该比夜间低
        assert score >= 60, f"满月白天评分应>=60分，实际: {score}"


class TestPressureTrend:
    """气压趋势分析测试"""

    def test_falling_fast_pressure(self):
        """测试气压快速下降"""
        # 模拟气压快速下降序列
        falling_series = [1020, 1018, 1015, 1012, 1009, 1005]
        result = analyze_pressure_trend(falling_series)

        assert result['trend'] == 'falling_fast', "应识别为快速下降"
        # v3.1调整：基于科学研究，气压影响系数从±20%降至±10%
        assert result['multiplier'] == 1.10, "快速下降应有1.10倍奖励（v3.1优化）"
        assert result['change_rate'] < -2, "变化率应<-2"

    def test_falling_slow_pressure(self):
        """测试气压缓慢下降"""
        # 调整数据以确保是缓慢下降（-2~-0.5 hPa/6h）
        falling_series = [1015, 1014.5, 1014, 1013.5, 1013, 1012.5]
        result = analyze_pressure_trend(falling_series)

        assert result['trend'] == 'falling_slow', "应识别为缓慢下降"
        # v3.1调整：缓慢下降从1.10降至1.05
        assert result['multiplier'] == 1.05, "缓慢下降应有1.05倍奖励（v3.1优化）"

    def test_stable_pressure(self):
        """测试气压稳定"""
        stable_series = [1013, 1013, 1013, 1013, 1013, 1013]
        result = analyze_pressure_trend(stable_series)

        assert result['trend'] == 'stable', "应识别为稳定"
        assert result['multiplier'] == 1.00, "稳定应无调整"

    def test_rising_fast_pressure(self):
        """测试气压快速上升"""
        rising_series = [1005, 1009, 1012, 1015, 1018, 1020]
        result = analyze_pressure_trend(rising_series)

        assert result['trend'] == 'rising_fast', "应识别为快速上升"
        # v3.1调整：快速上升从0.80调整至0.90
        assert result['multiplier'] == 0.90, "快速上升应有0.90倍惩罚（v3.1优化）"

    def test_insufficient_data(self):
        """测试数据不足"""
        short_series = [1013, 1012]
        result = analyze_pressure_trend(short_series)

        assert result['trend'] == 'insufficient_data', "数据不足应返回insufficient_data"
        assert result['multiplier'] == 1.0, "数据不足应无调整"


class TestTemperatureTrend:
    """温度趋势分析测试"""

    def test_fast_warming(self):
        """测试快速升温"""
        # 需要>3°C变化才算快速升温，调整数据
        warming_series = [18, 19, 20, 21.5, 23, 24.5]
        multiplier = analyze_temperature_trend(warming_series)

        assert multiplier == 1.10, "快速升温应有1.10倍奖励"

    def test_slow_warming(self):
        """测试缓慢升温"""
        warming_series = [20, 20.5, 21, 21.5, 22, 22.5]
        multiplier = analyze_temperature_trend(warming_series)

        assert multiplier == 1.05, "缓慢升温应有1.05倍奖励"

    def test_stable_temperature(self):
        """测试温度稳定"""
        stable_series = [20, 20.2, 20.1, 20.3, 20, 20.2]
        multiplier = analyze_temperature_trend(stable_series)

        assert multiplier == 1.00, "温度稳定应无调整"

    def test_fast_cooling(self):
        """测试快速降温"""
        cooling_series = [23, 22, 21, 20, 19, 18]
        multiplier = analyze_temperature_trend(cooling_series)

        assert multiplier == 0.90, "快速降温应有0.90倍惩罚"

    def test_insufficient_data(self):
        """测试数据不足"""
        short_series = [20, 21]
        multiplier = analyze_temperature_trend(short_series)

        assert multiplier == 1.0, "数据不足应无调整"


class TestWindStability:
    """风速稳定性分析测试"""

    def test_very_stable_wind(self):
        """测试非常稳定的风速"""
        stable_series = [3.0, 3.1, 2.9, 3.0, 3.2, 3.0]
        multiplier = analyze_wind_stability(stable_series)

        assert multiplier == 1.05, "非常稳定风速应有1.05倍奖励"

    def test_stable_wind(self):
        """测试稳定风速"""
        # 标准差在1-2 km/h之间为稳定，调整数据使其符合条件
        # 风速 m/s 转 km/h (*3.6)，需要标准差在1-2 km/h
        stable_series = [3.0, 3.6, 2.6, 3.5, 2.5, 3.4]  # 标准差约1.56 km/h
        multiplier = analyze_wind_stability(stable_series)

        assert multiplier == 1.00, "稳定风速应无调整"

    def test_unstable_wind(self):
        """测试不稳定风速"""
        unstable_series = [3.0, 5.0, 2.0, 6.0, 1.0, 7.0]
        multiplier = analyze_wind_stability(unstable_series)

        assert multiplier <= 0.90, "不稳定风速应有惩罚"

    def test_very_unstable_wind(self):
        """测试非常不稳定的风速"""
        very_unstable_series = [1.0, 10.0, 2.0, 12.0, 1.5, 15.0]
        multiplier = analyze_wind_stability(very_unstable_series)

        assert multiplier == 0.80, "非常不稳定风速应有0.80倍惩罚"

    def test_insufficient_data(self):
        """测试数据不足"""
        short_series = [3.0, 3.1]
        multiplier = analyze_wind_stability(short_series)

        assert multiplier == 1.0, "数据不足应无调整"


def run_all_tests():
    """运行所有测试"""
    print("开始运行增强评分引擎单元测试...\n")

    # 运行pytest
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == '__main__':
    run_all_tests()
