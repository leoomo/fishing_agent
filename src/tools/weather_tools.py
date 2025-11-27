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
    from ..utils.date_utils import parse_date_input, parse_dates_list, format_date, get_weekday_cn
except ImportError:
    # 回退到绝对导入
    from utils.coordinate_utils import get_coordinates
    from utils.api_client import get_weather_client
    from utils.cache import cache
    from utils.date_utils import parse_date_input, parse_dates_list, format_date, get_weekday_cn

logger = logging.getLogger(__name__)


@tool
def get_weather(location: str, dates: list = None) -> str:
    """
    获取指定位置的天气信息（纯天气查询专用工具）

    ⚠️ 重要提示：
    - ✅ 仅用于纯天气查询（用户未提及"钓鱼"关键词）
    - ❌ 如果用户提到"钓鱼"，必须改用 query_fishing_recommendation 工具
    - ❌ 绝对禁止与 query_fishing_recommendation 同时调用

    Args:
        location: 位置名称，如"杭州"、"北京"、"余杭区"等
        dates: 日期列表，支持：
              - 单日: ["今天"] 或 ["2024-12-25"]
              - 多日: ["今天", "明天", "后天"]
              - 空值/None: 默认["今天"]

    Returns:
        - 单日: 详细的当日天气信息
        - 多日: 多天天气预报表格

    ✅ 正确用法示例:
        "杭州明天天气如何？" → get_weather("杭州", ["明天"])
        "北京未来三天天气" → get_weather("北京", ["今天","明天","后天"])

    ❌ 错误用法（应使用 query_fishing_recommendation）:
        "杭州明天钓鱼天气" → 不要调用此工具！
        "今天余杭区钓鱼怎么样" → 不要调用此工具！
    """
    try:
        # 参数标准化
        if not dates:
            dates = ["今天"]

        # 限制最多7天
        if len(dates) > 7:
            return "❌ 最多支持查询7天的天气"

        # 获取坐标
        coords = get_coordinates(location)
        longitude, latitude = coords

        weather_client = get_weather_client()

        # 根据日期数量分发逻辑
        if len(dates) == 1:
            return _single_day_weather(location, dates[0], weather_client, longitude, latitude)
        else:
            return _multi_day_weather(location, dates, weather_client, longitude, latitude)

    except ValueError as e:
        return f"位置错误: {str(e)}"
    except Exception as e:
        logger.error(f"获取天气失败: {e}")
        return f"获取{location}天气时发生错误，请稍后重试。"


def _single_day_weather(location: str, date_str: str, weather_client, longitude: float, latitude: float) -> str:
    """单日天气查询"""
    target_date = parse_date_input(date_str)
    today = date.today()

    if target_date.date() == today:
        # 今天：获取实时天气
        weather_data = weather_client.get_realtime_weather(longitude, latitude)
        if weather_data:
            return _format_current_weather(weather_data, location, "今天")
    else:
        # 其他日期：获取预报
        days_diff = (target_date.date() - today).days
        if 1 <= days_diff <= 7:
            forecast_data = weather_client.get_hourly_forecast(longitude, latitude, days_diff * 24)
            if forecast_data:
                return _format_date_forecast(forecast_data, location, target_date.date())

    return f"抱歉，无法获取{location}在{date_str}的天气数据。"


def _multi_day_weather(location: str, dates: list, weather_client, longitude: float, latitude: float) -> str:
    """多日天气查询"""
    # 解析日期列表
    parsed_dates = parse_dates_list(dates)
    days = len(parsed_dates)

    # 优先尝试hourly预报
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
    get_weather
]