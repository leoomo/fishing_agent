#!/usr/bin/env python3
"""
天气工具模块 - 简化架构版本

使用LangChain 1.0+最佳实践，直接API调用，移除过度抽象。
整合所有天气相关功能到单个文件中，替代原来的20+个文件。
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
import logging
from langchain.tools import tool
from dateutil import parser as dateparser

try:
    from ..utils.coordinate_utils import get_coordinates
    from ..utils.api_client import get_weather_client
    from ..utils.cache import cache
except ImportError:
    # 回退到绝对导入
    from utils.coordinate_utils import get_coordinates
    from utils.api_client import get_weather_client
    from utils.cache import cache

logger = logging.getLogger(__name__)


@tool
def get_current_weather(location: str) -> str:
    """
    获取指定位置的当前天气信息

    Args:
        location: 位置名称，如"杭州"、"北京"、"余杭区"等

    Returns:
        详细的当前天气信息，包括温度、湿度、风速、天气状况等
    """
    try:
        # 获取坐标
        coords = get_coordinates(location)
        longitude, latitude = coords

        # 获取天气数据
        weather_client = get_weather_client()
        weather_data = weather_client.get_realtime_weather(longitude, latitude)

        if not weather_data:
            return f"抱歉，无法获取{location}的天气数据，请稍后重试。"

        # 解析天气数据
        realtime = weather_data.get('result', {}).get('realtime', {})

        temperature = realtime.get('temperature', 0)
        humidity = realtime.get('humidity', 0)
        pressure = realtime.get('pressure', 0)
        wind_speed = realtime.get('wind', {}).get('speed', 0)
        wind_direction = realtime.get('wind', {}).get('direction', 0)
        weather_skycon = realtime.get('skycon', 'unknown')
        visibility = realtime.get('visibility', 10)

        # 天气状况中文映射
        weather_map = {
            'CLEAR_DAY': '晴朗',
            'CLEAR_NIGHT': '晴朗（夜间）',
            'PARTLY_CLOUDY_DAY': '多云',
            'PARTLY_CLOUDY_NIGHT': '多云（夜间）',
            'CLOUDY': '阴天',
            'LIGHT_HAZE': '轻度雾霾',
            'MODERATE_HAZE': '中度雾霾',
            'HEAVY_HAZE': '重度雾霾',
            'LIGHT_RAIN': '小雨',
            'MODERATE_RAIN': '中雨',
            'HEAVY_RAIN': '大雨',
            'STORM_RAIN': '暴雨',
            'LIGHT_SNOW': '小雪',
            'MODERATE_SNOW': '中雪',
            'HEAVY_SNOW': '大雪',
            'STORM_SNOW': '暴雪',
            'DUST': '浮尘',
            'SAND': '沙尘',
            'WIND': '大风'
        }

        weather_cn = weather_map.get(weather_skycon, weather_skycon)

        # 构建返回结果
        result = f"🌤️ {location} 当前天气信息：\n\n"
        result += f"🌡️ 温度: {temperature}°C\n"
        result += f"☁️ 天气: {weather_cn}\n"
        result += f"💧 湿度: {humidity}%\n"
        result += f"💨 风速: {wind_speed} m/s\n"
        result += f"🧭 风向: {wind_direction}°\n"
        result += f"🌀 气压: {pressure} hPa\n"
        result += f"👁️ 能见度: {visibility} km\n"
        result += f"🕐 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        return result

    except ValueError as e:
        return f"位置错误: {str(e)}"
    except Exception as e:
        logger.error(f"获取天气失败: {e}")
        return f"获取{location}天气信息时发生错误，请稍后重试。"


@tool
def get_weather_forecast(location: str, days: int = 3) -> str:
    """
    获取指定位置的天气预报

    Args:
        location: 位置名称，如"杭州"、"北京"、"余杭区"等
        days: 预报天数（1-7天）

    Returns:
        详细的天气预报信息，包括未来几天的温度范围和天气状况
    """
    try:
        if not 1 <= days <= 7:
            return "预报天数必须在1-7天之间"

        # 获取坐标
        coords = get_coordinates(location)
        longitude, latitude = coords

        # 获取72小时预报数据（支持最多3天）
        weather_client = get_weather_client()

        # 优先尝试hourly预报（72小时）
        hourly_data = weather_client.get_hourly_forecast(longitude, latitude, 72)

        if hourly_data:
            return _format_hourly_forecast(hourly_data, location, days)
        else:
            # 降级到daily预报
            daily_data = weather_client.get_daily_forecast(longitude, latitude, days)
            if daily_data:
                return _format_daily_forecast(daily_data, location, days)
            else:
                return f"抱歉，无法获取{location}的天气预报数据，请稍后重试。"

    except ValueError as e:
        return f"位置错误: {str(e)}"
    except Exception as e:
        logger.error(f"获取天气预报失败: {e}")
        return f"获取{location}天气预报时发生错误，请稍后重试。"


def _format_hourly_forecast(hourly_data: Dict, location: str, days: int) -> str:
    """格式化小时级预报数据"""
    try:
        hourly = hourly_data.get('result', {}).get('hourly', {})
        temperatures = hourly.get('temperature', [])
        skycon = hourly.get('skycon', [])

        if not temperatures:
            return "无可用的小时级预报数据"

        # 按天聚合数据
        daily_data = {}
        for i, temp_data in enumerate(temperatures[:days * 24]):
            try:
                timestamp = temp_data['datetime']
                if isinstance(timestamp, str):
                    hour_date = dateparser.parse(timestamp).date()
                else:
                    hour_date = datetime.fromtimestamp(timestamp).date()

                if hour_date not in daily_data:
                    daily_data[hour_date] = {
                        'temps': [],
                        'conditions': []
                    }

                daily_data[hour_date]['temps'].append(temp_data['value'])

                if i < len(skycon):
                    daily_data[hour_date]['conditions'].append(skycon[i]['value'])

            except Exception as e:
                logger.debug(f"处理小时数据失败: {e}")
                continue

        # 格式化输出
        result = f"🌤️ {location} {days}天天气预报（72小时数据）：\n\n"

        weather_map = {
            'CLEAR_DAY': '晴', 'CLEAR_NIGHT': '晴',
            'PARTLY_CLOUDY_DAY': '多云', 'PARTLY_CLOUDY_NIGHT': '多云',
            'CLOUDY': '阴', 'LIGHT_RAIN': '小雨', 'MODERATE_RAIN': '中雨',
            'HEAVY_RAIN': '大雨', 'LIGHT_SNOW': '小雪', 'MODERATE_SNOW': '中雪'
        }

        for i, (forecast_date, day_data) in enumerate(sorted(daily_data.items())[:days]):
            temps = day_data['temps']
            if not temps:
                continue

            daily_high = max(temps)
            daily_low = min(temps)
            avg_temp = sum(temps) / len(temps)

            # 获取主要天气状况
            conditions = day_data['conditions']
            if conditions:
                main_condition = max(set(conditions), key=conditions.count)
                weather_cn = weather_map.get(main_condition, main_condition)
            else:
                weather_cn = '未知'

            date_str = forecast_date.strftime('%m-%d')
            day_name = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][forecast_date.weekday()]

            result += f"📅 第{i+1}天: {date_str} {day_name}\n"
            result += f"   🌡️ 温度: {daily_high:.1f}°C ~ {daily_low:.1f}°C (平均{avg_temp:.1f}°C)\n"
            result += f"   ☁️ 天气: {weather_cn}\n\n"

        return result

    except Exception as e:
        logger.error(f"格式化小时预报失败: {e}")
        return f"格式化天气预报数据时发生错误。"


def _format_daily_forecast(daily_data: Dict, location: str, days: int) -> str:
    """格式化日级预报数据"""
    try:
        daily = daily_data.get('result', {}).get('daily', {})
        temperatures = daily.get('temperature', [])
        skycon = daily.get('skycon', [])

        if not temperatures:
            return "无可用的日级预报数据"

        result = f"🌤️ {location} {days}天天气预报（日级数据）：\n\n"

        weather_map = {
            'CLEAR_DAY': '晴', 'CLEAR_NIGHT': '晴',
            'PARTLY_CLOUDY_DAY': '多云', 'PARTLY_CLOUDY_NIGHT': '多云',
            'CLOUDY': '阴', 'LIGHT_RAIN': '小雨', 'MODERATE_RAIN': '中雨',
            'HEAVY_RAIN': '大雨', 'LIGHT_SNOW': '小雪', 'MODERATE_SNOW': '中雪'
        }

        for i in range(min(days, len(temperatures) - 1)):
            try:
                temp_data = temperatures[i]
                forecast_date = date.fromtimestamp(temp_data['date'])

                daily_high = temp_data['max']
                daily_low = temp_data['min']

                # 获取天气状况
                if i < len(skycon):
                    weather_condition = skycon[i].get('value', 'unknown')
                    weather_cn = weather_map.get(weather_condition, weather_condition)
                else:
                    weather_cn = '未知'

                date_str = forecast_date.strftime('%m-%d')
                day_name = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][forecast_date.weekday()]

                result += f"📅 第{i+1}天: {date_str} {day_name}\n"
                result += f"   🌡️ 温度: {daily_high:.1f}°C ~ {daily_low:.1f}°C\n"
                result += f"   ☁️ 天气: {weather_cn}\n\n"

            except Exception as e:
                logger.debug(f"处理日级数据失败: {e}")
                continue

        return result + "\n注: 使用日级预报数据，精度略低于72小时小时级预报。"

    except Exception as e:
        logger.error(f"格式化日级预报失败: {e}")
        return f"格式化天气预报数据时发生错误。"


@tool
def get_weather_by_date(location: str, date_str: str) -> str:
    """
    获取指定位置和日期的天气信息

    Args:
        location: 位置名称，如"杭州"、"北京"、"余杭区"等
        date_str: 日期字符串，支持格式：
                - 相对日期: "明天"、"后天"、"今天"、"昨天"
                - 绝对日期: "2024-12-25"

    Returns:
        指定日期的详细天气信息或预报
    """
    try:
        # 解析日期
        target_date = _parse_date_input(date_str)
        today = date.today()

        # 获取坐标
        coords = get_coordinates(location)
        longitude, latitude = coords

        weather_client = get_weather_client()

        if target_date == today:
            # 今天：获取实时天气
            weather_data = weather_client.get_realtime_weather(longitude, latitude)
            if weather_data:
                return _format_current_weather(weather_data, location, "今天")
        else:
            # 其他日期：获取预报
            days_diff = (target_date - today).days
            if 1 <= days_diff <= 7:
                forecast_data = weather_client.get_hourly_forecast(longitude, latitude, days_diff * 24)
                if forecast_data:
                    return _format_date_forecast(forecast_data, location, target_date)

        return f"抱歉，无法获取{location}在{date_str}的天气数据。"

    except ValueError as e:
        return f"日期格式错误: {str(e)}"
    except Exception as e:
        logger.error(f"获取指定日期天气失败: {e}")
        return f"获取{location}在{date_str}的天气信息时发生错误，请稍后重试。"


def _parse_date_input(date_input: str) -> date:
    """解析日期输入"""
    if not date_input:
        return date.today()

    date_input = date_input.strip().lower()

    # 相对日期映射
    relative_dates = {
        'today': '今天', 'tomorrow': '明天', 'yesterday': '昨天',
        '今天': '今天', '明天': '明天', '昨天': '昨天', '后天': '后天'
    }

    if date_input in relative_dates:
        if date_input in ['today', '今天']:
            return date.today()
        elif date_input in ['tomorrow', '明天']:
            return date.today() + timedelta(days=1)
        elif date_input in ['yesterday', '昨天']:
            return date.today() - timedelta(days=1)
        elif date_input in ['后天']:
            return date.today() + timedelta(days=2)

    # 尝试解析绝对日期
    try:
        return datetime.strptime(date_input, '%Y-%m-%d').date()
    except ValueError:
        try:
            # 尝试其他格式
            return datetime.strptime(date_input, '%m-%d').date().replace(year=date.today().year)
        except ValueError:
            raise ValueError(f"无法解析日期格式: {date_input}")


def _format_current_weather(weather_data: Dict, location: str, time_desc: str) -> str:
    """格式化当前天气数据"""
    realtime = weather_data.get('result', {}).get('realtime', {})

    temperature = realtime.get('temperature', 0)
    humidity = realtime.get('humidity', 0)
    weather_skycon = realtime.get('skycon', 'unknown')

    weather_map = {
        'CLEAR_DAY': '晴朗', 'CLEAR_NIGHT': '晴朗（夜间）',
        'PARTLY_CLOUDY_DAY': '多云', 'PARTLY_CLOUDY_NIGHT': '多云（夜间）',
        'CLOUDY': '阴天', 'LIGHT_RAIN': '小雨', 'MODERATE_RAIN': '中雨',
        'HEAVY_RAIN': '大雨', 'LIGHT_SNOW': '小雪'
    }

    weather_cn = weather_map.get(weather_skycon, weather_skycon)

    return f"🌤️ {location} {time_desc}天气：\n温度: {temperature}°C，湿度: {humidity}%，天气: {weather_cn}"


def _format_date_forecast(forecast_data: Dict, location: str, target_date: date) -> str:
    """格式化指定日期的预报"""
    hourly = forecast_data.get('result', {}).get('hourly', {})
    temperatures = hourly.get('temperature', [])
    skycon = hourly.get('skycon', [])

    if not temperatures:
        return f"无{target_date}的预报数据"

    # 查找目标日期的数据
    target_temps = []
    target_conditions = []

    for i, temp_data in enumerate(temperatures):
        try:
            timestamp = temp_data['datetime']
            if isinstance(timestamp, str):
                hour_date = dateparser.parse(timestamp).date()
            else:
                hour_date = datetime.fromtimestamp(timestamp).date()

            if hour_date == target_date:
                target_temps.append(temp_data['value'])
                if i < len(skycon):
                    target_conditions.append(skycon[i]['value'])
        except:
            continue

    if not target_temps:
        return f"无{target_date}的预报数据"

    # 计算统计信息
    daily_high = max(target_temps)
    daily_low = min(target_temps)
    avg_temp = sum(target_temps) / len(target_temps)

    # 获取主要天气状况
    if target_conditions:
        main_condition = max(set(target_conditions), key=target_conditions.count)
        weather_map = {
            'CLEAR_DAY': '晴', 'CLEAR_NIGHT': '晴',
            'PARTLY_CLOUDY_DAY': '多云', 'PARTLY_CLOUDY_NIGHT': '多云',
            'CLOUDY': '阴', 'LIGHT_RAIN': '小雨', 'MODERATE_RAIN': '中雨',
            'HEAVY_RAIN': '大雨'
        }
        weather_cn = weather_map.get(main_condition, main_condition)
    else:
        weather_cn = '未知'

    date_str = target_date.strftime('%m月%d日')
    day_name = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][target_date.weekday()]

    return f"🌤️ {location} {date_str} {day_name}天气预报：\n温度: {daily_high:.1f}°C ~ {daily_low:.1f}°C (平均{avg_temp:.1f}°C)\n天气: {weather_cn}"


# 工具列表，用于agent创建
WEATHER_TOOLS = [
    get_current_weather,
    get_weather_forecast,
    get_weather_by_date
]