#!/usr/bin/env python3
"""
钓鱼评分工具模块
简化的钓鱼条件分析工具，基于天气数据进行分析
"""

from typing import Dict, Any, Optional
from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)


@tool
def analyze_fishing_conditions(
    location: str,
    temperature: float = None,
    weather_condition: str = None,
    wind_speed: float = None,
    humidity: float = None,
    pressure: float = None
) -> str:
    """分析钓鱼条件，提供专业的钓鱼评分和建议

    Args:
        location: 地区名称
        temperature: 温度(摄氏度)，如未提供将使用默认值
        weather_condition: 天气状况，如"晴"、"多云"、"阴"、"小雨"等
        wind_speed: 风速(km/h)，如未提供将使用默认值
        humidity: 湿度(百分比)，如未提供将使用默认值
        pressure: 气压(hPa)，如未提供将使用默认值

    Returns:
        详细的钓鱼条件分析报告，包含各维度评分和综合建议

    Examples:
        analyze_fishing_conditions("杭州", 22, "多云", 8, 65, 1013)
        analyze_fishing_conditions("北京", weather_condition="晴", wind_speed=12)
    """
    try:
        # 使用默认值处理空参数
        temp = temperature or 20.0
        condition = weather_condition or "多云"
        wind = wind_speed or 5.0
        humid = humidity or 60.0
        press = pressure or 1013.0

        # 简化的评分算法
        temp_score = _calculate_temperature_score(temp)
        weather_score = _calculate_weather_score(condition)
        wind_score = _calculate_wind_score(wind)
        humidity_score = _calculate_humidity_score(humid, press)
        pressure_score = _calculate_pressure_score(press)

        # 计算综合评分
        weights = {'temperature': 0.3, 'weather': 0.25, 'wind': 0.2, 'humidity': 0.15, 'pressure': 0.1}
        overall_score = (
            temp_score * weights['temperature'] +
            weather_score * weights['weather'] +
            wind_score * weights['wind'] +
            humidity_score * weights['humidity'] +
            pressure_score * weights['pressure']
        )

        # 格式化结果
        response = f"🎣 {location} 钓鱼条件分析报告\n"
        response += "=" * 50 + "\n\n"

        # 总体评分
        if overall_score >= 85:
            grade = "🌟 优秀"
            recommendation = "非常适合钓鱼"
        elif overall_score >= 70:
            grade = "👍 良好"
            recommendation = "适合钓鱼"
        elif overall_score >= 55:
            grade = "👌 一般"
            recommendation = "可以钓鱼，需注意时机"
        else:
            grade = "👎 较差"
            recommendation = "不太适合钓鱼"

        response += f"🏆 **综合评分**: {overall_score:.1f}/100\n"
        response += f"**等级**: {grade}\n"
        response += f"**建议**: {recommendation}\n\n"

        # 各维度评分
        response += f"📊 **各维度评分**:\n"
        response += f"• 🌡️ 温度: {temp_score:.1f}/100 ({temp}°C)\n"
        response += f"• ☁️ 天气: {weather_score:.1f}/100 ({condition})\n"
        response += f"• 💨 风力: {wind_score:.1f}/100 ({wind}km/h)\n"
        response += f"• 💧 湿度: {humidity_score:.1f}/100 ({humid}%)\n"
        response += f"• 🌀 气压: {pressure_score:.1f}/100 ({press}hPa)\n"

        # 具体建议
        response += f"\n💡 **钓鱼建议**:\n"
        if temp_score >= 70:
            response += "• ✅ 温度条件适宜（15-25°C最佳）\n"
        if weather_score >= 70:
            response += "• ✅ 天气状况良好（多云、阴天最佳）\n"
        if wind_score >= 70:
            response += "• ✅ 风力条件适中（<15km/h）\n"
        if pressure_score >= 70:
            response += "• ✅ 气压条件稳定\n"

        # 最佳时间建议
        response += f"\n🎯 **推荐时段**: 早上5-9点或傍晚18-21点\n"

        return response

    except Exception as e:
        logger.error(f"钓鱼条件分析失败: {str(e)}")
        return f"❌ 分析失败: {str(e)}"


