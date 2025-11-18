#!/usr/bin/env python3
"""
钓鱼推荐工具模块
基于天气条件分析最佳的钓鱼时间
"""

from typing import Optional, Dict, Any
from langchain_core.tools import tool
import logging

from core.tools.fishing_tool_core import find_best_fishing_time

logger = logging.getLogger(__name__)


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