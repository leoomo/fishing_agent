#!/usr/bin/env python3
"""
钓鱼评分引擎模块

职责:
- 7因子科学评分体系 (温度/天气/风力/气压/湿度/季节/月相)
- 24小时逐时评分计算
- 基础5因子评分 (无季节/月相数据时的回退方案)
- 单因子评分函数 (温度/天气/风力/湿度/气压)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)

try:
    from .enhanced_scorer import (
        calculate_seasonal_score,
        calculate_lunar_score,
        analyze_pressure_trend,
        analyze_temperature_trend,
        analyze_wind_stability
    )
    ENHANCED_SCORER_AVAILABLE = True
except ImportError:
    logger.warning("增强评分模块不可用，将使用基础评分")
    ENHANCED_SCORER_AVAILABLE = False


def calculate_fishing_score(
    weather_data: Dict[str, Any],
    target_date: datetime = None,
    historical_data: List[Dict[str, Any]] = None
) -> Dict[str, float]:
    """
    计算钓鱼评分 - 7因子科学评分体系 v3.1（基于科学研究优化）

    Args:
        weather_data: 天气数据字典
        target_date: 目标日期（用于季节和月相计算）
        historical_data: 历史数据列表（用于趋势分析，至少6个数据点）

    Returns:
        评分字典，包含7个因子评分和趋势分析结果
    """
    # 使用增强评分模块（已在模块顶部导入）
    if not ENHANCED_SCORER_AVAILABLE:
        logger.warning("增强评分模块不可用，使用基础评分")
        return calculate_basic_fishing_score(weather_data)

    # 严格验证天气数据完整性
    required_fields = ['temperature', 'condition', 'wind_speed', 'humidity', 'pressure']
    missing_fields = [field for field in required_fields if weather_data.get(field) is None]

    if missing_fields:
        logger.error(f"天气数据不完整，缺少字段: {missing_fields}")
        logger.error(f"现有数据: {weather_data}")
        # 返回所有0分，表示无法计算
        return {
            'overall': 0.0,
            'temperature': 0.0,
            'condition': 0.0,
            'wind': 0.0,
            'humidity': 0.0,
            'pressure': 0.0,
            'seasonal': 0.0,
            'lunar': 0.0,
            'data_quality': 'incomplete'
        }

    # 验证数据的合理性
    temp = weather_data['temperature']
    if not isinstance(temp, (int, float)) or temp < -60 or temp > 70:
        logger.error(f"温度数据异常: {temp} (类型: {type(temp)})")

        # 尝试从小时温度数据降级
        hourly_temps = weather_data.get('hourly_temps', [])
        if hourly_temps and len(hourly_temps) > 0:
            avg_temp = sum(hourly_temps) / len(hourly_temps)
            if -60 <= avg_temp <= 70:
                logger.info(f"使用小时温度平均值作为降级: {avg_temp}°C")
                weather_data['temperature'] = avg_temp
                weather_data['data_quality'] = 'estimated_from_hourly'
            else:
                return {
                    'overall': 0.0, 'temperature': 0.0, 'condition': 0.0, 'wind': 0.0,
                    'humidity': 0.0, 'pressure': 0.0, 'seasonal': 0.0, 'lunar': 0.0,
                    'data_quality': 'hourly_temp_invalid'
                }
        else:
            return {
                'overall': 0.0, 'temperature': 0.0, 'condition': 0.0, 'wind': 0.0,
                'humidity': 0.0, 'pressure': 0.0, 'seasonal': 0.0, 'lunar': 0.0,
                'data_quality': 'no_temperature_data'
            }

    # 获取验证过的数据
    condition = weather_data['condition']
    wind = weather_data['wind_speed']
    humidity = weather_data['humidity']
    pressure = weather_data['pressure']

    logger.info(f"使用验证过的天气数据: 温度={temp}°C, 天气={condition}, 风速={wind}m/s")

    # 各维度评分（基础5因子）
    temp_score = calc_temp_score(temp)
    weather_score = calc_weather_score(condition)
    wind_score = calc_wind_score(wind)
    humidity_score = calc_humidity_score(humidity)
    pressure_score = calc_pressure_score(pressure)

    # 新增因子：季节性评分
    seasonal_score = 75.0  # 默认中等评分
    if target_date:
        try:
            hour = target_date.hour if isinstance(target_date, datetime) else 12
            seasonal_score = calculate_seasonal_score(target_date, hour)
            logger.debug(f"季节性评分: {seasonal_score:.1f}分")
        except Exception as e:
            logger.warning(f"季节性评分计算失败: {e}")

    # 新增因子：月相评分
    lunar_score = 75.0  # 默认中等评分
    if target_date:
        try:
            is_night = target_date.hour < 6 or target_date.hour > 18
            lunar_score = calculate_lunar_score(target_date, is_night)
            logger.debug(f"月相评分: {lunar_score:.1f}分 (夜间={is_night})")
        except Exception as e:
            logger.warning(f"月相评分计算失败: {e}")

    # 趋势分析
    pressure_multiplier = 1.0
    temp_multiplier = 1.0
    wind_multiplier = 1.0

    if historical_data and len(historical_data) >= 3:
        try:
            # 气压趋势分析
            pressure_series = [d.get('pressure') for d in historical_data if d.get('pressure') is not None]
            if len(pressure_series) >= 3:
                pressure_trend = analyze_pressure_trend(pressure_series)
                pressure_multiplier = pressure_trend['multiplier']
                logger.info(f"气压趋势: {pressure_trend['trend']}, 调整系数={pressure_multiplier}")

            # 温度趋势分析
            temp_series = [d.get('temperature') for d in historical_data if d.get('temperature') is not None]
            if len(temp_series) >= 3:
                temp_multiplier = analyze_temperature_trend(temp_series)
                logger.debug(f"温度趋势调整系数: {temp_multiplier}")

            # 风速稳定性分析
            wind_series = [d.get('wind_speed') for d in historical_data if d.get('wind_speed') is not None]
            if len(wind_series) >= 3:
                wind_multiplier = analyze_wind_stability(wind_series)
                logger.debug(f"风速稳定性调整系数: {wind_multiplier}")

        except Exception as e:
            logger.warning(f"趋势分析失败: {e}")

    # 7因子权重配置 (v3.1 - 基于科学研究优化)
    # 科学依据:
    # - 气压: 黄鲈研究P=0.55无显著性，权重从15%降至10%
    # - 湿度: 与天气高度相关，权重从10%降至5%
    # - 季节性: 证据充分，权重从5%提升至13%
    # - 天气: 核心因子，权重从20%提升至27%
    weights = {
        'temperature': 0.25,  # 温度 25% (不变，核心因子)
        'weather': 0.27,      # 天气 27% (从20%提升) ⭐
        'wind': 0.15,         # 风力 15% (保持)
        'pressure': 0.10,     # 气压 10% (从15%降低，科学证据较弱) ⭐
        'humidity': 0.05,     # 湿度 5% (从10%降低，与天气重叠) ⭐
        'seasonal': 0.13,     # 季节 13% (从5%提升，证据充分) ⭐
        'lunar': 0.05         # 月相 5% (保持，作为参考因素)
    }

    # 基础加权评分
    overall_score = (
        temp_score * weights['temperature'] +
        weather_score * weights['weather'] +
        wind_score * weights['wind'] +
        pressure_score * weights['pressure'] +
        humidity_score * weights['humidity'] +
        seasonal_score * weights['seasonal'] +
        lunar_score * weights['lunar']
    )

    # 应用趋势调整（气压趋势最重要）
    overall_score *= pressure_multiplier
    overall_score *= temp_multiplier
    overall_score *= wind_multiplier

    # 确保评分在0-100范围内
    overall_score = min(100, max(0, overall_score))

    logger.info(f"综合评分: {overall_score:.1f}分 (气压调整={pressure_multiplier}, 温度调整={temp_multiplier}, 风速调整={wind_multiplier})")

    return {
        'overall': overall_score,
        'temperature': temp_score,
        'weather': weather_score,
        'wind': wind_score,
        'humidity': humidity_score,
        'pressure': pressure_score,
        'seasonal': seasonal_score,  # 新增
        'lunar': lunar_score,        # 新增
        'data_quality': 'valid',
        # 趋势分析结果
        'trend_analysis': {
            'pressure_multiplier': pressure_multiplier,
            'temp_multiplier': temp_multiplier,
            'wind_multiplier': wind_multiplier
        }
    }


def calculate_basic_fishing_score(weather_data: Dict[str, Any]) -> Dict[str, float]:
    """
    基础钓鱼评分（回退版本，当增强模块不可用时）
    5因子评分体系
    """
    # 严格验证天气数据完整性
    required_fields = ['temperature', 'condition', 'wind_speed', 'humidity', 'pressure']
    missing_fields = [field for field in required_fields if weather_data.get(field) is None]

    if missing_fields:
        logger.error(f"天气数据不完整，缺少字段: {missing_fields}")
        return {
            'overall': 0.0,
            'temperature': 0.0,
            'condition': 0.0,
            'wind': 0.0,
            'humidity': 0.0,
            'pressure': 0.0,
            'data_quality': 'incomplete'
        }

    # 验证数据的合理性
    temp = weather_data['temperature']
    if not isinstance(temp, (int, float)) or temp < -60 or temp > 70:
        logger.error(f"温度数据异常: {temp}")
        return {
            'overall': 0.0, 'temperature': 0.0, 'condition': 0.0, 'wind': 0.0,
            'humidity': 0.0, 'pressure': 0.0, 'data_quality': 'invalid'
        }

    # 获取验证过的数据
    condition = weather_data['condition']
    wind = weather_data['wind_speed']
    humidity = weather_data['humidity']
    pressure = weather_data['pressure']

    # 各维度评分
    temp_score = calc_temp_score(temp)
    weather_score = calc_weather_score(condition)
    wind_score = calc_wind_score(wind)
    humidity_score = calc_humidity_score(humidity)
    pressure_score = calc_pressure_score(pressure)

    # 基础权重配置（旧版本）
    weights = {
        'temperature': 0.25,
        'weather': 0.30,
        'wind': 0.20,
        'humidity': 0.15,
        'pressure': 0.10
    }

    overall_score = (
        temp_score * weights['temperature'] +
        weather_score * weights['weather'] +
        wind_score * weights['wind'] +
        humidity_score * weights['humidity'] +
        pressure_score * weights['pressure']
    )

    return {
        'overall': overall_score,
        'temperature': temp_score,
        'weather': weather_score,
        'wind': wind_score,
        'humidity': humidity_score,
        'pressure': pressure_score,
        'data_quality': 'valid'
    }


def calculate_hourly_scores(weather_data: Dict[str, Any], target_date: date = None) -> List[Dict[str, Any]]:
    """
    按小时计算钓鱼评分（使用7因子评分体系）

    Args:
        weather_data: 包含hourly数据数组的天气数据
        target_date: 目标日期（用于季节和月相计算）

    Returns:
        24小时评分列表，每项包含小时、时间、评分和天气详情
    """
    try:
        # 检查是否有小时数据
        if not weather_data.get('has_hourly_data', False):
            logger.warning("没有hourly数据，无法计算小时评分")
            return []

        hourly_temps = weather_data.get('hourly_temps', [])
        hourly_conditions = weather_data.get('hourly_conditions', [])
        hourly_wind_speeds = weather_data.get('hourly_wind_speeds', [])
        hourly_humidities = weather_data.get('hourly_humidities', [])
        hourly_pressures = weather_data.get('hourly_pressures', [])
        hourly_datetimes = weather_data.get('hourly_datetimes', [])

        # 验证数据完整性
        data_length = len(hourly_temps)
        if data_length == 0:
            logger.error("hourly_temps为空")
            return []

        hourly_scores = []

        # 遍历每个小时
        for i in range(data_length):
            try:
                # 获取该小时的天气数据
                temp = hourly_temps[i] if i < len(hourly_temps) else None
                condition = hourly_conditions[i] if i < len(hourly_conditions) else None
                wind_speed = hourly_wind_speeds[i] if i < len(hourly_wind_speeds) else None
                humidity = hourly_humidities[i] if i < len(hourly_humidities) else None
                pressure = hourly_pressures[i] if i < len(hourly_pressures) else None
                dt = hourly_datetimes[i] if i < len(hourly_datetimes) else None

                # 验证必需字段
                if None in [temp, condition, wind_speed, humidity, pressure]:
                    logger.debug(f"第{i}小时数据不完整，跳过")
                    continue

                # 构建该小时的天气数据字典
                hour_weather = {
                    'temperature': temp,
                    'condition': condition,
                    'wind_speed': wind_speed,
                    'humidity': humidity,
                    'pressure': pressure
                }

                # 构建该小时的datetime对象
                if dt:
                    hour_datetime = dt
                elif target_date:
                    # 如果没有具体datetime，从target_date构建
                    hour_datetime = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=i)
                else:
                    # 最后的回退：使用当前日期
                    hour_datetime = datetime.now().replace(hour=i, minute=0, second=0, microsecond=0)

                # 使用完整的7因子评分函数
                # 注意：小时评分暂不使用历史趋势分析（避免复杂度过高）
                hour_scores_dict = calculate_fishing_score(
                    hour_weather,
                    target_date=hour_datetime,
                    historical_data=None  # 小时评分不使用趋势分析
                )

                # 构建该小时的评分记录
                # 从 datetime 对象获取实际的小时值
                actual_hour = hour_datetime.hour if hasattr(hour_datetime, 'hour') else i
                hour_score = {
                    'hour': actual_hour,
                    'datetime': hour_datetime,
                    'time_str': hour_datetime.strftime('%H:%M'),
                    'score': hour_scores_dict['overall'],
                    'temperature': temp,
                    'condition': condition,
                    'wind_speed': wind_speed,
                    'humidity': humidity,
                    'pressure': pressure,
                    'scores': {
                        'temperature': hour_scores_dict['temperature'],
                        'weather': hour_scores_dict['weather'],
                        'wind': hour_scores_dict['wind'],
                        'humidity': hour_scores_dict['humidity'],
                        'pressure': hour_scores_dict['pressure'],
                        'seasonal': hour_scores_dict.get('seasonal', 75.0),
                        'lunar': hour_scores_dict.get('lunar', 75.0)
                    }
                }

                hourly_scores.append(hour_score)

            except Exception as e:
                logger.warning(f"计算第{i}小时评分失败: {e}")
                continue

        logger.info(f"成功计算{len(hourly_scores)}个小时的钓鱼评分（7因子体系）")
        return hourly_scores

    except Exception as e:
        logger.error(f"按小时计算评分失败: {e}")
        return []



def calc_temp_score(temp: float) -> float:
    """温度评分

    科学依据：大多数鱼类在60-75°F (15-24°C)最活跃
    扩大黄金区间至14-26°C，更符合实际观测
    """
    if 14 <= temp <= 26:       # 扩大黄金区间（从15-25°C）
        return 95.0
    elif 10 <= temp < 14 or 26 < temp <= 30:
        return 80.0
    elif 5 <= temp < 10 or 30 < temp <= 35:
        return 60.0
    else:
        return 35.0            # 极端温度（从30提高到35）


def calc_weather_score(condition: str) -> float:
    """天气状况评分

    科学依据：
    - 多云/阴天：鱼类在弱光条件下更大胆，愿意在开阔水域觅食
    - 小雨：虽带来氧气，但也会浑浊水体、降低水温，评分从95降至75
    - 晴天：总体条件好，但夏季中午会造成水层温差
    """
    if condition in ['多云', '阴']:
        return 95.0            # 最佳条件
    elif condition in ['晴', '雾']:
        return 80.0
    elif condition in ['小雨']:
        return 75.0            # 从95分降低（小雨效果不如多云/阴天稳定）
    elif condition in ['中雨']:
        return 50.0
    elif condition in ['大雨', '暴雨']:
        return 20.0
    else:
        return 70.0


def calc_wind_score(wind: float) -> float:
    """风力评分

    科学依据：
    - 最佳风速: 5-10 mph (8-16 km/h, 2.2-4.4 m/s)
    - 适度风速增加溶氧、推动浮游生物聚集
    - 过于平静时鱼类警觉性更高
    """
    # 输入单位: m/s
    if 2 <= wind <= 5:         # 最佳风速区间
        return 95.0
    elif wind < 2:             # 过于平静
        return 85.0
    elif wind <= 7:            # 中等风速
        return 80.0
    elif wind <= 10:           # 较大风速
        return 60.0
    else:                      # 强风
        return 30.0


def calc_humidity_score(humidity: float) -> float:
    """湿度评分"""
    if 50 <= humidity <= 70:
        return 90.0
    elif 40 <= humidity < 50 or 70 < humidity <= 80:
        return 75.0
    elif 30 <= humidity < 40 or 80 < humidity <= 90:
        return 60.0
    else:
        return 40.0


def calc_pressure_score(pressure: float) -> float:
    """气压评分"""
    if 1000 <= pressure <= 1020:
        return 90.0
    elif 990 <= pressure < 1000 or 1020 < pressure <= 1030:
        return 75.0
    else:
        return 55.0

