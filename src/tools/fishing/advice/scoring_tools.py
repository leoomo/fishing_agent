#!/usr/bin/env python3
"""
钓鱼评分工具模块
基于增强钓鱼评分算法的LangChain工具包装器
"""

from typing import Dict, Any, Optional
from langchain_core.tools import tool
import logging

from .fishing_scorer import EnhancedFishingScorer, FishingScore

logger = logging.getLogger(__name__)

# 创建全局评分器实例
scorer = EnhancedFishingScorer()

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
        # 执行钓鱼评分
        score_result = scorer.calculate_fishing_score(
            location=location,
            temperature=temperature,
            weather_condition=weather_condition,
            wind_speed=wind_speed,
            humidity=humidity,
            pressure=pressure
        )

        # 格式化结果
        response = f"🎣 {location} 钓鱼条件分析报告\n"
        response += "=" * 50 + "\n\n"

        # 综合评分
        response += f"🏆 **综合评分**: {score_result.overall:.1f}/100\n"

        # 评分等级
        if score_result.overall >= 85:
            grade = "🌟 优秀"
        elif score_result.overall >= 70:
            grade = "👍 良好"
        elif score_result.overall >= 55:
            grade = "👌 一般"
        else:
            grade = "⚠️ 较差"
        response += f"**等级**: {grade}\n\n"

        # 各维度评分
        response += f"📊 **各维度评分**:\n"
        response += f"• 🌡️ 温度评分: {score_result.temperature:.1f}/100\n"
        response += f"• ☁️ 天气评分: {score_result.weather:.1f}/100\n"
        response += f"• 💨 风力评分: {score_result.wind:.1f}/100\n"
        response += f"• 🌀 气压评分: {score_result.pressure:.1f}/100\n"
        response += f"• 💧 湿度评分: {score_result.humidity:.1f}/100\n"
        response += f"• 📅 季节评分: {score_result.seasonal:.1f}/100\n"
        response += f"• 🌙 月相评分: {score_result.lunar:.1f}/100\n\n"

        # 权重分析
        response += f"⚖️ **权重分配**:\n"
        for factor, weight in score_result.breakdown.items():
            response += f"• {factor}: {weight:.1%}\n"
        response += "\n"

        # 钓鱼建议
        if score_result.overall >= 70:
            response += "💡 **钓鱼建议**: 🎯 条件理想，适合出钓！\n"
            response += "• 推荐时段: 早上5-9点、傍晚18-21点\n"
            response += "• 建议钓点: 根据目标鱼种选择合适水域\n"
            response += "• 装备推荐: 根据天气条件调整线组和饵料\n"
        elif score_result.overall >= 55:
            response += "💡 **钓鱼建议**: 👍 条件较好，可以出钓\n"
            response += "• 选择性时段: 关注天气变化，抓住最佳时机\n"
            response += "• 注意事项: 携带适当装备应对天气变化\n"
        else:
            response += "💡 **钓鱼建议**: ⚠️ 条件一般，建议谨慎\n"
            response += "• 推迟计划: 等待更合适的天气条件\n"
            response += "• 如需出钓: 选择有遮挡的钓点，做好安全防护\n"

        response += f"\n📅 分析时间: {score_result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

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

        # 季节性建议
        seasonal_advice = _get_seasonal_advice()
        response += f"📅 **当前季节建议**:\n{seasonal_advice}\n\n"

        # 装备推荐
        equipment_advice = _get_equipment_advice(target_species)
        response += f"🎣 **装备推荐**:\n{equipment_advice}\n\n"

        response += "💡 **重要提醒**: 请关注实时天气变化，确保安全钓鱼"

        return response

    except Exception as e:
        logger.error(f"获取钓鱼洞察失败: {str(e)}")
        return f"❌ 获取洞察失败: {str(e)}"


def _get_location_insights(location: str) -> str:
    """获取地区钓鱼洞察"""
    # 简化的地区洞察逻辑
    insights = {
        "杭州": "西湖、千岛湖等水域资源丰富，适合多种淡水鱼类",
        "北京": "密云、怀柔等水库为主，以鲫鱼、鲤鱼为主",
        "上海": "长江口水域，海淡水鱼类丰富",
        "广州": "珠江流域，热带鱼类活跃",
        "成都": "都江堰、青城山等，水温适宜",
    }

    return insights.get(location, f"{location}地区水域条件良好，适合钓鱼活动")


def _get_species_insights(species: str) -> str:
    """获取目标鱼种钓法建议"""
    species_advice = {
        "鲈鱼": "• 最佳时段: 清晨和傍晚\n• 推荐钓法: 路亚钓法\n• 偏好水域: 水草边缘、障碍物附近",
        "鲫鱼": "• 最佳时段: 全天均可\n• 推荐钓法: 传统钓法、台钓\n• 偏好饵料: 蚯蚓、面饵",
        "鲤鱼": "• 最佳时段: 早晨和傍晚\n• 推荐钓法: 海竿钓法\n• 偏好水域: 底层水域",
        "草鱼": "• 最佳时段: 夏季早晚\n• 推荐钓法: 浮钓、底钓\n• 偏好食物: 植物性饵料"
    }

    return species_advice.get(species, "• 根据鱼种习性选择合适钓法和饵料\n• 关注目标鱼的活动规律\n• 选择合适的钓点和水层")


def _get_seasonal_advice() -> str:
    """获取季节性钓鱼建议"""
    from datetime import datetime
    month = datetime.now().month

    if 3 <= month <= 5:  # 春季
        return "• 水温回升，鱼类开始活跃\n• 浅滩水域钓鱼效果好\n• 适合多种钓法"
    elif 6 <= month <= 8:  # 夏季
        return "• 早晚时段为黄金时间\n• 深水区避暑效果好\n• 注意防暑降温"
    elif 9 <= month <= 11:  # 秋季
        return "• 鱼类进食旺盛，钓鱼最佳季节\n• 全天都适合钓鱼\n• 适合多种目标鱼种"
    else:  # 冬季
        return "• 鱼类活动减少，选择深水区\n• 中午时段相对较好\n• 需要耐心和技巧"


def _get_equipment_advice(target_species: str = None) -> str:
    """获取装备推荐"""
    if target_species == "鲈鱼":
        return "• 鱼竿: 中调路亚竿，2.1-2.4米\n• 鱼线: 0.8-1.5号PE线\n• 假饵: 米诺、波爬、软虫"
    elif target_species == "鲫鱼":
        return "• 鱼竿: 软调鲫鱼竿，3.6-5.4米\n• 鱼线: 0.4-1.0号尼龙线\n• 饵料: 蚯蚓、商品饵"
    else:
        return "• 鱼竿: 根据目标鱼选择合适调性\n• 鱼线: 匹配鱼竿和目标鱼大小\n• 辅助工具: 抄网、鱼护、饵料盒"