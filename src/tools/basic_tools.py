#!/usr/bin/env python3
"""
基础工具模块 - 简化架构版本

提供基础的通用工具功能，如时间查询、计算、搜索等。
使用LangChain 1.0+最佳实践，移除过度抽象。
"""

from typing import Dict, Any, Optional
from datetime import datetime, date
import logging
from langchain.tools import tool

logger = logging.getLogger(__name__)


@tool
def get_current_time() -> str:
    """
    获取当前时间和日期信息

    Returns:
        当前的详细时间信息，包括日期、时间、星期等
    """
    try:
        now = datetime.now()

        # 获取星期名称
        weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
        weekday = weekdays[now.weekday()]

        result = f"🕐 当前时间信息：\n\n"
        result += f"📅 日期: {now.strftime('%Y年%m月%d日')}\n"
        result += f"📆 星期: {weekday}\n"
        result += f"🕐 时间: {now.strftime('%H:%M:%S')}\n"
        result += f"🌟 完整时间: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"

        return result

    except Exception as e:
        logger.error(f"获取当前时间失败: {e}")
        return f"获取当前时间时发生错误: {str(e)}"


@tool
def calculate_fish_activity(temperature: float, time_of_day: str = "全天") -> str:
    """
    基于温度和时间估算鱼类活跃度

    Args:
        temperature: 水温或气温（摄氏度）
        time_of_day: 时间段，如"早晨"、"上午"、"下午"、"傍晚"、"夜间"、"全天"

    Returns:
        鱼类活跃度分析和建议
    """
    try:
        # 温度评分
        if 15 <= temperature <= 25:
            temp_score = 95
            temp_desc = "非常适宜"
        elif 12 <= temperature < 15 or 25 < temperature <= 28:
            temp_score = 80
            temp_desc = "适宜"
        elif 8 <= temperature < 12 or 28 < temperature <= 32:
            temp_score = 60
            temp_desc = "一般"
        else:
            temp_score = 30
            temp_desc = "不适宜"

        # 时间段评分
        time_scores = {
            "早晨": 95,    # 5:00-9:00
            "上午": 70,    # 9:00-12:00
            "下午": 65,    # 12:00-17:00
            "傍晚": 90,    # 17:00-21:00
            "夜间": 80,    # 21:00-5:00
            "全天": 85     # 平均值
        }

        time_desc_map = {
            "早晨": "觅食高峰期",
            "上午": "活跃度适中",
            "下午": "活跃度下降",
            "傍晚": "觅食高峰期",
            "夜间": "活跃度较高",
            "全天": "整体较好"
        }

        time_score = time_scores.get(time_of_day, 85)
        time_desc = time_desc_map.get(time_of_day, "一般")

        # 综合评分
        overall_score = (temp_score + time_score) / 2

        # 确定活跃度等级
        if overall_score >= 85:
            activity_level = "🔥 非常活跃"
            suggestion = "是钓鱼的绝佳时机，建议立即行动"
        elif overall_score >= 70:
            activity_level = "⭐ 比较活跃"
            suggestion = "钓鱼条件良好，建议出钓"
        elif overall_score >= 55:
            activity_level = "🐟 一般活跃"
            suggestion = "可以钓鱼，需要选择合适的钓点和时机"
        else:
            activity_level = "😴 活跃度低"
            suggestion = "不建议钓鱼，鱼类活动较少"

        result = f"🐟 鱼类活跃度分析\n"
        result += "=" * 40 + "\n\n"
        result += f"🌡️ 温度条件: {temperature}°C - {temp_desc} ({temp_score}/100)\n"
        result += f"🕐 时间条件: {time_of_day} - {time_desc} ({time_score}/100)\n"
        result += f"🏆 综合活跃度: {overall_score:.1f}/100 - {activity_level}\n\n"
        result += f"💡 建议: {suggestion}\n\n"

        # 添加具体建议
        result += "📋 钓鱼策略建议:\n"
        if temp_score >= 80:
            result += "• 温度理想，鱼类新陈代谢旺盛，可积极作钓\n"
        elif temp_score >= 60:
            result += "• 温度适中，建议选择深水区或遮荫处\n"
        else:
            result += "• 温度不佳，建议调整钓法或选择其他时间\n"

        if time_score >= 90:
            result += "• 黄金时间段，鱼类觅食活跃，饵料选择可多样化\n"
        elif time_score >= 70:
            result += "• 良好时间段，注意观察鱼情变化\n"
        else:
            result += "• 活跃度较低，建议使用味型较重的饵料\n"

        return result

    except Exception as e:
        logger.error(f"鱼类活跃度计算失败: {e}")
        return f"计算鱼类活跃度时发生错误: {str(e)}"


