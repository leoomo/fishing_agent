#!/usr/bin/env python3
"""
天气工具模块 - LangChain 工具函数
支持日期时间查询和时间粒度细化查询
"""

from typing import Optional, Dict, Any
from langchain_core.tools import tool
import logging

# 修复导入路径
from ...weather_tool_sync import WeatherTool
from ...fishing_analyzer_sync import find_best_fishing_time

logger = logging.getLogger(__name__)

# 创建全局天气工具实例
weather_tool = WeatherTool()

@tool
def query_current_weather(place: str) -> str:
    """查询当前天气信息

    Args:
        place: 地区名称，如"北京"、"上海"、"广州"等

    Returns:
        当前天气信息字符串，包含温度、天气状况、湿度等详细信息
    """
    try:
        result = weather_tool.execute(
            operation="current_weather",
            location=place
        )

        if result.success:
            data = result.data
            response = f"📍 {place}当前天气:\n"
            response += f"🌡️ 温度: {data.get('temperature', 'N/A')}°C (体感: {data.get('apparent_temperature', 'N/A')}°C)\n"
            response += f"☁️ 天气: {data.get('condition', 'N/A')}\n"
            response += f"💧 湿度: {data.get('humidity', 'N/A')}%\n"
            response += f"🌀 气压: {data.get('pressure', 'N/A')} hPa\n"
            response += f"💨 风速: {data.get('wind_speed', 'N/A')} km/h\n"
            response += f"📝 描述: {data.get('description', 'N/A')}\n"
            response += f"🔗 数据源: {data.get('source', 'N/A')}"

            if result.metadata and result.metadata.get('source') == 'cache':
                response += "\n📌 数据来源: 缓存"

            return response
        else:
            return f"❌ 查询{place}当前天气失败: {result.error}"

    except Exception as e:
        logger.error(f"查询当前天气失败: {str(e)}")
        return f"❌ 查询失败: {str(e)}"


@tool
def query_weather_by_date(place: str, date: str = "today") -> str:
    """查询指定日期的天气信息

    Args:
        place: 地区名称，如"北京"、"上海"、"广州"等
        date: 日期字符串，支持多种格式:
              - 相对日期: "today", "tomorrow", "yesterday", "明天", "昨天", "3天后", "上周三"
              - 绝对日期: "2024-12-25", "2025-01-01"
              - 中文日期: "2024年12月25日", "12月25日"

    Returns:
        格式化的天气信息字符串，包含温度、天气状况、湿度等详细信息

    Examples:
        query_weather_by_date("北京", "tomorrow")
        query_weather_by_date("上海", "2024-12-25")
        query_weather_by_date("广州", "昨天")
    """
    try:
        result = weather_tool.execute(
            operation="weather_by_date",
            location=place,
            date=date
        )

        if result.success:
            data = result.data
            response = f"📅 {place} {data.get('date', date)}的天气信息:\n"
            response += f"🌡️ 温度: {data.get('temperature', 'N/A')}°C\n"
            response += f"☁️ 天气: {data.get('condition', 'N/A')}\n"
            response += f"💧 湿度: {data.get('humidity', 'N/A')}%\n"
            response += f"📝 描述: {data.get('description', 'N/A')}\n"
            response += f"🔗 数据源: {data.get('source', 'N/A')}"

            if result.metadata and result.metadata.get('source') == 'cache':
                response += "\n📌 数据来源: 缓存"

            return response
        else:
            return f"❌ 查询{place}{date}的天气失败: {result.error}"

    except Exception as e:
        logger.error(f"查询指定日期天气失败: {str(e)}")
        return f"❌ 查询失败: {str(e)}"


@tool
def query_weather_by_datetime(place: str, datetime: str) -> str:
    """查询指定日期时间段的天气信息

    Args:
        place: 地区名称，如"北京"、"上海"、"广州"等
        datetime: 日期时间表达式，支持多种格式:
                - 日期+时间段: "明天上午", "后天下午", "周五晚上"
                - 绝对日期+时间段: "2024年12月25日晚上", "2024-12-25上午"
                - 时间段关键词: "早上", "上午", "中午", "下午", "晚上", "夜间"

    Returns:
        格式化的天气信息字符串，包含指定时间段的详细天气信息

    Examples:
        query_weather_by_datetime("北京", "明天上午")
        query_weather_by_datetime("上海", "2024-12-25晚上")
        query_weather_by_datetime("广州", "周五下午")
        query_weather_by_datetime("深圳", "后天早上")
    """
    try:
        result = weather_tool.execute(
            operation="weather_by_datetime",
            location=place,
            datetime_str=datetime
        )

        if result.success:
            data = result.data
            response = f"🕐 {place} {datetime}的天气信息:\n"

            # 如果是时间段聚合数据（使用新的字段名）
            if 'time_period' in data:
                response += f"🌡️ 平均温度: {data.get('temperature', 'N/A')}°C\n"
                response += f"☁️ 天气状况: {data.get('condition', 'N/A')}\n"
                response += f"💧 湿度: {data.get('humidity', 'N/A')}%\n"
                response += f"💨 风速: {data.get('wind_speed', 'N/A')} km/h\n"
                response += f"⏰ 时间段: {data.get('time_period', 'N/A')}\n"
                response += f"📅 日期: {data.get('date', 'N/A')}\n"
                response += f"📊 数据点数: {data.get('hourly_count', 'N/A')}"
            else:
                # 单个时间点数据
                response += f"🌡️ 温度: {data.get('temperature', 'N/A')}°C\n"
                response += f"☁️ 天气: {data.get('condition', 'N/A')}\n"
                response += f"💧 湿度: {data.get('humidity', 'N/A')}%\n"
                response += f"⏰ 时间段: {data.get('time_period', datetime)}"

            response += f"\n📝 描述: {data.get('description', 'N/A')}\n"
            response += f"🔗 数据源: {data.get('source', 'N/A')}"

            if result.metadata and result.metadata.get('source') == 'cache':
                response += "\n📌 数据来源: 缓存"

            return response
        else:
            return f"❌ 查询{place}{datetime}的天气失败: {result.error}"

    except Exception as e:
        logger.error(f"查询指定时间段天气失败: {str(e)}")
        return f"❌ 查询失败: {str(e)}"


