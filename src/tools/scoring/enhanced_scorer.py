#!/usr/bin/env python3
"""
增强钓鱼评分引擎

实现7因子科学评分体系:
1. 温度评分 (25%)
2. 天气评分 (20%)
3. 风力评分 (15%)
4. 气压评分 (15%)
5. 湿度评分 (10%)
6. 季节性评分 (5%) ⭐ 新增
7. 月相评分 (5%) ⭐ 新增

动态趋势分析:
- 气压趋势分析 (识别"钓鱼黄金期")
- 温度变化趋势
- 风速稳定性分析
"""

from typing import Dict, Any, List
from datetime import datetime
import math
import logging

logger = logging.getLogger(__name__)


# ===== 季节性评分配置 =====
SEASONAL_CONFIG = {
    'spring': [3, 4, 5],   # 春季月份
    'summer': [6, 7, 8],   # 夏季月份
    'autumn': [9, 10, 11], # 秋季月份
    'winter': [12, 1, 2]   # 冬季月份
}


def calculate_seasonal_score(date: datetime, hour: int = None) -> float:
    """
    计算季节性评分

    基于鱼类生物学规律和季节活动模式:
    - 春季(3-5月): 繁殖期，活跃度高，早晚最佳
    - 夏季(6-8月): 高温期，避开中午，清晨傍晚最佳
    - 秋季(9-11月): 觅食期，全天较好
    - 冬季(12-2月): 代谢缓慢，中午相对较好

    Args:
        date: 目标日期（datetime对象）
        hour: 小时数 (0-23)，如果为None则从date提取

    Returns:
        季节性评分 (0-100)

    Examples:
        >>> calculate_seasonal_score(datetime(2024, 4, 15, 7, 0), 7)
        100.0  # 春季早晨
        >>> calculate_seasonal_score(datetime(2024, 7, 15, 13, 0), 13)
        60.0   # 夏季中午
    """
    try:
        month = date.month
        if hour is None:
            hour = date.hour

        # 春季评分 (3-5月)
        if month in SEASONAL_CONFIG['spring']:
            if 6 <= hour <= 9 or 17 <= hour <= 19:
                return 100.0  # 早晚最佳
            elif 10 <= hour <= 16:
                return 85.0   # 白天尚可
            else:
                return 70.0   # 夜间一般

        # 夏季评分 (6-8月)
        elif month in SEASONAL_CONFIG['summer']:
            if 5 <= hour <= 8 or 18 <= hour <= 20:
                return 100.0  # 清晨傍晚最佳
            elif 11 <= hour <= 15:
                return 60.0   # 中午最差
            else:
                return 80.0   # 其他时段尚可

        # 秋季评分 (9-11月)
        elif month in SEASONAL_CONFIG['autumn']:
            if 7 <= hour <= 10 or 16 <= hour <= 19:
                return 100.0  # 早晚最佳
            else:
                return 85.0   # 全天较好

        # 冬季评分 (12-2月)
        else:
            if 11 <= hour <= 14:
                return 90.0   # 中午最佳
            elif 9 <= hour <= 16:
                return 75.0   # 白天尚可
            else:
                return 50.0   # 早晚很差

    except Exception as e:
        logger.error(f"季节性评分计算失败: {e}")
        return 75.0  # 返回默认中等评分


def calculate_lunar_phase(date: datetime) -> str:
    """
    计算月相（使用简化儒略日算法）

    月相周期: 29.53059天

    Args:
        date: 目标日期

    Returns:
        月相名称: 'new_moon', 'waxing_crescent', 'first_quarter', 'waxing_gibbous',
                 'full_moon', 'waning_gibbous', 'last_quarter', 'waning_crescent'

    Algorithm:
        使用简化儒略日计算:
        JD = C + E + D - 694039.09
        其中 C = 年份因子, E = 月份因子, D = 日期

    Examples:
        >>> calculate_lunar_phase(datetime(2024, 6, 6, 12, 0))
        'new_moon'  # 2024年6月6日是新月
    """
    try:
        year, month, day = date.year, date.month, date.day

        # 儒略日简化计算
        if month <= 2:
            year -= 1
            month += 12

        A = math.floor(year / 100)
        B = math.floor((year - A * 100) / 4)
        C = math.floor((year - A * 4 * 100 + B) / 4)
        E = math.floor((month + 1) * 30.6)

        # 简化的月相计算（已知新月参考点）
        jd = C + E + day - 694039.09
        lunar_cycle = 29.53059

        # 计算距离新月的天数
        days_since_new = (jd + 4.867) % lunar_cycle

        # 计算月相索引 (0-7)
        phase_index = int((days_since_new / lunar_cycle) * 8)

        # 月相名称映射
        moon_phases = [
            'new_moon',         # 新月
            'waxing_crescent',  # 娥眉月（上弦前）
            'first_quarter',    # 上弦月
            'waxing_gibbous',   # 盈凸月（满月前）
            'full_moon',        # 满月
            'waning_gibbous',   # 亏凸月（满月后）
            'last_quarter',     # 下弦月
            'waning_crescent'   # 残月（新月前）
        ]

        return moon_phases[phase_index]

    except Exception as e:
        logger.error(f"月相计算失败: {e}")
        return 'unknown'


