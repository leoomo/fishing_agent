#!/usr/bin/env python3
"""
LangChain 工具函数 - 同步版本
支持日期时间查询和时间粒度细化查询
"""

from typing import Optional, Dict, Any
from langchain_core.tools import tool
import logging

from tools.weather_tool_sync import WeatherTool
from tools.fishing_analyzer_sync import find_best_fishing_time

logger = logging.getLogger(__name__)

# 创建全局天气工具实例
weather_tool = WeatherTool()

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


# 原有的通用天气查询工具，保持向后兼容
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


def _parse_weather_summaries_sync(weather_summaries: dict) -> dict:
    """解析天气汇总数据，提取关键信息（同步版本）

    Args:
        weather_summaries: 原始天气汇总数据

    Returns:
        解析后的天气数据，包含条件、温度、风力等信息
    """
    conditions = []
    temps = []
    wind_speeds = []

    for period, weather in weather_summaries.items():
        if weather and weather != "无天气数据":
            # 更灵活的解析方式
            parts = weather.split()

            # 提取天气状况（寻找包含天气关键词的部分）
            condition = "未知"
            weather_keywords = ['晴', '多云', '阴', '雨', '雪', '雾', '霾', 'CLOUDY', 'CLEAR', 'RAIN', 'SNOW']
            for part in parts:
                if any(keyword in part.upper() for keyword in weather_keywords):
                    condition = part
                    break
            conditions.append(condition)

            # 提取温度（查找包含°C的部分）
            temp = 20.0  # 默认值
            for part in parts:
                if '°C' in part:
                    try:
                        temp = float(part.replace('°C', ''))
                        break
                    except ValueError:
                        continue
            temps.append(temp)

            # 提取风力（查找包含km/h的部分）
            wind_speed = 10.0  # 默认值
            for part in parts:
                # 优先处理 "风速12.7km/h" 这种格式
                if '风速' in part and 'km/h' in part:
                    try:
                        wind_speed = float(part.replace('风速', '').replace('km/h', ''))
                        break
                    except ValueError:
                        continue
                # 处理单独的 "12.7km/h" 格式
                elif 'km/h' in part and any(char.isdigit() for char in part):
                    try:
                        wind_speed = float(part.replace('km/h', ''))
                        break
                    except ValueError:
                        continue
            wind_speeds.append(wind_speed)

    return {
        'conditions': conditions,
        'temps': temps,
        'wind_speeds': wind_speeds,
        'has_data': len(conditions) > 0
    }


def _format_overall_weather_sync(parsed_weather: dict) -> str:
    """格式化总体天气情况（同步版本）

    Args:
        parsed_weather: 解析后的天气数据

    Returns:
        格式化的总体天气情况字符串
    """
    if not parsed_weather['has_data']:
        return ""

    conditions = parsed_weather['conditions']
    temps = parsed_weather['temps']
    wind_speeds = parsed_weather['wind_speeds']

    # 生成天气概述
    if conditions:
        # 统计主要天气状况
        condition_counts = {}
        for cond in conditions:
            condition_counts[cond] = condition_counts.get(cond, 0) + 1
        main_condition = max(condition_counts, key=condition_counts.get)

        # 计算温度和风力范围
        min_temp = min(temps)
        max_temp = max(temps)
        avg_temp = sum(temps) / len(temps)
        avg_wind = sum(wind_speeds) / len(wind_speeds)

        response = f"• **天气状况**: 以{main_condition}为主，{'变化较大' if len(set(conditions)) > 2 else '相对稳定'}\n"
        response += f"• **温度范围**: {min_temp:.1f}°C - {max_temp:.1f}°C (平均 {avg_temp:.1f}°C)\n"
        response += f"• **风力情况**: 平均 {avg_wind:.1f}km/h ({'微风' if avg_wind < 10 else '轻风' if avg_wind < 15 else '中风'})\n"

        # 天气适宜性评价
        temp_suitable = 15 <= avg_temp <= 25
        wind_suitable = avg_wind < 15
        condition_suitable = main_condition in ['晴', '多云', '阴', '小雨']

        if temp_suitable and wind_suitable and condition_suitable:
            response += "• **总体评价**: 🌟 天气条件良好，适合钓鱼\n"
        elif temp_suitable and wind_suitable:
            response += "• **总体评价**: 👍 天气条件基本适合钓鱼\n"
        else:
            response += "• **总体评价**: 👌 天气条件一般，需注意选择合适时机\n"

        return response

    return ""


def _format_time_slots_sync(best_slots: list, weather_summaries: dict) -> str:
    """格式化时间段推荐（同步版本）

    Args:
        best_slots: 最佳时间段列表
        weather_summaries: 天气汇总数据

    Returns:
        格式化的时间段推荐字符串
    """
    if not best_slots:
        return ""

    response = "🏆 **推荐时间段**:\n"
    for i, (period, score) in enumerate(best_slots, 1):
        score_emoji = "🌟" if score >= 80 else "👍" if score >= 60 else "👌"
        weather_info = weather_summaries.get(period, "无天气数据")
        response += f"  {i}. {score_emoji} {score:.1f}分 - {period} {weather_info}\n"
    response += "\n"

    return response


def _format_fishing_tips_sync() -> str:
    """格式化钓鱼小贴士（同步版本）

    Returns:
        钓鱼小贴士字符串
    """
    response = "\n🎯 **钓鱼小贴士**:\n"
    response += "• 最佳温度: 15-25°C\n"
    response += "• 偏好天气: 多云、阴天或小雨\n"
    response += "• 理想时段: 早上(5-9点)和傍晚(18-21点)\n"
    response += "• 避免强风(>15km/h)和恶劣天气"

    return response