@tool
def get_location_coordinates(location: str) -> str:
    """
    获取位置坐标信息

    Args:
        location: 位置名称，如"杭州"、"北京"、"西湖"等

    Returns:
        位置的经纬度坐标信息
    """
    try:
        from ..utils.coordinate_utils import get_coordinates

        coords = get_coordinates(location)
        longitude, latitude = coords

        result = f"📍 位置坐标信息\n"
        result += "=" * 30 + "\n\n"
        result += f"🏞️ 位置名称: {location}\n"
        result += f"🧭 经度: {longitude:.6f}°\n"
        result += f"🌍 纬度: {latitude:.6f}°\n"
        result += f"📋 坐标格式: {longitude:.6f},{latitude:.6f}\n\n"

        # 添加坐标用途说明
        result += "💡 坐标用途:\n"
        result += "• 用于精确的天气预报查询\n"
        result += "• 支持地图导航和定位\n"
        result += "• 便于钓点信息分享\n"

        return result

    except ValueError as e:
        return f"❌ 坐标查询失败: {str(e)}"
    except Exception as e:
        logger.error(f"获取坐标失败: {e}")
        return f"查询{location}坐标时发生错误: {str(e)}"


@tool
def get_fishing_season_advice(month: int = None) -> str:
    """
    获取钓鱼季节性建议

    Args:
        month: 月份（1-12），不指定则使用当前月份

    Returns:
        该月份的钓鱼季节性建议和技巧
    """
    try:
        if month is None:
            month = datetime.now().month

        if not 1 <= month <= 12:
            return "月份参数错误，请输入1-12之间的数字"

        month_names = ['一月', '二月', '三月', '四月', '五月', '六月',
                      '七月', '八月', '九月', '十月', '十一月', '十二月']
        month_name = month_names[month - 1]

        # 季节分类
        if month in [12, 1, 2]:
            season = "冬季"
            season_desc = "寒冷季节，鱼类活动减少"
            tips = [
                "选择向阳避风钓位，深水区为主",
                "使用红虫、蚯蚓等活饵效果好",
                "作钓时间选在上午10点后至下午3点前",
                "注意保暖，携带热水和食物",
                "钓组要灵敏，口轻时及时扬竿"
            ]
        elif month in [3, 4, 5]:
            season = "春季"
            season_desc = "万物复苏，鱼类开始活跃"
            tips = [
                "是钓鱼的黄金季节，鱼类觅食积极",
                "浅滩、岸边、水草区是重点钓位",
                "可用多种饵料，虫饵、面食皆可",
                "早晚时段是黄金钓鱼时间",
                "注意天气变化，春雨前后是最佳时机"
            ]
        elif month in [6, 7, 8]:
            season = "夏季"
            season_desc = "高温季节，鱼类避深水"
            tips = [
                "选择清晨、傍晚、夜间钓鱼效果好",
                "深水区、背阴处、桥下是好钓位",
                "使用清淡饵料，避免小鱼闹钩",
                "注意防暑防晒，携带足够饮水",
                "雷雨天气避免垂钓，确保安全"
            ]
        else:  # 9, 10, 11
            season = "秋季"
            season_desc = "丰收季节，鱼类储备过冬"
            tips = [
                "鱼类进食量大，是钓鱼的绝佳时期",
                "各种钓位都有好的收获，全天可钓",
                "饵料选择多样化，谷物饵效果好",
                "注意天气变化，秋高气爽是最佳时机",
                "可适当延长作钓时间，收获丰富"
            ]

        result = f"🎣 {month_name}钓鱼季节指南\n"
        result += "=" * 40 + "\n\n"
        result += f"🌸 季节: {season} - {season_desc}\n\n"
        result += "📋 钓鱼建议:\n"

        for i, tip in enumerate(tips, 1):
            result += f" {i}. {tip}\n"

        result += f"\n🎯 {month_name}钓鱼策略:\n"

        if season == "春季":
            result += "以追逐鱼为主，钓组要轻，反应要快\n"
        elif season == "夏季":
            result += "以守钓为主，耐心等待，注意小鱼闹钩\n"
        elif season == "秋季":
            result += "追逐守钓皆可，大鱼活跃，装备要结实\n"
        else:  # 冬季
            result += "以守钓为主，细线小钩，口轻及时扬竿\n"

        return result

    except Exception as e:
        logger.error(f"季节建议生成失败: {e}")
        return f"生成钓鱼季节建议时发生错误: {str(e)}"