@tool
def query_hourly_forecast(place: str, hours: int = 24) -> str:
    """查询小时级天气预报

    Args:
        place: 地区名称，如"北京"、"上海"、"广州"等
        hours: 预报小时数，默认24小时，最大支持48小时

    Returns:
        格式化的小时级天气预报信息，按时间顺序显示

    Examples:
        query_hourly_forecast("北京", 24)
        query_hourly_forecast("上海", 12)
        query_hourly_forecast("广州", 48)
    """
    try:
        result = weather_tool.execute(
            operation="hourly_forecast",
            location=place,
            hours=min(hours, 48)  # 限制最大48小时
        )

        if result.success:
            data = result.data
            response = f"📍 {place} 小时级天气预报 ({data.get('forecast_hours', 0)}小时):\n"
            response += "=" * 50 + "\n"

            hourly_data = data.get('hourly_forecast', [])
            # 只显示前72小时的详细信息，避免信息过多
            display_hours = min(72, len(hourly_data))

            for i, hour_info in enumerate(hourly_data[:display_hours]):
                datetime_str = hour_info.get('datetime', '')
                if datetime_str:
                    # 解析日期时间，只显示时间部分
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                        time_str = dt.strftime('%m-%d %H:%M')
                    except:
                        time_str = datetime_str
                else:
                    time_str = f"第{i+1}小时"

                response += f"🕐 {time_str}: "
                response += f"{hour_info.get('temperature', 'N/A')}°C, "
                response += f"{hour_info.get('condition', 'N/A')}, "
                response += f"💧{hour_info.get('humidity', 'N/A')}%\n"

            if len(hourly_data) > display_hours:
                response += f"... 还有{len(hourly_data) - display_hours}小时预报数据\n"

            response += f"\n🔗 数据源: {data.get('source', 'N/A')}"

            if result.metadata and result.metadata.get('source') == 'cache':
                response += "\n📌 数据来源: 缓存"

            return response
        else:
            return f"❌ 查询{place}小时级预报失败: {result.error}"

    except Exception as e:
        logger.error(f"查询小时级预报失败: {str(e)}")
        return f"❌ 查询失败: {str(e)}"


@tool
def query_time_period_weather(place: str, date: str, time_period: str) -> str:
    """查询指定日期和时间段的天气信息

    Args:
        place: 地区名称，如"北京"、"上海"、"广州"等
        date: 日期字符串，支持"today", "tomorrow", "2024-12-25"等格式
        time_period: 时间段，支持"早上", "上午", "中午", "下午", "晚上", "夜间"

    Returns:
        格式化的天气信息字符串，包含指定时间段的详细天气信息

    Examples:
        query_time_period_weather("北京", "tomorrow", "上午")
        query_time_period_weather("上海", "2024-12-25", "晚上")
        query_time_period_weather("广州", "today", "下午")
    """
    try:
        result = weather_tool.execute(
            operation="time_period_weather",
            location=place,
            date=date,
            time_period=time_period
        )

        if result.success:
            data = result.data
            response = f"🕐 {place} {date} {time_period}的天气信息:\n"

            # 如果是时间段聚合数据
            if 'temperature_avg' in data:
                response += f"🌡️ 温度范围: {data.get('temperature_min', 'N/A')}°C - {data.get('temperature_max', 'N/A')}°C\n"
                response += f"🌡️ 平均温度: {data.get('temperature_avg', 'N/A')}°C\n"
                response += f"☁️ 主要天气: {data.get('condition_primary', 'N/A')}\n"
                response += f"💧 平均湿度: {data.get('humidity_avg', 'N/A')}%\n"
                response += f"💨 平均风速: {data.get('wind_speed_avg', 'N/A')} km/h\n"
            else:
                # 单个时间点数据
                response += f"🌡️ 温度: {data.get('temperature', 'N/A')}°C\n"
                response += f"☁️ 天气: {data.get('condition', 'N/A')}\n"
                response += f"💧 湿度: {data.get('humidity', 'N/A')}%\n"

            response += f"\n📝 描述: {data.get('description', 'N/A')}\n"
            response += f"🔗 数据源: {data.get('source', 'N/A')}"

            if result.metadata and result.metadata.get('source') == 'cache':
                response += "\n📌 数据来源: 缓存"

            return response
        else:
            return f"❌ 查询{place}{date}{time_period}的天气失败: {result.error}"

    except Exception as e:
        logger.error(f"查询时间段天气失败: {str(e)}")
        return f"❌ 查询失败: {str(e)}"