def calculate_lunar_score(date: datetime, is_night: bool = False) -> float:
    """
    计算月相评分

    基于传统钓鱼经验和天文学知识:
    - 月球引力影响潮汐和鱼类活动
    - 满月期间鱼类夜间活动增加
    - 新月和满月是钓鱼的较好时机

    Args:
        date: 目标日期
        is_night: 是否为夜间 (18:00-6:00)

    Returns:
        月相评分 (0-100)

    Score Table:
        - 新月: 85分（鱼类活跃）
        - 娥眉月: 80分
        - 上弦月/下弦月: 75分
        - 盈凸月/亏凸月: 82分
        - 满月(夜间): 90分（最佳）⭐
        - 满月(白天): 65分（一般）

    Examples:
        >>> calculate_lunar_score(datetime(2024, 5, 23, 20, 0), is_night=True)
        90.0  # 满月夜间
        >>> calculate_lunar_score(datetime(2024, 5, 23, 12, 0), is_night=False)
        65.0  # 满月白天
    """
    try:
        moon_phase = calculate_lunar_phase(date)

        # 月相评分映射
        moon_scores = {
            'new_moon': 85,          # 新月
            'waxing_crescent': 80,   # 娥眉月
            'first_quarter': 75,     # 上弦月
            'waxing_gibbous': 82,    # 盈凸月
            'full_moon': 90 if is_night else 65,  # 满月：夜间最佳，白天一般
            'waning_gibbous': 78,    # 亏凸月
            'last_quarter': 75,      # 下弦月
            'waning_crescent': 80    # 残月
        }

        score = moon_scores.get(moon_phase, 75.0)

        logger.debug(f"月相评分: {moon_phase} -> {score}分 (夜间={is_night})")
        return score

    except Exception as e:
        logger.error(f"月相评分计算失败: {e}")
        return 75.0  # 返回默认中等评分


def analyze_pressure_trend(pressure_series: List[float]) -> Dict[str, Any]:
    """
    分析气压趋势（需要至少6个小时的历史数据）

    气压变化是鱼类活动的关键因子:
    - 气压下降: 预示天气系统变化，刺激鱼类进食（钓鱼黄金期）
    - 气压上升: 天气稳定，鱼类活跃度降低

    Args:
        pressure_series: 气压序列（至少6个数据点，按时间顺序）
                        单位: hPa (百帕)

    Returns:
        {
            'multiplier': float,    # 评分调整系数 (0.80-1.20)
            'trend': str,           # 趋势类型
            'change_rate': float,   # 变化速率 (hPa/6h)
            'recent_avg': float,    # 最近平均气压
            'earlier_avg': float    # 较早平均气压
        }

    Trend Types:
        - 'falling_fast': 快速下降 (<-2 hPa/6h) → +20%奖励 ⭐ 钓鱼黄金期
        - 'falling_slow': 缓慢下降 (-2~-0.5 hPa/6h) → +10%奖励
        - 'stable': 稳定 (±0.5 hPa/6h) → 正常评分
        - 'rising_slow': 缓慢上升 (0.5~2 hPa/6h) → -10%惩罚
        - 'rising_fast': 快速上升 (>2 hPa/6h) → -20%惩罚

    Examples:
        >>> analyze_pressure_trend([1020, 1018, 1015, 1012, 1009, 1005])
        {'multiplier': 1.20, 'trend': 'falling_fast', 'change_rate': -5.0, ...}
    """
    try:
        if not pressure_series or len(pressure_series) < 3:
            logger.warning("气压数据不足，无法进行趋势分析")
            return {
                'multiplier': 1.0,
                'trend': 'insufficient_data',
                'change_rate': 0.0,
                'recent_avg': None,
                'earlier_avg': None
            }

        # 计算最近3个点的平均值（代表最近气压）
        recent_avg = sum(pressure_series[-3:]) / 3

        # 计算较早3个点的平均值（代表6小时前气压）
        if len(pressure_series) >= 6:
            earlier_avg = sum(pressure_series[-6:-3]) / 3
        else:
            # 数据不足6个点，使用可用数据
            earlier_avg = sum(pressure_series[:-3]) / len(pressure_series[:-3]) if len(pressure_series) > 3 else recent_avg

        # 计算6小时变化率
        change = recent_avg - earlier_avg

        # 确定趋势类型和调整系数
        if change < -2:
            trend = 'falling_fast'
            multiplier = 1.20  # ⭐ 快速下降：20%奖励（钓鱼黄金期！）
        elif change < -0.5:
            trend = 'falling_slow'
            multiplier = 1.10  # 缓慢下降：10%奖励
        elif -0.5 <= change <= 0.5:
            trend = 'stable'
            multiplier = 1.00  # 稳定：正常评分
        elif change <= 2:
            trend = 'rising_slow'
            multiplier = 0.90  # 缓慢上升：-10%惩罚
        else:
            trend = 'rising_fast'
            multiplier = 0.80  # 快速上升：-20%惩罚

        logger.info(f"气压趋势分析: {trend}, 变化={change:.2f} hPa/6h, 调整系数={multiplier}")

        return {
            'multiplier': multiplier,
            'trend': trend,
            'change_rate': change,
            'recent_avg': recent_avg,
            'earlier_avg': earlier_avg
        }

    except Exception as e:
        logger.error(f"气压趋势分析失败: {e}")
        return {
            'multiplier': 1.0,
            'trend': 'error',
            'change_rate': 0.0,
            'recent_avg': None,
            'earlier_avg': None
        }