def _parse_fishing_result_sync(result: str) -> dict:
    """解析钓鱼分析结果（同步版本）

    Args:
        result: 分析结果的JSON字符串

    Returns:
        解析后的数据字典
    """
    import json
    try:
        data = json.loads(result)
        if "error" in data:
            return {"error": data['error']}
        return data
    except json.JSONDecodeError:
        return {"error": f"结果解析失败: {result}"}


def _build_fishing_response_sync(location: str, data: dict) -> str:
    """构建钓鱼推荐的完整响应（同步版本）

    Args:
        location: 地区名称
        data: 解析后的钓鱼数据

    Returns:
        完整的钓鱼推荐响应字符串
    """
    if "error" in data:
        return f"❌ 钓鱼分析失败: {data['error']}"

    # 格式化推荐结果
    response = f"🎣 {location} {data.get('date', '明天')}钓鱼时间推荐\n"
    response += "=" * 50 + "\n\n"

    # 总体天气情况概述
    weather_summaries = data.get('weather_summaries', {})
    if weather_summaries:
        parsed_weather = _parse_weather_summaries_sync(weather_summaries)
        overall_weather = _format_overall_weather_sync(parsed_weather)
        if overall_weather:
            response += "🌤️ **总体天气情况**:\n"
            response += overall_weather
            response += "\n"

    # 最佳时间段
    best_slots = data.get('best_time_slots', [])
    time_slots = _format_time_slots_sync(best_slots, weather_summaries)
    response += time_slots

    # 详细分析
    if data.get('detailed_analysis'):
        response += f"📊 **详细分析**:\n{data['detailed_analysis']}\n\n"

    # 总结建议
    if data.get('summary'):
        response += f"💡 **钓鱼建议**:\n{data['summary']}\n"

    # 添加钓鱼小贴士
    response += _format_fishing_tips_sync()

    return response


@tool
def query_fishing_recommendation(location: str, date: str = None) -> str:
    """查询钓鱼时间推荐，基于天气条件分析最佳的钓鱼时间

    Args:
        location: 地区名称，如"北京"、"上海"、"余杭区"、"临安"等
        date: 日期 (可选，格式为YYYY-MM-DD，默认为明天)

    Returns:
        详细的钓鱼时间推荐，包括最佳时间段、天气分析和钓鱼建议

    Examples:
        query_fishing_recommendation("余杭区")
        query_fishing_recommendation("临安", "2024-12-25")
        query_fishing_recommendation("杭州西湖", "tomorrow")
    """
    try:
        # 执行钓鱼分析（同步版本）
        result = find_best_fishing_time(location, date)

        # 解析结果
        data = _parse_fishing_result_sync(result)

        # 构建响应
        return _build_fishing_response_sync(location, data)

    except Exception as e:
        logger.error(f"查询钓鱼推荐失败: {str(e)}")
        return f"❌ 钓鱼推荐查询失败: {str(e)}"


# 工具列表，用于LangChain智能体
WEATHER_TOOLS_SYNC = [
    query_current_weather,
    query_weather_by_date,
    query_weather_by_datetime,
    query_hourly_forecast,
    query_time_period_weather,
    query_fishing_recommendation,  # 新增钓鱼推荐工具
]


def get_weather_tools_sync() -> list:
    """获取所有天气查询工具

    Returns:
        LangChain工具列表
    """
    return WEATHER_TOOLS_SYNC


def create_weather_tool_system_prompt() -> str:
    """创建天气工具的系统提示词

    Returns:
        系统提示词字符串
    """
    return """你可以使用以下天气查询工具来回答用户的天气相关问题:

可用的工具:
1. query_current_weather(place) - 查询当前天气
2. query_weather_by_date(place, date) - 查询指定日期天气
3. query_weather_by_datetime(place, datetime) - 查询指定时间段天气
4. query_hourly_forecast(place, hours) - 查询小时级预报
5. query_time_period_weather(place, date, time_period) - 查询指定日期和时间段的天气
6. query_fishing_recommendation(location, date) - 钓鱼时间推荐和天气分析

支持的日期格式:
- 相对日期: "today", "tomorrow", "yesterday", "明天", "昨天", "3天后", "上周三"
- 绝对日期: "2024-12-25", "2025-01-01"
- 中文日期: "2024年12月25日", "12月25日"

支持的时间段:
- 早上: 05:00-08:59
- 上午: 09:00-11:59
- 中午: 12:00-13:59
- 下午: 14:00-17:59
- 晚上: 18:00-21:59
- 夜间: 22:00-04:59

钓鱼专用工具说明:
- query_fishing_recommendation: 专门为钓鱼活动设计的智能推荐工具
- 会分析全天的天气条件，找出最适合钓鱼的时间段
- 考虑温度、天气、风力等因素对钓鱼的影响
- 提供专业的钓鱼建议和注意事项

使用指南:
- 当用户问"今天/明天/昨天天气"时，使用query_current_weather或query_weather_by_date
- 当用户问具体时间段的天气时(如"明天上午")，使用query_weather_by_datetime
- 当用户问小时级预报时，使用query_hourly_forecast
- 当用户问钓鱼相关问题时(如"明天钓鱼合适吗"、"什么时候钓鱼好")，使用query_fishing_recommendation
- 当用户问历史天气时，尝试使用query_weather_by_date
- 尽量提供详细和有用的天气信息，包括温度、天气状况、湿度等
- 如果查询失败，向用户说明具体原因

钓鱼专业知识:
- 最佳钓鱼温度: 15-25°C
- 理想天气条件: 多云、阴天或小雨天气
- 最佳钓鱼时段: 早上(5-9点)和傍晚(18-21点)
- 应避免的条件: 强风(>15km/h)、暴雨、极端温度
- 钓鱼活动受温度、天气、风力、湿度等因素综合影响
"""