@tool
def format_distance(distance: float, unit: str = "公里") -> str:
    """
    格式化距离显示

    Args:
        distance: 距离数值
        unit: 单位类型，可选"公里"、"米"、"英里"

    Returns:
        格式化的距离信息
    """
    try:
        # 输入验证
        if distance < 0:
            return "距离不能为负数"

        # 单位转换和格式化
        unit_map = {
            "公里": ("公里", "米", 1000),
            "米": ("米", "公里", 0.001),
            "英里": ("英里", "公里", 1.60934),
            "海里": ("海里", "公里", 1.852)
        }

        if unit not in unit_map:
            return f"不支持的单位: {unit}，支持的单位有: {', '.join(unit_map.keys())}"

        primary_unit, secondary_unit, conversion_factor = unit_map[unit]

        # 格式化主单位
        if distance >= 1000 and primary_unit in ["米"]:
            # 大数值显示为更合适的单位
            converted_distance = distance * conversion_factor
            formatted_distance = f"{converted_distance:.2f}{secondary_unit}"
        elif distance < 1 and primary_unit in ["公里", "英里", "海里"]:
            # 小数值显示为更合适的单位
            converted_distance = distance / conversion_factor if conversion_factor != 1 else distance
            formatted_distance = f"{converted_distance:.0f}{secondary_unit}"
        else:
            formatted_distance = f"{distance:.2f}{primary_unit}"

        # 添加步行/驾车时间估算
        result = f"📏 距离信息: {formatted_distance}\n"

        if unit in ["公里", "米"]:
            # 步行时间估算 (按5公里/小时)
            walking_distance = distance if unit == "公里" else distance / 1000
            walking_time = walking_distance / 5 * 60  # 分钟

            # 驾车时间估算 (按40公里/小时)
            driving_time = walking_distance / 40 * 60  # 分钟

            result += f"🚶‍♂️ 步行时间: 约{int(walking_time)}分钟\n"
            result += f"🚗 驾车时间: 约{int(driving_time)}分钟\n"

        # 添加距离规模描述
        if unit == "公里":
            if distance < 1:
                scale_desc = "近距离，步行可达"
            elif distance < 5:
                scale_desc = "短距离，适合骑行或短程驾车"
            elif distance < 20:
                scale_desc = "中距离，需要驾车"
            else:
                scale_desc = "长距离，建议规划行程"

            result += f"📍 距离规模: {scale_desc}"

        return result

    except Exception as e:
        logger.error(f"距离格式化失败: {e}")
        return f"格式化距离时发生错误: {str(e)}"


# 工具列表，用于agent创建
BASIC_TOOLS = [
    get_current_time,
    calculate_fish_activity,
    get_location_coordinates,
    get_fishing_season_advice,
    format_distance
]