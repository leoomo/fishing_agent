#!/usr/bin/env python3
"""
增强钓鱼评分器
基于专业钓鱼研究和气象数据分析，实施精细评分系统
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import math
import statistics
import logging


@dataclass
class FishingScore:
    """钓鱼评分结果"""
    overall: float                           # 综合评分
    temperature: float                       # 温度评分
    weather: float                          # 天气评分
    wind: float                             # 风力评分
    pressure: float                         # 气压评分
    humidity: float                         # 湿度评分
    seasonal: float                         # 季节性评分
    lunar: float                            # 月相评分
    breakdown: Dict[str, float]              # 权重分解
    timestamp: datetime                      # 计算时间戳
    analysis_details: Optional[Dict[str, Any]] = None  # 分析详情

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'overall_score': self.overall,
            'component_scores': {
                'temperature': self.temperature,
                'weather': self.weather,
                'wind': self.wind,
                'pressure': self.pressure,
                'humidity': self.humidity,
                'seasonal': self.seasonal,
                'lunar': self.lunar
            },
            'weights': self.breakdown,
            'timestamp': self.timestamp.isoformat(),
            'analysis_details': self.analysis_details or {}
        }


class WeatherTrendAnalyzer:
    """天气趋势分析器"""

    def __init__(self, window_size: int = 6):
        self.window_size = window_size
        self._logger = logging.getLogger(__name__)

    def get_pressure_trend(self, pressure_series: List[float]) -> Dict[str, Any]:
        """
        分析气压趋势

        Args:
            pressure_series: 气压时间序列

        Returns:
            趋势分析结果
        """
        if len(pressure_series) < 3:
            return {
                'trend': 'unknown',
                'change_rate': 0.0,
                'multiplier': 1.0,
                'stability': 'unknown'
            }

        try:
            # 计算变化率
            if len(pressure_series) >= self.window_size:
                recent_avg = statistics.mean(pressure_series[-3:])
                earlier_avg = statistics.mean(pressure_series[-self.window_size:-3])
            else:
                recent_avg = statistics.mean(pressure_series[-2:])
                earlier_avg = statistics.mean(pressure_series[:-2])

            change = recent_avg - earlier_avg

            # 确定趋势
            if change < -2:
                trend = 'falling_fast'
                multiplier = 1.20
            elif change < -0.5:
                trend = 'falling_slow'
                multiplier = 1.10
            elif -0.5 <= change <= 0.5:
                trend = 'stable'
                multiplier = 1.00
            elif change <= 2:
                trend = 'rising_slow'
                multiplier = 0.90
            else:
                trend = 'rising_fast'
                multiplier = 0.80

            # 计算稳定性
            if len(pressure_series) >= 3:
                std_dev = statistics.stdev(pressure_series[-min(6, len(pressure_series)):])
                stability = 'stable' if std_dev < 2 else 'unstable'
            else:
                stability = 'unknown'

            return {
                'trend': trend,
                'change_rate': change,
                'multiplier': multiplier,
                'stability': stability
            }

        except Exception as e:
            self._logger.warning(f"气压趋势分析失败: {e}")
            return {
                'trend': 'unknown',
                'change_rate': 0.0,
                'multiplier': 1.0,
                'stability': 'unknown'
            }

    def get_temperature_trend(self, temp_series: List[float]) -> Dict[str, Any]:
        """
        分析温度趋势

        Args:
            temp_series: 温度时间序列

        Returns:
            趋势分析结果
        """
        if len(temp_series) < 3:
            return {
                'trend': 'unknown',
                'change_rate': 0.0,
                'multiplier': 1.0
            }

        try:
            if len(temp_series) >= self.window_size:
                recent_avg = statistics.mean(temp_series[-3:])
                earlier_avg = statistics.mean(temp_series[-self.window_size:-3])
            else:
                recent_avg = statistics.mean(temp_series[-2:])
                earlier_avg = statistics.mean(temp_series[:-2])

            change = recent_avg - earlier_avg

            # 温度变化的奖励系数
            if change > 3:
                multiplier = 1.10
            elif change > 1:
                multiplier = 1.05
            elif -1 <= change <= 1:
                multiplier = 1.00
            elif change < -3:
                multiplier = 0.95
            else:
                multiplier = 0.98

            trend = 'rising' if change > 0.5 else 'falling' if change < -0.5 else 'stable'

            return {
                'trend': trend,
                'change_rate': change,
                'multiplier': multiplier
            }

        except Exception as e:
            self._logger.warning(f"温度趋势分析失败: {e}")
            return {
                'trend': 'unknown',
                'change_rate': 0.0,
                'multiplier': 1.0
            }

    def get_wind_stability(self, wind_series: List[float]) -> Dict[str, Any]:
        """
        分析风速稳定性

        Args:
            wind_series: 风速时间序列

        Returns:
            稳定性分析结果
        """
        if len(wind_series) < 3:
            return {
                'stability': 'unknown',
                'std_dev': 0.0,
                'multiplier': 1.0
            }

        try:
            # 计算风速标准差
            mean_wind = statistics.mean(wind_series[-min(6, len(wind_series)):])
            variance = statistics.mean([(w - mean_wind) ** 2 for w in wind_series[-min(6, len(wind_series)):]])
            std_dev = math.sqrt(variance)

            # 稳定性评分
            if std_dev < 1:
                multiplier = 1.05
                stability = 'very_stable'
            elif std_dev < 2:
                multiplier = 1.00
                stability = 'stable'
            elif std_dev < 4:
                multiplier = 0.95
                stability = 'unstable'
            else:
                multiplier = 0.90
                stability = 'very_unstable'

            return {
                'stability': stability,
                'std_dev': std_dev,
                'multiplier': multiplier
            }

        except Exception as e:
            self._logger.warning(f"风速稳定性分析失败: {e}")
            return {
                'stability': 'unknown',
                'std_dev': 0.0,
                'multiplier': 1.0
            }


class PressureTrendAnalyzer:
    """气压趋势分析器"""

    OPTIMAL_RANGE = (1005, 1029)  # 最佳气压范围 hPa

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def calculate_base_score(self, pressure: float) -> float:
        """
        计算基础气压评分

        Args:
            pressure: 气压值 (hPa)

        Returns:
            基础评分 (0-100)
        """
        min_optimal, max_optimal = self.OPTIMAL_RANGE

        if min_optimal <= pressure <= max_optimal:
            return 100.0
        elif pressure < min_optimal:
            if pressure < 980:
                return 60.0
            else:
                ratio = (pressure - 980) / (min_optimal - 980)
                return 60.0 + ratio * 40.0
        else:  # pressure > max_optimal
            if pressure > 1050:
                return 50.0
            else:
                ratio = (1050 - pressure) / (1050 - max_optimal)
                return 50.0 + ratio * 50.0

    def calculate_trend_score(self, pressure_series: List[float]) -> float:
        """
        计算气压趋势评分

        Args:
            pressure_series: 气压时间序列

        Returns:
            趋势评分 (0-115, 支持额外奖励)
        """
        if len(pressure_series) < 3:
            return 75.0

        try:
            # 计算变化趋势
            recent_avg = statistics.mean(pressure_series[-3:])
            earlier_avg = statistics.mean(pressure_series[-6:-3]) if len(pressure_series) >= 6 else recent_avg

            change = recent_avg - earlier_avg

            if change < -2:      # 快速下降 - 最佳时机
                return 115.0     # 额外奖励
            elif change < -0.5:  # 缓慢下降 - 良好
                return 105.0
            elif -0.5 <= change <= 0.5:  # 稳定 - 正常
                return 100.0
            elif change <= 2:    # 缓慢上升 - 稍差
                return 85.0
            else:                # 快速上升 - 较差
                return 70.0

        except Exception as e:
            self._logger.warning(f"气压趋势评分计算失败: {e}")
            return 75.0

    def analyze_pressure_pattern(self, pressure_series: List[float]) -> float:
        """
        分析气压模式

        Args:
            pressure_series: 气压时间序列

        Returns:
            模式调整系数 (0.9-1.1)
        """
        if len(pressure_series) < 4:
            return 1.0

        try:
            # 计算气压的周期性变化
            changes = [pressure_series[i] - pressure_series[i-1] for i in range(1, len(pressure_series))]

            # 检查是否有连续的下降趋势
            consecutive_decrease = 0
            for change in changes[-4:]:
                if change < 0:
                    consecutive_decrease += 1
                else:
                    break

            if consecutive_decrease >= 3:
                return 1.1  # 连续下降，有利钓鱼
            elif consecutive_decrease >= 2:
                return 1.05
            else:
                return 1.0

        except Exception as e:
            self._logger.warning(f"气压模式分析失败: {e}")
            return 1.0

    def calculate_comprehensive_score(self, current_pressure: float, pressure_series: List[float]) -> float:
        """
        综合气压评分计算

        Args:
            current_pressure: 当前气压值
            pressure_series: 气压时间序列

        Returns:
            综合评分 (0-115)
        """
        # 基础评分 (0-100)
        base_score = self.calculate_base_score(current_pressure)

        # 趋势评分 (0-115, 支持额外奖励)
        trend_score = self.calculate_trend_score(pressure_series)

        # 模式分析 (0.9-1.1 调整系数)
        pattern_multiplier = self.analyze_pressure_pattern(pressure_series)

        # 综合评分
        comprehensive_score = base_score * 0.7 + trend_score * 0.3
        comprehensive_score *= pattern_multiplier

        return min(115, max(0, comprehensive_score))


class AstronomicalCalculator:
    """天文计算器"""

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def calculate_lunar_phase(self, date: datetime) -> str:
        """
        计算月相

        Args:
            date: 目标日期

        Returns:
            月相标识符
        """
        try:
            # 简化月相计算算法
            year, month, day = date.year, date.month, date.day

            # 转换为简化儒略日
            if month <= 2:
                year -= 1
                month += 12

            A = math.floor(year / 100)
            B = 2 - A + math.floor(A / 4)

            jd = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + B - 1524.5

            # 月相计算 (已知新月参考点: 2000-01-06 18:14 UTC)
            new_moon_ref = 2451550.958

            lunar_cycle = 29.53058867  # 朔望月周期 (天)

            days_since_new = (jd - new_moon_ref) % lunar_cycle
            phase_fraction = days_since_new / lunar_cycle

            # 确定月相
            phase_index = int(phase_fraction * 8)
            moon_phases = [
                'new_moon', 'waxing_crescent', 'first_quarter', 'waxing_gibbous',
                'full_moon', 'waning_gibbous', 'last_quarter', 'waning_crescent'
            ]

            return moon_phases[phase_index]

        except Exception as e:
            self._logger.warning(f"月相计算失败: {e}")
            return 'unknown'

    def calculate_lunar_score(self, date: datetime, time_of_day: str) -> float:
        """
        计算月相对钓鱼的影响评分

        Args:
            date: 目标日期
            time_of_day: 时间段描述

        Returns:
            月相评分 (0-100)
        """
        moon_phase = self.calculate_lunar_phase(date)

        # 转换时间描述
        is_night = time_of_day in ['dawn', 'dusk', 'night', '深夜', '傍晚', '晚上']

        # 月相基础评分
        phase_scores = {
            'new_moon': 85,           # 新月：温和天气
            'waxing_crescent': 80,    # 娥眉月：渐佳
            'first_quarter': 75,      # 上弦月：中等
            'waxing_gibbous': 82,     # 盈凸月：较好
            'full_moon': 65,          # 满月：白天一般
            'waning_gibbous': 78,     # 亏凸月：中等
            'last_quarter': 75,       # 下弦月：中等
            'waning_crescent': 80,    # 残月：渐佳
            'unknown': 75             # 未知
        }

        base_score = phase_scores.get(moon_phase, 75)

        # 满月夜间调整
        if moon_phase == 'full_moon' and is_night:
            base_score = 90  # 满月夜间加分

        # 新月调整（通常伴随好天气）
        if moon_phase == 'new_moon':
            base_score = max(base_score, 85)

        return base_score

    def get_sun_position(self, date: datetime) -> Dict[str, Any]:
        """
        计算太阳位置

        Args:
            date: 目标日期时间

        Returns:
            太阳位置信息
        """
        try:
            hour = date.hour

            if 5 <= hour < 7:
                return {'position': 'dawn', 'intensity': 0.3}
            elif 7 <= hour < 11:
                return {'position': 'morning', 'intensity': 0.7}
            elif 11 <= hour < 13:
                return {'position': 'noon', 'intensity': 1.0}
            elif 13 <= hour < 17:
                return {'position': 'afternoon', 'intensity': 0.8}
            elif 17 <= hour < 19:
                return {'position': 'dusk', 'intensity': 0.4}
            else:
                return {'position': 'night', 'intensity': 0.1}

        except Exception as e:
            self._logger.warning(f"太阳位置计算失败: {e}")
            return {'position': 'unknown', 'intensity': 0.5}


class SeasonalAnalyzer:
    """季节性分析器"""

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def calculate_seasonal_score(self, date: datetime, time_of_day: str) -> float:
        """
        计算季节性评分

        Args:
            date: 目标日期
            time_of_day: 时间段描述

        Returns:
            季节性评分 (0-100)
        """
        month = date.month
        hour = date.hour

        # 季节识别
        if 3 <= month <= 5:      # 春季
            return self._spring_season_score(hour)
        elif 6 <= month <= 8:    # 夏季
            return self._summer_season_score(hour)
        elif 9 <= month <= 11:   # 秋季
            return self._autumn_season_score(hour)
        else:                    # 冬季
            return self._winter_season_score(hour)

    def _spring_season_score(self, hour: int) -> float:
        """春季评分：繁殖期，早晚活跃"""
        if 6 <= hour <= 9 or 17 <= hour <= 19:
            return 100.0      # 早晚最佳
        elif 10 <= hour <= 16:
            return 85.0       # 中午稍差
        else:
            return 70.0       # 其他时间

    def _summer_season_score(self, hour: int) -> float:
        """夏季评分：避高温，清晨傍晚"""
        if 5 <= hour <= 8 or 18 <= hour <= 20:
            return 100.0      # 清晨傍晚最佳
        elif 11 <= hour <= 15:
            return 60.0       # 中午最差
        else:
            return 80.0       # 其他时间尚可

    def _autumn_season_score(self, hour: int) -> float:
        """秋季评分：觅食期，全天较好"""
        if 7 <= hour <= 10 or 16 <= hour <= 19:
            return 100.0      # 上午下午最佳
        else:
            return 85.0       # 其他时间也很好

    def _winter_season_score(self, hour: int) -> float:
        """冬季评分：低温期，中午相对较好"""
        if 11 <= hour <= 14:
            return 90.0       # 中午最佳
        elif 9 <= hour <= 16:
            return 75.0       # 白天尚可
        else:
            return 50.0       # 早晚很差

    def get_season_info(self, date: datetime) -> Dict[str, Any]:
        """
        获取季节信息

        Args:
            date: 目标日期

        Returns:
            季节信息字典
        """
        month = date.month

        if 3 <= month <= 5:
            season = 'spring'
            season_name = '春季'
        elif 6 <= month <= 8:
            season = 'summer'
            season_name = '夏季'
        elif 9 <= month <= 11:
            season = 'autumn'
            season_name = '秋季'
        else:
            season = 'winter'
            season_name = '冬季'

        return {
            'season': season,
            'season_name': season_name,
            'month': month
        }

    def get_optimal_fishing_times(self, season: str) -> List[Tuple[int, int]]:
        """
        获取指定季节的最佳钓鱼时间段

        Args:
            season: 季节标识

        Returns:
            最佳时间段列表
        """
        optimal_times = {
            'spring': [(6, 9), (17, 19)],
            'summer': [(5, 8), (18, 20)],
            'autumn': [(7, 10), (16, 19)],
            'winter': [(11, 14)]
        }

        return optimal_times.get(season, [(6, 9), (17, 19)])


class EnhancedFishingScorer:
    """增强钓鱼评分器"""

    def __init__(self):
        """初始化增强评分器"""
        self._logger = logging.getLogger(__name__)

        # 初始化各分析器组件
        self.weather_analyzer = WeatherTrendAnalyzer()
        self.astronomical_calculator = AstronomicalCalculator()
        self.seasonal_analyzer = SeasonalAnalyzer()
        self.pressure_analyzer = PressureTrendAnalyzer()

        # 评分权重配置 (总和为1.0)
        self.weights = {
            'temperature': 0.263,  # 26.3%
            'weather': 0.211,      # 21.1%
            'wind': 0.105,         # 15.8% (修复重复)
            'pressure': 0.158,     # 15.8%
            'humidity': 0.105,     # 10.5%
            'seasonal': 0.053,     # 5.3%
            'lunar': 0.053         # 5.3%
        }

        # 验证权重总和
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.0001:
            # 如果权重和不为1.0，进行标准化
            scale_factor = 1.0 / total_weight
            for key in self.weights:
                self.weights[key] *= scale_factor

        # 评分参数
        self.optimal_temp_range = (15, 25)
        self.optimal_wind_speed = (0, 15)
        self.preferred_weather = ["晴", "多云", "阴", "小雨"]

    def _calculate_temperature_score(self, temperature: float) -> float:
        """计算温度评分"""
        min_temp, max_temp = self.optimal_temp_range

        if min_temp <= temperature <= max_temp:
            return 100.0
        elif temperature < min_temp:
            if temperature < 0:
                return 0.0
            ratio = temperature / min_temp
            return max(0.0, ratio * 80)
        else:
            if temperature > 35:
                return 0.0
            excess = temperature - max_temp
            ratio = max(0, 1 - excess / 10)
            return ratio * 80

    def _calculate_weather_score(self, condition: str) -> float:
        """计算天气评分"""
        condition = condition.lower()

        best_weather = ["多云", "阴"]
        for weather in best_weather:
            if weather in condition:
                return 100.0

        good_weather = ["晴", "小雨"]
        for weather in good_weather:
            if weather in condition:
                return 85.0

        fair_weather = ["中雨"]
        for weather in fair_weather:
            if weather in condition:
                return 50.0

        poor_weather = ["大雨", "暴雨", "雷阵雨"]
        for weather in poor_weather:
            if weather in condition:
                return 20.0

        terrible_weather = ["雪", "冰雹", "雾", "霾"]
        for weather in terrible_weather:
            if weather in condition:
                return 10.0

        return 60.0

    def _calculate_wind_score(self, wind_speed: float) -> float:
        """计算风力评分"""
        min_wind, max_wind = self.optimal_wind_speed

        if min_wind <= wind_speed <= max_wind:
            return 100.0
        elif wind_speed < min_wind:
            return 85.0
        else:
            if wind_speed > 30:
                return 10.0
            excess = wind_speed - max_wind
            ratio = max(0, 1 - excess / 15)
            return ratio * 80

    def _calculate_humidity_score(self, humidity: float, pressure_trend: str = 'stable') -> float:
        """计算湿度评分"""
        if 60 <= humidity <= 80:
            base_score = 100.0          # 理想湿度
        elif 80 < humidity <= 90:
            base_score = 95.0           # 高湿度（低气压信号）
        elif 90 < humidity <= 95:
            base_score = 90.0           # 很高湿度
        elif 40 <= humidity < 60:
            base_score = 80.0           # 中等湿度
        else:
            base_score = 65.0           # 极端湿度

        # 气压趋势调整
        if pressure_trend == 'falling' and humidity > 75:
            base_score += 5  # 下降气压+高湿度双重奖励

        return min(100, base_score)

    def _get_time_of_day(self, date: datetime) -> str:
        """获取时间段描述"""
        hour = date.hour

        if 5 <= hour < 7:
            return 'dawn'
        elif 7 <= hour < 9:
            return 'morning'
        elif 9 <= hour < 12:
            return 'late_morning'
        elif 12 <= hour < 14:
            return 'noon'
        elif 14 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 19:
            return 'dusk'
        elif 19 <= hour < 22:
            return 'evening'
        else:
            return 'night'

    def calculate_comprehensive_score(
        self,
        hourly_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]],
        date: datetime
    ) -> FishingScore:
        """
        计算综合钓鱼评分

        Args:
            hourly_data: 当前小时数据
            historical_data: 历史数据序列 (用于趋势分析)
            date: 目标日期

        Returns:
            FishingScore: 详细的评分结果
        """
        try:
            # 1. 基础评分计算 (保持现有逻辑)
            base_temperature_score = self._calculate_temperature_score(hourly_data['temperature'])
            base_weather_score = self._calculate_weather_score(hourly_data['condition'])
            base_wind_score = self._calculate_wind_score(hourly_data['wind_speed'])

            # 2. 趋势分析 (需要历史数据)
            pressure_series = [h.get('pressure', 1013) for h in historical_data[-6:]]
            temp_series = [h.get('temperature', 20) for h in historical_data[-6:]]
            wind_series = [h.get('wind_speed', 5) for h in historical_data[-6:]]

            # 3. 新权重因子计算
            pressure_score = self.pressure_analyzer.calculate_comprehensive_score(
                hourly_data['pressure'], pressure_series
            )

            humidity_score = self._calculate_humidity_score(
                hourly_data['humidity'],
                self.weather_analyzer.get_pressure_trend(pressure_series).get('trend', 'stable')
            )

            temperature_trend_bonus = self.weather_analyzer.get_temperature_trend(temp_series)
            wind_stability_bonus = self.weather_analyzer.get_wind_stability(wind_series)

            seasonal_score = self.seasonal_analyzer.calculate_seasonal_score(
                date, self._get_time_of_day(date)
            )

            lunar_score = self.astronomical_calculator.calculate_lunar_score(
                date, self._get_time_of_day(date)
            )

            # 4. 综合权重计算
            overall_score = (
                base_temperature_score * self.weights['temperature'] +
                base_weather_score * self.weights['weather'] +
                base_wind_score * self.weights['wind'] +
                pressure_score * self.weights['pressure'] +
                humidity_score * self.weights['humidity'] +
                seasonal_score * self.weights['seasonal'] +
                lunar_score * self.weights['lunar']
            )

            # 5. 应用趋势调整
            overall_score *= temperature_trend_bonus.get('multiplier', 1.0)
            overall_score *= wind_stability_bonus.get('multiplier', 1.0)

            # 6. 限制在0-100范围
            overall_score = min(100, max(0, overall_score))

            # 7. 创建分析详情
            analysis_details = {
                'pressure_trend': self.weather_analyzer.get_pressure_trend(pressure_series).get('trend', 'unknown'),
                'temperature_change': temperature_trend_bonus.get('change_rate', 0),
                'wind_stability': wind_stability_bonus.get('stability', 'unknown'),
                'lunar_phase': self.astronomical_calculator.calculate_lunar_phase(date),
                'seasonal_factor': self.seasonal_analyzer.get_season_info(date).get('season_name', 'unknown')
            }

            return FishingScore(
                overall=overall_score,
                temperature=base_temperature_score,
                weather=base_weather_score,
                wind=base_wind_score,
                pressure=pressure_score,
                humidity=humidity_score,
                seasonal=seasonal_score,
                lunar=lunar_score,
                breakdown=self.weights.copy(),
                timestamp=datetime.now(),
                analysis_details=analysis_details
            )

        except Exception as e:
            self._logger.error(f"综合评分计算失败: {e}")
            # 返回默认评分
            return FishingScore(
                overall=50.0,
                temperature=70.0,
                weather=70.0,
                wind=70.0,
                pressure=70.0,
                humidity=70.0,
                seasonal=70.0,
                lunar=70.0,
                breakdown=self.weights.copy(),
                timestamp=datetime.now(),
                analysis_details={'error': str(e)}
            )

    def get_score_breakdown(self, score: FishingScore) -> Dict[str, Any]:
        """
        获取评分详细分解

        Args:
            score: 评分结果

        Returns:
            评分分解信息字典
        """
        breakdown = score.to_dict()

        # 添加权重分析
        weight_analysis = {}
        total_weight = sum(score.breakdown.values())

        for factor, weight in score.breakdown.items():
            factor_score = getattr(score, factor, 0)
            contribution = factor_score * weight
            weight_analysis[factor] = {
                'weight': weight,
                'weight_percentage': (weight / total_weight) * 100,
                'score': factor_score,
                'contribution': contribution,
                'contribution_percentage': (contribution / score.overall) * 100 if score.overall > 0 else 0
            }

        breakdown['weight_analysis'] = weight_analysis
        return breakdown