@tool
def get_fishing_insights(
    location: str,
    target_species: str = None
) -> str:
    """获取钓鱼洞察和建议

    Args:
        location: 地区名称
        target_species: 目标鱼种，如"鲈鱼"、"鲫鱼"、"鲤鱼"等

    Returns:
        专业的钓鱼洞察报告，包含当地钓鱼特点和针对性建议

    Examples:
        get_fishing_insights("杭州", "鲈鱼")
        get_fishing_insights("北京")
    """
    try:
        # 基于地区和目标鱼种提供洞察
        response = f"🎯 {location} 钓鱼洞察报告\n"
        response += "=" * 50 + "\n\n"

        # 地区特点分析
        location_insights = _get_location_insights(location)
        response += f"📍 **地区特点**:\n{location_insights}\n\n"

        # 如果指定了目标鱼种
        if target_species:
            species_insights = _get_species_insights(target_species)
            response += f"🐟 **{target_species}钓法建议**:\n{species_insights}\n\n"

        # 通用钓鱼建议
        response += "💡 **通用建议**:\n"
        response += "• 选择清晨或傍晚时段，避开正午高温\n"
        response += "• 根据天气调整钓法和钓点\n"
        response += "• 注意安全，配备必要装备\n"
        response += "• 遵守当地钓鱼规定\n"

        return response

    except Exception as e:
        logger.error(f"钓鱼洞察分析失败: {str(e)}")
        return f"❌ 洞察分析失败: {str(e)}"


def _calculate_temperature_score(temp: float) -> float:
    """计算温度评分"""
    if 15 <= temp <= 25:
        return 95.0
    elif 10 <= temp < 15 or 25 < temp <= 30:
        return 75.0
    elif 5 <= temp < 10 or 30 < temp <= 35:
        return 55.0
    else:
        return 25.0


def _calculate_weather_score(condition: str) -> float:
    """计算天气评分"""
    condition = condition.lower()
    if condition in ['多云', '阴', '小雨']:
        return 95.0
    elif condition in ['晴', '雾']:
        return 80.0
    elif condition in ['中雨', '大雨']:
        return 40.0
    else:
        return 60.0


def _calculate_wind_score(wind: float) -> float:
    """计算风力评分"""
    if wind < 10:
        return 95.0
    elif 10 <= wind < 15:
        return 75.0
    elif 15 <= wind < 20:
        return 50.0
    else:
        return 25.0


def _calculate_humidity_score(humidity: float, pressure: float) -> float:
    """计算湿度评分"""
    if 40 <= humidity <= 70:
        return 85.0
    elif 30 <= humidity < 40 or 70 < humidity <= 80:
        return 70.0
    else:
        return 50.0


def _calculate_pressure_score(pressure: float) -> float:
    """计算气压评分"""
    if 1000 <= pressure <= 1020:
        return 85.0
    elif 990 <= pressure < 1000 or 1020 < pressure <= 1030:
        return 70.0
    else:
        return 50.0


def _get_location_insights(location: str) -> str:
    """获取地区钓鱼洞察"""
    insights_map = {
        '杭州': '西湖水域丰富，适合鲫鱼、鲤鱼、草鱼等淡水鱼种',
        '北京': '水库和公园湖泊较多，以鲫鱼、鲤鱼为主',
        '上海': '黄浦江水系和人工湖，资源相对丰富',
        '广州': '珠江水系，热带鱼种较多，气候温暖',
        '成都': '都江堰水系，水质清澈，鱼类资源丰富'
    }

    return insights_map.get(location, f'该地区钓鱼资源需要进一步了解，建议咨询当地钓友')


def _get_species_insights(species: str) -> str:
    """获取鱼种钓法建议"""
    species_map = {
        '鲫鱼': '适合底钓，使用蚯蚓、面团等天然饵料，选择近岸浅水区',
        '鲤鱼': '适合底钓和中层钓法，使用玉米、面包等饵料',
        '鲈鱼': '适合路亚钓法，使用拟饵，选择清晨和傍晚活跃时段',
        '草鱼': '适合浮钓，使用草类饵料，选择水草丰富区域',
        '鲢鱼': '适合浮钓，使用酸味饵料，选择上层水域'
    }

    return species_map.get(species, f'该鱼种的钓法建议需要进一步了解')