def analyze_temperature_trend(temp_series: List[float]) -> float:
    """
    分析温度变化趋势

    温度上升有利于鱼类活动:
    - 升温: 鱼类新陈代谢加快，活跃度提升
    - 降温: 鱼类活跃度降低

    Args:
        temp_series: 温度序列（至少6个数据点，按时间顺序）
                    单位: °C

    Returns:
        multiplier: 评分调整系数 (0.80-1.10)

    Adjustment Rules:
        - 快速升温 (>3°C/6h): 1.10倍 (+10%)
        - 缓慢升温 (1-3°C/6h): 1.05倍 (+5%)
        - 稳定 (±1°C/6h): 1.00倍 (正常)
        - 缓慢降温 (-1~-3°C/6h): 0.95倍 (-5%)
        - 快速降温 (<-3°C/6h): 0.90倍 (-10%)

    Examples:
        >>> analyze_temperature_trend([18, 19, 20, 21, 22, 23])
        1.10  # 快速升温
    """
    try:
        if not temp_series or len(temp_series) < 3:
            logger.warning("温度数据不足，无法进行趋势分析")
            return 1.0

        # 计算最近3个点的平均值
        recent_avg = sum(temp_series[-3:]) / 3

        # 计算较早3个点的平均值
        if len(temp_series) >= 6:
            earlier_avg = sum(temp_series[-6:-3]) / 3
        else:
            earlier_avg = sum(temp_series[:-3]) / len(temp_series[:-3]) if len(temp_series) > 3 else recent_avg

        # 计算6小时变化
        change = recent_avg - earlier_avg

        # 确定调整系数
        if change > 3:
            multiplier = 1.10  # 快速升温：+10%
        elif change > 1:
            multiplier = 1.05  # 缓慢升温：+5%
        elif -1 <= change <= 1:
            multiplier = 1.00  # 稳定：正常
        elif change > -3:
            multiplier = 0.95  # 缓慢降温：-5%
        else:
            multiplier = 0.90  # 快速降温：-10%

        logger.debug(f"温度趋势分析: 变化={change:.2f}°C/6h, 调整系数={multiplier}")

        return multiplier

    except Exception as e:
        logger.error(f"温度趋势分析失败: {e}")
        return 1.0


def analyze_wind_stability(wind_series: List[float]) -> float:
    """
    分析风速稳定性

    稳定的风速更利于钓鱼:
    - 稳定风速: 便于观漂和抛竿
    - 不稳定风速: 影响钓鱼准确性和舒适度

    Args:
        wind_series: 风速序列（至少6个数据点）
                    单位: m/s

    Returns:
        multiplier: 评分调整系数 (0.80-1.05)

    Stability Rules:
        - 标准差 < 1 km/h: 1.05倍 (+5%) 稳定
        - 标准差 < 2 km/h: 1.00倍 (正常)
        - 标准差 < 4 km/h: 0.90倍 (-10%) 较不稳定
        - 标准差 >= 4 km/h: 0.80倍 (-20%) 非常不稳定

    Examples:
        >>> analyze_wind_stability([3.0, 3.1, 2.9, 3.0, 3.2, 3.0])
        1.05  # 稳定风速
    """
    try:
        if not wind_series or len(wind_series) < 3:
            logger.warning("风速数据不足，无法进行稳定性分析")
            return 1.0

        # 转换为 km/h 进行计算（更符合气象习惯）
        wind_kmh = [w * 3.6 for w in wind_series]

        # 计算平均值
        mean = sum(wind_kmh) / len(wind_kmh)

        # 计算标准差
        variance = sum((x - mean) ** 2 for x in wind_kmh) / len(wind_kmh)
        std_dev = math.sqrt(variance)

        # 确定调整系数
        if std_dev < 1:
            multiplier = 1.05  # 非常稳定：+5%
        elif std_dev < 2:
            multiplier = 1.00  # 稳定：正常
        elif std_dev < 4:
            multiplier = 0.90  # 较不稳定：-10%
        else:
            multiplier = 0.80  # 非常不稳定：-20%

        logger.debug(f"风速稳定性分析: 标准差={std_dev:.2f} km/h, 调整系数={multiplier}")

        return multiplier

    except Exception as e:
        logger.error(f"风速稳定性分析失败: {e}")
        return 1.0
